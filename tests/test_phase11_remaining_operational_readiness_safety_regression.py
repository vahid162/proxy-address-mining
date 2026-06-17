from __future__ import annotations

import json

from mpf.services.phase11_evidence_contract_readiness_service import (
    build_contract_readiness_report,
)
from mpf.services.phase11_operational_completion_gap_inventory_service import (
    build_phase11_operational_completion_gap_inventory_report,
)


def test_remaining_evidence_contract_blocks_unsafe_gate_flags(tmp_path) -> None:
    (tmp_path / "production_controls_pause_block_expire.json").write_text(
        json.dumps(
            {
                "production_controls_pause_block_expire": "production_controls_pause_block_expire_ready",
                "ready": True,
                "operator": "operator",
                "evidence_collected_at": "2026-06-17T00:00:00Z",
                "scope": "phase11",
                "final_decision": "READY",
                "mutation_performed": False,
                "db_mutation_performed": False,
                "firewall_apply_performed": False,
                "conntrack_flush_performed": False,
                "docker_restart_performed": False,
                "systemd_restart_performed": False,
                "phase12_start_allowed": False,
                "worker_enforcement_allowed": "yes",
            }
        ),
        encoding="utf-8",
    )

    report = build_contract_readiness_report(
        "production_controls_pause_block_expire", tmp_path
    )

    assert report["production_controls_pause_block_expire"] == "missing_or_partial"
    assert "unsafe_gate_flag:worker_enforcement_allowed" in report["blockers"]
    assert report["phase12_start_allowed"] is False
    assert report["mutation_performed"] is False


def test_gap_inventory_never_marks_full_ready_without_restart_proof() -> None:
    report = build_phase11_operational_completion_gap_inventory_report(
        onboarding_readiness={
            "production_onboarding_flow": "production_onboarding_flow_ready"
        },
        usage_report_check_surface={
            "usage_report_check_surface_ready": True,
            "final_decision": "USAGE_REPORT_CHECK_SURFACE_READY",
            "blockers": [],
            "warnings": [],
        },
        abuse_runner_readiness={
            "production_abuse_runner": "production_abuse_runner_ready"
        },
        controls_readiness={
            "production_controls_pause_block_expire": "production_controls_pause_block_expire_ready"
        },
        backup_restore_readiness={"backup_restore_drill": "backup_restore_drill_ready"},
    )

    assert report["restart_autostart_proof"] == "missing_or_partial"
    assert report["full_cli_production_operations"] == "missing_or_partial"
    assert report["phase12_start_allowed"] is False
