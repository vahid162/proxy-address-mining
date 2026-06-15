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
    present_mpf = _mpf_present(present)
    known_stale = _known_stale_lines(desired_lines)
    allowed = set(known_stale) | {line for line in desired_lines if _is_chain_decl(line)}
    unknown = sorted({line for line in present_mpf if line not in allowed and line not in set(desired_lines) and not _known_stale_shape(line)})
    stale_present = [line for line in known_stale if line in present and not _is_chain_decl(line)]
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
    missing_required = [line for line in required_exact if line not in present]
    corrected_any_dispatch_present = [line for line in present_mpf if "customer_any_policy_dispatch" in line]
    stale_hook_order_ok = True
    try:
        guard_i = present.index(required_exact[0])
        acct_i = present.index(required_exact[1])
        cust_i = present.index(required_exact[2])
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
    return {"component": "phase11_controlled_artifact_refresh_execute_preflight", "repository_version": __version__, "package_id": package.get("package_id"), "package_sha256": package.get("package_sha256"), "execution_precondition_fingerprint": package.get("execution_precondition_fingerprint"), "restore_test_invoked": restore_test_invoked, "apply_invoked": False, "firewall_mutation_performed": False, "blockers": sorted(set(blockers)), "final_decision": REFRESH_PREFLIGHT_READY if not blockers else REFRESH_PREFLIGHT_BLOCKED}


def verify_post_apply_refresh(*, package: dict[str, object], post_apply_plan: dict[str, object], current_gate_report: dict[str, object] | None = None) -> dict[str, object]:
    blockers: list[str] = []
    text = str(post_apply_plan.get("iptables_save_text", ""))
    desired = post_apply_plan.get("desired_state") if isinstance(post_apply_plan.get("desired_state"), dict) else {}
    corrected = classify_controlled_artifacts(iptables_save_text=text, ip6tables_save_text=str(post_apply_plan.get("ip6tables_save_text", "")), desired_state=desired)
    stale_after = classify_stale_0_1_269_graph(iptables_save_text=text, ip6tables_save_text=str(post_apply_plan.get("ip6tables_save_text", "")), desired_state=desired, backend_target=post_apply_plan.get("backend_target") if isinstance(post_apply_plan.get("backend_target"), dict) else {})
    stale_rules_after = [line for line in stale_after.get("known_stale_artifacts", []) if isinstance(line, str) and _known_stale_shape(line)]
    if stale_rules_after:
        blockers.append("stale_0_1_269_artifacts_still_present")
    if corrected.get("blockers"):
        blockers.append("corrected_graph_controlled_artifact_classification_blocked")
    if corrected.get("status") != "exact_present":
        blockers.append("corrected_graph_not_exact_present")
    required_substrings = ["--ctstate DNAT --ctorigdstport 20001", "--ctstate DNAT --ctorigdstport 20101", "! --ctstate DNAT", "customer_any_policy_dispatch", "mpf:backend_guard:btc:60010"]
    for substring in required_substrings:
        if substring not in text:
            blockers.append(f"post_apply_missing:{substring}")
    if current_gate_report is None:
        blockers.append("current_controlled_artifact_gate_report_required")
    else:
        if not str(current_gate_report.get("final_decision", "")).startswith("PASS") and not str(current_gate_report.get("final_decision", "")).endswith("READY"):
            blockers.append("current_controlled_artifact_gate_not_pass_ready")
        if current_gate_report.get("unknown_mpf_artifacts"):
            blockers.append("current_controlled_artifact_gate_unknown_mpf_artifacts")
        if current_gate_report.get("forbidden_public_runtime_exposure"):
            blockers.append("forbidden_public_runtime_exposure_detected")
    return {"component": "phase11_controlled_artifact_refresh_post_apply_verification", "repository_version": __version__, "package_id": package.get("package_id"), "corrected_artifact_status": corrected.get("status"), "stale_graph_status": NO_STALE if not stale_rules_after else stale_after.get("final_decision"), "blockers": sorted(set(blockers)), "final_decision": REFRESH_VERIFY_READY if not blockers else REFRESH_VERIFY_BLOCKED, "mutation_performed": False}
