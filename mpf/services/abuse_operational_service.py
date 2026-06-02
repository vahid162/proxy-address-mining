from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from mpf.domain.abuse_operational import OperationalAbuseEvaluation, evaluate_operational_abuse
from mpf.repositories.abuse_operational_repo import AbuseOperationalRepo


def abuse_doctor_report() -> dict[str, Any]:
    return {
        "component": "controlled_abuse_operational_core",
        "status": "READY",
        "runner": "operator_invoked_only",
        "timer_enabled": False,
        "daemon_enabled": False,
        "background_automation_enabled": False,
        "worker_enforcement_enabled": False,
        "firewall_apply_mode_required": "plan_only",
        "runtime_activation_allowed_required": False,
        "hard_unhard_boundary": "controlled_package_only",
    }


def run_abuse_cycle(repo: AbuseOperationalRepo, *, execute: bool, actor: str = "mpf-abuse-cli", now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    try:
        customers = repo.list_eligible_customers(now)
    except Exception as exc:
        return {"status": "BLOCKED", "execute": execute, "blockers": ["database_read_failed"], "error": str(exc), "evaluations": [], "hard_applied_count": 0}
    evaluations: list[OperationalAbuseEvaluation] = []
    blockers: list[str] = []
    for customer in customers:
        evaluation = evaluate_operational_abuse(customer, now=now)
        evaluations.append(evaluation)
        if evaluation.blockers:
            blockers.extend(f"customer_{customer.customer_id}:{item}" for item in evaluation.blockers)
        if not execute:
            continue
        try:
            if evaluation.write_transition:
                repo.write_transition(evaluation, actor=actor)
            elif evaluation.event_type:
                repo.record_evaluation_event(evaluation, actor=actor)
        except Exception as exc:
            blockers.append(f"customer_{customer.customer_id}:database_write_failed")
            blockers.append(str(exc))
    report = {
        "status": "BLOCKED" if blockers else "OK",
        "execute": execute,
        "scanned_customer_count": len(customers),
        "evaluations": [item.as_dict() for item in evaluations],
        "blockers": blockers,
        "hard_applied_count": 0,
        "note": "hard plans require mpf abuse hard --controlled-package; runner never applies firewall directly",
    }
    if execute:
        try:
            repo.record_job_run(status="failed" if blockers else "ok", data=report)
        except Exception as exc:
            report["status"] = "BLOCKED"
            report["blockers"].append("job_run_write_failed")
            report["blockers"].append(str(exc))
    return report


def apply_controlled_hard(repo: AbuseOperationalRepo, evaluation: OperationalAbuseEvaluation, package: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    blockers = _validate_controlled_package(package, operation="hard")
    if not evaluation.requires_controlled_hard or evaluation.proposed_state != "hard":
        blockers.append("sustained_miner_abuse_hard_plan_required")
    firewall = package.get("firewall", {})
    if firewall.get("apply_succeeded") is not True:
        blockers.append("controlled_firewall_apply_unavailable_or_failed")
    if firewall.get("verify_succeeded") is not True:
        blockers.append("controlled_firewall_verify_unavailable_or_failed")
    if firewall.get("conntrack_flush_succeeded") is not True:
        blockers.append("controlled_conntrack_flush_unavailable_or_failed")
    if blockers:
        return {"status": "BLOCKED", "operation": "hard", "blockers": sorted(set(blockers)), "hard_applied_at": None}
    try:
        applied = OperationalAbuseEvaluation(**{**asdict(evaluation), "result": "hard_applied", "event_type": "abuse.hard_applied", "write_transition": True})
        repo.write_transition(applied, actor=str(package["operator"]), hard_applied_at=now, audit=True)
    except Exception as exc:
        return {"status": "BLOCKED", "operation": "hard", "blockers": ["database_write_failed"], "error": str(exc), "hard_applied_at": None}
    return {"status": "OK", "operation": "hard", "hard_applied_at": now.isoformat(), "blockers": []}


def apply_controlled_unhard(repo: AbuseOperationalRepo, evaluation: OperationalAbuseEvaluation, package: dict[str, Any]) -> dict[str, Any]:
    blockers = _validate_controlled_package(package, operation="unhard")
    if evaluation.current_state != "hard":
        blockers.append("current_state_must_be_hard")
    firewall = package.get("firewall", {})
    if firewall.get("apply_succeeded") is not True or firewall.get("verify_succeeded") is not True:
        blockers.append("controlled_firewall_apply_verify_required")
    if blockers:
        return {"status": "BLOCKED", "operation": "unhard", "blockers": sorted(set(blockers))}
    target = OperationalAbuseEvaluation(**{**asdict(evaluation), "proposed_state": "normal", "result": "unhard_applied", "event_type": "abuse.unhard_applied", "write_transition": True})
    try:
        repo.write_transition(target, actor=str(package["operator"]), audit=True)
    except Exception as exc:
        return {"status": "BLOCKED", "operation": "unhard", "blockers": ["database_write_failed"], "error": str(exc)}
    return {"status": "OK", "operation": "unhard", "blockers": []}


def _validate_controlled_package(package: dict[str, Any], *, operation: str) -> list[str]:
    blockers: list[str] = []
    if package.get("operation") != operation:
        blockers.append("controlled_package_operation_mismatch")
    for name in ("operator", "reason", "evidence_reference", "restore_point_reference", "policy_backup_reference"):
        if not str(package.get(name, "")).strip():
            blockers.append(f"controlled_package_missing_{name}")
    firewall = package.get("firewall")
    if not isinstance(firewall, dict) or firewall.get("controlled_path") is not True:
        blockers.append("controlled_firewall_package_path_required")
    return blockers


def status_report(repo: AbuseOperationalRepo | None = None) -> dict[str, Any]:
    if repo is None:
        return {"status": "BLOCKED", "blockers": ["database_repository_not_configured"], "states": [], "note": "status is fail-closed until the controlled PostgreSQL repository is configured"}
    try:
        customers = repo.list_eligible_customers(datetime.now(UTC))
    except Exception as exc:
        return {"status": "BLOCKED", "blockers": ["database_read_failed"], "error": str(exc), "states": []}
    return {"status": "OK", "blockers": [], "states": [{"customer_id": c.customer_id, "lane_id": c.lane_id, "customer_key": c.customer_key, "port": c.port, "state": asdict(c.state)} for c in customers]}


def events_report(repo: AbuseOperationalRepo | None = None) -> dict[str, Any]:
    if repo is None:
        return {"status": "BLOCKED", "blockers": ["database_repository_not_configured"], "events": [], "note": "events are fail-closed until the controlled PostgreSQL repository is configured"}
    try:
        return {"status": "OK", "blockers": [], "events": repo.list_events()}
    except Exception as exc:
        return {"status": "BLOCKED", "blockers": ["database_read_failed"], "error": str(exc), "events": []}
