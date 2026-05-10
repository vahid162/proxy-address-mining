from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from mpf.domain.customer_lifecycle import CustomerLifecycleInput
from mpf.domain.customers import (
    CustomerCreateRequest,
    CustomerDeleteRequest,
    CustomerDisableRequest,
    CustomerPolicyInput,
    CustomerRenewRequest,
    CustomerSetIpsRequest,
    CustomerUpdateRequest,
)
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
    customer: dict | None = field(default_factory=lambda: {"id": 1, "customer_key": "cust_a", "name": "cust-a", "status": "active", "lane_id": 1, "activation_mode": "immediate", "service_days": 30, "deleted_at": None})
    current_policy: dict | None = field(default_factory=lambda: {"id": 10, "version": 1, "miners": 10, "farms": 4, "maxconn": 10, "rate_per_min": 60, "burst": 20, "ips_mode": "any", "reason": "r1"})
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
            self._result = (1,) if self.db.duplicate_port else None
        elif "select 1 from customers where customer_key=" in q:
            self._result = (1,) if self.db.duplicate_key else None
        elif "from customers c where c.customer_key=" in q:
            c = self.db.customer
            self._result = None if c is None else (c["id"], c["customer_key"], c["name"], c["status"], c["lane_id"], c["activation_mode"], c["service_days"], c["deleted_at"])
        elif "from customer_policies where customer_id=" in q and "is_current=true" in q:
            p = self.db.current_policy
            self._result = None if p is None else (p["id"], p["version"], p["miners"], p["farms"], p["maxconn"], p["rate_per_min"], p["burst"], p["ips_mode"], p["reason"])
        elif "insert into customers" in q:
            cid = len(self.db.customers) + 1
            self.db.customers.append({"id": cid, "params": params})
            self._result = (cid,)
        elif "insert into customer_policies" in q:
            self.db.policies.append({"params": params})
            self._result = None
        elif "update customer_policies set is_current=false" in q:
            self.db.policies.append({"deactivate": params})
            self._result = None
        elif "update customer_ip_pins set enabled=false" in q:
            self.db.pins.append({"clear": params})
            self._result = None
        elif "insert into customer_ip_pins" in q:
            self.db.pins.append({"params": params})
            self._result = None
        elif "update customers set" in q:
            self.db.customers.append({"update": params, "sql": q})
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return _FakeCursor(self.db)

    def transaction(self):
        return self


def _install_fake_psycopg(monkeypatch: pytest.MonkeyPatch, db: _FakeDB) -> None:
    conn = _FakeConn(db)

    class _FakePsycopg:
        @staticmethod
        def connect(*args, **kwargs):
            return conn

    monkeypatch.setitem(__import__("sys").modules, "psycopg", _FakePsycopg)


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


