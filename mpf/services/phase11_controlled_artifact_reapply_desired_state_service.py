from __future__ import annotations

from mpf import __version__
from mpf.services.phase11_controlled_artifact_reapply_core import build_controlled_desired_state


def build_controlled_artifact_reapply_desired_state_report(*, lanes, customers, backend_target, expected_version: str = __version__) -> dict[str, object]:
    return build_controlled_desired_state(lanes=lanes, customers=customers, backend_target=backend_target, expected_version=expected_version)
