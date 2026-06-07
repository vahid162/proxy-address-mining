from __future__ import annotations

from mpf import __version__
from mpf.services.phase11_controlled_artifact_reapply_core import ControlledBackendTargetResolver


def build_controlled_backend_target_report(*, expected_version: str = __version__, runner=None, reachability=None, hostname: str | None = None) -> dict[str, object]:
    return ControlledBackendTargetResolver(runner=runner, reachability=reachability, hostname=hostname).resolve(expected_version=expected_version)
