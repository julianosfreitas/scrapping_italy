# 🇮🇹 Ponte Italia — Plataforma de Intercâmbio Acadêmico

> Plataforma web que centraliza a jornada de estudantes brasileiros rumo a graduação e mestrado na **Itália** (e Europa em geral): perfil com documentação, descoberta de universidades, comparativo de requisitos, radar de notícias via web scraping e newsletter diária automática.

**Repositório:** `github.com/julianosfreitas/scrapping_italy`
**Stack principal:** Python (FastAPI) · C#/.NET 8 (worker de newsletter) · MySQL · Redis · Docker
**Estilo de código:** Programação Funcional em Python (funções puras, imutabilidade, HOFs, `functools`, generators) — o projeto é também material prático da apresentação acadêmica de Paradigmas.

### Estado atual

| | |
|---|---|
| Roadmap | **6 de 6 sprints concluídas** (seção 10) |
| Testes | **215** — 161 na API · 36 no scraper · 18 no worker .NET |
| Qualidade | `ruff` + `black` + `mypy --strict` limpos; CI em todo push |
| Migrations | 6, todas via Alembic |
| Conceitos de PF | **16 de 16** documentados em [`docs/RELATORIO_FP.md`](docs/RELATORIO_FP.md) |

---

## 1. O problema que o site resolve

Estudantes que querem estudar fora enfrentam informação espalhada em dezenas de sites (universidades, consulados, Universitaly, portais de bolsa), prazos diferentes por instituição, listas de documentos que mudam por curso, e notícias sobre vistos/regras que passam despercebidas.

A plataforma responde a isso com quatro promessas:

1. **Um perfil, toda a documentação** — cada estudante sobe passaporte, visto, histórico, certificados de idioma etc. uma única vez.
2. **Comparativo automático** — ao adicionar uma universidade de interesse, o sistema cruza os documentos exigidos com os que o estudante já tem no perfil e mostra o *gap* (o que falta, o que vence, o que está ok).
3. **Radar de oportunidades e notícias** — scraping + RSS de fontes sobre estudo na Itália/Europa (bolsas, prazos, mudanças de visto).
4. **Newsletter diária** — e-mail automático toda manhã (09h) com os tópicos essenciais do dia, **traduzidos para português**.

### Usuários iniciais (seed)

| Estudante | Área | Objetivo |
|---|---|---|
| **Juliano Freitas** | Ciência da Computação | Mestrado na Itália |
| **Davi Neves** | Engenharia | Graduação/mestrado na Itália |

O cadastro é aberto: novos estudantes podem ser adicionados pela própria plataforma.

---

## 2. Mapa do site (páginas / abas)

1. **Home** (`/`) — o que é a plataforma, o problema que resolve, CTA "Criar meu perfil".
2. **Estudantes** (`/estudantes`) — grid com os perfis; página individual de cada estudante.
   - Dados pessoais, bio, área de estudo, nível de italiano/inglês.
   - **Cofre de documentos**: upload categorizado (identidade, acadêmico, financeiro, idioma, visto), com data de validade e status derivado.
   - **Minhas universidades**: instituições salvas + comparativo documentação exigida × documentação no perfil + alerta de prazo.
3. **Universidades** (`/universidades`) — busca de universidades e cursos, com requisitos, prazos e custos; botão "adicionar ao meu perfil".
4. **Radar** (`/radar`) — feed agregado por scraping/RSS, com filtros por categoria e fonte e paginação server-side.
5. **Newsletter** (`/newsletter`) — página de inscrição + arquivo das edições (`/newsletter/{data}`).
6. **Ajuda** (`/ajuda`) — FAQ com categorias aninhadas (árvore percorrida por recursão) e busca sem acento.

Documentação da API em `/docs` (Swagger, gerado pelo FastAPI).

---

## 3. Arquitetura

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

**A regra que organiza o código** (vale para os três serviços Python):

> **Regra de negócio = função pura em `services/`. I/O = router.**

Os routers buscam dados, convertem para dataclasses congeladas e delegam o cálculo. Nenhuma função de `api/app/services/` ou de `scraper/pipeline.py` toca banco, rede ou relógio — o que varia (inclusive a data de hoje) entra por parâmetro. É por isso que a suíte roda inteira em memória, sem Docker.

**Por que essa divisão:**

