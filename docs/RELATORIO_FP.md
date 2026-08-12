# Relatório — Programação Funcional em Python no projeto Ponte Italia

> Este documento é atualizado a CADA implementação que usa um conceito
> funcional. Ele é a base do relatório acadêmico e da apresentação
> (disciplina de Paradigmas — Programação Funcional em Python).
>
> Formato de cada entrada: conceito → onde está no código → trecho →
> por que o estilo funcional ajudou → (opcional) versão imperativa
> equivalente para comparação.

## Índice de conceitos demonstrados

| # | Conceito | Status | Onde |
|---|----------|--------|------|
| 1 | Funções puras | ✅ implementado | **CENTRAL: `calcular_gap` em `api/app/services/comparativo.py`**; também `calcular_status`, `parse_env_linhas`, `faltantes` |
| 2 | Imutabilidade (`frozen=True`) | ✅ implementado | schemas Pydantic (`ConfigDict(frozen=True)`) em `api/app/schemas/`, `Settings` e `EstudanteSeed` (dataclasses) |
| 3 | Funções de primeira classe | ✅ implementado | registry `PARSERS` em `scraper/sources/__init__.py` |
| 4 | Funções de alta ordem (HOF) | ✅ implementado | **CENTRAL: `processar` em `scraper/pipeline.py`** (composição map→filter→dedupe→map); também `agrupar_por_categoria`, `_coletar_paginas`, `ordenar_por_prazo` |
| 5 | Transparência referencial | ✅ implementado | `calcular_status` (relógio injetado) + justificativa do cache em `requisitos_por_categoria` (entrada 12) |
| 6 | lambda | ✅ implementado | `sorted(key=lambda ...)` em `ordenar_por_prazo` (`api/app/services/cursos.py`) |
| 7 | map / filter | ✅ implementado | `processar` e `filtrar_por_categoria` em `scraper/pipeline.py` |
| 8 | functools.reduce | ✅ implementado | `estatisticas` em `scraper/pipeline.py` (score de prontidão já coberto pelo percentual do Gap) |
| 9 | Comprehensions | ✅ implementado | normalização de scraping: `parse_rss`, `parse_noticias_html`, `parse_universidades` (`scraper/sources/base.py`) |
| 10 | Generators / lazy | ✅ implementado | `iterar_itens_rss` (`scraper/sources/base.py`) + `paginar`/`janelas` (`api/app/services/feed.py`) |
| 11 | functools.partial | ✅ implementado | `parser_universitaly` em `scraper/sources/universitaly.py` |
| 12 | functools.lru_cache | ✅ implementado | `requisitos_por_categoria` em `api/app/services/comparativo.py` (+ `get_settings`) |
| 13 | Closures | ✅ implementado | `retry_backoff` em `api/app/core/decoradores.py` |
| 14 | Decoradores (@wraps) | ✅ implementado | `@cronometrar`, `@retry_backoff` e `@exigir_auth` (`api/app/core/seguranca.py`) |
| 15 | Recursão | ⬜ pendente | árvore de categorias do FAQ |
| 16 | Comparação imperativo × funcional | ⬜ pendente | estudo de caso do relatório |

Legenda: ⬜ pendente · 🟨 parcial · ✅ implementado e documentado

---

## Entradas

<!-- MODELO DE ENTRADA — copiar e preencher:

### [N]. <Conceito> — <nome curto da funcionalidade>

**Onde:** `caminho/do/arquivo.py` → `nome_da_funcao()`
**Sprint:** X · **Commit:** <hash curto>

```python
# trecho de 5–15 linhas
```

**Por que funcional ajudou:** 2–4 frases (testabilidade, cache seguro,
paralelismo, legibilidade, ausência de efeitos colaterais...).

**Equivalente imperativo (opcional):**

```python
# versão com loop/estado mutável, para o slide de comparação
```
-->

### 14. Decorador com `functools.wraps` — `@cronometrar`

**Onde:** `api/app/core/decoradores.py` → `cronometrar()`
**Sprint:** 1 · **Commit:** `630b54c`

```python
def cronometrar[**P, R](funcao: Callable[P, R]) -> Callable[P, R]:
    """Loga a duração da chamada, preservando assinatura e metadados (@wraps)."""

    @wraps(funcao)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        inicio = time.perf_counter()
        try:
            return funcao(*args, **kwargs)
        finally:
            duracao_ms = (time.perf_counter() - inicio) * 1000
            logger.info("%s levou %.1f ms", funcao.__qualname__, duracao_ms)

    return wrapper
```

