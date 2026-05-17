from __future__ import annotations
from pathlib import Path
from mpf.config import MPFConfig
from mpf.services.phase9_diagnostics_bundle_service import build_phase9_diagnostics_bundle_report

def build_phase9_abuse_visibility_report(cfg: MPFConfig, repo_root: Path | None=None) -> dict[str, object]:
    return build_phase9_diagnostics_bundle_report(cfg, repo_root=repo_root)["sections"]["abuse_visibility"]