- **API core em Python/FastAPI** — os módulos de transformação (normalização de scraping, comparativo de documentos, curadoria da newsletter, árvore do FAQ) são *pipelines de funções puras*, exemplos reais para a apresentação.
- **Worker de newsletter em C#/.NET** — serviço independente que consome a fila do Redis, renderiza o e-mail e dispara às 09h.
- **Scraper separado** — roda agendado, grava via API e invalida o cache. Falha de scraping nunca derruba o site.

Detalhamento em [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md).

### Onde a programação funcional aparece (mapa código → apresentação)

| Conceito | Onde vive |
|---|---|
| Funções puras / imutabilidade | `calcular_gap`, `calcular_status` (`api/app/services/`); DTOs `@dataclass(frozen=True)` |
| Comprehensions | normalização dos parsers (`scraper/sources/base.py`) |
| Generators / lazy | `iterar_itens_rss`, `paginar`, `janelas` (`api/app/services/feed.py`) |
| `map`/`filter` | pipeline de limpeza (`scraper/pipeline.py`) |
| `functools.reduce` | `estatisticas` e `agrupar_por_topico` (curadoria) |
| `functools.partial` | um parser por fonte (`parser_universitaly`) |
| `functools.lru_cache` | `requisitos_por_categoria`, `get_settings`, `traduzir` |
| Closures / decoradores | `@cronometrar`, `retry_backoff`, `@exigir_auth` |
| Recursão | árvore de categorias do FAQ (`api/app/services/faq.py`) |

---

## 4. Stack detalhada

### Back-end (Python 3.12)
- **FastAPI** + **Uvicorn** — API REST, docs automáticas (Swagger), validação com **Pydantic v2** (schemas `frozen=True`).
- **SQLAlchemy 2.0** + **Alembic** — ORM e migrations versionadas.
- **httpx** + **BeautifulSoup4** — coleta e parsing de páginas estáticas e RSS.
- **Playwright** — fallback para páginas com challenge JavaScript.
- **APScheduler** — agenda a coleta do Radar e a curadoria da newsletter.
- **Redis** — cache do feed + fila da newsletter para o worker .NET.
- **deep-translator** — tradução das notícias para português (serviço externo, com fallback).
- **bcrypt** + **PyJWT** — autenticação.
- **PyTest** — 161 testes; as funções puras rodam sem banco e sem rede.
- Qualidade: **ruff** (lint), **black** (formatação), **mypy --strict** (tipos).

### Serviço de newsletter (C# / .NET 8)
- **Worker Service** + **Quartz.NET** (cron `0 0 9 * * ?`, fuso America/Recife).
- **StackExchange.Redis** — consome a fila montada pelo Python.
- **RazorLight** — renderiza o template `.cshtml` do e-mail em runtime.
- **MailKit** — envio SMTP, com o logo embutido como recurso vinculado (`cid:`).
- **xUnit** — 18 testes (parsing da fila, serialização e renderização).

### Front-end
- **Fase 1 (atual):** templates Jinja2 servidos pelo FastAPI + **Tailwind CSS** (CDN) + JS vanilla em `api/app/static/js/`.
- **Fase 2:** migração das áreas logadas para **React + Vite + TypeScript**, consumindo a mesma API.

### Infra
- **Docker + docker-compose** — dev: `mysql`, `redis`, `mailpit`. Produção: os 5 serviços + Caddy.
- **GitHub Actions** — lint, tipos e testes dos três módulos em todo push.
- **Deploy** — VPS com `docker-compose.prod.yml` + **Caddy** (HTTPS automático).

### Ferramentas de documentação
Scripts em `docs/`, fora do caminho da aplicação: geração dos assets do logo (**Pillow**), da apresentação (**python-pptx**) e das capturas de tela (**Playwright**).

---

## 5. Modelo de dados (MySQL)

