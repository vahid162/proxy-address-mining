from __future__ import annotations

from pathlib import Path

from mpf.models import Customer, Lane, Setting


EXPECTED_LIFECYCLE_COLUMNS = {
    "customer_key",
    "activation_mode",
    "service_days",
    "activated_at",
    "first_connected_at",
    "activation_event_id",
    "expired_at",
    "delete_after_expired_days",
    "auto_expire_enabled",
    "auto_delete_enabled",
    "delete_eligible_at",
    "deleted_at",
    "lifecycle_note",
}


def test_phase5_migration_file_exists_and_contains_lifecycle_columns() -> None:
    path = Path("migrations/versions/0002_phase5_customer_lifecycle.py")
    assert path.exists()
    text = path.read_text()
    for column in EXPECTED_LIFECYCLE_COLUMNS:
        assert f'"{column}"' in text


def test_customer_model_exposes_lifecycle_columns() -> None:
    model_columns = {column.name for column in Customer.__table__.columns}
    assert EXPECTED_LIFECYCLE_COLUMNS <= model_columns



def test_setting_model_does_not_expose_customer_lifecycle_columns() -> None:
    setting_columns = {column.name for column in Setting.__table__.columns}
    assert EXPECTED_LIFECYCLE_COLUMNS.isdisjoint(setting_columns)


def test_unrelated_models_do_not_expose_customer_lifecycle_columns() -> None:
    lane_columns = {column.name for column in Lane.__table__.columns}
    assert EXPECTED_LIFECYCLE_COLUMNS.isdisjoint(lane_columns)

def test_patch_does_not_introduce_runtime_modules() -> None:
    forbidden_paths = [
        Path("mpf/services/firewall_service.py"),
        Path("mpf/services/abuse_runner.py"),
        Path("scripts/first_connect_detector.py"),
        Path("scripts/auto_expire_customers.py"),
        Path("scripts/auto_delete_customers.py"),
        Path("docker-compose.runtime.yml"),
    ]
    assert not any(path.exists() for path in forbidden_paths)
