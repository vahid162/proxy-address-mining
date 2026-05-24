from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service
from mpf.services.phase11_single_customer_firewall_apply_gate_service import _parse_live_snapshot, _read_live_snapshot

TARGET = "limited-btc-001:btc:20101:172.18.0.3:60010"
EMBEDDED_PLAN_GATE_SHA = "0893d1d63b7cb7f60a3473ad9f922c3f65bc9b3e6ff8d5b84aecfa701d45c438"
EMBEDDED_PLAN_SUMMARY_SHA = "7e971dd7e635f46bde2b568ecf133d6ec9ddd1a211386591a95df97d2ee18a41"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_read(path: Path | None, blocker: str) -> tuple[str | None, str | None]:
    if path is None:
        return None, blocker
    if not path.exists() or not path.is_file():
        return None, blocker
    return _sha(path.read_bytes()), None


def _parse_post_apply(snapshot: str) -> dict[str, object]:
    lines = snapshot.splitlines()
    canary_nat = [l for l in lines if "MPF_NAT_PRE" in l and "--dport 20001" in l and "-j DNAT" in l]
    dnat_20101 = [l for l in lines if "MPF_NAT_PRE" in l and "--dport 20101" in l and "-j DNAT" in l]
    unrelated = [l for l in lines if "-A MPF_NAT_PRE" in l and "mpf:" in l and "limited-btc-001" not in l and "canary-btc-001" not in l]
    connlimit_rules = [l for l in lines if "-A MPFC_20101" in l and "--dport 20101" in l and "mpf:limited-btc-001:customer_connlimit_reject" in l and "-j REJECT" in l]
    hashlimit_rules = [l for l in lines if "-A MPFC_20101" in l and "--dport 20101" in l and "mpf:limited-btc-001:customer_hashlimit_reject" in l and "-j REJECT" in l]
    return {
        "mpf_nat_pre_exists": ":MPF_NAT_PRE" in snapshot,
        "mpfc_20001_exists": ":MPFC_20001" in snapshot,
        "mpfc_20101_exists": ":MPFC_20101" in snapshot,
        "canary_20001_exact_artifact_preserved": len([l for l in canary_nat if "--to-destination 172.18.0.3:60010" in l and "mpf:canary-btc-001:customer_nat_redirect" in l]) == 1,
        "dnat_20101_exact_target_count": len([l for l in dnat_20101 if "--to-destination 172.18.0.3:60010" in l and "mpf:limited-btc-001:customer_nat_redirect" in l]),
        "dnat_20101_loopback_count": len([l for l in dnat_20101 if "--to-destination 127.0.0.1:" in l]),
        "unrelated_customer_nat_rule_count": len(unrelated),
        "limited_20101_connlimit_reject_rule_count": len(connlimit_rules),
        "limited_20101_hashlimit_reject_rule_count": len(hashlimit_rules),
        "limited_20101_filter_primitives_verified": len(connlimit_rules) == 1 and len(hashlimit_rules) == 1,
    }


def _payload() -> str:
    return """*filter
:MPFC_20101 - [0:0]
-A MPFC_20101 -p tcp --dport 20101 -m connlimit --connlimit-above 120 -m comment --comment \"mpf:limited-btc-001:customer_connlimit_reject\" -j REJECT
-A MPFC_20101 -p tcp --dport 20101 -m hashlimit --hashlimit-above 40/sec --hashlimit-burst 80 --hashlimit-mode srcip --hashlimit-name mpf_20101 -m comment --comment \"mpf:limited-btc-001:customer_hashlimit_reject\" -j REJECT
COMMIT
*nat
-A MPF_NAT_PRE -p tcp -m comment --comment \"mpf:limited-btc-001:customer_nat_redirect\" --dport 20101 -j DNAT --to-destination 172.18.0.3:60010
COMMIT
"""


