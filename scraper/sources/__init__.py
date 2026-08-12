"""Registry de parsers: fontes → funções (funções de primeira classe).

O registry é um mapeamento IMUTÁVEL montado uma única vez: quem consome
(`scraper.coleta`) escolhe o parser pelo nome e o carrega como valor —
nenhum `if fonte == ...` espalhado pelo código. Novas fontes entram aqui
com uma linha.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from scraper.sources.base import Parser, ParserNoticias
from scraper.sources.google_news import parser_google_news
from scraper.sources.laziodisco import parser_laziodisco
from scraper.sources.studyinitaly import parser_studyinitaly
from scraper.sources.universitaly import parser_universitaly

PARSERS: Mapping[str, Parser] = MappingProxyType(
    {
        "universitaly": parser_universitaly,
    }
)

PARSERS_NOTICIAS: Mapping[str, ParserNoticias] = MappingProxyType(
    {
        "google_news": parser_google_news,
        "laziodisco": parser_laziodisco,
        "studyinitaly": parser_studyinitaly,
    }
)

__all__ = ["PARSERS", "PARSERS_NOTICIAS", "Parser", "ParserNoticias"]
