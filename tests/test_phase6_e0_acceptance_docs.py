from pathlib import Path


def test_phase6_e0_acceptance_doc_exists_and_contains_required_evidence() -> None:
    p = Path("docs/PHASE_6_E0_ACCEPTANCE_EVIDENCE.md")
    assert p.exists()
    t = p.read_text(encoding="utf-8")
    for needle in [
        "Version accepted: 0.1.61",
        "pytest with venv: 376 passed",
        "verify_current_phase_gate.sh: passed",
        "production_traffic: none",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "fake/no-op harness only",
        "report-only harness service",
        "deterministic plan -> apply -> verify ordering tested",
        "verify-failure rollback-guidance ordering tested",
        "no customer NAT redirects",
        "no customer firewall rules",
        "no MPF/customer firewall refs",
        "no live firewall read",
        "no live firewall write",
        "no live firewall apply",
        "no iptables-save execution",
        "no iptables-restore execution",
        "no subprocess firewall calls",
        "no real iptables adapter",
        "no lock acquisition",
        "no restore point write",
        "no DB apply write",
    ]:
        assert needle in t


def test_phase_status_has_required_current_state_and_e0_e1_wording() -> None:
    t = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    for needle in [
        "current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5",
        "current_working_phase: Phase 6 — Firewall Planner",
        "production_traffic: none",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "customer_onboarding_allowed: db_only",
        "proxy_data_plane_allowed: limited_runtime_local_only",
        "ui_allowed: no",
        "telegram_allowed: no",
        "Phase 6-E0 — Isolated Apply Harness Contracts",
        "Phase 6-E1",
        "isolated/non-production",
        "Live apply remains forbidden",
    ]:
        assert needle in t


def test_index_references_acceptance_doc_in_required_sections() -> None:
    t = Path("docs/INDEX.md").read_text(encoding="utf-8")
    assert "docs/PHASE_6_E0_ACCEPTANCE_EVIDENCE.md" in t
    assert "## Start Here" in t and "## Current Phase Contracts" in t
    assert "## Documentation Summary" in t


def test_remaining_plan_and_safety_wording() -> None:
    t = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "Phase 6-E1 must remain fake/no-op, isolated/non-production, and must not mutate the host production firewall." in t


def test_abuse_invariant_and_no_e1_live_authorization() -> None:
    t = Path("docs/PHASE_6_E0_ACCEPTANCE_EVIDENCE.md").read_text(encoding="utf-8")
    assert "normal -> over_tracking -> over_grace -> hard" in t
    assert "3600 seconds" in t
    assert "farms-over alone must not harden" in t
    assert "worker-over alone must not harden" in t
    assert "all active customers in enabled lanes must be covered" in t
    assert "no silent skip" in t

    for file in [
        "docs/PHASE_STATUS.md",
        "docs/INDEX.md",
        "docs/REMAINING_PHASE_PLAN.md",
        "docs/AI_PHASE_6_TASK.md",
        "docs/FIREWALL.md",
    ]:
        content = Path(file).read_text(encoding="utf-8").lower()
        assert "phase 6-e1 authorizes live apply" not in content
        assert "phase 6-e1 authorizes host production firewall mutation" not in content
        assert "iptables-save is allowed now" not in content
        assert "iptables-restore is allowed now" not in content
        assert "real iptables adapter is allowed now" not in content
