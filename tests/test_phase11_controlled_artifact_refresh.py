from __future__ import annotations

from mpf.services.phase11_controlled_artifact_refresh_service import (
    BLOCKED_MIXED_UNKNOWN,
    CONTROLLED_REFRESH_REQUIRED,
    EXACT_STALE,
    NO_STALE,
    REFRESH_BLOCKED,
    REFRESH_READY,
    build_refresh_execute_preflight,
    build_refresh_package_from_plan,
    build_refresh_plan,
    classify_stale_0_1_269_graph,
    verify_post_apply_refresh,
    verify_refresh_package,
)
from mpf.services.phase11_controlled_artifact_reapply_core import build_controlled_desired_state
from tests.test_phase11_controlled_artifact_reapply import PHASE, customers, lanes, target


def _backend(ip: str = "172.18.0.2"):
    report = target(ip=ip)
    report["controlled_artifact_graph_binding_mode"] = "verified_docker_user_forward_post_dnat"
    report["filter_packet_path"] = "docker_user_forward_verified"
    return report


def _desired(backend=None):
    return build_controlled_desired_state(lanes=lanes(), customers=customers(), backend_target=backend or _backend())


def _stale_snapshot(*, backend_ip: str = "172.18.0.2", duplicate: bool = False) -> str:
    chains = [":" + item.split()[1] + " - [0:0]" for item in _desired(_backend(backend_ip))["artifact_lines"] if item.startswith("filter:-N ")]
    rules = [
        '-A DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:backend_guard" -j MPF_GUARD',
        '-A DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:accounting" -j MPF_ACCT_IN',
        '-A DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:customers" -j MPF_CUSTOMERS',
        '-A MPF_GUARD -p tcp --dport 60010 -m comment --comment "mpf:backend_guard:btc:60010" -j REJECT',
        '-A MPF_ACCT_IN -p tcp --dport 60010 -m comment --comment "mpf:canary-btc-001:customer_accounting_in" -j RETURN',
        '-A MPF_ACCT_IN -p tcp --dport 60010 -m comment --comment "mpf:limited-btc-001:customer_accounting_in" -j RETURN',
        '-A MPF_CUSTOMERS -p tcp --dport 60010 -m comment --comment "mpf:canary-btc-001:customer_dispatch" -j MPFC_20001',
        '-A MPF_CUSTOMERS -p tcp --dport 60010 -m comment --comment "mpf:limited-btc-001:customer_dispatch" -j MPFC_20101',
        '-A MPFC_20001 -p tcp --dport 60010 -m comment --comment "mpf:canary-btc-001:customer_accept" -j ACCEPT',
        '-A MPFC_20101 -p tcp --dport 60010 -m comment --comment "mpf:limited-btc-001:customer_accept" -j ACCEPT',
        '-A MPFO_20001 -p tcp --dport 60010 -m comment --comment "mpf:canary-btc-001:customer_over_limit" -j REJECT',
        '-A MPFO_20101 -p tcp --dport 60010 -m comment --comment "mpf:limited-btc-001:customer_over_limit" -j REJECT',
        f'-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination {backend_ip}:60010',
        f'-A MPF_NAT_PRE -p tcp --dport 20101 -m comment --comment "mpf:limited-btc-001:customer_nat_redirect" -j DNAT --to-destination {backend_ip}:60010',
    ]
    if duplicate:
        rules.append(rules[0])
    return "*filter\n" + "\n".join(chains + rules) + "\nCOMMIT\n"


def _corrected_snapshot() -> str:
    desired = _desired()["artifact_lines"]
    filter_lines = [item.split(":", 1)[1] for item in desired if item.startswith("filter:")]
    nat_lines = [item.split(":", 1)[1] for item in desired if item.startswith("nat:")]
    return "*filter\n" + "\n".join(filter_lines) + "\nCOMMIT\n*nat\n" + "\n".join(nat_lines) + "\nCOMMIT\n"


