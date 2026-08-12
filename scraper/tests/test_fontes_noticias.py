"""Parsers de notícias: RSS e HTML via fixtures; generators lazy."""

import functools
from datetime import datetime
from pathlib import Path

from scraper.sources import PARSERS_NOTICIAS
from scraper.sources.base import iterar_itens_rss, parse_data_rfc822
from scraper.sources.google_news import parser_google_news
from scraper.sources.laziodisco import parser_laziodisco

_FIXTURES = Path(__file__).parent / "fixtures"
RSS = (_FIXTURES / "google_news.xml").read_text(encoding="utf-8")
LAZIODISCO = (_FIXTURES / "laziodisco_busca.html").read_text(encoding="utf-8")


# ── RSS (Google News) ────────────────────────────────────


def test_parse_rss_google_news() -> None:
    noticias = parser_google_news(RSS)
    assert len(noticias) == 2  # item sem título é descartado
    primeira = noticias[0]
    assert primeira.titulo.startswith("Borse di studio 2026")
    assert primeira.url == "https://esempio.it/borse-2026"
    assert primeira.fonte == "google_news"
    assert primeira.idioma == "it"
    assert primeira.publicada_em == datetime(2026, 8, 11, 8, 30)


def test_parse_data_rfc822_invalida() -> None:
    assert parse_data_rfc822("data qualquer") is None
    assert parse_data_rfc822(None) is None


def test_iterar_itens_rss_e_lazy() -> None:
    """GERADOR: nada é consumido antes do next() — avaliação sob demanda."""
    gerador = iterar_itens_rss(RSS)
    assert (next(gerador)["titulo"] or "").startswith("Borse")
    assert (next(gerador)["titulo"] or "").startswith("Permesso")
    # o 3º item existe mas nunca foi materializado até aqui — quem controla
    # o consumo é o chamador, item a item


# ── HTML (laziodisco) ────────────────────────────────────


def test_parse_laziodisco() -> None:
    noticias = parser_laziodisco(LAZIODISCO)
    assert len(noticias) == 2  # bloco sem título/link é descartado
    assert noticias[0].url == "https://laziodisco.it/news-it/chiuso-il-bando-diritto-allo-studio"
    assert noticias[1].url.startswith("https://www.laziodisco.it/news-it/")  # relativo resolvido
    assert noticias[0].publicada_em == datetime(2026, 8, 11)
    assert noticias[0].fonte == "laziodisco"
    assert noticias[0].resumo is not None and "12:00" in noticias[0].resumo


# ── registry e partial ───────────────────────────────────


def test_registry_de_noticias_completo() -> None:
    assert set(PARSERS_NOTICIAS) == {"google_news", "laziodisco", "studyinitaly"}
    assert all(callable(parser) for parser in PARSERS_NOTICIAS.values())


def test_parsers_de_noticias_sao_partials_do_generico() -> None:
    assert isinstance(parser_google_news, functools.partial)
    assert parser_google_news.keywords["fonte"] == "google_news"
    assert isinstance(parser_laziodisco, functools.partial)
    assert parser_laziodisco.keywords["fonte"] == "laziodisco"