**Por que funcional ajudou:** funções são valores de primeira classe em Python,
então o decorador recebe uma função e devolve outra que a envolve — a medição
de tempo vira uma preocupação transversal reutilizável, sem duplicar
`time.perf_counter()` dentro de cada função de negócio. O `functools.wraps`
preserva `__name__`, `__doc__` e assinatura, mantendo introspecção e docs do
FastAPI intactas. O `try/finally` garante a medição mesmo quando a função
decorada lança exceção — comportamento coberto por teste.

### 13. Closure parametrizada — fábrica de decoradores `retry_backoff`

**Onde:** `api/app/core/decoradores.py` → `retry_backoff()`
**Sprint:** 1 · **Commit:** `630b54c`

```python
def retry_backoff[**P, R](
    tentativas: int = 3,
    atraso_base: float = 0.5,
    fator: float = 2.0,
    excecoes: tuple[type[BaseException], ...] = (Exception,),
    dormir: Callable[[float], None] = time.sleep,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorador(funcao: Callable[P, R]) -> Callable[P, R]:
        @wraps(funcao)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for tentativa in range(tentativas):
                try:
                    return funcao(*args, **kwargs)
                except excecoes:
                    if tentativa == tentativas - 1:
                        raise
                    dormir(atraso_base * fator**tentativa)
        return wrapper
    return decorador
```

**Por que funcional ajudou:** `retry_backoff(...)` é uma fábrica: cada chamada
cria uma closure que captura sua própria configuração (tentativas, atraso,
fator), então duas funções decoradas têm políticas independentes sem nenhum
estado global — propriedade verificada por teste. A função de espera `dormir`
é injetada como argumento (função como valor), o que permite testar a
sequência exata de backoff `[0.1, 0.2, 0.4…]` sem dormir de verdade nem
mockar módulos.

**Equivalente imperativo:** sem closures, a configuração de retry viria de
constantes globais ou de uma classe com atributos mutáveis
(`RetryHelper.max_tentativas = 3`), compartilhada entre chamadores — qualquer
ajuste em um ponto vazaria para os demais, e o teste exigiria patch de
`time.sleep` global.

---

### 1. Função pura — `calcular_status` do cofre de documentos

**Onde:** `api/app/services/documentos.py` → `calcular_status()`
**Sprint:** 2 · **Commit:** `86cfed6`

```python
def calcular_status(
    data_validade: date | None,
    data_atual: date,
    janela_vencendo_dias: int = JANELA_VENCENDO_DIAS,
) -> StatusDocumento:
    if data_validade is None:
        return StatusDocumento.OK
    if data_validade < data_atual:
        return StatusDocumento.VENCIDO
    if data_validade <= data_atual + timedelta(days=janela_vencendo_dias):
        return StatusDocumento.VENCENDO
    return StatusDocumento.OK
```

**Por que funcional ajudou:** o status NÃO é coluna no banco — é derivado no
momento da leitura, então nunca fica defasado (um documento que venceu ontem
aparece como vencido hoje sem nenhum job de atualização). A data atual entra
como parâmetro em vez de `date.today()` dentro da função: isso a torna
determinística e permitiu uma bateria de testes de fronteira (vence hoje,
vence em exatos 30 dias, em 31, sem validade) fixando `data_atual` — nenhum
teste depende do relógio da máquina.

**Equivalente imperativo:** persistir `status` na tabela e atualizá-lo por
rotina agendada (cron) ou em cada escrita — duas fontes de verdade, status
defasado entre execuções e testes dependentes de estado do banco.

### 5. Transparência referencial — mesma entrada, mesma saída

**Onde:** `api/app/services/documentos.py` → `calcular_status()` · teste
`test_transparencia_referencial` em `api/tests/test_status_documento.py`
**Sprint:** 2 · **Commit:** `86cfed6`

```python
def test_transparencia_referencial() -> None:
    resultados = {calcular_status(HOJE + timedelta(days=10), HOJE) for _ in range(100)}
    assert resultados == {StatusDocumento.VENCENDO}
```

