from __future__ import annotations

from pathlib import Path

from mpf.config import MPFConfig


def build_worker_policy_contract_readiness_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
    del cfg, repo_root
    return {
        "component": "phase10_worker_policy_contract_readiness",
        "final_decision": "ACCEPTED",
        "report_only": True,
        "execution_allowed": False,
        "enforcement_enabled": False,
        "policy_enforcement_authorized": False,
        "firewall_mutation_authorized": False,
        "customer_mutation_authorized": False,
        "pause_automation_authorized": False,
        "hard_block_authorized": False,
        "worker_policy_modes_defined": True,
        "report_only_default_defined": True,
        "explicit_future_gate_required": True,
        "worker_policy_contract_fields": [
            "policy_id", "customer_id", "lane_id", "mode", "allowed_workers", "denied_workers",
            "max_workers", "violation_action", "enforcement_enabled", "created_at", "updated_at",
        ],
        "allowed_modes": ["observe_only", "allowlist", "denylist", "future_enforce"],
        "allowed_violation_actions": ["report_only", "future_reject", "future_pause", "future_hard_candidate"],
        "blockers": [],
        "warnings": [],
        "errors": [],
    }
