from __future__ import annotations

from types import SimpleNamespace

import pytest

from mpf.db import DBQueryResult
from mpf.domain.customers import CustomerDisableRequest, CustomerPolicyInput, CustomerUpdateRequest
from mpf.services import customer_dry_run_readiness_service as svc


def _cfg():
    return SimpleNamespace(database=SimpleNamespace(url="postgresql:///mpf"))


def _customer(status="active", deleted_at=None):
    return {"id": 7, "customer_key": "limited-btc-001", "status": status, "deleted_at": deleted_at}


def _policy(ips_mode="any"):
    return {"id": 3, "version": 1, "miners": 10, "farms": 4, "maxconn": 10, "rate_per_min": 60, "burst": 20, "ips_mode": ips_mode, "reason": "r"}


def _policy_input(ips_mode="any", ip_whitelist=None):
    return CustomerPolicyInput(miners=11, farms=4, maxconn=11, rate_per_min=61, burst=21, ips_mode=ips_mode, ip_whitelist=ip_whitelist or [])


def test_disable_dry_run_uses_query_database_params(monkeypatch):
    calls = []
    monkeypatch.setattr(svc, "query_database_params", lambda cfg, sql, params=(): calls.append((sql, params)) or DBQueryResult(True, [_customer()], "OK"))
    res = svc.dry_run_disable_customer(_cfg(), CustomerDisableRequest(customer_key="limited-btc-001"))
    assert res.ok and res.message == "DRY_RUN_OK"
    assert res.customer_id == 7 and res.would_mutate_customer is True
    assert res.would_create_event is True and res.would_create_audit is True
    assert len(calls) == 1 and calls[0][1] == ("limited-btc-001",)


def test_update_status_only_dry_run_uses_query_database_params(monkeypatch):
    calls = []
    monkeypatch.setattr(svc, "query_database_params", lambda cfg, sql, params=(): calls.append((sql, params)) or DBQueryResult(True, [_customer()], "OK"))
    res = svc.dry_run_update_customer(_cfg(), CustomerUpdateRequest(customer_key="limited-btc-001", status="paused"))
    assert res.ok and res.message == "DRY_RUN_OK"
    assert res.would_mutate_customer is True and res.would_create_policy_version is False
    assert len(calls) == 1


def test_update_with_policy_reads_current_policy(monkeypatch):
    calls = []
    def fake(cfg, sql, params=()):
        calls.append((sql, params))
        if len(calls) == 1:
            return DBQueryResult(True, [_customer()], "OK")
        return DBQueryResult(True, [_policy()], "OK")
    monkeypatch.setattr(svc, "query_database_params", fake)
    res = svc.dry_run_update_customer(_cfg(), CustomerUpdateRequest(customer_key="limited-btc-001", policy=_policy_input()))
    assert res.ok and res.would_create_policy_version is True
    assert len(calls) == 2 and calls[1][1] == (7,)


def test_update_with_lane_reads_lane_and_fails_if_disabled(monkeypatch):
    calls = []
    def fake(cfg, sql, params=()):
        calls.append((sql, params))
        if len(calls) == 1:
            return DBQueryResult(True, [_customer()], "OK")
        return DBQueryResult(True, [{"id": 1, "enabled": False}], "OK")
    monkeypatch.setattr(svc, "query_database_params", fake)
    res = svc.dry_run_update_customer(_cfg(), CustomerUpdateRequest(customer_key="limited-btc-001", lane="btc"))
    assert res.ok is False and res.message == "lane is disabled: btc"
    assert calls[-1][1] == ("btc",)


@pytest.mark.parametrize("rows,message", [([], "customer not found"), ([_customer(status="deleted")], "deleted customer cannot be mutated"), ([_customer(deleted_at="2026")], "deleted customer cannot be mutated")])
def test_customer_missing_or_deleted_fails_closed(monkeypatch, rows, message):
    monkeypatch.setattr(svc, "query_database_params", lambda *a, **k: DBQueryResult(True, rows, "OK"))
    res = svc.dry_run_disable_customer(_cfg(), CustomerDisableRequest(customer_key="limited-btc-001"))
    assert res.ok is False and res.message == message


def test_read_error_fails_closed(monkeypatch):
    monkeypatch.setattr(svc, "query_database_params", lambda *a, **k: DBQueryResult(False, [], "read failed"))
    res = svc.dry_run_update_customer(_cfg(), CustomerUpdateRequest(customer_key="limited-btc-001", status="active"))
    assert res.ok is False and res.message == "read failed"


def test_update_policy_ip_changes_fail_closed(monkeypatch):
    calls = []
    def fake(cfg, sql, params=()):
        calls.append((sql, params))
        return DBQueryResult(True, [_customer()] if len(calls) == 1 else [_policy("any")], "OK")
    monkeypatch.setattr(svc, "query_database_params", fake)
    res = svc.dry_run_update_customer(_cfg(), CustomerUpdateRequest(customer_key="limited-btc-001", policy=_policy_input(ips_mode="whitelist", ip_whitelist=["10.0.0.0/24"])))
    assert res.ok is False and res.message == "use set_customer_ips"
