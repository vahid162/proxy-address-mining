"""Domain DTOs for read-only customer block control-intent preflight."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from mpf.domain.customer_lifecycle import DomainValidationError, validate_customer_key


ALLOWED_BLOCK_CONTROL_SCOPES = {"customer"}


@dataclass(slots=True)
class CustomerBlockPreflightRequest:
    """Read-only request describing a future customer block control intent.

    Block is intentionally modeled as a control intent, not as a customer
    lifecycle status. This DTO only validates the requested intent shape; the
    service layer remains responsible for read-only target resolution.
    """

    customer_key: str
    reason: str
    scope: str = "customer"
    expires_at: datetime | None = None
    operator: str | None = None

    def validate(self) -> None:
        validate_customer_key(self.customer_key)
        if self.scope not in ALLOWED_BLOCK_CONTROL_SCOPES:
            raise DomainValidationError("block scope must be customer")
        if not self.reason or not self.reason.strip():
            raise DomainValidationError("block reason must be non-empty")
        if len(self.reason.strip()) > 500:
            raise DomainValidationError("block reason is too long")
        if self.operator is not None and len(self.operator.strip()) > 128:
            raise DomainValidationError("operator is too long")
