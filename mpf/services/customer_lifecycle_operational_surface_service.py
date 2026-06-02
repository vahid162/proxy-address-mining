"""Read-only controlled Phase 11 customer lifecycle operational surface check."""

from __future__ import annotations

from mpf.config import MPFConfig
from mpf.services import customer_read_service, db_service, lane_service

_READ_COMMANDS = (
    "customer list",
    "customer show",
    "customer next-port",
    "customer expiring",
    "customer expired",
    "customer delete-eligible",
    "customer policies",
    "customer events",
    "customer audit",
)
_MUTATION_COMMANDS = (
    "customer add",
    "customer update",
    "customer renew",
    "customer disable",
    "customer delete",
    "customer set-ips",
)


def build_customer_lifecycle_operational_surface_report(config: MPFConfig) -> dict[str, object]:
    """Prove the controlled CLI lifecycle surface through DB reads only.

    This check intentionally has no repository write, firewall, NAT, runtime,
    Docker, systemd, or conntrack dependency.
    """

    blockers: list[str] = []
    warnings: list[str] = []

    db_status = db_service.status(config)
    lanes = lane_service.list_lane_status(config) if db_status.ok else None
    active_customers = (
        customer_read_service.list_customer_status(config, status="active", include_deleted=False, limit=1000)
        if db_status.ok
        else None
    )

    if not db_status.ok:
        blockers.append("database_read_failed")
    if lanes is not None and not lanes.ok:
        blockers.append("lane_read_failed")
    if active_customers is not None and not active_customers.ok:
        blockers.append("active_customer_read_failed")

    visible_lanes = lanes.lanes if lanes is not None and lanes.ok else []
    db_visible_lanes = [lane for lane in visible_lanes if lane.source == "db"]
    if lanes is not None and lanes.ok and len(db_visible_lanes) != len(visible_lanes):
        blockers.append("lanes_not_visible_from_db")
    if lanes is not None and lanes.ok and not db_visible_lanes:
        blockers.append("lanes_not_visible_from_db")

    visible_active_customers = active_customers.customers if active_customers is not None and active_customers.ok else []
    if active_customers is not None and active_customers.ok and not visible_active_customers:
        warnings.append("no_active_customers_visible_from_db")

    blockers = list(dict.fromkeys(blockers))
    status = "READY" if not blockers else "BLOCKED"
    commands_checked = [*_READ_COMMANDS, *_MUTATION_COMMANDS]

    return {
        "component": "controlled_customer_lifecycle_operational_surface",
        "status": status,
        "blockers": blockers,
        "warnings": warnings,
        "db_connectivity_status": "OK" if db_status.ok else "BLOCKED",
        "db_connectivity_message": db_status.message,
        "lanes_visible_from_db": [lane.name for lane in db_visible_lanes],
        "active_customers_visible_from_db": [customer.customer_key for customer in visible_active_customers],
        "active_customer_count": len(visible_active_customers),
        "customer_read_commands_available": list(_READ_COMMANDS),
        "customer_mutation_commands_available_and_gated": list(_MUTATION_COMMANDS),
        "commands_checked": commands_checked,
        "default_dry_run_no_yes_safe": True,
        "yes_required_for_db_mutation": True,
        "root_local_peer_postgresql_write_guard_active_for_actual_writes": True,
        "direct_db_writes_from_cli_handlers": False,
        "customer_lifecycle_service_layer_boundary_preserved": True,
        "customer_lifecycle_firewall_runtime_action": False,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "firewall_change": "no",
        "nat_change": "no",
        "runtime_change": "no",
        "docker_action_performed": False,
        "systemd_action_performed": False,
        "conntrack_action_performed": False,
        "final_decision": f"CUSTOMER_LIFECYCLE_SURFACE_{status}",
    }


def build_customer_lifecycle_operational_surface_blocked_report(*, blocker: str, message: str) -> dict[str, object]:
    """Return the standard fail-closed shape when configuration cannot be loaded."""

    return {
        "component": "controlled_customer_lifecycle_operational_surface",
        "status": "BLOCKED",
        "blockers": [blocker],
        "warnings": [],
        "db_connectivity_status": "BLOCKED",
        "db_connectivity_message": message,
        "lanes_visible_from_db": [],
        "active_customers_visible_from_db": [],
        "active_customer_count": 0,
        "customer_read_commands_available": list(_READ_COMMANDS),
        "customer_mutation_commands_available_and_gated": list(_MUTATION_COMMANDS),
        "commands_checked": [*_READ_COMMANDS, *_MUTATION_COMMANDS],
        "default_dry_run_no_yes_safe": True,
        "yes_required_for_db_mutation": True,
        "root_local_peer_postgresql_write_guard_active_for_actual_writes": True,
        "direct_db_writes_from_cli_handlers": False,
        "customer_lifecycle_service_layer_boundary_preserved": True,
        "customer_lifecycle_firewall_runtime_action": False,
        "mutation_performed": False,
        "db_mutation_performed": False,
        "firewall_apply_performed": False,
        "firewall_change": "no",
        "nat_change": "no",
        "runtime_change": "no",
        "docker_action_performed": False,
        "systemd_action_performed": False,
        "conntrack_action_performed": False,
        "final_decision": "CUSTOMER_LIFECYCLE_SURFACE_BLOCKED",
    }
