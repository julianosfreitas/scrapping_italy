"""criacao do faq com categorias aninhadas

Revision ID: fb6a914c9b9b
Revises: 175fe94d3fe2
Create Date: 2026-08-13 14:32:11.104882

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "fb6a914c9b9b"
down_revision: str | None = "175fe94d3fe2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "faq",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        # auto-referente: um nó aponta para a categoria pai; raiz aponta para NULL
        sa.Column("categoria_id", sa.Integer(), nullable=True),
        sa.Column("nome", sa.String(length=200), nullable=True),
        sa.Column("pergunta", sa.String(length=300), nullable=True),
        sa.Column("resposta", sa.Text(), nullable=True),
        sa.Column("fontes", sa.JSON(), nullable=True),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["categoria_id"], ["faq.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_faq_categoria_id"), "faq", ["categoria_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_faq_categoria_id"), table_name="faq")
    op.drop_table("faq")
