from __future__ import annotations
from mpf import __version__
from mpf.services.phase11_controlled_artifact_reapply_core import execute_package


def execute_controlled_artifact_reapply_package(*, package: dict[str, object], package_sha256: str, package_id: str, operator: str, reason: str, execute: bool = False, yes: bool = False, expected_version: str = __version__, **kwargs) -> dict[str, object]:
    return execute_package(package=package, package_sha256=package_sha256, package_id=package_id, operator=operator, reason=reason, execute=execute, yes=yes, expected_version=expected_version, **kwargs)
