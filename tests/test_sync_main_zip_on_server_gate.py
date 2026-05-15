from pathlib import Path


def test_sync_script_forbids_stale_phase6_phase7_hardcodes() -> None:
    text = Path("scripts/sync_main_zip_on_server.sh").read_text(encoding="utf-8")

    forbidden_fragments = [
        "current_accepted_phase: Phase 6 — Firewall Planner accepted on farm5",
        "current_working_phase: Phase 7 — Usage + Policy/Reject Accounting",
        "new PHASE_STATUS does not show accepted Phase 6 Firewall Planner gate",
        "new PHASE_STATUS does not show Phase 7 Usage + Policy/Reject Accounting working phase",
        "mpf phase-status is not aligned with accepted Phase 6 gate",
        "mpf phase-status is not aligned with Phase 7",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in text


def test_sync_script_requires_generic_phase_markers_and_phase8_doc() -> None:
    text = Path("scripts/sync_main_zip_on_server.sh").read_text(encoding="utf-8")

    assert "current_accepted_phase:" in text
    assert "current_working_phase:" in text
    assert "docs/AI_PHASE_8_TASK.md" in text


def test_sync_script_preserves_hard_safety_checks_and_current_gate_verifier_call() -> None:
    text = Path("scripts/sync_main_zip_on_server.sh").read_text(encoding="utf-8")

    required_fragments = [
        "production_traffic: none",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "customer_onboarding_allowed: db_only",
        "proxy_data_plane_allowed: limited_runtime_local_only",
        "ui_allowed: no",
        "telegram_allowed: no",
        "runtime_activation_allowed: false",
        'bash "$APP_DIR/scripts/verify_current_phase_gate.sh"',
    ]

    for fragment in required_fragments:
        assert fragment in text


def test_verify_current_phase_gate_remains_exact_phase7_phase8_validator() -> None:
    text = Path("scripts/verify_current_phase_gate.sh").read_text(encoding="utf-8")

    assert "current_accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5" in text
    assert "current_working_phase: Phase 8 — Abuse 1h Core planning/readiness" in text


def test_sync_phase_gate_regression_note_for_pr117() -> None:
    text = Path("tests/test_sync_main_zip_on_server_gate.py").read_text(encoding="utf-8")

    assert "PR #117" in text
    assert "Phase 7 accepted / Phase 8 planning/readiness" in text
    assert "must not reject" in text
