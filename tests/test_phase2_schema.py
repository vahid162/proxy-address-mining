from __future__ import annotations

import mpf.extension_models  # noqa: F401 - registers extension-ready tables on Base.metadata
import mpf.future_models  # noqa: F401 - registers future-ready tables on Base.metadata
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


def test_future_buyer_account_boundary_is_represented() -> None:
    required = {
        "buyer_accounts",
        "buyer_users",
        "customer_service_links",
        "customer_service_permissions",
        "action_requests",
    }
    assert required <= table_names()
    assert {"account_key", "display_name", "status"} <= columns("buyer_accounts")
    assert {"buyer_account_id", "email", "password_hash", "status"} <= columns("buyer_users")
    assert {"buyer_account_id", "customer_id", "status"} <= columns("customer_service_links")
    assert {"buyer_user_id", "customer_id", "scope", "enabled"} <= columns("customer_service_permissions")
    assert {"requester_type", "action_type", "target_type", "status", "payload_json"} <= columns("action_requests")


def test_future_entitlement_and_plan_boundary_is_represented() -> None:
    required = {
        "plans",
        "plan_versions",
        "subscriptions",
        "subscription_items",
        "service_entitlements",
        "customer_policy_overrides",
    }
    assert required <= table_names()
    assert {"code", "name", "status"} <= columns("plans")
    assert {"plan_id", "version", "limits_json", "status"} <= columns("plan_versions")
    assert {"buyer_account_id", "status", "starts_at", "ends_at"} <= columns("subscriptions")
    assert {"subscription_id", "plan_version_id", "customer_id", "item_type", "status"} <= columns(
        "subscription_items"
    )
    assert {"buyer_account_id", "customer_id", "entitlement", "enabled"} <= columns("service_entitlements")
    assert {"customer_id", "field_name", "value_json", "status", "reason"} <= columns("customer_policy_overrides")


def test_future_worker_policy_boundary_is_represented() -> None:
    required = {
        "worker_identities",
        "worker_policies",
        "worker_blocks",
        "worker_enforcement_events",
    }
    assert required <= table_names()
    assert {"customer_id", "worker_name", "normalized_worker_name", "status"} <= columns("worker_identities")
    assert {"customer_id", "mode", "reason"} <= columns("worker_policies")
    assert {"customer_id", "worker_name", "match_type", "reason", "status"} <= columns("worker_blocks")
    assert {"customer_id", "worker_name", "src_ip", "action", "adapter", "evidence_json"} <= columns(
        "worker_enforcement_events"
    )


def test_control_plane_operational_extension_tables_are_represented() -> None:
    required = {
        "feature_flags",
        "notification_rules",
        "config_snapshots",
        "restore_drills",
        "server_profiles",
        "preflight_runs",
        "preflight_findings",
        "secret_references",
        "maintenance_windows",
        "abuse_profiles",
    }
    assert required <= table_names()
    assert {"key", "enabled", "scope", "reason"} <= columns("feature_flags")
    assert {"event_type", "severity_min", "target_id", "enabled", "throttle_sec"} <= columns("notification_rules")
    assert {"config_path", "config_text", "checksum", "reason"} <= columns("config_snapshots")
    assert {"backup_id", "drill_type", "status", "tested_at", "result_json"} <= columns("restore_drills")
    assert {"hostname", "iptables_backend", "docker_version", "postgres_version", "last_preflight_at"} <= columns(
        "server_profiles"
    )
    assert {"server_profile_id", "status", "started_at", "finished_at", "summary_json"} <= columns("preflight_runs")
    assert {"preflight_run_id", "key", "severity", "message", "data_json"} <= columns("preflight_findings")
    assert {"name", "secret_type", "path", "required_by", "status"} <= columns("secret_references")
    assert {"scope", "subject_id", "starts_at", "ends_at", "behavior", "reason"} <= columns("maintenance_windows")
    assert {"name", "threshold_sec", "grace_sec", "hard_strategy", "conntrack_flush_strategy"} <= columns(
        "abuse_profiles"
    )


def test_import_health_and_incident_extension_tables_are_represented() -> None:
    required = {
        "import_batches",
        "import_staged_customers",
        "import_validation_errors",
        "customer_health_snapshots",
        "incidents",
        "incident_events",
        "runbook_steps",
    }
    assert required <= table_names()
    assert {"source", "status", "summary_json", "confirmed_at", "confirmed_by"} <= columns("import_batches")
    assert {"import_batch_id", "proposed_name", "proposed_port", "raw_json", "validation_json", "status"} <= columns(
        "import_staged_customers"
    )
    assert {"import_batch_id", "staged_customer_id", "severity", "code", "message"} <= columns(
        "import_validation_errors"
    )
    assert {"customer_id", "status", "score", "reasons_json", "checked_at"} <= columns("customer_health_snapshots")
    assert {"incident_type", "severity", "status", "title", "opened_at", "closed_at"} <= columns("incidents")
    assert {"incident_id", "event_type", "message", "data_json"} <= columns("incident_events")
    assert {"incident_type", "step_order", "title", "command_hint", "enabled"} <= columns("runbook_steps")


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


def test_customers_are_not_buyer_accounts() -> None:
    assert "buyer_account_id" not in columns("customers")
    assert "customer_id" in columns("customer_service_links")


def test_worker_blocks_are_not_firewall_only() -> None:
    assert "worker_name" in columns("worker_blocks")
    assert "adapter" in columns("worker_enforcement_events")


def test_default_feature_flags_are_separate_from_runtime_actions() -> None:
    assert "enabled" in columns("feature_flags")
    assert "key" in columns("feature_flags")
    assert "firewall_applies" in table_names()


def test_no_sqlite_source_of_truth_tables_are_introduced() -> None:
    forbidden = {"customer_tsv", "sqlite_state", "flatfile_customers"}
    assert table_names().isdisjoint(forbidden)
