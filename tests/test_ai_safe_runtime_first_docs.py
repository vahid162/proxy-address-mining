from pathlib import Path


def test_ai_safe_runtime_first_contract_exists() -> None:
    text = Path("docs/AI_SAFE_RUNTIME_FIRST.md").read_text(encoding="utf-8")
    assert "AI-safe Runtime-first" in text
    assert "`docs/PHASE_STATUS.md` remains authoritative" in text
    assert "prefer the shortest safe path from planning/readiness to a real controlled runtime gate" in text
    assert "It is a Phase 11 execution discipline, not a shortcut around safety gates." in text
    assert "limited real customer onboarding after canary acceptance" in text
    assert "production_traffic: controlled_cli_limited" in text
    assert "worker_enforcement_allowed: no" in text
    assert "ui_allowed: no" in text
    assert "telegram_allowed: no" in text


def test_phase11_docs_reference_runtime_first_boundary() -> None:
    phase11 = Path("docs/AI_PHASE_11_TASK.md").read_text(encoding="utf-8")
    gate = Path("docs/PRODUCTION_ACTIVATION_GATE.md").read_text(encoding="utf-8")
    assert "AI-safe Runtime-first" in phase11
    assert "docs/AI_SAFE_RUNTIME_FIRST.md" in phase11
    assert "By final Phase 11 acceptance, the target is controlled real customer sales" in phase11
    assert "docs/AI_SAFE_RUNTIME_FIRST.md" in gate
    assert "Phase 11 Final Operational Target" in gate
    assert "customer_onboarding_allowed: controlled_cli_limited" in gate


def test_runtime_first_does_not_open_current_gates() -> None:
    status = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    assert "current_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness" in status
    assert "production_traffic: none" in status
    assert "firewall_apply_allowed: no" in status
    assert "abuse_automation_allowed: no" in status
    assert "customer_onboarding_allowed: db_only" in status
    assert "ui_allowed: no" in status
    assert "telegram_allowed: no" in status
