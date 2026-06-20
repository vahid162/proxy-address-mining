from pathlib import Path


def _read(rel: str) -> str:
    return Path(rel).read_text(encoding="utf-8")


def test_e1_acceptance_evidence_exists() -> None:
    assert Path("docs/PHASE_6_E1_ACCEPTANCE_EVIDENCE.md").exists()


def test_phase_status_current_state_block_unchanged() -> None:
    t = _read("docs/history/PHASE_STATUS_LEGACY_0.1.302.md")
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
    assert expected in t


def test_phase_status_has_e1_accepted_evidence_and_e2_next_step() -> None:
    t = _read("docs/history/PHASE_STATUS_LEGACY_0.1.302.md")
    assert "### Phase 6-E1 — Isolated Harness Contract Hardening" in t
    assert "version accepted on farm5: 0.1.63" in t
    assert "pytest with venv: 392 passed" in t
    assert "docs/PHASE_6_E1_ACCEPTANCE_EVIDENCE.md added" in t
    assert "Phase 6-G is accepted as controlled live apply gate planning / pre-apply review only, documentation/test-only and non-authorizing" in t


def test_docs_do_not_authorize_live_apply_boundary_breaks() -> None:
    docs = [
        "README.md",
        "AGENTS.md",
        "docs/AI_CODING_RULES.md",
        "docs/history/PHASE_STATUS_LEGACY_0.1.302.md",
        "docs/INDEX.md",
        "docs/AI_PHASE_6_TASK.md",
        "docs/FIREWALL.md",
        "docs/REMAINING_PHASE_PLAN.md",
        "docs/PHASE_6_E1_ACCEPTANCE_EVIDENCE.md",
    ]
    combined = "\n".join(_read(d).lower() for d in docs)
    forbidden = [
        "live apply is authorized now",
        "iptables-save is allowed now",
        "iptables-restore is allowed now",
        "real iptables adapter is allowed now",
        "db apply writes are allowed now",
        "locks are allowed now",
        "restore point writes are allowed now",
    ]
    for phrase in forbidden:
        assert phrase not in combined


def test_abuse_invariant_preserved() -> None:
    combined = "\n".join([_read("docs/ABUSE.md"), _read("docs/PHASE_6_E1_ACCEPTANCE_EVIDENCE.md")]).lower()
    checks = [
        "normal -> over_tracking -> over_grace -> hard",
        "sustained miner-abuse hardens after about",
        "farms-over alone must not harden",
        "worker-over alone must not harden",
        "all active customers in enabled lanes must be covered",
        "no silent skip",
    ]
    for c in checks:
        assert c in combined


def test_stale_phrase_guards_removed() -> None:
    combined = "\n".join([_read("README.md"), _read("docs/INDEX.md"), _read("docs/AI_PHASE_6_TASK.md")])
    assert "Current Phase 6-E0 Accepted State and Next Planned Step" not in combined
    assert "with Phase 6-E1 isolated/non-production next step" not in combined
    assert "Phase 6-E0 is accepted as isolated/non-production apply harness contracts only. The next planned implementation step is Phase 6-E1" not in combined
