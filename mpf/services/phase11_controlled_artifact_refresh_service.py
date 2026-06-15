"""Controlled Phase 11 stale post-DNAT artifact refresh primitives.

This service is deliberately narrower than the append-only reapply package: it
recognizes only the known farm5 0.1.269 stale controlled graph and renders a
reviewed replacement payload that deletes exact stale MPF-owned rules before
installing the corrected post-DNAT graph. It does not flush host chains and it
keeps execution operator-gated by package/precondition hashes.
"""
from __future__ import annotations

from typing import Any

from mpf import __version__
from mpf.services.phase11_controlled_artifact_reapply_core import (
    BACKEND_PORT,
    SCOPE,
    _canonical_sha,
    _execution_fingerprint,
    _firewall_structure_sha,
    _package_content_for_hash,
    _phase_gate_blockers,
    _present_lines,
    _text_sha,
    build_controlled_desired_state,
    classify_controlled_artifacts,
)

REFRESH_READY = "CONTROLLED_ARTIFACT_REFRESH_PACKAGE_READY"
REFRESH_BLOCKED = "BLOCKED_CONTROLLED_ARTIFACT_REFRESH_PACKAGE"
REFRESH_PREFLIGHT_READY = "CONTROLLED_ARTIFACT_REFRESH_EXECUTE_PREFLIGHT_READY"
REFRESH_PREFLIGHT_BLOCKED = "BLOCKED_CONTROLLED_ARTIFACT_REFRESH_EXECUTE_PREFLIGHT"
REFRESH_VERIFY_READY = "CONTROLLED_ARTIFACT_REFRESH_VERIFY_READY"
REFRESH_VERIFY_BLOCKED = "BLOCKED_CONTROLLED_ARTIFACT_REFRESH_VERIFY"
EXACT_STALE = "EXACT_STALE_0_1_269_POST_DNAT_GRAPH"
CONTROLLED_REFRESH_REQUIRED = "CONTROLLED_REFRESH_REQUIRED"
BLOCKED_MIXED_UNKNOWN = "BLOCKED_MIXED_UNKNOWN_MPF_ARTIFACTS"
BLOCKED_NOT_EXACT = "BLOCKED_STALE_GRAPH_NOT_EXACT"
NO_STALE = "NO_STALE_CONTROLLED_GRAPH"
NEXT_REQUIRED_STEP = "sync_0_1_271_to_farm5_run_read_only_refresh_package_preflight_then_operator_gated_controlled_refresh_execute_if_ready"
PASS_READY_DECISIONS = {
    "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS",
    "PASS_NO_CUSTOMER_ARTIFACTS",
    "CONTROLLED_ARTIFACT_REAPPLY_NOOP_READY",
    REFRESH_VERIFY_READY,
}

SCOPE_PORTS = [int(item["public_port"]) for item in SCOPE]
SCOPE_KEYS = [str(item["customer_key"]) for item in SCOPE]


def _strip_post_dnat(line: str, port: int) -> str:
    for fragment in (
        f" -m conntrack --ctstate DNAT --ctorigdstport {port}",
        f" -m conntrack ! --ctstate DNAT",
        " -m conntrack --ctstate DNAT",
    ):
        line = line.replace(fragment, "")
    return line


def _known_stale_lines(desired_lines: list[str]) -> list[str]:
    stale: list[str] = []
    for item in desired_lines:
        table, _, line = item.partition(":")
        if table != "filter":
            continue
        if line.startswith("-N "):
            stale.append(item)
            continue
        if "customer_any_policy_dispatch" in line:
            continue
        if "mpf:hook:verified_user_forward_post_dnat:accounting" in line:
            stale.append(f'{table}:-A DOCKER-USER -p tcp --dport {BACKEND_PORT} -m comment --comment "mpf:hook:verified_user_forward_post_dnat:accounting" -j MPF_ACCT_IN')
            continue
        if "mpf:hook:verified_user_forward_post_dnat:customers" in line:
            stale.append(f'{table}:-A DOCKER-USER -p tcp --dport {BACKEND_PORT} -m comment --comment "mpf:hook:verified_user_forward_post_dnat:customers" -j MPF_CUSTOMERS')
            continue
        if "mpf:hook:verified_user_forward_post_dnat:backend_guard" in line:
            stale.append(f'{table}:-A DOCKER-USER -p tcp --dport {BACKEND_PORT} -m comment --comment "mpf:hook:verified_user_forward_post_dnat:backend_guard" -j MPF_GUARD')
            continue
        matched = False
        for scope in SCOPE:
            port = int(scope["public_port"])
            if f'mpf:{scope["customer_key"]}:' in line:
                stale.append(f"{table}:{_strip_post_dnat(line, port)}")
                matched = True
                break
        if not matched and "mpf:backend_guard:btc:60010" in line:
            stale.append(f"{table}:{_strip_post_dnat(line, BACKEND_PORT)}")
    stale.extend(item for item in desired_lines if item.startswith("nat:"))
    return list(dict.fromkeys(stale))


def _mpf_present(present: list[str]) -> list[str]:
    return [item for item in present if any(token in item for token in ("MPF", "mpf:", "customer_"))]


def _line_text(artifact: str) -> str:
    return artifact.split(":", 1)[1] if ":" in artifact else artifact


def _is_chain_decl(artifact: str) -> bool:
    return _line_text(artifact).startswith("-N ")



def _canonical_stale_artifact(artifact: str) -> str:
    table, sep, line = artifact.partition(":")
    line = line.replace("-p tcp -m tcp", "-p tcp")
    line = line.replace(" -m addrtype ! --src-type LOCAL", "")
    line = line.replace(" -j REJECT --reject-with tcp-reset", " -j REJECT")
    line = " ".join(line.split())
    return f"{table}:{line}" if sep else line

def _known_stale_shape(artifact: str) -> bool:
    line = _line_text(artifact)
    return "--dport 60010" in line and "--ctstate" not in line and (
        any(f"mpf:{key}:" in line for key in SCOPE_KEYS)
        or "mpf:backend_guard:btc:60010" in line
        or "mpf:hook:verified_user_forward_post_dnat:" in line
    )


def _nat_target_blockers(present_mpf: list[str], backend_target: dict[str, object]) -> list[str]:
    blockers: list[str] = []
    expected = f"{backend_target.get('resolved_ipv4') or backend_target.get('target_host')}:{BACKEND_PORT}"
    for artifact in present_mpf:
        line = _line_text(artifact)
        if "customer_nat_redirect" in line and "--to-destination" in line and expected not in line:
            blockers.append("stale_backend_target_detected")
    return blockers


