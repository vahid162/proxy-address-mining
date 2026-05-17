from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig
from mpf.services.phase10_readiness_service import build_phase10_readiness_report

def build_enforcement_boundary_service_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    report = build_phase10_readiness_report(cfg, repo_root=repo_root)
    return report["enforcement_boundary_readiness"] if False else {"component": "phase10_enforcement_boundary_service", "final_decision": report["final_decision"], "authorization_status": report["authorization_status"], "execution_allowed": report["execution_allowed"], "enforcement_boundary_readiness": report["enforcement_boundary_readiness"], "blockers": report["blockers"], "warnings": report["warnings"], "errors": report["errors"]}
