# 🇮🇹 Ponte Italia — Plataforma de Intercâmbio Acadêmico

> Plataforma web que centraliza a jornada de estudantes brasileiros rumo a graduação e mestrado na **Itália** (e Europa em geral): perfil com documentação, descoberta de universidades, comparativo de requisitos, radar de notícias via web scraping e newsletter diária automática.

**Repositório:** `github.com/julianosfreitas/scrapping_italy`
**Stack principal:** Python (FastAPI) · C#/.NET (serviço de newsletter) · MySQL · Redis · Docker
**Estilo de código:** Programação Funcional em Python (funções puras, imutabilidade, HOFs, `functools`, generators) — o projeto é também material prático da apresentação acadêmica de Paradigmas.

---

## 1. O problema que o site resolve

Estudantes que querem estudar fora enfrentam informação espalhada em dezenas de sites (universidades, consulados, Universitaly, portais de bolsa), prazos diferentes por instituição, listas de documentos que mudam por curso, e notícias sobre vistos/regras que passam despercebidas.

A plataforma responde a isso com quatro promessas:

1. **Um perfil, toda a documentação** — cada estudante sobe passaporte, visto, histórico, certificados de idioma etc. uma única vez.
2. **Comparativo automático** — ao adicionar uma universidade de interesse, o sistema cruza os documentos exigidos com os que o estudante já tem no perfil e mostra o *gap* (o que falta, o que vence, o que está ok).
3. **Radar de oportunidades e notícias** — scraping + APIs de fontes sobre estudo na Itália/Europa (bolsas, prazos, mudanças de visto, mercado para estudantes estrangeiros).
4. **Newsletter diária** — e-mail automático toda manhã (09h) com os 10 tópicos essenciais do dia para quem está no processo.

### Usuários iniciais (seed)

| Estudante | Área | Objetivo |
|---|---|---|
| **Juliano Freitas** | Ciência da Computação | Mestrado na Itália |
| **Davi Neves** | Engenharia | Graduação/mestrado na Itália |

O cadastro é aberto: novos estudantes podem ser adicionados pela própria plataforma.

---

## 2. Mapa do site (páginas / abas)

1. **Home (landing page)** — o que é a plataforma, o problema que resolve, CTA "Criar meu perfil".
2. **Estudantes** — grid com os perfis; página individual de cada estudante.
   - Dados pessoais, foto, bio, área de estudo, nível de italiano/inglês.
   - **Cofre de documentos**: upload categorizado (identidade, acadêmico, financeiro, idioma, visto), com data de validade e status.
   - **Minhas universidades**: instituições salvas + comparativo documentação exigida × documentação no perfil + prazos.
3. **Universidades** — busca/exploração de universidades e cursos na Itália e Europa (dados via API + scraping), com requisitos, prazos, custos e tempo de preparação estimado; botão "adicionar ao meu perfil" (gera alerta).
4. **Radar (notícias)** — feed agregado por scraping/APIs: notícias de vistos, bolsas, mercado internacional para estudantes estrangeiros, separadas por categoria.
5. **Newsletter** — página de inscrição + arquivo das edições enviadas.
6. **Ajuda (FAQ)** — perguntas e soluções mais recorrentes do processo (montadas a partir de varredura na web + curadoria), buscáveis e por categoria.

---

## 3. Arquitetura

