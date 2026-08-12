"""Paginação lazy do feed — generators (avaliação sob demanda).

`paginar` recebe QUALQUER iterável — inclusive um generator infinito — e só
consome os itens necessários para a página pedida: `islice` avança sem
materializar o restante. Com o `Result` do SQLAlchemy (que também é lazy),
as linhas além da página nunca chegam a virar objetos Python.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from itertools import islice

TAMANHO_PAGINA_PADRAO = 10
TAMANHO_PAGINA_MAXIMO = 50


def paginar[T](itens: Iterable[T], pagina: int, por_pagina: int) -> tuple[T, ...]:
    """Fatia lazy: consome no máximo `pagina * por_pagina` itens do iterável."""
    inicio = (pagina - 1) * por_pagina
    return tuple(islice(itens, inicio, inicio + por_pagina))


def janelas[T](itens: Iterable[T], tamanho: int) -> Iterator[tuple[T, ...]]:
    """GERADOR de páginas consecutivas — cada `next()` produz uma janela.

    Usado para varrer o feed em lotes (ex.: montagem da newsletter na
    Sprint 5) mantendo em memória apenas a janela corrente.
    """
    iterador = iter(itens)
    while janela := tuple(islice(iterador, tamanho)):
        yield janela
