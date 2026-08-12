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
| 1 | Funções puras | ⬜ pendente | `api/app/services/comparativo.py` (planejado) |
| 2 | Imutabilidade (`frozen=True`) | ⬜ pendente | schemas Pydantic / dataclasses |
| 3 | Funções de primeira classe | ⬜ pendente | registry de parsers do scraper |
| 4 | Funções de alta ordem (HOF) | ⬜ pendente | pipeline de limpeza de notícias |
| 5 | Transparência referencial | ⬜ pendente | justificativa do `lru_cache` |
| 6 | lambda | ⬜ pendente | `sorted(key=...)` no ranking |
| 7 | map / filter | ⬜ pendente | `scraper/pipeline.py` |
| 8 | functools.reduce | ⬜ pendente | score de prontidão do estudante |
| 9 | Comprehensions | ⬜ pendente | normalização de scraping |
| 10 | Generators / lazy | ⬜ pendente | paginação do feed |
| 11 | functools.partial | ⬜ pendente | parsers especializados por fonte |
| 12 | functools.lru_cache | ⬜ pendente | requisitos por curso |
| 13 | Closures | ⬜ pendente | fábrica de rate-limiter |
| 14 | Decoradores (@wraps) | ⬜ pendente | `@retry_backoff`, `@cronometrar` |
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