**Por que funcional ajudou:** como a função não lê relógio, banco nem estado
global, qualquer chamada pode ser substituída pelo seu valor sem mudar o
programa — a definição operacional de transparência referencial. É essa
propriedade que torna seguro memoizar resultados (base do `lru_cache` que o
comparativo da Sprint 3 vai explorar) e paralelizar chamadas sem lock.

### 2. Imutabilidade — schemas Pydantic congelados

**Onde:** `api/app/schemas/` (todos os schemas) → `ConfigDict(frozen=True)`
**Sprint:** 2 · **Commit:** `6cc100b`

```python
class _Congelado(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)


class EstudanteCriar(_Congelado):
    nome: str = Field(min_length=2, max_length=120)
    email: str = Field(pattern=PADRAO_EMAIL, max_length=255)
    senha: str = Field(min_length=8, max_length=128)
```

**Por que funcional ajudou:** os DTOs que atravessam a API são imutáveis por
construção — tentar `dados.email = "x"` levanta erro em vez de introduzir um
bug silencioso. Um schema recebido por um router pode ser passado a qualquer
função sem cópia defensiva, porque ninguém consegue alterá-lo; edições
parciais geram um novo dict via `model_dump(exclude_unset=True)` em vez de
mutar o objeto.

### 14b. Decorador de autorização — `@exigir_auth`

**Onde:** `api/app/core/seguranca.py` → `exigir_auth()`
**Sprint:** 2 · **Commit:** `2403005`

```python
def exigir_auth[**P, R](funcao: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    @wraps(funcao)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        request = next(
            (v for v in (*args, *kwargs.values()) if isinstance(v, Request)), None
        )
        payload = decodificar_token(_extrair_bearer(request), get_settings().jwt_segredo)
        request.state.estudante_id = int(payload["sub"])
        return await funcao(*args, **kwargs)
    return wrapper
```

**Por que funcional ajudou:** a autorização é uma preocupação transversal —
como função de alta ordem, ela envolve qualquer endpoint sem que ele conheça
JWT: o endpoint recebe `request.state.estudante_id` já validado. O `@wraps`
preserva a assinatura, essencial aqui porque o FastAPI inspeciona os
parâmetros do endpoint para montar a injeção de dependências e a
documentação OpenAPI.

### 1 (CENTRAL). Função pura — `calcular_gap`, o comparativo de documentos

**Onde:** `api/app/services/comparativo.py` → `calcular_gap()`
**Sprint:** 3 · **Commit:** `ea7bae5`

```python
def calcular_gap(
    requisitos: tuple[Requisito, ...],
    documentos: tuple[DocumentoResumo, ...],
) -> Gap:
    docs_por_categoria = agrupar_por_categoria(documentos, lambda d: d.categoria)
    avaliacoes = tuple(
        _avaliar(requisito, docs_por_categoria.get(categoria, ()))
        for categoria, do_grupo in requisitos_por_categoria(requisitos).items()
        for requisito in do_grupo
    )
    return Gap(
        atendidos=tuple(i for s, i in avaliacoes if s == "atendido"),
        faltando=tuple(i for s, i in avaliacoes if s == "faltando"),
        vencendo=tuple(i for s, i in avaliacoes if s == "vencendo"),
    )
```

**Por que funcional ajudou:** este é o cálculo mais importante do produto — é
ele que diz ao estudante o que falta para se candidatar — e é uma função sem
NENHUM efeito colateral: recebe tuplas de dataclasses congeladas, devolve um
`Gap` congelado, não conhece banco, HTTP nem relógio (o status dos documentos
chega já derivado por `calcular_status`, outra função pura — composição). As
consequências práticas:

1. **Testabilidade total**: a bateria de 14 testes cobre todos os cruzamentos
   (ok/vencendo/vencido/ausente, precedências, partição completa) sem mock,
   sem fixture de banco, sem setup — cada teste são três linhas.
2. **Nenhum estado para dar errado**: dois requests simultâneos, ou dois
   estudantes comparando o mesmo curso, não compartilham nada mutável — o
   paralelismo é seguro por construção.
3. **Raciocínio local**: a regra de negócio inteira (OK atende > VENCENDO
   alerta > resto falta) está em `_avaliar`, legível em 10 linhas, sem
   `SELECT` no meio.