```
                         ┌────────────────────────────┐
                         │   Front-end (SPA leve)     │
                         │   HTML + Tailwind + JS     │
                         │   (ou React/Vite, fase 2)  │
                         └────────────┬───────────────┘
                                      │ REST/JSON
                    ┌─────────────────▼──────────────────┐
                    │        API core — Python           │
                    │        FastAPI (estilo funcional)  │
                    │  auth · estudantes · documentos    │
                    │  universidades · comparativo · FAQ │
                    └───────┬───────────────┬────────────┘
                            │               │
                 ┌──────────▼───┐     ┌─────▼──────┐
                 │   MySQL 8.0  │     │   Redis    │
                 │ (dados)      │     │ cache/fila │
                 └──────────────┘     └─────┬──────┘
                                            │
        ┌───────────────────────┐   ┌───────▼──────────────────┐
        │  Scraper — Python     │   │  Newsletter — C#/.NET 8  │
        │  httpx + BeautifulSoup│   │  Worker Service          │
        │  + Playwright (JS)    │   │  Quartz.NET (cron 09h)   │
        │  APScheduler (cron)   │   │  MailKit/SendGrid        │
        └───────────────────────┘   └──────────────────────────┘
```

**Por que essa divisão:**

- **API core em Python/FastAPI** — coerente com a apresentação: os módulos de transformação de dados (normalização de scraping, comparativo de documentos, montagem da newsletter) são escritos como *pipelines de funções puras*, exemplos reais para o slide 27.
- **Serviço de newsletter em C#/.NET** — worker independente que consome a fila do Redis, renderiza o e-mail e dispara às 09h. Justifica o .NET do CV e demonstra arquitetura de microsserviço.
- **Scraper como módulo separado** — roda agendado (APScheduler), grava no MySQL e invalida cache no Redis. Falha de scraping nunca derruba o site.

### Onde a programação funcional aparece (mapa código → apresentação)

| Ferramenta do roteiro | Onde usamos no projeto |
|---|---|
| Funções puras / imutabilidade | Regras do comparativo de documentos: `calcular_gap(docs_exigidos, docs_do_perfil) -> Gap` — sem I/O, 100% testável; DTOs com `@dataclass(frozen=True)` |
| Comprehensions | Normalização dos resultados de scraping em listas/dicts |
| Generators / lazy | Paginação do feed de notícias e leitura de páginas raspadas item a item |
| `map`/`filter` | Pipeline de limpeza de notícias (dedupe, filtro por categoria) |
| `functools.reduce` | Agregação de score de "prontidão" do estudante por categoria |
| `functools.partial` | Especialização de parsers por fonte (`parser_universitaly = partial(parse, fonte="universitaly")`) |
| `functools.lru_cache` | Cache de consultas puras (ex.: lista de requisitos por curso) |
| Closures / decoradores | `@cronometrar`, `@retry(backoff)`, `@exigir_auth` na API |
| Recursão | Varredura de categorias aninhadas do FAQ |

---

## 4. Stack detalhada

### Back-end (Python 3.12)
- **FastAPI** + **Uvicorn** — API REST, docs automáticas (Swagger), validação com **Pydantic v2**.
- **SQLAlchemy 2.0** + **Alembic** — ORM e migrations versionadas.
- **httpx** (requisições async) + **BeautifulSoup4** — scraping de páginas estáticas.
- **Playwright** — scraping de páginas com JavaScript (fallback).
- **APScheduler** — agendamento dos jobs de scraping.
- **Redis** — cache de feed + fila de e-mails (lista/stream) para o worker .NET.
- **PyTest** — testes (as funções puras do comparativo são o alvo perfeito).
- Qualidade: **ruff** (lint), **black** (formatação), **mypy** (type hints) — exatamente as dicas do slide 27.

### Serviço de newsletter (C# / .NET 8)
- **Worker Service** + **Quartz.NET** (cron `0 0 9 * * ?`, fuso America/Recife).
- **StackExchange.Redis** — consome a fila montada pelo Python.
- **MailKit** (SMTP) ou **SendGrid** — envio; template Razor para o HTML do e-mail.

### Front-end
- **Fase 1 (MVP):** templates Jinja2 servidos pelo FastAPI + **Tailwind CSS** + JS vanilla — entrega rápida e tudo em Python.
- **Fase 2:** migração das áreas logadas para **React + Vite + TypeScript** (stack do CV), consumindo a mesma API.

