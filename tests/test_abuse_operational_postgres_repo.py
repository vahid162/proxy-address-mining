from __future__ import annotations

from datetime import UTC, datetime, timedelta

from mpf.config import MPFConfig
from mpf.db import DBQueryResult
from mpf.domain.abuse_operational import OperationalAbuseEvidence, evaluate_operational_abuse
from mpf.repositories.abuse_operational_postgres_repo import PostgresAbuseOperationalRepo
from mpf.services.abuse_operational_service import events_report, run_abuse_cycle, status_report

NOW = datetime(2026, 6, 2, 12, 0, tzinfo=UTC)


def cfg() -> MPFConfig:
    return MPFConfig.model_validate({"server": {"name": "test"}, "database": {"url": "postgresql://test/mpf"}, "lanes": {"btc": {"enabled": True, "backend_port": 60010, "chain_prefix": "BTC"}}})


def row(**overrides):
    base = {"customer_id": 1, "lane_id": 1, "customer_key": "btc-1", "port": 20101, "lane_enabled": True, "miners": 10, "farms": 2,
            "policy_expires_at": NOW + timedelta(days=1), "abuse_exempt": False, "abuse_exempt_reason": None, "abuse_exempt_until": None,
            "abuse_status": "normal", "first_seen_over": None, "last_seen_over": None, "last_recovery_at": None, "hard_applied_at": None}
    return {**base, **overrides}


def fresh(hot=11):
    return OperationalAbuseEvidence(hot_sessions=hot, unique_source_ips=1, unique_workers=1, observed_at=NOW, collected_at=NOW, source="controlled_operator_package")


def test_repo_query_scans_only_active_non_deleted_current_policy_enabled_lane_and_non_expired(monkeypatch) -> None:
    seen = {}
    def query(_cfg, sql, params=()):
        seen["sql"], seen["params"] = sql, params
        return DBQueryResult(True, [row(), row(customer_id=2, customer_key="btc-2", port=20102)], "OK")
    monkeypatch.setattr("mpf.repositories.abuse_operational_postgres_repo.query_database_params", query)
    customers = PostgresAbuseOperationalRepo(cfg()).list_eligible_customers(NOW)
    assert [item.customer_key for item in customers] == ["btc-1", "btc-2"]
    assert "l.enabled = true" in seen["sql"]
    assert "c.status = 'active'" in seen["sql"] and "c.deleted_at is null" in seen["sql"]
    assert "p.is_current = true" in seen["sql"] and "c.expires_at >= %s" in seen["sql"]


def test_db_counters_are_visibility_only_and_missing_evidence_never_hardens(monkeypatch) -> None:
    monkeypatch.setattr("mpf.repositories.abuse_operational_postgres_repo.query_database_params", lambda *_args, **_kwargs: DBQueryResult(True, [row(abuse_status="over_tracking", first_seen_over=NOW - timedelta(hours=2))], "OK"))
    report = run_abuse_cycle(PostgresAbuseOperationalRepo(cfg()), execute=False, now=NOW)
    assert report["evaluations"][0]["result"] == "evaluation_failed"
    assert report["evaluations"][0]["blockers"] == ["missing_evidence"]
    assert report["hard_applied_count"] == 0


def test_stale_explicit_evidence_records_evaluation_failed_and_never_hardens(monkeypatch) -> None:
    stale = OperationalAbuseEvidence(hot_sessions=99, unique_source_ips=1, unique_workers=1, observed_at=NOW - timedelta(minutes=6), collected_at=NOW, source="controlled_operator_package")
    monkeypatch.setattr("mpf.repositories.abuse_operational_postgres_repo.query_database_params", lambda *_args, **_kwargs: DBQueryResult(True, [row(abuse_status="over_tracking", first_seen_over=NOW - timedelta(hours=2))], "OK"))
    repo = PostgresAbuseOperationalRepo(cfg(), evidence_by_customer_id={1: stale})
    report = run_abuse_cycle(repo, execute=False, now=NOW)
    assert report["evaluations"][0]["result"] == "stale_evidence"
    assert report["evaluations"][0]["requires_controlled_hard"] is False