def test_exact_farm5_0_1_269_stale_graph_is_controlled_refresh_required():
    classifier = classify_stale_0_1_269_graph(iptables_save_text=_stale_snapshot(), ip6tables_save_text="", desired_state=_desired(), backend_target=_backend())
    assert classifier["exact_classifier"] == EXACT_STALE
    assert classifier["final_decision"] == CONTROLLED_REFRESH_REQUIRED
    plan = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=_stale_snapshot(), phase_status_text=PHASE)
    assert plan["final_decision"] == REFRESH_READY


def test_unknown_mixed_stale_stale_backend_conntrack_ipv6_and_duplicate_block():
    unknown = _stale_snapshot().replace("COMMIT\n", '-A MPF_EVIL -m comment --comment "mpf:evil:unknown" -j ACCEPT\nCOMMIT\n')
    plan = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=unknown, phase_status_text=PHASE)
    assert plan["stale_graph_classifier"]["final_decision"] == BLOCKED_MIXED_UNKNOWN
    assert plan["final_decision"] == REFRESH_BLOCKED
    stale_target = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=_stale_snapshot(backend_ip="172.18.0.9"), phase_status_text=PHASE)
    assert "stale_backend_target_detected" in stale_target["blockers"]
    no_ct = _backend(); no_ct["conntrack_original_destination_supported"] = False
    assert "conntrack_original_destination_match_unsupported" in build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=no_ct, iptables_save_text=_stale_snapshot(), phase_status_text=PHASE)["blockers"]
    ipv6 = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=_stale_snapshot(), ip6tables_save_text='*filter\n:MPF6 - [0:0]\nCOMMIT\n', phase_status_text=PHASE)
    assert "ipv6_mpf_or_customer_artifact_detected" in ipv6["blockers"]
    duplicate = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=_stale_snapshot(duplicate=True), phase_status_text=PHASE)
    assert "duplicate_controlled_artifact_detected" in duplicate["blockers"]


def test_replacement_payload_deletes_stale_hooks_rules_and_contains_corrected_post_dnat_graph():
    payload = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=_stale_snapshot(), phase_status_text=PHASE)["payload"]
    assert payload.index('-D DOCKER-USER -p tcp --dport 60010') < payload.index('-A DOCKER-USER -p tcp --dport 60010 -m conntrack --ctstate DNAT')
    assert '-D DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:backend_guard" -j MPF_GUARD' in payload
    assert '-D MPF_ACCT_IN -p tcp --dport 60010 -m comment --comment "mpf:canary-btc-001:customer_accounting_in" -j RETURN' in payload
    assert '-D MPF_CUSTOMERS -p tcp --dport 60010 -m comment --comment "mpf:limited-btc-001:customer_dispatch" -j MPFC_20101' in payload
    assert '-D MPFO_20001 -p tcp --dport 60010' in payload
    assert '-D MPFO_20101 -p tcp --dport 60010' in payload
    assert "--ctstate DNAT --ctorigdstport 20001" in payload
    assert "--ctstate DNAT --ctorigdstport 20101" in payload
    assert "! --ctstate DNAT" in payload
    assert "MPFC_20001" in payload and "-j MPFO_20001" in payload
    assert "MPFC_20101" in payload and "-j MPFO_20101" in payload
    assert 'mpf:backend_guard:btc:60010" -j REJECT' in payload
    assert "\n-F" not in payload and "*raw" not in payload and "*mangle" not in payload


