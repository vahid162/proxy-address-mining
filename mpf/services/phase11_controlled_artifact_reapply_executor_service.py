from __future__ import annotations

from pathlib import Path

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.services.phase11_controlled_artifact_reapply_audit_service import ControlledArtifactReapplyAuditRepo
from mpf.services.phase11_controlled_artifact_reapply_core import (
    FileBackupAdapter,
    FlockHostLock,
    ProductionIptablesRestoreRunner,
    execute_package,
)
from mpf.services.phase11_controlled_artifact_reapply_package_service import run_controlled_artifact_reapply_plan


def execute_controlled_artifact_reapply_package(
    *,
    package: dict[str, object],
    package_sha256: str,
    package_id: str,
    operator: str,
    reason: str,
    execute: bool = False,
    yes: bool = False,
    expected_version: str = __version__,
    config_path: Path = DEFAULT_CONFIG_PATH,
    **kwargs,
) -> dict[str, object]:
    cfg = load_config(config_path)
    return execute_package(
        package=package,
        package_sha256=package_sha256,
        package_id=package_id,
        operator=operator,
        reason=reason,
        execute=execute,
        yes=yes,
        expected_version=expected_version,
        live_plan_builder=lambda: run_controlled_artifact_reapply_plan(config_path, expected_version=expected_version),
        runner=ProductionIptablesRestoreRunner(),
        backup=FileBackupAdapter(),
        metadata_repo=ControlledArtifactReapplyAuditRepo(cfg),
        lock=FlockHostLock(),
        **kwargs,
    )
