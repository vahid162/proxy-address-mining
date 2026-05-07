from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for the MPF PostgreSQL schema."""


JsonDict = dict[str, Any]


def utcnow_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Lane(Base, TimestampMixin):
    __tablename__ = "lanes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    backend_port: Mapped[int] = mapped_column(Integer, nullable=False)
    chain_prefix: Mapped[str] = mapped_column(String(64), nullable=False)
    protocol: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'stratum'"))

    upstreams: Mapped[list[LaneUpstream]] = relationship(back_populates="lane", cascade="all, delete-orphan")
    customers: Mapped[list[Customer]] = relationship(back_populates="lane")


class LaneUpstream(Base, TimestampMixin):
    __tablename__ = "lane_upstreams"
    __table_args__ = (UniqueConstraint("lane_id", "host", "port", name="uq_lane_upstream_endpoint"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    lane_id: Mapped[int] = mapped_column(ForeignKey("lanes.id", ondelete="CASCADE"), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("100"))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    lane: Mapped[Lane] = relationship(back_populates="upstreams")


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("port", name="uq_customers_port"),
        Index("ix_customers_lane_status", "lane_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    lane_id: Mapped[int] = mapped_column(ForeignKey("lanes.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'active'"))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    lane: Mapped[Lane] = relationship(back_populates="customers")
    policies: Mapped[list[CustomerPolicy]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    ip_pins: Mapped[list[CustomerIpPin]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    abuse_state: Mapped[AbuseState | None] = relationship(back_populates="customer", uselist=False)


class CustomerPolicy(Base):
    __tablename__ = "customer_policies"
    __table_args__ = (
        UniqueConstraint("customer_id", "version", name="uq_customer_policy_version"),
        Index("ix_customer_policies_current", "customer_id", "is_current"),
        Index("uq_customer_current_policy", "customer_id", unique=True, postgresql_where=text("is_current")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    miners: Mapped[int] = mapped_column(Integer, nullable=False)
    farms: Mapped[int] = mapped_column(Integer, nullable=False)
    maxconn: Mapped[int] = mapped_column(Integer, nullable=False)
    rate_per_min: Mapped[int] = mapped_column(Integer, nullable=False)
    burst: Mapped[int] = mapped_column(Integer, nullable=False)
    ips_mode: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'any'"))
    abuse_exempt: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    abuse_exempt_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    abuse_exempt_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    abuse_exempt_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="policies")


class CustomerIpPin(Base):
    __tablename__ = "customer_ip_pins"
    __table_args__ = (Index("ix_customer_ip_pins_customer_enabled", "customer_id", "enabled"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    ip_cidr: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="ip_pins")


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (Index("ix_events_subject", "subject_type", "subject_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'info'"))
    subject_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_log_resource", "resource_type", "resource_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    before_json: Mapped[JsonDict | None] = mapped_column(JSONB, nullable=True)
    after_json: Mapped[JsonDict | None] = mapped_column(JSONB, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_key: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)


class FirewallSnapshot(Base):
    __tablename__ = "firewall_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    backend: Mapped[str] = mapped_column(String(32), nullable=False)
    iptables_save_text: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class Backup(Base):
    __tablename__ = "backups"

    id: Mapped[int] = mapped_column(primary_key=True)
    backup_type: Mapped[str] = mapped_column(String(32), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))


class RestorePoint(Base):
    __tablename__ = "restore_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    restore_type: Mapped[str] = mapped_column(String(32), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("firewall_snapshots.id", ondelete="SET NULL"), nullable=True)
    backup_id: Mapped[int | None] = mapped_column(ForeignKey("backups.id", ondelete="SET NULL"), nullable=True)
    metadata_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)


class FirewallApply(Base):
    __tablename__ = "firewall_applies"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    apply_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    backend: Mapped[str] = mapped_column(String(32), nullable=False)
    restore_point_id: Mapped[int | None] = mapped_column(ForeignKey("restore_points.id", ondelete="SET NULL"), nullable=True)
    snapshot_before_id: Mapped[int | None] = mapped_column(ForeignKey("firewall_snapshots.id", ondelete="SET NULL"), nullable=True)
    snapshot_after_id: Mapped[int | None] = mapped_column(ForeignKey("firewall_snapshots.id", ondelete="SET NULL"), nullable=True)
    plan_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class FirewallRuleDesired(Base):
    __tablename__ = "firewall_rules_desired"

    id: Mapped[int] = mapped_column(primary_key=True)
    apply_id: Mapped[int | None] = mapped_column(ForeignKey("firewall_applies.id", ondelete="CASCADE"), nullable=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    lane_id: Mapped[int | None] = mapped_column(ForeignKey("lanes.id", ondelete="SET NULL"), nullable=True)
    table_name: Mapped[str] = mapped_column(String(32), nullable=False)
    chain_name: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_key: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_text: Mapped[str] = mapped_column(Text, nullable=False)
    rule_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class FirewallRuleLive(Base):
    __tablename__ = "firewall_rules_live"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("firewall_snapshots.id", ondelete="CASCADE"), nullable=False)
    table_name: Mapped[str] = mapped_column(String(32), nullable=False)
    chain_name: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_key: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_text: Mapped[str] = mapped_column(Text, nullable=False)
    rule_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class UsageSample(Base):
    __tablename__ = "usage_samples"
    __table_args__ = (Index("ix_usage_samples_customer_time", "customer_id", "sampled_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    lane_id: Mapped[int] = mapped_column(ForeignKey("lanes.id", ondelete="RESTRICT"), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    bytes_in: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    bytes_out: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    packets_in: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    packets_out: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    connlimit_rejects: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    hashlimit_rejects: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    pause_rejects: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    block_rejects: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    sampled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)


class PolicyEvent(Base):
    __tablename__ = "policy_events"
    __table_args__ = (Index("ix_policy_events_customer_seen", "customer_id", "seen_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    lane_id: Mapped[int | None] = mapped_column(ForeignKey("lanes.id", ondelete="SET NULL"), nullable=True)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    src_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    counter_delta: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    evidence_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class FlowSession(Base):
    __tablename__ = "flow_sessions"
    __table_args__ = (Index("ix_flow_sessions_customer_last_seen", "customer_id", "last_seen_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    lane_id: Mapped[int | None] = mapped_column(ForeignKey("lanes.id", ondelete="SET NULL"), nullable=True)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    src_ip: Mapped[str] = mapped_column(String(64), nullable=False)
    src_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dst_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'tcp'"))
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))


class FlowEvent(Base):
    __tablename__ = "flow_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    flow_session_id: Mapped[int | None] = mapped_column(ForeignKey("flow_sessions.id", ondelete="CASCADE"), nullable=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class WorkerEvent(Base):
    __tablename__ = "worker_events"
    __table_args__ = (Index("ix_worker_events_customer_seen", "customer_id", "seen_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    lane_id: Mapped[int | None] = mapped_column(ForeignKey("lanes.id", ondelete="SET NULL"), nullable=True)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    src_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    worker_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evidence_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))


class CustomerWorker(Base):
    __tablename__ = "customer_workers"
    __table_args__ = (Index("ix_customer_workers_customer_status", "customer_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    worker_name: Mapped[str] = mapped_column(String(255), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_src_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    seen_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'active'"))


class AbuseState(Base):
    __tablename__ = "abuse_states"
    __table_args__ = (Index("ix_abuse_states_status", "status"),)

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'normal'"))
    current_hot: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    current_unique_ips: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    current_unique_workers: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    first_seen_over: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_over: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_recovery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hard_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    policy_backup_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    restore_point_id: Mapped[int | None] = mapped_column(ForeignKey("restore_points.id", ondelete="SET NULL"), nullable=True)
    last_event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    customer: Mapped[Customer] = relationship(back_populates="abuse_state")


class AbuseEvent(Base):
    __tablename__ = "abuse_events"
    __table_args__ = (Index("ix_abuse_events_customer_created", "customer_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    policy_backup_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    restore_point_id: Mapped[int | None] = mapped_column(ForeignKey("restore_points.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)


class JobRun(Base):
    __tablename__ = "job_runs"
    __table_args__ = (Index("ix_job_runs_name_started", "job_name", "started_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    job_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    affected_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class SchedulerLock(Base):
    __tablename__ = "scheduler_locks"

    lock_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    owner: Mapped[str] = mapped_column(String(128), nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))


class Block(Base):
    __tablename__ = "blocks"
    __table_args__ = (Index("ix_blocks_status_expires", "status", "expires_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    ip_cidr: Mapped[str | None] = mapped_column(String(64), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    removed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)


class Pause(Base):
    __tablename__ = "pauses"
    __table_args__ = (Index("ix_pauses_status_expires", "status", "expires_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    removed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)


class Operator(Base, TimestampMixin):
    __tablename__ = "operators"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False, server_default=text("'operator'"))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    operator_id: Mapped[int] = mapped_column(ForeignKey("operators.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class NotificationTarget(Base, TimestampMixin):
    __tablename__ = "notification_targets"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    config_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("notification_targets.id", ondelete="CASCADE"), nullable=False)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value_json: Mapped[JsonDict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
