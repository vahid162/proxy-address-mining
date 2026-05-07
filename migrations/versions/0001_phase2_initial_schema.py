"""phase 2 initial schema

Revision ID: 0001_phase2_initial_schema
Revises: None
Create Date: 2026-05-07
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from mpf.models import Base
import mpf.future_models  # noqa: F401 - registers future-ready tables on Base.metadata
import mpf.extension_models  # noqa: F401 - registers extension-ready tables on Base.metadata

revision: str = "0001_phase2_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
