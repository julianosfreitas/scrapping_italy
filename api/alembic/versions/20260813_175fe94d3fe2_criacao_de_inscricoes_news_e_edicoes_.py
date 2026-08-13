"""criacao de inscricoes_news e edicoes_newsletter

Revision ID: 175fe94d3fe2
Revises: a5bd1c8b1abb
Create Date: 2026-08-13 12:54:29.687455

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "175fe94d3fe2"
down_revision: str | None = "a5bd1c8b1abb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "inscricoes_news",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_inscricoes_news_email"), "inscricoes_news", ["email"], unique=True)

    op.create_table(
        "edicoes_newsletter",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("conteudo", sa.JSON(), nullable=False),
        sa.Column("enviada_em", sa.DateTime(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_edicoes_newsletter_data"), "edicoes_newsletter", ["data"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_edicoes_newsletter_data"), table_name="edicoes_newsletter")
    op.drop_table("edicoes_newsletter")
    op.drop_index(op.f("ix_inscricoes_news_email"), table_name="inscricoes_news")
    op.drop_table("inscricoes_news")
