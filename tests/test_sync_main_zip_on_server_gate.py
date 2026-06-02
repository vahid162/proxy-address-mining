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


def test_sync_script_requires_phase11_accepted_phase12_working_gate() -> None:
    text = Path("scripts/sync_main_zip_on_server.sh").read_text(encoding="utf-8")

    required_fragments = [
        "current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5",
        "current_working_phase: Phase 11 operational completion",
        "production_traffic: controlled_cli_limited",
        "firewall_apply_allowed: controlled",
        "abuse_automation_allowed: controlled_operator_gated",
        "customer_onboarding_allowed: controlled_cli_limited",
        "worker_enforcement_allowed: no",
        "proxy_data_plane_allowed: limited_runtime_local_only",
        "ui_allowed: no",
        "telegram_allowed: no",
        "phase12_start_allowed: no",
        "runtime_activation_allowed: false",
        'bash "$APP_DIR/scripts/verify_current_phase_gate.sh"',
    ]

    for fragment in required_fragments:
        assert fragment in text


def test_sync_script_no_longer_requires_pre_acceptance_phase11_closed_gate() -> None:
    text = Path("scripts/sync_main_zip_on_server.sh").read_text(encoding="utf-8")

    stale_fragments = [
        "new PHASE_STATUS does not keep production_traffic=none",
        "new PHASE_STATUS does not keep firewall apply disabled",
        "new PHASE_STATUS does not keep abuse automation disabled",
        "new PHASE_STATUS does not keep customer onboarding DB-only",
        "mpf phase-status does not keep production_traffic=none",
        "mpf phase-status does not keep firewall apply disabled",
        "mpf phase-status does not keep abuse automation disabled",
    ]

    for fragment in stale_fragments:
        assert fragment not in text


def test_verify_current_phase_gate_requires_phase11_operational_completion() -> None:
    text = Path("scripts/verify_current_phase_gate.sh").read_text(encoding="utf-8")

    assert "current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5" in text
    assert "current_working_phase: Phase 11 operational completion" in text
    assert "current Phase 11 accepted / Phase 11 operational completion working safety gate passed" in text
    assert "current Phase 10 accepted / Phase 11 planning safety gate passed" not in text


def test_sync_phase_gate_regression_note_for_pr117() -> None:
    text = Path("tests/test_sync_main_zip_on_server_gate.py").read_text(encoding="utf-8")

    assert "PR #117" in text
    assert "Phase 7 accepted / Phase 8 planning/readiness" in text
    assert "must not reject" in text


def test_verify_current_phase_gate_uses_version_file_for_expected_version() -> None:
    text = Path("scripts/verify_current_phase_gate.sh").read_text(encoding="utf-8")

    assert "--expected-version 0.1.209" not in text
    assert "--expected-version 0.1.210" not in text
    assert 'VERSION_FILE="${REPO_ROOT}/VERSION"' in text
    assert 'EXPECTED_VERSION="$(tr -d "[:space:]" < "$VERSION_FILE")"' in text
    assert 'current-controlled-artifact-gate --expected-version "$EXPECTED_VERSION"' in text
