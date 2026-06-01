import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest


SCRIPT_PATH = Path("scripts/phase11e_run_limited_activation_execute_package.sh")
SCRIPT = SCRIPT_PATH.read_text(encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


@pytest.fixture
def helper_args(tmp_path: Path) -> tuple[list[str], Path, Path, Path]:
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    decision = _write_json(inputs / "decision.json", {})
    execution = _write_json(inputs / "execution-package.json", {})
    rollback = _write_json(inputs / "rollback.json", {})
    artifact = _write_json(inputs / "artifact.json", {})
    source = _write_json(inputs / "source.json", {"db_status": {"ok": True, "status": "OK"}, "proxy_doctor": {"ok": True, "final_verdict": "OK"}, "mpf_doctor": {"ok": True, "status": "OK"}, "lanes": [{"name": "btc", "enabled": True}], "customers": [{"customer_key": "limited-btc-001", "status": "active", "lane": "btc"}], "current_controlled_artifact_gate": {"production_gates_remain_closed": True}})
    out_dir = tmp_path / "out"
    args = [
        "bash", str(SCRIPT_PATH),
        "--expected-version", "0.1.228",
        "--decision-json", str(decision), "--decision-json-sha256", _sha(decision),
        "--execution-package-json", str(execution), "--execution-package-json-sha256", _sha(execution),
        "--rollback-package-json", str(rollback), "--rollback-package-json-sha256", _sha(rollback),
        "--artifact-gate-json", str(artifact), "--artifact-gate-json-sha256", _sha(artifact),
        "--out-dir", str(out_dir), "--operator", "test-operator", "--reason", "test-reason",
    ]
    return args, out_dir, source, tmp_path


def _fake_mpf(tmp_path: Path) -> tuple[Path, Path]:
    fake = tmp_path / "fake-mpf"
    log = tmp_path / "fake-mpf.log"
    fake.write_text(
        """#!/usr/bin/env bash
set -Eeuo pipefail
printf '%s\\n' \"$*\" >> \"$FAKE_MPF_LOG\"
command=\"$2\"
out_json=
while [ \"$#\" -gt 0 ]; do
  if [ \"$1\" = --out-json ]; then out_json=\"$2\"; break; fi
  shift
done
[ -n \"$out_json\" ]
if [ \"$command\" = phase11e-limited-activation-execute ]; then
  printf '%s\\n' \"${FAKE_EXECUTION_JSON:?}\" > \"$out_json\"
else
  printf '{\"final_decision\":\"PHASE11E_LIMITED_ACTIVATION_POST_EVIDENCE_READY\"}\\n' > \"$out_json\"
fi
""",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    return fake, log


def _execute_flags() -> list[str]:
    return [
        "--execute", "--operator-confirmed",
        "--i-understand-this-mutates-limited-customer-db-state", "--i-understand-limited-btc-001-only",
        "--i-understand-canary-must-be-preserved", "--i-understand-no-firewall-apply",
        "--i-understand-no-unrestricted-production", "--i-understand-no-miner-traffic-expansion",
        "--i-understand-no-abuse-automation", "--i-understand-phase11-not-accepted",
        "--i-have-reviewed-rollback-package", "--i-have-reviewed-post-evidence-command",
    ]


def _env(fake: Path, log: Path, execution_json: str) -> dict[str, str]:
    return {**os.environ, "MPF_BIN": str(fake), "FAKE_MPF_LOG": str(log), "FAKE_EXECUTION_JSON": execution_json}


def test_script_resolves_console_entrypoint_and_writes_manifests() -> None:
    assert "MPF_BIN" in SCRIPT
    assert "PYTHON_BIN" in SCRIPT
    assert '"$MPF_BIN" production phase11e-limited-activation-execute' in SCRIPT
    assert '"$MPF_BIN" production phase11e-limited-activation-post-evidence-collect' in SCRIPT
    assert "-m mpf" not in SCRIPT
    assert "manifest.json" in SCRIPT
    assert "sha256-manifest.txt" in SCRIPT


def test_dry_run_manifest_reports_no_helper_mutation(helper_args: tuple[list[str], Path, Path, Path]) -> None:
    args, out_dir, _, _ = helper_args
    subprocess.run(args, check=True)
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["execute_requested"] is False
    assert manifest["mutation_performed_by_helper"] is False


def test_execute_manifest_reflects_execution_json_mutation_fields(helper_args: tuple[list[str], Path, Path, Path]) -> None:
    args, out_dir, _, tmp_path = helper_args
    fake, log = _fake_mpf(tmp_path)
    execution = json.dumps({"mutation_performed": True, "db_mutation_performed": True, "activation_executed": True, "final_decision": "PHASE11E_LIMITED_ACTIVATION_EXECUTED_PENDING_EVIDENCE"})
    subprocess.run(args + _execute_flags(), check=True, env=_env(fake, log, execution))
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["mutation_performed_by_helper"] is True
    assert manifest["db_mutation_performed_by_helper"] is True
    assert manifest["activation_executed_by_helper"] is True
    assert manifest["execution_final_decision"] == "PHASE11E_LIMITED_ACTIVATION_EXECUTED_PENDING_EVIDENCE"


def test_malformed_execute_json_fails_closed_without_manifest(helper_args: tuple[list[str], Path, Path, Path]) -> None:
    args, out_dir, _, tmp_path = helper_args
    fake, log = _fake_mpf(tmp_path)
    out_dir.mkdir()
    (out_dir / "manifest.json").write_text("stale misleading manifest", encoding="utf-8")
    result = subprocess.run(args + _execute_flags(), check=False, env=_env(fake, log, "not-json"), capture_output=True, text=True)
    assert result.returncode != 0
    assert not (out_dir / "manifest.json").exists()


def test_post_evidence_collection_passes_optional_source_evidence_args(helper_args: tuple[list[str], Path, Path, Path]) -> None:
    args, _, source, tmp_path = helper_args
    fake, log = _fake_mpf(tmp_path)
    execution = json.dumps({"mutation_performed": True, "db_mutation_performed": True, "activation_executed": True, "final_decision": "PHASE11E_LIMITED_ACTIVATION_EXECUTED_PENDING_EVIDENCE"})
    post_flags = ["--collect-post-evidence", "--source-evidence-json", str(source), "--source-evidence-json-sha256", _sha(source), "--i-understand-post-evidence-only", "--i-understand-no-db-mutation", "--i-understand-no-production-traffic-expansion"]
    subprocess.run(args + _execute_flags() + post_flags, check=True, env=_env(fake, log, execution))
    post_call = log.read_text(encoding="utf-8").splitlines()[1]
    assert "phase11e-limited-activation-post-evidence-collect" in post_call
    assert f"--source-evidence-json {source}" in post_call
    assert f"--source-evidence-json-sha256 {_sha(source)}" in post_call


def test_script_requires_execute_and_excludes_forbidden_mutation_commands() -> None:
    assert 'if [ "$EXECUTE" != true ]' in SCRIPT
    for forbidden in (
        "iptables-restore", "conntrack -F", "conntrack -D", "docker restart", "docker compose up",
        "docker compose down", "docker compose restart", "systemctl restart", "systemctl enable",
        "mpf customer activate", "mpf abuse hard", "mpf abuse unhard",
    ):
        assert forbidden not in SCRIPT
