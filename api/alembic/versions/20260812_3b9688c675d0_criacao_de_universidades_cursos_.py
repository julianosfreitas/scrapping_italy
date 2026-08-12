"""criacao de universidades cursos requisitos e associacao

Revision ID: 3b9688c675d0
Revises: a1b2c3d4e5f6
Create Date: 2026-08-12 03:19:09.154837

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3b9688c675d0"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "universidades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("pais", sa.String(length=80), nullable=False),
        sa.Column("cidade", sa.String(length=120), nullable=False),
        sa.Column("site_oficial", sa.String(length=500), nullable=True),
        sa.Column("fonte", sa.Enum("api", "scraping", "manual", name="fontedado"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome", "cidade", name="uq_universidade_nome_cidade"),
    )
    op.create_table(
        "cursos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("universidade_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("grau", sa.Enum("grad", "mestrado", name="graucurso"), nullable=False),
        sa.Column("idioma", sa.String(length=40), nullable=True),
        sa.Column("custo_anual", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("prazo_inscricao", sa.Date(), nullable=True),
        sa.Column("tempo_preparacao_meses", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["universidade_id"], ["universidades.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cursos_universidade_id"), "cursos", ["universidade_id"], unique=False)
    op.create_table(
        "estudante_universidade",
        sa.Column("estudante_id", sa.Integer(), nullable=False),
        sa.Column("curso_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("interessado", "preparando", "inscrito", "aceito", name="statusjornada"),
            nullable=False,
        ),
        sa.Column("alerta_prazo", sa.Boolean(), nullable=False),
        sa.Column("adicionado_em", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["curso_id"], ["cursos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["estudante_id"], ["estudantes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("estudante_id", "curso_id"),
    )
    op.create_table(
        "requisitos_curso",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("curso_id", sa.Integer(), nullable=False),
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
        sa.Column("descricao", sa.String(length=300), nullable=False),
        sa.Column("obrigatorio", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["curso_id"], ["cursos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_requisitos_curso_curso_id"), "requisitos_curso", ["curso_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_requisitos_curso_curso_id"), table_name="requisitos_curso")
    op.drop_table("requisitos_curso")
    op.drop_table("estudante_universidade")
    op.drop_index(op.f("ix_cursos_universidade_id"), table_name="cursos")
    op.drop_table("cursos")
    op.drop_table("universidades")
