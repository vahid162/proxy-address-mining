import json
from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services.phase11_firewall_completion_evidence_bundle_service import (
    verify_firewall_completion_evidence_bundle,
    write_manifest_and_sha256s,
)
from mpf.services.phase11_operational_completion_gap_inventory_service import build_phase11_operational_completion_gap_inventory_report


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _bundle(tmp_path: Path) -> Path:
    b = tmp_path / "bundle"
    b.mkdir(parents=True)
    _write_json(b / "controlled-backend-target.json", {"status": "ok", "repository_version": "0.1.283", "resolved_ipv4": "172.18.0.2", "target_port": 60010, "backend_public_exposure": False, "blockers": []})
    (b / "iptables-save.txt").write_text("*nat\nCOMMIT\n", encoding="utf-8")
    (b / "ip6tables-save.txt").write_text("*filter\nCOMMIT\n", encoding="utf-8")
    _write_json(b / "current-controlled-artifact-gate-with-target.json", {"repository_version": "0.1.283", "current_phase_gate_ok": True, "current_working_phase": "Phase 11 operational completion — Full CLI Production Operations", "production_traffic": "controlled_cli_limited", "customer_onboarding_allowed": "controlled_cli_limited", "phase12_start_allowed": False, "backend_public_exposure": False, "unknown_mpf_artifacts": [], "duplicate_nat_redirect_count": 0, "forbidden_public_runtime_exposure": False, "mutation_performed": False})
    _write_json(b / "controlled-artifact-reapply-plan-target-aware.json", {"repository_version": "0.1.283", "mutation_performed": False})
    _write_json(b / "controlled-artifact-reapply-package-target-aware.json", {"repository_version": "0.1.283", "mutation_performed": False})
    _write_json(b / "controlled-artifact-reapply-readiness-target-aware.json", {"repository_version": "0.1.283", "mutation_performed": False})
    _write_json(b / "production-firewall-apply-verify-rollback-readiness.json", {"repository_version": "0.1.283", "production_firewall_apply_verify_rollback": "missing_or_partial", "phase12_start_allowed": False, "mutation_performed": False})
    write_manifest_and_sha256s(b)
    return b


def test_valid_bundle_verifies_and_stays_preflight_only(tmp_path):
    report = verify_firewall_completion_evidence_bundle(_bundle(tmp_path))
    assert report["final_decision"] == "PHASE11_FIREWALL_COMPLETION_EVIDENCE_BUNDLE_PREFLIGHT_READY"
    assert report["bundle_preflight_ready"] is True
    assert report["production_firewall_apply_verify_rollback"] == "missing_or_partial"
    assert report["phase12_start_allowed"] is False


def test_manifest_and_sha_mismatch_fail_closed(tmp_path):
    b = _bundle(tmp_path)
    (b / "iptables-save.txt").write_text("tampered", encoding="utf-8")
    report = verify_firewall_completion_evidence_bundle(b)
    assert any(x.startswith("sha256_mismatch:iptables-save.txt") for x in report["blockers"])
    assert report["bundle_preflight_ready"] is False


def test_missing_bundle_and_required_files_fail_closed(tmp_path):
    assert "bundle_dir_missing" in verify_firewall_completion_evidence_bundle(tmp_path / "missing")["blockers"]
    b = _bundle(tmp_path)
    (b / "iptables-save.txt").unlink()
    report = verify_firewall_completion_evidence_bundle(b)
    assert "required_file_missing:iptables-save.txt" in report["blockers"]


def test_ip6tables_missing_fails_closed(tmp_path):
    b = _bundle(tmp_path)
    (b / "ip6tables-save.txt").unlink()
    assert "required_file_missing:ip6tables-save.txt" in verify_firewall_completion_evidence_bundle(b)["blockers"]


def test_safety_blockers_fail_closed(tmp_path):
    cases = [
        ("controlled-backend-target.json", {"resolved_ipv4": None}, "backend_target_missing"),
        ("controlled-backend-target.json", {"backend_public_exposure": True}, "backend_public_exposure_true"),
        ("current-controlled-artifact-gate-with-target.json", {"unknown_mpf_artifacts": ["x"]}, "unknown_mpf_artifacts_non_empty"),
        ("current-controlled-artifact-gate-with-target.json", {"duplicate_nat_redirect_count": 1}, "duplicate_nat_redirect_count_non_zero"),
        ("current-controlled-artifact-gate-with-target.json", {"forbidden_public_runtime_exposure": True}, "forbidden_public_runtime_exposure_true"),
        ("current-controlled-artifact-gate-with-target.json", {"phase12_start_allowed": True}, "phase12_start_allowed_true"),
        ("current-controlled-artifact-gate-with-target.json", {"mutation_performed": True}, "mutation_flag_true:current-controlled-artifact-gate-with-target.json:mutation_performed"),
    ]
    for filename, patch, blocker in cases:
        b = _bundle(tmp_path / blocker.replace(":", "_"))
        data = json.loads((b / filename).read_text(encoding="utf-8"))
        data.update(patch)
        _write_json(b / filename, data)
        write_manifest_and_sha256s(b)
        assert blocker in verify_firewall_completion_evidence_bundle(b)["blockers"]


def test_malformed_json_fails_closed(tmp_path):
    b = _bundle(tmp_path)
    (b / "controlled-backend-target.json").write_text("{not json", encoding="utf-8")
    write_manifest_and_sha256s(b)
    report = verify_firewall_completion_evidence_bundle(b)
    assert "malformed_json:controlled-backend-target.json" in report["blockers"]


def test_gap_inventory_remains_missing_with_clean_preflight_bundle(tmp_path):
    gap = build_phase11_operational_completion_gap_inventory_report(
        None,
        persistence_plan_report={},
        readiness_report={},
        firewall_completion_evidence_dir=_bundle(tmp_path),
    )
    assert gap["production_firewall_apply_verify_rollback"] == "missing_or_partial"
    assert gap["full_cli_production_operations"] == "missing_or_partial"
    assert gap["phase12_start_allowed"] is False


def test_cli_verify_registered(tmp_path):
    result = CliRunner().invoke(app, ["production", "firewall-completion-evidence-bundle-verify", "--evidence-dir", str(_bundle(tmp_path)), "--output", "json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["bundle_preflight_ready"] is True
