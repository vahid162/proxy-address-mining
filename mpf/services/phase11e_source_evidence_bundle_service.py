from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig

EXPECTED = {"customer_key": "limited-btc-001", "lane": "btc", "public_port": 20101, "backend_target": "172.18.0.3:60010"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path, blockers: list[str], missing: str, invalid: str) -> dict[str, object] | None:
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




def _bad_source_label(v: object) -> bool:
    if not isinstance(v, str):
        return False
    return v.strip().lower() in {"default","synthetic","placeholder","docs+tests","runtime-observation","exposure-observation","source_bundle"}
def _is_ok_status(obj: dict[str, object]) -> bool:
    val = str(obj.get("status", "")).upper()
    return val in {"OK", "PASS", "HEALTHY", "READY"} or obj.get("ok") is True


def build_phase11e_source_evidence_bundle_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    warnings: list[str] = []
    expected_version = str(kwargs.get("expected_version", __version__))

    for c in [
        "operator_confirmed",
        "i_understand_read_only",
        "i_understand_no_activation",
        "i_understand_no_firewall_apply",
        "i_understand_no_db_mutation",
        "i_understand_no_restart",
        "i_understand_no_abuse_automation",
    ]:
        if kwargs.get(c) is not True:
            blockers.append(f"missing_confirmation:{c}")

    vis_path = Path(str(kwargs.get("visibility_bundle_json", "")))
    vis = _load_json(vis_path, blockers, "visibility_bundle_missing", "visibility_bundle_invalid")
    vis_sha = str(kwargs.get("visibility_bundle_json_sha256", ""))
    if vis is not None and _sha(vis_path) != vis_sha:
        blockers.append("visibility_bundle_hash_mismatch")

    phase = kwargs.get("phase_status") if isinstance(kwargs.get("phase_status"), dict) else None
    mpf_doctor = kwargs.get("mpf_doctor") if isinstance(kwargs.get("mpf_doctor"), dict) else None
    db_status = kwargs.get("db_status") if isinstance(kwargs.get("db_status"), dict) else None
    proxy_doctor = kwargs.get("proxy_doctor") if isinstance(kwargs.get("proxy_doctor"), dict) else None
    lanes = kwargs.get("lanes") if isinstance(kwargs.get("lanes"), list) else None
    customers = kwargs.get("customers") if isinstance(kwargs.get("customers"), list) else None
    artifact = kwargs.get("current_controlled_artifact_gate") if isinstance(kwargs.get("current_controlled_artifact_gate"), dict) else None
    runtime_order_observations = kwargs.get("runtime_order_observations") if isinstance(kwargs.get("runtime_order_observations"), dict) else None
    exposure_observations = kwargs.get("exposure_observations") if isinstance(kwargs.get("exposure_observations"), dict) else None
    abuse_contract_observations = kwargs.get("abuse_contract_observations") if isinstance(kwargs.get("abuse_contract_observations"), dict) else None

    if phase is None:
        blockers.append("missing_phase_status_source")
    if mpf_doctor is None:
        blockers.append("missing_mpf_doctor_source")
    if db_status is None:
        blockers.append("missing_db_status_source")
    if proxy_doctor is None:
        blockers.append("missing_proxy_doctor_source")
    if lanes is None:
        blockers.append("missing_lane_source")
    if customers is None:
        blockers.append("missing_customer_source")
    if artifact is None:
        blockers.append("missing_current_controlled_artifact_gate_source")
    if runtime_order_observations is None:
        blockers.append("missing_runtime_order_observations")
    elif not runtime_order_observations.get("source_files") or not runtime_order_observations.get("source_hashes"):
        blockers.append("runtime_order_observations_missing_source_references")
    if exposure_observations is None:
        blockers.append("missing_exposure_observations")
    elif not exposure_observations.get("source_files") or not exposure_observations.get("source_hashes"):
        blockers.append("exposure_observations_missing_source_references")
    if abuse_contract_observations is None:
        blockers.append("missing_abuse_contract_observations")
    elif not abuse_contract_observations.get("source_files") or not abuse_contract_observations.get("source_hashes"):
        blockers.append("abuse_contract_observations_missing_source_references")

    if vis is not None:
        if vis.get("expected_version") != "0.1.218":
            blockers.append("unsupported_source_visibility_bundle_version")
        if vis.get("candidate_customer_key") != EXPECTED["customer_key"] or vis.get("candidate_lane") != EXPECTED["lane"] or vis.get("candidate_public_port") != EXPECTED["public_port"] or vis.get("candidate_backend_target") != EXPECTED["backend_target"]:
            blockers.append("visibility_bundle_scope_mismatch")
        for f in ("production_traffic_enabled", "miner_traffic_allowed", "phase11_accepted", "db_activation_allowed", "mutation_performed"):
            if vis.get(f) is not False:
                blockers.append("visibility_bundle_safety_boundary_open")
                break

    if phase is not None:
        required_phase = {
            "production_traffic": "none",
            "firewall_apply_allowed": "no",
            "abuse_automation_allowed": "no",
            "customer_onboarding_allowed": "db_only",
            "ui_allowed": "no",
            "telegram_allowed": "no",
        }
        for k, v in required_phase.items():
            if str(phase.get(k)) != v:
                blockers.append(f"unsafe_phase_status:{k}")

    if mpf_doctor is not None and (_bad_source_label(mpf_doctor.get("source")) or not _is_ok_status(mpf_doctor)):
        blockers.append("mpf_doctor_not_ok")
    if db_status is not None and (_bad_source_label(db_status.get("source")) or not _is_ok_status(db_status)):
        blockers.append("db_status_not_ok")
    if proxy_doctor is not None and (_bad_source_label(proxy_doctor.get("source")) or not _is_ok_status(proxy_doctor)):
        blockers.append("proxy_doctor_not_ok")

    lanes_val = lanes or []
    customers_val = customers or []
    if lanes is not None:
        btc_enabled = any(isinstance(x, dict) and x.get("name") == "btc" and x.get("enabled") is True for x in lanes_val)
        if not btc_enabled:
            blockers.append("btc_lane_not_enabled")
    if customers is not None:
        limited_paused = any(isinstance(x, dict) and x.get("customer_key") == "limited-btc-001" and x.get("status") == "paused" for x in customers_val)
        if not limited_paused:
            blockers.append("limited_btc_001_not_paused")

    if artifact is not None:
        if kwargs.get("current_controlled_artifact_gate_sha256") in (None, ""):
            blockers.append("missing_artifact_gate_source_hash")
        if artifact.get("repository_version") != __version__:
            blockers.append("artifact_gate_repository_version_mismatch")
        if artifact.get("current_phase_gate_ok") is not True:
            blockers.append("artifact_gate_phase_not_ok")
        if artifact.get("unknown_mpf_artifacts") != []:
            blockers.append("unknown_mpf_artifacts")
        if artifact.get("forbidden_public_runtime_exposure") is not False:
            blockers.append("forbidden_public_runtime_exposure")
        if artifact.get("production_gates_remain_closed") is not True:
            blockers.append("artifact_gate_production_gates_open")
        if artifact.get("final_decision") not in {"PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS", "PASS_NO_CUSTOMER_ARTIFACTS"}:
            blockers.append("artifact_gate_not_passed")

    active = [
        c.get("customer_key")
        for c in customers_val
        if isinstance(c, dict)
        and c.get("status") == "active"
        and c.get("lane") in [l.get("name") for l in lanes_val if isinstance(l, dict) and l.get("enabled")]
    ]
    paused = [c.get("customer_key") for c in customers_val if isinstance(c, dict) and c.get("status") == "paused"]
    disabled = [l.get("name") for l in lanes_val if isinstance(l, dict) and not l.get("enabled")]

    ready = len(blockers) == 0
    return {
        "component": "phase11e_source_evidence_bundle",
        "expected_version": expected_version,
        "repository_version": __version__,
        "source_visibility_bundle_version": None if vis is None else vis.get("expected_version"),
        "source_visibility_bundle_repository_version": None if vis is None else vis.get("repository_version"),
        "candidate_customer_key": EXPECTED["customer_key"],
        "candidate_lane": EXPECTED["lane"],
        "candidate_public_port": EXPECTED["public_port"],
        "candidate_backend_target": EXPECTED["backend_target"],
        "visibility_bundle_sha256": vis_sha,
        "phase_status": phase or {},
        "mpf_doctor": mpf_doctor or {},
        "db_status": db_status or {},
        "proxy_doctor": proxy_doctor or {},
        "lanes": lanes_val,
        "customers": customers_val,
        "active_enabled_lane_customers": active,
        "paused_candidate_customers": paused,
        "disabled_lanes": disabled,
        "current_controlled_artifact_gate": artifact or {},
        "current_controlled_artifact_gate_sha256": kwargs.get("current_controlled_artifact_gate_sha256"),
        "runtime_order_observations": runtime_order_observations or {},
        "exposure_observations": exposure_observations or {},
        "abuse_contract_observations": abuse_contract_observations or {},
        "source_files": kwargs.get("source_files", []),
        "source_hashes": kwargs.get("source_hashes", {}),
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "abuse_automation_enabled": False,
        "phase11_accepted": False,
        "db_activation_allowed": False,
        "mutation_performed": False,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "final_decision": "PHASE11E_SOURCE_EVIDENCE_BUNDLE_READY" if ready else "BLOCKED",
    }
