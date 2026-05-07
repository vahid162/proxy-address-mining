from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from mpf.models import Base, TimestampMixin

JsonDict = dict[str, Any]


class BuyerAccount(Base, TimestampMixin):
    """Future buyer/customer account boundary.

    This is intentionally separate from `customers`, because `customers` are service/port
    allocations, not human login identities.
    """

    __tablename__ = "buyer_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'active'"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class BuyerUser(Base, TimestampMixin):
    """Future login identity for a buyer account.

    Authentication is not implemented in Phase 2. This table only reserves the
    boundary so future buyer UI work does not overload operator identities.
    """

    __tablename__ = "buyer_users"
    __table_args__ = (UniqueConstraint("buyer_account_id", "email", name="uq_buyer_user_email_per_account"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    buyer_account_id: Mapped[int] = mapped_column(ForeignKey("buyer_accounts.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'active'"))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CustomerServiceLink(Base):
    """Links a buyer account to one or more customer service/port records."""

    __tablename__ = "customer_service_links"
    __table_args__ = (
        UniqueConstraint("buyer_account_id", "customer_id", name="uq_buyer_customer_service_link"),
        Index("ix_customer_service_links_buyer_status", "buyer_account_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    buyer_account_id: Mapped[int] = mapped_column(ForeignKey("buyer_accounts.id", ondelete="CASCADE"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'active'"))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class CustomerServicePermission(Base):
    """Small future-safe permission layer for buyer-visible services.

    This is not heavy RBAC. It reserves a controlled scope boundary for future
    buyer UI and API tokens.
    """

    __tablename__ = "customer_service_permissions"
    __table_args__ = (UniqueConstraint("buyer_user_id", "customer_id", "scope", name="uq_buyer_user_customer_scope"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    buyer_user_id: Mapped[int] = mapped_column(ForeignKey("buyer_users.id", ondelete="CASCADE"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)


class ActionRequest(Base):
    """Future request/approval queue for buyer-safe actions.

    Buyer UI should create requests rather than directly mutating customers,
    firewall, abuse, blocks, or pauses.
    """

    __tablename__ = "action_requests"
    __table_args__ = (Index("ix_action_requests_status_created", "status", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_type: Mapped[str] = mapped_column(String(32), nullable=False)
    requester_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action_type: Mapped[str] = mapped_column(String(128), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'pending'"))
    payload_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    reviewed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class WorkerIdentity(Base):
    """Observed worker identity for future worker reporting and policy.

    Worker names are Stratum-layer identities, not firewall-layer identities.
    """

    __tablename__ = "worker_identities"
    __table_args__ = (
        UniqueConstraint("customer_id", "normalized_worker_name", name="uq_customer_normalized_worker"),
        Index("ix_worker_identities_customer_status", "customer_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    worker_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_worker_name: Mapped[str] = mapped_column(String(255), nullable=False)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'observed'"))


class WorkerPolicy(Base):
    """Future worker policy mode per customer.

    Enforcement is not implemented in Phase 2. This table only models the policy
    intent for later worker timeline / Stratum-aware enforcement phases.
    """

    __tablename__ = "worker_policies"
    __table_args__ = (UniqueConstraint("customer_id", name="uq_worker_policy_customer"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'allow_all'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class WorkerBlock(Base):
    """Future worker block rule.

    Worker blocks cannot be assumed to be firewall-only. They require worker
    observation and, for strict enforcement, a Stratum-aware adapter.
    """

    __tablename__ = "worker_blocks"
    __table_args__ = (Index("ix_worker_blocks_customer_status", "customer_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    worker_name: Mapped[str] = mapped_column(String(255), nullable=False)
    match_type: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'exact'"))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'active'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    removed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)


class WorkerEnforcementEvent(Base):
    """Future evidence/audit trail for worker enforcement decisions."""

    __tablename__ = "worker_enforcement_events"
    __table_args__ = (Index("ix_worker_enforcement_customer_created", "customer_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    worker_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    src_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    adapter: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
