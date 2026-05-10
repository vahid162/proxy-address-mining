from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import ip_network

from mpf.domain.customer_lifecycle import (
    CustomerLifecycleInput,
    DomainValidationError,
    validate_customer_key,
    validate_customer_status,
)

RESERVED_PORTS = {2015, 60010, 60015, 60020}
ALLOWED_IPS_MODE = {"any", "whitelist"}


def _require_positive_int(value: int, name: str) -> None:
    if value <= 0:
        raise DomainValidationError(f"{name} must be positive")


def validate_port(port: int) -> None:
    if port < 1 or port > 65535:
        raise DomainValidationError("port must be TCP 1..65535")
    if port in RESERVED_PORTS:
        raise DomainValidationError("port is reserved by runtime/backend")


@dataclass(slots=True)
class CustomerPolicyInput:
    miners: int
    farms: int
    maxconn: int
    rate_per_min: int
    burst: int
    ips_mode: str = "any"
    ip_whitelist: list[str] = field(default_factory=list)
    reason: str | None = None

    def validate(self) -> None:
        for key in ("miners", "farms", "maxconn", "rate_per_min", "burst"):
            _require_positive_int(getattr(self, key), key)
        if self.maxconn < self.miners:
            raise DomainValidationError("maxconn must be >= miners")
        if self.ips_mode not in ALLOWED_IPS_MODE:
            raise DomainValidationError("ips_mode must be any or whitelist")
        if self.ips_mode == "any" and self.ip_whitelist:
            raise DomainValidationError("ip_whitelist must be empty when ips_mode=any")
        for cidr in self.ip_whitelist:
            try:
                ip_network(cidr, strict=False)
            except ValueError as exc:
                raise DomainValidationError(f"invalid IP/CIDR: {cidr}") from exc
        if self.reason is not None and len(self.reason.strip()) > 500:
            raise DomainValidationError("reason is too long")


@dataclass(slots=True)
class CustomerCreateRequest:
    lane: str
    name: str
    port: int
    status: str
    policy: CustomerPolicyInput
    lifecycle: CustomerLifecycleInput
    customer_key: str | None = None

    def validate(self) -> None:
        if not self.lane.strip():
            raise DomainValidationError("lane name/key must be non-empty")
        validate_customer_key(self.customer_key)
        validate_port(self.port)
        validate_customer_status(self.status)
        self.policy.validate()
        self.lifecycle.validate()


@dataclass(slots=True)
class CustomerUpdateRequest:
    customer_key: str
    lane: str | None = None
    name: str | None = None
    status: str | None = None
    policy: CustomerPolicyInput | None = None
    lifecycle: CustomerLifecycleInput | None = None

    def validate(self) -> None:
        validate_customer_key(self.customer_key)
        if self.lane is not None and not self.lane.strip():
            raise DomainValidationError("lane name/key must be non-empty")
        if self.status is not None:
            validate_customer_status(self.status)
        if self.policy is not None:
            self.policy.validate()
        if self.lifecycle is not None:
            self.lifecycle.validate()


@dataclass(slots=True)
class CustomerRenewRequest:
    customer_key: str
    service_days: int
    lifecycle_note: str | None = None

    def validate(self) -> None:
        validate_customer_key(self.customer_key)
        _require_positive_int(self.service_days, "service_days")
        if self.lifecycle_note is not None and len(self.lifecycle_note.strip()) > 500:
            raise DomainValidationError("lifecycle_note is too long")


@dataclass(slots=True)
class CustomerDisableRequest:
    customer_key: str
    reason: str | None = None

    def validate(self) -> None:
        validate_customer_key(self.customer_key)
        if self.reason is not None and len(self.reason.strip()) > 500:
            raise DomainValidationError("reason is too long")


@dataclass(slots=True)
class CustomerDeleteRequest:
    customer_key: str
    reason: str | None = None
    soft_delete_only: bool = True

    def validate(self) -> None:
        validate_customer_key(self.customer_key)
        if not self.soft_delete_only:
            raise DomainValidationError("delete request must be soft-delete intent only")


@dataclass(slots=True)
class CustomerSetIpsRequest:
    customer_key: str
    ips_mode: str
    ip_whitelist: list[str] = field(default_factory=list)

    def validate(self) -> None:
        validate_customer_key(self.customer_key)
        if self.ips_mode not in ALLOWED_IPS_MODE:
            raise DomainValidationError("ips_mode must be any or whitelist")
        if self.ips_mode == "any" and self.ip_whitelist:
            raise DomainValidationError("ip_whitelist must be empty when ips_mode=any")
        for cidr in self.ip_whitelist:
            try:
                ip_network(cidr, strict=False)
            except ValueError as exc:
                raise DomainValidationError(f"invalid IP/CIDR: {cidr}") from exc
