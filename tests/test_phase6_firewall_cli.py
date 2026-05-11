from __future__ import annotations

import subprocess

from typer.testing import CliRunner

from mpf.domain.firewall import FirewallPlanMessage, FirewallPlanResult
from mpf.interfaces.cli import app
from mpf.services import firewall_planner_service
from tests.test_smoke import example_config_path

RUNNER = CliRunner()


def _db_plan() -> FirewallPlanResult:
    p = FirewallPlanResult(planner_customer_source="db_readonly", db_customer_input_loaded=True)
    p.finalize()
    return p


def _config_plan() -> FirewallPlanResult:
    p = FirewallPlanResult(planner_customer_source="config_only", db_customer_input_loaded=False)
    p.warnings.append(FirewallPlanMessage(code="planner_customer_source", message="explicit config-only source requested", severity="warning"))
    p.finalize()
    return p


def test_firewall_plan_and_diff_default_to_db_readonly(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    for cmd in (["firewall", "plan"], ["firewall", "diff"]):
        res = RUNNER.invoke(app, [*cmd, "--config", str(example_config_path())])
        assert res.exit_code == 0
        assert "planner_customer_source: db_readonly" in res.output
        assert "db_customer_input_loaded: true" in res.output
        assert "firewall_change: planned_only" in res.output


def test_firewall_plan_json_reports_db_source(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "plan", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0
    assert '"planner_customer_source": "db_readonly"' in res.output
    assert '"db_customer_input_loaded": true' in res.output


def test_firewall_plan_config_only_is_explicit(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_config", lambda cfg: _config_plan())
    res = RUNNER.invoke(app, ["firewall", "plan", "--config", str(example_config_path()), "--source", "config-only"])
    assert res.exit_code == 0
    assert "planner_customer_source: config_only" in res.output
    assert "db_customer_input_loaded: false" in res.output
    assert "WARNING" in res.output


def test_firewall_plan_db_failure_exits_nonzero(monkeypatch) -> None:
    def raise_fail(cfg):
        raise RuntimeError("failed to load lanes: db down")

    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", raise_fail)
    res = RUNNER.invoke(app, ["firewall", "plan", "--config", str(example_config_path())])
    assert res.exit_code == 1
    assert "ERROR: failed to load lanes: db down" in res.output


def test_firewall_diff_json_with_offline_live_snapshot_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db_with_live_snapshot", lambda cfg, snapshot: _db_plan())
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")
    res = RUNNER.invoke(app, ["firewall", "diff", "--config", str(example_config_path()), "--output", "json", "--live-snapshot-file", str(snapshot)])
    assert res.exit_code == 0
    assert '"planner_customer_source": "db_readonly"' in res.output


def test_firewall_diff_live_snapshot_missing_file_exits_nonzero(tmp_path) -> None:
    missing = tmp_path / "missing.save"
    res = RUNNER.invoke(app, ["firewall", "diff", "--config", str(example_config_path()), "--live-snapshot-file", str(missing)])
    assert res.exit_code == 1
    assert f"ERROR: unable to read live snapshot file: {missing}: file does not exist" in res.output


def test_firewall_diff_live_snapshot_not_a_file_exits_nonzero(tmp_path) -> None:
    not_file = tmp_path / "snapshots"
    not_file.mkdir()
    res = RUNNER.invoke(app, ["firewall", "diff", "--config", str(example_config_path()), "--live-snapshot-file", str(not_file)])
    assert res.exit_code == 1
    assert f"ERROR: unable to read live snapshot file: {not_file}: not a file" in res.output


def test_firewall_diff_live_snapshot_file_does_not_call_subprocess(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db_with_live_snapshot", lambda cfg, snapshot: _db_plan())

    def _fail(*args, **kwargs):
        raise AssertionError("subprocess call is forbidden in offline snapshot diff")

    monkeypatch.setattr(subprocess, "run", _fail)
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")
    res = RUNNER.invoke(app, ["firewall", "diff", "--config", str(example_config_path()), "--live-snapshot-file", str(snapshot)])
    assert res.exit_code == 0




def test_firewall_doctor_defaults_to_db_readonly(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "doctor", "--config", str(example_config_path())])
    assert res.exit_code == 0
    assert "planner_customer_source: db_readonly" in res.output


def test_firewall_doctor_json_reports_db_source(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "doctor", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0
    assert '"planner_customer_source": "db_readonly"' in res.output
    assert '"db_customer_input_loaded": true' in res.output


def test_firewall_doctor_config_only_is_warn(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_config", lambda cfg: _config_plan())
    res = RUNNER.invoke(app, ["firewall", "doctor", "--config", str(example_config_path()), "--source", "config-only"])
    assert res.exit_code == 0
    assert "final_verdict: WARN" in res.output


def test_firewall_doctor_db_failure_exits_nonzero(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: (_ for _ in ()).throw(RuntimeError("failed to load lanes: db down")))
    res = RUNNER.invoke(app, ["firewall", "doctor", "--config", str(example_config_path())])
    assert res.exit_code == 1
    assert "ERROR: failed to load lanes: db down" in res.output


def test_firewall_doctor_live_snapshot_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db_with_live_snapshot", lambda cfg, snapshot: _db_plan())
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")
    res = RUNNER.invoke(app, ["firewall", "doctor", "--config", str(example_config_path()), "--live-snapshot-file", str(snapshot)])
    assert res.exit_code == 0
    assert "snapshot_input: file" in res.output


def test_firewall_doctor_invalid_snapshot_file_exits_nonzero(tmp_path) -> None:
    missing = tmp_path / "missing.save"
    res = RUNNER.invoke(app, ["firewall", "doctor", "--config", str(example_config_path()), "--live-snapshot-file", str(missing)])
    assert res.exit_code == 1
    assert f"ERROR: unable to read live snapshot file: {missing}: file does not exist" in res.output


def test_firewall_doctor_snapshot_file_does_not_call_subprocess(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db_with_live_snapshot", lambda cfg, snapshot: _db_plan())

    def _fail(*args, **kwargs):
        raise AssertionError("subprocess call is forbidden in offline snapshot doctor")

    monkeypatch.setattr(subprocess, "run", _fail)
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")
    res = RUNNER.invoke(app, ["firewall", "doctor", "--config", str(example_config_path()), "--live-snapshot-file", str(snapshot)])
    assert res.exit_code == 0

def test_no_firewall_apply_or_rollback_commands() -> None:
    apply_res = RUNNER.invoke(app, ["firewall", "apply"])
    rollback_res = RUNNER.invoke(app, ["firewall", "rollback"])
    assert apply_res.exit_code != 0
    assert rollback_res.exit_code != 0
    verify_res = RUNNER.invoke(app, ["firewall", "verify"])
    assert verify_res.exit_code != 0

def test_firewall_render_restore_human(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "render-restore", "--config", str(example_config_path())])
    assert res.exit_code == 0
    assert "MPF firewall restore artifact (offline)" in res.output


def test_firewall_render_restore_json_flags(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "render-restore", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0
    assert '"artifact_only": true' in res.output
    assert '"live_apply_allowed": false' in res.output


def test_firewall_render_restore_payload_only(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "render-restore", "--config", str(example_config_path()), "--output", "payload"])
    assert res.exit_code == 0
    assert res.output.startswith("*filter\n")
    assert "MPF firewall restore artifact" not in res.output


def test_firewall_render_restore_config_only_warn(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_config", lambda cfg: _config_plan())
    res = RUNNER.invoke(app, ["firewall", "render-restore", "--config", str(example_config_path()), "--source", "config-only"])
    assert res.exit_code == 0
    assert "WARNING [planner_customer_source]" in res.output


def test_firewall_render_restore_db_failure_exits_nonzero(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: (_ for _ in ()).throw(RuntimeError("failed to load lanes: db down")))
    res = RUNNER.invoke(app, ["firewall", "render-restore", "--config", str(example_config_path())])
    assert res.exit_code == 1
    assert "ERROR: failed to load lanes: db down" in res.output


def test_firewall_render_restore_does_not_call_subprocess(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())

    def _fail(*args, **kwargs):
        raise AssertionError("subprocess call is forbidden in render-restore")

    monkeypatch.setattr(subprocess, "run", _fail)
    res = RUNNER.invoke(app, ["firewall", "render-restore", "--config", str(example_config_path())])
    assert res.exit_code == 0


def test_firewall_render_restore_payload_validation_error_no_payload(monkeypatch) -> None:
    bad = _db_plan()
    bad.errors.append(FirewallPlanMessage(code="forced", message="forced", severity="error"))
    bad.finalize()
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: bad)
    res = RUNNER.invoke(app, ["firewall", "render-restore", "--config", str(example_config_path()), "--output", "payload"])
    assert res.exit_code == 1
    assert "*filter" not in res.output
    assert "*nat" not in res.output


def test_firewall_render_restore_no_save_restore_subprocess(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())

    def _fail(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", "")
        text = " ".join(cmd) if isinstance(cmd, (list, tuple)) else str(cmd)
        if "iptables-save" in text or "iptables-restore" in text:
            raise AssertionError("iptables-save/iptables-restore subprocess is forbidden in render-restore")
        raise AssertionError("subprocess call is forbidden in render-restore")

    monkeypatch.setattr(subprocess, "run", _fail)
    res = RUNNER.invoke(app, ["firewall", "render-restore", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0


def test_firewall_apply_contract_human(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "apply-contract", "--config", str(example_config_path())])
    assert res.exit_code == 0
    assert "MPF firewall apply contract (offline)" in res.output
    assert "artifact_only: true" in res.output
    assert "live_apply_allowed: false" in res.output
    assert "applyable: false" in res.output


def test_firewall_apply_contract_json(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "apply-contract", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0
    assert '"artifact_only": true' in res.output
    assert '"live_apply_allowed": false' in res.output


def test_firewall_apply_contract_config_only_warning(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_config", lambda cfg: _config_plan())
    res = RUNNER.invoke(app, ["firewall", "apply-contract", "--config", str(example_config_path()), "--source", "config-only"])
    assert res.exit_code == 0
    assert "warnings:" in res.output


def test_firewall_apply_contract_db_failure_exits_nonzero(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: (_ for _ in ()).throw(RuntimeError("failed to load lanes: db down")))
    res = RUNNER.invoke(app, ["firewall", "apply-contract", "--config", str(example_config_path())])
    assert res.exit_code == 1
    assert "ERROR: failed to load lanes: db down" in res.output


def test_firewall_apply_contract_no_yes_and_no_subprocess(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("subprocess forbidden")))
    bad = RUNNER.invoke(app, ["firewall", "apply-contract", "--yes"])
    assert bad.exit_code != 0
    res = RUNNER.invoke(app, ["firewall", "apply-contract", "--config", str(example_config_path())])
    assert res.exit_code == 0
