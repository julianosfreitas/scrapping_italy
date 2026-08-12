"""Coleta educada: robots.txt, intervalo e injeção de funções (sem rede)."""

from pathlib import Path

import pytest

from scraper.coleta import INTERVALO_SEGUNDOS, ColetaBloqueada, coletar, pode_raspar

FIXTURE = (Path(__file__).parent / "fixtures" / "universitaly_atenei.html").read_text(
    encoding="utf-8"
)

ROBOTS_PERMISSIVO = "User-agent: *\nAllow: /\n"
ROBOTS_RESTRITIVO = "User-agent: *\nDisallow: /cerca-corsi\n"


def test_pode_raspar_respeita_disallow() -> None:
    url = "https://www.universitaly.it/cerca-corsi"
    assert pode_raspar(ROBOTS_PERMISSIVO, url)
    assert not pode_raspar(ROBOTS_RESTRITIVO, url)


def test_robots_vazio_permite() -> None:
    assert pode_raspar("", "https://www.universitaly.it/qualquer")


def test_coletar_com_funcoes_injetadas_sem_rede() -> None:
    urls = ("https://x.it/pagina-1", "https://x.it/pagina-2")
    pedidas: list[str] = []
    esperas: list[float] = []

    def obter_falso(url: str) -> str:
        pedidas.append(url)
        return ROBOTS_PERMISSIVO if url.endswith("robots.txt") else FIXTURE

    universidades = coletar("universitaly", urls, obter=obter_falso, dormir=esperas.append)

    assert pedidas[0] == "https://x.it/robots.txt"  # robots antes de tudo
    assert pedidas[1:] == list(urls)
    assert esperas == [INTERVALO_SEGUNDOS]  # intervalo entre páginas, não antes da 1ª
    assert len(universidades) == 4  # 2 universidades por página × 2 páginas


def test_coletar_barrado_pelo_robots() -> None:
    def obter_falso(url: str) -> str:
        return ROBOTS_RESTRITIVO if url.endswith("robots.txt") else FIXTURE

    with pytest.raises(ColetaBloqueada, match="robots.txt"):
        coletar(
            "universitaly",
            ("https://www.universitaly.it/cerca-corsi",),
            obter=obter_falso,
            dormir=lambda _s: None,
        )


def test_coletar_sem_urls_devolve_vazio() -> None:
    assert coletar("universitaly", (), obter=lambda u: "", dormir=lambda _s: None) == ()
