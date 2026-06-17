"""Read-only Phase 11 production pause/block/expire controls preflight readiness."""

from __future__ import annotations

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, MPFConfig, load_config
from mpf.domain.customers import CustomerDisableRequest, CustomerUpdateRequest
from mpf.services import customer_mutation_service, customer_read_service


def _flags(result) -> dict[str, object]:
    return {
        "would_mutate_customer": bool(getattr(result, "would_mutate_customer", False)),
        "would_create_event": bool(getattr(result, "would_create_event", False)),
        "would_create_audit": bool(getattr(result, "would_create_audit", False)),
    }


def _blocked_preflight(method: str, message: str, blockers: list[str]) -> dict[str, object]:
    return {
        "ready": False,
        "method": method,
        "message": message,
        "would_mutate_customer": False,
        "would_create_event": False,
        "would_create_audit": False,
        "executed": False,
        "yes_used": False,
        "blockers": blockers,
    }


def build_phase11_production_controls_pause_block_expire_readiness_report(
    config: MPFConfig, *, customer_key: str = "limited-btc-001"
) -> dict[str, object]:
    blockers: list[str] = []
    warnings: list[str] = []

    try:
        target = customer_read_service.show_customer(config, customer_key=customer_key)
    except Exception as exc:  # noqa: BLE001 - readiness must fail closed without traceback.
        target = None
        warnings.append(str(exc))

    if target is None or not target.ok or target.customer is None:
        blockers.append("customer_show_or_target_resolution_failed")
        msg = getattr(target, "message", "target customer could not be read safely")
        pause = _blocked_preflight("customer_disable_service_dry_run", msg, ["customer_show_or_target_resolution_failed"])
        expire = _blocked_preflight("customer_update_status_expired_service_dry_run", msg, ["customer_show_or_target_resolution_failed"])
    else:
        try:
            pr = customer_mutation_service.disable_db_only_customer(
                config, CustomerDisableRequest(customer_key=customer_key, reason="phase11-controls-readiness-dry-run"), dry_run=True
            )
            pause_blockers = [] if pr.ok and pr.message == "DRY_RUN_OK" else ["pause_dry_run_failed"]
            if pause_blockers:
                blockers.extend(pause_blockers)
            pause = {
                "ready": not pause_blockers,
                "method": "customer_disable_service_dry_run",
                "message": pr.message,
                **_flags(pr),
                "executed": False,
                "yes_used": False,
                "blockers": pause_blockers,
            }
        except Exception as exc:  # noqa: BLE001
            blockers.append("pause_dry_run_failed")
            pause = _blocked_preflight("customer_disable_service_dry_run", str(exc), ["pause_dry_run_failed"])
        try:
            er = customer_mutation_service.update_db_only_customer(
                config, CustomerUpdateRequest(customer_key=customer_key, status="expired"), dry_run=True
            )
            expire_blockers = [] if er.ok and er.message == "DRY_RUN_OK" else ["expire_dry_run_failed"]
            if expire_blockers:
                blockers.extend(expire_blockers)
            expire = {
                "ready": not expire_blockers,
                "method": "customer_update_status_expired_service_dry_run",
                "message": er.message,
                **_flags(er),
                "executed": False,
                "yes_used": False,
                "blockers": expire_blockers,
            }
        except Exception as exc:  # noqa: BLE001
            blockers.append("expire_dry_run_failed")
            expire = _blocked_preflight("customer_update_status_expired_service_dry_run", str(exc), ["expire_dry_run_failed"])

    blockers.append("block_capability_not_defined")
    blockers = sorted(set(blockers), key=blockers.index)
    return {
        "component": "phase11_production_controls_pause_block_expire_readiness",
        "repository_version": __version__,
        "phase11_operational_completion_required": True,
        "readiness_scope": "read_only_controls_preflight",
        "target_customer_key": customer_key,
        "pause_preflight": pause,
        "expire_run_preflight": expire,
        "block_preflight": {
            "ready": False,
            "method": "not_implemented",
            "message": "block capability is not defined in the customer lifecycle domain",
            "supported_statuses": ["active", "paused", "expired", "deleted"],
            "blockers": ["block_capability_not_defined"],
        },
        "production_controls_pause_block_expire": "missing_or_partial",
        "production_controls_pause_block_expire_ready": False,
        "blockers": blockers,
        "warnings": warnings,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "conntrack_flush_performed": False,
        "docker_restart_performed": False,
        "systemd_restart_performed": False,
        "phase12_start_allowed": False,
        "worker_enforcement_allowed": "no",
        "ui_allowed": "no",
        "telegram_allowed": "no",
        "production_traffic": "controlled_cli_limited",
        "customer_onboarding_allowed": "controlled_cli_limited",
        "final_decision": "BLOCKED_PRODUCTION_CONTROLS_PAUSE_BLOCK_EXPIRE_BLOCK_CAPABILITY_NOT_DEFINED",
    }


def run_phase11_production_controls_pause_block_expire_readiness_report(
    config_path=DEFAULT_CONFIG_PATH, *, customer_key: str = "limited-btc-001"
) -> dict[str, object]:
    return build_phase11_production_controls_pause_block_expire_readiness_report(load_config(config_path), customer_key=customer_key)
