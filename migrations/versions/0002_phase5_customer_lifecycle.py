"""phase 5 customer lifecycle schema foundation

Revision ID: 0002_phase5_customer_lifecycle
Revises: 0001_phase2_initial_schema
Create Date: 2026-05-10
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_phase5_customer_lifecycle"
down_revision: str | None = "0001_phase2_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("customer_key", sa.String(length=64), nullable=True))
    op.add_column("customers", sa.Column("activation_mode", sa.String(length=32), nullable=False, server_default="immediate"))
    op.add_column("customers", sa.Column("service_days", sa.Integer(), nullable=True))
    op.add_column("customers", sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("customers", sa.Column("first_connected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("customers", sa.Column("activation_event_id", sa.Integer(), nullable=True))
    op.add_column("customers", sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("customers", sa.Column("delete_after_expired_days", sa.Integer(), nullable=True))
    op.add_column("customers", sa.Column("auto_expire_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("customers", sa.Column("auto_delete_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("customers", sa.Column("delete_eligible_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("customers", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("customers", sa.Column("lifecycle_note", sa.Text(), nullable=True))

    op.create_check_constraint(
        "ck_customers_activation_mode",
        "customers",
        "activation_mode in ('immediate', 'first_connect')",
    )
    op.create_check_constraint("ck_customers_service_days_positive", "customers", "service_days is null or service_days > 0")
    op.create_check_constraint(
        "ck_customers_delete_after_expired_days_nonnegative",
        "customers",
        "delete_after_expired_days is null or delete_after_expired_days >= 0",
    )
    op.create_index(
        "uq_customers_customer_key_non_null",
        "customers",
        ["customer_key"],
        unique=True,
        postgresql_where=sa.text("customer_key is not null"),
    )


def downgrade() -> None:
    op.drop_index("uq_customers_customer_key_non_null", table_name="customers")
    op.drop_constraint("ck_customers_delete_after_expired_days_nonnegative", "customers", type_="check")
    op.drop_constraint("ck_customers_service_days_positive", "customers", type_="check")
    op.drop_constraint("ck_customers_activation_mode", "customers", type_="check")

    op.drop_column("customers", "lifecycle_note")
    op.drop_column("customers", "deleted_at")
    op.drop_column("customers", "delete_eligible_at")
    op.drop_column("customers", "auto_delete_enabled")
    op.drop_column("customers", "auto_expire_enabled")
    op.drop_column("customers", "delete_after_expired_days")
    op.drop_column("customers", "expired_at")
    op.drop_column("customers", "activation_event_id")
    op.drop_column("customers", "first_connected_at")
    op.drop_column("customers", "activated_at")
    op.drop_column("customers", "service_days")
    op.drop_column("customers", "activation_mode")
    op.drop_column("customers", "customer_key")