def test_create_dry_run_writes_no_rows_and_contract(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.create_db_only_customer(_FakeConfig(), _create_req(), dry_run=True)
    assert result.ok
    assert result.would_create_customer is True and result.would_mutate_customer is True
    assert result.would_create_policy_version is True and result.would_create_event is True and result.would_create_audit is True
    assert not db.customers and not db.policies and not db.events and not db.audits and not db.pins


def test_create_immediate_writes_customer_policy_event_audit(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.create_db_only_customer(_FakeConfig(), _create_req())
    assert result.ok
    assert len(db.customers) == 1 and len(db.policies) == 1 and len(db.events) == 1 and len(db.audits) == 1


def test_create_first_connect_keeps_lifecycle_dates_null(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.create_db_only_customer(_FakeConfig(), _create_req(activation_mode="first_connect"))
    assert result.ok
    params = db.customers[0]["params"]
    assert params[4] is None and params[5] is None and params[9] is None


def test_create_whitelist_creates_ip_pins(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.create_db_only_customer(_FakeConfig(), _create_req(ips_mode="whitelist", ip_whitelist=["10.1.0.0/24", "10.2.0.0/24"]))
    assert result.ok
    assert len([x for x in db.pins if "params" in x]) == 2


@pytest.mark.parametrize(
    ("db", "expected"),
    [
        (_FakeDB(lane_exists=False), "unknown lane"),
        (_FakeDB(lane_enabled=False), "lane is disabled"),
        (_FakeDB(duplicate_port=True), "duplicate port"),
        (_FakeDB(duplicate_key=True), "duplicate customer_key"),
    ],
)
def test_create_validation_rejections(monkeypatch, db, expected):
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.create_db_only_customer(_FakeConfig(), _create_req())
    assert result.ok is False and expected in result.message


def test_update_creates_policy_version_2(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    req = CustomerUpdateRequest(customer_key="cust_a", policy=CustomerPolicyInput(miners=20, farms=4, maxconn=20, rate_per_min=80, burst=30, ips_mode="any"))
    result = customer_mutation_service.update_db_only_customer(_FakeConfig(), req)
    assert result.ok
    inserts = [x for x in db.policies if "params" in x]
    assert any("deactivate" in x for x in db.policies)
    assert inserts[-1]["params"][1] == 2


def test_update_rejects_deleted_status(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.update_db_only_customer(_FakeConfig(), CustomerUpdateRequest(customer_key="cust_a", status="deleted"))
    assert result.ok is False and "use soft_delete_customer" in result.message


def test_update_rejects_policy_ip_changes(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    req = CustomerUpdateRequest(customer_key="cust_a", policy=CustomerPolicyInput(miners=10, farms=4, maxconn=10, rate_per_min=60, burst=20, ips_mode="whitelist", ip_whitelist=["10.1.0.0/24"]))
    result = customer_mutation_service.update_db_only_customer(_FakeConfig(), req)
    assert result.ok is False and "use set_customer_ips" in result.message




def test_update_rejects_changing_ips_mode_from_whitelist_to_any(monkeypatch):
    db = _FakeDB(current_policy={"id": 10, "version": 1, "miners": 10, "farms": 4, "maxconn": 10, "rate_per_min": 60, "burst": 20, "ips_mode": "whitelist", "reason": "r1"})
    _install_fake_psycopg(monkeypatch, db)
    req = CustomerUpdateRequest(customer_key="cust_a", policy=CustomerPolicyInput(miners=11, farms=4, maxconn=11, rate_per_min=61, burst=21, ips_mode="any"))
    result = customer_mutation_service.update_db_only_customer(_FakeConfig(), req)
    assert result.ok is False and "use set_customer_ips" in result.message


def test_update_allows_numeric_policy_update_when_ips_mode_any_stable(monkeypatch):
    db = _FakeDB(current_policy={"id": 10, "version": 1, "miners": 10, "farms": 4, "maxconn": 10, "rate_per_min": 60, "burst": 20, "ips_mode": "any", "reason": "r1"})
    _install_fake_psycopg(monkeypatch, db)
    req = CustomerUpdateRequest(customer_key="cust_a", policy=CustomerPolicyInput(miners=12, farms=5, maxconn=12, rate_per_min=90, burst=22, ips_mode="any"))
    result = customer_mutation_service.update_db_only_customer(_FakeConfig(), req)
    assert result.ok is True

def test_renew_updates_lifecycle_immediate(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.renew_db_only_customer(_FakeConfig(), CustomerRenewRequest(customer_key="cust_a", service_days=45))
    assert result.ok and any("activated_at" in x["sql"] for x in db.customers if "sql" in x)


def test_disable_sets_paused(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.disable_db_only_customer(_FakeConfig(), CustomerDisableRequest(customer_key="cust_a"))
    assert result.ok and any("status='paused'" in x["sql"] for x in db.customers if "sql" in x)


def test_soft_delete_sets_deleted(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.soft_delete_db_only_customer(_FakeConfig(), CustomerDeleteRequest(customer_key="cust_a"))
    assert result.ok and any("status='deleted'" in x["sql"] and "deleted_at=now()" in x["sql"] for x in db.customers if "sql" in x)


def test_set_ips_whitelist_writes_pins(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.set_ips_db_only_customer(_FakeConfig(), CustomerSetIpsRequest(customer_key="cust_a", ips_mode="whitelist", ip_whitelist=["10.1.0.0/24"]))
    assert result.ok and any("clear" in x for x in db.pins) and any("params" in x for x in db.pins)


def test_set_ips_any_clears_pins(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.set_ips_db_only_customer(_FakeConfig(), CustomerSetIpsRequest(customer_key="cust_a", ips_mode="any"))
    assert result.ok and any("clear" in x for x in db.pins)


@pytest.mark.parametrize(
    "fn,req",
    [
        (customer_mutation_service.update_db_only_customer, CustomerUpdateRequest(customer_key="cust_a", name="x")),
        (customer_mutation_service.renew_db_only_customer, CustomerRenewRequest(customer_key="cust_a", service_days=10)),
        (customer_mutation_service.disable_db_only_customer, CustomerDisableRequest(customer_key="cust_a")),
        (customer_mutation_service.soft_delete_db_only_customer, CustomerDeleteRequest(customer_key="cust_a")),
        (customer_mutation_service.set_ips_db_only_customer, CustomerSetIpsRequest(customer_key="cust_a", ips_mode="any")),
    ],
)
def test_dry_run_writes_no_rows(monkeypatch, fn, req):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    result = fn(_FakeConfig(), req, dry_run=True)
    assert result.ok and result.firewall_change == "no" and result.nat_change == "no" and result.runtime_change == "no"
    assert not db.events and not db.audits and not db.policies and not [x for x in db.customers if "update" in x]


def test_deleted_customer_rejected(monkeypatch):
    db = _FakeDB(customer={"id": 1, "customer_key": "cust_a", "name": "cust-a", "status": "deleted", "lane_id": 1, "activation_mode": "immediate", "service_days": 30, "deleted_at": "2020"})
    _install_fake_psycopg(monkeypatch, db)
    result = customer_mutation_service.disable_db_only_customer(_FakeConfig(), CustomerDisableRequest(customer_key="cust_a"))
    assert result.ok is False


def test_event_audit_created(monkeypatch):
    db = _FakeDB()
    _install_fake_psycopg(monkeypatch, db)
    customer_mutation_service.disable_db_only_customer(_FakeConfig(), CustomerDisableRequest(customer_key="cust_a"))
    assert len(db.events) == 1 and len(db.audits) == 1
