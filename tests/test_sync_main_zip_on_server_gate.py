from pathlib import Path


def test_sync_script_calls_current_gate_not_historical_gate() -> None:
    text = Path("scripts/sync_main_zip_on_server.sh").read_text(encoding="utf-8")

    assert 'bash "$APP_DIR/scripts/verify_current_phase_gate.sh"' in text
    assert 'bash "$APP_DIR/scripts/verify_phase4_planning_gate.sh"' not in text
    assert 'RUN CURRENT PHASE SAFETY GATE' in text


def test_current_gate_verifier_contains_phase5_accepted_phase6_working_checks() -> None:
    text = Path("scripts/verify_current_phase_gate.sh").read_text(encoding="utf-8")

    required_fragments = [
        "docs/PHASE_STATUS.md",
        "current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5",
        "current_working_phase: Phase 6 — Firewall Planner",
    ]

    for fragment in required_fragments:
        assert fragment in text


def test_current_gate_verifier_preserves_safety_gates() -> None:
    text = Path("scripts/verify_current_phase_gate.sh").read_text(encoding="utf-8")

    required_fragments = [
        "production_traffic: none",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "customer_onboarding_allowed: db_only",
        "proxy_data_plane_allowed: limited_runtime_local_only",
        "ui_allowed: no",
        "telegram_allowed: no",
        "apply_mode: plan_only",
        "runtime_activation_allowed: false",
    ]

    for fragment in required_fragments:
        assert fragment in text


def test_current_gate_verifier_checks_docker_nat_as_informational_and_preserves_safety() -> None:
    text = Path("scripts/verify_current_phase_gate.sh").read_text(encoding="utf-8")

    assert "DOCKER LOCAL PUBLISH NAT REFERENCES" in text
    assert "Docker-managed local publish DNAT rules" in text
    assert "grep -Eiq '(-j DNAT|--to-destination)'" not in text
    assert "MPF|MPFBTC|MPFC_|MPFO_" in text
    assert "accepted limited runtime listeners are local-only" in text
