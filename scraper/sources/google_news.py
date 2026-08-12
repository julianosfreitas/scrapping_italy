"""Fonte Google News RSS (seção 6 do README) — queries documentadas."""

from __future__ import annotations

from functools import partial
from urllib.parse import quote

from scraper.sources.base import parse_rss

_QUERIES = ("studiare in Italia stranieri", "student visa Italy")


def _url_da_query(query: str, idioma: str, pais: str) -> str:
    return (
        "https://news.google.com/rss/search"
        f"?q={quote(query)}&hl={idioma}&gl={pais}&ceid={pais}:{idioma}"
    )


URLS_COLETA = (
    _url_da_query(_QUERIES[0], "it", "IT"),
    _url_da_query(_QUERIES[1], "en", "US"),
)

# conceito 11: o parser da fonte é o parser genérico de RSS parcializado.
parser_google_news = partial(parse_rss, fonte="google_news")
