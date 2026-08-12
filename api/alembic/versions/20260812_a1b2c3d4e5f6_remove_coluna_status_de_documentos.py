"""remove coluna status de documentos

Revision ID: a1b2c3d4e5f6
Revises: 15068ba53ecc
Create Date: 2026-08-12 03:05:00.000000

O status (ok | vencendo | vencido) deixa de ser persistido: passa a ser
derivado por função pura de (data_validade, data_atual) em
app/services/documentos.py — elimina o risco de status defasado no banco.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "15068ba53ecc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("documentos", "status")


def downgrade() -> None:
    op.add_column(
        "documentos",
        sa.Column(
            "status",
            sa.Enum("ok", "vencendo", "vencido", name="statusdocumento"),
            nullable=False,
            server_default="ok",
        ),
    )
