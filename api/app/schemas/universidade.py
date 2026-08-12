"""Schemas de universidades, cursos e comparativo — imutáveis (frozen=True)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.documento import CategoriaDocumento
from app.models.estudante_universidade import StatusJornada
from app.models.universidade import FonteDado, GrauCurso


class _Congelado(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)


# ── cadastro (manual e via scraper) ──────────────────────


class RequisitoCriar(_Congelado):
    categoria: CategoriaDocumento
    descricao: str = Field(min_length=3, max_length=300)
    obrigatorio: bool = True


class CursoCriar(_Congelado):
    nome: str = Field(min_length=2, max_length=200)
    grau: GrauCurso
    idioma: str | None = Field(default=None, max_length=40)
    custo_anual: Decimal | None = Field(default=None, ge=0)
    prazo_inscricao: date | None = None
    tempo_preparacao_meses: int | None = Field(default=None, ge=0, le=60)
    requisitos: tuple[RequisitoCriar, ...] = ()


class UniversidadeCriar(_Congelado):
    nome: str = Field(min_length=2, max_length=200)
    pais: str = Field(default="Itália", max_length=80)
    cidade: str = Field(min_length=2, max_length=120)
    site_oficial: str | None = Field(default=None, max_length=500)
    fonte: FonteDado = FonteDado.MANUAL
    cursos: tuple[CursoCriar, ...] = ()


# ── leitura ──────────────────────────────────────────────


class RequisitoPublico(_Congelado):
    id: int
    categoria: CategoriaDocumento
    descricao: str
    obrigatorio: bool


class CursoPublico(_Congelado):
    id: int
    universidade_id: int
    nome: str
    grau: GrauCurso
    idioma: str | None
    custo_anual: Decimal | None
    prazo_inscricao: date | None
    tempo_preparacao_meses: int | None
    prazo_proximo: bool = False
    requisitos: tuple[RequisitoPublico, ...] = ()


class UniversidadePublica(_Congelado):
    id: int
    nome: str
    pais: str
    cidade: str
    site_oficial: str | None
    fonte: FonteDado
    total_cursos: int = 0


class UniversidadeDetalhe(UniversidadePublica):
    cursos: tuple[CursoPublico, ...] = ()


# ── "Minhas universidades" + comparativo ─────────────────


class AssociacaoCriar(_Congelado):
    curso_id: int
    alerta_prazo: bool = True


class AssociacaoEditar(_Congelado):
    status: StatusJornada | None = None
    alerta_prazo: bool | None = None


class ItemGapPublico(_Congelado):
    categoria: CategoriaDocumento
    descricao: str
    obrigatorio: bool
    documentos: tuple[str, ...]


class GapPublico(_Congelado):
    atendidos: tuple[ItemGapPublico, ...]
    faltando: tuple[ItemGapPublico, ...]
    vencendo: tuple[ItemGapPublico, ...]
    percentual_pronto: int


class MinhaUniversidade(_Congelado):
    curso: CursoPublico
    universidade: UniversidadePublica
    status: StatusJornada
    alerta_prazo: bool
    adicionado_em: datetime
    gap: GapPublico