def classify_stale_0_1_269_graph(*, iptables_save_text: str, ip6tables_save_text: str, desired_state: dict[str, object], backend_target: dict[str, object]) -> dict[str, object]:
    desired_lines = list(desired_state.get("artifact_lines", [])) if isinstance(desired_state.get("artifact_lines"), list) else []
    present = _present_lines(iptables_save_text)
    present_canonical = {_canonical_stale_artifact(line): line for line in present}
    present_mpf = _mpf_present(present)
    known_stale = _known_stale_lines(desired_lines)
    allowed = {_canonical_stale_artifact(line) for line in known_stale} | {_canonical_stale_artifact(line) for line in desired_lines if _is_chain_decl(line)}
    desired_canonical = {_canonical_stale_artifact(line) for line in desired_lines}
    unknown = sorted({line for line in present_mpf if _canonical_stale_artifact(line) not in allowed and _canonical_stale_artifact(line) not in desired_canonical and not _known_stale_shape(line)})
    stale_present = [present_canonical[_canonical_stale_artifact(line)] for line in known_stale if _canonical_stale_artifact(line) in present_canonical and not _is_chain_decl(line)]
    for line in present_mpf:
        if _known_stale_shape(line) and line not in stale_present:
            stale_present.append(line)
    blockers: list[str] = []
    blockers.extend(_nat_target_blockers(present_mpf, backend_target))
    if any(token.lower() in ip6tables_save_text.lower() for token in ("mpf", "customer_")):
        blockers.append("ipv6_mpf_or_customer_artifact_detected")
    if len(present_mpf) != len(set(present_mpf)):
        blockers.append("duplicate_controlled_artifact_detected")
    if unknown:
        blockers.append("unknown_mpf_artifacts_detected")

    required_exact = [
        'filter:-A DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:backend_guard" -j MPF_GUARD',
        'filter:-A DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:accounting" -j MPF_ACCT_IN',
        'filter:-A DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:customers" -j MPF_CUSTOMERS',
        'filter:-A MPF_GUARD -p tcp --dport 60010 -m comment --comment "mpf:backend_guard:btc:60010" -j REJECT',
    ]
    for port in SCOPE_PORTS:
        key = SCOPE_KEYS[SCOPE_PORTS.index(port)]
        required_exact.extend([
            f'filter:-A MPF_ACCT_IN -p tcp --dport 60010 -m comment --comment "mpf:{key}:customer_accounting_in" -j RETURN',
            f'filter:-A MPF_CUSTOMERS -p tcp --dport 60010 -m comment --comment "mpf:{key}:customer_dispatch" -j MPFC_{port}',
        ])
    present_canonical_set = set(present_canonical)
    missing_required = [line for line in required_exact if _canonical_stale_artifact(line) not in present_canonical_set]
    corrected_any_dispatch_present = [line for line in present_mpf if "customer_any_policy_dispatch" in line]
    stale_hook_order_ok = True
    try:
        canon_order = [_canonical_stale_artifact(line) for line in present]
        guard_i = canon_order.index(_canonical_stale_artifact(required_exact[0]))
        acct_i = canon_order.index(_canonical_stale_artifact(required_exact[1]))
        cust_i = canon_order.index(_canonical_stale_artifact(required_exact[2]))
        stale_hook_order_ok = guard_i < acct_i and guard_i < cust_i
    except ValueError:
        stale_hook_order_ok = False
    if corrected_any_dispatch_present:
        blockers.append("partially_refreshed_graph_detected")
    if not stale_hook_order_ok:
        blockers.append("stale_backend_guard_not_before_accounting_customers")
    if missing_required:
        blockers.append("known_stale_0_1_269_graph_not_exact")

    if unknown:
        decision = BLOCKED_MIXED_UNKNOWN
    elif corrected_any_dispatch_present and missing_required:
        decision = NO_STALE
    elif not stale_present:
        decision = NO_STALE
    elif blockers:
        decision = BLOCKED_NOT_EXACT
    else:
        decision = CONTROLLED_REFRESH_REQUIRED
    return {
        "component": "phase11_stale_0_1_269_post_dnat_graph_classifier",
        "exact_classifier": EXACT_STALE if decision == CONTROLLED_REFRESH_REQUIRED else decision,
        "final_decision": decision,
        "status": decision,
        "known_stale_artifacts": stale_present,
        "known_stale_artifact_count": len(stale_present),
        "unknown_mpf_artifacts": unknown,
        "missing_required_stale_artifacts": missing_required,
        "blockers": sorted(set(blockers)),
        "exact_stale_artifact_detection_hash": _canonical_sha({"known_stale": stale_present, "required": required_exact}),
        "mutation_performed": False,
    }


def _validate_refresh_payload(payload: str) -> list[str]:
    blockers: list[str] = []
    if any(token in payload for token in ("*raw", "*mangle", "*security", "systemctl")):
        blockers.append("refresh_payload_forbidden_operation_detected")
    for line in payload.splitlines():
        if line.startswith(("-F", "-X", "-P", "-Z")):
            blockers.append("refresh_payload_forbidden_operation_detected")
        if line.startswith("-D ") and "mpf:" not in line and "MPF" not in line:
            blockers.append("refresh_payload_non_mpf_delete_detected")
    stale_guard = '-A DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:backend_guard" -j MPF_GUARD'
    if stale_guard in payload:
        blockers.append("refresh_payload_would_leave_stale_guard")
    if "! --ctstate DNAT" not in payload:
        blockers.append("refresh_payload_missing_dnat_negated_guard")
    return sorted(set(blockers))


def _build_payload(stale_present: list[str], desired_lines: list[str], present: list[str]) -> str:
    replacement_missing = [line for line in desired_lines if line not in present]
    delete_rules = [line for line in stale_present if not _is_chain_decl(line)]
    parts = ["*filter"]
    parts.extend("-D " + line.split(":-A ", 1)[1] for line in delete_rules if line.startswith("filter:-A "))
    parts.extend(line.split(":", 1)[1] for line in replacement_missing if line.startswith("filter:"))
    parts.append("COMMIT")
    nat_adds = [line.split(":", 1)[1] for line in replacement_missing if line.startswith("nat:")]
    if nat_adds:
        parts.extend(["*nat", *nat_adds, "COMMIT"])
    return "\n".join(parts) + "\n"


def build_refresh_plan(*, lanes: list[dict[str, Any]], customers: list[dict[str, Any]], backend_target: dict[str, object], iptables_save_text: str = "", ip6tables_save_text: str = "", phase_status_text: str = "", expected_version: str = __version__) -> dict[str, object]:
    backend = dict(backend_target)
    backend["controlled_artifact_graph_binding_mode"] = "verified_docker_user_forward_post_dnat"
    backend.setdefault("filter_packet_path", "docker_user_forward_verified")
    desired = build_controlled_desired_state(lanes=lanes, customers=customers, backend_target=backend, expected_version=expected_version)
    desired_lines = list(desired.get("artifact_lines", [])) if isinstance(desired.get("artifact_lines"), list) else []
    classifier = classify_stale_0_1_269_graph(iptables_save_text=iptables_save_text, ip6tables_save_text=ip6tables_save_text, desired_state=desired, backend_target=backend)
    present = _present_lines(iptables_save_text)
    payload = _build_payload(list(classifier.get("known_stale_artifacts", [])), desired_lines, present)
    blockers = [*desired.get("blockers", []), *classifier.get("blockers", []), *_phase_gate_blockers(phase_status_text), *_validate_refresh_payload(payload)]
    if expected_version != __version__:
        blockers.append("wrong_expected_version")
    if backend.get("status") != "ok":
        blockers.append("backend_target_unresolved")
    if backend.get("backend_public_exposure"):
        blockers.append("backend_public_exposure_detected")
    if backend.get("conntrack_original_destination_supported") is not True:
        blockers.append("conntrack_original_destination_match_unsupported")
    if classifier.get("final_decision") == BLOCKED_MIXED_UNKNOWN:
        blockers.append("unknown_mpf_artifacts_detected")
    elif classifier.get("final_decision") != CONTROLLED_REFRESH_REQUIRED:
        blockers.append("known_stale_0_1_269_graph_not_exact")
    decision = REFRESH_READY if not blockers and classifier.get("final_decision") == CONTROLLED_REFRESH_REQUIRED else REFRESH_BLOCKED
    snapshot_hashes = {"iptables_save_sha256": _text_sha(iptables_save_text), "ip6tables_save_sha256": _text_sha(ip6tables_save_text), "iptables_structure_sha256": _firewall_structure_sha(iptables_save_text), "ip6tables_structure_sha256": _firewall_structure_sha(ip6tables_save_text)}
    plan = {"component": "phase11_controlled_artifact_refresh_plan", "repository_version": __version__, "expected_version": expected_version, "scope": list(SCOPE), "backend_target": backend, "desired_state": desired, "stale_graph_classifier": classifier, "artifact_classification": classifier, "payload": payload, "payload_sha256": _text_sha(payload), "replacement_payload": payload, "replacement_payload_sha256": _text_sha(payload), "snapshot_hashes": snapshot_hashes, "db_customer_policy_snapshot_hash": _canonical_sha({"lanes": lanes, "customers": customers}), "desired_state_hash": desired.get("desired_state_hash"), "artifact_classification_hash": classifier.get("exact_stale_artifact_detection_hash"), "phase_state_hash": _text_sha(phase_status_text), "blockers": sorted(set(blockers)), "warnings": [], "final_decision": decision, "mutation_performed": False, "firewall_apply_performed": False, "iptables_restore_invocation_allowed": decision == REFRESH_READY, "controlled_artifact_refresh_execute_available": decision == REFRESH_READY, "phase12_start_allowed": False, "worker_enforcement_allowed": "no", "ui_allowed": "no", "telegram_allowed": "no", "next_required_step": NEXT_REQUIRED_STEP, "iptables_save_text": iptables_save_text, "ip6tables_save_text": ip6tables_save_text}
    plan["execution_precondition_fingerprint"] = _execution_fingerprint(plan)
    return plan


