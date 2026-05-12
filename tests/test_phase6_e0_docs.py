from pathlib import Path


def test_phase6_e0_doc_exists_and_non_authorizing() -> None:
    p = Path("docs/PHASE_6_E0_ISOLATED_APPLY_HARNESS.md")
    assert p.exists()
    t = p.read_text(encoding="utf-8").lower()
    assert "isolated/non-production only" in t
    assert "does **not** authorize" in t
    assert "host production firewall mutation" in t
    assert "live firewall read" in t and "live firewall write" in t
    assert "iptables-save" in t and "iptables-restore" in t


def test_phase6_e0_doc_preserves_abuse_requirements() -> None:
    t = Path("docs/PHASE_6_E0_ISOLATED_APPLY_HARNESS.md").read_text(encoding="utf-8")
    assert "normal -> over_tracking -> over_grace -> hard" in t
    assert "3600 seconds" in t
    assert "farms-over alone must not harden" in t
    assert "worker-over alone must not harden" in t
    assert "all active customers in enabled lanes must be covered" in t
    assert "no silent skip is allowed" in t


def test_phase_status_current_state_unchanged_and_next_step_present() -> None:
    t = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    for needle in [
        "current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5",
        "current_working_phase: Phase 6 — Firewall Planner",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
    ]:
        assert needle in t
    assert "Phase 6-E0 — Isolated Apply Harness Contracts" in t
    assert "Live apply remains forbidden until a dedicated apply gate is explicitly accepted." in t


def test_no_cli_apply_or_rollback_command_added() -> None:
    t = Path("mpf/interfaces/cli.py").read_text(encoding="utf-8")
    assert "def firewall_apply(" not in t
    assert "def firewall_rollback(" not in t


def _extract_current_phase_read_block(text: str) -> str:
    anchor = "## Current Phase Contracts"
    start = text.index(anchor)
    read_anchor = "Read:\n\n"
    read_start = text.index(read_anchor, start) + len(read_anchor)
    end = text.index("\n\nPhase 6-E2 is accepted as isolated/non-production evidence package / boundary planning only.", read_start)
    return text[read_start:end].strip()


def test_index_current_phase_read_block_includes_e0_exact_and_sequential() -> None:
    text = Path("docs/INDEX.md").read_text(encoding="utf-8")
    block = _extract_current_phase_read_block(text)
    expected = """1. `docs/PHASE_STATUS.md`
2. `docs/AI_PHASE_6_TASK.md`
3. `docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md` (non-authorizing, documentation/test-only)
4. `docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md`
5. `docs/PHASE_6_E0_ISOLATED_APPLY_HARNESS.md`
6. `docs/PHASE_6_E0_ACCEPTANCE_EVIDENCE.md`
7. `docs/PHASE_6_E1_ISOLATED_HARNESS_HARDENING.md`
8. `docs/PHASE_6_E1_ACCEPTANCE_EVIDENCE.md`
9. `docs/PHASE_6_E2_ISOLATED_HARNESS_EVIDENCE_PACKAGE.md`
10. `docs/PHASE_6_E2_ACCEPTANCE_EVIDENCE.md`
11. `docs/FIREWALL.md`
12. `docs/BACKEND_PORT_POLICY.md`
13. `docs/PHASE_6_C0_APPLY_GATE_READINESS.md`
14. `docs/PHASE_6_C1_APPLY_GATE_RISK_MATRIX.md`
15. `docs/PHASE_6_C_ACCEPTANCE_EVIDENCE.md`
16. `docs/REMAINING_PHASE_PLAN.md`
17. `docs/SAFETY.md`
18. `docs/DATA_MODEL.md`
19. `docs/TAXONOMY.md`
20. `docs/ABUSE.md`
21. `docs/PHASE_5_FINAL_ACCEPTANCE.md`
22. `docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md`
23. `docs/OBSERVABILITY_HASHRATE.md`
24. `docs/INTRANET_INSTALL.md`"""
    assert block == expected


def test_index_documentation_summary_places_e0_before_roadmap_and_not_after_final_rule() -> None:
    text = Path("docs/INDEX.md").read_text(encoding="utf-8")
    e0 = "### `docs/PHASE_6_E0_ISOLATED_APPLY_HARNESS.md`"
    summary_anchor = "## Documentation Summary"
    roadmap_anchor = "## Current Roadmap Snapshot"
    final_rule_anchor = "## Final Rule"
    assert e0 in text
    assert text.index(summary_anchor) < text.index(e0) < text.index(roadmap_anchor)
    assert text.rfind(e0) < text.index(final_rule_anchor)


def test_index_current_phase_text_mentions_e0_isolated_only() -> None:
    text = Path("docs/INDEX.md").read_text(encoding="utf-8")
    assert "Phase 6-E2 accepted" in text
    assert "Phase 6-E3 — Isolated Harness Evidence Review / Non-Authorizing Gate Checklist, isolated/non-production only" in text


def test_remaining_phase_plan_phase6e_formatting_clean() -> None:
    text = Path("docs/REMAINING_PHASE_PLAN.md").read_text(encoding="utf-8")
    assert "## Phase 6-E — Isolated Apply Harness" in text
    assert "Phase 6-E0 accepted on farm5" in text
    assert "Host production firewall mutation remains forbidden" in text
    assert "forbidden. — Isolated Apply Harness" not in text



def test_ai_phase6_task_e0_status_and_no_stale_d0_wording() -> None:
    text = Path("docs/AI_PHASE_6_TASK.md").read_text(encoding="utf-8")
    required = [
        "Phase 6-E1 isolated harness contract hardening is accepted on farm5",
        "current sub-step: Phase 6-E2 accepted",
        "Phase 6-E2 isolated harness evidence package / boundary planning",
        "non-authorizing",
    ]
    for item in required:
        assert item in text

    stale = [
        "Status: active task for Phase 6-D0 / Phase 6-D",
        "next safe step: Phase 6-D0 / Phase 6-D",
        "Next safe work now is Phase 6-D0 / Phase 6-D",
        "Tests Required for the Post-Phase-6-C / Phase 6-D1 Documentation-Test-Only Boundary",
    ]
    for item in stale:
        assert item not in text


def test_index_no_stale_d0_next_step_wording_and_has_e0_guidance() -> None:
    text = Path("docs/INDEX.md").read_text(encoding="utf-8")
    assert "The next safe step is Phase 6-D0 / Phase 6-D documentation/test-only boundary review" not in text
    assert "Phase 6-D1 is accepted as a documentation/test-only live-apply boundary contract" not in text
    assert "Phase 6-E2 is accepted as isolated/non-production evidence package / boundary planning only" in text
    assert "The next planned implementation step is Phase 6-E3 — Isolated Harness Evidence Review / Non-Authorizing Gate Checklist, isolated/non-production only" in text
