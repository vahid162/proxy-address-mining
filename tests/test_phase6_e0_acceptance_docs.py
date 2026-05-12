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



def test_phase_status_e0_section_placement_and_no_stale_next_step_wording() -> None:
    t = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert t.index("### Phase 6-E0 — Isolated Apply Harness Contracts") < t.index("## Current Server Warning")
    assert t.index("### Phase 6-E0 — Isolated Apply Harness Contracts") < t.index("## Next Planned Step")
    next_step = t[t.index("## Next Planned Step") :]
    assert "### Phase 6-E0 — Isolated Apply Harness Contracts" not in next_step
    assert "The post-Phase-6-C boundary remains **Phase 6-D0 / Phase 6-D**" not in t
    assert "After Phase 6-D1 acceptance evidence, the next planned implementation step is **Phase 6-E0" not in t
    assert "Phase 6-E2 is accepted as isolated/non-production evidence package / boundary planning only" in next_step
    assert "Phase 6-E3 — Isolated Harness Evidence Review / Non-Authorizing Gate Checklist, isolated/non-production only" in next_step
    assert "Live apply remains forbidden until a dedicated apply gate is explicitly accepted" in next_step


def test_index_single_documentation_summary_and_no_duplicate_after_final_rule() -> None:
    t = Path("docs/INDEX.md").read_text(encoding="utf-8")
    assert t.count("## Documentation Summary") == 1
    summary = t.index("## Documentation Summary")
    roadmap = t.index("## Current Roadmap Snapshot")
    summary_block = t[summary:roadmap]
    assert "docs/PHASE_6_E0_ACCEPTANCE_EVIDENCE.md" in summary_block
    final_rule = t.index("## Final Rule")
    assert "## Documentation Summary" not in t[final_rule:]
    assert "Phase 6-D1 is accepted as a documentation/test-only live-apply boundary contract. The next planned implementation step is Phase 6-E0" not in t
    assert "Phase 6-E2 is accepted as isolated/non-production evidence package / boundary planning only" in t
    assert "Phase 6-E3 — Isolated Harness Evidence Review / Non-Authorizing Gate Checklist, isolated/non-production only" in t


def test_ai_phase6_task_e1_current_next_safe_work_and_no_stale_e0_next_wording() -> None:
    t = Path("docs/AI_PHASE_6_TASK.md").read_text(encoding="utf-8")
    required = [
        "current sub-step: Phase 6-E2 accepted",
        "next planned step: Phase 6-E3 isolated harness evidence review / non-authorizing gate checklist, isolated/non-production only",
        "Next safe work now is Phase 6-E3 isolated harness evidence review / non-authorizing gate checklist, isolated/non-production only",
        "Tests Required for the Phase 6-E2 Isolated Evidence/Boundary Planning",
    ]
    for needle in required:
        assert needle in t
    stale = [
        "current sub-step: Phase 6-D1 accepted",
        "next planned step: Phase 6-E0 isolated apply harness planning/contracts",
        "Next safe work now is Phase 6-E0 isolated apply harness planning/contracts",
        "Tests Required for the Phase 6-E0 Isolated Apply Harness Boundary",
    ]
    for needle in stale:
        assert needle not in t