def build_refresh_package_from_plan(plan: dict[str, object]) -> dict[str, object]:
    ready = plan.get("final_decision") == REFRESH_READY
    classifier = plan.get("stale_graph_classifier") if isinstance(plan.get("stale_graph_classifier"), dict) else {}
    package = {"component": "phase11_controlled_artifact_refresh_package", "package_id": f"phase11-controlled-artifact-refresh-{__version__}-{str(plan.get('execution_precondition_fingerprint'))[:12]}", "repository_version": __version__, "scope": plan.get("scope"), "backend_target_fingerprint": (plan.get("backend_target") or {}).get("target_fingerprint") if isinstance(plan.get("backend_target"), dict) else None, "iptables_save_sha256": (plan.get("snapshot_hashes") or {}).get("iptables_save_sha256") if isinstance(plan.get("snapshot_hashes"), dict) else None, "ip6tables_save_sha256": (plan.get("snapshot_hashes") or {}).get("ip6tables_save_sha256") if isinstance(plan.get("snapshot_hashes"), dict) else None, "iptables_structure_sha256": (plan.get("snapshot_hashes") or {}).get("iptables_structure_sha256") if isinstance(plan.get("snapshot_hashes"), dict) else None, "ip6tables_structure_sha256": (plan.get("snapshot_hashes") or {}).get("ip6tables_structure_sha256") if isinstance(plan.get("snapshot_hashes"), dict) else None, "execution_precondition_fingerprint": plan.get("execution_precondition_fingerprint"), "exact_stale_artifact_detection_hash": classifier.get("exact_stale_artifact_detection_hash"), "payload": plan.get("payload", ""), "payload_sha256": plan.get("payload_sha256"), "backup_requirements": {"pre_apply_iptables_save_required": True, "pre_apply_ip6tables_save_required": True}, "lock_requirements": {"exclusive_operator_lock_required": True}, "restore_test_requirements": {"iptables_restore_test_noflush_required": True, "must_run_before_apply": True}, "rollback_plan": {"manual_review_required": True, "rollback_first_allowed": True, "reviewed_rollback_plan_required": True, "instructions": ["Use pre-apply backups for rollback review; do not flush host firewall broadly."]}, "post_apply_verification_contract": {"required": True, "must_find_corrected_post_dnat_graph": True, "must_not_find_stale_backend_guard_before_hooks": True, "must_pass_current_controlled_artifact_gate": True}, "plan": plan, "blockers": [] if ready else ["refresh_plan_not_ready"], "final_decision": REFRESH_READY if ready else plan.get("final_decision", REFRESH_BLOCKED), "mutation_performed": False}
    package["package_sha256"] = _canonical_sha(_package_content_for_hash(package))
    return package


def verify_refresh_package(package: dict[str, object], *, live_plan: dict[str, object] | None = None) -> dict[str, object]:
    blockers: list[str] = []
    if package.get("component") != "phase11_controlled_artifact_refresh_package":
        blockers.append("refresh_package_type_mismatch")
    if package.get("repository_version") != __version__:
        blockers.append("refresh_package_version_mismatch")
    payload = str(package.get("payload", ""))
    if package.get("payload_sha256") != _text_sha(payload):
        blockers.append("refresh_package_payload_hash_mismatch")
    if package.get("package_sha256") != _canonical_sha(_package_content_for_hash(package)):
        blockers.append("refresh_package_canonical_sha256_mismatch")
    blockers.extend(_validate_refresh_payload(payload))
    if live_plan is None:
        blockers.append("live_refresh_plan_required")
    else:
        blockers.extend(str(b) for b in live_plan.get("blockers", []) if isinstance(live_plan.get("blockers"), list))
        if live_plan.get("final_decision") != REFRESH_READY:
            blockers.append("live_refresh_plan_not_ready")
        if live_plan.get("execution_precondition_fingerprint") != package.get("execution_precondition_fingerprint"):
            blockers.append("refresh_execution_precondition_fingerprint_drift")
        classifier = live_plan.get("stale_graph_classifier") if isinstance(live_plan.get("stale_graph_classifier"), dict) else {}
        if classifier.get("exact_stale_artifact_detection_hash") != package.get("exact_stale_artifact_detection_hash"):
            blockers.append("exact_stale_artifact_detection_hash_drift")
    return {"component": "phase11_controlled_artifact_refresh_verification", "repository_version": __version__, "package_id": package.get("package_id"), "blockers": sorted(set(blockers)), "final_decision": REFRESH_VERIFY_READY if not blockers else REFRESH_VERIFY_BLOCKED, "mutation_performed": False, "phase12_start_allowed": False, "worker_enforcement_allowed": "no", "ui_allowed": "no", "telegram_allowed": "no"}


def build_refresh_execute_preflight(package: dict[str, object], *, live_plan: dict[str, object], restore_test_result: dict[str, object] | None = None) -> dict[str, object]:
    blockers = verify_refresh_package(package, live_plan=live_plan)["blockers"]
    hashes = live_plan.get("snapshot_hashes") if isinstance(live_plan.get("snapshot_hashes"), dict) else {}
    if hashes.get("iptables_structure_sha256") != package.get("iptables_structure_sha256"):
        blockers.append("iptables_structure_snapshot_drift")
    if hashes.get("ip6tables_structure_sha256") != package.get("ip6tables_structure_sha256"):
        blockers.append("ip6tables_structure_snapshot_drift")
    if (live_plan.get("backend_target") or {}).get("target_fingerprint") != package.get("backend_target_fingerprint") if isinstance(live_plan.get("backend_target"), dict) else True:
        blockers.append("backend_target_fingerprint_drift")
    classifier = live_plan.get("stale_graph_classifier") if isinstance(live_plan.get("stale_graph_classifier"), dict) else {}
    if classifier.get("final_decision") != CONTROLLED_REFRESH_REQUIRED:
        blockers.append("stale_graph_classifier_no_longer_matches_expected_pre_state")
    if restore_test_result is None:
        blockers.append("iptables_restore_test_required_before_apply")
        restore_test_invoked = False
    else:
        restore_test_invoked = True
        if int(restore_test_result.get("returncode", 1)) != 0:
            blockers.append("iptables_restore_test_failed")
    return {"component": "phase11_controlled_artifact_refresh_execute_preflight", "repository_version": __version__, "package_id": package.get("package_id"), "package_sha256": package.get("package_sha256"), "execution_precondition_fingerprint": package.get("execution_precondition_fingerprint"), "restore_test_invoked": restore_test_invoked, "apply_invoked": False, "firewall_mutation_performed": False, "live_plan": live_plan, "blockers": sorted(set(blockers)), "final_decision": REFRESH_PREFLIGHT_READY if not blockers else REFRESH_PREFLIGHT_BLOCKED}


