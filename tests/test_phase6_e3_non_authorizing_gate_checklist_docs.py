from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _between(text: str, start: str, end: str) -> str:
    i = text.index(start)
    j = text.index(end, i)
    return text[i:j]


def test_phase6_e3_doc_exists_and_status_markers() -> None:
    text = _read("docs/PHASE_6_E3_NON_AUTHORIZING_GATE_CHECKLIST.md")
    assert "Status: planned, isolated/non-production only, non-authorizing." in text


def test_phase6_e3_non_authorizations_and_abuse_invariant() -> None:
    text = _read("docs/PHASE_6_E3_NON_AUTHORIZING_GATE_CHECKLIST.md")
    required = [
        "does not authorize",
        "live firewall read",
        "live firewall write",
        "live firewall apply",
        "live rollback",
        "live verify",
        "iptables-save",
        "iptables-restore",
        "real iptables adapter",
        "DB apply writes",
        "lock acquisition",
        "restore point writes",
        "customer NAT redirects",
        "customer firewall rules",
    ]
    for token in required:
        assert token in text

    assert "normal -> over_tracking -> over_grace -> hard" in text
    assert "sustained miner-abuse hardens after about 3600 seconds" in text
    assert "farms-over alone must not harden" in text
    assert "worker-over alone must not harden" in text
    assert "all active customers in enabled lanes must be covered" in text
    assert "no silent skip is allowed" in text


def test_phase_status_remains_unchanged_and_e3_not_accepted() -> None:
    text = _read("docs/history/PHASE_STATUS_LEGACY_0.1.302.md")
    expected = """## Current State

```text
current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5
current_working_phase: Phase 11 operational completion — Full CLI Production Operations
server_state: farm5 controlled CLI-limited BTC production/customer activation is accepted; Phase 11 operational completion now requires Full CLI Production Operations acceptance before Phase 12 implementation
production_traffic: controlled_cli_limited
firewall_apply_allowed: controlled
abuse_automation_allowed: controlled_operator_gated
customer_onboarding_allowed: controlled_cli_limited
proxy_data_plane_allowed: limited_runtime_local_only
worker_enforcement_allowed: no
ui_allowed: no
telegram_allowed: no
phase12_start_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only
```"""
    assert expected in text
    assert "### Phase 6-E3" in text
    assert "Future dedicated Phase 6 apply gate remains not accepted and not authorized" in text
    assert "controlled live apply gate planning / pre-apply review only" in text


def test_index_includes_e3_doc_in_required_sections() -> None:
    text = _read("docs/history/INDEX_LEGACY_0.1.299.md")
    start_here = _between(text, "## Start Here", "## Core Contracts")
    current_phase = _between(text, "## Current Phase Contracts", "## Reading Order by Task")
    doc_summary = _between(text, "## Documentation Summary", "## Current Roadmap Snapshot")

    e3_doc = "docs/PHASE_6_E3_NON_AUTHORIZING_GATE_CHECKLIST.md"
    assert e3_doc in start_here
    assert e3_doc in current_phase
    assert e3_doc in doc_summary
    assert "- `docs/PHASE_6_E3_NON_AUTHORIZING_GATE_CHECKLIST.md`" not in doc_summary


def test_no_docs_authorize_phase6e3_live_apply_or_mutations() -> None:
    docs = [
        "docs/PHASE_6_E3_NON_AUTHORIZING_GATE_CHECKLIST.md",
        "docs/history/PHASE_STATUS_LEGACY_0.1.302.md",
        "docs/INDEX.md",
        "docs/AI_PHASE_6_TASK.md",
        "docs/FIREWALL.md",
        "docs/REMAINING_PHASE_PLAN.md",
    ]
    all_text = "\n".join(_read(p).lower() for p in docs)
    forbidden = [
        "phase 6-e3 authorizes live apply",
        "phase 6-e3 authorizes iptables-save",
        "phase 6-e3 authorizes iptables-restore",
        "phase 6-e3 authorizes a real iptables adapter",
        "phase 6-e3 authorizes db apply writes",
        "phase 6-e3 authorizes locks",
        "phase 6-e3 authorizes restore point writes",
    ]
    for token in forbidden:
        assert token not in all_text