def build_phase11_single_customer_firewall_apply_execution_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    expected_version = str(kwargs.get("expected_version", __version__))
    execute = bool(kwargs.get("execute", False))
    blockers: list[str] = []
    payload = _payload()
    payload_sha = _sha(payload.encode("utf-8"))

    result = {
        "component": "phase11_single_customer_firewall_apply_execution",
        "expected_version": expected_version,
        "repository_version": __version__,
        "candidate_customer_key": "limited-btc-001",
        "candidate_lane": "btc",
        "candidate_public_port": 20101,
        "candidate_backend_target": "172.18.0.3:60010",
        "execute_requested": execute,
        "firewall_apply_allowed": False,
        "nat_apply_allowed": False,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "phase11_accepted": False,
        "generated_apply_payload_sha256": payload_sha,
    }

    path = Path(str(kwargs.get("apply_gate_json", "")))
    gate_data: dict[str, object] | None = None
    file_sha: str | None = None
    if not path.exists() or not path.is_file():
        blockers.append("apply_gate_json_missing")
    else:
        raw = path.read_bytes()
        file_sha = _sha(raw)
        result["apply_gate_json_file_sha256"] = file_sha
        try:
            gate_data = json.loads(raw.decode("utf-8"))
        except Exception:
            blockers.append("apply_gate_json_invalid")

    supplied_file_sha = kwargs.get("apply_gate_json_file_sha256")
    if supplied_file_sha and file_sha and str(supplied_file_sha) != file_sha:
        blockers.append("apply_gate_json_file_hash_mismatch")

    if expected_version != __version__:
        blockers.append("expected_version_mismatch")

    required_gate = {
        "component": "phase11_single_customer_firewall_apply_gate",
        "expected_version": "0.1.203",
        "repository_version": "0.1.203",
        "candidate_customer_key": "limited-btc-001",
        "candidate_lane": "btc",
        "candidate_public_port": 20101,
        "candidate_backend_target": "172.18.0.3:60010",
        "phase11e_firewall_apply_gate_ready": True,
        "apply_gate_package_generated": True,
        "firewall_apply_execution_allowed": False,
        "firewall_apply_allowed": False,
        "nat_apply_allowed": False,
        "iptables_restore_authorized": False,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "phase11_accepted": False,
        "limited_onboarding_allowed": False,
        "db_mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "docker_mutation_performed": False,
        "mutation_performed": False,
        "next_required_step": "phase11e_single_customer_firewall_apply_execution_pr",
        "final_decision": "PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_GATE_READY",
    }
    if gate_data is not None:
        if gate_data.get("blockers") != [] or gate_data.get("warnings") != []:
            blockers.append("apply_gate_not_ready")
        if any(gate_data.get(k) != v for k, v in required_gate.items()):
            blockers.append("apply_gate_not_ready")
        if gate_data.get("firewall_plan_gate_json_sha256") != EMBEDDED_PLAN_GATE_SHA:
            blockers.append("embedded_firewall_plan_gate_hash_mismatch")
        if gate_data.get("plan_summary_sha256") != EMBEDDED_PLAN_SUMMARY_SHA:
            blockers.append("embedded_plan_summary_hash_mismatch")
        live = gate_data.get("live_firewall_summary") if isinstance(gate_data.get("live_firewall_summary"), dict) else {}
        expected_live = {
            "canary_nat_chain_present": True,
            "canary_customer_chain_present": True,
            "canary_20001_nat_rule_count": 1,
            "canary_20001_exact_target_rule_count": 1,
            "canary_20001_loopback_rule_count": 0,
            "canary_comment_present": True,
            "limited_20101_chain_present": False,
            "limited_20101_dnat_present": False,
            "limited_customer_reference_present": False,
        }
        if any(live.get(k) != v for k, v in expected_live.items()):
            blockers.append("apply_gate_live_summary_mismatch")

    for f, b in {
        "operator_confirmed": "operator_not_confirmed",
        "i_understand_single_customer_apply_execution": "single_customer_apply_not_confirmed",
        "i_understand_firewall_nat_apply_will_mutate_host_in_execute_mode": "host_mutation_not_confirmed",
        "i_understand_no_production_traffic_acceptance": "no_production_traffic_boundary_not_confirmed",
        "i_understand_no_miner_traffic_acceptance": "no_miner_traffic_boundary_not_confirmed",
        "i_confirm_pre_apply_snapshot_taken": "pre_apply_snapshot_not_confirmed",
        "i_confirm_restore_point_created": "restore_point_not_confirmed",
        "i_confirm_operator_lock_acquired": "operator_lock_not_confirmed",
        "i_confirm_rollback_artifact_created": "rollback_artifact_not_confirmed",
        "i_confirm_canary_20001_must_be_preserved": "canary_preserve_not_confirmed",
        "i_confirm_post_apply_verification_required": "post_apply_verify_not_confirmed",
        "i_confirm_runtime_path_evidence_required_after_apply": "runtime_evidence_not_confirmed",
        "i_confirm_abuse_1h_evidence_required_before_customer_traffic": "abuse_evidence_not_confirmed",
        "i_confirm_restart_container_order_evidence_required_before_limited_acceptance": "restart_evidence_not_confirmed",
    }.items():
        if kwargs.get(f) is not True:
            blockers.append(b)

    try:
        customers = customer_read_service.list_customer_status(config, include_deleted=False, limit=5000)
    except Exception:
        customers = customer_read_service.CustomerList(ok=False, message="exception", customers=[])
    if not customers.ok:
        blockers.append("db_read_failed")
    else:
        rows = customers.customers
        staged = [r for r in rows if r.customer_key == "limited-btc-001"]
        if len(staged) != 1:
            blockers.append("staged_customer_missing")
        else:
            s = staged[0]
            if s.lane != "btc" or s.port != 20101:
                blockers.append("staged_customer_scope_mismatch")
            if str(getattr(s, "status", "")).strip().lower() != "paused":
                blockers.append("staged_customer_not_paused")
        if [r for r in rows if r.port == 20101 and r.customer_key != "limited-btc-001"]:
            blockers.append("candidate_port_collision")

    try:
        pre_snap = _read_live_snapshot(Path(str(kwargs.get("live_snapshot_file"))) if kwargs.get("live_snapshot_file") else None, bool(kwargs.get("collect_live", False)), kwargs.get("live_snapshot_reader"))
    except Exception:
        pre_snap = ""
        blockers.append("live_firewall_read_failed")
    if pre_snap:
        _, pre_blockers = _parse_live_snapshot(pre_snap)
        blockers.extend(pre_blockers)

    if any(x in payload for x in (" -F", " -X", " -D", " -I")) or "*mangle" in payload or "*raw" in payload:
        blockers.append("payload_unsafe")

    if execute and os.getenv("CI"):
        blockers.append("execute_forbidden_in_ci")
    if execute and (os.getenv("MPF_PHASE11_SINGLE_CUSTOMER_APPLY_EXECUTION") != "allow" or os.getenv("MPF_PHASE11_SINGLE_CUSTOMER_APPLY_TARGET") != TARGET or os.getenv("MPF_PHASE11_SINGLE_CUSTOMER_APPLY_I_UNDERSTAND_HOST_FIREWALL_MUTATION") != "allow"):
        blockers.append("apply_execution_environment_not_confirmed")

    pre_file = Path(str(kwargs.get("pre_apply_snapshot_file"))) if kwargs.get("pre_apply_snapshot_file") else None
    rb_file = Path(str(kwargs.get("rollback_artifact_file"))) if kwargs.get("rollback_artifact_file") else None
    rs_path = Path(str(kwargs.get("restore_point_path"))) if kwargs.get("restore_point_path") else None
    lock_id = str(kwargs.get("operator_lock_id", "")).strip()

    pre_sha, pre_block = _safe_read(pre_file, "pre_apply_snapshot_file_missing")
    rb_sha, rb_block = _safe_read(rb_file, "rollback_artifact_file_missing")
    result["pre_apply_snapshot_sha256"] = pre_sha
    result["rollback_artifact_sha256"] = rb_sha
    result["required_pre_apply_artifacts"] = ["pre_apply_snapshot_file", "rollback_artifact_file", "restore_point_path", "operator_lock_id"]
    missing = []
    if pre_block: missing.append("pre_apply_snapshot_file")
    if rb_block: missing.append("rollback_artifact_file")
    if rs_path is None or not rs_path.exists(): missing.append("restore_point_path")
    if not lock_id: missing.append("operator_lock_id")
    result["missing_pre_apply_artifacts"] = missing

    if execute:
        if pre_block: blockers.append(pre_block)
        if rb_block: blockers.append(rb_block)
        if rs_path is None or not rs_path.exists(): blockers.append("restore_point_missing")
        if not lock_id: blockers.append("operator_lock_missing")

    if blockers:
        return {
            **result,
            "apply_execution_ready": False,
            "firewall_apply_execution_allowed": False,
            "iptables_restore_authorized": False,
            "mutation_performed": False,
            "firewall_mutation_performed": False,
            "nat_mutation_performed": False,
            "blockers": sorted(set(blockers)),
            "warnings": [],
            "final_decision": "BLOCKED",
        }

    if not execute:
        return {
            **result,
            "apply_execution_ready": True,
            "firewall_apply_execution_allowed": False,
            "iptables_restore_authorized": False,
            "mutation_performed": False,
            "firewall_mutation_performed": False,
            "nat_mutation_performed": False,
            "payload_summary": {"has_filter_commit": "COMMIT\n*nat" in payload, "single_20101_dnat_count": payload.count("--dport 20101")},
            "required_operator_command": "mpf production single-customer-firewall-apply-execute --execute ...",
            "required_post_apply_evidence": ["post_apply_snapshot", "verify_canary_20001", "verify_20101_redirect", "runtime_path_evidence"],
            "blockers": [],
            "warnings": [],
            "final_decision": "PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_EXECUTION_PACKAGE_READY",
        }

    test_cp = subprocess.run(["iptables-restore", "--test", "--noflush"], input=payload, text=True, capture_output=True, check=False)
    if test_cp.returncode != 0:
        return {**result, "apply_execution_ready": True, "firewall_apply_execution_allowed": False, "iptables_restore_authorized": False, "mutation_performed": False, "blockers": ["FAILED_APPLY_EXECUTION"], "warnings": [], "final_decision": "FAILED_APPLY_EXECUTION"}
    apply_cp = subprocess.run(["iptables-restore", "--noflush"], input=payload, text=True, capture_output=True, check=False)
    if apply_cp.returncode != 0:
        return {**result, "apply_execution_ready": True, "firewall_apply_execution_allowed": False, "iptables_restore_authorized": False, "mutation_performed": False, "partial_apply_possible": True, "blockers": ["FAILED_APPLY_EXECUTION"], "warnings": [], "final_decision": "FAILED_APPLY_EXECUTION"}

    post_cp = subprocess.run(["iptables-save"], capture_output=True, text=True, check=False)
    if post_cp.returncode != 0:
        return {**result, "apply_execution_ready": True, "firewall_apply_execution_allowed": False, "iptables_restore_authorized": False, "mutation_performed": False, "partial_apply_possible": True, "blockers": ["FAILED_POST_APPLY_VERIFICATION"], "warnings": [], "final_decision": "FAILED_POST_APPLY_VERIFICATION"}
    post = _parse_post_apply(post_cp.stdout)
    ok = post["mpf_nat_pre_exists"] and post["mpfc_20001_exists"] and post["mpfc_20101_exists"] and post["canary_20001_exact_artifact_preserved"] and post["dnat_20101_exact_target_count"] == 1 and post["dnat_20101_loopback_count"] == 0 and post["unrelated_customer_nat_rule_count"] == 0 and post["limited_20101_connlimit_reject_rule_count"] == 1 and post["limited_20101_hashlimit_reject_rule_count"] == 1 and post["limited_20101_filter_primitives_verified"] is True
    if not ok:
        return {**result, "apply_execution_ready": True, "firewall_apply_execution_allowed": False, "iptables_restore_authorized": False, "mutation_performed": False, "partial_apply_possible": True, "post_apply_verification": post, "blockers": ["FAILED_POST_APPLY_VERIFICATION"], "warnings": [], "final_decision": "FAILED_POST_APPLY_VERIFICATION"}

    return {**result, "apply_execution_ready": True, "firewall_apply_execution_allowed": True, "iptables_restore_authorized": True, "mutation_performed": True, "firewall_mutation_performed": True, "nat_mutation_performed": True, "post_apply_verification": post, "blockers": [], "warnings": [], "next_required_step": "phase11e_post_apply_runtime_evidence_pr", "final_decision": "PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_EXECUTED_PENDING_REVIEW"}
