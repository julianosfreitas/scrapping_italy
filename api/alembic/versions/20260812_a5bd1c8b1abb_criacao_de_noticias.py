"""criacao de noticias

Revision ID: a5bd1c8b1abb
Revises: 3b9688c675d0
Create Date: 2026-08-12 03:42:05.075619

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a5bd1c8b1abb"
down_revision: str | None = "3b9688c675d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "noticias",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("titulo", sa.String(length=300), nullable=False),
        sa.Column("resumo", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("fonte", sa.String(length=40), nullable=False),
        sa.Column("categoria", sa.String(length=40), nullable=False),
        sa.Column("idioma", sa.String(length=10), nullable=True),
        sa.Column("publicada_em", sa.DateTime(), nullable=True),
        sa.Column("coletada_em", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_noticias_categoria"), "noticias", ["categoria"], unique=False)
    op.create_index(op.f("ix_noticias_fonte"), "noticias", ["fonte"], unique=False)
    op.create_index(op.f("ix_noticias_url"), "noticias", ["url"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_noticias_url"), table_name="noticias")
    op.drop_index(op.f("ix_noticias_fonte"), table_name="noticias")
    op.drop_index(op.f("ix_noticias_categoria"), table_name="noticias")
    op.drop_table("noticias")
