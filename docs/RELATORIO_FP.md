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
| 1 | Funções puras | 🟨 parcial | `api/app/core/config.py` (`parse_env_linhas`, `montar_settings`), `api/app/seed.py` (`faltantes`); exemplo central em `api/app/services/comparativo.py` (planejado, Sprint 3) |
| 2 | Imutabilidade (`frozen=True`) | 🟨 parcial | `Settings` em `api/app/core/config.py`, `EstudanteSeed` em `api/app/seed.py` |
| 3 | Funções de primeira classe | ⬜ pendente | registry de parsers do scraper |
| 4 | Funções de alta ordem (HOF) | ⬜ pendente | pipeline de limpeza de notícias |
| 5 | Transparência referencial | ⬜ pendente | justificativa do `lru_cache` |
| 6 | lambda | ⬜ pendente | `sorted(key=...)` no ranking |
| 7 | map / filter | ⬜ pendente | `scraper/pipeline.py` |
| 8 | functools.reduce | ⬜ pendente | score de prontidão do estudante |
| 9 | Comprehensions | ⬜ pendente | normalização de scraping |
| 10 | Generators / lazy | ⬜ pendente | paginação do feed |
| 11 | functools.partial | ⬜ pendente | parsers especializados por fonte |
| 12 | functools.lru_cache | 🟨 parcial | `get_settings()` em `api/app/core/config.py`; exemplo central (requisitos por curso) na Sprint 3 |
| 13 | Closures | ✅ implementado | `retry_backoff` em `api/app/core/decoradores.py` |
| 14 | Decoradores (@wraps) | ✅ implementado | `@cronometrar` e `@retry_backoff` em `api/app/core/decoradores.py` |
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
