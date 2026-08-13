"""Ingestão: envia o resultado da coleta para a API REST autenticada.

Uso (com a api no ar e um estudante cadastrado):

    PONTE_EMAIL=... PONTE_SENHA=... python -m scraper.ingestao --fixture \\
        scraper/tests/fixtures/universitaly_atenei.html

Sem ``--fixture``, tenta a coleta ao vivo do Universitaly (hoje bloqueada
por WAF — ver nota em sources/universitaly.py; Playwright entra na Sprint 4).
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import asdict
from pathlib import Path

import httpx

from scraper.coleta import USER_AGENT, coletar
from scraper.sources import PARSERS
from scraper.sources.base import NoticiaColetada, UniversidadeColetada
from scraper.sources.universitaly import URLS_COLETA

API_PADRAO = "http://localhost:8000"


def _payload(universidade: UniversidadeColetada) -> dict[str, object]:
    corpo = asdict(universidade)
    # `fonte` da coleta identifica a ORIGEM (ex.: "universitaly"); no modelo
    # da api o enum é api|scraping|manual — tudo que vem do scraper é scraping.
    corpo["fonte"] = "scraping"
    for curso in corpo["cursos"]:
        prazo = curso.get("prazo_inscricao")
        if prazo is not None:
            curso["prazo_inscricao"] = prazo.isoformat()
    return corpo


def _payload_noticia(noticia: NoticiaColetada) -> dict[str, object]:
    return {
        "titulo": noticia.titulo,
        "resumo": noticia.resumo,
        "url": noticia.url,
        "fonte": noticia.fonte,
        "categoria": noticia.categoria,
        "idioma": noticia.idioma,
        "publicada_em": noticia.publicada_em.isoformat() if noticia.publicada_em else None,
    }


def ingerir_noticias(noticias: tuple[NoticiaColetada, ...], api: str, token: str) -> dict[str, int]:
    """Envia o lote para POST /api/noticias; o dedupe final (URL única) é da api."""
    resposta = httpx.post(
        f"{api}/api/noticias",
        json=[_payload_noticia(n) for n in noticias],
        headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT},
        timeout=60,
    )
    resposta.raise_for_status()
    resultado: dict[str, int] = resposta.json()
    return resultado


def disparar_curadoria(api: str, token: str, janela_horas: int | None = None) -> dict[str, object]:
    """Dispara a curadoria da newsletter (POST /api/newsletter/curadoria).

    Quem monta e enfileira a edição é a api — aqui só existe o gatilho, do
    mesmo jeito que a ingestão do Radar: o scraper nunca fala com o banco.
    """
    parametros = {} if janela_horas is None else {"janela_horas": janela_horas}
    resposta = httpx.post(
        f"{api}/api/newsletter/curadoria",
        params=parametros,
        headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT},
        timeout=60,
    )
    resposta.raise_for_status()
    edicao: dict[str, object] = resposta.json()
    return edicao


def obter_token(api: str, email: str, senha: str) -> str:
    resposta = httpx.post(f"{api}/api/auth/login", json={"email": email, "senha": senha})
    resposta.raise_for_status()
    token: str = resposta.json()["access_token"]
    return token


def ingerir(universidades: tuple[UniversidadeColetada, ...], api: str, token: str) -> int:
    with httpx.Client(
        headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT}
    ) as cliente:
        for universidade in universidades:
            resposta = cliente.post(f"{api}/api/universidades", json=_payload(universidade))
            resposta.raise_for_status()
    return len(universidades)


def main(argumentos: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coleta e ingere universidades via API")
    parser.add_argument("--fonte", default="universitaly", choices=sorted(PARSERS))
    parser.add_argument("--fixture", type=Path, help="HTML local no lugar da coleta ao vivo")
    parser.add_argument("--api", default=os.environ.get("PONTE_API", API_PADRAO))
    opcoes = parser.parse_args(argumentos)

    email = os.environ.get("PONTE_EMAIL")
    senha = os.environ.get("PONTE_SENHA")
    if not email or not senha:
        print("Defina PONTE_EMAIL e PONTE_SENHA para autenticar a ingestão.")
        return 2

    if opcoes.fixture is not None:
        html = opcoes.fixture.read_text(encoding="utf-8")
        universidades = PARSERS[opcoes.fonte](html)
    else:
        universidades = coletar(opcoes.fonte, URLS_COLETA)

    total = ingerir(universidades, opcoes.api, obter_token(opcoes.api, email, senha))
    print(f"Ingestão concluída: {total} universidade(s) enviadas para {opcoes.api}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