```
estudantes            documentos                universidades
─────────────         ─────────────             ─────────────
id (pk)               id (pk)                   id (pk)
nome                  estudante_id (fk)         nome
email (uniq)          categoria (enum:          pais / cidade
senha_hash              identidade|academico|   site_oficial
foto_url                financeiro|idioma|      fonte (api|scraping|manual)
area_estudo             visto|outros)
bio                   tipo (passaporte, ...)    cursos
nivel_italiano        arquivo_url               ─────────────
nivel_ingles          data_validade             id (pk)
criado_em             criado_em                 universidade_id (fk)
                                                nome / grau (grad|mestrado)
inscricoes_news       noticias                  idioma / custo_anual
─────────────         ─────────────             prazo_inscricao
id, email (uniq),     id, titulo, resumo,       tempo_preparacao_meses
ativo, criado_em      url (uniq), fonte,
                      categoria, idioma,        requisitos_curso
edicoes_newsletter    publicada_em,             ─────────────
─────────────         coletada_em               id, curso_id (fk),
id, data (uniq),                                categoria, descricao,
conteudo (JSON),      faq                       obrigatorio (bool)
enviada_em,           ─────────────
criado_em             id, categoria_id (fk      estudante_universidade
                        AUTO-REFERENTE),        ─────────────
                      nome, pergunta,           estudante_id + curso_id (pk)
                      resposta, fontes (JSON),  status, alerta_prazo (bool)
                      ordem                     adicionado_em
```

Três decisões de modelagem que valem nota:

- **O comparativo não é tabela.** É função pura que recebe `requisitos_curso` × `documentos` e devolve `{atendidos, faltando, vencendo}` — calculado on-the-fly e cacheável com `lru_cache`.
- **O status do documento não é coluna.** É derivado na leitura por `calcular_status(validade, hoje)`; gravá-lo deixaria o dado defasado no dia seguinte.
- **O FAQ é uma árvore numa tabela só.** `categoria_id` referencia `faq.id`, o que permite subcategorias em qualquer profundidade — e é a estrutura que a recursão percorre.

---

## 6. Fontes de dados (scraping + RSS)

| Fonte | Tipo | Estado |
|---|---|---|
| **Google News RSS** (queries "studiare in Italia stranieri", "student visa Italy") | RSS | ✅ coletando |
| **laziodisco.it** — bolsas do DSU do Lazio | Scraping | ✅ coletando |
| **studyinitaly.esteri.it** — bandos do MAECI | Scraping | ✅ coletando |
| **Universitaly** — cursos e requisitos | Scraping | ⛔ bloqueado por WAF — usa fixture |
| DISCO de outras regiões | Scraping | ⬜ não implementado |
| Reddit API | API oficial | ⬜ depende de decisão sobre auth/custo |
| X/Twitter | API paga | ⬜ "nice to have" |

**Regras do scraper:** respeitar `robots.txt` (RSS é isento — é endpoint de sindicação), identificar `User-Agent`, intervalo entre requisições, dedupe por URL em duas camadas (lote e índice único), retry com backoff exponencial via decorador, e isolamento por fonte — uma fonte fora do ar não impede as outras.

**Sobre o Universitaly:** fica atrás de AWS WAF com challenge JavaScript. Foram tentados httpx (HTTP 202 vazio) e Playwright com Chromium (também barrado). **A decisão registrada é não insistir em contornar o bloqueio** — nada de rotação de IP ou resolução de captcha. A coleta usa fixture e o parser segue testado. Detalhes em [`docs/FONTES_SCRAPING.md`](docs/FONTES_SCRAPING.md).

---

## 7. Newsletter diária (09h)

1. **Curadoria (08h30, agendada pelo scraper)** — dispara `POST /api/newsletter/curadoria`. A função pura `curar` seleciona as notícias da janela, ranqueia por recência e agrupa nos **10 tópicos essenciais** (vistos · prazos · bolsas · idioma · moradia · finanças · documentação · admissões · vida na Itália · mercado para estrangeiros) com `reduce`. O texto é resumido (`resumir`, puro) e traduzido para português (`traduzir`, I/O com cache e fallback). A edição é arquivada no banco e publicada na fila do Redis.
2. **Disparo (09h, worker .NET)** — lê a fila, busca os inscritos ativos na API, renderiza o HTML com RazorLight e envia por MailKit, **uma mensagem por inscrito** (Bcc vazaria a lista). Ao final confirma o envio na API.
3. **Arquivo** — cada edição vira página em `/newsletter/{data}`.

A curadoria é **idempotente por dia**: `edicoes_newsletter.data` é única, então rodar de novo atualiza a edição em vez de duplicar.

**Em desenvolvimento** o SMTP aponta para o **Mailpit** do compose (captura as mensagens em `localhost:8025`, não entrega nada). Para envio real, basta apontar `SMTP_*` no `.env` para um provedor — com Gmail é obrigatório usar **senha de app**, e o remetente precisa ser a mesma conta autenticada.

