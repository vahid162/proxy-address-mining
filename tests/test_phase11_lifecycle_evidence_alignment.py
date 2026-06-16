from __future__ import annotations

import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services import phase11_production_customer_lifecycle_execution_service as svc
from mpf.services.phase11_operational_completion_gap_inventory_service import build_phase11_operational_completion_gap_inventory_report
from mpf.services.phase11_production_customer_lifecycle_execution_readiness_service import build_phase11_production_customer_lifecycle_execution_readiness_report

RUNNER = CliRunner()


def _evidence(tmp_path: Path) -> Path:
    backup = tmp_path / "backup.json"
    backup.write_text('{"ok": true}\n', encoding="utf-8")
    ev = {
        "package_id": "pkg",
        "package_sha256": "pkgsha",
        "correlation_id": "corr",
        "customer_id": 5,
        "backup_id": 1,
        "restore_point_id": 2,
        "event_id": 3,
        "audit_id": 4,
        "backup_path": str(backup),
        "backup_sha256": hashlib.sha256(backup.read_bytes()).hexdigest(),
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        "phase12_start_allowed": False,
    }
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(ev), encoding="utf-8")
    return path


def test_lifecycle_verify_uses_project_read_only_db_helper(monkeypatch, tmp_path):
    evidence = _evidence(tmp_path)
    calls = []

    def fake_query(config, sql, params=()):
        calls.append((sql, params))
        class R:
            ok = True
            message = "OK"
            rows = []
        r = R()
        if "from customers" in sql:
            r.rows = [{"id": 5, "customer_key": "limited-btc-001", "lane": "btc", "port": 20101, "status": "active"}]
        elif "from backups" in sql:
            r.rows = [{"id": 1, "metadata_json": {"package_id": "pkg", "correlation_id": "corr"}}]
        elif "from restore_points" in sql:
            r.rows = [{"backup_id": 1, "subject_id": 5, "metadata_json": {"package_id": "pkg", "correlation_id": "corr"}}]
        elif "from events" in sql:
            r.rows = [{"event_type": "phase11.production_customer_lifecycle_execution", "data_json": {"package_id": "pkg", "correlation_id": "corr"}, "correlation_id": "corr"}]
        elif "from audit_log" in sql:
            r.rows = [{"action": "phase11.production_customer_lifecycle_execution", "after_json": {"package_id": "pkg", "correlation_id": "corr"}, "correlation_id": "corr"}]
        return r

    cfg = tmp_path / "mpf.yaml"
    cfg.write_text(Path("configs/mpf.example.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(svc, "query_database_params", fake_query)
    out = svc.verify(evidence, cfg)
    assert out["final_decision"] == svc.READY
    assert out["blockers"] == []
    assert calls
    assert out["mutation_performed"] is False
    assert out["db_mutation_performed"] is False
    assert out["phase12_start_allowed"] is False


def test_readiness_and_gap_keep_only_lifecycle_item_advanced():
    ready = {"final_decision": svc.READY}
    report = build_phase11_production_customer_lifecycle_execution_readiness_report(lifecycle_execution_evidence=ready)
    statuses = {c["name"]: c["status"] for c in report["checks"]}
    assert report["production_customer_lifecycle_execution"] == "controlled_execution_evidence_ready"
    assert statuses["audit_event_path_availability"] == "ready"
    assert statuses["backup_restore_point_requirement"] == "ready"
    assert "audit_event_path_availability" not in report["blockers"]
    assert "backup_restore_point_requirement" not in report["blockers"]
    for key in ("production_onboarding_flow", "production_abuse_runner", "backup_restore_drill", "full_cli_production_operations"):
        assert report[key] == "missing_or_partial"
    assert report["next_required_step"] == "production_firewall_apply_verify_rollback"

    gap = build_phase11_operational_completion_gap_inventory_report(readiness_report=None, lifecycle_execution_evidence_json=None)
    for key in ("production_firewall_apply_verify_rollback", "production_usage_report_check_evidence", "production_abuse_runner", "backup_restore_drill", "full_cli_production_operations"):
        assert gap[key] == "missing_or_partial"
    assert gap["phase12_start_allowed"] is False
    assert gap["worker_enforcement_allowed"] == "no"


def test_abuse_status_output_option(monkeypatch):
    import mpf.interfaces.cli as cli

    monkeypatch.setattr(cli, "_load_abuse_postgres_repo", lambda config: object())
    monkeypatch.setattr(cli.abuse_operational_service, "status_report", lambda repo: {"status": "OK", "states": [], "blockers": []})
    result = RUNNER.invoke(app, ["abuse", "status", "--output", "json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["status"] == "OK"
    default = RUNNER.invoke(app, ["abuse", "status"])
    assert default.exit_code == 0, default.output
    assert json.loads(default.output)["status"] == "OK"
    human = RUNNER.invoke(app, ["abuse", "status", "--output", "human"])
    assert human.exit_code == 0, human.output
    assert "status: OK" in human.output


def test_operational_surfaces_collector_lifecycle_evidence_passthrough_contract():
    text = Path("scripts/phase11_collect_operational_surfaces_evidence.sh").read_text(encoding="utf-8")
    assert "MPF_LIFECYCLE_EXECUTION_EVIDENCE_JSON" in text
    assert "production-customer-lifecycle-execution-evidence.json" in text
    assert "production-customer-lifecycle-execution-evidence.sha256" in text
    assert "--lifecycle-execution-evidence-json" in text
    assert "lifecycle_execution_evidence" in text
    assert "iptables-restore" not in text
    assert "conntrack" not in text
