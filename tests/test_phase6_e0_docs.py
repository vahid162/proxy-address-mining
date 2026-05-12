from pathlib import Path


def test_phase6_e0_doc_exists_and_non_authorizing() -> None:
    p = Path("docs/PHASE_6_E0_ISOLATED_APPLY_HARNESS.md")
    assert p.exists()
    t = p.read_text(encoding="utf-8").lower()
    assert "isolated/non-production only" in t
    assert "does **not** authorize" in t
    assert "host production firewall mutation" in t
    assert "live firewall read" in t and "live firewall write" in t
    assert "iptables-save" in t and "iptables-restore" in t


def test_phase6_e0_doc_preserves_abuse_requirements() -> None:
    t = Path("docs/PHASE_6_E0_ISOLATED_APPLY_HARNESS.md").read_text(encoding="utf-8")
    assert "normal -> over_tracking -> over_grace -> hard" in t
    assert "3600 seconds" in t
    assert "farms-over alone must not harden" in t
    assert "worker-over alone must not harden" in t
    assert "all active customers in enabled lanes must be covered" in t
    assert "no silent skip is allowed" in t


def test_phase_status_current_state_unchanged_and_next_step_present() -> None:
    t = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    for needle in [
        "current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5",
        "current_working_phase: Phase 6 — Firewall Planner",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
    ]:
        assert needle in t
    assert "Phase 6-E0 — Isolated Apply Harness Planning/Contracts, isolated/non-production only" in t
    assert "Live apply remains forbidden until a dedicated apply gate is explicitly accepted." in t


def test_no_cli_apply_or_rollback_command_added() -> None:
    t = Path("mpf/interfaces/cli.py").read_text(encoding="utf-8")
    assert 'def firewall_apply(' not in t
    assert 'def firewall_rollback(' not in t
