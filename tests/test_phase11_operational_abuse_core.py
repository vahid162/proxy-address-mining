from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from typer.testing import CliRunner

from mpf.domain.abuse_operational import OperationalAbuseCustomer, OperationalAbuseEvidence, OperationalAbusePolicy, OperationalAbuseState, evaluate_operational_abuse
from mpf.interfaces.cli import app
from mpf.repositories.abuse_operational_repo import InMemoryAbuseOperationalRepo
from mpf.services.abuse_operational_service import apply_controlled_hard, run_abuse_cycle

NOW = datetime(2026, 6, 2, 12, 0, tzinfo=UTC)


def customer(*, status: str = "normal", hot: int | None = 2, ips: int | None = 1, workers: int | None = 1, observed_at: datetime | None = NOW, collected_at: datetime | None = NOW, first_seen: datetime | None = None, recovery: datetime | None = None, evidence: bool = True) -> OperationalAbuseCustomer:
    return OperationalAbuseCustomer(customer_id=1, lane_id=1, customer_key="btc-1", port=20101, active=True, lane_enabled=True, policy=OperationalAbusePolicy(miners=10, farms=2, expires_at=NOW + timedelta(days=1)), state=OperationalAbuseState(status=status, first_seen_over=first_seen, last_recovery_at=recovery), evidence=None if not evidence else OperationalAbuseEvidence(hot_sessions=hot, unique_source_ips=ips, unique_workers=workers, observed_at=observed_at, collected_at=collected_at))


def test_required_state_transitions() -> None:
    assert evaluate_operational_abuse(customer(hot=11), now=NOW).proposed_state == "over_tracking"
    assert evaluate_operational_abuse(customer(status="over_tracking", hot=2, first_seen=NOW - timedelta(seconds=20)), now=NOW).proposed_state == "over_grace"
    assert evaluate_operational_abuse(customer(status="over_grace", hot=2, recovery=NOW - timedelta(seconds=901)), now=NOW).proposed_state == "normal"
    assert evaluate_operational_abuse(customer(status="over_grace", hot=11, recovery=NOW - timedelta(seconds=20)), now=NOW).proposed_state == "over_tracking"


def test_hard_requires_sustained_miner_abuse_about_one_hour() -> None:
    before = evaluate_operational_abuse(customer(status="over_tracking", hot=11, first_seen=NOW - timedelta(seconds=3599)), now=NOW)
    after = evaluate_operational_abuse(customer(status="over_tracking", hot=11, first_seen=NOW - timedelta(seconds=3600)), now=NOW)
    assert before.proposed_state == "over_tracking" and not before.requires_controlled_hard
    assert after.proposed_state == "hard" and after.requires_controlled_hard and after.result == "hard_planned"


def test_farms_worker_missing_and_stale_evidence_never_harden() -> None:
    farms = evaluate_operational_abuse(customer(status="over_tracking", hot=2, ips=99, first_seen=NOW - timedelta(hours=2)), now=NOW)
    workers = evaluate_operational_abuse(customer(status="over_tracking", hot=2, workers=99, first_seen=NOW - timedelta(hours=2)), now=NOW)
    missing = evaluate_operational_abuse(customer(status="over_tracking", evidence=False, first_seen=NOW - timedelta(hours=2)), now=NOW)
    stale = evaluate_operational_abuse(customer(status="over_tracking", hot=99, first_seen=NOW - timedelta(hours=2), observed_at=NOW - timedelta(minutes=6)), now=NOW)
    assert all(not item.requires_controlled_hard for item in (farms, workers, missing, stale))
    assert missing.result == "evaluation_failed"
    assert stale.result == "stale_evidence"


def test_runner_scans_every_eligible_customer_and_records_missing_evidence() -> None:
    one = customer(evidence=False)
    two = OperationalAbuseCustomer(**{**one.__dict__, "customer_id": 2, "customer_key": "btc-2", "evidence": OperationalAbuseEvidence(hot_sessions=1, unique_source_ips=1, unique_workers=1, observed_at=NOW, collected_at=NOW)})
    repo = InMemoryAbuseOperationalRepo([one, two])
    report = run_abuse_cycle(repo, execute=True, now=NOW)
    assert report["scanned_customer_count"] == 2
    assert report["status"] == "BLOCKED"
    assert repo.events[0]["event_type"] == "abuse.evaluation_failed"


def test_database_failure_fails_closed_and_does_not_hard() -> None:
    report = run_abuse_cycle(InMemoryAbuseOperationalRepo(fail_reads=True), execute=True, now=NOW)
    assert report["status"] == "BLOCKED"
    assert report["hard_applied_count"] == 0
    assert report["blockers"] == ["database_read_failed"]


def hard_package(**firewall: object) -> dict[str, object]:
    return {"operation": "hard", "operator": "operator-1", "reason": "reviewed miner abuse", "evidence_reference": "evidence-1", "restore_point_reference": "restore-1", "policy_backup_reference": "backup-1", "firewall": {"controlled_path": True, **firewall}}


def test_firewall_plan_apply_or_verify_failure_never_marks_hard_applied_at() -> None:
    c = customer(status="over_tracking", hot=11, first_seen=NOW - timedelta(hours=1))
    evaluation = evaluate_operational_abuse(c, now=NOW)
    repo = InMemoryAbuseOperationalRepo([c])
    result = apply_controlled_hard(repo, evaluation, hard_package(apply_succeeded=False, verify_succeeded=False), now=NOW)
    assert result["status"] == "BLOCKED" and result["hard_applied_at"] is None
    assert repo.customers[0].state.status == "over_tracking"
    assert repo.customers[0].state.hard_applied_at is None


