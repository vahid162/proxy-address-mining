from dataclasses import dataclass
from pathlib import Path
import json

from mpf.services.phase11_production_onboarding_flow_readiness_service import (
    build_phase11_production_onboarding_flow_readiness_report,
    READY as ONBOARDING_READY,
)
from mpf.services.phase11_production_abuse_runner_readiness_service import (
    build_phase11_production_abuse_runner_readiness_report,
    READY as ABUSE_READY,
)
from mpf.services.phase11_evidence_contract_readiness_service import (
    build_contract_readiness_report,
)
from mpf.services.phase11_operational_completion_gap_inventory_service import (
    build_phase11_operational_completion_gap_inventory_report,
)


@dataclass(frozen=True)
class Lane:
    name: str
    enabled: bool = True


@dataclass(frozen=True)
class Cust:
    id: int
    customer_key: str
    lane: str
    port: int
    status: str = "active"


LIFE = {
    "production_customer_lifecycle_execution": "controlled_execution_evidence_ready"
}
FW = {
    "production_firewall_apply_verify_rollback": "production_firewall_apply_verify_rollback_ready"
}
CUSTOMERS = [
    Cust(1, "canary-btc-001", "btc", 20001),
    Cust(2, "limited-btc-001", "btc", 20101),
]
LANES = [Lane("btc", True)]
USAGE = {
    "usage_report_check_surface_ready": True,
    "final_decision": "USAGE_REPORT_CHECK_SURFACE_READY",
    "blockers": [],
    "warnings": ["usage_runtime_evidence_not_yet_collected"],
}


def test_onboarding_readiness_ready_and_safe_flags():
    r = build_phase11_production_onboarding_flow_readiness_report(
        lifecycle_readiness=LIFE,
        firewall_readiness=FW,
        lanes=LANES,
        active_customers=CUSTOMERS,
    )
    assert r["production_onboarding_flow"] == ONBOARDING_READY
    assert r["mutation_performed"] is False and r["db_mutation_performed"] is False
    assert (
        r["phase12_start_allowed"] is False and r["worker_enforcement_allowed"] == "no"
    )


def test_onboarding_missing_customer_disabled_lane_unsafe_gate_fail_closed():
    r = build_phase11_production_onboarding_flow_readiness_report(
        lifecycle_readiness=LIFE,
        firewall_readiness=FW,
        lanes=[Lane("btc", False)],
        active_customers=CUSTOMERS[:1],
        gates={"production_traffic": "cli_production"},
    )
    assert r["production_onboarding_flow"] == "missing_or_partial"
    assert "btc_lane_not_enabled" in r["blockers"]
    assert any(b.startswith("unsafe_gate_flag") for b in r["blockers"])


def test_abuse_runner_ready_and_invariant_no_hard_authorization():
    abuse = {
        "status": "OK",
        "blockers": [],
        "states": [
            {"customer_key": "canary-btc-001"},
            {"customer_key": "limited-btc-001"},
        ],
    }
    r = build_phase11_production_abuse_runner_readiness_report(
        active_customers=CUSTOMERS, lanes=LANES, abuse_status=abuse
    )
    assert r["production_abuse_runner"] == ABUSE_READY
    assert r["abuse_invariant"]["farms_over_only_hard_authorized"] is False
    assert r["abuse_invariant"]["worker_over_only_hard_authorized"] is False
    assert r["abuse_invariant"]["hard_unhard_execution_allowed"] is False


def test_abuse_runner_missing_coverage_fails_closed():
    r = build_phase11_production_abuse_runner_readiness_report(
        active_customers=CUSTOMERS,
        lanes=LANES,
        abuse_status={
            "status": "OK",
            "blockers": [],
            "states": [{"customer_key": "canary-btc-001"}],
        },
    )
    assert r["production_abuse_runner"] == "missing_or_partial"
    assert any(b.startswith("abuse_state_coverage_missing") for b in r["blockers"])
    assert r["mutation_performed"] is False


def test_remaining_contracts_missing_and_valid(tmp_path):
    assert (
        build_contract_readiness_report(
            "production_controls_pause_block_expire", tmp_path
        )["production_controls_pause_block_expire"]
        == "missing_or_partial"
    )
    data = {
        "production_controls_pause_block_expire": "production_controls_pause_block_expire_ready",
        "ready": True,
        "pause_preflight": {"ready": True},
        "expire_run_preflight": {"ready": True},
        "block_preflight": {"ready": True},
        "production_controls_pause_block_expire_ready": True,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "production_traffic": "controlled_cli_limited",
        "customer_onboarding_allowed": "controlled_cli_limited",
        "operator": "op",
        "evidence_collected_at": "now",
        "scope": "phase11",
        "final_decision": "READY",
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "phase12_start_allowed": False,
    }
    (tmp_path / "production_controls_pause_block_expire.json").write_text(
        json.dumps(data), encoding="utf-8"
    )
    assert (
        build_contract_readiness_report(
            "production_controls_pause_block_expire", tmp_path
        )["production_controls_pause_block_expire"]
        == "production_controls_pause_block_expire_ready"
    )


def test_gap_inventory_progression_and_usage_warnings_preserved(tmp_path):
    onboarding = build_phase11_production_onboarding_flow_readiness_report(
        lifecycle_readiness=LIFE,
        firewall_readiness=FW,
        lanes=LANES,
        active_customers=CUSTOMERS,
    )
    abuse = build_phase11_production_abuse_runner_readiness_report(
        active_customers=CUSTOMERS,
        lanes=LANES,
        abuse_status={
            "status": "OK",
            "blockers": [],
            "states": [
                {"customer_key": "canary-btc-001"},
                {"customer_key": "limited-btc-001"},
            ],
        },
    )
    r = build_phase11_operational_completion_gap_inventory_report(
        lifecycle_execution_evidence_json=None,
        firewall_completion_evidence_dir=None,
        onboarding_readiness=onboarding,
        usage_report_check_surface=USAGE,
        abuse_runner_readiness=abuse,
        controls_readiness={
            "production_controls_pause_block_expire": "missing_or_partial"
        },
        backup_restore_readiness={"backup_restore_drill": "missing_or_partial"},
    )
    assert (
        r["production_usage_report_check_evidence"]
        == "production_usage_report_check_evidence_ready"
    )
    assert r["production_usage_report_check_warnings"] == [
        "usage_runtime_evidence_not_yet_collected"
    ]
    assert (
        r["next_required_step"] == "production_controls_pause_block_expire"
        or r["next_required_step"]
        == "prepare_live_ready_controlled_artifact_reapply_package"
    )
    assert r["full_cli_production_operations"] == "missing_or_partial"
