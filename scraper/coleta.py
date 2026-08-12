"""Camada de I/O da coleta: robots.txt, User-Agent, intervalo e retry.

Regras da seção 6 do README: respeitar robots.txt, User-Agent identificado,
intervalo entre requisições e retry com backoff exponencial (reutiliza o
``@retry_backoff`` da api). As funções de espera e obtenção são injetáveis —
os testes exercitam a coleta inteira sem rede e sem dormir.
"""

from __future__ import annotations

import time
import urllib.robotparser
from collections.abc import Callable
from urllib.parse import urlparse

import httpx
from app.core.decoradores import retry_backoff

from scraper.sources import PARSERS, PARSERS_NOTICIAS
from scraper.sources.base import NoticiaColetada, UniversidadeColetada

USER_AGENT = "PonteItaliaBot/0.1 (+https://github.com/julianosfreitas/scrapping_italy)"
INTERVALO_SEGUNDOS = 2.0
TIMEOUT_SEGUNDOS = 30.0


class ColetaBloqueada(RuntimeError):
    """A fonte recusou a coleta (robots.txt ou challenge anti-bot)."""


def pode_raspar(robots_txt: str, url: str, agente: str = USER_AGENT) -> bool:
    """Função determinística: avalia um robots.txt JÁ BAIXADO contra a URL."""
    analisador = urllib.robotparser.RobotFileParser()
    analisador.parse(robots_txt.splitlines())
    return analisador.can_fetch(agente, url)


@retry_backoff(tentativas=3, atraso_base=1.0, excecoes=(httpx.HTTPError,))
def _obter_http(url: str) -> str:
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SEGUNDOS) as cliente:
        resposta = cliente.get(url, follow_redirects=True)
        resposta.raise_for_status()
        if resposta.status_code != 200 or not resposta.text.strip():
            raise ColetaBloqueada(
                f"{url} respondeu {resposta.status_code} sem conteúdo "
                "(possível challenge anti-bot — ver nota no parser da fonte)"
            )
        return resposta.text


def _obter_robots(url_robots: str, obter: Callable[[str], str]) -> str:
    """Baixa o robots.txt com a semântica padrão: 4xx (não existe) = tudo permitido."""
    try:
        return obter(url_robots)
    except httpx.HTTPStatusError as erro:
        if 400 <= erro.response.status_code < 500:
            return ""  # sem robots.txt -> sem restrições
        raise


def _coletar_paginas[T](
    parser: Callable[[str], tuple[T, ...]],
    urls: tuple[str, ...],
    obter: Callable[[str], str],
    dormir: Callable[[float], None],
    checar_robots: bool = True,
) -> tuple[T, ...]:
    """Coleta educada genérica: robots.txt primeiro, intervalo entre páginas.

    HOF: recebe o parser como valor — serve para universidades e notícias.
    ``checar_robots=False`` é reservado para endpoints DE SINDICAÇÃO (RSS):
    feeds são oferecidos para consumo por leitores; o robots.txt do host
    governa o crawling de páginas HTML, não a assinatura do próprio feed.
    """
    if not urls:
        return ()

    if checar_robots:
        raiz = urlparse(urls[0])
        robots_txt = _obter_robots(f"{raiz.scheme}://{raiz.netloc}/robots.txt", obter)
        bloqueadas = tuple(url for url in urls if not pode_raspar(robots_txt, url))
        if bloqueadas:
            raise ColetaBloqueada(f"robots.txt proíbe: {', '.join(bloqueadas)}")

    itens: list[T] = []
    for indice, url in enumerate(urls):
        if indice > 0:
            dormir(INTERVALO_SEGUNDOS)
        itens.extend(parser(obter(url)))
    return tuple(itens)


def coletar(
    fonte: str,
    urls: tuple[str, ...],
    obter: Callable[[str], str] = _obter_http,
    dormir: Callable[[float], None] = time.sleep,
) -> tuple[UniversidadeColetada, ...]:
    """Coleta de universidades com o parser do registry."""
    return _coletar_paginas(PARSERS[fonte], urls, obter, dormir)


def coletar_noticias(
    fonte: str,
    urls: tuple[str, ...],
    obter: Callable[[str], str] = _obter_http,
    dormir: Callable[[float], None] = time.sleep,
    checar_robots: bool = True,
) -> tuple[NoticiaColetada, ...]:
    """Coleta de notícias com o parser do registry de notícias."""
    return _coletar_paginas(PARSERS_NOTICIAS[fonte], urls, obter, dormir, checar_robots)
