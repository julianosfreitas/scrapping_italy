"""Paginação lazy (generators) — conceito 10."""

from itertools import count

from app.services.feed import janelas, paginar


def test_paginar_fatia_correta() -> None:
    itens = tuple(range(1, 26))
    assert paginar(itens, pagina=1, por_pagina=10) == tuple(range(1, 11))
    assert paginar(itens, pagina=3, por_pagina=10) == (21, 22, 23, 24, 25)
    assert paginar(itens, pagina=4, por_pagina=10) == ()


def test_paginar_e_lazy_ate_com_iteravel_infinito() -> None:
    """A prova da avaliação sob demanda: count() é INFINITO — se paginar
    materializasse o iterável, este teste jamais terminaria."""
    assert paginar(count(start=1), pagina=2, por_pagina=5) == (6, 7, 8, 9, 10)


def test_paginar_consome_apenas_o_necessario() -> None:
    consumidos: list[int] = []

    def instrumentado() -> "object":
        for n in range(1, 1000):
            consumidos.append(n)
            yield n

    paginar(instrumentado(), pagina=1, por_pagina=3)
    assert consumidos == [1, 2, 3]  # nada além da página foi produzido


def test_janelas_gera_lotes_sob_demanda() -> None:
    gerador = janelas(range(1, 8), tamanho=3)
    assert next(gerador) == (1, 2, 3)
    assert next(gerador) == (4, 5, 6)
    assert next(gerador) == (7,)
