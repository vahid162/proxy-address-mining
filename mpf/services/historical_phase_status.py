"""Non-authorizing helpers for preserved historical phase-status provenance."""
from __future__ import annotations

from pathlib import Path

HISTORICAL_PHASE_STATUS_PATH = Path("docs/history/PHASE_STATUS_LEGACY_0.1.302.md")
HISTORICAL_REMAINING_PHASE_PLAN_PATH = Path("docs/history/REMAINING_PHASE_PLAN_LEGACY_0.1.303.md")


def historical_phase_status_path(root: Path) -> Path:
    return root / HISTORICAL_PHASE_STATUS_PATH


def read_historical_phase_status(root: Path) -> str:
    """Read preserved phase-status history for historical reports only.

    This helper is intentionally non-authorizing: current gates and runtime
    permissions must continue to read active docs/PHASE_STATUS.md.
    """
    path = historical_phase_status_path(root)
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def read_historical_remaining_phase_plan(root: Path) -> str:
    """Read preserved remaining-plan history for historical reports only."""
    path = root / HISTORICAL_REMAINING_PHASE_PLAN_PATH
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return text.split("---\n", 1)[1] if "---\n" in text else text