class Cursor:
    def __init__(self, statements): self.statements = statements
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def execute(self, sql, params=()): self.statements.append((" ".join(sql.split()), params))


class Conn:
    def __init__(self, statements): self.statements = statements
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def transaction(self): return self
    def cursor(self): return Cursor(self.statements)


def test_controlled_execute_writes_only_allowed_tables_and_persists_transition_and_job(monkeypatch) -> None:
    statements = []
    monkeypatch.setattr("mpf.repositories.abuse_operational_postgres_repo.query_database_params", lambda *_args, **_kwargs: DBQueryResult(True, [row()], "OK"))
    repo = PostgresAbuseOperationalRepo(cfg(), evidence_by_customer_id={1: fresh()})
    monkeypatch.setattr(repo, "_connect", lambda: Conn(statements))
    report = run_abuse_cycle(repo, execute=True, now=NOW)
    sql = " ".join(item[0] for item in statements).lower()
    assert report["evaluations"][0]["proposed_state"] == "over_tracking"
    assert "insert into abuse_states" in sql and "insert into abuse_events" in sql and "insert into job_runs" in sql
    for forbidden in ("customers", "customer_policies", "lanes", "hard_applied_at = excluded.hard_applied_at"):
        assert f"insert into {forbidden}" not in sql and f"update {forbidden}" not in sql


def test_sustained_miner_over_records_hard_plan_event_without_state_hard_apply(monkeypatch) -> None:
    statements = []
    monkeypatch.setattr("mpf.repositories.abuse_operational_postgres_repo.query_database_params", lambda *_args, **_kwargs: DBQueryResult(True, [row(abuse_status="over_tracking", first_seen_over=NOW - timedelta(seconds=3600))], "OK"))
    repo = PostgresAbuseOperationalRepo(cfg(), evidence_by_customer_id={1: fresh()})
    monkeypatch.setattr(repo, "_connect", lambda: Conn(statements))
    report = run_abuse_cycle(repo, execute=True, now=NOW)
    sql = " ".join(item[0] for item in statements).lower()
    assert report["evaluations"][0]["result"] == "hard_planned"
    assert "insert into abuse_events" in sql and "insert into abuse_states" not in sql
    assert report["hard_applied_count"] == 0


def test_read_and_write_failures_are_blocked(monkeypatch) -> None:
    monkeypatch.setattr("mpf.repositories.abuse_operational_postgres_repo.query_database_params", lambda *_args, **_kwargs: DBQueryResult(False, [], "down"))
    assert run_abuse_cycle(PostgresAbuseOperationalRepo(cfg()), execute=False, now=NOW)["blockers"] == ["database_read_failed"]
    assert status_report(PostgresAbuseOperationalRepo(cfg()))["blockers"] == ["database_read_failed"]
    assert events_report(PostgresAbuseOperationalRepo(cfg()))["blockers"] == ["database_read_failed"]

    monkeypatch.setattr("mpf.repositories.abuse_operational_postgres_repo.query_database_params", lambda *_args, **_kwargs: DBQueryResult(True, [row()], "OK"))
    repo = PostgresAbuseOperationalRepo(cfg(), evidence_by_customer_id={1: fresh()})
    monkeypatch.setattr(repo, "_connect", lambda: (_ for _ in ()).throw(RuntimeError("write down")))
    report = run_abuse_cycle(repo, execute=True, now=NOW)
    assert report["status"] == "BLOCKED" and any("database_write_failed" in blocker for blocker in report["blockers"])


def test_dry_run_performs_no_db_writes(monkeypatch) -> None:
    monkeypatch.setattr("mpf.repositories.abuse_operational_postgres_repo.query_database_params", lambda *_args, **_kwargs: DBQueryResult(True, [row()], "OK"))
    repo = PostgresAbuseOperationalRepo(cfg(), evidence_by_customer_id={1: fresh()})
    monkeypatch.setattr(repo, "_connect", lambda: (_ for _ in ()).throw(AssertionError("dry-run must not connect for writes")))
    report = run_abuse_cycle(repo, execute=False, now=NOW)
    assert report["execute"] is False and report["evaluations"][0]["proposed_state"] == "over_tracking"