---

## 8. Design

O logo é um monograma **PI** sobre uma ponte, dentro de uma estrela de quatro pontas, impresso em papel. Dele saem duas paletas irmãs.

### Site (Jinja2 + Tailwind)

| Papel | Hex |
|---|---|
| Fundo | `#FAFAF7` |
| Texto | `#1F2933` |
| Ação | `#2E7D5B` |
| Ação suave | `#EAF3EF` |

### Carta (e-mail) e apresentação — tons do papel do logo

| Papel | Hex | Contraste sobre `#F0E8DE` |
|---|---|---|
| Fundo | `#F0E8DE` | — |
| Creme (cartões) | `#F2E5D5` | — |
| Neutro (cartões) | `#E3E2DF` | — |
| Tinta | `#1B1A18` | 15,4:1 ✅ |
| Sálvia escura (rótulos) | `#5A5A47` | 5,7:1 ✅ |
| Sálvia (ornamento) | `#797963` | 3,7:1 — **só texto grande e filetes** |
| Bege (bordas) | `#BFAE99` | — |

**Tipografia:** Inter (site) e serifada (carta e slides, para o tom de documento).
**Componentes:** cards `rounded-2xl`, sombras sutis, muito espaço em branco.
**Acessibilidade:** contraste AA, foco visível em todo elemento interativo, semântica antes de estilo (`<details>` no FAQ, `role="search"`, `aria-live` nos avisos), mobile-first.

Os assets do logo são gerados por `docs/gerar_logo.py`, que extrai a silhueta do mockup em papel e produz as versões monocromáticas (verde, sálvia, bege, branco) mais os favicons. Detalhes em [`docs/DESIGN.md`](docs/DESIGN.md).

---

## 9. Estrutura do repositório

```
scrapping_italy/
├── README.md · CLAUDE.md · .env.example
├── docker-compose.yml            # dev: mysql, redis, mailpit
├── docker-compose.prod.yml       # produção: 5 serviços + caddy
├── .github/workflows/ci.yml      # api · scraper · newsletter
├── deploy/
│   ├── Caddyfile                 # HTTPS automático
│   └── smoke.sh                  # 16 verificações pós-deploy
├── api/                          # FastAPI (Python)
│   ├── app/
│   │   ├── main.py
│   │   ├── core/                 # config, db, segurança, cache, fila, tradução
│   │   ├── models/               # SQLAlchemy
│   │   ├── schemas/              # Pydantic (frozen)
│   │   ├── routers/              # I/O: estudantes, documentos, universidades,
│   │   │                         #      notícias, newsletter, faq, páginas
│   │   ├── services/             # FUNÇÕES PURAS: comparativo, curadoria, feed, faq
│   │   ├── templates/            # Jinja2
│   │   └── static/               # JS e imagens (logo, favicons)
│   ├── tests/                    # 161 testes
│   ├── alembic/                  # 6 migrations
│   ├── Dockerfile
│   └── pyproject.toml
├── scraper/                      # Python
│   ├── sources/                  # um parser por fonte (partial/HOF)
│   ├── pipeline.py               # map/filter/reduce de limpeza
│   ├── coleta.py · navegador.py  # HTTP educado + fallback Playwright
│   ├── scheduler.py              # APScheduler: radar + curadoria
│   ├── tests/                    # 36 testes, sem rede
│   └── Dockerfile
├── newsletter/                   # C#/.NET 8
│   ├── Newsletter.Worker/        # Quartz, Redis, Razor, MailKit
│   ├── Newsletter.Tests/         # 18 testes (xUnit)
│   └── Dockerfile
└── docs/
    ├── ARQUITETURA.md · FONTES_SCRAPING.md · DESIGN.md
    ├── RELATORIO_FP.md           # 16 conceitos de PF documentados
    ├── AJUSTES_APRESENTACAO.md   # conformidade da apresentação
    ├── PF-Python-Ponte-Italia.pptx / .pdf
    ├── screenshots/              # capturas do sistema
    ├── gerar_logo.py · gerar_slides.py · capturar_telas.py
    └── verificar_slides.py · verificar_layout.py
```

---

## 10. Roadmap — concluído

