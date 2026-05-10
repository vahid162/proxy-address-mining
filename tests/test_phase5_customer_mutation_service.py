from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from mpf.domain.customer_lifecycle import CustomerLifecycleInput
from mpf.domain.customers import CustomerCreateRequest, CustomerPolicyInput
from mpf.services import customer_mutation_service


class _FakeConfig:
    class database:
        url = "postgresql:///mpf"


@dataclass
class _FakeDB:
    lane_enabled: bool = True
    lane_exists: bool = True
    duplicate_port: bool = False
    duplicate_key: bool = False
    duplicate_deleted_port: bool = False
    customers: list[dict] = field(default_factory=list)
    policies: list[dict] = field(default_factory=list)
    pins: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    audits: list[dict] = field(default_factory=list)


class _FakeCursor:
    def __init__(self, db: _FakeDB) -> None:
        self.db = db
        self._result = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        q = " ".join(sql.lower().split())
        if "select id, enabled from lanes" in q:
            self._result = (1, self.db.lane_enabled) if self.db.lane_exists else None
        elif "select 1 from customers where port=" in q:
            self._result = (1,) if (self.db.duplicate_port or self.db.duplicate_deleted_port) else None
        elif "select 1 from customers where customer_key=" in q:
            self._result = (1,) if self.db.duplicate_key else None
        elif "insert into customers" in q:
            cid = len(self.db.customers) + 1
            self.db.customers.append({"id": cid, "params": params})
            self._result = (cid,)
        elif "insert into customer_policies" in q:
            self.db.policies.append({"params": params})
            self._result = None
        elif "insert into customer_ip_pins" in q:
            self.db.pins.append({"params": params})
            self._result = None
        elif "insert into events" in q:
            self.db.events.append({"params": params})
            self._result = None
        elif "insert into audit_log" in q:
            self.db.audits.append({"params": params})
            self._result = None
        else:
            raise AssertionError(f"unexpected SQL: {sql}")

    def fetchone(self):
        return self._result


class _FakeConn:
    def __init__(self, db: _FakeDB) -> None:
        self.db = db
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return _FakeCursor(self.db)

    def transaction(self):
        return self

    def commit(self):
        self.commits += 1


def _install_fake_psycopg(monkeypatch: pytest.MonkeyPatch, db: _FakeDB) -> _FakeConn:
    conn = _FakeConn(db)

    class _FakePsycopg:
        @staticmethod
        def connect(*args, **kwargs):
            return conn

    monkeypatch.setitem(__import__("sys").modules, "psycopg", _FakePsycopg)
    return conn


def _create_req(ips_mode: str = "any", ip_whitelist: list[str] | None = None, activation_mode: str = "immediate") -> CustomerCreateRequest:
    return CustomerCreateRequest(
        lane="btc",
        name="cust-a",
        port=32055,
        status="active",
        customer_key="cust_a",
        policy=CustomerPolicyInput(miners=10, farms=4, maxconn=10, rate_per_min=60, burst=20, ips_mode=ips_mode, ip_whitelist=ip_whitelist or []),
        lifecycle=CustomerLifecycleInput(activation_mode=activation_mode, service_days=30),
    )


def test_dry_run_writes_no_rows(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.create_db_only_customer(_FakeConfig(), _create_req(), dry_run=True)
    assert result.ok
    assert result.would_create_customer is True
    assert result.would_create_policy_version is True
    assert result.would_create_event is True
    assert result.would_create_audit is True
    assert not db.customers and not db.policies and not db.events and not db.audits and not db.pins


def test_create_immediate_writes_customer_policy_event_audit(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.create_db_only_customer(_FakeConfig(), _create_req())
    assert result.ok
    assert len(db.customers) == 1 and len(db.policies) == 1
    assert len(db.events) == 1 and len(db.audits) == 1


def test_transaction_path_does_not_require_explicit_commit_call(monkeypatch):
    db = _FakeDB()
    conn = _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.create_db_only_customer(_FakeConfig(), _create_req())
    assert result.ok
    assert conn.commits == 0


def test_create_first_connect_keeps_lifecycle_dates_null(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.create_db_only_customer(_FakeConfig(), _create_req(activation_mode="first_connect"))
    assert result.ok
    params = db.customers[0]["params"]
    assert params[4] is None and params[5] is None and params[9] is None


def test_whitelist_creates_ip_pins(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.create_db_only_customer(_FakeConfig(), _create_req(ips_mode="whitelist", ip_whitelist=["10.1.0.0/24", "10.2.0.0/24"]))
    assert result.ok
    assert len(db.pins) == 2


@pytest.mark.parametrize(
    ("db", "expected"),
    [
        (_FakeDB(lane_exists=False), "unknown lane"),
        (_FakeDB(lane_enabled=False), "lane is disabled"),
        (_FakeDB(duplicate_port=True), "duplicate port"),
        (_FakeDB(duplicate_deleted_port=True), "duplicate port"),
        (_FakeDB(duplicate_key=True), "duplicate customer_key"),
    ],
)
def test_validation_rejections(monkeypatch, db, expected):
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.create_db_only_customer(_FakeConfig(), _create_req())
    assert result.ok is False
    assert expected in result.message
