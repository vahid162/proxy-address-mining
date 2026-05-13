from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_phase_status_current_state_block_unchanged() -> None:
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


def test_phase_status_has_slice12_sync_evidence_and_slice3_next() -> None:
    text = _read("docs/PHASE_STATUS.md")
    for phrase in [
        "### Phase 6 Apply Slice 1-2 — Documentation/Readiness Boundary Sync",
        "version accepted on farm5: 0.1.83",
        "pytest with venv: 486 passed",
        "sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip",
        "backup: /var/backups/mpf/source-before-zip-sync-20260513T055542Z",
        "Slice 1 and Slice 2 are accepted only as documentation/test-only readiness boundaries",
        "Next planned Phase 6 implementation sub-step is Apply Slice 3 — Controlled No-Customer Apply Harness.",
    ]:
        assert phrase in text
    assert "firewall_apply_allowed: yes" not in text
    assert "production_traffic: enabled" not in text
    assert "abuse_automation_allowed: yes" not in text


def test_slice3_referenced_as_next_planned_across_docs() -> None:
    for path in ["README.md", "AGENTS.md", "docs/AI_CODING_RULES.md", "docs/AI_PHASE_6_TASK.md"]:
        text = _read(path)
        assert "Apply Slice 3 — Controlled No-Customer Apply Harness" in text
        assert "Apply Slice 2 — Restore Point + Lock + DB Apply Record Readiness (planned" not in text


def test_no_authorization_introduced_in_changed_docs() -> None:
    docs = [
        "docs/PHASE_STATUS.md",
        "docs/REMAINING_PHASE_PLAN.md",
        "docs/AI_PHASE_6_TASK.md",
        "README.md",
        "AGENTS.md",
        "docs/AI_CODING_RULES.md",
        "docs/INDEX.md",
    ]
    text = "\n".join(_read(d) for d in docs)
    forbidden = [
        "authorize no-customer apply now",
        "live firewall read is authorized now",
        "live firewall write is authorized now",
        "live firewall apply is authorized now",
        "iptables-save is allowed now",
        "iptables-restore is allowed now",
        "real adapters are allowed now",
        "subprocess firewall calls are allowed now",
        "restore point writes are allowed now",
        "lock acquisition is allowed now",
        "DB apply writes are allowed now",
        "DB apply records are allowed now",
        "migrations are allowed now",
        "customer NAT redirects are allowed now",
        "customer firewall rules are allowed now",
        "production traffic is allowed now",
        "usage automation is allowed now",
        "abuse automation is allowed now",
        "UI is allowed now",
        "Telegram is allowed now",
    ]
    for item in forbidden:
        assert item not in text
    assert "normal -> over_tracking -> over_grace -> hard" in (_read("AGENTS.md") + _read("docs/REMAINING_PHASE_PLAN.md"))
