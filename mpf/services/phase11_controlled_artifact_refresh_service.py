"""Controlled Phase 11 stale post-DNAT artifact refresh primitives.

This service is deliberately narrower than the append-only reapply package: it
recognizes only the known farm5 0.1.269 stale controlled graph and renders a
reviewed replacement payload that deletes exact stale MPF-owned rules before
installing the corrected post-DNAT graph.  It does not flush host chains and it
keeps execution operator-gated by package/precondition hashes.
"""
from __future__ import annotations

from typing import Any

from mpf import __version__
from mpf.services.phase11_controlled_artifact_reapply_core import (
    BACKEND_PORT,
    PACKAGE_BLOCKED,
    SCOPE,
    _canonical_sha,
    _execution_fingerprint,
    _firewall_structure_sha,
    _package_content_for_hash,
    _phase_gate_blockers,
    _present_lines,
    _text_sha,
    build_controlled_desired_state,
)

REFRESH_READY = "CONTROLLED_ARTIFACT_REFRESH_PACKAGE_READY"
REFRESH_BLOCKED = "BLOCKED_CONTROLLED_ARTIFACT_REFRESH_PACKAGE"
REFRESH_VERIFY_READY = "CONTROLLED_ARTIFACT_REFRESH_VERIFY_READY"
REFRESH_VERIFY_BLOCKED = "BLOCKED_CONTROLLED_ARTIFACT_REFRESH_VERIFY"
KNOWN_STALE_STATUS = "controlled_refresh_required"
NEXT_REQUIRED_STEP = "run_operator_gated_controlled_artifact_refresh_execute_if_ready"


def _customer_key_for_port(port: int) -> str:
    for item in SCOPE:
        if int(item["public_port"]) == port:
            return str(item["customer_key"])
    return f"unknown-{port}"


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
        matched_customer = False
        for scope in SCOPE:
            port = int(scope["public_port"])
            if f'mpf:{scope["customer_key"]}:' in line:
                stale.append(f"{table}:{_strip_post_dnat(line, port)}")
                matched_customer = True
                break
        if not matched_customer and "mpf:backend_guard:btc:60010" in line:
            stale.append(f"{table}:{_strip_post_dnat(line, BACKEND_PORT)}")
    # nat artifacts were not the stale blocker, but are MPF-owned controlled scope.
    stale.extend(item for item in desired_lines if item.startswith("nat:"))
    return list(dict.fromkeys(stale))


def _mpf_present(present: list[str]) -> list[str]:
    return [item for item in present if any(token in item for token in ("MPF", "mpf:", "customer_"))]


def _validate_refresh_payload(payload: str) -> list[str]:
    blockers: list[str] = []
    if any(token in payload for token in ("*raw", "*mangle", "COMMIT\n*security", "docker", "systemctl")):
        blockers.append("refresh_payload_forbidden_operation_detected")
    for line in payload.splitlines():
        if line.startswith(("-F", "-X", "-P", "-Z")):
            blockers.append("refresh_payload_forbidden_operation_detected")
        if line.startswith("-D ") and "mpf:" not in line and "MPF" not in line:
            blockers.append("refresh_payload_non_mpf_delete_detected")
    if "-A DOCKER-USER -p tcp --dport 60010 -m comment --comment \"mpf:hook:verified_user_forward_post_dnat:backend_guard\" -j MPF_GUARD" in payload:
        blockers.append("refresh_payload_would_leave_stale_guard")
    if "! --ctstate DNAT" not in payload:
        blockers.append("refresh_payload_missing_dnat_negated_guard")
    return sorted(set(blockers))

