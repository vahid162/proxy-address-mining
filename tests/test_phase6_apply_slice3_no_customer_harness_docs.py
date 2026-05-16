from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_slice3_doc_exists_and_status() -> None:
    p = Path("docs/PHASE_6_APPLY_SLICE_3_CONTROLLED_NO_CUSTOMER_HARNESS.md")
    assert p.exists()
    assert "Status: planned, documentation/test-only, non-authorizing" in p.read_text(encoding="utf-8")


def test_phase_status_current_state_unchanged_and_slice3_not_accepted() -> None:
    phase_status = _read("docs/PHASE_STATUS.md")
    expected = """current_accepted_phase: Phase 8 — Abuse 1h Core accepted on farm5
current_working_phase: Phase 9 — Check / Report / Diagnostics planning/readiness
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no"""
    assert expected in phase_status
    accepted = phase_status.split("## Accepted Server Results", 1)[1].split("## Next Planned Step", 1)[0]
    assert "Phase 6 Apply Slice 3-4 — Documentation Boundary Sync" in accepted
    assert "Apply Slice 3 and Slice 4 are server-synced and accepted only as documentation/test-only boundaries." in phase_status


def test_docs_alignment_and_non_authorization_bundle() -> None:
    docs = [
        "docs/PHASE_6_APPLY_SLICE_3_CONTROLLED_NO_CUSTOMER_HARNESS.md",
        "docs/PHASE_STATUS.md",
        "docs/REMAINING_PHASE_PLAN.md",
        "docs/AI_PHASE_6_TASK.md",
        "docs/INDEX.md",
        "README.md",
        "AGENTS.md",
        "docs/AI_CODING_RULES.md",
    ]
    text = "\n".join(_read(d).lower() for d in docs)
    assert "docs/phase_6_apply_slice_3_controlled_no_customer_harness.md" in _read("docs/INDEX.md").lower()
    assert "future dedicated phase 6 apply gate proposal/review" in _read("docs/AI_PHASE_6_TASK.md").lower()
    required = [
        "does not authorize no-customer apply",
        "live firewall read/write/apply/rollback/verify",
        "iptables-save",
        "iptables-restore",
        "real adapters",
        "subprocess firewall calls",
        "restore point writes",
        "lock acquisition",
        "db apply writes",
        "db apply records",
        "migrations",
        "customer nat",
        "customer firewall rules",
        "production traffic",
        "usage automation",
        "abuse automation",
        "ui",
        "telegram",
    ]
    for token in required:
        assert token in text


def test_abuse_invariant_preserved() -> None:
    t = _read("docs/PHASE_6_APPLY_SLICE_3_CONTROLLED_NO_CUSTOMER_HARNESS.md")
    for line in [
        "normal -> over_tracking -> over_grace -> hard",
        "sustained miner-abuse hardens after about 3600 seconds",
        "farms-over alone must not harden",
        "worker-over alone must not harden",
        "all active customers in enabled lanes must be covered",
        "no silent skip is allowed",
        "abuse automation remains forbidden until Phase 8",
    ]:
        assert line in t
