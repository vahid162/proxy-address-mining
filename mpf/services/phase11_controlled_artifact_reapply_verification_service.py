from __future__ import annotations

from pathlib import Path

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH
from mpf.services.phase11_controlled_artifact_reapply_core import verify_package
from mpf.services.phase11_controlled_artifact_reapply_package_service import run_controlled_artifact_reapply_plan


def build_controlled_artifact_reapply_verify_report(
    *,
    package: dict[str, object],
    live_plan: dict[str, object] | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
    expected_version: str = __version__,
) -> dict[str, object]:
    """Verify a package against fresh read-only live evidence, never package-self state."""

    if live_plan is None:
        try:
            live_plan = run_controlled_artifact_reapply_plan(config_path, expected_version=expected_version)
        except Exception as exc:  # noqa: BLE001 - read-only verification must fail closed.
            live_plan = {
                "component": "phase11_controlled_artifact_reapply_plan",
                "final_decision": "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE",
                "blockers": ["live_read_only_plan_failed", str(exc)],
                "mutation_performed": False,
            }
    report = verify_package(package, live_plan=live_plan)
    report["live_plan_source"] = "fresh_read_only_preflight"
    report["live_plan_final_decision"] = live_plan.get("final_decision") if isinstance(live_plan, dict) else None
    report["live_plan_blockers"] = live_plan.get("blockers", []) if isinstance(live_plan, dict) else ["live_plan_invalid"]
    return report