def test_preflight_exposes_hashes_and_blocks_drift_backend_change_classifier_change_and_requires_restore_test():
    live = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=_stale_snapshot(), phase_status_text=PHASE)
    pkg = build_refresh_package_from_plan(live)
    assert pkg["package_id"] and pkg["package_sha256"] and pkg["execution_precondition_fingerprint"]
    assert verify_refresh_package(pkg, live_plan=live)["final_decision"] == "CONTROLLED_ARTIFACT_REFRESH_VERIFY_READY"
    no_test = build_refresh_execute_preflight(pkg, live_plan=live)
    assert "iptables_restore_test_required_before_apply" in no_test["blockers"]
    ready = build_refresh_execute_preflight(pkg, live_plan=live, restore_test_result={"returncode": 0})
    assert ready["final_decision"] == "CONTROLLED_ARTIFACT_REFRESH_EXECUTE_PREFLIGHT_READY"
    drift = dict(live); drift["snapshot_hashes"] = {**live["snapshot_hashes"], "iptables_structure_sha256": "drift"}
    assert "iptables_structure_snapshot_drift" in build_refresh_execute_preflight(pkg, live_plan=drift, restore_test_result={"returncode": 0})["blockers"]
    backend_drift = dict(live); backend_drift["backend_target"] = {**live["backend_target"], "target_fingerprint": "changed"}
    assert "backend_target_fingerprint_drift" in build_refresh_execute_preflight(pkg, live_plan=backend_drift, restore_test_result={"returncode": 0})["blockers"]
    partial = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=_corrected_snapshot(), phase_status_text=PHASE)
    assert "stale_graph_classifier_no_longer_matches_expected_pre_state" in build_refresh_execute_preflight(pkg, live_plan=partial, restore_test_result={"returncode": 0})["blockers"]


def test_post_apply_verifier_passes_only_when_corrected_graph_present_and_stale_gone():
    pre = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=_stale_snapshot(), phase_status_text=PHASE)
    pkg = build_refresh_package_from_plan(pre)
    corrected = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=_corrected_snapshot(), phase_status_text=PHASE)
    gate = {"final_decision": "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS", "unknown_mpf_artifacts": [], "forbidden_public_runtime_exposure": False}
    report = verify_post_apply_refresh(package=pkg, post_apply_plan=corrected, current_gate_report=gate)
    assert report["final_decision"] == "CONTROLLED_ARTIFACT_REFRESH_VERIFY_READY"
    stale_report = verify_post_apply_refresh(package=pkg, post_apply_plan=pre, current_gate_report=gate)
    assert "stale_0_1_269_artifacts_still_present" in stale_report["blockers"]
    assert classify_stale_0_1_269_graph(iptables_save_text=_corrected_snapshot(), ip6tables_save_text="", desired_state=_desired(), backend_target=_backend())["final_decision"] == NO_STALE


def test_live_ready_refresh_mode_bypasses_binding_only_for_exact_stale_graph(monkeypatch, tmp_path):
    from mpf.services import phase11_live_ready_reapply_package_service as live

    stale = _stale_snapshot()
    monkeypatch.setattr(live, "build_verified_filter_hook_binding_report", lambda _dir: {"final_decision": "BLOCKED_VERIFIED_FILTER_HOOK_BINDING", "backend_ip": "172.18.0.2", "blockers": ["packet_path_final_decision_not_ready", "unknown_mpf_artifacts_present"]})
    report = live.build_live_ready_reapply_package_report(packet_path_evidence_dir=tmp_path, lanes=lanes(), customers=customers(), iptables_save_text=stale, phase_status_text=PHASE, controlled_refresh_mode=True)
    assert report["final_decision"] == "READY_LIVE_READY_CONTROLLED_ARTIFACT_REFRESH_PACKAGE"
    assert report["binding_bypassed_for_exact_stale_refresh"] is True
    mixed = stale.replace("COMMIT\n", '-A MPF_EVIL -m comment --comment "mpf:evil:unknown" -j ACCEPT\nCOMMIT\n')
    blocked = live.build_live_ready_reapply_package_report(packet_path_evidence_dir=tmp_path, lanes=lanes(), customers=customers(), iptables_save_text=mixed, phase_status_text=PHASE, controlled_refresh_mode=True)
    assert blocked["final_decision"] == live.BLOCKED
    assert "unknown_mpf_artifacts_detected" in blocked["blockers"]
