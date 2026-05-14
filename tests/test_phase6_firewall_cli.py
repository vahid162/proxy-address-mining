from __future__ import annotations

import subprocess

from typer.testing import CliRunner

from mpf.domain.firewall import FirewallPlanMessage, FirewallPlanResult
from mpf.interfaces import cli
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


def test_firewall_package_human(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "package", "--config", str(example_config_path())])
    assert res.exit_code == 0
    assert "MPF firewall apply package (offline)" in res.output
    assert "artifact_only: true" in res.output


def test_firewall_package_json_flags(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "package", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0
    assert '"artifact_only": true' in res.output
    assert '"inspection_only": true' in res.output
    assert '"live_apply_allowed": false' in res.output
    assert '"applyable": false' in res.output


def test_firewall_package_config_only_warn(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_config", lambda cfg: _config_plan())
    res = RUNNER.invoke(app, ["firewall", "package", "--config", str(example_config_path()), "--source", "config-only"])
    assert res.exit_code == 0
    assert "planner_customer_source: config_only" in res.output
    assert "WARNING" in res.output


def test_firewall_package_db_failure_exits_nonzero(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: (_ for _ in ()).throw(RuntimeError("failed to load lanes: db down")))
    res = RUNNER.invoke(app, ["firewall", "package", "--config", str(example_config_path())])
    assert res.exit_code == 1
    assert "ERROR: failed to load lanes: db down" in res.output


def test_firewall_package_no_yes_option() -> None:
    res = RUNNER.invoke(app, ["firewall", "package", "--yes"])
    assert res.exit_code != 0


def test_firewall_package_does_not_call_subprocess(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())

    def _fail(*args, **kwargs):
        raise AssertionError("subprocess call is forbidden in firewall package")

    monkeypatch.setattr(subprocess, "run", _fail)
    res = RUNNER.invoke(app, ["firewall", "package", "--config", str(example_config_path())])
    assert res.exit_code == 0

def test_firewall_render_rollback_human(tmp_path) -> None:
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")
    res = RUNNER.invoke(app, ["firewall", "render-rollback", "--config", str(example_config_path()), "--snapshot-file", str(snapshot)])
    assert res.exit_code == 0
    assert "MPF firewall rollback artifact (offline)" in res.output


def test_firewall_render_rollback_json_flags(tmp_path) -> None:
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")
    res = RUNNER.invoke(app, ["firewall", "render-rollback", "--config", str(example_config_path()), "--snapshot-file", str(snapshot), "--output", "json"])
    assert res.exit_code == 0
    assert '"artifact_only": true' in res.output
    assert '"inspection_only": true' in res.output
    assert '"applyable": false' in res.output


def test_firewall_render_rollback_payload_only(tmp_path) -> None:
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")
    res = RUNNER.invoke(app, ["firewall", "render-rollback", "--config", str(example_config_path()), "--snapshot-file", str(snapshot), "--output", "payload"])
    assert res.exit_code == 0
    assert res.output.startswith("# MPF rollback artifact only")


def test_firewall_render_rollback_without_config_human(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(cli, "_load", lambda config: cli.load_config(example_config_path()))
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")
    res = RUNNER.invoke(app, ["firewall", "render-rollback", "--snapshot-file", str(snapshot)])
    assert res.exit_code == 0
    assert "MPF firewall rollback artifact (offline)" in res.output


def test_firewall_render_rollback_without_config_json(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(cli, "_load", lambda config: cli.load_config(example_config_path()))
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")
    res = RUNNER.invoke(app, ["firewall", "render-rollback", "--snapshot-file", str(snapshot), "--output", "json"])
    assert res.exit_code == 0
    assert '"artifact_only": true' in res.output


def test_firewall_render_rollback_without_config_payload(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(cli, "_load", lambda config: cli.load_config(example_config_path()))
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")
    res = RUNNER.invoke(app, ["firewall", "render-rollback", "--snapshot-file", str(snapshot), "--output", "payload"])
    assert res.exit_code == 0
    assert res.output.startswith("# MPF rollback artifact only")


def test_firewall_render_rollback_missing_snapshot_nonzero() -> None:
    res = RUNNER.invoke(app, ["firewall", "render-rollback", "--config", str(example_config_path())])
    assert res.exit_code != 0


def test_firewall_render_rollback_invalid_snapshot_path_nonzero(tmp_path) -> None:
    missing = tmp_path / "missing.save"
    res = RUNNER.invoke(app, ["firewall", "render-rollback", "--config", str(example_config_path()), "--snapshot-file", str(missing)])
    assert res.exit_code == 1
    assert "ERROR: unable to read rollback snapshot file" in res.output


def test_firewall_render_rollback_invalid_content_payload_mode_nonzero(tmp_path) -> None:
    bad = tmp_path / "bad.save"
    bad.write_text("", encoding="utf-8")
    res = RUNNER.invoke(app, ["firewall", "render-rollback", "--config", str(example_config_path()), "--snapshot-file", str(bad), "--output", "payload"])
    assert res.exit_code == 1
    assert "*filter" not in res.output


def test_firewall_render_rollback_no_yes_option() -> None:
    res = RUNNER.invoke(app, ["firewall", "render-rollback", "--yes"])
    assert res.exit_code != 0


def test_firewall_render_rollback_does_not_call_subprocess(monkeypatch, tmp_path) -> None:
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")

    def _fail(*args, **kwargs):
        raise AssertionError("subprocess call is forbidden in render-rollback")

    monkeypatch.setattr(subprocess, "run", _fail)
    res = RUNNER.invoke(app, ["firewall", "render-rollback", "--config", str(example_config_path()), "--snapshot-file", str(snapshot), "--output", "json"])
    assert res.exit_code == 0


def test_firewall_render_rollback_no_save_restore_subprocess(monkeypatch, tmp_path) -> None:
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")

    def _fail(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", "")
        text = " ".join(cmd) if isinstance(cmd, (list, tuple)) else str(cmd)
        if "iptables-save" in text or "iptables-restore" in text:
            raise AssertionError("iptables-save/iptables-restore subprocess is forbidden in render-rollback")
        raise AssertionError("subprocess call is forbidden in render-rollback")

    monkeypatch.setattr(subprocess, "run", _fail)
    res = RUNNER.invoke(app, ["firewall", "render-rollback", "--config", str(example_config_path()), "--snapshot-file", str(snapshot)])
    assert res.exit_code == 0

def test_firewall_preflight_human_defaults_db(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "preflight", "--config", str(example_config_path())])
    assert res.exit_code == 0
    assert "MPF firewall preflight (offline)" in res.output
    assert "final_verdict: BLOCKED" in res.output
    assert "planner_customer_source: db_readonly" in res.output


def test_firewall_preflight_json_flags(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "preflight", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0
    assert '"artifact_only": true' in res.output
    assert '"inspection_only": true' in res.output
    assert '"live_apply_allowed": false' in res.output
    assert '"applyable": false' in res.output
    assert '"final_verdict": "BLOCKED"' in res.output


def test_firewall_preflight_config_only_warning(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_config", lambda cfg: _config_plan())
    res = RUNNER.invoke(app, ["firewall", "preflight", "--config", str(example_config_path()), "--source", "config-only"])
    assert res.exit_code == 0
    assert "WARNING" in res.output


def test_firewall_preflight_rollback_snapshot_file_and_invalid_path(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    snapshot = tmp_path / "rollback.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")
    ok = RUNNER.invoke(app, ["firewall", "preflight", "--config", str(example_config_path()), "--rollback-snapshot-file", str(snapshot)])
    assert ok.exit_code == 0
    bad = RUNNER.invoke(app, ["firewall", "preflight", "--config", str(example_config_path()), "--rollback-snapshot-file", str(tmp_path / 'missing.save')])
    assert bad.exit_code == 1
    assert "ERROR: unable to read rollback snapshot file" in bad.output


def test_firewall_preflight_no_yes_and_no_subprocess(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("subprocess forbidden")))
    bad = RUNNER.invoke(app, ["firewall", "preflight", "--yes"])
    assert bad.exit_code != 0
    res = RUNNER.invoke(app, ["firewall", "preflight", "--config", str(example_config_path())])
    assert res.exit_code == 0


def test_firewall_preflight_defaults_to_db_no_config_fallback(monkeypatch) -> None:
    calls = {"db": 0, "config": 0}

    def _db(cfg):
        calls["db"] += 1
        return _db_plan()

    def _config(cfg):
        calls["config"] += 1
        return _config_plan()

    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", _db)
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_config", _config)
    res = RUNNER.invoke(app, ["firewall", "preflight", "--config", str(example_config_path())])
    assert res.exit_code == 0
    assert calls["db"] == 1
    assert calls["config"] == 0


def test_firewall_preflight_db_failure_exits_nonzero(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: (_ for _ in ()).throw(RuntimeError("failed to load lanes: db down")))
    res = RUNNER.invoke(app, ["firewall", "preflight", "--config", str(example_config_path())])
    assert res.exit_code == 1
    assert "ERROR: failed to load lanes: db down" in res.output

def test_firewall_evidence_human_default_db(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "evidence", "--config", str(example_config_path())])
    assert res.exit_code == 0
    assert "MPF firewall evidence bundle (offline)" in res.output
    assert "planner_customer_source: db_readonly" in res.output


def test_firewall_evidence_json_flags(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "evidence", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0
    assert '"artifact_only": true' in res.output
    assert '"inspection_only": true' in res.output
    assert '"live_apply_allowed": false' in res.output
    assert '"applyable": false' in res.output
    assert '"final_verdict": "BLOCKED"' in res.output


def test_firewall_evidence_config_only_warn(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_config", lambda cfg: _config_plan())
    res = RUNNER.invoke(app, ["firewall", "evidence", "--config", str(example_config_path()), "--source", "config-only"])
    assert res.exit_code == 0
    assert "WARNING" in res.output


def test_firewall_evidence_db_failure_exits_nonzero(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: (_ for _ in ()).throw(RuntimeError("failed to load lanes: db down")))
    res = RUNNER.invoke(app, ["firewall", "evidence", "--config", str(example_config_path())])
    assert res.exit_code == 1
    assert "ERROR: failed to load lanes: db down" in res.output


def test_firewall_evidence_rollback_snapshot_path_checks(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    missing = tmp_path / "missing.save"
    res = RUNNER.invoke(app, ["firewall", "evidence", "--config", str(example_config_path()), "--rollback-snapshot-file", str(missing)])
    assert res.exit_code == 1
    assert "ERROR: unable to read rollback snapshot file" in res.output


def test_firewall_evidence_snapshot_does_not_call_subprocess(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())

    def _fail(*args, **kwargs):
        raise AssertionError("subprocess call is forbidden in offline snapshot evidence")

    monkeypatch.setattr(subprocess, "run", _fail)
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")
    res = RUNNER.invoke(app, ["firewall", "evidence", "--config", str(example_config_path()), "--rollback-snapshot-file", str(snapshot)])
    assert res.exit_code == 0


def test_firewall_evidence_has_no_yes_option() -> None:
    res = RUNNER.invoke(app, ["firewall", "evidence", "--yes"])
    assert res.exit_code != 0


def test_firewall_evidence_invalid_output_exits_nonzero(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "evidence", "--config", str(example_config_path()), "--output", "payload"])
    assert res.exit_code != 0


def test_firewall_evidence_rollback_snapshot_not_a_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    not_file = tmp_path / "snapshots"
    not_file.mkdir()
    res = RUNNER.invoke(app, ["firewall", "evidence", "--config", str(example_config_path()), "--rollback-snapshot-file", str(not_file)])
    assert res.exit_code == 1
    assert "ERROR: unable to read rollback snapshot file" in res.output
    assert "not a file" in res.output


def test_firewall_gate_review_human_default_db(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "gate-review", "--config", str(example_config_path())])
    assert res.exit_code == 0
    assert "MPF firewall gate review (offline)" in res.output
    assert "final_decision: BLOCKED" in res.output
    assert "apply_gate_readiness: summary" in res.output
    assert "  final_decision: BLOCKED" in res.output
    assert "live_snapshot_scaffold: summary" in res.output
    assert "  authorization_status: NOT_AUTHORIZED" in res.output
    assert "restore_lock_record_execution_gate: summary" in res.output
    assert "  authorization_status: NOT_AUTHORIZED_FOR_EXECUTION" in res.output
    assert "  execution_allowed: false" in res.output
    assert "final_decision: BLOCKED" in res.output
    assert "applyable: false" in res.output
    assert "live_apply_allowed: false" in res.output


def test_firewall_gate_review_json_flags(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    res = RUNNER.invoke(app, ["firewall", "gate-review", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0
    assert '"inspection_only": true' in res.output
    assert '"artifact_only": true' in res.output
    assert '"live_apply_allowed": false' in res.output
    assert '"applyable": false' in res.output
    assert '"final_decision": "BLOCKED"' in res.output
    assert '"apply_gate_readiness_summary": {' in res.output
    assert '"live_snapshot_scaffold_summary": {' in res.output
    assert '"authorization_status": "NOT_AUTHORIZED"' in res.output
    assert '"final_decision": "BLOCKED"' in res.output


def test_firewall_gate_review_config_only_warning(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_config", lambda cfg: _config_plan())
    res = RUNNER.invoke(app, ["firewall", "gate-review", "--config", str(example_config_path()), "--source", "config-only"])
    assert res.exit_code == 0
    assert "WARNING" in res.output


def test_firewall_gate_review_db_failure_exits_nonzero(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: (_ for _ in ()).throw(RuntimeError("failed to load lanes: db down")))
    res = RUNNER.invoke(app, ["firewall", "gate-review", "--config", str(example_config_path())])
    assert res.exit_code == 1
    assert "ERROR: failed to load lanes: db down" in res.output


def test_firewall_gate_review_rollback_snapshot_file_only(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    snapshot = tmp_path / "iptables.save"
    snapshot.write_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n", encoding="utf-8")
    res = RUNNER.invoke(app, ["firewall", "gate-review", "--config", str(example_config_path()), "--rollback-snapshot-file", str(snapshot)])
    assert res.exit_code == 0


def test_firewall_gate_review_invalid_rollback_snapshot_exits_nonzero(tmp_path) -> None:
    missing = tmp_path / "missing.save"
    res = RUNNER.invoke(app, ["firewall", "gate-review", "--config", str(example_config_path()), "--rollback-snapshot-file", str(missing)])
    assert res.exit_code == 1
    assert f"ERROR: unable to read rollback snapshot file: {missing}: file does not exist" in res.output


def test_firewall_gate_review_does_not_call_subprocess(monkeypatch) -> None:
    monkeypatch.setattr(firewall_planner_service, "build_plan_from_db", lambda cfg: _db_plan())
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("subprocess forbidden")))
    res = RUNNER.invoke(app, ["firewall", "gate-review", "--config", str(example_config_path())])
    assert res.exit_code == 0


def test_firewall_gate_review_invalid_output_exits_nonzero() -> None:
    res = RUNNER.invoke(app, ["firewall", "gate-review", "--output", "payload"])
    assert res.exit_code != 0


def test_firewall_gate_review_no_yes_option() -> None:
    res = RUNNER.invoke(app, ["firewall", "gate-review", "--yes"])
    assert res.exit_code != 0


def test_firewall_gate_review_snapshot_directory_exits_nonzero(tmp_path) -> None:
    snapdir = tmp_path / "snaps"
    snapdir.mkdir()
    res = RUNNER.invoke(app, ["firewall", "gate-review", "--config", str(example_config_path()), "--rollback-snapshot-file", str(snapdir)])
    assert res.exit_code == 1
    assert "not a file" in res.output


def test_firewall_live_snapshot_readiness_human_output() -> None:
    res = RUNNER.invoke(app, ["firewall", "live-snapshot-readiness", "--config", str(example_config_path())])
    assert res.exit_code == 0
    assert "component: firewall_live_snapshot_read" in res.output
    assert "authorization_status: AUTHORIZED_READ_ONLY" in res.output


def test_firewall_live_snapshot_readiness_json_output() -> None:
    res = RUNNER.invoke(app, ["firewall", "live-snapshot-readiness", "--config", str(example_config_path()), "--output", "json"])
    assert res.exit_code == 0
    assert '"component": "firewall_live_snapshot_read"' in res.output
    assert '"live_firewall_read_executed": false' in res.output


def test_firewall_live_snapshot_readiness_invalid_output_nonzero() -> None:
    res = RUNNER.invoke(app, ["firewall", "live-snapshot-readiness", "--config", str(example_config_path()), "--output", "yaml"])
    assert res.exit_code != 0


def test_firewall_live_snapshot_readiness_does_not_require_root() -> None:
    res = RUNNER.invoke(app, ["firewall", "live-snapshot-readiness", "--config", str(example_config_path())])
    assert res.exit_code == 0


def test_firewall_live_snapshot_read_no_execute_does_not_run_subprocess(monkeypatch) -> None:
    import subprocess
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no subprocess")))
    res = RUNNER.invoke(app, ["firewall", "live-snapshot-read", "--config", str(example_config_path())])
    assert res.exit_code == 0
    assert "subprocess_executed: false" in res.output


def test_firewall_live_snapshot_read_execute_runs_iptables_save(monkeypatch) -> None:
    import subprocess
    calls = {}
    def _run(args, **kwargs):
        calls["args"] = args
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="*filter\n:INPUT ACCEPT [0:0]\nCOMMIT\n", stderr="")
    monkeypatch.setattr(subprocess, "run", _run)
    res = RUNNER.invoke(app, ["firewall", "live-snapshot-read", "--config", str(example_config_path()), "--execute", "--output", "json"])
    assert res.exit_code == 0
    assert calls["args"] == ["iptables-save"]
    assert '"final_decision": "READ_ONLY_SNAPSHOT_COLLECTED"' in res.output


def test_firewall_live_snapshot_read_execute_empty_stdout_fails_closed(monkeypatch) -> None:
    import subprocess
    monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr=""))
    res = RUNNER.invoke(app, ["firewall", "live-snapshot-read", "--config", str(example_config_path()), "--execute"])
    assert res.exit_code == 1
    assert "FAILED_READ_ONLY_SNAPSHOT" in res.output
