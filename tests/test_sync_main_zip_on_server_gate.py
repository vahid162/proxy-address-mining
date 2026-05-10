from pathlib import Path


def test_sync_script_requires_phase5_accepted_phase6_working_gate() -> None:
    text = Path("scripts/sync_main_zip_on_server.sh").read_text(encoding="utf-8")

    assert "current_accepted_phase: Phase 4 Runtime Activation" not in text
    assert "current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5" in text
    assert "current_working_phase: Phase 6 — Firewall Planner" in text


def test_sync_script_preserves_required_safety_checks() -> None:
    text = Path("scripts/sync_main_zip_on_server.sh").read_text(encoding="utf-8")

    required_fragments = [
        "production_traffic: none",
        "firewall_apply_allowed: no",
        "abuse_automation_allowed: no",
        "proxy_data_plane_allowed: limited_runtime_local_only",
        "ui_allowed: no",
        "telegram_allowed: no",
        "runtime_activation_allowed: false",
        "--pull never",
        "customer_onboarding_allowed: db_only",
    ]

    for fragment in required_fragments:
        assert fragment in text
