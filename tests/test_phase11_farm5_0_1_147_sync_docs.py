from pathlib import Path


def test_phase11_farm5_0_1_147_evidence_doc_present_and_tokens() -> None:
    t = Path("docs/PHASE_11_FARM5_0_1_147_SYNC_TEST_EVIDENCE.md").read_text(encoding="utf-8")
    assert "0.1.147" in t
    assert "813 passed in 139.03s" in t
    assert "mpf doctor: OK" in t
    assert "database: OK" in t
    assert "proxy config: OK" in t
    assert "proxy status: OK" in t
    assert "proxy doctor: OK" in t
    assert "planning safety gate passed" in t
    assert "execution_allowed: false" in t
    assert "live_canary_performed: false" in t
    assert "production_traffic_enabled: false" in t
    assert "firewall_apply_mode_plan_only: OK" in t
    assert "no MPF/customer IPv4 firewall references detected" in t
    assert "no MPF/customer IPv6 firewall references detected" in t
    assert "no customer NAT redirects are active" in t
    assert "127.0.0.1:2015 local-only" in t
    assert "127.0.0.1:60010 local-only" in t
    assert "does **not** authorize Phase 11D execution" in t
    assert "manual chained command block was run from `/root`" in t
    assert "one customer row in the database, but no non-deleted/active customer" in t


def test_readme_phase_status_and_plan_alignment_for_0_1_147() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    status = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    plan = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")

    assert "Latest recorded farm5 sync evidence is 0.1.153." in readme
    assert "Actual canary execution has not been performed or accepted." in readme

    current_state = status.split("## Current State", 1)[1].split("## Accepted Server Results", 1)[0]
    assert "current_accepted_phase: Phase 10" in current_state
    assert "current_working_phase: Phase 11" in current_state
    assert "production_traffic: none" in current_state

    assert "Phase 11 farm5 0.1.147 Sync/Test Evidence" in status
    assert "Phase 11D execution not authorized." in status

    assert "latest recorded farm5 sync evidence is 0.1.153." in plan
    assert "Next target: sync latest main to farm5, run explicit operator-approved single-canary execution once, and collect evidence; if execution blocks, implement the exact missing primitive reported as `accepted_single_canary_host_apply_primitive`." in plan
    assert "Phase 11D manual canary execution gate package is implemented and farm5 evidence is recorded." in plan
    assert "Current accepted phase is Phase 10." in plan
    assert "Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness." in plan
