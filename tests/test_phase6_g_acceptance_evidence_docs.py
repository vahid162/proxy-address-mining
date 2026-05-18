from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_phase6_g_acceptance_doc_exists() -> None:
    assert Path("docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md").exists()


def test_phase_status_current_state_unchanged() -> None:
    text = _read("docs/PHASE_STATUS.md")
    expected = """## Current State

```text
current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5
current_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness
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


def test_phase_status_has_phase6g_accepted_evidence_and_conservative_next_step() -> None:
    text = _read("docs/PHASE_STATUS.md")
    assert "### Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review" in text
    assert "version accepted on farm5: 0.1.76" in text
    assert "docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md added" in text
    assert "Future dedicated Phase 6 apply gate remains not accepted and not authorized." in text


def test_phase_status_does_not_enable_forbidden_state() -> None:
    text = _read("docs/PHASE_STATUS.md")
    assert "firewall_apply_allowed: yes" not in text
    assert "production_traffic: enabled" not in text
    assert "abuse_automation_allowed: yes" not in text


def test_index_includes_phase6g_acceptance_in_required_sections() -> None:
    text = _read("docs/INDEX.md")
    assert "docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md" in text
    start_here = text[text.index("## Start Here"):text.index("## Core Contracts")]
    current_phase = text[text.index("## Current Phase Contracts"):text.index("## Reading Order by Task")]
    assert "docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md" in start_here
    assert "docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md" in current_phase
    assert "### `docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md`" in text


def test_no_doc_authorizes_forbidden_live_behaviors_now() -> None:
    docs = [
        "docs/PHASE_STATUS.md",
        "docs/INDEX.md",
        "docs/AI_PHASE_6_TASK.md",
        "docs/FIREWALL.md",
        "docs/ROADMAP.md",
        "docs/REMAINING_PHASE_PLAN.md",
        "docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md",
    ]
    combined = "\n".join(_read(p).lower() for p in docs)
    forbidden = [
        "live apply is authorized now",
        "iptables-save is allowed now",
        "iptables-restore is allowed now",
        "real iptables adapter is allowed now",
        "db apply writes are allowed now",
        "locks are allowed now",
        "restore point writes are allowed now",
        "customer nat redirects are allowed now",
        "customer firewall rules are allowed now",
    ]
    for token in forbidden:
        assert token not in combined


def test_abuse_invariant_preserved_in_phase6g_acceptance_doc() -> None:
    text = _read("docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md")
    assert "normal -> over_tracking -> over_grace -> hard" in text
    assert "sustained miner-abuse hardens after about 3600 seconds" in text
    assert "farms-over alone must not harden" in text
    assert "worker-over alone must not harden" in text
    assert "all active customers in enabled lanes must be covered" in text
    assert "no silent skip is allowed" in text
