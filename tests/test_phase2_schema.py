from __future__ import annotations

from mpf.models import Base


def table_names() -> set[str]:
    return set(Base.metadata.tables)


def columns(table_name: str) -> set[str]:
    return set(Base.metadata.tables[table_name].columns.keys())


def test_phase2_required_tables_exist() -> None:
    required = {
        "settings",
        "operators",
        "api_tokens",
        "lanes",
        "lane_upstreams",
        "customers",
        "customer_policies",
        "customer_ip_pins",
        "events",
        "audit_log",
        "notes",
        "firewall_applies",
        "firewall_snapshots",
        "firewall_rules_desired",
        "firewall_rules_live",
        "restore_points",
        "usage_samples",
        "policy_events",
        "flow_sessions",
        "flow_events",
        "worker_events",
        "customer_workers",
        "abuse_states",
        "abuse_events",
        "job_runs",
        "scheduler_locks",
        "blocks",
        "pauses",
        "notifications",
        "notification_targets",
        "backups",
    }
    assert required <= table_names()


def test_lane_and_customer_core_fields_are_represented() -> None:
    assert {"name", "enabled", "backend_port", "chain_prefix", "protocol"} <= columns("lanes")
    assert {"lane_id", "name", "port", "status", "starts_at", "expires_at"} <= columns("customers")


def test_customer_policy_is_versioned_and_abuse_exemption_is_explicit() -> None:
    required = {
        "customer_id",
        "version",
        "is_current",
        "miners",
        "farms",
        "maxconn",
        "rate_per_min",
        "burst",
        "ips_mode",
        "abuse_exempt",
        "abuse_exempt_reason",
        "abuse_exempt_until",
        "abuse_exempt_by",
    }
    assert required <= columns("customer_policies")


def test_abuse_state_machine_is_representable() -> None:
    required = {
        "customer_id",
        "status",
        "current_hot",
        "current_unique_ips",
        "current_unique_workers",
        "first_seen_over",
        "last_seen_over",
        "last_recovery_at",
        "hard_applied_at",
        "policy_backup_id",
        "restore_point_id",
        "last_event_id",
    }
    assert required <= columns("abuse_states")


def test_firewall_history_and_restore_are_represented() -> None:
    assert {"backend", "iptables_save_text", "checksum"} <= columns("firewall_snapshots")
    assert {"restore_type", "snapshot_id", "backup_id", "metadata_json", "checksum"} <= columns("restore_points")
    assert {
        "action",
        "status",
        "apply_mode",
        "backend",
        "restore_point_id",
        "snapshot_before_id",
        "snapshot_after_id",
        "plan_json",
    } <= columns("firewall_applies")


def test_job_runs_and_scheduler_locks_are_represented() -> None:
    assert {"job_name", "status", "started_at", "finished_at", "duration_ms", "data_json"} <= columns("job_runs")
    assert {"lock_name", "owner", "acquired_at", "expires_at", "metadata_json"} <= columns("scheduler_locks")


def test_no_sqlite_source_of_truth_tables_are_introduced() -> None:
    forbidden = {"customer_tsv", "sqlite_state", "flatfile_customers"}
    assert table_names().isdisjoint(forbidden)
