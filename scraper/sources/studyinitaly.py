"""Fonte Study in Italy / MAECI (studyinitaly.esteri.it) — seção 6 do README.

A página /ListaBandi anuncia o estado das calls de bolsas MAECI. O conteúdo
é raso quando não há call aberta (linhas informativas + links), mas é a
fonte oficial: quando a call 2026/2027 abrir, os itens aparecem aqui.
"""

from __future__ import annotations

from functools import partial

from scraper.sources.base import SeletoresNoticia, parse_noticias_html

URLS_COLETA = ("https://studyinitaly.esteri.it/ListaBandi",)

SELETORES_STUDYINITALY = SeletoresNoticia(
    item="div.row:has(> div a[href])",
    titulo="a[href]",
    link="a[href]",
    resumo=None,
    data=None,
)

parser_studyinitaly = partial(
    parse_noticias_html,
    fonte="studyinitaly",
    seletores=SELETORES_STUDYINITALY,
    idioma="en",
    base_url="https://studyinitaly.esteri.it",
)
