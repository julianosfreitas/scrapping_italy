"""Fonte DISCO Lazio (laziodisco.it) — bolsas regionais DSU (seção 6 do README).

WordPress com markup de blocos: a busca por "bando" devolve os posts mais
recentes sobre bolsas de estudo com título, resumo, data e link.
"""

from __future__ import annotations

from functools import partial

from scraper.sources.base import SeletoresNoticia, parse_noticias_html

URLS_COLETA = ("https://www.laziodisco.it/?s=bando",)

SELETORES_LAZIODISCO = SeletoresNoticia(
    item="li.wp-block-post",
    titulo="h2.wp-block-post-title",
    link="h2.wp-block-post-title a",
    resumo="p.wp-block-post-excerpt__excerpt",
    data="div.wp-block-post-date",
)

parser_laziodisco = partial(
    parse_noticias_html,
    fonte="laziodisco",
    seletores=SELETORES_LAZIODISCO,
    idioma="it",
    base_url="https://www.laziodisco.it",
)
