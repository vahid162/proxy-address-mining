from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs/PRODUCT_ROLES_AND_UX.md"


def read_doc() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_product_roles_and_ux_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_phase5_db_only_and_forbidden_runtime_boundaries_are_documented() -> None:
    text = read_doc()

    assert "Phase 5 is **DB-only**" in text
    assert "no UI service" in text
    assert "no buyer UI service" in text
    assert "no Telegram bot" in text
    assert "no public API binding" in text
    assert "no direct DB write from UI/API/Telegram" in text
    assert "no direct firewall apply" in text
    assert "no shell command execution from Telegram" in text
    assert "no migration" in text
    assert "no model changes" in text
    assert "no production customer traffic" in text


def test_required_roles_are_documented() -> None:
    text = read_doc()

    for role in (
        "buyer/customer",
        "seller/operator",
        "technician/support",
        "Telegram admin/operator",
        "Telegram buyer",
        "local Web UI operator",
        "buyer-safe Web UI user",
    ):
        assert role in text

    for label in (
        "Needs:",
        "Allowed information:",
        "Forbidden information:",
        "Allowed actions:",
        "Request-only actions:",
        "Dangerous actions:",
        "Required confirmation:",
        "Required event/audit:",
        "Future phase placement:",
    ):
        assert label in text


def test_action_safety_classes_and_confirmation_rules_are_documented() -> None:
    text = read_doc()

    for action_class in (
        "read_only",
        "request_only",
        "operator_confirmed",
        "plan_required",
        "dangerous_with_restore_point",
        "forbidden",
    ):
        assert action_class in text

    assert "confirmation modal" in text
    assert "plan preview" in text
    assert "restore point" in text
    assert "event/audit" in text
    assert "buyer request is not execution" in text
    assert "approval is separate from dangerous execution" in text


def test_required_journeys_are_documented() -> None:
    text = read_doc()

    for journey in (
        "customer onboarding",
        "service renewal",
        "first-connect activation",
        "IP whitelist change request",
        "customer cannot connect",
        "customer expired",
        "customer paused",
        "abuse warning / hard state",
        "worker mismatch",
        "high reject rate",
        "backend/pool issue",
        "seller creates service",
        "seller renews service",
        "technician diagnoses issue",
        "buyer opens support request",
        "operator approves action request",
        "UI dangerous action confirmation",
        "Telegram notification and acknowledgement",
    ):
        assert journey in text


def test_surface_contracts_are_documented() -> None:
    text = read_doc()

    assert "### CLI" in text
    assert "### Local Web UI" in text
    assert "### Buyer Web UI" in text
    assert "### Telegram" in text
    assert "### Future API" in text
    assert "127.0.0.1" in text
    assert "Unix socket" in text
    assert "notification-only" in text
    assert "Read-only commands" in text
    assert "Restricted actions" in text
    assert "table-shaped direct mutations" in text


def test_phase_placement_for_future_surfaces_is_documented() -> None:
    text = read_doc()

    assert "Phase 11" in text and "Local Web UI read-only" in text
    assert "Phase 12" in text and "Buyer-safe read-only reporting" in text
    assert "Phase 13" in text and "Local operator UI actions with confirmation" in text
    assert "Phase 14" in text and "Telegram notifications" in text
    assert "Phase 15+" in text and "Worker enforcement" in text


def test_no_forbidden_runtime_artifacts_added() -> None:
    forbidden_paths = {
        "mpf/interfaces/web.py",
        "mpf/interfaces/public_api.py",
        "mpf/interfaces/telegram.py",
        "mpf/services/telegram_service.py",
        "mpf/services/web_ui_service.py",
        "mpf/services/buyer_ui_service.py",
        "systemd/mpf-web.service",
        "systemd/mpf-telegram.service",
    }

    for relative_path in forbidden_paths:
        assert not (ROOT / relative_path).exists(), relative_path
