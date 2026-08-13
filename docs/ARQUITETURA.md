# Arquitetura — Ponte Italia

Detalhamento da seção 3 do README: o que cada serviço faz, como conversam e
por que a divisão é essa.

## Visão geral

```
                    Caddy (HTTPS automático, :80/:443)
                                  │
                    ┌─────────────▼──────────────┐
                    │   api — FastAPI (:8000)    │
                    │   Jinja2 + Tailwind        │
                    │   REST /api/*              │
                    └──┬──────────────────────┬──┘
                       │                      │
              ┌────────▼────────┐    ┌────────▼────────┐
              │   MySQL 8.0     │    │     Redis 7     │
              │  dados          │    │ cache + fila    │
              └─────────────────┘    └────────┬────────┘
                       ▲                      │
          ingestão     │                      │ fila newsletter:fila
          autenticada  │                      │
              ┌────────┴────────┐    ┌────────▼─────────────┐
              │ scraper (Python)│    │ newsletter (.NET 8)  │
              │ APScheduler     │    │ Quartz.NET cron 09h  │
              │ • radar 3/3h    │    │ RazorLight + MailKit │
              │ • curadoria 8h30│    │                      │
              └─────────────────┘    └──────────────────────┘
```

## Regra que organiza o código

Está no CLAUDE.md e vale para os três serviços Python:

> **Regra de negócio = função pura em `services/`. I/O = router.**

Os routers buscam dados, convertem para dataclasses congeladas e delegam o
cálculo. Nenhuma função de `api/app/services/` ou de `scraper/pipeline.py`
toca banco, rede ou relógio — o que varia (inclusive a data de hoje) entra
por parâmetro. É por isso que a suíte roda inteira em memória, sem Docker.

## Serviços

### api (FastAPI, Python 3.12)

Dono do banco e única porta de entrada para os outros serviços. Serve tanto
o HTML (Jinja2 + Tailwind) quanto a API REST documentada em `/docs`.

| Camada | Papel |
|---|---|
| `app/routers/` | I/O: consulta, autentica, serializa |
| `app/services/` | funções puras: comparativo, curadoria, feed, FAQ |
| `app/models/` | SQLAlchemy 2.0 |
| `app/schemas/` | Pydantic v2, todos `frozen=True` |
| `app/core/` | config, banco, segurança, cache, fila, decoradores |
| `app/static/` | JS servido direto pelo navegador (`/static/*`) |

Autenticação por JWT (`@exigir_auth`); senhas com bcrypt. Uploads ficam fora
do repositório, em volume, com download por URL assinada de escopo restrito.

### scraper (Python)

Roda separado porque **falha de scraping não pode derrubar o site**. Dois
jobs no mesmo `BlockingScheduler` (fuso America/Recife):

- **Radar**, a cada `RADAR_INTERVALO_MINUTOS` (padrão 180): coleta educada por
  fonte → `pipeline.processar` (map/filter/dedupe/classificação) → `POST
  /api/noticias` autenticado. Cada fonte é isolada em try/except: uma fonte
  fora do ar só perde aquela fonte naquela rodada.
- **Curadoria**, cron diário às `NEWSLETTER_HORA_CURADORIA` (padrão 08h30):
  dispara `POST /api/newsletter/curadoria`. Quem monta a edição é a api.

O scraper **nunca fala com o MySQL** — só com a API, como qualquer cliente.

### newsletter (C#/.NET 8)

Worker Service com Quartz.NET, cron `0 0 9 * * ?` em America/Recife:

1. `RPOP` na lista `newsletter:fila` do Redis (o Python faz `LPUSH` → FIFO);
2. busca os inscritos ativos em `GET /api/newsletter/inscritos`;
3. renderiza o HTML com RazorLight (`Templates/Edicao.cshtml`);
4. envia por SMTP com MailKit, **uma mensagem por inscrito** (Bcc vazaria a
   lista de e-mails);
5. confirma em `POST /api/newsletter/edicoes/{data}/enviada`.

`NEWSLETTER_DISPARAR_AO_INICIAR=true` adiciona um gatilho imediato na subida —
usado na demo e em operação manual; em produção fica desligado.

### MySQL e Redis

MySQL guarda tudo que é permanente. Redis tem dois papéis distintos:

- **cache** do feed do Radar (`radar:feed:*`, TTL 300s), invalidado a cada
  ingestão;
- **fila** da newsletter (`newsletter:fila`).

Ambos degradam com elegância: sem Redis, o feed continua respondendo (só mais
lento) e a edição continua salva no banco e visível em `/newsletter/{data}`.

## Fluxos

### Coleta → Radar

```
fontes → coletar_noticias (robots, User-Agent, backoff)
       → pipeline.processar   (map normalizar → filter válida → dedupe URL → map classificar)
       → POST /api/noticias   (dedupe final pela URL única)
       → invalidar_feed()
```

### Curadoria → e-mail

```
08h30  scraper  → POST /api/newsletter/curadoria
                → curar(notícias, agora)   [função pura]
                → arquiva em edicoes_newsletter (data única ⇒ idempotente)
                → LPUSH newsletter:fila
09h00  worker   → RPOP → Razor → MailKit → marca enviada
```

## Decisões e limitações conhecidas

- **Universitaly atrás de WAF.** A fonte fica atrás de AWS WAF com challenge
  JavaScript; nem httpx nem Playwright passam. A decisão registrada é NÃO
  insistir em contornar o bloqueio: a coleta usa fixture e o caso está
  documentado em `scraper/navegador.py`.
- **Entrega da fila é at-most-once.** O worker faz `RPOP`, que remove antes de
  processar: se ele morrer no meio do disparo, aquela edição se perde da fila.
  A recuperação é simples porque a edição continua no banco — basta rodar a
  curadoria de novo, que reenfileira. Uma fila confiável (`LMOVE` para uma
  lista de processamento) é o próximo passo natural se isso incomodar.
- **Janela da curadoria.** `curar` considera a data de publicação da notícia
  (e a de coleta, quando não há publicação). Se as fontes não publicarem nada
  nas últimas 24h, a edição do dia sai vazia — comportamento correto para a
  leitura literal da seção 7, e o parâmetro `janela_horas` permite ampliar.
- **Cache do feed por chave composta.** A chave inclui categoria, fonte,
  página e tamanho; qualquer ingestão limpa o prefixo inteiro.

## Deploy

`docker-compose.prod.yml` sobe os 5 serviços mais o Caddy. MySQL e Redis não
expõem porta no host. Antes de subir, preencha no `.env`: `DOMINIO`,
`ACME_EMAIL`, `MYSQL_*`, `JWT_SEGREDO`, `PONTE_EMAIL`/`PONTE_SENHA` e as
credenciais SMTP do provedor real.

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
docker compose -f docker-compose.prod.yml exec api python -m app.seed
docker compose -f docker-compose.prod.yml exec api python -m app.seed_faq
./deploy/smoke.sh https://SEU.DOMINIO
```

O certificado só é emitido com o `DOMINIO` já apontando para o IP do servidor
e as portas 80/443 abertas.
