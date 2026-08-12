"""Infra comum dos parsers de fontes: tipos imutáveis e o parser genérico.

Cada fonte é uma ESPECIALIZAÇÃO do parser genérico via ``functools.partial``
(conceito 11): o parser não sabe de onde o HTML veio — recebe os seletores e
o mapa de graus como parâmetros. Parsers são funções de primeira classe
(conceito 3): vivem no registry ``PARSERS`` (dict nome → função) e são
passados adiante como valores.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from itertools import islice
from typing import Protocol
from xml.etree import ElementTree

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


# ── notícias (Radar, Sprint 4) ───────────────────────────


@dataclass(frozen=True)
class NoticiaColetada:
    """Item bruto de notícia vindo de uma fonte — imutável desde o nascimento."""

    titulo: str
    url: str
    fonte: str
    resumo: str | None = None
    idioma: str | None = None
    publicada_em: datetime | None = None
    categoria: str = "geral"


@dataclass(frozen=True)
class SeletoresNoticia:
    """Seletores CSS que especializam o parser genérico de notícias HTML."""

    item: str
    titulo: str
    link: str
    resumo: str | None = None
    data: str | None = None


class ParserNoticias(Protocol):
    def __call__(self, conteudo: str) -> tuple[NoticiaColetada, ...]: ...


def iterar_itens_rss(xml: str) -> Iterator[dict[str, str | None]]:
    """GERADOR: percorre os <item> de um RSS um a um, sem materializar a lista.

    Feeds grandes (Google News devolve dezenas de itens por query) são
    consumidos item a item — quem chama decide quantos quer (ex.: islice),
    e nada além do item corrente ocupa memória.
    """
    raiz = ElementTree.fromstring(xml)
    idioma_feed = raiz.findtext("channel/language")
    for item in raiz.iterfind("channel/item"):
        yield {
            "titulo": item.findtext("title"),
            "url": item.findtext("link"),
            "resumo": item.findtext("description"),
            "data": item.findtext("pubDate"),
            "idioma": idioma_feed,
        }


def parse_data_rfc822(texto: str | None) -> datetime | None:
    """'Tue, 11 Aug 2026 08:30:00 GMT' -> datetime; inválido -> None."""
    if not texto:
        return None
    try:
        return parsedate_to_datetime(texto).replace(tzinfo=None)
    except (TypeError, ValueError):
        return None


def parse_rss(xml: str, *, fonte: str, maximo_itens: int = 50) -> tuple[NoticiaColetada, ...]:
    """Parser genérico de RSS — especializado por fonte via functools.partial."""
    return tuple(
        NoticiaColetada(
            titulo=item["titulo"].strip(),
            url=item["url"].strip(),
            fonte=fonte,
            resumo=item["resumo"],
            idioma=(item["idioma"] or "").split("-")[0] or None,
            publicada_em=parse_data_rfc822(item["data"]),
        )
        for item in islice(iterar_itens_rss(xml), maximo_itens)
        if item["titulo"] and item["url"]
    )


def parse_noticias_html(
    html: str,
    *,
    fonte: str,
    seletores: SeletoresNoticia,
    idioma: str | None = None,
    base_url: str = "",
) -> tuple[NoticiaColetada, ...]:
    """Parser genérico de páginas de notícias — especializado via partial."""
    sopa = BeautifulSoup(html, "html.parser")
    return tuple(
        NoticiaColetada(
            titulo=titulo,
            url=url if url.startswith("http") else f"{base_url}{url}",
            fonte=fonte,
            resumo=_texto(bloco, seletores.resumo),
            idioma=idioma,
            publicada_em=_para_datetime(parse_data_italiana(_texto(bloco, seletores.data))),
        )
        for bloco in sopa.select(seletores.item)
        if (titulo := _texto(bloco, seletores.titulo)) is not None
        and (url := _atributo_href(bloco, seletores.link)) is not None
    )


def _para_datetime(dia: date | None) -> datetime | None:
    return datetime(dia.year, dia.month, dia.day) if dia else None


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
