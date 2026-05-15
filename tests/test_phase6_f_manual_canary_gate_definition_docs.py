from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _between(text: str, start: str, end: str) -> str:
    i = text.index(start)
    j = text.index(end, i)
    return text[i:j]


def test_phase6_f_doc_exists() -> None:
    assert Path("docs/PHASE_6_F_MANUAL_CANARY_GATE_DEFINITION.md").exists()


def test_phase_status_current_state_unchanged_and_phase6f_accepted() -> None:
    text = _read("docs/PHASE_STATUS.md")
    expected = """## Current State

```text
current_accepted_phase: Phase 6 — Firewall Planner accepted on farm5
current_working_phase: Phase 7 — Usage + Policy/Reject Accounting
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only
```"""
    assert expected in text
    assert "Phase 6-G is accepted as controlled live apply gate planning / pre-apply review only" in text
    assert "Future dedicated Phase 6 apply gate remains not accepted and not authorized" in text
    assert "Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review" in text
    assert "docs/PHASE_6_F_MANUAL_CANARY_GATE_DEFINITION.md" in text
    assert "Phase 6-F accepted" not in text


def _current_phase_read_list(text: str) -> str:
    anchor = "Read:\n\n"
    section = _between(text, "## Current Phase Contracts", "## Reading Order by Task")
    i = section.index(anchor) + len(anchor)
    j = section.index("\n\nPhase 6-G is accepted as controlled live apply gate planning / pre-apply review only", i)
    return section[i:j]


def test_index_includes_phase6f_in_required_sections() -> None:
    text = _read("docs/INDEX.md")
    start_here = _between(text, "## Start Here", "## Core Contracts")
    current_phase = _between(text, "## Current Phase Contracts", "## Reading Order by Task")
    doc_summary = _between(text, "## Documentation Summary", "## Current Roadmap Snapshot")

    phase6f_doc = "docs/PHASE_6_F_MANUAL_CANARY_GATE_DEFINITION.md"
    assert phase6f_doc in start_here
    assert phase6f_doc in current_phase
    assert phase6f_doc in doc_summary

    read_list = _current_phase_read_list(text)
    assert "13. `docs/PHASE_6_F_MANUAL_CANARY_GATE_DEFINITION.md`" in read_list


def test_no_doc_authorizes_live_apply_or_related_mutations_now() -> None:
    docs = [
        "docs/PHASE_6_F_MANUAL_CANARY_GATE_DEFINITION.md",
        "docs/PHASE_STATUS.md",
        "docs/INDEX.md",
        "docs/AI_PHASE_6_TASK.md",
        "docs/FIREWALL.md",
        "docs/REMAINING_PHASE_PLAN.md",
        "docs/ROADMAP.md",
    ]
    all_text = "\n".join(_read(p).lower() for p in docs)
    forbidden = [
                "phase 6-f authorizes live apply",
        "phase 6-f authorizes iptables-save",
        "phase 6-f authorizes iptables-restore",
        "phase 6-f authorizes real iptables adapter",
        "phase 6-f authorizes db apply writes",
        "phase 6-f authorizes lock acquisition",
        "phase 6-f authorizes restore point writes",
        "phase 6-f authorizes customer nat redirects",
        "phase 6-f authorizes customer firewall rules",
    ]
    for token in forbidden:
        assert token not in all_text


def test_no_stale_wording_phase6e3_as_next_safe_work() -> None:
    docs = ["docs/INDEX.md", "docs/AI_PHASE_6_TASK.md", "docs/PHASE_STATUS.md", "docs/REMAINING_PHASE_PLAN.md"]
    all_text = "\n".join(_read(p).lower() for p in docs)
    assert "next safe work is phase 6-e3" not in all_text
    assert "phase 6-e3 is the current next planned step" not in all_text


def test_abuse_invariant_preserved_in_phase6f_doc() -> None:
    text = _read("docs/PHASE_6_F_MANUAL_CANARY_GATE_DEFINITION.md")
    assert "normal -> over_tracking -> over_grace -> hard" in text
    assert "sustained miner-abuse hardens after about 3600 seconds" in text
    assert "farms-over alone must not harden" in text
    assert "worker-over alone must not harden" in text
    assert "all active customers in enabled lanes must be covered" in text
    assert "no silent skip is allowed" in text