| Sprint | Entrega | Estado |
|---|---|---|
| **1 — Fundação** | docker-compose, FastAPI, Alembic, modelos de estudantes/documentos, seed, CI | ✅ |
| **2 — Perfis e cofre** | CRUD, auth JWT + bcrypt, upload com validade e status derivado, páginas Jinja2 | ✅ |
| **3 — Universidades** | modelos de cursos/requisitos, **`calcular_gap` puro** + testes, tela de comparativo | ✅ |
| **4 — Radar** | 3 fontes + pipeline funcional, APScheduler, aba Radar com filtros, cache Redis | ✅ |
| **5 — Newsletter** | curadoria em 10 tópicos, fila Redis, worker .NET com Quartz + MailKit, arquivo de edições | ✅ |
| **6 — FAQ, polimento e deploy** | FAQ recursivo, aba Ajuda, extração do JS, Caddy + compose de produção, documentação | ✅ |

Cada sprint tem uma branch própria (`sprint-1-fundacao` … `sprint-6-faq-deploy`), toda mergeada em `main`.

---

## 11. Como rodar (dev)

```bash
git clone https://github.com/julianosfreitas/scrapping_italy.git
cd scrapping_italy
cp .env.example .env          # ajuste segredos: DB, JWT, PONTE_*, SMTP

# 1. infraestrutura
docker compose up -d mysql redis mailpit

# 2. api
cd api
python -m venv .venv && .venv/Scripts/activate    # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
python -m app.seed            # estudantes iniciais
python -m app.seed_faq        # árvore do FAQ
uvicorn app.main:app --reload # http://localhost:8000

# 3. scraper (radar 3/3h + curadoria 08h30)
cd .. && PONTE_EMAIL=... PONTE_SENHA=... python -m scraper.scheduler

# 4. worker da newsletter
cd newsletter && dotnet run --project Newsletter.Worker
```

Caixa de entrada de teste (Mailpit): <http://localhost:8025>
API documentada: <http://localhost:8000/docs>

### Gate de qualidade

```bash
cd api      && ruff check . && black --check . && mypy app && pytest
cd ..       && ruff check scraper && black --check scraper \
            && MYPYPATH=api mypy --config-file scraper/pyproject.toml -p scraper \
            && pytest scraper/tests
cd newsletter && dotnet build && dotnet test
./deploy/smoke.sh                 # com a api no ar
```

### Produção

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
./deploy/smoke.sh https://SEU.DOMINIO
```

Antes de subir, defina no `.env`: `DOMINIO`, `ACME_EMAIL`, `MYSQL_*`, `JWT_SEGREDO`, `PONTE_EMAIL`/`PONTE_SENHA` e as credenciais SMTP. O certificado só é emitido com o domínio já apontando para o servidor e as portas 80/443 abertas.

---

## 12. Riscos e decisões em aberto

- **Universitaly atrás de WAF.** Decisão registrada: não contornar. A fonte usa fixture até haver acesso legítimo ou API oficial.
- **Entrega da fila é *at-most-once*.** O worker faz `RPOP`, que remove antes de processar: se ele morrer no meio do disparo, aquela edição sai da fila. A recuperação é simples porque a edição continua no banco — basta rodar a curadoria de novo. Uma fila confiável (`LMOVE` para lista de processamento) é o próximo passo natural.
- **Tradução depende de serviço externo não oficial.** `deep-translator` usa o Google Tradutor; se cair, o texto sai no idioma original em vez de a edição falhar. Um resumo *abstrativo* de verdade exigiria um LLM — hoje o resumo é extrativo (primeiras frases).
- **Janela da curadoria.** `curar` considera a data de publicação (e a de coleta, quando não há publicação). Se as fontes não publicarem nada nas últimas 24h, a edição do dia sai vazia — comportamento correto para a leitura literal da seção 7; o parâmetro `janela_horas` permite ampliar.
- **Gmail para envio real** tem limite diário e tende a cair em spam quando o volume cresce. Produção pede SendGrid/Resend com domínio verificado (SPF/DKIM).
- **Tailwind via CDN** é ótimo para prototipar e ruim para produção (sem purge, sem versão fixa). Some na migração para React + Vite da fase 2.
- **LGPD** — documentos pessoais ficam em volume fora do repositório, com URL assinada de escopo restrito, senha com bcrypt e HTTPS obrigatório.