4. **Reuso de HOF**: o agrupamento por categoria é o mesmo
   `agrupar_por_categoria` do cofre — a função recebe a chave como função
   (`lambda d: d.categoria`) e serve aos dois domínios.

**Equivalente imperativo (para o slide de comparação):**

```python
# Versão acoplada: consulta ao banco no meio do cálculo, listas mutadas,
# impossível de testar sem MySQL de pé e dados semeados.
def calcular_gap_imperativo(curso_id, estudante_id, sessao):
    atendidos, faltando, vencendo = [], [], []
    requisitos = sessao.execute(
        "SELECT * FROM requisitos_curso WHERE curso_id = %s", curso_id
    )
    for req in requisitos:
        docs = sessao.execute(  # N+1: uma query por requisito
            "SELECT * FROM documentos WHERE estudante_id = %s AND categoria = %s",
            (estudante_id, req.categoria),
        )
        achou = False
        for doc in docs:
            if doc.status == "ok":        # status defasado lido do banco!
                atendidos.append(req)
                achou = True
                break
        if not achou:
            ...  # mais flags e appends aninhados
    return {"atendidos": atendidos, "faltando": faltando, "vencendo": vencendo}
```

A versão imperativa mistura três responsabilidades (buscar, derivar status,
particionar), depende de um `status` persistido que envelhece, e cada teste
precisa montar um banco. A versão pura separa o I/O (routers) do cálculo e
faz o cálculo ser trivialmente verificável.

### 12. `functools.lru_cache` — índice de requisitos por curso

**Onde:** `api/app/services/comparativo.py` → `requisitos_por_categoria()`
**Sprint:** 3 · **Commit:** `ea7bae5`

```python
@lru_cache(maxsize=256)
def requisitos_por_categoria(
    requisitos: tuple[Requisito, ...],
) -> Mapping[CategoriaDocumento, tuple[Requisito, ...]]:
    return MappingProxyType(agrupar_por_categoria(requisitos, lambda r: r.categoria))
```

**Por que funcional ajudou (a parte que faltava do conceito 5):** memoizar só
é CORRETO quando a função é referencialmente transparente — e aqui os três
pré-requisitos são garantidos pelo desenho: (a) entrada hashável e imutável
(tupla de dataclasses congeladas), (b) função determinística sem efeitos,
(c) saída imutável (`MappingProxyType`), então compartilhar o resultado entre
chamadores não cria acoplamento. O mesmo curso é comparado por muitos
estudantes: a indexação roda uma vez por curso, não uma vez por request — e o
teste comprova com `cache_info()` que a segunda chamada é *hit* e devolve o
MESMO objeto. Cachear uma função impura (que lesse o banco) seria um bug de
dados obsoletos; cachear esta é apenas otimização invisível.

### 3. Funções de primeira classe — registry de parsers

**Onde:** `scraper/sources/__init__.py` → `PARSERS`
**Sprint:** 3 · **Commit:** `14f5211`

```python
PARSERS: Mapping[str, Parser] = MappingProxyType(
    {
        "universitaly": parser_universitaly,
    }
)

# consumo em scraper/coleta.py:
parser = PARSERS[fonte]   # a função é um VALOR escolhido por nome
universidades = parser(html)
```

**Por que funcional ajudou:** parsers são valores num mapeamento imutável —
`coletar()` seleciona o parser por nome e o invoca sem nenhum
`if fonte == "universitaly"` espalhado. Fonte nova (Sprint 4) é uma linha no
registry; o código de coleta não muda. O `MappingProxyType` impede mutação em
runtime — o registry é montado uma vez, no import, e vira dado somente-leitura.

### 11. `functools.partial` — parser especializado por fonte

**Onde:** `scraper/sources/universitaly.py` → `parser_universitaly`
**Sprint:** 3 · **Commit:** `14f5211`

```python
parser_universitaly = partial(
    parse_universidades, fonte="universitaly", seletores=SELETORES_UNIVERSITALY
)
```

**Por que funcional ajudou:** o parser genérico (`parse_universidades`) sabe
transformar HTML em tuplas imutáveis dados os seletores; cada fonte é só uma
APLICAÇÃO PARCIAL dele com a configuração pré-preenchida — sem subclasse, sem
copiar código, sem `self`. O teste verifica inclusive que
`parser_universitaly.keywords["fonte"] == "universitaly"`: a especialização é
um dado inspecionável, não uma hierarquia de classes.

