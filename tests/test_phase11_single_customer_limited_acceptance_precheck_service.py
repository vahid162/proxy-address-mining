import hashlib
import json
from pathlib import Path

from mpf.config import load_config
from mpf.services import phase11_single_customer_limited_acceptance_precheck_service as service


cfg = lambda: load_config(Path("configs/mpf.example.yaml"))


def write_json(path: Path, obj: object) -> Path:
    path.write_text(json.dumps(obj), encoding="utf-8")
    return path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def base_visibility(visibility_sha: str | None = None) -> dict[str, object]:
    del visibility_sha
    return {
        "expected_version": "0.1.218",
        "repository_version": "0.1.218",
        "candidate_customer_key": "limited-btc-001",
        "candidate_lane": "btc",
        "candidate_public_port": 20101,
        "candidate_backend_target": "172.18.0.3:60010",
        "final_decision": "PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY",
        "visibility_bundle_ready": True,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "phase11_accepted": False,
        "db_activation_allowed": False,
        "mutation_performed": False,
    }


def base_readiness(*, kind: str, visibility_sha: str) -> dict[str, object]:
    ready_key = "abuse_1h_coverage_ready" if kind == "abuse" else "restart_container_order_ready"
    return {
        "expected_version": "0.1.282",
        "repository_version": "0.1.282",
        "source_visibility_bundle_version": "0.1.218",
        "source_visibility_bundle_repository_version": "0.1.218",
        "candidate_customer_key": "limited-btc-001",
        "candidate_lane": "btc",
        "candidate_public_port": 20101,
        "candidate_backend_target": "172.18.0.3:60010",
        "visibility_bundle_sha256": visibility_sha,
        ready_key: True,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "abuse_automation_enabled": False,
        "phase11_accepted": False,
        "db_activation_allowed": False,
        "mutation_performed": False,
    }


def test_blocks_on_non_dict_and_safety_flags(tmp_path):
    visibility = write_json(tmp_path / "visibility.json", [])
    abuse = write_json(
        tmp_path / "abuse.json",
        {
            "abuse_1h_coverage_ready": True,
            "production_traffic_enabled": False,
            "miner_traffic_allowed": False,
            "abuse_automation_enabled": False,
            "phase11_accepted": False,
            "db_activation_allowed": False,
            "mutation_performed": False,
        },
    )
    restart = write_json(
        tmp_path / "restart.json",
        {
            "restart_container_order_ready": True,
            "production_traffic_enabled": True,
            "miner_traffic_allowed": False,
            "abuse_automation_enabled": False,
            "phase11_accepted": False,
            "db_activation_allowed": False,
            "mutation_performed": False,
        },
    )

    report = service.build_phase11_single_customer_limited_acceptance_precheck_report(
        cfg(),
        visibility_bundle_json=visibility,
        visibility_bundle_json_sha256=sha256(visibility),
        abuse_1h_readiness_json=abuse,
        restart_container_order_readiness_json=restart,
        operator="operator",
        reason="test",
        operator_confirmed=True,
        i_understand_precheck_only=True,
        i_understand_no_customer_activation=True,
        i_understand_no_production_traffic_acceptance=True,
        i_understand_no_miner_traffic_acceptance=True,
        i_understand_no_db_activation=True,
    )

    assert report["final_decision"] == "BLOCKED"
    assert "visibility_bundle_invalid" in report["blockers"]
    assert "restart_readiness_safety_boundary_open" in report["blockers"]


def test_ready_accepts_0218_source_visibility_bundle_with_0219_readiness_reports(tmp_path):
    visibility = write_json(tmp_path / "visibility.json", base_visibility())
    visibility_sha = sha256(visibility)
    abuse = write_json(tmp_path / "abuse.json", base_readiness(kind="abuse", visibility_sha=visibility_sha))
    restart = write_json(tmp_path / "restart.json", base_readiness(kind="restart", visibility_sha=visibility_sha))

    report = service.build_phase11_single_customer_limited_acceptance_precheck_report(
        cfg(),
        expected_version="0.1.282",
        visibility_bundle_json=visibility,
        visibility_bundle_json_sha256=visibility_sha,
        abuse_1h_readiness_json=abuse,
        abuse_1h_readiness_json_sha256=sha256(abuse),
        restart_container_order_readiness_json=restart,
        restart_container_order_readiness_json_sha256=sha256(restart),
        operator="operator",
        reason="test",
        operator_confirmed=True,
        i_understand_precheck_only=True,
        i_understand_no_customer_activation=True,
        i_understand_no_production_traffic_acceptance=True,
        i_understand_no_miner_traffic_acceptance=True,
        i_understand_no_db_activation=True,
    )

    assert report["final_decision"] == "PHASE11_SINGLE_CUSTOMER_LIMITED_ACCEPTANCE_PRECHECK_READY"
    assert report["limited_acceptance_precheck_ready"] is True
    assert report["source_visibility_bundle_version"] == "0.1.218"
    assert report["source_visibility_bundle_repository_version"] == "0.1.218"
    assert report["repository_version"] == "0.1.282"
    assert report["phase11_accepted"] is False
    assert report["production_traffic_enabled"] is False
    assert report["miner_traffic_allowed"] is False
    assert report["db_activation_allowed"] is False
    assert report["mutation_performed"] is False


def test_blocks_on_readiness_visibility_hash_mismatch(tmp_path):
    visibility = write_json(tmp_path / "visibility.json", base_visibility())
    visibility_sha = sha256(visibility)
    abuse_payload = base_readiness(kind="abuse", visibility_sha="wrong-sha")
    abuse = write_json(tmp_path / "abuse.json", abuse_payload)
    restart = write_json(tmp_path / "restart.json", base_readiness(kind="restart", visibility_sha=visibility_sha))

    report = service.build_phase11_single_customer_limited_acceptance_precheck_report(
        cfg(),
        expected_version="0.1.282",
        visibility_bundle_json=visibility,
        visibility_bundle_json_sha256=visibility_sha,
        abuse_1h_readiness_json=abuse,
        restart_container_order_readiness_json=restart,
        operator="operator",
        reason="test",
        operator_confirmed=True,
        i_understand_precheck_only=True,
        i_understand_no_customer_activation=True,
        i_understand_no_production_traffic_acceptance=True,
        i_understand_no_miner_traffic_acceptance=True,
        i_understand_no_db_activation=True,
    )

    assert report["final_decision"] == "BLOCKED"
    assert "abuse_readiness_visibility_bundle_sha256_mismatch" in report["blockers"]
