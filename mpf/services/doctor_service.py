from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mpf.config import load_config, validate_config
from mpf.services.db_service import status as db_status


@dataclass(frozen=True)
class DoctorStatus:
    ok: bool
    config_ok: bool
    db_ok: bool
    message: str
    config_path: Path
    apply_mode: str | None
    traffic_changes: str = "none"
    firewall_mutation: str = "disabled"
    abuse_automation: str = "disabled"


def run(config_path: Path) -> DoctorStatus:
    config_ok, config_message = validate_config(config_path)
    if not config_ok:
        return DoctorStatus(
            ok=False,
            config_ok=False,
            db_ok=False,
            message=config_message,
            config_path=config_path,
            apply_mode=None,
        )

    config = load_config(config_path)
    database = db_status(config)
    return DoctorStatus(
        ok=database.ok,
        config_ok=True,
        db_ok=database.ok,
        message=database.message,
        config_path=config_path,
        apply_mode=config.firewall.apply_mode,
    )
