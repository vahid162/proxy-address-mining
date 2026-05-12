from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_phase6_h_doc_exists() -> None:
    assert Path("docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md").exists()


def test_phase6_h_status_and_abuse_invariant() -> None:
    text = _read("docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md")
    assert "Status: planned, documentation/test-only, non-authorizing" in text
    for phrase in [
        "normal -> over_tracking -> over_grace -> hard",
        "sustained miner-abuse hardens after about 3600 seconds",
        "farms-over alone must not harden",
        "worker-over alone must not harden",
        "all active customers in enabled lanes must be covered",
        "no silent skip is allowed",
    ]:
        assert phrase in text


def test_phase_status_current_state_block_unchanged_and_phase6h_position() -> None:
    text = _read("docs/PHASE_STATUS.md")
    expected = """## Current State

```text
current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
current_working_phase: Phase 6 — Firewall Planner
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
```"""
    assert expected in text
    assert "Next planned documentation/test-only step is Phase 6-H" in text
    accepted_section = text.split("## Accepted Server Results", 1)[1]
    assert "### Phase 6-H" not in accepted_section


def test_index_and_ai_phase6_task_reference_phase6h() -> None:
    index_text = _read("docs/INDEX.md")
    assert "docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md" in index_text
    assert "Defines planned Phase 6-H dedicated apply gate entry criteria / authorization boundary only." in index_text
    task_text = _read("docs/AI_PHASE_6_TASK.md")
    assert "next planned documentation/test-only step is Phase 6-H" in task_text


def test_no_doc_authorizes_live_behaviors_now() -> None:
    docs = [
        "docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md",
        "docs/PHASE_STATUS.md",
        "docs/INDEX.md",
        "docs/AI_PHASE_6_TASK.md",
        "docs/FIREWALL.md",
        "docs/ROADMAP.md",
        "docs/REMAINING_PHASE_PLAN.md",
    ]
    combined = "\n".join(_read(p) for p in docs)
    forbidden = [
        "live apply is authorized now",
        "live firewall read is authorized now",
        "live firewall write is authorized now",
        "iptables-save is allowed now",
        "iptables-restore is allowed now",
        "real iptables adapter is allowed now",
        "DB apply writes are allowed now",
        "locks are allowed now",
        "restore point writes are allowed now",
        "customer NAT redirects are allowed now",
        "customer firewall rules are allowed now",
        "production traffic is allowed now",
        "usage automation is allowed now",
        "abuse automation is allowed now",
        "UI is allowed now",
        "Telegram is allowed now",
    ]
    for phrase in forbidden:
        assert phrase not in combined
