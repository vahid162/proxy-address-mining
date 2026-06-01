import hashlib
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mpf.interfaces.cli import app


RUNNER = CliRunner()
CONFIG = "configs/mpf.example.yaml"


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _decision_args(tmp_path: Path) -> list[str]:
    payloads = {
        "visibility-bundle": {"final_decision": "PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY", "candidate_customer_key": "limited-btc-001", "candidate_lane": "btc", "candidate_public_port": 20101, "candidate_backend_target": "172.18.0.3:60010", "production_traffic_enabled": False, "miner_traffic_allowed": False, "abuse_automation_enabled": False, "phase11_accepted": False, "db_activation_allowed": False, "mutation_performed": False},
        "source-evidence": {"final_decision": "PHASE11E_SOURCE_EVIDENCE_BUNDLE_READY", "candidate_customer_key": "limited-btc-001", "candidate_lane": "btc", "candidate_public_port": 20101, "candidate_backend_target": "172.18.0.3:60010", "production_traffic_enabled": False, "miner_traffic_allowed": False, "abuse_automation_enabled": False, "phase11_accepted": False, "db_activation_allowed": False, "mutation_performed": False},
        "abuse-readiness": {"final_decision": "PHASE11_SINGLE_CUSTOMER_ABUSE_1H_READINESS_READY", "candidate_customer_key": "limited-btc-001"},
        "restart-readiness": {"final_decision": "PHASE11_SINGLE_CUSTOMER_RESTART_CONTAINER_ORDER_READINESS_READY", "candidate_lane": "btc"},
        "limited-acceptance-precheck": {"final_decision": "PHASE11_SINGLE_CUSTOMER_LIMITED_ACCEPTANCE_PRECHECK_READY", "candidate_public_port": 20101, "candidate_backend_target": "172.18.0.3:60010"},
        "artifact-gate": {"final_decision": "PASS_NO_CUSTOMER_ARTIFACTS", "unknown_mpf_artifacts": [], "production_gates_remain_closed": True},
    }
    args = ["production", "phase11e-limited-activation-decision"]
    for option, payload in payloads.items():
        path = _write_json(tmp_path / f"{option}.json", payload)
        args.extend([f"--{option}-json", str(path), f"--{option}-json-sha256", _sha256(path)])
    return args + [
        "--operator", "operator", "--reason", "regression-test", "--operator-confirmed",
        "--i-understand-decision-only", "--i-understand-no-activation-performed", "--i-understand-no-db-mutation",
        "--i-understand-no-firewall-apply", "--i-understand-no-production-traffic", "--i-understand-no-miner-traffic",
        "--i-understand-no-abuse-automation", "--i-understand-phase11-not-accepted",
    ]


def _decision_file(tmp_path: Path) -> Path:
    return _write_json(tmp_path / "decision.json", {"final_decision": "PHASE11E_LIMITED_ACTIVATION_DECISION_READY"})


def _execution_package_args(tmp_path: Path, *, digest: str | None = None) -> list[str]:
    path = _decision_file(tmp_path)
    return [
        "production", "phase11e-limited-activation-execution-package", "--limited-activation-decision-json", str(path),
        "--limited-activation-decision-json-sha256", digest or _sha256(path), "--operator", "operator", "--reason", "regression-test",
        "--operator-confirmed", "--i-understand-package-only", "--i-understand-no-activation-performed", "--i-understand-no-db-mutation",
        "--i-understand-no-firewall-apply", "--i-understand-no-production-traffic", "--i-understand-no-miner-traffic",
        "--i-understand-no-abuse-automation", "--i-understand-phase11-not-accepted",
    ]


def _rollback_package_args(tmp_path: Path) -> list[str]:
    path = _decision_file(tmp_path)
    return [
        "production", "phase11e-limited-activation-rollback-package", "--limited-activation-decision-json", str(path),
        "--limited-activation-decision-json-sha256", _sha256(path), "--operator", "operator", "--reason", "regression-test",
        "--operator-confirmed", "--i-understand-rollback-package-only", "--i-understand-no-rollback-performed",
        "--i-understand-no-db-mutation", "--i-understand-no-firewall-apply",
    ]


def _post_evidence_args(tmp_path: Path) -> list[str]:
    path = _write_json(tmp_path / "activation-execution.json", {"candidate_customer_key": "limited-btc-001"})
    return [
        "production", "phase11e-limited-activation-post-evidence", "--activation-execution-json", str(path),
        "--activation-execution-json-sha256", _sha256(path), "--operator", "operator", "--reason", "regression-test",
        "--operator-confirmed", "--i-understand-post-evidence-only", "--i-understand-no-db-mutation", "--i-understand-no-firewall-apply",
        "--i-understand-no-production-traffic-expansion", "--i-understand-no-miner-traffic-expansion",
    ]


@pytest.mark.parametrize(
    ("args_builder", "expected_decision"),
    [
        (_decision_args, "PHASE11E_LIMITED_ACTIVATION_DECISION_READY"),
        (_execution_package_args, "PHASE11E_LIMITED_ACTIVATION_EXECUTION_PACKAGE_READY"),
        (_rollback_package_args, "PHASE11E_LIMITED_ACTIVATION_ROLLBACK_PACKAGE_READY"),
        (_post_evidence_args, "PHASE11E_LIMITED_ACTIVATION_POST_EVIDENCE_READY"),
    ],
)
def test_phase11e_limited_activation_cli_commands_write_out_json_without_duplicate_config(tmp_path, args_builder, expected_decision):
    out_json = tmp_path / f"{expected_decision}.json"
    result = RUNNER.invoke(app, [*args_builder(tmp_path), "--out-json", str(out_json), "--output", "json", "--config", CONFIG])
    assert result.exit_code == 0, result.stdout
    report = json.loads(result.stdout)
    assert report["final_decision"] == expected_decision
    assert json.loads(out_json.read_text(encoding="utf-8")) == report


def test_phase11e_limited_activation_decision_missing_confirmations_is_blocked_not_traceback(tmp_path):
    args = [item for item in _decision_args(tmp_path) if item != "--operator-confirmed"]
    result = RUNNER.invoke(app, [*args, "--output", "json", "--config", CONFIG])
    assert result.exit_code == 0, result.stdout
    report = json.loads(result.stdout)
    assert report["final_decision"] == "BLOCKED"
    assert "missing_confirmation:operator_confirmed" in report["blockers"]


def test_phase11e_limited_activation_execution_package_wrong_hash_is_blocked_not_traceback(tmp_path):
    result = RUNNER.invoke(app, [*_execution_package_args(tmp_path, digest="wrong-hash"), "--output", "json", "--config", CONFIG])
    assert result.exit_code == 0, result.stdout
    report = json.loads(result.stdout)
    assert report["final_decision"] == "BLOCKED"
    assert "decision_hash_mismatch" in report["blockers"]
