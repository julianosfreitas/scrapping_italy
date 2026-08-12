"""Modelo da tabela `documentos` (seção 5 do README)."""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.estudante import Estudante


class CategoriaDocumento(enum.StrEnum):
    IDENTIDADE = "identidade"
    ACADEMICO = "academico"
    FINANCEIRO = "financeiro"
    IDIOMA = "idioma"
    VISTO = "visto"
    OUTROS = "outros"


class StatusDocumento(enum.StrEnum):
    OK = "ok"
    VENCENDO = "vencendo"
    VENCIDO = "vencido"


class Documento(Base):
    __tablename__ = "documentos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    estudante_id: Mapped[int] = mapped_column(
        ForeignKey("estudantes.id", ondelete="CASCADE"), index=True
    )
    categoria: Mapped[CategoriaDocumento] = mapped_column(
        Enum(CategoriaDocumento, values_callable=lambda e: [m.value for m in e])
    )
    tipo: Mapped[str] = mapped_column(String(80))
    arquivo_url: Mapped[str] = mapped_column(String(500))
    data_validade: Mapped[date | None] = mapped_column(Date)
    # status NÃO é coluna: é derivado por função pura de (data_validade, data_atual)
    # — ver app/services/documentos.py::calcular_status
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    estudante: Mapped[Estudante] = relationship(back_populates="documentos")
