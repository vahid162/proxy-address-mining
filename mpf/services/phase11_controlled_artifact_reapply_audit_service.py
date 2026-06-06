from __future__ import annotations


class ControlledArtifactReapplyAuditRepoUnavailable:
    """Fail-closed placeholder until PostgreSQL operational metadata writes are implemented."""

    production_ready = False

    def record_intent(self, *args, **kwargs) -> None:
        raise RuntimeError("real_postgresql_operational_metadata_repo_unavailable")

    def record_result(self, *args, **kwargs) -> None:
        raise RuntimeError("real_postgresql_operational_metadata_repo_unavailable")


ControlledArtifactReapplyAuditRepo = ControlledArtifactReapplyAuditRepoUnavailable