### Infra
- **Docker + docker-compose** — 5 serviços: `api`, `scraper`, `newsletter`, `mysql`, `redis`.
- **GitHub Actions** — lint + testes em todo PR; build das imagens no merge em `main`.
- **Deploy** — VPS (Hetzner/Contabo/DigitalOcean) com compose + **Caddy** (HTTPS automático). Alternativa gratuita para demo: Railway/Render.

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
criado_em             status (ok|vencendo|      universidade_id (fk)
                        vencido)                nome / grau (grad|mestrado)
inscricoes_news       criado_em                 idioma / custo_anual
─────────────                                   prazo_inscricao
id, email,            requisitos_curso          tempo_preparacao_meses
ativo, criado_em      ─────────────
                      id, curso_id (fk),        estudante_universidade
noticias              categoria, descricao,     ─────────────
─────────────         obrigatorio (bool)        estudante_id + curso_id (pk)
id, titulo, resumo,                             status, alerta_prazo (bool)
url (uniq), fonte,    faq                       adicionado_em
categoria, idioma,    ─────────────
publicada_em,         id, categoria_id (fk auto-
coletada_em             ref p/ subcategorias),
                        pergunta, resposta, fontes
```

O **comparativo** não é tabela: é função pura que recebe `requisitos_curso` × `documentos` do estudante e devolve `{atendidos, faltando, vencendo}` — calculado on-the-fly e cacheável com `lru_cache`.

---

## 6. Fontes de dados (scraping + APIs)

| Fonte | Tipo | O que extrair |
|---|---|---|
| **Universitaly** (universitaly.it) | Scraping | Cursos, universidades, requisitos de pré-matrícula |
| **Study in Italy / MAECI** | Scraping | Regras de visto de estudo, prazos consulares |
| **DISCO/laziodisco e regionais** | Scraping | Bolsas regionais (DSU) |
| **Scholarships portals (ex.: studyinitaly, europa.eu)** | Scraping/RSS | Bolsas e editais europeus |
| **Reddit API** (r/Italy, r/studyAbroad) | API oficial | Discussões e dúvidas recorrentes (alimenta FAQ) |
| **Google News RSS** (queries: "studiare in Italia stranieri", "student visa Italy") | RSS | Notícias gerais |
| **X/Twitter** | API (avaliar custo) ou fallback via Nitter/RSS | Alertas de consulados e perfis de intercâmbio |

Regras do scraper: respeitar `robots.txt`, identificar `User-Agent`, intervalo entre requisições, dedupe por URL, retry com backoff exponencial (decorador funcional — mesmo padrão que você já usa na integração SEFAZ do Tuttor).

---

## 7. Newsletter diária (09h)

1. **Curadoria (Python, job 08h30):** função-pipeline seleciona as notícias das últimas 24h, ranqueia, agrupa nos **10 tópicos essenciais** (vistos · prazos · bolsas · idioma · moradia · finanças · documentação · admissões · vida na Itália · mercado para estrangeiros) e publica um JSON na fila do Redis.
2. **Disparo (.NET, 09h):** worker lê a fila, renderiza o template HTML (design clean, mesma identidade do site) e envia para todos os inscritos ativos; grava log de envio.
3. **Arquivo:** cada edição vira página em `/newsletter/{data}` no site.

---

## 8. Design (referência: Duolingo — clean e moderno)

- **Paleta contida:** fundo branco/off-white `#FAFAF7`, texto grafite `#1F2933`, **um** verde de ação `#2E7D5B` (aceno à bandeira italiana sem clichê), cinzas de apoio. Nada de neon, nada de gradiente chamativo.
- **Tipografia:** Inter ou Nunito Sans (títulos bold, corpo regular, entrelinha generosa).
- **Componentes:** cards com cantos arredondados (12–16px), sombras sutis, muito espaço em branco, ícones de linha (Lucide).
- **Tom:** direto e amigável; landing com uma frase-problema, uma frase-solução, um CTA.
- **Acessibilidade:** contraste AA, foco visível, mobile-first.

