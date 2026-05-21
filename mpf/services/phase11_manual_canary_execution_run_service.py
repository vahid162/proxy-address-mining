from __future__ import annotations

from dataclasses import dataclass

from mpf import __version__
from mpf.domain.production import ManualCanaryExecutionRunRequest

_DANGEROUS_SAFETY_FLAGS = (
    "production_traffic_authorized",
    "controlled_cli_canary_execution_authorized",
    "limited_customer_onboarding_authorized",
    "customer_db_mutation_authorized",
    "firewall_apply_authorized",
    "iptables_restore_authorized",
    "customer_nat_apply_authorized",
    "customer_firewall_rules_apply_authorized",
    "abuse_automation_authorized",
    "conntrack_flush_authorized",
    "worker_enforcement_authorized",
    "scheduler_authorized",
    "collector_authorized",
    "ui_authorized",
    "telegram_authorized",
)


@dataclass(slots=True)
class CanaryExecutionAdapters:
    readiness: object | None = None
    restore: object | None = None
    lock: object | None = None
    customer: object | None = None
    firewall: object | None = None
    verify: object | None = None
    evidence: object | None = None


def _call(adapter: object, fn: str, report: dict[str, object]) -> dict[str, object]:
    try:
        method = getattr(adapter, fn)
    except AttributeError:
        return {"status": "error", "error": f"adapter method missing: {fn}"}
    try:
        result = method(report)
    except Exception as exc:  # pragma: no cover - defensive fail-closed conversion
        return {"status": "error", "error": f"adapter call failed: {fn}: {exc}"}
    if not isinstance(result, dict):
        return {"status": "error", "error": f"adapter call must return dict: {fn}"}
    return result


def _record_partial_firewall_mutation(report: dict[str, object]) -> bool:
    firewall_apply = report.get("firewall_apply")
    if not isinstance(firewall_apply, dict):
        return False
    if firewall_apply.get("partial_mutation") is not True and firewall_apply.get("mutation_performed") is not True:
        return False
    report["mutation_performed"] = True
    report["firewall_mutation_performed"] = bool(firewall_apply.get("firewall_mutation_performed", True))
    report["nat_mutation_performed"] = bool(firewall_apply.get("nat_mutation_performed"))
    report["production_traffic_enabled"] = False
    report["rollback_readiness"] = {
        "status": "required",
        "instructions": firewall_apply.get("rollback_instructions"),
        "restore_point": report.get("restore_point"),
        "iptables_save_backup": report.get("iptables_save_backup"),
        "pre_apply_nat_sha256": firewall_apply.get("pre_apply_nat_sha256"),
        "post_apply_nat_sha256": firewall_apply.get("post_apply_nat_sha256"),
        "verification_error": firewall_apply.get("error"),
    }
    return True


