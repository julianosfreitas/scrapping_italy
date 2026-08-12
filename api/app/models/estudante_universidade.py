"""Associação estudante ↔ curso ("Minhas universidades", seção 5 do README)."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.estudante import Estudante
from app.models.universidade import Curso


class StatusJornada(enum.StrEnum):
    INTERESSADO = "interessado"
    PREPARANDO = "preparando"
    INSCRITO = "inscrito"
    ACEITO = "aceito"


class EstudanteUniversidade(Base):
    __tablename__ = "estudante_universidade"

    estudante_id: Mapped[int] = mapped_column(
        ForeignKey("estudantes.id", ondelete="CASCADE"), primary_key=True
    )
    curso_id: Mapped[int] = mapped_column(
        ForeignKey("cursos.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[StatusJornada] = mapped_column(
        Enum(StatusJornada, values_callable=lambda e: [m.value for m in e]),
        default=StatusJornada.INTERESSADO,
    )
    alerta_prazo: Mapped[bool] = mapped_column(default=True)
    adicionado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    estudante: Mapped[Estudante] = relationship()
    curso: Mapped[Curso] = relationship()
