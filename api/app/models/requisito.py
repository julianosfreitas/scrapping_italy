"""Modelo de requisitos por curso (seção 5 do README).

A categoria usa o MESMO enum dos documentos do cofre — é esse alinhamento
que permite ao `calcular_gap` cruzar requisito × documento por categoria.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.documento import CategoriaDocumento

if TYPE_CHECKING:
    from app.models.universidade import Curso


class RequisitoCurso(Base):
    __tablename__ = "requisitos_curso"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    curso_id: Mapped[int] = mapped_column(ForeignKey("cursos.id", ondelete="CASCADE"), index=True)
    categoria: Mapped[CategoriaDocumento] = mapped_column(
        Enum(CategoriaDocumento, values_callable=lambda e: [m.value for m in e])
    )
    descricao: Mapped[str] = mapped_column(String(300))
    obrigatorio: Mapped[bool] = mapped_column(default=True)

    curso: Mapped[Curso] = relationship(back_populates="requisitos")
