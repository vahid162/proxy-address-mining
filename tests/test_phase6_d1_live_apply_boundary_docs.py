from pathlib import Path


def _extract_current_phase_read_block(index_text: str) -> str:
    anchor = "## Current Phase Contracts"
    start = index_text.index(anchor)
    read_anchor = "Read:\n\n"
    read_start = index_text.index(read_anchor, start) + len(read_anchor)
    read_end = index_text.index("\n\nPhase 6-C is accepted", read_start)
    return index_text[read_start:read_end].strip()


def test_phase6_d1_doc_exists() -> None:
    assert Path("docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md").exists()


def test_phase6_d1_required_content() -> None:
    text = Path("docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md").read_text(encoding="utf-8").lower()
    required = [
        "documentation/test-only",
        "does not authorize live apply",
        "live firewall reads remain forbidden now",
        "live firewall writes remain forbidden now",
        "iptables-save remains forbidden now",
        "iptables-restore remains forbidden now",
        "customer nat/customer firewall rules remain forbidden now",
        "no-op/fake apply adapter contract",
        "restore point boundary",
        "lock boundary",
        "verify boundary",
        "rollback boundary",
        "future phase 6-e entry criteria",
        "normal -> over_tracking -> over_grace -> hard",
        "sustained miner-abuse hardens after about 3600 seconds",
        "farms-over alone must not harden",
        "worker-over alone must not harden",
        "no silent skip",
    ]
    for item in required:
        assert item in text


def test_ai_phase6_task_explicit_d1_boundary_language() -> None:
    text = Path("docs/AI_PHASE_6_TASK.md").read_text(encoding="utf-8").lower()
    required = [
        "phase 6-d1",
        "docs/phase_6_d1_live_apply_boundary.md",
        "documentation/test-only",
        "does not authorize live apply",
        "live firewall reads remain forbidden now",
        "live firewall writes remain forbidden now",
        "iptables-save remains forbidden now",
        "iptables-restore remains forbidden now",
    ]
    for item in required:
        assert item in text

    stale = [
        "tests required before advancing beyond phase 6-b",
        "phase 6-b is still not a production traffic phase",
    ]
    for item in stale:
        assert item not in text


def test_index_current_phase_contracts_read_list_exact_and_sequential() -> None:
    text = Path("docs/INDEX.md").read_text(encoding="utf-8")
    block = _extract_current_phase_read_block(text)
    expected = """1. `docs/PHASE_STATUS.md`
2. `docs/AI_PHASE_6_TASK.md`
3. `docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md` (non-authorizing, documentation/test-only)
4. `docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md`
5. `docs/PHASE_6_E0_ISOLATED_APPLY_HARNESS.md`
6. `docs/FIREWALL.md`
7. `docs/BACKEND_PORT_POLICY.md`
8. `docs/PHASE_6_C0_APPLY_GATE_READINESS.md`
9. `docs/PHASE_6_C1_APPLY_GATE_RISK_MATRIX.md`
10. `docs/PHASE_6_C_ACCEPTANCE_EVIDENCE.md`
11. `docs/REMAINING_PHASE_PLAN.md`
12. `docs/SAFETY.md`
13. `docs/DATA_MODEL.md`
14. `docs/TAXONOMY.md`
15. `docs/ABUSE.md`
16. `docs/PHASE_5_FINAL_ACCEPTANCE.md`
17. `docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md`
18. `docs/OBSERVABILITY_HASHRATE.md`
19. `docs/INTRANET_INSTALL.md`"""
    assert block == expected


def test_index_has_separate_descriptions_and_no_malformed_numbering() -> None:
    text = Path("docs/INDEX.md").read_text(encoding="utf-8")
    assert "### `docs/AI_PHASE_6_TASK.md`" in text
    assert (
        "Defines the active AI coding boundary for current Phase 6 planner/offline contract work and references the Phase 6-D1 boundary."
        in text
    )
    assert "### `docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md`" in text
    assert (
        "Defines the non-authorizing documentation/test-only live-apply boundary contract for Phase 6-D1."
        in text
    )

    malformed = [
        "5. `docs/TAXONOMY.md`\n7. `docs/FIREWALL.md`",
        "6. `docs/PHASE_6_C0_APPLY_GATE_READINESS.md`\n6. `docs/PHASE_6_C1_APPLY_GATE_RISK_MATRIX.md`",
        "4. `docs/ARCHITECTURE.md`\n6. `docs/SAFETY.md`",
        "12. `docs/TAXONOMY.md`\n10. `docs/ABUSE.md`",
        "12. `docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md`",
    ]
    for item in malformed:
        assert item not in text


def test_phase_status_gate_values_unchanged() -> None:
    text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    required = [
        "production_traffic: none",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "customer_onboarding_allowed: db_only",
        "proxy_data_plane_allowed: limited_runtime_local_only",
        "ui_allowed: no",
        "telegram_allowed: no",
    ]
    for item in required:
        assert item in text


def test_no_docs_authorize_live_apply_or_iptables_now() -> None:
    docs_text = "\n".join(
        path.read_text(encoding="utf-8").lower() for path in Path("docs").glob("*.md")
    )
    forbidden = [
        "phase 6-d1 authorizes live apply",
        "phase 6 d1 authorizes live apply",
        "iptables-save is allowed now",
        "iptables-restore is allowed now",
    ]
    for item in forbidden:
        assert item not in docs_text
