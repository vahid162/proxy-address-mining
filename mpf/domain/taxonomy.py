from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import uuid4


class EventSeverity(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SubjectType(StrEnum):
    SYSTEM = "system"
    SERVER = "server"
    CONFIG = "config"
    LANE = "lane"
    CUSTOMER = "customer"
    CUSTOMER_POLICY = "customer_policy"
    FIREWALL = "firewall"
    FIREWALL_APPLY = "firewall_apply"
    RESTORE_POINT = "restore_point"
    USAGE = "usage"
    POLICY_EVENT = "policy_event"
    WORKER = "worker"
    WORKER_POLICY = "worker_policy"
    WORKER_BLOCK = "worker_block"
    ABUSE = "abuse"
    JOB = "job"
    BLOCK = "block"
    PAUSE = "pause"
    BACKUP = "backup"
    NOTIFICATION = "notification"


class ActorType(StrEnum):
    OPERATOR = "operator"
    BUYER_USER = "buyer_user"
    API_TOKEN = "api_token"
    JOB = "job"
    SYSTEM = "system"
    TELEGRAM_BOT = "telegram_bot"
    UI = "ui"
    INTERNAL_API = "internal_api"
    MIGRATION = "migration"
    IMPORTER = "importer"


class ResourceType(StrEnum):
    CONFIG = "config"
    DATABASE = "database"
    LANE = "lane"
    CUSTOMER = "customer"
    CUSTOMER_POLICY = "customer_policy"
    FIREWALL = "firewall"
    FIREWALL_APPLY = "firewall_apply"
    RESTORE_POINT = "restore_point"
    ABUSE = "abuse"
    JOB = "job"
    BLOCK = "block"
    PAUSE = "pause"
    BACKUP = "backup"
    WORKER_BLOCK = "worker_block"


class AuditAction(StrEnum):
    READ = "read"
    INSPECT = "inspect"
    STATUS = "status"
    PLAN = "plan"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    APPLY = "apply"
    VERIFY = "verify"
    ROLLBACK = "rollback"


class CustomerStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    DELETED = "deleted"
    SUSPENDED = "suspended"
    PENDING = "pending"


class JobStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEGRADED = "degraded"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class AbuseStatus(StrEnum):
    NORMAL = "normal"
    OVER_TRACKING = "over_tracking"
    OVER_GRACE = "over_grace"
    HARD = "hard"
    EXEMPT_UNTIL = "exempt_until"
    DISABLED_MANUAL = "disabled_manual"


class FirewallApplyStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    APPLIED = "applied"
    VERIFIED = "verified"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


class PolicyEventType(StrEnum):
    CONNLIMIT_REJECT = "connlimit_reject"
    HASHLIMIT_REJECT = "hashlimit_reject"
    PAUSE_REJECT = "pause_reject"
    BLOCK_REJECT = "block_reject"
    WHITELIST_REJECT = "whitelist_reject"
    BACKEND_GUARD_REJECT = "backend_guard_reject"
    UNKNOWN_REJECT = "unknown_reject"


class WorkerEventType(StrEnum):
    AUTHORIZE_OBSERVED = "worker.authorize.observed"
    SUBMIT_OBSERVED = "worker.submit.observed"
    IDENTITY_OBSERVED = "worker.identity.observed"
    IDENTITY_MISMATCH = "worker.identity.mismatch"
    POLICY_REPORTED = "worker.policy.reported"
    POLICY_BLOCK_DETECTED = "worker.policy.block_detected"
    ENFORCEMENT_BLOCKED = "worker.enforcement.blocked"
    ENFORCEMENT_REJECTED = "worker.enforcement.rejected"
    ENFORCEMENT_FAILED = "worker.enforcement.failed"


@dataclass(frozen=True)
class RequestContext:
    """Stable request metadata passed from interfaces to services.

    Phase 3 is read-only, but keeping the context shape now prevents later UI,
    API, Telegram, and job entrypoints from inventing incompatible audit fields.
    """

    correlation_id: str = field(default_factory=lambda: uuid4().hex)
    actor_type: ActorType = ActorType.SYSTEM
    actor_id: str | None = None
    source_interface: str = "cli"
    source_ip: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    reason: str | None = None
    confirmed: bool = False