def test_verified_controlled_firewall_path_is_only_way_to_mark_hard_applied_at() -> None:
    c = customer(status="over_tracking", hot=11, first_seen=NOW - timedelta(hours=1))
    repo = InMemoryAbuseOperationalRepo([c])
    result = apply_controlled_hard(repo, evaluate_operational_abuse(c, now=NOW), hard_package(apply_succeeded=True, verify_succeeded=True, conntrack_flush_succeeded=True), now=NOW)
    assert result["status"] == "OK"
    assert repo.customers[0].state.status == "hard"
    assert repo.customers[0].state.hard_applied_at == NOW
    assert repo.audits[0]["action"] == "abuse.hard_applied"


def test_cli_surface_is_thin_and_fail_closed_without_controlled_package(tmp_path: Path) -> None:
    runner = CliRunner()
    assert runner.invoke(app, ["abuse", "doctor"]).exit_code == 0
    status = runner.invoke(app, ["abuse", "status"])
    assert status.exit_code == 0 and "database_read_failed" in status.stdout
    events = runner.invoke(app, ["abuse", "events", "--limit", "50"])
    assert events.exit_code == 0 and "database_read_failed" in events.stdout
    dry = runner.invoke(app, ["abuse", "run", "--dry-run"])
    assert dry.exit_code == 0 and "database_read_failed" in dry.stdout
    missing = runner.invoke(app, ["abuse", "run", "--controlled-execute"])
    assert missing.exit_code == 1 and "controlled_package_required" in missing.stdout


def test_cli_controlled_run_evaluates_package_without_runtime_mutation(tmp_path: Path, monkeypatch) -> None:
    cli_now = datetime.now(UTC)
    payload = {"operator": "operator-1", "reason": "reviewed", "customers": [{"customer_id": 1, "lane_id": 1, "customer_key": "btc-1", "port": 20101, "policy": {"miners": 10, "farms": 2, "expires_at": (cli_now + timedelta(days=1)).isoformat()}, "state": {"status": "normal"}, "evidence": {"hot_sessions": 11, "unique_source_ips": 1, "unique_workers": 1, "observed_at": cli_now.isoformat(), "collected_at": cli_now.isoformat()}}]}
    package = tmp_path / "abuse.json"
    package.write_text(json.dumps(payload), encoding="utf-8")
    cli_customer = OperationalAbuseCustomer(customer_id=1, lane_id=1, customer_key="btc-1", port=20101, active=True, lane_enabled=True, policy=OperationalAbusePolicy(miners=10, farms=2, expires_at=cli_now + timedelta(days=1)), state=OperationalAbuseState(), evidence=OperationalAbuseEvidence(hot_sessions=11, unique_source_ips=1, unique_workers=1, observed_at=cli_now, collected_at=cli_now))
    monkeypatch.setattr("mpf.interfaces.cli._load_abuse_postgres_repo", lambda config, evidence_by_customer_id=None: InMemoryAbuseOperationalRepo([cli_customer]))
    result = CliRunner().invoke(app, ["abuse", "run", "--controlled-execute", "--package", str(package)])
    assert result.exit_code == 0
    assert '"proposed_state": "over_tracking"' in result.stdout
    assert "writes only abuse_states, abuse_events, and job_runs" in result.stdout


def test_cli_hard_and_unhard_are_controlled_package_gated_and_adapter_blocked(tmp_path: Path) -> None:
    cli_now = datetime.now(UTC)
    common = {"operator": "operator-1", "reason": "reviewed", "evidence_reference": "evidence-1", "restore_point_reference": "restore-1", "policy_backup_reference": "backup-1", "firewall": {"controlled_path": True, "apply_succeeded": True, "verify_succeeded": True}}
    base_customer = {"customer_id": 1, "lane_id": 1, "customer_key": "btc-1", "port": 20101, "policy": {"miners": 10, "farms": 2, "expires_at": (cli_now + timedelta(days=1)).isoformat()}, "evidence": {"hot_sessions": 11, "unique_source_ips": 1, "unique_workers": 1, "observed_at": cli_now.isoformat(), "collected_at": cli_now.isoformat()}}
    hard = tmp_path / "hard.json"
    hard.write_text(json.dumps({**common, "operation": "hard", "customers": [{**base_customer, "state": {"status": "over_tracking", "first_seen_over": (cli_now - timedelta(hours=1)).isoformat()}}]}), encoding="utf-8")
    hard_result = CliRunner().invoke(app, ["abuse", "hard", "--controlled-package", str(hard)])
    assert hard_result.exit_code == 0
    assert "controlled_firewall_apply_integration_unavailable" in hard_result.stdout
    assert '"hard_applied_at": null' in hard_result.stdout

    unhard = tmp_path / "unhard.json"
    unhard.write_text(json.dumps({**common, "operation": "unhard", "customers": [{**base_customer, "state": {"status": "hard", "hard_applied_at": cli_now.isoformat()}}]}), encoding="utf-8")
    unhard_result = CliRunner().invoke(app, ["abuse", "unhard", "--controlled-package", str(unhard)])
    assert unhard_result.exit_code == 0
    assert "controlled_firewall_apply_integration_unavailable" in unhard_result.stdout