def build_refresh_plan(*, lanes: list[dict[str, Any]], customers: list[dict[str, Any]], backend_target: dict[str, object], iptables_save_text: str = "", ip6tables_save_text: str = "", phase_status_text: str = "", expected_version: str = __version__) -> dict[str, object]:
    backend = dict(backend_target)
    backend["controlled_artifact_graph_binding_mode"] = "verified_docker_user_forward_post_dnat"
    backend.setdefault("filter_packet_path", "docker_user_forward_verified")
    desired = build_controlled_desired_state(lanes=lanes, customers=customers, backend_target=backend, expected_version=expected_version)
    desired_lines = list(desired.get("artifact_lines", [])) if isinstance(desired.get("artifact_lines"), list) else []
    known_stale = _known_stale_lines(desired_lines)
    present = _present_lines(iptables_save_text)
    present_mpf = _mpf_present(present)
    known_set = set(known_stale) | {line for line in desired_lines if line.startswith("filter:-N ") or line.startswith("nat:-N ")}
    
    def _known_stale_shape(line: str) -> bool:
        text = line.split(":", 1)[1] if ":" in line else line
        return "--dport 60010" in text and (
            any(f'mpf:{scope["customer_key"]}:' in text for scope in SCOPE)
            or "mpf:backend_guard:btc:60010" in text
            or "mpf:hook:verified_user_forward_post_dnat:" in text
        )

    stale_present = [line for line in known_stale if line in present]
    unknown = sorted({line for line in present_mpf if line not in known_set and line not in set(desired_lines) and not _known_stale_shape(line)})
    for line in present_mpf:
        if _known_stale_shape(line) and line not in stale_present:
            stale_present.append(line)
    required_markers = [
        'filter:-A DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:backend_guard" -j MPF_GUARD',
        'filter:-A DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:accounting" -j MPF_ACCT_IN',
        'filter:-A DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:customers" -j MPF_CUSTOMERS',
    ]
    blockers = [*desired.get("blockers", []), *_phase_gate_blockers(phase_status_text)]
    if expected_version != __version__:
        blockers.append("wrong_expected_version")
    if backend.get("status") != "ok":
        blockers.append("backend_target_unresolved")
    if backend.get("backend_public_exposure"):
        blockers.append("backend_public_exposure_detected")
    if backend.get("conntrack_original_destination_supported") is not True:
        blockers.append("conntrack_original_destination_match_unsupported")
    if any(token.lower() in ip6tables_save_text.lower() for token in ("mpf", "customer_")):
        blockers.append("ipv6_mpf_or_customer_artifact_detected")
    if len(present_mpf) != len(set(present_mpf)):
        blockers.append("duplicate_controlled_artifact_detected")
    if unknown:
        blockers.append("unknown_mpf_artifacts_detected")
    if not all(marker in present for marker in required_markers):
        blockers.append("known_stale_0_1_269_graph_not_exact")
    if not stale_present:
        blockers.append("known_stale_0_1_269_graph_not_present")
    replacement_missing = [line for line in desired_lines if line not in present]
    delete_rules = [line for line in stale_present if not line.split(":", 1)[1].startswith("-N ")]
    payload_lines = ["*filter"]
    payload_lines.extend("-D " + line.split(":-A ", 1)[1] for line in delete_rules if line.startswith("filter:-A "))
    payload_lines.extend(line.split(":", 1)[1] for line in replacement_missing if line.startswith("filter:"))
    payload_lines.append("COMMIT")
    nat_adds = [line.split(":", 1)[1] for line in replacement_missing if line.startswith("nat:")]
    if nat_adds:
        payload_lines.extend(["*nat", *nat_adds, "COMMIT"])
    payload = "\n".join(payload_lines) + "\n"
    blockers.extend(_validate_refresh_payload(payload))
    status = KNOWN_STALE_STATUS if stale_present and not unknown and not blockers else "blocked"
    decision = REFRESH_READY if status == KNOWN_STALE_STATUS else REFRESH_BLOCKED
    snapshot_hashes = {"iptables_save_sha256": _text_sha(iptables_save_text), "ip6tables_save_sha256": _text_sha(ip6tables_save_text), "iptables_structure_sha256": _firewall_structure_sha(iptables_save_text), "ip6tables_structure_sha256": _firewall_structure_sha(ip6tables_save_text)}
    plan = {"component": "phase11_controlled_artifact_refresh_plan", "repository_version": __version__, "expected_version": expected_version, "scope": list(SCOPE), "backend_target": backend, "desired_state": desired, "artifact_classification": {"status": status, "known_stale_artifacts": stale_present, "known_stale_artifact_count": len(stale_present), "unknown_mpf_artifacts": unknown, "exact_stale_artifact_detection_hash": _canonical_sha({"known_stale": stale_present})}, "payload": payload, "payload_sha256": _text_sha(payload), "replacement_payload": payload, "replacement_payload_sha256": _text_sha(payload), "snapshot_hashes": snapshot_hashes, "db_customer_policy_snapshot_hash": _canonical_sha({"lanes": lanes, "customers": customers}), "desired_state_hash": desired.get("desired_state_hash"), "artifact_classification_hash": _canonical_sha({"stale": stale_present, "unknown": unknown}), "phase_state_hash": _text_sha(phase_status_text), "blockers": sorted(set(blockers)), "warnings": [], "final_decision": decision, "mutation_performed": False, "firewall_apply_performed": False, "iptables_restore_invocation_allowed": decision == REFRESH_READY, "controlled_artifact_refresh_execute_available": decision == REFRESH_READY, "phase12_start_allowed": False, "worker_enforcement_allowed": "no", "ui_allowed": "no", "telegram_allowed": "no", "next_required_step": NEXT_REQUIRED_STEP}
    plan["execution_precondition_fingerprint"] = _execution_fingerprint(plan)
    return plan