def test_missing_evidence_execute_records_evaluation_failed_without_hardening(monkeypatch) -> None:
    statements = []
    monkeypatch.setattr("mpf.repositories.abuse_operational_postgres_repo.query_database_params", lambda *_args, **_kwargs: DBQueryResult(True, [row(abuse_status="over_tracking", first_seen_over=NOW - timedelta(hours=2))], "OK"))
    repo = PostgresAbuseOperationalRepo(cfg())
    monkeypatch.setattr(repo, "_connect", lambda: Conn(statements))
    report = run_abuse_cycle(repo, execute=True, now=NOW)
    sql = " ".join(item[0] for item in statements).lower()
    assert report["evaluations"][0]["result"] == "evaluation_failed"
    assert "insert into abuse_events" in sql and "insert into job_runs" in sql
    assert "insert into abuse_states" not in sql and report["hard_applied_count"] == 0


def test_each_db_only_transition_persists_without_setting_hard_applied_at(monkeypatch) -> None:
    scenarios = [
        (row(), fresh(11), "over_tracking"),
        (row(abuse_status="over_tracking", first_seen_over=NOW - timedelta(seconds=20)), fresh(2), "over_grace"),
        (row(abuse_status="over_grace", last_recovery_at=NOW - timedelta(seconds=901)), fresh(2), "normal"),
        (row(abuse_status="over_grace", last_recovery_at=NOW - timedelta(seconds=20)), fresh(11), "over_tracking"),
    ]
    for source_row, evidence, expected in scenarios:
        statements = []
        monkeypatch.setattr("mpf.repositories.abuse_operational_postgres_repo.query_database_params", lambda *_args, _row=source_row, **_kwargs: DBQueryResult(True, [_row], "OK"))
        repo = PostgresAbuseOperationalRepo(cfg(), evidence_by_customer_id={1: evidence})
        monkeypatch.setattr(repo, "_connect", lambda: Conn(statements))
        report = run_abuse_cycle(repo, execute=True, now=NOW)
        assert report["evaluations"][0]["proposed_state"] == expected
        state_params = next(params for sql, params in statements if "insert into abuse_states" in sql.lower())
        assert state_params[1] == expected
        assert "hard_applied_at = abuse_states.hard_applied_at" in " ".join(sql for sql, _ in statements)


def test_status_and_events_reports_use_db_visibility_fields_and_limit(monkeypatch) -> None:
    calls = []
    def query(_cfg, sql, params=()):
        calls.append((sql, params))
        if "select ae.customer_id" in sql:
            return DBQueryResult(True, [{"customer_id": 1, "event_type": "abuse.evaluation_failed", "old_status": "normal", "new_status": "normal", "created_at": NOW, "created_by": "operator", "evidence_json": {}}], "OK")
        return DBQueryResult(True, [{"customer_id": 1, "customer_key": "btc-1", "lane": "btc", "port": 20101, "status": "normal", "current_hot": 0, "current_unique_ips": 0, "current_unique_workers": 0, "first_seen_over": None, "last_seen_over": None, "last_recovery_at": None, "hard_applied_at": None, "latest_event": "abuse.evaluation_failed", "warnings": [], "blockers": []}], "OK")
    monkeypatch.setattr("mpf.repositories.abuse_operational_postgres_repo.query_database_params", query)
    repo = PostgresAbuseOperationalRepo(cfg())
    state = status_report(repo)["states"][0]
    events = events_report(repo, limit=50, customer_key="btc-1")["events"]
    assert state["lane"] == "btc" and state["current_hot"] == 0 and state["latest_event"] == "abuse.evaluation_failed"
    assert events[0]["created_by"] == "operator"
    assert "limit 50" in calls[-1][0].lower() and calls[-1][1] == ("btc-1",)
