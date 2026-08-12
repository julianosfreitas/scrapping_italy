"""Parser do Universitaly: fixture HTML → tuplas imutáveis."""

import dataclasses
import functools
from datetime import date
from pathlib import Path

import pytest

from scraper.sources import PARSERS
from scraper.sources.base import normalizar_grau, parse_data_italiana
from scraper.sources.universitaly import SELETORES_UNIVERSITALY, parser_universitaly

FIXTURE = (Path(__file__).parent / "fixtures" / "universitaly_atenei.html").read_text(
    encoding="utf-8"
)


def test_parse_da_fixture_completa() -> None:
    universidades = parser_universitaly(FIXTURE)
    assert [u.nome for u in universidades] == ["Politecnico di Milano", "Università di Bologna"]

    polimi = universidades[0]
    assert polimi.cidade == "Milano"
    assert polimi.site_oficial == "https://www.polimi.it"
    assert polimi.fonte == "universitaly"
    # o curso "Master di II livello" não está no grau_mapa -> descartado
    assert [(c.nome, c.grau) for c in polimi.cursos] == [
        ("Computer Science and Engineering", "mestrado"),
        ("Ingegneria Informatica", "grad"),
    ]
    assert polimi.cursos[0].prazo_inscricao == date(2026, 12, 2)
    assert polimi.cursos[0].idioma == "Inglese"


def test_bloco_sem_cidade_e_descartado() -> None:
    universidades = parser_universitaly(FIXTURE)
    assert all(u.cidade for u in universidades)


def test_prazo_ilegivel_vira_none() -> None:
    bolonha = parser_universitaly(FIXTURE)[1]
    assert bolonha.cursos[0].prazo_inscricao is None  # "data da definire"


def test_resultado_e_imutavel() -> None:
    universidade = parser_universitaly(FIXTURE)[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        universidade.nome = "outro"  # type: ignore[misc]


def test_parser_e_determinstico() -> None:
    assert parser_universitaly(FIXTURE) == parser_universitaly(FIXTURE)


# ── registry e partial (conceitos 3 e 11) ────────────────


def test_registry_expoe_parser_como_funcao_de_primeira_classe() -> None:
    parser = PARSERS["universitaly"]  # função escolhida por nome, carregada como valor
    assert callable(parser)
    assert parser is parser_universitaly
    assert parser(FIXTURE) == parser_universitaly(FIXTURE)


def test_registry_e_imutavel() -> None:
    with pytest.raises(TypeError):
        PARSERS["nova"] = parser_universitaly  # type: ignore[index]


def test_parser_da_fonte_e_partial_do_generico() -> None:
    assert isinstance(parser_universitaly, functools.partial)
    assert parser_universitaly.keywords["fonte"] == "universitaly"
    assert parser_universitaly.keywords["seletores"] is SELETORES_UNIVERSITALY


# ── normalizações puras ──────────────────────────────────


def test_normalizar_grau() -> None:
    mapa = SELETORES_UNIVERSITALY.grau_mapa
    assert normalizar_grau("Laurea Magistrale", mapa) == "mestrado"
    assert normalizar_grau("Corso di Laurea", mapa) == "grad"
    assert normalizar_grau("Master di II livello", mapa) is None
    assert normalizar_grau(None, mapa) is None


def test_parse_data_italiana() -> None:
    assert parse_data_italiana("02/12/2026") == date(2026, 12, 2)
    assert parse_data_italiana("data da definire") is None
    assert parse_data_italiana(None) is None
