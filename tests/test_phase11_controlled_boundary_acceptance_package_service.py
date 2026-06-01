import hashlib
import json
from types import SimpleNamespace

import pytest
from mpf import __version__
from mpf.services import phase11_controlled_boundary_acceptance_package_service as service

SCOPE = {"candidate_customer_key": "limited-btc-001", "lane": "btc", "public_port": 20101, "backend_target": "172.18.0.3:60010"}

def _write(path, payload):
    path.write_text(json.dumps(payload) + "\n")
    return str(path), hashlib.sha256(path.read_bytes()).hexdigest()

def _kwargs(tmp_path):
    decision = {**SCOPE, "final_decision": "PHASE11_LIMITED_ACCEPTANCE_DECISION_GATE_READY", "limited_acceptance_decision_ready": True, "controlled_boundary_package_pr_ready": True, "phase11_final_acceptance_allowed": False, "production_expansion_allowed": False, "miner_traffic_expansion_allowed": False, "abuse_automation_allowed": False, "ui_allowed": False, "telegram_allowed": False, "blockers": []}
    artifact = {"final_decision": "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS", "current_phase_gate_ok": True, "unknown_mpf_artifacts": [], "forbidden_public_runtime_exposure": False, "production_gates_remain_closed": True}
    source = {**SCOPE, "db_ok": True, "proxy_ok": True, "customers": [{"customer_key": "limited-btc-001", "status": "active"}, {"customer_key": "canary-btc-001", "status": "active"}], "required_containers_running": True, "required_listeners_local_only": True}
    abuse = {**SCOPE, "final_decision": "PHASE11_SINGLE_CUSTOMER_ABUSE_1H_READINESS_READY", "abuse_1h_coverage_ready": True, "abuse_state_machine_contract_ready": True, "hard_after_1h_contract_ready": True, "no_farms_only_hard_contract_ready": True, "no_worker_only_hard_contract_ready": True, "no_missing_stale_evidence_hard_contract_ready": True, "abuse_automation_enabled": False, "mutation_performed": False, "blockers": []}
    restart = {**SCOPE, "final_decision": "PHASE11_SINGLE_CUSTOMER_RESTART_CONTAINER_ORDER_READINESS_READY", "restart_container_order_ready": True, "container_order_contract_ready": True, "local_only_runtime_ready": True, "backend_public_exposure_blocked": True, "backend_internal_reachability_ready": True, "production_traffic_enabled": False, "miner_traffic_allowed": False, "abuse_automation_enabled": False, "mutation_performed": False, "blockers": []}
    kwargs = {"expected_version": __version__, "operator": "operator", "reason": "read-only package"}
    for name, payload in (("limited_acceptance_decision", decision), ("artifact_gate", artifact), ("source_evidence", source), ("abuse_readiness", abuse), ("restart_readiness", restart)):
        kwargs[f"{name}_json"], kwargs[f"{name}_json_sha256"] = _write(tmp_path / f"{name}.json", payload)
    for name in service.CONFIRMATIONS: kwargs[name] = True
    return kwargs

def _run(tmp_path, edit=None, hash_mismatch=False):
    kwargs = _kwargs(tmp_path)
    if edit:
        name, changes = edit; path = tmp_path / f"{name}.json"; payload = json.loads(path.read_text()); payload.update(changes); kwargs[f"{name}_json"], kwargs[f"{name}_json_sha256"] = _write(path, payload)
    if hash_mismatch: kwargs["source_evidence_json_sha256"] = "0" * 64
    return service.build_phase11_controlled_boundary_acceptance_package_report(SimpleNamespace(), **kwargs)

def test_ready_path_keeps_all_dangerous_gates_closed(tmp_path):
    report = _run(tmp_path)
    assert report["final_decision"] == "PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_PACKAGE_READY"
    assert report["next_required_step"] == "phase11_controlled_boundary_acceptance_decision_pr"
    for key in ("phase11_final_acceptance_allowed", "production_expansion_allowed", "miner_traffic_expansion_allowed", "abuse_automation_allowed", "ui_allowed", "telegram_allowed", "mutation_performed", "db_mutation_performed", "firewall_apply_performed", "conntrack_flush_performed", "docker_restart_performed", "systemd_restart_performed", "phase11_accepted"):
        assert report[key] is False

@pytest.mark.parametrize("edit", [("limited_acceptance_decision", {"final_decision": "BLOCKED"}), ("source_evidence", {"db_ok": False}), ("source_evidence", {"proxy_ok": False}), ("source_evidence", {"customers": [{"customer_key": "limited-btc-001", "status": "paused"}, {"customer_key": "canary-btc-001", "status": "active"}]}), ("source_evidence", {"customers": [{"customer_key": "limited-btc-001", "status": "active"}, {"customer_key": "canary-btc-001", "status": "paused"}]}), ("artifact_gate", {"unknown_mpf_artifacts": ["unsafe"]}), ("abuse_readiness", {"final_decision": "BLOCKED"}), ("restart_readiness", {"final_decision": "BLOCKED"})])
def test_blocks_unsafe_or_incomplete_evidence(tmp_path, edit):
    assert _run(tmp_path, edit)["final_decision"] == "BLOCKED"

def test_blocks_hash_mismatch(tmp_path):
    assert "source_evidence_json_hash_mismatch" in _run(tmp_path, hash_mismatch=True)["blockers"]

def test_blocks_if_current_phase_gate_opens(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "validate_current_phase_gate", lambda blockers: blockers.append("current_phase_gate_open:production_traffic"))
    report = _run(tmp_path); assert report["final_decision"] == "BLOCKED" and report["current_phase_gate_ok"] is False
