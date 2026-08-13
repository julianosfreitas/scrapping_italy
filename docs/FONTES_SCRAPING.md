# Fontes de scraping — estado real

Detalhamento da seção 6 do README com o que efetivamente está coletando hoje,
o que está bloqueado e sob que regras o scraper opera.

## Situação por fonte

| Fonte | Tipo | Estado | Observação |
|---|---|---|---|
| **Google News RSS** | RSS | ✅ coletando | queries "studiare in Italia stranieri" e "student visa Italy" |
| **laziodisco.it** | Scraping HTML | ✅ coletando | bandos do DSU do Lazio |
| **studyinitaly.esteri.it** | Scraping HTML | ✅ coletando | lista de bandos do MAECI |
| **Universitaly** | Scraping HTML | ⛔ bloqueado | AWS WAF com challenge JS — usa fixture |
| **DISCO regionais (fora Lazio)** | Scraping | ⬜ não implementado | um parser por região, mesmo molde do laziodisco |
| **Reddit API** | API oficial | ⬜ não implementado | depende de decisão sobre auth/custo |
| **X/Twitter** | API | ⬜ não implementado | API paga — "nice to have" da seção 12 |

Volume da última coleta real: **111 itens** brutos (google_news 100,
laziodisco 10, studyinitaly 1), 8 novos após o dedupe por URL.

## O caso Universitaly

O portal fica atrás de AWS WAF com challenge JavaScript. Duas tentativas
foram feitas, nesta ordem:

1. **httpx** — devolve HTTP 202 com corpo vazio (o challenge não é resolvido);
2. **Playwright + Chromium headless** (`scraper/navegador.py`) — executa o
   challenge como um navegador real, mas o WAF continua barrando.

**Decisão registrada: não insistir em contornar o bloqueio.** Nada de rotação
de IP, de user-agent falso ou de serviço de resolução de captcha. A coleta do
Universitaly permanece via fixture (`scraper/tests/fixtures/universitaly_atenei.html`),
o parser continua testado e, no dia em que o acesso for liberado (ou surgir
uma API oficial), só a camada de obtenção muda — o parser não.

## Regras de coleta

Valem para todas as fontes, em `scraper/coleta.py`:

- **robots.txt** consultado antes de cada host de HTML. Um 404 no robots é
  tratado como "sem restrições" (é o caso do studyinitaly).
- **Endpoints RSS pulam a checagem de robots** — sindicação existe justamente
  para ser consumida por leitores de feed; `robots.txt` governa crawling de
  HTML.
- **User-Agent identificado**, com contato — nada de se passar por navegador.
- **Intervalo entre requisições** e **retry com backoff exponencial**
  (decorador `@retry_backoff`), para não martelar o servidor de origem.
- **Dedupe por URL**, em duas camadas: dentro do lote (`pipeline.dedupe_por_url`)
  e no banco (índice único em `noticias.url`).
- **Isolamento por fonte**: cada fonte roda em try/except próprio. Uma fonte
  fora do ar não impede as outras de coletar naquela rodada.

## Como adicionar uma fonte

1. Criar `scraper/sources/<fonte>.py` especializando o parser genérico com
   `functools.partial` — RSS via `parse_rss`, HTML via `parse_noticias_html`
   com um `SeletoresNoticia`.
2. Registrar em `PARSERS_NOTICIAS` (`scraper/sources/__init__.py`) — uma linha.
3. Adicionar a `FONTES_NOTICIAS` em `scraper/scheduler.py`, informando se a
   fonte exige checagem de robots.
4. Salvar uma fixture do HTML/XML real em `scraper/tests/fixtures/` e escrever
   o teste de contrato — **os testes do scraper nunca acessam a rede**.

O classificador de categorias (`pipeline.classificar`) é compartilhado: a
fonte nova já entra nos 10 tópicos da seção 7 sem código adicional.

## Classificação em tópicos

Palavras-chave em português, italiano e inglês mapeiam cada notícia para um
dos 10 tópicos (vistos, prazos, bolsas, idioma, moradia, finanças,
documentação, admissões, vida na Itália, mercado). Sem correspondência, a
notícia vira `geral` — visível no Radar, mas **fora da newsletter**, que por
definição da seção 7 só monta os 10 tópicos essenciais.
