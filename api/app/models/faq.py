"""Modelo da tabela `faq` (seção 5 do README) — uma ÁRVORE numa tabela só.

`categoria_id` é a chave estrangeira AUTO-REFERENTE que permite subcategorias
em qualquer profundidade: um nó aponta para o pai, e a raiz aponta para NULL.

Dois tipos de nó convivem na mesma tabela, distinguidos por `resposta`:

- **categoria** — tem `nome`, não tem `resposta`; pode ter filhos (subcategorias
  e perguntas);
- **pergunta** — tem `pergunta`, `resposta` e `fontes`; é sempre folha.

É essa estrutura naturalmente recursiva que a Sprint 6 usa como exemplo
central de RECURSÃO no relatório de programação funcional.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base


class ItemFaq(Base):
    __tablename__ = "faq"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    categoria_id: Mapped[int | None] = mapped_column(
        ForeignKey("faq.id", ondelete="CASCADE"), index=True
    )
    nome: Mapped[str | None] = mapped_column(String(200))
    pergunta: Mapped[str | None] = mapped_column(String(300))
    resposta: Mapped[str | None] = mapped_column(Text)
    fontes: Mapped[list[Any] | None] = mapped_column(JSON().with_variant(MySQLJSON, "mysql"))
    ordem: Mapped[int] = mapped_column(Integer, default=0)

    # o relacionamento também é auto-referente: `filhos` são subcategorias e
    # perguntas do nó; `remote_side` diz ao SQLAlchemy qual ponta é o pai
    pai: Mapped[ItemFaq | None] = relationship(
        back_populates="filhos", remote_side=[id], lazy="selectin"
    )
    filhos: Mapped[list[ItemFaq]] = relationship(
        back_populates="pai", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def eh_categoria(self) -> bool:
        return self.resposta is None
