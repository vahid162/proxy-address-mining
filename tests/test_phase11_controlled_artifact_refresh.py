from __future__ import annotations
from mpf.services.phase11_controlled_artifact_refresh_service import REFRESH_BLOCKED, REFRESH_READY, build_refresh_package_from_plan, build_refresh_plan, verify_refresh_package
from mpf.services.phase11_controlled_artifact_reapply_core import build_controlled_desired_state
from tests.test_phase11_controlled_artifact_reapply import PHASE, customers, lanes, target


def _backend():
    report = target(ip="172.18.0.2")
    report["controlled_artifact_graph_binding_mode"] = "verified_docker_user_forward_post_dnat"
    report["filter_packet_path"] = "docker_user_forward_verified"
    return report


def _stale_snapshot() -> str:
    desired = build_controlled_desired_state(lanes=lanes(), customers=customers(), backend_target=_backend())
    chains = [":" + item.split()[1] + " - [0:0]" for item in desired["artifact_lines"] if item.startswith("filter:-N ")]
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
    ]
    return "*filter\n" + "\n".join(dict.fromkeys(chains + rules)) + "\nCOMMIT\n"


def test_detect_exact_farm5_0_1_269_stale_graph_as_controlled_refresh_required():
    plan = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=_stale_snapshot(), phase_status_text=PHASE)
    assert plan["final_decision"] == REFRESH_READY
    assert plan["artifact_classification"]["status"] == "controlled_refresh_required"


def test_detect_mixed_stale_graph_unrelated_unknown_mpf_artifact_as_blocked():
    snap = _stale_snapshot().replace("COMMIT\n", '-A MPF_EVIL -m comment --comment "mpf:evil:unknown" -j ACCEPT\nCOMMIT\n')
    plan = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=snap, phase_status_text=PHASE)
    assert plan["final_decision"] == REFRESH_BLOCKED
    assert "unknown_mpf_artifacts_detected" in plan["blockers"]


def test_refresh_plan_replaces_stale_hooks_and_contains_corrected_post_dnat_graph():
    payload = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=_stale_snapshot(), phase_status_text=PHASE)["payload"]
    assert '-D DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:backend_guard" -j MPF_GUARD' in payload
    assert '-D MPF_CUSTOMERS -p tcp --dport 60010 -m comment --comment "mpf:canary-btc-001:customer_dispatch" -j MPFC_20001' in payload
    assert "--ctstate DNAT --ctorigdstport 20001" in payload
    assert "--ctstate DNAT --ctorigdstport 20101" in payload
    assert "! --ctstate DNAT" in payload
    assert "MPFC_20001" in payload and "-j MPFO_20001" in payload
    assert "MPFC_20101" in payload and "-j MPFO_20101" in payload


def test_append_only_package_blocked_if_stale_guard_remains_before_new_hooks_and_backend_reject_remains():
    payload = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=_stale_snapshot(), phase_status_text=PHASE)["payload"]
    assert payload.index('-D DOCKER-USER -p tcp --dport 60010') < payload.index('-A DOCKER-USER -p tcp --dport 60010 -m conntrack --ctstate DNAT')
    assert '-A DOCKER-USER -p tcp --dport 60010 -m conntrack ! --ctstate DNAT' in payload
    assert 'mpf:backend_guard:btc:60010" -j REJECT' in payload


def test_refresh_preflight_and_verify_block_on_drift_backend_public_conntrack_ipv6():
    live = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=_stale_snapshot(), phase_status_text=PHASE)
    pkg = build_refresh_package_from_plan(live)
    assert verify_refresh_package(pkg, live_plan=live)["final_decision"] == "CONTROLLED_ARTIFACT_REFRESH_VERIFY_READY"
    drift = dict(live); drift["execution_precondition_fingerprint"] = "drift"
    assert "refresh_execution_precondition_fingerprint_drift" in verify_refresh_package(pkg, live_plan=drift)["blockers"]
    public = _backend(); public["backend_public_exposure"] = True
    assert "backend_public_exposure_detected" in build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=public, iptables_save_text=_stale_snapshot(), phase_status_text=PHASE)["blockers"]
    no_ct = _backend(); no_ct["conntrack_original_destination_supported"] = False
    assert "conntrack_original_destination_match_unsupported" in build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=no_ct, iptables_save_text=_stale_snapshot(), phase_status_text=PHASE)["blockers"]
    ipv6 = build_refresh_plan(lanes=lanes(), customers=customers(), backend_target=_backend(), iptables_save_text=_stale_snapshot(), ip6tables_save_text='*filter\n:MPF6 - [0:0]\nCOMMIT\n', phase_status_text=PHASE)
    assert "ipv6_mpf_or_customer_artifact_detected" in ipv6["blockers"]
