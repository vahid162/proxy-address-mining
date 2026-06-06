from __future__ import annotations
from mpf.services.phase11_controlled_artifact_reapply_core import collect_evidence_bundle


def build_controlled_artifact_reapply_evidence_report(*, plan=None, package=None) -> dict[str, object]:
    return collect_evidence_bundle(plan=plan, package=package)