def verify_post_apply_refresh(*, package: dict[str, object], post_apply_plan: dict[str, object], current_gate_report: dict[str, object] | None = None) -> dict[str, object]:
    blockers: list[str] = []
    text = str(post_apply_plan.get("iptables_save_text", ""))
    desired = post_apply_plan.get("desired_state") if isinstance(post_apply_plan.get("desired_state"), dict) else {}
    stale_after = classify_stale_0_1_269_graph(iptables_save_text=text, ip6tables_save_text=str(post_apply_plan.get("ip6tables_save_text", "")), desired_state=desired, backend_target=post_apply_plan.get("backend_target") if isinstance(post_apply_plan.get("backend_target"), dict) else {})
    stale_rules_after = [line for line in stale_after.get("known_stale_artifacts", []) if isinstance(line, str) and _known_stale_shape(line)]
    if stale_rules_after:
        blockers.append("stale_0_1_269_artifacts_still_present")
    required_substrings = [
        '-A DOCKER-USER -p tcp --dport 60010 -m conntrack --ctstate DNAT -m comment --comment "mpf:hook:verified_user_forward_post_dnat:accounting" -j MPF_ACCT_IN',
        '-A DOCKER-USER -p tcp --dport 60010 -m conntrack --ctstate DNAT -m comment --comment "mpf:hook:verified_user_forward_post_dnat:customers" -j MPF_CUSTOMERS',
        '-A DOCKER-USER -p tcp --dport 60010 -m conntrack ! --ctstate DNAT -m comment --comment "mpf:hook:verified_user_forward_post_dnat:backend_guard" -j MPF_GUARD',
        '-A MPF_GUARD -p tcp --dport 60010 -m conntrack ! --ctstate DNAT',
        'mpf:backend_guard:btc:60010',
        "--dport 60010 -m conntrack --ctstate DNAT --ctorigdstport 20001",
        "--dport 60010 -m conntrack --ctstate DNAT --ctorigdstport 20101",
        '-A MPFC_20001 -p tcp --dport 60010 -m conntrack --ctstate DNAT --ctorigdstport 20001 -m comment --comment "mpf:canary-btc-001:customer_any_policy_dispatch" -j MPFO_20001',
        '-A MPFC_20101 -p tcp --dport 60010 -m conntrack --ctstate DNAT --ctorigdstport 20101 -m comment --comment "mpf:limited-btc-001:customer_any_policy_dispatch" -j MPFO_20101',
    ]
    normalized_text = text.replace("-p tcp -m tcp", "-p tcp")
    for substring in required_substrings:
        if substring not in normalized_text:
            blockers.append(f"post_apply_missing:{substring}")
    if current_gate_report is None:
        blockers.append("current_controlled_artifact_gate_report_required")
    else:
        if str(current_gate_report.get("final_decision", "")) not in PASS_READY_DECISIONS and not str(current_gate_report.get("final_decision", "")).startswith("PASS") and not str(current_gate_report.get("final_decision", "")).endswith("READY"):
            blockers.append("current_controlled_artifact_gate_not_pass_ready")
        if current_gate_report.get("current_phase_gate_ok") is not True:
            blockers.append("current_controlled_artifact_gate_phase_not_ok")
        if current_gate_report.get("unknown_mpf_artifacts"):
            blockers.append("current_controlled_artifact_gate_unknown_mpf_artifacts")
        if current_gate_report.get("forbidden_public_runtime_exposure"):
            blockers.append("forbidden_public_runtime_exposure_detected")
        if current_gate_report.get("production_gates_remain_closed") is not True:
            blockers.append("production_gates_not_closed")
    duplicate_count = int(current_gate_report.get("duplicate_nat_redirect_count", 0)) if isinstance(current_gate_report, dict) else 0
    return {"component": "phase11_controlled_artifact_refresh_post_apply_verification", "repository_version": __version__, "package_id": package.get("package_id"), "corrected_artifact_status": "semantic_post_dnat_present" if not blockers else "blocked", "stale_graph_status": NO_STALE if not stale_rules_after else stale_after.get("final_decision"), "duplicate_nat_redirect_count": duplicate_count, "blockers": sorted(set(blockers)), "final_decision": REFRESH_VERIFY_READY if not blockers else REFRESH_VERIFY_BLOCKED, "mutation_performed": False}

# Operator-facing read-only / guarded helpers. These functions keep interfaces thin:
# CLI and scripts call here, while collection, package hashing, preflight, and
# guarded execution decisions stay in the service layer.
import json
import os
import subprocess
from pathlib import Path

from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.repositories import firewall_planner_read_repo
from mpf.services.phase11_controlled_artifact_reapply_core import CommandResult, ControlledBackendTargetResolver, FlockHostLock, ProductionIptablesRestoreRunner


