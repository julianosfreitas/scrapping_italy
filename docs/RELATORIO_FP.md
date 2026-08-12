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
| 1 | Funções puras | ✅ implementado | `calcular_status` em `api/app/services/documentos.py`; também `parse_env_linhas`, `montar_settings`, `faltantes`; comparativo (Sprint 3) será o 2º exemplo central |
| 2 | Imutabilidade (`frozen=True`) | ✅ implementado | schemas Pydantic (`ConfigDict(frozen=True)`) em `api/app/schemas/`, `Settings` e `EstudanteSeed` (dataclasses) |
| 3 | Funções de primeira classe | ⬜ pendente | registry de parsers do scraper |
| 4 | Funções de alta ordem (HOF) | 🟨 parcial | `agrupar_por_categoria(itens, categoria_de)` em `api/app/services/documentos.py`; pipeline de notícias (Sprint 4) será o exemplo central |
| 5 | Transparência referencial | ✅ implementado | `calcular_status` com relógio injetado (entrada 5); justificativa do `lru_cache` se aprofunda na Sprint 3 |
| 6 | lambda | ⬜ pendente | `sorted(key=...)` no ranking |
| 7 | map / filter | ⬜ pendente | `scraper/pipeline.py` |
| 8 | functools.reduce | ⬜ pendente | score de prontidão do estudante |
| 9 | Comprehensions | ⬜ pendente | normalização de scraping |
| 10 | Generators / lazy | ⬜ pendente | paginação do feed |
| 11 | functools.partial | ⬜ pendente | parsers especializados por fonte |
| 12 | functools.lru_cache | 🟨 parcial | `get_settings()` em `api/app/core/config.py`; exemplo central (requisitos por curso) na Sprint 3 |
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
