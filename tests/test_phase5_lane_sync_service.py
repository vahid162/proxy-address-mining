from __future__ import annotations

from dataclasses import dataclass, field

from mpf.repositories import lane_write_repo
from mpf.services import lane_sync_service


@dataclass
class _Lane:
    enabled: bool
    backend_port: int
    chain_prefix: str


@dataclass
class _Cfg:
    lanes: dict[str, _Lane]
    database: object = field(default_factory=lambda: type("DB", (), {"url": "postgresql://x"})())


class _FakeCursor:
    def __init__(self, db):
        self.db = db
        self.rows = []

    def execute(self, sql, params=None):
        sql = " ".join(sql.lower().split())
        if sql.startswith("select name, enabled, backend_port, chain_prefix, protocol from lanes"):
            self.rows = [tuple(x) for x in self.db["lanes"]]
            return
        if sql.startswith("insert into lanes"):
            self.db["lanes"].append((params[0], params[1], params[2], params[3], params[4]))
            return
        if sql.startswith("update lanes"):
            for i, row in enumerate(self.db["lanes"]):
                if row[0].lower() == params[4].lower():
                    self.db["lanes"][i] = (row[0], params[0], params[1], params[2], params[3])
                    break
            return
        if sql.startswith("insert into events"):
            self.db["events"] += 1
            return
        if sql.startswith("insert into audit_log"):
            self.db["audit"] += 1
            return

    def fetchall(self):
        return self.rows

    def __enter__(self): return self
    def __exit__(self, *a): return False


class _FakeConn:
    def __init__(self, db): self.db = db
    def cursor(self): return _FakeCursor(self.db)
    def transaction(self): return self
    def __enter__(self): return self
    def __exit__(self, *a): return False


def _patch_psycopg(monkeypatch, db):
    class FakePsy:
        @staticmethod
        def connect(*args, **kwargs):
            return _FakeConn(db)

    monkeypatch.setitem(__import__("sys").modules, "psycopg", FakePsy)


def _cfg():
    return _Cfg(lanes={"btc": _Lane(True, 60010, "MPFBTC"), "ltc": _Lane(False, 60020, "MPFLTC"), "zec": _Lane(False, 60015, "MPFZEC")})


def test_dry_run_writes_no_rows(monkeypatch):
    db = {"lanes": [], "events": 0, "audit": 0}
    _patch_psycopg(monkeypatch, db)
    result = lane_sync_service.sync_lane_config_db_only(_cfg(), dry_run=True)
    assert result.ok and result.would_create_lanes == 3
    assert db["lanes"] == [] and db["events"] == 0 and db["audit"] == 0


def test_sync_creates_and_updates_and_reports_stale(monkeypatch):
    db = {"lanes": [("btc", False, 60010, "OLD", "stratum"), ("xmr", True, 61000, "MPFX", "stratum")], "events": 0, "audit": 0}
    _patch_psycopg(monkeypatch, db)
    result = lane_sync_service.sync_lane_config_db_only(_cfg(), dry_run=False, yes=True)
    assert result.ok and "xmr" in result.stale_lanes
    assert {x[0] for x in db["lanes"]} >= {"btc", "ltc", "zec", "xmr"}
    btc = [x for x in db["lanes"] if x[0] == "btc"][0]
    assert btc[1] is True and btc[3] == "MPFBTC"
    assert db["events"] == 1 and db["audit"] == 1


def test_idempotent_no_duplicates(monkeypatch):
    db = {"lanes": [], "events": 0, "audit": 0}
    _patch_psycopg(monkeypatch, db)
    lane_sync_service.sync_lane_config_db_only(_cfg(), dry_run=False, yes=True)
    lane_sync_service.sync_lane_config_db_only(_cfg(), dry_run=False, yes=True)
    assert len([x for x in db["lanes"] if x[0] == "btc"]) == 1


def test_requires_yes_for_write():
    result = lane_sync_service.sync_lane_config_db_only(_cfg(), dry_run=False, yes=False)
    assert result.ok is False and "--yes" in result.message


def test_duplicate_enabled_backend_port_rejected():
    cfg = _Cfg(lanes={"btc": _Lane(True, 60010, "A"), "dup": _Lane(True, 60010, "B")})
    result = lane_sync_service.sync_lane_config_db_only(cfg, dry_run=True)
    assert result.ok is False and "duplicate backend_port" in result.message


def test_build_plan_reports_stale_only():
    plan = lane_write_repo.build_lane_sync_plan(_cfg(), {"stale": lane_write_repo.LaneSyncItem("stale", True, 62000, "S", "stratum")})
    assert len(plan.stale_items) == 1
