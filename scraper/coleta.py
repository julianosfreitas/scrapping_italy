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

from scraper.sources import PARSERS
from scraper.sources.base import UniversidadeColetada

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


def coletar(
    fonte: str,
    urls: tuple[str, ...],
    obter: Callable[[str], str] = _obter_http,
    dormir: Callable[[float], None] = time.sleep,
) -> tuple[UniversidadeColetada, ...]:
    """Coleta educada: robots.txt primeiro, intervalo entre páginas, parser do registry."""
    parser = PARSERS[fonte]  # função de primeira classe vinda do registry
    if not urls:
        return ()

    raiz = urlparse(urls[0])
    robots_txt = obter(f"{raiz.scheme}://{raiz.netloc}/robots.txt")
    bloqueadas = tuple(url for url in urls if not pode_raspar(robots_txt, url))
    if bloqueadas:
        raise ColetaBloqueada(f"robots.txt proíbe: {', '.join(bloqueadas)}")

    universidades: list[UniversidadeColetada] = []
    for indice, url in enumerate(urls):
        if indice > 0:
            dormir(INTERVALO_SEGUNDOS)
        universidades.extend(parser(obter(url)))
    return tuple(universidades)
