from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


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
    assert "### Phase 6-E3" not in text
    assert "next planned implementation step is Phase 6-E3" in text
    assert "isolated/non-production only" in text


def test_index_includes_e3_doc_in_required_sections() -> None:
    text = _read("docs/INDEX.md")
    assert "docs/PHASE_6_E3_NON_AUTHORIZING_GATE_CHECKLIST.md" in text
    assert "## Start Here" in text
    assert "## Current Phase Contracts" in text
    assert "## Documentation Summary" in text


def test_no_docs_authorize_phase6e3_live_apply_or_mutations() -> None:
    docs = [
        "docs/PHASE_6_E3_NON_AUTHORIZING_GATE_CHECKLIST.md",
        "docs/PHASE_STATUS.md",
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
