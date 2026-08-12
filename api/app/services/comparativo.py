"""Comparativo requisitos do curso × documentos do estudante — o coração do site.

Módulo 100% puro: nenhuma função toca banco, disco ou relógio. O router busca
os dados, converte para as estruturas imutáveis daqui e delega o cálculo.
É o exemplo central de função pura do relatório de Programação Funcional.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from types import MappingProxyType

from app.models.documento import CategoriaDocumento, StatusDocumento
from app.services.documentos import agrupar_por_categoria


@dataclass(frozen=True)
class Requisito:
    """Snapshot imutável de um requisito do curso."""

    categoria: CategoriaDocumento
    descricao: str
    obrigatorio: bool = True


@dataclass(frozen=True)
class DocumentoResumo:
    """Snapshot imutável de um documento do cofre, com status JÁ derivado."""

    categoria: CategoriaDocumento
    tipo: str
    status: StatusDocumento


@dataclass(frozen=True)
class ItemGap:
    """Um requisito avaliado + os documentos que sustentam a avaliação."""

    requisito: Requisito
    documentos: tuple[str, ...]


@dataclass(frozen=True)
class Gap:
    """Resultado do comparativo: três partições imutáveis de requisitos."""

    atendidos: tuple[ItemGap, ...]
    faltando: tuple[ItemGap, ...]
    vencendo: tuple[ItemGap, ...]

    @property
    def total(self) -> int:
        return len(self.atendidos) + len(self.faltando) + len(self.vencendo)

    @property
    def percentual_pronto(self) -> int:
        """% de requisitos atendidos (100 quando o curso não exige nada)."""
        return round(100 * len(self.atendidos) / self.total) if self.total else 100


@lru_cache(maxsize=256)
def requisitos_por_categoria(
    requisitos: tuple[Requisito, ...],
) -> Mapping[CategoriaDocumento, tuple[Requisito, ...]]:
    """Indexa os requisitos de um curso por categoria — consulta pura CACHEADA.

    O cache só é correto porque a função é referencialmente transparente:
    a entrada é uma tupla de dataclasses congeladas (hashável e imutável) e a
    saída é um MappingProxyType imutável. Cursos são consultados repetidamente
    por estudantes diferentes; a mesma tupla de requisitos vira o mesmo índice
    sem recomputar nada.
    """
    return MappingProxyType(agrupar_por_categoria(requisitos, lambda r: r.categoria))


def _avaliar(
    requisito: Requisito, docs_da_categoria: tuple[DocumentoResumo, ...]
) -> tuple[str, ItemGap]:
    """Avalia UM requisito contra os documentos da mesma categoria.

    Regra: qualquer documento OK atende; senão, um documento VENCENDO deixa o
    requisito em alerta; sem documento válido (nenhum, ou só vencidos) falta.
    """
    ok = tuple(d.tipo for d in docs_da_categoria if d.status is StatusDocumento.OK)
    if ok:
        return "atendido", ItemGap(requisito, ok)
    vencendo = tuple(d.tipo for d in docs_da_categoria if d.status is StatusDocumento.VENCENDO)
    if vencendo:
        return "vencendo", ItemGap(requisito, vencendo)
    return "faltando", ItemGap(requisito, ())


def calcular_gap(
    requisitos: tuple[Requisito, ...],
    documentos: tuple[DocumentoResumo, ...],
) -> Gap:
    """Cruza requisitos do curso com os documentos do estudante.

    Função pura: sem I/O, sem relógio (o status dos documentos já chega
    derivado por `calcular_status`), sem mutação — as entradas são tuplas de
    dataclasses congeladas e a saída é um `Gap` congelado. Mesmo par de
    entradas, mesmo Gap, sempre.
    """
    docs_por_categoria = agrupar_por_categoria(documentos, lambda d: d.categoria)
    avaliacoes = tuple(
        _avaliar(requisito, docs_por_categoria.get(categoria, ()))
        for categoria, do_grupo in requisitos_por_categoria(requisitos).items()
        for requisito in do_grupo
    )
    return Gap(
        atendidos=tuple(item for situacao, item in avaliacoes if situacao == "atendido"),
        faltando=tuple(item for situacao, item in avaliacoes if situacao == "faltando"),
        vencendo=tuple(item for situacao, item in avaliacoes if situacao == "vencendo"),
    )
