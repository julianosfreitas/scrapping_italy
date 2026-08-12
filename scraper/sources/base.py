"""Infra comum dos parsers de fontes: tipos imutáveis e o parser genérico.

Cada fonte é uma ESPECIALIZAÇÃO do parser genérico via ``functools.partial``
(conceito 11): o parser não sabe de onde o HTML veio — recebe os seletores e
o mapa de graus como parâmetros. Parsers são funções de primeira classe
(conceito 3): vivem no registry ``PARSERS`` (dict nome → função) e são
passados adiante como valores.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from bs4 import BeautifulSoup
from bs4.element import Tag


@dataclass(frozen=True)
class RequisitoColetado:
    categoria: str
    descricao: str
    obrigatorio: bool = True


@dataclass(frozen=True)
class CursoColetado:
    nome: str
    grau: str  # "grad" | "mestrado"
    idioma: str | None = None
    prazo_inscricao: date | None = None
    requisitos: tuple[RequisitoColetado, ...] = ()


@dataclass(frozen=True)
class UniversidadeColetada:
    nome: str
    cidade: str
    pais: str = "Itália"
    site_oficial: str | None = None
    fonte: str = "scraping"
    cursos: tuple[CursoColetado, ...] = ()


@dataclass(frozen=True)
class SeletoresFonte:
    """Seletores CSS + normalizações que especializam o parser genérico."""

    universidade: str
    nome: str
    cidade: str
    site: str | None
    curso: str
    curso_nome: str
    curso_grau: str
    curso_idioma: str | None
    curso_prazo: str | None
    grau_mapa: tuple[tuple[str, str], ...]  # ("laurea magistrale" -> "mestrado"), ...


class Parser(Protocol):
    def __call__(self, html: str) -> tuple[UniversidadeColetada, ...]: ...


def _texto(elemento: Tag, seletor: str | None) -> str | None:
    if seletor is None:
        return None
    alvo = elemento.select_one(seletor)
    if alvo is None:
        return None
    texto = alvo.get_text(strip=True)
    return texto or None


def normalizar_grau(texto: str | None, grau_mapa: tuple[tuple[str, str], ...]) -> str | None:
    """'Laurea Magistrale' -> 'mestrado'. Desconhecido -> None (curso é descartado)."""
    if texto is None:
        return None
    minusculo = texto.strip().lower()
    return next((grau for padrao, grau in grau_mapa if padrao in minusculo), None)


def parse_data_italiana(texto: str | None) -> date | None:
    """'10/09/2026' -> date(2026, 9, 10); formato inesperado -> None."""
    if not texto:
        return None
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def _parse_curso(elemento: Tag, seletores: SeletoresFonte) -> CursoColetado | None:
    nome = _texto(elemento, seletores.curso_nome)
    grau = normalizar_grau(_texto(elemento, seletores.curso_grau), seletores.grau_mapa)
    if nome is None or grau is None:
        return None
    return CursoColetado(
        nome=nome,
        grau=grau,
        idioma=_texto(elemento, seletores.curso_idioma),
        prazo_inscricao=parse_data_italiana(_texto(elemento, seletores.curso_prazo)),
    )


def parse_universidades(
    html: str, *, fonte: str, seletores: SeletoresFonte
) -> tuple[UniversidadeColetada, ...]:
    """Parser genérico: HTML → tuplas imutáveis. Determinístico para o mesmo HTML."""
    sopa = BeautifulSoup(html, "html.parser")
    return tuple(
        UniversidadeColetada(
            nome=nome,
            cidade=cidade,
            site_oficial=_atributo_href(bloco, seletores.site),
            fonte=fonte,
            cursos=tuple(
                curso
                for elemento in bloco.select(seletores.curso)
                if (curso := _parse_curso(elemento, seletores)) is not None
            ),
        )
        for bloco in sopa.select(seletores.universidade)
        if (nome := _texto(bloco, seletores.nome)) is not None
        and (cidade := _texto(bloco, seletores.cidade)) is not None
    )


def _atributo_href(elemento: Tag, seletor: str | None) -> str | None:
    if seletor is None:
        return None
    alvo = elemento.select_one(seletor)
    if alvo is None:
        return None
    href = alvo.get("href")
    return href if isinstance(href, str) and href else None