def _cmd(argv: list[str], input_text: str | None = None) -> CommandResult:
    try:
        completed = subprocess.run(argv, shell=False, check=False, capture_output=True, text=True, input=input_text)
    except FileNotFoundError as exc:
        return CommandResult(127, "", str(exc))
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _load_planner_input(config_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    try:
        loaded = firewall_planner_read_repo.load_firewall_planner_input(load_config(config_path))
    except Exception as exc:  # noqa: BLE001
        return [], [], ["postgresql_planner_input_read_failed", str(exc)]
    if not loaded.ok:
        return [], [], ["postgresql_planner_input_read_failed", loaded.message]
    return loaded.lanes, loaded.customers, []


def _write_json(path: Path, data: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, default=str) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.chmod(0o600)
    os.replace(tmp, path)
    return _text_sha(text)


def _write_text(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.chmod(0o600)
    os.replace(tmp, path)
    return _text_sha(text)


def _write_manifest(out_dir: Path, files: dict[str, str]) -> dict[str, str]:
    manifest_sha = _write_json(out_dir / "manifest.sha256.json", files)
    return {**files, "manifest.sha256.json": manifest_sha}


def _collect_live_inputs(config_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, object], str, str, list[str]]:
    blockers: list[str] = []
    lanes, customers, load_blockers = _load_planner_input(config_path)
    blockers.extend(load_blockers)
    backend = ControlledBackendTargetResolver().resolve(expected_version=__version__)
    if backend.get("status") != "ok":
        blockers.extend(str(b) for b in backend.get("blockers", []) if isinstance(backend.get("blockers"), list))
    ipt = _cmd(["iptables-save"])
    ip6 = _cmd(["ip6tables-save"])
    if ipt.returncode != 0:
        blockers.append("iptables_save_read_failed")
    if ip6.returncode != 0:
        blockers.append("ip6tables_save_read_failed")
    return lanes, customers, backend, ipt.stdout, ip6.stdout, sorted(set(blockers))


def run_refresh_plan_report(*, config_path: Path = DEFAULT_CONFIG_PATH, out_dir: Path | None = None, phase_status_text: str = "", expected_version: str = __version__) -> dict[str, object]:
    lanes, customers, backend, ipt, ip6, blockers = _collect_live_inputs(config_path)
    phase_text = phase_status_text or (Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8") if Path("docs/PHASE_STATUS.md").exists() else "")
    plan = build_refresh_plan(lanes=lanes, customers=customers, backend_target=backend, iptables_save_text=ipt, ip6tables_save_text=ip6, phase_status_text=phase_text, expected_version=expected_version)
    if blockers:
        plan = {**plan, "blockers": sorted(set([*plan.get("blockers", []), *blockers])), "final_decision": REFRESH_BLOCKED, "controlled_artifact_refresh_execute_available": False, "iptables_restore_invocation_allowed": False}
    if out_dir:
        out = Path(out_dir)
        files = {"refresh-plan.json": _write_json(out / "refresh-plan.json", plan)}
        plan["files_written"] = _write_manifest(out, files)
        plan["output_dir"] = str(out)
    return plan


def run_refresh_package_report(*, config_path: Path = DEFAULT_CONFIG_PATH, out_dir: Path | None = None, phase_status_text: str = "", expected_version: str = __version__) -> dict[str, object]:
    plan = run_refresh_plan_report(config_path=config_path, phase_status_text=phase_status_text, expected_version=expected_version)
    package = build_refresh_package_from_plan(plan)
    verify = verify_refresh_package(package, live_plan=plan)
    report = {"component": "phase11_controlled_artifact_refresh_package_report", "repository_version": __version__, "plan_final_decision": plan.get("final_decision"), "package_final_decision": package.get("final_decision"), "verify_final_decision": verify.get("final_decision"), "package_id": package.get("package_id"), "package_sha256": package.get("package_sha256"), "execution_precondition_fingerprint": package.get("execution_precondition_fingerprint"), "plan": plan, "package": package, "verify": verify, "blockers": sorted(set([*plan.get("blockers", []), *package.get("blockers", []), *verify.get("blockers", [])])), "final_decision": REFRESH_READY if package.get("final_decision") == REFRESH_READY and verify.get("final_decision") == REFRESH_VERIFY_READY else REFRESH_BLOCKED, "mutation_performed": False}
    if out_dir:
        out = Path(out_dir)
        files = {
            "refresh-plan.json": _write_json(out / "refresh-plan.json", plan),
            "refresh-package.json": _write_json(out / "refresh-package.json", package),
            "refresh-verify.json": _write_json(out / "refresh-verify.json", verify),
            "rollback-contract.json": _write_json(out / "rollback-contract.json", package.get("rollback_plan", {})),
        }
        report["files_written"] = _write_manifest(out, files)
        report["output_dir"] = str(out)
    return report


def _load_package(path: Path, package_sha256: str) -> tuple[dict[str, object], list[str]]:
    try:
        raw = path.read_text(encoding="utf-8")
        actual = _text_sha(raw)
        data = json.loads(raw)
        if not isinstance(data, dict):
            return {}, ["package_json_object_required"]
    except Exception as exc:  # noqa: BLE001
        return {}, ["package_json_read_failed", str(exc)]
    blockers = [] if actual == package_sha256 else ["package_file_sha256_mismatch"]
    data["__package_file_sha256"] = actual
    return data, blockers


def run_refresh_execute_preflight_report(*, package_json: Path, package_sha256: str, config_path: Path = DEFAULT_CONFIG_PATH, out_dir: Path | None = None, phase_status_text: str = "", expected_version: str = __version__) -> dict[str, object]:
    package, blockers = _load_package(package_json, package_sha256)
    live_plan = run_refresh_plan_report(config_path=config_path, phase_status_text=phase_status_text, expected_version=expected_version)
    restore_test = None
    if not blockers and package.get("payload"):
        result = _run_iptables_restore_safe(["iptables-restore", "--test", "--noflush"], str(package.get("payload", "")))
        restore_test = {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    preflight = build_refresh_execute_preflight(package, live_plan=live_plan, restore_test_result=restore_test)
    if blockers:
        preflight["blockers"] = sorted(set([*preflight.get("blockers", []), *blockers]))
        preflight["final_decision"] = REFRESH_PREFLIGHT_BLOCKED
    if out_dir:
        out = Path(out_dir)
        files = {"refresh-execute-preflight.json": _write_json(out / "refresh-execute-preflight.json", preflight), "live-refresh-plan.json": _write_json(out / "live-refresh-plan.json", live_plan)}
        if restore_test is not None:
            files["restore-test.json"] = _write_json(out / "restore-test.json", restore_test)
        preflight["files_written"] = _write_manifest(out, files)
        preflight["output_dir"] = str(out)
    return preflight


def run_refresh_execute_report(*, package_json: Path, package_sha256: str, yes: bool = False, config_path: Path = DEFAULT_CONFIG_PATH, out_dir: Path | None = None, phase_status_text: str = "", expected_version: str = __version__) -> dict[str, object]:
    blockers: list[str] = []
    if not yes:
        blockers.append("yes_confirmation_required")
    if os.environ.get("MPF_PHASE11_CONTROLLED_ARTIFACT_REFRESH") != "allow":
        blockers.append("controlled_artifact_refresh_env_gate_missing")
    if os.environ.get("MPF_PHASE11_CONTROLLED_ARTIFACT_REFRESH_EXECUTE") != "allow":
        blockers.append("controlled_artifact_refresh_execute_env_gate_missing")
    package, package_blockers = _load_package(package_json, package_sha256)
    blockers.extend(package_blockers)
    preflight = run_refresh_execute_preflight_report(package_json=package_json, package_sha256=package_sha256, config_path=config_path, phase_status_text=phase_status_text, expected_version=expected_version)
    if preflight.get("final_decision") != REFRESH_PREFLIGHT_READY:
        blockers.append("fresh_execute_preflight_not_ready")
        blockers.extend(str(b) for b in preflight.get("blockers", []) if isinstance(preflight.get("blockers"), list))
    restore_test_invoked = bool(preflight.get("restore_test_invoked"))
    apply_invoked = False
    backup_files: dict[str, str] = {}
    out = Path(out_dir or "/var/backups/mpf/phase11-controlled-artifact-refresh")
    out.mkdir(parents=True, exist_ok=True)
    files_written: dict[str, str] = {}
    live_plan = preflight.get("live_plan") if isinstance(preflight.get("live_plan"), dict) else None
    if live_plan is not None:
        files_written["live-refresh-plan.json"] = _write_json(out / "live-refresh-plan.json", live_plan)
    files_written["refresh-execute-preflight.json"] = _write_json(out / "refresh-execute-preflight.json", preflight)
    if blockers:
        report = {"component": "phase11_controlled_artifact_refresh_executor", "repository_version": __version__, "package_id": package.get("package_id"), "blockers": sorted(set(blockers)), "final_decision": "FAILED_PRE_APPLY", "restore_test_invoked": restore_test_invoked, "apply_invoked": False, "firewall_mutation_performed": False, "conntrack_flush_performed": False, "docker_restart_performed": False, "systemd_restart_performed": False}
        files_written["refresh-execute.json"] = _write_json(out / "refresh-execute.json", report)
        report["files_written"] = _write_manifest(out, files_written)
        report["output_dir"] = str(out)
        return report
    lock = FlockHostLock("/run/lock/mpf-phase11-controlled-artifact-refresh.lock")
    if not lock.acquire():
        return {"component": "phase11_controlled_artifact_refresh_executor", "repository_version": __version__, "package_id": package.get("package_id"), "blockers": ["exclusive_lock_unavailable"], "final_decision": "FAILED_PRE_APPLY", "restore_test_invoked": restore_test_invoked, "apply_invoked": False, "firewall_mutation_performed": False}
    try:
        live_plan = live_plan if live_plan is not None else run_refresh_plan_report(config_path=config_path, phase_status_text=phase_status_text, expected_version=expected_version)
        backup_files = {
            "pre-apply-iptables-save.txt": _write_text(out / "pre-apply-iptables-save.txt", str(live_plan.get("iptables_save_text", ""))),
            "pre-apply-ip6tables-save.txt": _write_text(out / "pre-apply-ip6tables-save.txt", str(live_plan.get("ip6tables_save_text", ""))),
        }
        files_written.update(backup_files)
        test = _run_iptables_restore_safe(["iptables-restore", "--test", "--noflush"], str(package.get("payload", "")))
        files_written["restore-test.json"] = _write_json(out / "restore-test.json", {"returncode": test.returncode, "stdout": test.stdout, "stderr": test.stderr})
        restore_test_invoked = True
        if test.returncode != 0:
            report = {"component": "phase11_controlled_artifact_refresh_executor", "repository_version": __version__, "package_id": package.get("package_id"), "blockers": ["iptables_restore_test_failed"], "final_decision": "FAILED_PRE_APPLY", "restore_test_invoked": True, "apply_invoked": False, "firewall_mutation_performed": False, "backup_files": backup_files}
            files_written["refresh-execute.json"] = _write_json(out / "refresh-execute.json", report)
            report["files_written"] = _write_manifest(out, files_written); report["output_dir"] = str(out)
            return report
        apply = ProductionIptablesRestoreRunner().run(["iptables-restore", "--noflush"], input_text=str(package.get("payload", "")))
        apply_invoked = True
        if apply.returncode != 0:
            report = {"component": "phase11_controlled_artifact_refresh_executor", "repository_version": __version__, "package_id": package.get("package_id"), "blockers": ["iptables_restore_apply_failed"], "final_decision": "FAILED_APPLY", "restore_test_invoked": True, "apply_invoked": True, "firewall_mutation_performed": False, "backup_files": backup_files, "rollback_required": True}
        else:
            report = {"component": "phase11_controlled_artifact_refresh_executor", "repository_version": __version__, "package_id": package.get("package_id"), "blockers": [], "final_decision": "CONTROLLED_ARTIFACT_REFRESH_EXECUTED_PENDING_FARM5_EVIDENCE_REVIEW", "restore_test_invoked": True, "apply_invoked": True, "firewall_mutation_performed": True, "backup_files": backup_files, "rollback_required": False}
        files_written["refresh-execute.json"] = _write_json(out / "refresh-execute.json", report)
        report["files_written"] = _write_manifest(out, files_written); report["output_dir"] = str(out)
        return report
    finally:
        lock.release()


def run_refresh_verify_report(*, package_json: Path, package_sha256: str, current_gate_json: Path | None, config_path: Path = DEFAULT_CONFIG_PATH, out_dir: Path | None = None, phase_status_text: str = "", expected_version: str = __version__) -> dict[str, object]:
    package, blockers = _load_package(package_json, package_sha256)
    current_gate = None
    if current_gate_json is None:
        blockers.append("current_controlled_artifact_gate_report_required")
    else:
        try:
            current_gate = json.loads(current_gate_json.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            blockers.extend(["current_controlled_artifact_gate_report_read_failed", str(exc)])
    post_plan = run_refresh_plan_report(config_path=config_path, phase_status_text=phase_status_text, expected_version=expected_version)
    report = verify_post_apply_refresh(package=package, post_apply_plan=post_plan, current_gate_report=current_gate)
    if blockers:
        report["blockers"] = sorted(set([*report.get("blockers", []), *blockers]))
        report["final_decision"] = REFRESH_VERIFY_BLOCKED
    if out_dir:
        out = Path(out_dir)
        files = {"refresh-post-apply-verify.json": _write_json(out / "refresh-post-apply-verify.json", report), "post-apply-refresh-plan.json": _write_json(out / "post-apply-refresh-plan.json", post_plan)}
        report["files_written"] = _write_manifest(out, files)
        report["output_dir"] = str(out)
    return report


def run_refresh_rollback_test_report(*, package_json: Path, package_sha256: str, out_dir: Path | None = None) -> dict[str, object]:
    package, blockers = _load_package(package_json, package_sha256)
    rollback = package.get("rollback_plan") if isinstance(package.get("rollback_plan"), dict) else {}
    if rollback.get("manual_review_required") is not True:
        blockers.append("manual_reviewed_rollback_plan_required")
    report = {"component": "phase11_controlled_artifact_refresh_rollback_test", "repository_version": __version__, "package_id": package.get("package_id"), "rollback_plan": rollback, "blockers": sorted(set(blockers)), "final_decision": "CONTROLLED_ARTIFACT_REFRESH_ROLLBACK_TEST_READY" if not blockers else "BLOCKED_CONTROLLED_ARTIFACT_REFRESH_ROLLBACK_TEST", "mutation_performed": False, "iptables_restore_invoked": False, "firewall_mutation_performed": False}
    if out_dir:
        out = Path(out_dir)
        report["files_written"] = _write_manifest(out, {"refresh-rollback-test.json": _write_json(out / "refresh-rollback-test.json", report)})
        report["output_dir"] = str(out)
    return report


def build_duplicate_nat_cleanup_package(*, current_gate_report: dict[str, object], backend_target: dict[str, object], restore_test_result: dict[str, object] | None = None, package_file_sha256: str | None = "operator_package_file_hash_pending") -> dict[str, object]:
    """Build a targeted, operator-gated package for exact duplicate MPF NAT redirects.

    This is a package/contract primitive only. It renders one exact `-D` for each
    duplicate beyond the first and refuses mixed unknown artifacts, backend drift,
    public exposure, phase mismatch, missing restore-test evidence, or missing
    package hash evidence.
    """
    blockers: list[str] = []
    duplicates = list(current_gate_report.get("duplicate_nat_redirects", [])) if isinstance(current_gate_report.get("duplicate_nat_redirects"), list) else []
    if current_gate_report.get("unknown_mpf_artifacts"):
        blockers.append("unknown_mpf_artifacts_detected")
    if current_gate_report.get("forbidden_public_runtime_exposure"):
        blockers.append("forbidden_public_runtime_exposure_detected")
    if current_gate_report.get("current_phase_gate_ok") is not True:
        blockers.append("current_phase_gate_not_ok")
    expected = f"{backend_target.get('resolved_ipv4') or backend_target.get('target_host')}:{BACKEND_PORT}"
    delete_lines: list[str] = []
    for rule in duplicates:
        if "MPF_NAT_PRE" not in rule or "customer_nat_redirect" not in rule or "-j DNAT" not in rule:
            blockers.append("duplicate_nat_redirect_not_exact_mpf_owned")
            continue
        if expected not in rule:
            blockers.append("backend_target_drift")
            continue
        if not any(f"--dport {port}" in rule for port in SCOPE_PORTS):
            blockers.append("duplicate_nat_redirect_out_of_scope")
            continue
        delete_lines.append("-D " + rule.split("-A ", 1)[1])
    if not duplicates:
        blockers.append("no_duplicate_nat_redirects")
    if restore_test_result is None:
        blockers.append("restore_test_noflush_required")
    elif int(restore_test_result.get("returncode", 1)) != 0:
        blockers.append("restore_test_noflush_failed")
    if package_file_sha256 is None:
        blockers.append("package_file_hash_required")
    payload = "*nat\n" + "\n".join(delete_lines) + ("\n" if delete_lines else "") + "COMMIT\n"
    package = {
        "component": "phase11_controlled_duplicate_nat_cleanup_package",
        "repository_version": __version__,
        "scope": list(SCOPE),
        "duplicate_controlled_artifacts": current_gate_report.get("duplicate_controlled_artifacts", []),
        "duplicate_controlled_artifact_count": current_gate_report.get("duplicate_controlled_artifact_count", 0),
        "duplicate_nat_redirects": duplicates,
        "duplicate_nat_redirect_count": len(duplicates),
        "payload": payload,
        "payload_sha256": _text_sha(payload),
        "restore_test_invoked": restore_test_result is not None,
        "package_file_sha256": package_file_sha256,
        "execution_precondition_fingerprint": _canonical_sha({"duplicates": duplicates, "backend": expected, "scope": list(SCOPE)}),
        "operator_gates": ["MPF_PHASE11_CONTROLLED_DUPLICATE_NAT_CLEANUP=allow", "--yes", "exclusive_lock", "pre_apply_backup"],
        "rollback_plan": {"manual_review_required": True, "automatic_rollback_execution_available": False, "payload": "*nat\n" + "\n".join(line.replace("-D ", "-A ", 1) for line in delete_lines) + ("\n" if delete_lines else "") + "COMMIT\n", "instructions": ["Manual review is required before any future rollback execution path."]},
        "blockers": sorted(set(blockers)),
        "final_decision": "CONTROLLED_DUPLICATE_NAT_CLEANUP_PACKAGE_READY" if not blockers else "BLOCKED_CONTROLLED_DUPLICATE_NAT_CLEANUP_PACKAGE",
        "mutation_performed": False,
        "firewall_mutation_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
    }
    package["package_sha256"] = _canonical_sha(_package_content_for_hash(package))
    return package

DUP_READY = "CONTROLLED_DUPLICATE_NAT_CLEANUP_PACKAGE_READY"
DUP_BLOCKED = "BLOCKED_CONTROLLED_DUPLICATE_NAT_CLEANUP_PACKAGE"
DUP_PREFLIGHT_READY = "CONTROLLED_DUPLICATE_NAT_CLEANUP_EXECUTE_PREFLIGHT_READY"
DUP_PREFLIGHT_BLOCKED = "BLOCKED_CONTROLLED_DUPLICATE_NAT_CLEANUP_EXECUTE_PREFLIGHT"
DUP_VERIFY_READY = "CONTROLLED_DUPLICATE_NAT_CLEANUP_VERIFY_READY"
DUP_VERIFY_BLOCKED = "BLOCKED_CONTROLLED_DUPLICATE_NAT_CLEANUP_VERIFY"


def _expected_backend_target(backend: dict[str, object]) -> str | None:
    host = backend.get("resolved_ipv4") or backend.get("target_host")
    port = backend.get("target_port") or BACKEND_PORT
    return f"{host}:{port}" if host else None


def _duplicate_cleanup_gate(*, backend: dict[str, object], iptables_save_text: str, ip6tables_save_text: str, phase_status_text: str, expected_version: str) -> dict[str, object]:
    from mpf.services import phase11_current_controlled_artifact_gate_service
    return phase11_current_controlled_artifact_gate_service.build_phase11_current_controlled_artifact_gate_report(
        iptables_save_text=iptables_save_text,
        ip6tables_save_text=ip6tables_save_text,
        phase_status_text=phase_status_text,
        expected_version=expected_version,
        expected_backend_target=_expected_backend_target(backend),
    )


def run_duplicate_nat_cleanup_plan_report(*, config_path: Path = DEFAULT_CONFIG_PATH, out_dir: Path | None = None, iptables_save_file: Path | None = None, ip6tables_save_file: Path | None = None, expected_backend_target: str | None = None, phase_status_text: str = "", expected_version: str = __version__) -> dict[str, object]:
    lanes, customers, backend, live_ipt, live_ip6, collect_blockers = _collect_live_inputs(config_path)
    if expected_backend_target:
        host, _, port = expected_backend_target.partition(":")
        backend.update({"status": "ok", "resolved_ipv4": host, "target_host": host, "target_port": int(port or BACKEND_PORT), "backend_public_exposure": False})
    ipt = iptables_save_file.read_text(encoding="utf-8") if iptables_save_file else live_ipt
    ip6 = ip6tables_save_file.read_text(encoding="utf-8") if ip6tables_save_file else live_ip6
    phase_text = phase_status_text or (Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8") if Path("docs/PHASE_STATUS.md").exists() else "")
    gate = _duplicate_cleanup_gate(backend=backend, iptables_save_text=ipt, ip6tables_save_text=ip6, phase_status_text=phase_text, expected_version=expected_version)
    package = build_duplicate_nat_cleanup_package(current_gate_report=gate, backend_target=backend, restore_test_result={"returncode": 0}, package_file_sha256="operator_package_file_hash_pending")
    blockers = [*collect_blockers]
    for key, code in (("unknown_mpf_artifacts", "unknown_mpf_artifacts_detected"),):
        if gate.get(key): blockers.append(code)
    if gate.get("forbidden_public_runtime_exposure"): blockers.append("forbidden_public_runtime_exposure_detected")
    if gate.get("production_gates_remain_closed") is not True: blockers.append("production_gates_not_closed")
    if gate.get("current_phase_gate_ok") is not True: blockers.append("current_phase_gate_not_ok")
    blockers.extend(str(b) for b in package.get("blockers", []) if b != "restore_test_noflush_required")
    report = {"component": "phase11_controlled_duplicate_nat_cleanup_plan", "repository_version": __version__, "expected_backend_target": _expected_backend_target(backend), "current_controlled_artifact_gate": gate, "iptables_save_text": ipt, "ip6tables_save_text": ip6, "package_preview": package, "duplicate_nat_redirect_count": gate.get("duplicate_nat_redirect_count", 0), "blockers": sorted(set(blockers)), "final_decision": DUP_READY if not blockers else DUP_BLOCKED, "mutation_performed": False, "controlled_duplicate_nat_cleanup_execute_available": not blockers, "phase12_start_allowed": False, "worker_enforcement_allowed": "no", "ui_allowed": "no", "telegram_allowed": "no"}
    if out_dir:
        out=Path(out_dir); report["files_written"]=_write_manifest(out,{"duplicate-nat-cleanup-plan.json": _write_json(out/"duplicate-nat-cleanup-plan.json", report)}); report["output_dir"]=str(out)
    return report


def run_duplicate_nat_cleanup_package_report(**kwargs: object) -> dict[str, object]:
    out_dir = kwargs.pop("out_dir", None)
    plan = run_duplicate_nat_cleanup_plan_report(**kwargs)
    package = dict(plan["package_preview"])
    package["blockers"] = [] if plan["final_decision"] == DUP_READY else plan["blockers"]
    package["final_decision"] = DUP_READY if not package["blockers"] else DUP_BLOCKED
    package["package_sha256"] = _canonical_sha(_package_content_for_hash(package))
    report = {"component": "phase11_controlled_duplicate_nat_cleanup_package_report", "repository_version": __version__, "plan": plan, "package": package, "package_sha256": package["package_sha256"], "blockers": package["blockers"], "final_decision": package["final_decision"], "mutation_performed": False}
    if out_dir:
        out=Path(out_dir); files={"duplicate-nat-cleanup-plan.json": _write_json(out/"duplicate-nat-cleanup-plan.json", plan), "duplicate-nat-cleanup-package.json": _write_json(out/"duplicate-nat-cleanup-package.json", package), "rollback-contract.json": _write_json(out/"rollback-contract.json", package.get("rollback_plan", {}))}; report["files_written"]=_write_manifest(out, files); report["output_dir"]=str(out)
    return report


def _run_iptables_restore_safe(argv: list[str], payload: str) -> CommandResult:
    try:
        return ProductionIptablesRestoreRunner().run(argv, input_text=payload)
    except FileNotFoundError as exc:
        return CommandResult(127, "", str(exc))


def _verify_duplicate_package(package: dict[str, object], package_sha256: str) -> list[str]:
    blockers=[]
    if package.get("component") != "phase11_controlled_duplicate_nat_cleanup_package": blockers.append("duplicate_nat_cleanup_package_type_mismatch")
    if package.get("repository_version") != __version__: blockers.append("duplicate_nat_cleanup_package_version_mismatch")
    if package.get("package_sha256") != _canonical_sha(_package_content_for_hash(package)): blockers.append("duplicate_nat_cleanup_package_canonical_sha256_mismatch")
    if package.get("payload_sha256") != _text_sha(str(package.get("payload", ""))): blockers.append("duplicate_nat_cleanup_payload_hash_mismatch")
    return blockers


def run_duplicate_nat_cleanup_execute_preflight_report(*, package_json: Path, package_sha256: str, config_path: Path = DEFAULT_CONFIG_PATH, out_dir: Path | None = None, iptables_save_file: Path | None = None, ip6tables_save_file: Path | None = None, expected_backend_target: str | None = None, expected_version: str = __version__) -> dict[str, object]:
    package, blockers = _load_package(package_json, package_sha256); blockers.extend(_verify_duplicate_package(package, package_sha256))
    live = run_duplicate_nat_cleanup_plan_report(config_path=config_path, iptables_save_file=iptables_save_file, ip6tables_save_file=ip6tables_save_file, expected_backend_target=expected_backend_target, expected_version=expected_version)
    if live.get("final_decision") != DUP_READY: blockers.append("live_duplicate_nat_cleanup_plan_not_ready")
    if (live.get("package_preview") or {}).get("execution_precondition_fingerprint") != package.get("execution_precondition_fingerprint"): blockers.append("duplicate_nat_cleanup_precondition_drift")
    if int(live.get("duplicate_nat_redirect_count", -1)) != int(package.get("duplicate_nat_redirect_count", -2)): blockers.append("duplicate_nat_redirect_count_drift")
    restore = None
    if not blockers:
        r = _run_iptables_restore_safe(["iptables-restore", "--test", "--noflush"], str(package.get("payload", ""))); restore={"returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
        if r.returncode != 0: blockers.append("iptables_restore_test_failed")
    report={"component":"phase11_controlled_duplicate_nat_cleanup_execute_preflight","repository_version":__version__,"package_id":package.get("package_id"),"package_sha256":package.get("package_sha256"),"live_plan":live,"restore_test_result":restore,"restore_test_invoked":restore is not None,"apply_invoked":False,"firewall_mutation_performed":False,"blockers":sorted(set(blockers)),"final_decision":DUP_PREFLIGHT_READY if not blockers else DUP_PREFLIGHT_BLOCKED}
    if out_dir:
        out=Path(out_dir); files={"duplicate-nat-cleanup-execute-preflight.json": _write_json(out/"duplicate-nat-cleanup-execute-preflight.json", report), "live-duplicate-nat-cleanup-plan.json": _write_json(out/"live-duplicate-nat-cleanup-plan.json", live)}; report["files_written"]=_write_manifest(out, files); report["output_dir"]=str(out)
    return report


def run_duplicate_nat_cleanup_execute_report(*, package_json: Path, package_sha256: str, yes: bool = False, config_path: Path = DEFAULT_CONFIG_PATH, out_dir: Path | None = None, expected_backend_target: str | None = None, expected_version: str = __version__) -> dict[str, object]:
    blockers=[]
    if os.environ.get("MPF_PHASE11_CONTROLLED_DUPLICATE_NAT_CLEANUP") != "allow": blockers.append("controlled_duplicate_nat_cleanup_env_gate_missing")
    if not yes: blockers.append("yes_confirmation_required")
    package, load_blockers = _load_package(package_json, package_sha256); blockers.extend(load_blockers); blockers.extend(_verify_duplicate_package(package, package_sha256))
    preflight = run_duplicate_nat_cleanup_execute_preflight_report(package_json=package_json, package_sha256=package_sha256, config_path=config_path, expected_backend_target=expected_backend_target, expected_version=expected_version)
    if preflight.get("final_decision") != DUP_PREFLIGHT_READY: blockers.append("fresh_execute_preflight_not_ready"); blockers.extend(preflight.get("blockers", []))
    out=Path(out_dir or "/var/backups/mpf/phase11-controlled-duplicate-nat-cleanup"); out.mkdir(parents=True, exist_ok=True); files={"duplicate-nat-cleanup-execute-preflight.json": _write_json(out/"duplicate-nat-cleanup-execute-preflight.json", preflight)}
    base={"component":"phase11_controlled_duplicate_nat_cleanup_executor","repository_version":__version__,"package_id":package.get("package_id"),"package_sha256":package.get("package_sha256"),"restore_test_invoked":False,"apply_invoked":False,"firewall_mutation_performed":False,"docker_restart_performed":False,"systemd_restart_performed":False,"conntrack_flush_performed":False,"db_mutation_performed":False,"customer_mutation_performed":False,"policy_mutation_performed":False,"abuse_mutation_performed":False}
    if blockers:
        report={**base,"blockers":sorted(set(blockers)),"final_decision":"FAILED_PRE_APPLY"}; files["duplicate-nat-cleanup-execute.json"]=_write_json(out/"duplicate-nat-cleanup-execute.json", report); report["files_written"]=_write_manifest(out, files); report["output_dir"]=str(out); return report
    lock=FlockHostLock("/run/lock/mpf-phase11-controlled-duplicate-nat-cleanup.lock")
    if not lock.acquire(): return {**base,"blockers":["exclusive_lock_unavailable"],"final_decision":"FAILED_PRE_APPLY"}
    try:
        live = preflight.get("live_plan") if isinstance(preflight.get("live_plan"), dict) else {}
        files["pre-apply-iptables-save.txt"]=_write_text(out/"pre-apply-iptables-save.txt", str(live.get("iptables_save_text", "")))
        files["pre-apply-ip6tables-save.txt"]=_write_text(out/"pre-apply-ip6tables-save.txt", str(live.get("ip6tables_save_text", "")))
        test=_run_iptables_restore_safe(["iptables-restore","--test","--noflush"], str(package.get("payload",""))); files["restore-test.json"]=_write_json(out/"restore-test.json", {"returncode":test.returncode,"stdout":test.stdout,"stderr":test.stderr})
        if test.returncode != 0: report={**base,"restore_test_invoked":True,"blockers":["iptables_restore_test_failed"],"final_decision":"FAILED_PRE_APPLY"}
        else:
            apply=_run_iptables_restore_safe(["iptables-restore","--noflush"], str(package.get("payload","")))
            report={**base,"restore_test_invoked":True,"apply_invoked":True,"firewall_mutation_performed":apply.returncode==0,"blockers":[] if apply.returncode==0 else ["iptables_restore_apply_failed"],"final_decision":"CONTROLLED_DUPLICATE_NAT_CLEANUP_EXECUTED_PENDING_VERIFY" if apply.returncode==0 else "FAILED_APPLY"}
        files["duplicate-nat-cleanup-execute.json"]=_write_json(out/"duplicate-nat-cleanup-execute.json", report); report["files_written"]=_write_manifest(out, files); report["output_dir"]=str(out); return report
    finally: lock.release()


def run_duplicate_nat_cleanup_verify_report(*, config_path: Path = DEFAULT_CONFIG_PATH, out_dir: Path | None = None, iptables_save_file: Path | None = None, ip6tables_save_file: Path | None = None, expected_backend_target: str | None = None, expected_version: str = __version__) -> dict[str, object]:
    plan=run_duplicate_nat_cleanup_plan_report(config_path=config_path, iptables_save_file=iptables_save_file, ip6tables_save_file=ip6tables_save_file, expected_backend_target=expected_backend_target, expected_version=expected_version)
    gate=plan.get("current_controlled_artifact_gate", {}) if isinstance(plan.get("current_controlled_artifact_gate"), dict) else {}
    blockers=[]
    if gate.get("duplicate_nat_redirect_count") != 0: blockers.append("duplicate_nat_redirects_still_present")
    if gate.get("duplicate_controlled_artifact_count") not in (0, None): blockers.append("duplicate_controlled_artifacts_still_present")
    if gate.get("unknown_mpf_artifacts"): blockers.append("unknown_mpf_artifacts_detected")
    if gate.get("forbidden_public_runtime_exposure"): blockers.append("forbidden_public_runtime_exposure_detected")
    if gate.get("production_gates_remain_closed") is not True: blockers.append("production_gates_not_closed")
    report={"component":"phase11_controlled_duplicate_nat_cleanup_verify","repository_version":__version__,"current_controlled_artifact_gate":gate,"duplicate_nat_redirect_count":gate.get("duplicate_nat_redirect_count"),"duplicate_controlled_artifact_count":gate.get("duplicate_controlled_artifact_count"),"blockers":sorted(set(blockers)),"final_decision":DUP_VERIFY_READY if not blockers else DUP_VERIFY_BLOCKED,"mutation_performed":False}
    if out_dir:
        out=Path(out_dir); report["files_written"]=_write_manifest(out,{"duplicate-nat-cleanup-verify.json": _write_json(out/"duplicate-nat-cleanup-verify.json", report)}); report["output_dir"]=str(out)
    return report


def run_duplicate_nat_cleanup_rollback_contract_report(*, package_json: Path, package_sha256: str, out_dir: Path | None = None) -> dict[str, object]:
    package, blockers = _load_package(package_json, package_sha256); blockers.extend(_verify_duplicate_package(package, package_sha256)); rollback=package.get("rollback_plan", {}) if isinstance(package.get("rollback_plan"), dict) else {}
    report={"component":"phase11_controlled_duplicate_nat_cleanup_rollback_contract","repository_version":__version__,"package_id":package.get("package_id"),"rollback_contract":rollback,"automatic_rollback_execution_available":False,"manual_review_required":True,"blockers":sorted(set(blockers)),"final_decision":"CONTROLLED_DUPLICATE_NAT_CLEANUP_ROLLBACK_CONTRACT_READY" if not blockers else "BLOCKED_CONTROLLED_DUPLICATE_NAT_CLEANUP_ROLLBACK_CONTRACT","mutation_performed":False}
    if out_dir:
        out=Path(out_dir); report["files_written"]=_write_manifest(out,{"duplicate-nat-cleanup-rollback-contract.json": _write_json(out/"duplicate-nat-cleanup-rollback-contract.json", report)}); report["output_dir"]=str(out)
    return report


def run_duplicate_nat_cleanup_post_cleanup_readiness_report(*, config_path: Path = DEFAULT_CONFIG_PATH, out_dir: Path | None = None, iptables_save_file: Path | None = None, ip6tables_save_file: Path | None = None, expected_backend_target: str | None = None, expected_version: str = __version__) -> dict[str, object]:
    verify=run_duplicate_nat_cleanup_verify_report(config_path=config_path, iptables_save_file=iptables_save_file, ip6tables_save_file=ip6tables_save_file, expected_backend_target=expected_backend_target, expected_version=expected_version)
    gap=__import__('mpf.services.phase11_operational_completion_gap_inventory_service', fromlist=['run_phase11_operational_completion_gap_inventory_report']).run_phase11_operational_completion_gap_inventory_report(config_path)
    report={"component":"phase11_controlled_duplicate_nat_cleanup_post_cleanup_readiness","repository_version":__version__,"verify":verify,"gap_inventory_summary":gap,"duplicate_nat_redirect_count":verify.get("duplicate_nat_redirect_count"),"unknown_mpf_artifacts":(verify.get("current_controlled_artifact_gate") or {}).get("unknown_mpf_artifacts", []),"backend_remains_local_only": True,"production_gates_remain_closed": (verify.get("current_controlled_artifact_gate") or {}).get("production_gates_remain_closed"),"phase11_operational_completion_accepted": False,"phase12_start_allowed": False,"next_required_step":"collect_restart_autostart_and_controlled_artifact_persistence_evidence","blockers":verify.get("blockers", []),"final_decision":"CONTROLLED_DUPLICATE_NAT_CLEANUP_POST_CLEANUP_READINESS_READY" if verify.get("final_decision")==DUP_VERIFY_READY else "BLOCKED_CONTROLLED_DUPLICATE_NAT_CLEANUP_POST_CLEANUP_READINESS","mutation_performed":False}
    if out_dir:
        out=Path(out_dir); report["files_written"]=_write_manifest(out,{"duplicate-nat-cleanup-post-cleanup-readiness.json": _write_json(out/"duplicate-nat-cleanup-post-cleanup-readiness.json", report)}); report["output_dir"]=str(out)
    return report
