from __future__ import annotations

import pytest

from mpf.domain.customer_lifecycle import CustomerLifecycleInput, DomainValidationError
from mpf.domain.customers import (
    CustomerCreateRequest,
    CustomerDeleteRequest,
    CustomerPolicyInput,
    CustomerSetIpsRequest,
)


def _valid_policy() -> CustomerPolicyInput:
    return CustomerPolicyInput(miners=10, farms=4, maxconn=10, rate_per_min=60, burst=20, ips_mode="whitelist", ip_whitelist=["10.1.0.0/24"])


def test_valid_immediate_lifecycle_input() -> None:
    lifecycle = CustomerLifecycleInput(activation_mode="immediate", service_days=30)
    lifecycle.validate()
    assert lifecycle.immediate_window() is not None


def test_valid_first_connect_lifecycle_input() -> None:
    lifecycle = CustomerLifecycleInput(activation_mode="first_connect", service_days=30)
    lifecycle.validate()


def test_first_connect_does_not_create_pending_activation_status() -> None:
    req = CustomerCreateRequest(
        lane="BTC",
        name="cust-a",
        port=32001,
        status="active",
        customer_key="cust_a",
        policy=_valid_policy(),
        lifecycle=CustomerLifecycleInput(activation_mode="first_connect", service_days=15),
    )
    req.validate()


def test_invalid_activation_mode_rejected() -> None:
    with pytest.raises(DomainValidationError):
        CustomerLifecycleInput(activation_mode="later", service_days=30).validate()


def test_invalid_service_days_rejected() -> None:
    with pytest.raises(DomainValidationError):
        CustomerLifecycleInput(activation_mode="immediate", service_days=0).validate()


@pytest.mark.parametrize("port", [0, 65536, 2015, 60010, 60015, 60020])
def test_reserved_or_invalid_ports_rejected(port: int) -> None:
    req = CustomerCreateRequest(
        lane="BTC",
        name="cust-a",
        port=port,
        status="active",
        customer_key="cust_a",
        policy=_valid_policy(),
        lifecycle=CustomerLifecycleInput(activation_mode="immediate", service_days=15),
    )
    with pytest.raises(DomainValidationError):
        req.validate()


def test_invalid_status_rejected() -> None:
    req = CustomerCreateRequest(
        lane="BTC",
        name="cust-a",
        port=32002,
        status="pending_activation",
        customer_key="cust_a",
        policy=_valid_policy(),
        lifecycle=CustomerLifecycleInput(activation_mode="first_connect", service_days=15),
    )
    with pytest.raises(DomainValidationError):
        req.validate()


def test_invalid_cidr_rejected() -> None:
    req = CustomerSetIpsRequest(customer_key="cust_a", ips_mode="whitelist", ip_whitelist=["10.0.0.1/99"])
    with pytest.raises(DomainValidationError):
        req.validate()


def test_maxconn_less_than_miners_rejected() -> None:
    policy = CustomerPolicyInput(miners=11, farms=4, maxconn=10, rate_per_min=60, burst=20)
    with pytest.raises(DomainValidationError):
        policy.validate()


def test_policy_fields_must_be_positive() -> None:
    policy = CustomerPolicyInput(miners=0, farms=4, maxconn=10, rate_per_min=60, burst=20)
    with pytest.raises(DomainValidationError):
        policy.validate()


def test_delete_request_is_soft_delete_intent_only() -> None:
    with pytest.raises(DomainValidationError):
        CustomerDeleteRequest(customer_key="cust_a", soft_delete_only=False).validate()


def test_set_ips_any_mode_rejects_non_empty_whitelist() -> None:
    req = CustomerSetIpsRequest(customer_key="cust_a", ips_mode="any", ip_whitelist=["10.1.0.0/24"])
    with pytest.raises(DomainValidationError):
        req.validate()