---

## 9. Estrutura do repositório

```
scrapping_italy/
├── README.md
├── docker-compose.yml
├── .github/workflows/ci.yml
├── api/                      # FastAPI (Python)
│   ├── app/
│   │   ├── main.py
│   │   ├── core/             # config, seguranca, decoradores
│   │   ├── models/           # SQLAlchemy
│   │   ├── schemas/          # Pydantic (frozen)
│   │   ├── routers/          # estudantes, documentos, universidades, noticias, faq, newsletter
│   │   ├── services/         # FUNÇÕES PURAS: comparativo, ranking, curadoria
│   │   └── templates/        # Jinja2 (fase 1)
│   ├── tests/
│   ├── alembic/
│   └── pyproject.toml
├── scraper/                  # Python
│   ├── sources/              # um parser por fonte (partial/HOF)
│   ├── pipeline.py           # map/filter/reduce de limpeza
│   ├── scheduler.py          # APScheduler
│   └── tests/
├── newsletter/               # C#/.NET 8 Worker
│   ├── Newsletter.Worker/
│   └── Newsletter.Tests/
└── docs/
    ├── ARQUITETURA.md
    ├── FONTES_SCRAPING.md
    └── DESIGN.md
```

---

## 10. Roadmap (6 sprints de 1 semana)

**Sprint 1 — Fundação**
Repo, docker-compose (mysql+redis), FastAPI esqueleto, Alembic, modelos `estudantes`/`documentos`, seed do Juliano e do Davi, CI com ruff+pytest.

**Sprint 2 — Perfis e cofre de documentos**
CRUD de estudantes, auth (JWT simples), upload de arquivos com categoria/validade/status, páginas Jinja2 + Tailwind (home, estudantes, perfil).

**Sprint 3 — Universidades e comparativo**
Modelos `universidades`/`cursos`/`requisitos`, cadastro manual + primeira fonte via scraping (Universitaly), **função pura `calcular_gap`** com bateria de testes, tela de comparativo e alertas de prazo.

**Sprint 4 — Radar (scraping)**
Módulo `scraper/` com 3 fontes + Google News RSS, pipeline funcional de limpeza/dedupe, APScheduler, aba Radar com filtros por categoria, cache Redis.

**Sprint 5 — Newsletter**
Job de curadoria (10 tópicos) → fila Redis → worker .NET com Quartz + MailKit, template de e-mail, página de inscrição e arquivo de edições.

**Sprint 6 — FAQ, polimento e deploy**
FAQ com categorias (varredura Reddit + curadoria), revisão de design, Caddy + HTTPS na VPS, deploy do compose, smoke tests, documentação final.

---

## 11. Como rodar (dev)

```bash
git clone https://github.com/julianosfreitas/scrapping_italy.git
cd scrapping_italy
cp .env.example .env          # segredos: DB, Redis, SMTP
docker compose up -d mysql redis
cd api && pip install -e ".[dev]" && alembic upgrade head
uvicorn app.main:app --reload  # http://localhost:8000
# scraper:    python -m scraper.scheduler
# newsletter: dotnet run --project newsletter/Newsletter.Worker
```

---

## 12. Riscos e decisões em aberto

- **API do X/Twitter é paga** — começar por Reddit + RSS; Twitter fica como "nice to have".
- **Sites italianos mudam de HTML** — parsers isolados por fonte + testes de contrato; falha de uma fonte não derruba o feed.
- **LGPD** — documentos pessoais: armazenar fora do repositório (volume/S3), URLs assinadas, senha com hash (bcrypt), HTTPS obrigatório.
- **Entregabilidade de e-mail** — usar SendGrid/Resend com domínio verificado (SPF/DKIM) em vez de SMTP puro, para não cair em spam.
