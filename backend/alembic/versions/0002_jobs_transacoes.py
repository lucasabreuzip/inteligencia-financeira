"""jobs + transacoes

Revision ID: 0002_jobs_transacoes
Revises: 0001_init
Create Date: 2026-03-09 11:30:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_jobs_transacoes"
down_revision: str | None = "0001_init"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("rows_total", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("rows_processed", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_jobs"),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])

    op.create_table(
        "transacoes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("valor", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("cliente", sa.String(length=120), nullable=False),
        sa.Column("descricao", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name="fk_transacoes_job_id_jobs",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_transacoes"),
    )
    op.create_index("ix_transacoes_job_id", "transacoes", ["job_id"])
    op.create_index("ix_transacoes_data", "transacoes", ["data"])
    op.create_index("ix_transacoes_status", "transacoes", ["status"])
    op.create_index("ix_transacoes_cliente", "transacoes", ["cliente"])


def downgrade() -> None:
    op.drop_index("ix_transacoes_cliente", table_name="transacoes")
    op.drop_index("ix_transacoes_status", table_name="transacoes")
    op.drop_index("ix_transacoes_data", table_name="transacoes")
    op.drop_index("ix_transacoes_job_id", table_name="transacoes")
    op.drop_table("transacoes")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_table("jobs")