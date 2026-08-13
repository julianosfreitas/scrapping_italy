"""Agendamento do Radar e da newsletter (APScheduler, seções 4 e 7 do README).

Uso: ``PONTE_EMAIL=... PONTE_SENHA=... python -m scraper.scheduler``

Dois jobs no mesmo agendador, ambos no fuso America/Recife:

- **coleta do Radar** — intervalo de ``RADAR_INTERVALO_MINUTOS`` (padrão 180);
- **curadoria da newsletter** — cron diário às ``NEWSLETTER_HORA_CURADORIA``
  (padrão 08h30), meia hora antes do disparo das 09h feito pelo worker .NET.

Os jobs compõem peças já testadas: coleta educada por fonte → pipeline
funcional de limpeza → ingestão via API autenticada. ``@cronometrar`` (da
Sprint 1) loga a duração de cada execução.
"""

from __future__ import annotations

import logging
import os
import sys

from app.core.decoradores import cronometrar
from apscheduler.schedulers.blocking import BlockingScheduler

from scraper import pipeline
from scraper.coleta import ColetaBloqueada, coletar_noticias
from scraper.ingestao import API_PADRAO, disparar_curadoria, ingerir_noticias, obter_token
from scraper.sources import google_news, laziodisco, studyinitaly
from scraper.sources.base import NoticiaColetada

logger = logging.getLogger("scraper.scheduler")

# (fonte, urls, checar_robots) — RSS pula robots: é endpoint de sindicação,
# oferecido para leitores de feed; robots.txt governa crawling de HTML.
FONTES_NOTICIAS: tuple[tuple[str, tuple[str, ...], bool], ...] = (
    ("google_news", google_news.URLS_COLETA, False),
    ("laziodisco", laziodisco.URLS_COLETA, True),
    ("studyinitaly", studyinitaly.URLS_COLETA, True),
)


def _coletar_fonte_segura(
    fonte: str, urls: tuple[str, ...], checar_robots: bool
) -> tuple[NoticiaColetada, ...]:
    """Falha de uma fonte NUNCA derruba a coleta das demais (seção 12 do README)."""
    try:
        return coletar_noticias(fonte, urls, checar_robots=checar_robots)
    except (ColetaBloqueada, Exception) as erro:  # noqa: BLE001 — isolar por fonte é o requisito
        logger.warning("fonte %s falhou nesta rodada: %s", fonte, erro)
        return ()


def _credenciais() -> tuple[str, str, str]:
    """(api, email, senha) — falha cedo e com mensagem clara se faltar credencial."""
    api = os.environ.get("PONTE_API", API_PADRAO)
    email, senha = os.environ.get("PONTE_EMAIL"), os.environ.get("PONTE_SENHA")
    if not email or not senha:
        raise RuntimeError("Defina PONTE_EMAIL e PONTE_SENHA para a ingestão agendada")
    return api, email, senha


@cronometrar
def executar_coleta() -> dict[str, int]:
    """Uma rodada completa: fontes → pipeline → ingestão. Devolve o resultado da api."""
    brutas = tuple(
        noticia
        for fonte, urls, checar_robots in FONTES_NOTICIAS
        for noticia in _coletar_fonte_segura(fonte, urls, checar_robots)
    )
    limpas = pipeline.processar(brutas)
    numeros = pipeline.estatisticas(limpas)
    logger.info("coleta: %s", dict(numeros))

    api, email, senha = _credenciais()
    resultado = ingerir_noticias(limpas, api, obter_token(api, email, senha))
    logger.info("ingestão: %s", resultado)
    return resultado


@cronometrar
def executar_curadoria() -> dict[str, object]:
    """Job das 08h30: pede à api a edição do dia e a publicação na fila do Redis."""
    api, email, senha = _credenciais()
    edicao = disparar_curadoria(api, obter_token(api, email, senha))
    topicos = edicao.get("topicos")
    logger.info(
        "curadoria: %s tópico(s), %s item(ns)",
        len(topicos) if isinstance(topicos, list) else 0,
        edicao.get("total"),
    )
    return edicao


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    intervalo = int(os.environ.get("RADAR_INTERVALO_MINUTOS", "180"))
    hora, _, minuto = os.environ.get("NEWSLETTER_HORA_CURADORIA", "08:30").partition(":")

    agendador = BlockingScheduler(timezone="America/Recife")
    agendador.add_job(executar_coleta, "interval", minutes=intervalo, id="radar")
    agendador.add_job(
        executar_curadoria,
        "cron",
        hour=int(hora),
        minute=int(minuto or 0),
        id="curadoria",
    )
    logger.info(
        "radar a cada %d minuto(s); curadoria diária às %s:%s — primeira coleta imediata",
        intervalo,
        hora,
        minuto or "00",
    )
    executar_coleta()
    agendador.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
