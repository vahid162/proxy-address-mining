from __future__ import annotations

import time
from datetime import datetime

from mpf.config import MPFConfig
from mpf.services import customer_read_service
from mpf.services.phase11e_limited_activation_common import (
    CANARY_KEY, SCOPE, base_report, load_hashed_json, source_db_ok, source_proxy_ok,
    validate_artifact_gate, validate_confirmations, validate_current_phase_gate,
    validate_expected_version, validate_operator, validate_scope,
)

CONFIRMATIONS = (
    "operator_confirmed", "i_understand_observation_window_only", "i_understand_no_db_mutation",
    "i_understand_no_firewall_apply", "i_understand_no_runtime_change",
    "i_understand_no_production_traffic_expansion", "i_understand_no_miner_traffic_expansion",
    "i_understand_no_abuse_automation", "i_understand_phase11_not_accepted",
)


def _parse_window(kwargs: dict[str, object], blockers: list[str]) -> tuple[str, str, int, int]:
    start, end = str(kwargs.get("window_start", "")).strip(), str(kwargs.get("window_end", "")).strip()
    try:
        start_dt, end_dt = datetime.fromisoformat(start.replace("Z", "+00:00")), datetime.fromisoformat(end.replace("Z", "+00:00"))
        if end_dt < start_dt: blockers.append("observation_window_invalid")
    except ValueError:
        blockers.append("observation_window_invalid")
    try: interval = int(kwargs.get("sample_interval_seconds", -1))
    except (TypeError, ValueError): interval = -1
    try: minimum = int(kwargs.get("min_samples", 0))
    except (TypeError, ValueError): minimum = 0
    if interval < 0: blockers.append("sample_interval_seconds_invalid")
    if minimum < 1: blockers.append("min_samples_invalid")
    try:
        if interval >= 0 and minimum >= 1 and (minimum - 1) * interval > (end_dt - start_dt).total_seconds(): blockers.append("observation_window_too_short")
    except UnboundLocalError:
        pass
    return start, end, interval, minimum


def _read_customer_sample(config: MPFConfig, blockers: list[str]) -> tuple[str | None, str | None]:
    try:
        rows = customer_read_service.list_customer_status(config, include_deleted=False, limit=5000)
    except Exception:  # noqa: BLE001 - observation reports fail closed
        blockers.append("customer_state_read_failed")
        return None, None
    if not rows.ok:
        blockers.append("customer_state_read_failed")
        return None, None
    limited_rows = [r for r in rows.customers if r.customer_key == SCOPE["candidate_customer_key"]]
    canary_rows = [r for r in rows.customers if r.customer_key == CANARY_KEY]
    if len(limited_rows) != 1: blockers.append("limited_customer_missing_or_ambiguous")
    if len(canary_rows) != 1: blockers.append("canary_missing_or_ambiguous")
    limited = limited_rows[0] if len(limited_rows) == 1 else None
    canary = canary_rows[0] if len(canary_rows) == 1 else None
    if limited is not None:
        if limited.status != "active": blockers.append("limited_customer_not_active")
        if limited.lane != SCOPE["lane"] or limited.port != SCOPE["public_port"]: blockers.append("limited_customer_scope_mismatch")
    if canary is not None and canary.status != "active": blockers.append("canary_missing_or_not_active")
    return None if limited is None else limited.status, None if canary is None else canary.status


def build_phase11e_limited_customer_observation_window_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    blockers: list[str] = []
    expected_version = validate_expected_version(kwargs, blockers)
    validate_operator(kwargs, blockers); validate_confirmations(kwargs, CONFIRMATIONS, blockers)
    observation = load_hashed_json(kwargs, "observation_json", "observation_json_sha256", blockers)
    review = load_hashed_json(kwargs, "acceptance_review_json", "acceptance_review_json_sha256", blockers)
    artifact = load_hashed_json(kwargs, "artifact_gate_json", "artifact_gate_json_sha256", blockers)
    source = load_hashed_json(kwargs, "source_evidence_json", "source_evidence_json_sha256", blockers)
    validate_scope(observation, blockers, "observation"); validate_scope(review, blockers, "acceptance_review")
    validate_artifact_gate(artifact, blockers)
    before_gate = len(blockers); validate_current_phase_gate(blockers); current_phase_gate_ok = len(blockers) == before_gate
    start, end, interval, minimum = _parse_window(kwargs, blockers)
    observation_ready = observation is not None and observation.get("final_decision") == "PHASE11E_LIMITED_ACTIVATION_OBSERVATION_READY"
    review_ready = review is not None and review.get("final_decision") == "PHASE11E_LIMITED_ACTIVATION_ACCEPTANCE_REVIEW_READY"
    if not observation_ready: blockers.append("limited_activation_observation_not_ready")
    if not review_ready: blockers.append("limited_activation_acceptance_review_not_ready")
    db_ok, proxy_ok = source is not None and source_db_ok(source), source is not None and source_proxy_ok(source)
    if not db_ok or not proxy_ok: blockers.append("source_evidence_db_or_proxy_not_ok")
    samples: list[dict[str, object]] = []
    limited_status = canary_status = None
    if minimum > 0 and interval >= 0 and not blockers:
        for index in range(minimum):
            limited_status, canary_status = _read_customer_sample(config, blockers)
            samples.append({"sample": index + 1, "limited_customer_status": limited_status, "canary_customer_status": canary_status})
            if interval and index + 1 < minimum: time.sleep(interval)
    artifact_passed = artifact is not None and not any(x in blockers for x in ("artifact_gate_not_passed", "unknown_mpf_artifacts", "forbidden_public_runtime_exposure", "production_gates_not_closed"))
    ready = not blockers and len(samples) >= minimum
    report = base_report("phase11e_limited_customer_observation_window", expected_version)
    report.update({"window_start": start, "window_end": end, "sample_interval_seconds": interval, "min_samples": minimum,
        "samples_collected": len(samples), "samples": samples, "observation_ready": observation_ready, "acceptance_review_ready": review_ready,
        "source_evidence_ready": db_ok and proxy_ok, "artifact_gate_passed": artifact_passed, "limited_customer_status": limited_status,
        "canary_customer_status": canary_status, "canary_preserved": canary_status == "active", "db_ok": db_ok, "proxy_ok": proxy_ok,
        "doctor_ok": db_ok and proxy_ok, "current_phase_gate_ok": current_phase_gate_ok,
        "production_gates_remain_closed": None if artifact is None else artifact.get("production_gates_remain_closed"),
        "unknown_mpf_artifacts": None if artifact is None else artifact.get("unknown_mpf_artifacts"),
        "forbidden_public_runtime_exposure": None if artifact is None else artifact.get("forbidden_public_runtime_exposure"),
        "ui_allowed": False, "telegram_allowed": False, "blockers": sorted(set(blockers)), "warnings": [],
        "next_required_step": "phase11_final_acceptance_readiness_planning" if ready else "fix_blockers_and_rerun_observation_window",
        "final_decision": "PHASE11E_LIMITED_CUSTOMER_OBSERVATION_WINDOW_READY" if ready else "BLOCKED"})
    return report
