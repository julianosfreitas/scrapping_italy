"""Modelos de universidades e cursos (seção 5 do README)."""

from __future__ import annotations

import enum
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.requisito import RequisitoCurso


class FonteDado(enum.StrEnum):
    API = "api"
    SCRAPING = "scraping"
    MANUAL = "manual"


class GrauCurso(enum.StrEnum):
    GRADUACAO = "grad"
    MESTRADO = "mestrado"


class Universidade(Base):
    __tablename__ = "universidades"
    # identidade natural usada pelo upsert do cadastro/scraper
    __table_args__ = (UniqueConstraint("nome", "cidade", name="uq_universidade_nome_cidade"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(200))
    pais: Mapped[str] = mapped_column(String(80), default="Itália")
    cidade: Mapped[str] = mapped_column(String(120))
    site_oficial: Mapped[str | None] = mapped_column(String(500))
    fonte: Mapped[FonteDado] = mapped_column(
        Enum(FonteDado, values_callable=lambda e: [m.value for m in e]),
        default=FonteDado.MANUAL,
    )

    cursos: Mapped[list[Curso]] = relationship(
        back_populates="universidade", cascade="all, delete-orphan"
    )


class Curso(Base):
    __tablename__ = "cursos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    universidade_id: Mapped[int] = mapped_column(
        ForeignKey("universidades.id", ondelete="CASCADE"), index=True
    )
    nome: Mapped[str] = mapped_column(String(200))
    grau: Mapped[GrauCurso] = mapped_column(
        Enum(GrauCurso, values_callable=lambda e: [m.value for m in e])
    )
    idioma: Mapped[str | None] = mapped_column(String(40))
    custo_anual: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    prazo_inscricao: Mapped[date | None] = mapped_column(Date)
    tempo_preparacao_meses: Mapped[int | None] = mapped_column()

    universidade: Mapped[Universidade] = relationship(back_populates="cursos")
    requisitos: Mapped[list[RequisitoCurso]] = relationship(
        back_populates="curso", cascade="all, delete-orphan"
    )
