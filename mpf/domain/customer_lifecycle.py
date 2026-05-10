from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

ALLOWED_CUSTOMER_STATUSES = {"active", "paused", "expired", "deleted"}
ALLOWED_ACTIVATION_MODES = {"immediate", "first_connect"}
_CUSTOMER_KEY_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{2,63}$")


class DomainValidationError(ValueError):
    """Raised when a Phase 5 customer DTO is invalid."""


@dataclass(slots=True)
class CustomerLifecycleInput:
    activation_mode: str
    service_days: int | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    lifecycle_note: str | None = None

    def validate(self) -> None:
        if self.activation_mode not in ALLOWED_ACTIVATION_MODES:
            raise DomainValidationError("activation_mode must be immediate or first_connect")
        if self.service_days is not None and self.service_days <= 0:
            raise DomainValidationError("service_days must be positive")
        if self.lifecycle_note is not None and len(self.lifecycle_note.strip()) > 500:
            raise DomainValidationError("lifecycle_note is too long")

        if self.activation_mode == "first_connect":
            if self.starts_at is not None or self.expires_at is not None:
                raise DomainValidationError("first_connect lifecycle cannot pre-set starts_at or expires_at")
        elif self.starts_at is not None and self.expires_at is not None and self.expires_at <= self.starts_at:
            raise DomainValidationError("expires_at must be after starts_at")

    def immediate_window(self, now: datetime | None = None) -> tuple[datetime, datetime] | None:
        self.validate()
        if self.activation_mode != "immediate" or self.service_days is None:
            return None
        anchor = now or datetime.now(UTC)
        return anchor, anchor + timedelta(days=self.service_days)


def validate_customer_key(customer_key: str | None) -> None:
    if customer_key is None:
        return
    if not _CUSTOMER_KEY_RE.match(customer_key):
        raise DomainValidationError("customer_key must be 3..64 chars and URL-safe")


def validate_customer_status(status: str) -> None:
    if status not in ALLOWED_CUSTOMER_STATUSES:
        raise DomainValidationError("status must be active/paused/expired/deleted")
    if status == "pending_activation":
        raise DomainValidationError("pending_activation status is forbidden")
