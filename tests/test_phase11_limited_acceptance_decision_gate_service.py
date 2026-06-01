import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mpf import __version__
from mpf.services import phase11_limited_acceptance_decision_gate_service as service
from tests.test_phase11e_limited_activation_execute_service import _j, _sha

SCOPE = {"candidate_customer_key": "limited-btc-001", "lane": "btc", "public_port": 20101, "backend_target": "172.18.0.3:60010"}


def _kwargs(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    def add(name, payload):
        artifact = _j(path / f"{name}.json", payload)
        return {f"{name}_json": str(artifact), f"{name}_json_sha256": _sha(artifact)}
    window = {**SCOPE, "final_decision": "PHASE11E_LIMITED_CUSTOMER_OBSERVATION_WINDOW_READY", "samples_collected": 3,
        "limited_customer_status": "active", "canary_customer_status": "active", "canary_preserved": True,
        "db_ok": True, "proxy_ok": True, "artifact_gate_passed": True, "current_phase_gate_ok": True,
        "production_gates_remain_closed": True, "unknown_mpf_artifacts": [], "forbidden_public_runtime_exposure": False, "blockers": []}
    readiness = {**SCOPE, "final_decision": "PHASE11_FINAL_ACCEPTANCE_READINESS_PLANNING_READY",
        "phase11_final_acceptance_pr_ready": True, "phase11_final_acceptance_allowed": False,
        "production_expansion_allowed": False, "miner_traffic_expansion_allowed": False,
        "abuse_automation_allowed": False, "ui_allowed": False, "telegram_allowed": False, "blockers": []}
    artifact = {"final_decision": "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS", "unknown_mpf_artifacts": [],
        "forbidden_public_runtime_exposure": False, "production_gates_remain_closed": True}
    kwargs = {"expected_version": __version__, "operator": "operator", "reason": "read-only decision", **add("observation_window", window),
        **add("final_readiness_planning", readiness), **add("artifact_gate", artifact)}
    kwargs.update({name: True for name in service.CONFIRMATIONS})
    return kwargs


def _run(path: Path, edit=None, *, hash_mismatch=False):
    kwargs = _kwargs(path)
    if edit:
        name, changes = edit
        artifact = Path(kwargs[f"{name}_json"])
        payload = json.loads(artifact.read_text())
        payload.update(changes)
        _j(artifact, payload)
        kwargs[f"{name}_json_sha256"] = _sha(artifact)
    if hash_mismatch:
        kwargs["observation_window_json_sha256"] = "0" * 64
    return service.build_phase11_limited_acceptance_decision_gate_report(SimpleNamespace(), **kwargs)


def test_ready_path_is_limited_decision_only(tmp_path):
    report = _run(tmp_path)
    assert report["final_decision"] == "PHASE11_LIMITED_ACCEPTANCE_DECISION_GATE_READY"
    assert report["limited_acceptance_decision_ready"] is True
    assert report["controlled_boundary_package_pr_ready"] is True
    assert report["next_required_step"] == "phase11_controlled_boundary_acceptance_package_pr"
    for key in ("phase11_final_acceptance_allowed", "production_expansion_allowed", "miner_traffic_expansion_allowed",
        "abuse_automation_allowed", "ui_allowed", "telegram_allowed", "mutation_performed", "db_mutation_performed",
        "firewall_apply_performed", "conntrack_flush_performed", "docker_restart_performed", "systemd_restart_performed", "phase11_accepted"):
        assert report[key] is False


@pytest.mark.parametrize("edit", [
    ("observation_window", {"final_decision": "BLOCKED"}),
    ("final_readiness_planning", {"final_decision": "BLOCKED"}),
    ("observation_window", {"samples_collected": 2}),
    ("observation_window", {"limited_customer_status": "paused"}),
    ("observation_window", {"canary_customer_status": "paused"}),
    ("observation_window", {"canary_preserved": False}),
    ("artifact_gate", {"unknown_mpf_artifacts": ["unsafe"]}),
])
def test_blocks_unsafe_or_incomplete_evidence(tmp_path, edit):
    assert _run(tmp_path, edit)["final_decision"] == "BLOCKED"


def test_blocks_hash_mismatch(tmp_path):
    report = _run(tmp_path, hash_mismatch=True)
    assert report["final_decision"] == "BLOCKED"
    assert "observation_window_json_hash_mismatch" in report["blockers"]


def test_blocks_if_current_phase_gate_opens(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "validate_current_phase_gate", lambda blockers: blockers.append("current_phase_gate_open:production_traffic"))
    report = _run(tmp_path)
    assert report["final_decision"] == "BLOCKED"
    assert report["current_phase_gate_ok"] is False