def build_refresh_package_from_plan(plan: dict[str, object]) -> dict[str, object]:
    ready = plan.get("final_decision") == REFRESH_READY
    package = {"component": "phase11_controlled_artifact_refresh_package", "package_id": f"phase11-controlled-artifact-refresh-{__version__}-{str(plan.get('execution_precondition_fingerprint'))[:12]}", "repository_version": __version__, "scope": plan.get("scope"), "backend_target_fingerprint": (plan.get("backend_target") or {}).get("target_fingerprint") if isinstance(plan.get("backend_target"), dict) else None, "iptables_save_sha256": (plan.get("snapshot_hashes") or {}).get("iptables_save_sha256") if isinstance(plan.get("snapshot_hashes"), dict) else None, "ip6tables_save_sha256": (plan.get("snapshot_hashes") or {}).get("ip6tables_save_sha256") if isinstance(plan.get("snapshot_hashes"), dict) else None, "iptables_structure_sha256": (plan.get("snapshot_hashes") or {}).get("iptables_structure_sha256") if isinstance(plan.get("snapshot_hashes"), dict) else None, "ip6tables_structure_sha256": (plan.get("snapshot_hashes") or {}).get("ip6tables_structure_sha256") if isinstance(plan.get("snapshot_hashes"), dict) else None, "execution_precondition_fingerprint": plan.get("execution_precondition_fingerprint"), "exact_stale_artifact_detection_hash": (plan.get("artifact_classification") or {}).get("exact_stale_artifact_detection_hash") if isinstance(plan.get("artifact_classification"), dict) else None, "payload": plan.get("payload", ""), "payload_sha256": plan.get("payload_sha256"), "backup_requirements": {"pre_apply_iptables_save_required": True, "pre_apply_ip6tables_save_required": True}, "lock_requirements": {"exclusive_operator_lock_required": True}, "restore_test_requirements": {"iptables_restore_test_noflush_required": True}, "rollback_plan": {"manual_review_required": True, "rollback_first_allowed": True, "reviewed_rollback_plan_required": True, "instructions": ["Use pre-apply backups for rollback review; do not flush host firewall broadly."]}, "post_apply_verification_contract": {"required": True, "must_find_corrected_post_dnat_graph": True, "must_not_find_stale_backend_guard_before_hooks": True}, "plan": plan, "blockers": [] if ready else ["refresh_plan_not_ready"], "final_decision": REFRESH_READY if ready else plan.get("final_decision", REFRESH_BLOCKED), "mutation_performed": False}
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
        if (live_plan.get("artifact_classification") or {}).get("exact_stale_artifact_detection_hash") != package.get("exact_stale_artifact_detection_hash") if isinstance(live_plan.get("artifact_classification"), dict) else True:
            blockers.append("exact_stale_artifact_detection_hash_drift")
    return {"component": "phase11_controlled_artifact_refresh_verification", "repository_version": __version__, "package_id": package.get("package_id"), "blockers": sorted(set(blockers)), "final_decision": REFRESH_VERIFY_READY if not blockers else REFRESH_VERIFY_BLOCKED, "mutation_performed": False, "phase12_start_allowed": False, "worker_enforcement_allowed": "no", "ui_allowed": "no", "telegram_allowed": "no"}