### 6. lambda — ordenação de cursos por prazo

**Onde:** `api/app/services/cursos.py` → `ordenar_por_prazo()`
**Sprint:** 3 · **Commit:** `ea7bae5`

```python
def ordenar_por_prazo[T](
    cursos: Iterable[T], prazo_de: Callable[[T], date | None]
) -> tuple[T, ...]:
    return tuple(sorted(cursos, key=lambda c: (prazo_de(c) is None, prazo_de(c) or date.max)))
```

**Por que funcional ajudou:** a lambda como argumento de `sorted` expressa a
regra de ordenação inteira — "quem tem prazo vem antes, prazo mais próximo
primeiro" — em uma tupla-chave, sem loop de comparação manual. Seguindo a
PEP 8 (regra do CLAUDE.md), a lambda só aparece inline como argumento; a
função nomeada `ordenar_por_prazo` é um `def`. Os chamadores passam o extrator
de prazo (`lambda c: c.prazo_inscricao`), então a MESMA ordenação serve para
cursos ORM e para associações — outra HOF na prática.

### 4 (CENTRAL). Funções de alta ordem — o pipeline de limpeza do Radar

**Onde:** `scraper/pipeline.py` → `processar()`
**Sprint:** 4 · **Commit:** `ccbbfb8`

```python
def processar(brutas: tuple[NoticiaColetada, ...]) -> tuple[NoticiaColetada, ...]:
    normalizadas = map(normalizar, brutas)
    validas = filter(eh_valida, normalizadas)
    unicas = dedupe_por_url(tuple(validas))
    return tuple(map(classificar, unicas))
```

**Por que funcional ajudou:** o pipeline inteiro é a COMPOSIÇÃO de quatro
funções puras nomeadas — `normalizar`, `eh_valida`, `dedupe_por_url`,
`classificar` — passadas como valores para `map`/`filter`. Cada etapa é
testada isolada em três linhas; a composição é testada como um todo; e trocar
a ordem, remover ou acrescentar uma etapa é editar UMA linha, não desemaranhar
um loop de 40 linhas com flags. Como nenhuma etapa tem efeito colateral,
notícias de fontes diferentes podem atravessar o pipeline em qualquer ordem —
ou em paralelo — com o mesmo resultado. A infraestrutura de coleta usa o
mesmo princípio: `_coletar_paginas(parser, urls, obter, dormir)` recebe
TODAS as suas dependências como funções, e é por isso que os 34 testes do
scraper rodam sem rede e sem dormir.

### 7. `map`/`filter` — limpeza declarativa

**Onde:** `scraper/pipeline.py` → `processar()`, `filtrar_por_categoria()`
**Sprint:** 4 · **Commit:** `ccbbfb8`

```python
def filtrar_por_categoria(
    noticias: tuple[NoticiaColetada, ...], categoria: str
) -> tuple[NoticiaColetada, ...]:
    return tuple(filter(lambda n: n.categoria == categoria, noticias))
```

**Por que funcional ajudou:** `map` e `filter` declaram O QUE acontece com a
coleção (transformar, peneirar) sem gerenciar COMO (índices, appends,
continues). São lazy: em `processar`, nenhuma lista intermediária é
materializada entre a normalização e a validação — os itens fluem um a um
até a tupla final. O predicado é dado como lambda inline (PEP 8) ou função
nomeada, o que os torna reutilizáveis e testáveis por si.

### 8. `functools.reduce` — estatísticas da coleta

**Onde:** `scraper/pipeline.py` → `estatisticas()`
**Sprint:** 4 · **Commit:** `ccbbfb8`

```python
def _acumular(acc: Mapping[str, int], noticia: NoticiaColetada) -> Mapping[str, int]:
    fonte = f"fonte:{noticia.fonte}"
    categoria = f"categoria:{noticia.categoria}"
    return {
        **acc,
        "total": acc.get("total", 0) + 1,
        fonte: acc.get(fonte, 0) + 1,
        categoria: acc.get(categoria, 0) + 1,
    }

def estatisticas(noticias: tuple[NoticiaColetada, ...]) -> Mapping[str, int]:
    vazio: Mapping[str, int] = {}
    resultado: Mapping[str, int] = reduce(_acumular, noticias, vazio)
    return MappingProxyType(dict(resultado))
```

