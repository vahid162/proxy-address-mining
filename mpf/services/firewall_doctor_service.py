from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from mpf.domain.firewall import FirewallPlanResult

_CRITICAL_CODES = {
    "backend_exposure",
    "nat_target_mismatch",
    "rule_chain_missing",
    "duplicate_rule_key",
}
_WARN_CODES = {
    "whitelist_missing_sources",
    "inactive_placeholder",
    "unexpected_mpf_chain",
    "unexpected_mpf_rule",
    "stale_deleted_customer_rule",
}
_PLACEHOLDER_KINDS = {"customer_pause_reject", "customer_expired_reject"}


@dataclass(frozen=True)
class FirewallDoctorReport:
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return self.payload

    def to_human(self) -> str:
        p = self.payload
        c = p["counts"]
        lines = [
            "MPF firewall doctor (planner-only)",
            f"component: {p['component']}",
            f"final_verdict: {p['final_verdict']}",
            f"backend: {p['backend']}",
            f"apply_mode: {p['apply_mode']}",
            f"applyable: {str(p['applyable']).lower()}",
            f"firewall_change: {p['firewall_change']}",
            f"nat_change: {p['nat_change']}",
            f"runtime_change: {p['runtime_change']}",
            f"planner_customer_source: {p['planner_customer_source']}",
            f"db_customer_input_loaded: {str(p['db_customer_input_loaded']).lower()}",
            f"chains: {c['chains']}",
            f"rules: {c['rules']}",
            f"changes: {c['changes']}",
            f"warnings: {c['warnings']}",
            f"errors: {c['errors']}",
            f"enabled_lanes: {c['enabled_lanes']}",
            f"lane_backend_coverage_count: {c['lane_backend_coverage']}",
            f"customer_coverage_count: {c['customer_coverage']}",
            f"affected_customers_count: {c['affected_customers']}",
            f"accounting_coverage_count: {c['accounting_coverage']}",
            f"active_forwarding_intent_count: {c['active_forwarding_intents']}",
            f"nat_redirect_intent_count: {c['nat_redirect_intents']}",
            f"backend_guard_intent_count: {c['backend_guard_intents']}",
            f"placeholder_intent_count: {c['placeholder_intents']}",
            f"whitelist_intent_count: {c['whitelist_intents']}",
            f"snapshot_input: {p['snapshot_input']}",
            f"drift_summary: {p['drift_summary']}",
        ]
        return "\n".join(lines)


def build_doctor_report(plan: FirewallPlanResult, *, snapshot_input: str = "none") -> FirewallDoctorReport:
    rule_kind_counts = Counter(r.rule_kind for r in plan.rules)
    change_counts = Counter(f"{c.kind}_{c.object_type}" for c in plan.changes)
    warning_codes = [w.code for w in plan.warnings]
    error_codes = [e.code for e in plan.errors]

    payload = {
        "component": "firewall_planner",
        "final_verdict": _verdict(plan, warning_codes, error_codes),
        "backend": plan.backend,
        "apply_mode": plan.apply_mode,
        "applyable": plan.applyable,
        "firewall_change": plan.firewall_change,
        "nat_change": plan.nat_change,
        "runtime_change": plan.runtime_change,
        "planner_customer_source": plan.planner_customer_source,
        "db_customer_input_loaded": plan.db_customer_input_loaded,
        "counts": {
            "chains": len(plan.chains),
            "rules": len(plan.rules),
            "changes": len(plan.changes),
            "warnings": len(plan.warnings),
            "errors": len(plan.errors),
            "enabled_lanes": len({r.lane for r in plan.rules if r.lane}),
            "lane_backend_coverage": len(set(plan.lane_backend_coverage)),
            "customer_coverage": len(set(plan.customer_coverage)),
            "affected_customers": len(set(plan.affected_customers)),
            "accounting_coverage": sum(1 for v in plan.accounting_coverage.values() if v),
            "active_forwarding_intents": rule_kind_counts.get("customer_dispatch", 0) + rule_kind_counts.get("customer_nat_redirect", 0),
            "nat_redirect_intents": rule_kind_counts.get("customer_nat_redirect", 0),
            "backend_guard_intents": rule_kind_counts.get("backend_guard", 0),
            "placeholder_intents": sum(v for k, v in rule_kind_counts.items() if k in _PLACEHOLDER_KINDS or k.endswith("_reject") and "customer_" in k and "nat" not in k and "connlimit" not in k and "hashlimit" not in k),
            "whitelist_intents": rule_kind_counts.get("customer_whitelist_allow", 0),
        },
        "warning_codes": sorted(set(warning_codes)),
        "error_codes": sorted(set(error_codes)),
        "snapshot_input": snapshot_input,
        "drift_summary": {
            "create_chain_count": change_counts.get("create_chain", 0),
            "create_rule_count": change_counts.get("create_rule", 0),
            "update_rule_count": change_counts.get("update_rule", 0),
            "keep_rule_count": change_counts.get("keep_rule", 0),
            "unexpected_mpf_chain_count": warning_codes.count("unexpected_mpf_chain"),
            "unexpected_mpf_rule_count": warning_codes.count("unexpected_mpf_rule"),
            "stale_deleted_customer_rule_count": warning_codes.count("stale_deleted_customer_rule"),
            "nat_target_mismatch_count": error_codes.count("nat_target_mismatch"),
            "duplicate_rule_key_count": error_codes.count("duplicate_rule_key"),
        },
        "safety": {
            "live_firewall_read": False,
            "live_firewall_write": False,
            "iptables_save_executed": False,
            "iptables_restore_executed": False,
            "runtime_change": "no",
        },
    }
    return FirewallDoctorReport(payload)


def _verdict(plan: FirewallPlanResult, warning_codes: list[str], error_codes: list[str]) -> str:
    if (not plan.applyable) or error_codes or any(code in _CRITICAL_CODES for code in error_codes):
        return "CRITICAL"
    if plan.planner_customer_source == "config_only" or not plan.db_customer_input_loaded:
        return "WARN"
    if warning_codes or any(code in _WARN_CODES for code in warning_codes):
        return "WARN"
    return "OK"
