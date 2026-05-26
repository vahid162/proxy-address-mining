from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig

EXP = {"customer_key": "limited-btc-001", "lane": "btc", "public_port": 20101, "backend_target": "172.18.0.3:60010"}
SAFETY_FLAGS = ["production_traffic_enabled", "miner_traffic_allowed", "abuse_automation_enabled", "phase11_accepted", "db_activation_allowed", "mutation_performed"]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load(path: Path, blockers: list[str], missing: str, invalid: str) -> dict[str, object] | None:
    if not path.exists() or not path.is_file():
        blockers.append(missing)
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        blockers.append(invalid)
        return None
    if not isinstance(obj, dict):
        blockers.append(invalid)
        return None
    return obj


def _validate_scope_and_safety(obj: dict[str, object] | None, blockers: list[str], tag: str) -> None:
    if not isinstance(obj, dict):
        return
    ck = obj.get("candidate_customer_key", obj.get("customer_key"))
    ln = obj.get("candidate_lane", obj.get("lane"))
    pp = obj.get("candidate_public_port", obj.get("public_port"))
    bt = obj.get("candidate_backend_target", obj.get("backend_target"))
    if ck is not None and ck != EXP["customer_key"]:
        blockers.append(f"scope_mismatch:{tag}")
    if ln is not None and ln != EXP["lane"]:
        blockers.append(f"scope_mismatch:{tag}")
    if pp is not None and int(pp) != EXP["public_port"]:
        blockers.append(f"scope_mismatch:{tag}")
    if bt is not None and bt != EXP["backend_target"]:
        blockers.append(f"scope_mismatch:{tag}")
    for flag in SAFETY_FLAGS:
        if flag in obj and obj.get(flag) is not False:
            blockers.append(f"safety_flag_open:{tag}")


def build_phase11e_limited_activation_decision_report(config: MPFConfig, **k: object) -> dict[str, object]:
    del config
    b: list[str] = []

    for c in [
        "operator_confirmed", "i_understand_decision_only", "i_understand_no_activation_performed", "i_understand_no_db_mutation",
        "i_understand_no_firewall_apply", "i_understand_no_production_traffic", "i_understand_no_miner_traffic",
        "i_understand_no_abuse_automation", "i_understand_phase11_not_accepted",
    ]:
        if k.get(c) is not True:
            b.append(f"missing_confirmation:{c}")

    def _load_hashed(name: str, sha_key: str, missing_hash_blocker: str, mismatch_blocker: str) -> dict[str, object] | None:
        path = Path(str(k.get(name, "")))
        obj = _load(path, b, f"{name}_missing", f"{name}_invalid")
        exp = str(k.get(sha_key, "")).strip()
        if not exp:
            b.append(missing_hash_blocker)
            return obj
        if obj is not None and _sha(path) != exp:
            b.append(mismatch_blocker)
        return obj

    vis = _load_hashed("visibility_bundle_json", "visibility_bundle_json_sha256", "missing_visibility_bundle_hash", "visibility_bundle_hash_mismatch")
    src = _load_hashed("source_evidence_json", "source_evidence_json_sha256", "missing_source_evidence_hash", "source_evidence_hash_mismatch")
    abuse = _load_hashed("abuse_readiness_json", "abuse_readiness_json_sha256", "missing_abuse_readiness_hash", "abuse_readiness_hash_mismatch")
    rst = _load_hashed("restart_readiness_json", "restart_readiness_json_sha256", "missing_restart_readiness_hash", "restart_readiness_hash_mismatch")
    pre = _load_hashed("limited_acceptance_precheck_json", "limited_acceptance_precheck_json_sha256", "missing_limited_acceptance_precheck_hash", "limited_acceptance_precheck_hash_mismatch")
    art = _load_hashed("artifact_gate_json", "artifact_gate_json_sha256", "missing_artifact_gate_hash", "artifact_gate_hash_mismatch")

    expected_decisions = [
        (vis, "PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY", "visibility_bundle_not_ready"),
        (src, "PHASE11E_SOURCE_EVIDENCE_BUNDLE_READY", "source_evidence_not_ready"),
        (abuse, "PHASE11_SINGLE_CUSTOMER_ABUSE_1H_READINESS_READY", "abuse_readiness_not_ready"),
        (rst, "PHASE11_SINGLE_CUSTOMER_RESTART_CONTAINER_ORDER_READINESS_READY", "restart_readiness_not_ready"),
        (pre, "PHASE11_SINGLE_CUSTOMER_LIMITED_ACCEPTANCE_PRECHECK_READY", "limited_acceptance_precheck_not_ready"),
    ]
    for obj, expected, blocker in expected_decisions:
        if isinstance(obj, dict) and obj.get("final_decision") != expected:
            b.append(blocker)

    for obj, tag in [(vis, "visibility"), (src, "source"), (abuse, "abuse_readiness"), (rst, "restart_readiness"), (pre, "limited_acceptance_precheck")]:
        _validate_scope_and_safety(obj, b, tag)

    if isinstance(art, dict):
        if art.get("final_decision") not in {"PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS", "PASS_NO_CUSTOMER_ARTIFACTS"}:
            b.append("artifact_gate_not_passed")
        if art.get("unknown_mpf_artifacts") != []:
            b.append("unknown_mpf_artifacts")
        if art.get("production_gates_remain_closed") is not True:
            b.append("production_gates_not_closed")

    ready = not b
    return {
        "component": "phase11e_limited_activation_decision",
        "expected_version": str(k.get("expected_version", __version__)),
        "repository_version": __version__,
        "candidate_customer_key": EXP["customer_key"],
        "lane": EXP["lane"],
        "public_port": EXP["public_port"],
        "backend_target": EXP["backend_target"],
        "visibility_bundle_sha256": k.get("visibility_bundle_json_sha256"),
        "source_evidence_sha256": k.get("source_evidence_json_sha256"),
        "artifact_gate_sha256": k.get("artifact_gate_json_sha256"),
        "abuse_readiness_final_decision": None if abuse is None else abuse.get("final_decision"),
        "restart_readiness_final_decision": None if rst is None else rst.get("final_decision"),
        "limited_acceptance_precheck_final_decision": None if pre is None else pre.get("final_decision"),
        "all_readiness_inputs_ready": ready,
        "controlled_activation_decision_ready": ready,
        "activation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "abuse_automation_enabled": False,
        "phase11_accepted": False,
        "blockers": sorted(set(b)),
        "warnings": [],
        "next_required_step": "phase11e_limited_activation_execution_package_review" if ready else "fix_blockers_and_regenerate",
        "final_decision": "PHASE11E_LIMITED_ACTIVATION_DECISION_READY" if ready else "BLOCKED",
    }
