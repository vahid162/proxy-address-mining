"""Non-authorizing helpers for preserved historical phase-status provenance."""
from __future__ import annotations

from pathlib import Path

HISTORICAL_PHASE_STATUS_PATH = Path("docs/history/PHASE_STATUS_LEGACY_0.1.302.md")


def historical_phase_status_path(root: Path) -> Path:
    archive = root / HISTORICAL_PHASE_STATUS_PATH
    if archive.exists():
        return archive
    # Test fixtures for old historical services may provide only a synthetic
    # PHASE_STATUS file; production/current authorization checks must not use
    # this helper.
    return root / "docs/PHASE_STATUS.md"


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