def build_phase11_manual_canary_execution_run_report(request: ManualCanaryExecutionRunRequest, runtime_context: dict[str, object] | None = None, adapters: dict[str, object] | None = None) -> dict[str, object]:
    _ = runtime_context
    adapters = adapters or {}
    expected_repo_version = __version__
    validation_errors = request.validate(expected_repo_version=expected_repo_version)
    blockers: list[str] = []
    warnings: list[str] = []
    preflight_results = {"phase_gate": "OK", "mpf_doctor": "OK", "db_status": "OK", "proxy_doctor": "OK", "no_customer_nat_baseline": "OK", "no_customer_firewall_baseline": "OK", "local_only_runtime_baseline": "OK"}

    report = {
        "component": "phase11_manual_canary_execution_run",
        "phase": "Phase 11E — Production service-layer manual canary execution adapter wiring",
        "mode": request.requested_action,
        "final_decision": "BLOCKED",
        "authorization_status": "MANUAL_CANARY_EXECUTION_OPERATOR_APPROVAL_REQUIRED",
        "execution_allowed": False,
        "execution_requested": request.requested_action == "execute",
        "execution_preflight_passed": False,
        "execution_started": False,
        "execution_completed": False,
        "execution_failed": False,
        "actual_canary_execution_performed": False,
        "mutation_performed": False,
        "customer_db_mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "production_traffic_enabled": False,
        "scope": {"single_canary_only": True, "customer_key": "canary-btc-001", "lane": "btc", "port": 20001},
        "adapter_mode": "none",
        "real_adapters_wired": False,
        "missing_real_adapter_capabilities": [],
        "canary_customer_idempotency": "unknown",
        "firewall_apply_boundary": "unknown",
        "production_execution_ready": False,
        "request": request.as_dict(),
        "validation_errors": validation_errors,
        "blockers": blockers,
        "warnings": warnings,
        "preflight_results": preflight_results,
        "restore_point": None,
        "iptables_save_backup": None,
        "lock": {"acquired": False, "released": False},
        "customer_result": None,
        "firewall_plan": None,
        "firewall_diff": None,
        "firewall_apply": None,
        "post_apply_verification": None,
        "canary_connection": None,
        "nat_hit_visibility": None,
        "usage_visibility": None,
        "reject_visibility": None,
        "session_worker_visibility": None,
        "abuse_1h_coverage": None,
        "rollback_readiness": {"status": "required"},
        "evidence_summary": None,
        "operator_next_steps": [],
        "safety_flags": {key: False for key in _DANGEROUS_SAFETY_FLAGS},
    }

    if validation_errors:
        blockers.append("validation failed; execution is fail-closed")

    if request.requested_action == "plan":
        report["final_decision"] = "PLAN_READY_FOR_FARM5_SYNC_EVIDENCE" if not validation_errors else "BLOCKED"
        report["authorization_status"] = "MANUAL_CANARY_EXECUTION_PACKAGE_NON_AUTHORIZING"
        warnings.append("plan mode is non-mutating and non-authorizing")
        report["adapter_mode"] = "production_service_layer" if adapters else "none"
        report["real_adapters_wired"] = bool(adapters)
        return report

    report["adapter_mode"] = "production_service_layer"
    report["real_adapters_wired"] = True
    report["canary_customer_idempotency"] = "service_layer_adapter_required"
    report["firewall_apply_boundary"] = "accepted_service_layer_apply_required"

    missing = [k for k in ("readiness", "restore", "lock", "customer", "firewall", "verify", "evidence") if k not in adapters]
    if missing:
        blockers.append(f"missing execution adapters: {', '.join(missing)}")
        report["real_adapters_wired"] = False
        return report

    lock_acquired = False
    report["execution_allowed"] = False
    try:
        for step, key in (("check_readiness", "preflight_results"), ("create_restore_point", "restore_point"), ("create_iptables_save_backup", "iptables_save_backup")):
            obj = _call(adapters["readiness"] if step == "check_readiness" else adapters["restore"], step, report)
            if obj.get("status") != "ok":
                blockers.append(obj.get("error", f"{step} failed"))
                report["final_decision"] = "BLOCKED"
                return report
            if key in obj:
                report[key] = obj[key]

        report["execution_preflight_passed"] = True
        report["execution_allowed"] = True

        lock_resp = _call(adapters["lock"], "acquire", report)
        lock_acquired = lock_resp.get("acquired", False)
        report["lock"]["acquired"] = lock_acquired
        if not lock_acquired:
            blockers.append(lock_resp.get("error", "lock acquire failed"))
            report["final_decision"] = "BLOCKED"
            report["execution_allowed"] = False
            return report

        report["execution_started"] = True

        report["customer_result"] = _call(adapters["customer"], "ensure_customer", report)
        if report["customer_result"].get("status") != "ok":
            blockers.append(report["customer_result"].get("error", "ensure_customer failed"))
            report["final_decision"] = "EXECUTION_FAILED"
            report["execution_failed"] = True
            report["execution_allowed"] = False
            return report

        report["firewall_plan"] = _call(adapters["firewall"], "build_plan", report)
        if report["firewall_plan"].get("status") != "ok":
            blockers.append(report["firewall_plan"].get("error", "build_plan failed"))
            report["final_decision"] = "EXECUTION_FAILED"
            report["execution_failed"] = True
            report["execution_allowed"] = False
            return report

        report["firewall_diff"] = _call(adapters["firewall"], "render_diff", report)
        if report["firewall_diff"].get("status") != "ok":
            blockers.append(report["firewall_diff"].get("error", "render_diff failed"))
            report["final_decision"] = "EXECUTION_FAILED"
            report["execution_failed"] = True
            report["execution_allowed"] = False
            return report

        report["firewall_apply"] = _call(adapters["firewall"], "apply_plan", report)
        if report["firewall_apply"].get("status") != "ok":
            blocker = report["firewall_apply"].get("error", "firewall apply failed")
            blockers.append(blocker)
            partial_mutation = _record_partial_firewall_mutation(report)
            if report["firewall_apply"].get("status") == "blocked" and not partial_mutation:
                report["missing_real_adapter_capabilities"].append(blocker)
                report["firewall_apply_boundary"] = blocker
                missing_primitive = report["firewall_apply"].get("missing_primitive")
                report["operator_next_steps"] = [f"implement {missing_primitive}" if missing_primitive else f"resolve blocker: {blocker}"]
                report["final_decision"] = "BLOCKED"
                report["execution_allowed"] = False
                return report
            report["final_decision"] = "EXECUTION_FAILED"
            report["execution_failed"] = True
            report["execution_allowed"] = False
            return report

        for field, method in (("post_apply_verification", "verify_post_apply"), ("canary_connection", "verify_canary_connection"), ("nat_hit_visibility", "verify_nat_hit"), ("usage_visibility", "verify_usage"), ("reject_visibility", "verify_reject"), ("session_worker_visibility", "verify_session_worker"), ("abuse_1h_coverage", "verify_abuse_coverage"), ("rollback_readiness", "rollback_readiness")):
            out = _call(adapters["verify"], method, report)
            report[field] = out
            if out.get("status") not in ("ok", "instruction_required"):
                blockers.append(out.get("error", f"{method} failed"))
                report["final_decision"] = "EXECUTION_FAILED"
                report["execution_failed"] = True
                report["execution_allowed"] = False
                return report

        report["evidence_summary"] = _call(adapters["evidence"], "emit_evidence", report)
        if report["evidence_summary"].get("status") != "ok":
            blockers.append(report["evidence_summary"].get("error", "emit_evidence failed"))
            report["final_decision"] = "EXECUTION_FAILED"
            report["execution_failed"] = True
            report["execution_allowed"] = False
            return report

        customer_ok = report["customer_result"].get("status") == "ok" and report["customer_result"].get("placeholder") is not True
        applied = report["firewall_apply"].get("applied") is True
        nat_ok = report["firewall_apply"].get("nat_rule_verified") is True
        report["safety_flags"].update({
            "controlled_cli_canary_execution_authorized": True,
            "customer_db_mutation_authorized": bool(customer_ok and report["customer_result"].get("created") is True),
            "firewall_apply_authorized": applied,
            "iptables_restore_authorized": bool(report["firewall_apply"].get("iptables_restore_used") is True),
            "customer_nat_apply_authorized": nat_ok,
            "customer_firewall_rules_apply_authorized": applied,
            "production_traffic_authorized": nat_ok,
        })
        report["production_execution_ready"] = True
        report["final_decision"] = "EXECUTION_COMPLETED_PENDING_REVIEW"
        report["execution_completed"] = True
        report["actual_canary_execution_performed"] = True
        report["mutation_performed"] = bool(applied or report["customer_result"].get("created") is True)
        report["customer_db_mutation_performed"] = bool(report["customer_result"].get("created") is True)
        report["firewall_mutation_performed"] = applied
        report["nat_mutation_performed"] = nat_ok
        report["production_traffic_enabled"] = nat_ok
    finally:
        if lock_acquired:
            release = _call(adapters["lock"], "release", report)
            report["lock"]["released"] = release.get("released", False)

    return report