**Por que funcional ajudou:** `reduce` dobra a coleção inteira num único
valor com UMA regra local (`_acumular`): dado o acumulado e um item, produz
um NOVO acumulado — sem `total += 1` espalhado, sem dict global mutado. Na
coleta real da sprint, foi este reduce que produziu
`{'total': 111, 'fonte:google_news': 100, 'categoria:vistos': 31, ...}` de
uma passada. O resultado sai como `MappingProxyType`: quem recebe não
consegue corromper os contadores.

### 9. Comprehensions — normalização do scraping

**Onde:** `scraper/sources/base.py` → `parse_rss()`, `parse_noticias_html()`
**Sprint:** 4 · **Commit:** `943254f`

```python
return tuple(
    NoticiaColetada(
        titulo=titulo,
        url=url if url.startswith("http") else f"{base_url}{url}",
        fonte=fonte,
        resumo=_texto(bloco, seletores.resumo),
        ...
    )
    for bloco in sopa.select(seletores.item)
    if (titulo := _texto(bloco, seletores.titulo)) is not None
    and (url := _atributo_href(bloco, seletores.link)) is not None
)
```

**Por que funcional ajudou:** a comprehension expressa transformação E
filtragem numa única construção declarativa — "para cada bloco que tem
título e link, construa uma NoticiaColetada" — em vez de loop + append +
continue. O walrus (`:=`) evita extrair o mesmo campo duas vezes, e o
resultado nasce direto como tupla imutável. Blocos malformados (sem título,
sem link) simplesmente não passam pelo `if` — o caso de erro não precisa de
código.

### 10. Generators — leitura lazy e paginação sob demanda

**Onde:** `scraper/sources/base.py` → `iterar_itens_rss()` ·
`api/app/services/feed.py` → `paginar()`, `janelas()`
**Sprint:** 4 · **Commit:** `943254f` / `fcc3004`

```python
def iterar_itens_rss(xml: str) -> Iterator[dict[str, str | None]]:
    raiz = ElementTree.fromstring(xml)
    idioma_feed = raiz.findtext("channel/language")
    for item in raiz.iterfind("channel/item"):
        yield { "titulo": item.findtext("title"), ... }

def paginar[T](itens: Iterable[T], pagina: int, por_pagina: int) -> tuple[T, ...]:
    inicio = (pagina - 1) * por_pagina
    return tuple(islice(itens, inicio, inicio + por_pagina))
```

**Por que funcional ajudou (memória/lazy evaluation):** o generator produz um
item por vez, quando pedido — o feed do Google News chega com dezenas de
itens, mas só os `maximo_itens` consumidos pelo `islice` viram objetos. Na
API, `paginar` recebe o `Result` lazy do SQLAlchemy e consome SÓ as linhas
da página: o teste `test_paginar_e_lazy_ate_com_iteravel_infinito` pagina
`itertools.count()` — um iterável INFINITO — e termina, o que seria
impossível se a função materializasse a entrada. Outro teste instrumentado
prova que, pedida a página 1 de 3 itens, exatamente 3 itens são produzidos
de um gerador de 999. `janelas()` complementa: um gerador de páginas
consecutivas que a newsletter (Sprint 5) consumirá lote a lote.

---

### Nota da Sprint 1 — conceitos tocados parcialmente

- **Funções puras (1):** `parse_env_linhas` (linhas → dict, sem I/O),
  `montar_settings` (dict → Settings) e `faltantes` no seed (candidatos ×
  e-mails existentes → tupla dos que faltam). O I/O de arquivo/banco fica em
  funções separadas (`_ler_ambiente`, `executar_seed`), mantendo o cálculo
  determinístico e testado sem mocks.
- **Imutabilidade (2):** `Settings` e `EstudanteSeed` são
  `@dataclass(frozen=True)` — o snapshot de configuração pode ser cacheado e
  compartilhado sem risco de mutação.
- **lru_cache (12):** `get_settings()` usa `@lru_cache(maxsize=1)`; o cache só
  é seguro porque o retorno é imutável — a justificativa de transparência
  referencial entra no exemplo central da Sprint 3.

Os exemplos centrais desses conceitos (comparativo de documentos, requisitos
por curso) continuam planejados para a Sprint 3, quando ganham entrada própria.
