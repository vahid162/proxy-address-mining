import json
import hashlib
from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services.phase11_backup_restore_drill_readiness_service import (
    build_phase11_backup_restore_drill_readiness_report,
)
from mpf.services.phase11_operational_completion_gap_inventory_service import (
    build_phase11_operational_completion_gap_inventory_report,
)

RUNNER = CliRunner()


def _write_bundle(root: Path) -> None:
    root.mkdir(exist_ok=True)
    (root / "phase-status.txt").write_text("phase12_start_allowed: no\nworker_enforcement_allowed: no\nui_allowed: no\ntelegram_allowed: no\n", encoding="utf-8")
    (root / "db-status.txt").write_text("ok\n", encoding="utf-8")
    lifecycle = {"restore_point_id": "rp-1", "backup_artifact": "backup.sql"}
    (root / "production-customer-lifecycle-execution-evidence.json").write_text(json.dumps(lifecycle), encoding="utf-8")
    safe = {
        "blockers": [],
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
    }
    firewall = {**safe, "production_firewall_apply_verify_rollback": "production_firewall_apply_verify_rollback_ready", "final_decision": "PRODUCTION_FIREWALL_APPLY_VERIFY_ROLLBACK_EVIDENCE_READY"}
    controls = {**safe, "production_controls_pause_block_expire": "production_controls_pause_block_expire_ready", "final_decision": "PRODUCTION_CONTROLS_PAUSE_BLOCK_EXPIRE_READY"}
    (root / "production-firewall-apply-verify-rollback-readiness.json").write_text(json.dumps(firewall), encoding="utf-8")
    (root / "production-controls-pause-block-expire-readiness.json").write_text(json.dumps(controls), encoding="utf-8")
    manifest = {
        "files": [],
        "mutation_flags": "mutation-flags.json",
        "source_evidence_mutation_flags": "source-evidence-mutation-flags.json",
        "backup_roots": ["/var/backups/mpf"],
        "lifecycle_execution_evidence": {"path": "production-customer-lifecycle-execution-evidence.json"},
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "mutation-flags.json").write_text("{}", encoding="utf-8")
    (root / "source-evidence-mutation-flags.json").write_text(json.dumps({"classification": "historical_source_evidence_not_current_collector_run"}), encoding="utf-8")
    lines = []
    for p in sorted(root.iterdir()):
        if p.name == "SHA256SUMS.txt" or not p.is_file():
            continue
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")
    (root / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_readiness_missing_evidence_dir_fails_closed(tmp_path):
    report = build_phase11_backup_restore_drill_readiness_report(tmp_path / "missing")
    assert report["backup_restore_drill"] == "missing_or_partial"
    assert report["final_decision"] == "BLOCKED_BACKUP_RESTORE_DRILL"
    assert report["mutation_performed"] is False


def test_readiness_missing_required_files_fails_closed(tmp_path):
    tmp_path.mkdir(exist_ok=True)
    report = build_phase11_backup_restore_drill_readiness_report(tmp_path)
    assert report["backup_restore_drill"] == "missing_or_partial"
    assert "required_evidence_missing:manifest.json" in report["blockers"]


def test_readiness_ready_for_minimal_isolated_bundle(tmp_path):
    _write_bundle(tmp_path)
    report = build_phase11_backup_restore_drill_readiness_report(tmp_path)
    assert report["backup_restore_drill"] == "backup_restore_drill_ready"
    assert report["backup_restore_drill_ready"] is True
    assert report["final_decision"] == "BACKUP_RESTORE_DRILL_READY"
    for key in ("mutation_performed", "db_mutation_performed", "firewall_apply_performed", "conntrack_flush_performed", "docker_restart_performed", "systemd_restart_performed", "phase12_start_allowed"):
        assert report[key] is False


def test_cli_returns_strict_json_exit_zero_for_fail_closed(tmp_path):
    result = RUNNER.invoke(app, ["production", "backup-restore-drill-readiness", "--evidence-dir", str(tmp_path / "missing"), "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["backup_restore_drill"] == "missing_or_partial"


def test_gap_inventory_consumes_explicit_backup_restore_readiness(tmp_path):
    _write_bundle(tmp_path)
    report = build_phase11_backup_restore_drill_readiness_report(tmp_path)
    (tmp_path / "backup-restore-drill-readiness.json").write_text(json.dumps(report), encoding="utf-8")
    inventory = build_phase11_operational_completion_gap_inventory_report(evidence_dir=tmp_path)
    assert inventory["backup_restore_drill"] == "backup_restore_drill_ready"
    assert inventory["full_cli_production_operations"] == "missing_or_partial"


def test_collector_invokes_backup_restore_readiness_without_mutation_words():
    text = Path("scripts/phase11_collect_operational_surfaces_evidence.sh").read_text(encoding="utf-8")
    assert "backup-restore-drill-readiness.json" in text
    assert "production backup-restore-drill-readiness" in text
    assert "backup_restore_drill_readiness" in text
