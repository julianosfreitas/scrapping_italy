"""Modelo da tabela `estudantes` (seção 5 do README)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.documento import Documento


class Estudante(Base):
    __tablename__ = "estudantes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    foto_url: Mapped[str | None] = mapped_column(String(500))
    area_estudo: Mapped[str | None] = mapped_column(String(120))
    bio: Mapped[str | None] = mapped_column(Text)
    nivel_italiano: Mapped[str | None] = mapped_column(String(10))
    nivel_ingles: Mapped[str | None] = mapped_column(String(10))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    documentos: Mapped[list[Documento]] = relationship(
        back_populates="estudante", cascade="all, delete-orphan"
    )
