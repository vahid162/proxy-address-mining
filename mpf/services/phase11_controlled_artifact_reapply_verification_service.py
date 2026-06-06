from __future__ import annotations
from mpf.services.phase11_controlled_artifact_reapply_core import verify_package


def build_controlled_artifact_reapply_verify_report(*, package: dict[str, object], live_plan: dict[str, object] | None = None) -> dict[str, object]:
    return verify_package(package, live_plan=live_plan)
