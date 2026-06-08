"""Canonical active Phase 11 operational-completion progression state."""
from __future__ import annotations

from mpf.domain.phase11_controlled_filter_packet_path import NEXT_REQUIRED_STEP, FUTURE_READY_RECOMMENDATION

ACTIVE_PROGRESSION: dict[str, object] = {
    "read_only_reapply_foundation_implemented": True,
    "controlled_filter_packet_path_evidence_capability_implemented": True,
    "controlled_filter_packet_path_evidence_ready": False,
    "controlled_filter_packet_path_verified": False,
    "artifact_graph_binding_ready": False,
    "desired_artifact_semantics_complete": False,
    "production_execution_available": False,
    "live_ready_package_available": False,
    "controlled_artifact_reapply_package_evidence_ready": False,
    "restart_autostart_proof": "missing_or_partial",
    "full_cli_production_operations": "missing_or_partial",
    "production_traffic": "controlled_cli_limited",
    "customer_onboarding_allowed": "controlled_cli_limited",
    "firewall_apply_allowed": "controlled",
    "abuse_automation_allowed": "controlled_operator_gated",
    "proxy_data_plane_allowed": "limited_runtime_local_only",
    "worker_enforcement_allowed": "no",
    "ui_allowed": "no",
    "telegram_allowed": "no",
    "phase12_start_allowed": "no",
    "next_required_step": NEXT_REQUIRED_STEP,
    "future_ready_recommendation": FUTURE_READY_RECOMMENDATION,
}


def active_progression() -> dict[str, object]:
    return dict(ACTIVE_PROGRESSION)
