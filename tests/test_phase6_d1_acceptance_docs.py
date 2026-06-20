from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_phase6_d1_acceptance_evidence_exists_and_contains_required_lines() -> None:
    text = _read("docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md")
    required = [
        "Version accepted: 0.1.59",
        "pytest with venv: 357 passed",
        "verify_current_phase_gate.sh: passed",
        "production_traffic: none",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "no customer NAT redirects",
        "no customer firewall rules",
        "no MPF/customer firewall refs",
        "no live firewall read",
        "no live firewall write",
        "no live firewall apply",
        "no iptables-save execution",
        "no iptables-restore execution",
        "no lock acquisition",
        "no restore point write",
        "no DB apply write",
    ]
    for item in required:
        assert item in text


def test_phase_status_current_state_unchanged_and_phase6_d1_doce0_present() -> None:
    text = _read("docs/PHASE_STATUS.md")
    current_state_required = [
        "current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5",
        "current_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness",
        "production_traffic: none",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "customer_onboarding_allowed: db_only",
        "proxy_data_plane_allowed: limited_runtime_local_only",
        "ui_allowed: no",
        "telegram_allowed: no",
    ]
    for item in current_state_required:
        assert item in text

    for item in [
        "Phase 6-D1 — Live-Apply Boundary Contract",
        "Phase 6-E0",
        "controlled live apply gate planning / pre-apply review",
        "Live apply remains forbidden",
    ]:
        assert item in text


def test_index_remaining_plan_and_non_authorization_constraints() -> None:
    index_text = _read("docs/history/INDEX_LEGACY_0.1.299.md")
    remaining_text = _read("docs/REMAINING_PHASE_PLAN.md")
    acceptance_text = _read("docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md")
    ai_phase6_text = _read("docs/AI_PHASE_6_TASK.md")
    firewall_text = _read("docs/FIREWALL.md")

    assert "docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md" in index_text
    assert "must not mutate the host production firewall" in remaining_text

    for item in [
        "normal -> over_tracking -> over_grace -> hard",
        "sustained miner-abuse hardens after about 3600 seconds",
        "farms-over alone must not harden",
        "worker-over alone must not harden",
        "all active customers in enabled lanes must be covered",
        "no silent skip",
    ]:
        assert item in acceptance_text

    combined = "\n".join([index_text, remaining_text, acceptance_text, ai_phase6_text, firewall_text])
    assert "Phase 6-E0 authorizes live apply" not in combined
    assert "Phase 6-E0 authorizes host production firewall mutation" not in combined
    assert "iptables-save is allowed now" not in combined
    assert "iptables-restore is allowed now" not in combined


def _extract_current_phase_read_block(index_text: str) -> str:
    anchor = "## Current Phase Contracts"
    start = index_text.index(anchor)
    read_anchor = "Read:\n\n"
    read_start = index_text.index(read_anchor, start) + len(read_anchor)
    read_end = index_text.index("\n\nPhase 6-G is accepted as controlled live apply gate planning / pre-apply review only, documentation/test-only and non-authorizing.", read_start)
    return index_text[read_start:read_end].strip()


def test_index_current_phase_contracts_read_block_exact_1_to_18_with_d1_acceptance_doc() -> None:
    text = _read("docs/history/INDEX_LEGACY_0.1.299.md")
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
11. `docs/PHASE_6_E3_NON_AUTHORIZING_GATE_CHECKLIST.md`
12. `docs/PHASE_6_E3_ACCEPTANCE_EVIDENCE.md`
13. `docs/PHASE_6_F_MANUAL_CANARY_GATE_DEFINITION.md`
14. `docs/PHASE_6_F_ACCEPTANCE_EVIDENCE.md`
15. `docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md`
16. `docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md`
17. `docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md`
18. `docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md`
19. `docs/FIREWALL.md`
20. `docs/BACKEND_PORT_POLICY.md`
21. `docs/PHASE_6_C0_APPLY_GATE_READINESS.md`
22. `docs/PHASE_6_C1_APPLY_GATE_RISK_MATRIX.md`
23. `docs/PHASE_6_C_ACCEPTANCE_EVIDENCE.md`
24. `docs/REMAINING_PHASE_PLAN.md`
25. `docs/SAFETY.md`
26. `docs/DATA_MODEL.md`
27. `docs/TAXONOMY.md`
28. `docs/ABUSE.md`
29. `docs/PHASE_5_FINAL_ACCEPTANCE.md`
30. `docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md`
31. `docs/OBSERVABILITY_HASHRATE.md`
32. `docs/INTRANET_INSTALL.md`"""
    assert block == expected


def test_index_documentation_summary_has_d1_acceptance_evidence_entry() -> None:
    text = _read("docs/history/INDEX_LEGACY_0.1.299.md")
    assert "### `docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md`" in text
    assert "accepted farm5 evidence" in text
    assert "does not authorize live apply" in text
