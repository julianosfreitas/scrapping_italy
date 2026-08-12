"""criacao de estudantes e documentos

Revision ID: 15068ba53ecc
Revises:
Create Date: 2026-08-12 02:40:20.584761

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "15068ba53ecc"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "estudantes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("foto_url", sa.String(length=500), nullable=True),
        sa.Column("area_estudo", sa.String(length=120), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("nivel_italiano", sa.String(length=10), nullable=True),
        sa.Column("nivel_ingles", sa.String(length=10), nullable=True),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_estudantes_email"), "estudantes", ["email"], unique=True)
    op.create_table(
        "documentos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("estudante_id", sa.Integer(), nullable=False),
        sa.Column(
            "categoria",
            sa.Enum(
                "identidade",
                "academico",
                "financeiro",
                "idioma",
                "visto",
                "outros",
                name="categoriadocumento",
            ),
            nullable=False,
        ),
        sa.Column("tipo", sa.String(length=80), nullable=False),
        sa.Column("arquivo_url", sa.String(length=500), nullable=False),
        sa.Column("data_validade", sa.Date(), nullable=True),
        sa.Column(
            "status", sa.Enum("ok", "vencendo", "vencido", name="statusdocumento"), nullable=False
        ),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["estudante_id"], ["estudantes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_documentos_estudante_id"), "documentos", ["estudante_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_documentos_estudante_id"), table_name="documentos")
    op.drop_table("documentos")
    op.drop_index(op.f("ix_estudantes_email"), table_name="estudantes")
    op.drop_table("estudantes")
