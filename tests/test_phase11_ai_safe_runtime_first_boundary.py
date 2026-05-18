from pathlib import Path


def test_ai_safe_runtime_first_boundary_exists_and_is_non_authorizing() -> None:
    text = Path("docs/AI_SAFE_RUNTIME_FIRST.md").read_text(encoding="utf-8")

    assert "AI-safe Runtime-first means" in text
    assert "shortest safe path to a real controlled runtime gate" in text
    assert "Runtime-first does not mean bypassing safety" in text
    assert "docs/PHASE_STATUS.md" in text
    assert "does not open production traffic" in text
    assert "canary-first production activation" in text


def test_phase11_runtime_first_final_state_boundaries() -> None:
    text = Path("docs/AI_SAFE_RUNTIME_FIRST.md").read_text(encoding="utf-8")

    assert "production_traffic: controlled_cli_canary or controlled_cli_limited" in text
    assert "firewall_apply_allowed: controlled" in text
    assert "abuse_automation_allowed: controlled" in text
    assert "customer_onboarding_allowed: controlled_cli_canary or controlled_cli_limited" in text
    assert "unrestricted production onboarding: no" in text
    assert "worker_enforcement_allowed: no" in text
    assert "ui_allowed: no" in text
    assert "telegram_allowed: no" in text


def test_phase11_runtime_first_stop_conditions_are_explicit() -> None:
    text = Path("docs/AI_SAFE_RUNTIME_FIRST.md").read_text(encoding="utf-8")

    for phrase in [
        "ad-hoc iptables mutation",
        "customer NAT outside the firewall desired model/planner",
        "firewall apply without backup/lock/verify/rollback path",
        "production traffic without canary evidence",
        "abuse hardening without all-active-customer coverage",
        "hardening on missing/stale evidence",
        "legacy shell scripts as runtime backend",
    ]:
        assert phrase in text
