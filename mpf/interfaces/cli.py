from __future__ import annotations

import json
from typing import Literal
from pathlib import Path

import typer

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.db import write_local_peer_root_guard_message
from mpf.domain.customer_lifecycle import CustomerLifecycleInput
from mpf.domain.customers import CustomerCreateRequest, CustomerDeleteRequest, CustomerDisableRequest, CustomerPolicyInput, CustomerRenewRequest, CustomerSetIpsRequest, CustomerUpdateRequest
from mpf.domain.health import HealthReport
from mpf.domain import production as production_domain
from mpf.services import (
    phase8_controlled_worker_dry_run_gate_service,
    firewall_apply_gate_readiness_service,
    firewall_no_customer_apply_acceptance_gate_service,
    firewall_no_customer_apply_execution_acceptance_service,
    firewall_no_customer_apply_execution_gate_service,
    firewall_no_customer_apply_package_service,
    firewall_no_customer_apply_scaffold_service,
    firewall_no_customer_runtime_execution_approval_service,
    firewall_no_customer_runtime_execution_evidence_service,
    firewall_live_snapshot_scaffold_service,
    firewall_live_snapshot_read_service,
    firewall_manual_canary_customer_acceptance_readiness_service,
    firewall_manual_canary_customer_proposal_service,
    firewall_manual_canary_customer_server_evidence_service,
    phase6_final_acceptance_readiness_service,
    phase6_final_acceptance_review_service,
    phase6_operator_acceptance_decision_service,
    config_service,
    customer_mutation_service,
    customer_read_service,
    db_service,
    doctor_service,
    firewall_snapshot_parser,
    job_service,
    lane_service,
    lane_sync_service,
    firewall_planner_service,
    firewall_doctor_service,
    firewall_restore_payload_renderer,
    firewall_apply_contract_service,
    firewall_apply_package_service,
    firewall_rollback_artifact_renderer,
    firewall_preflight_service,
    firewall_evidence_service,
    firewall_gate_review_service,
    firewall_restore_lock_record_acceptance_gate_service,
    firewall_restore_lock_record_execution_gate_service,
    firewall_restore_lock_record_gate_service,
    firewall_restore_lock_record_readiness_service,
    proxy_doctor_service,
    phase7_policy_reject_accounting_contract_service,
    phase7_usage_accounting_contract_service,
    phase7_usage_policy_readiness_service,
    phase7_reports_doctor_service,
    phase7_final_acceptance_readiness_service,
    phase7_operator_acceptance_decision_service,
    phase8_planning_readiness_service,
    phase8_abuse_state_machine_contract_service,
    phase8_abuse_evidence_reporting_contract_service,
    phase8_abuse_dry_run_evaluator_service,
    phase8_db_transition_readiness_service,
    phase8_runtime_worker_integration_readiness_service,
    phase8_db_transition_execution_service,
    phase8_runtime_worker_dry_run_harness_service,
    phase8_controlled_worker_pre_acceptance_service,
    phase8_controlled_worker_dry_run_service,
    phase8_farm5_dry_run_evidence_collection_service,
    phase8_final_acceptance_readiness_service,
    phase8_final_acceptance_service,
    phase9_final_verdict_diagnostics_service,
    phase9_readiness_service,
    phase9_diagnostics_bundle_service,
    phase9_final_acceptance_readiness_service,
    phase9_final_acceptance_service,
    phase9_customer_diagnostics_service,
    phase9_abuse_visibility_service,
    phase9_usage_visibility_service,
    phase9_policy_reject_visibility_service,
    phase9_proxy_runtime_diagnostics_service,
    phase9_evidence_pack_service,
    phase9_troubleshooting_summary_service,
    phase10_readiness_service,
    phase10_session_readiness_service,
    phase10_session_model_readiness_service,
    phase10_worker_identity_readiness_service,
    phase10_worker_policy_readiness_service,
    phase10_worker_policy_contract_readiness_service,
    phase10_implementation_readiness_service,
    phase10_share_timeline_readiness_service,
    phase10_share_timeline_model_readiness_service,
    phase10_collector_dry_run_gate_service,
    phase10_collector_dry_run_plan_service,
    phase10_runtime_worker_dry_run_readiness_service,
    phase10_scheduler_dry_run_readiness_service,
    phase10_worker_cycle_dry_run_plan_service,
    phase10_final_acceptance_readiness_service,
    phase10_final_acceptance_service,
    phase10_enforcement_boundary_service,
    phase11_production_readiness_service,
    phase11_canary_plan_service,
    phase11_controlled_activation_harness_service,
    phase11_manual_canary_acceptance_service,
    phase11_manual_canary_execution_gate_service,
    phase11_manual_canary_execution_run_preparation_service,
    phase11_manual_canary_execution_run_service,
    phase11_manual_canary_execution_adapters,
    phase11_canary_acceptance_review_service,
    phase11_live_canary_evidence_collector_service,
    phase11_canary_visibility_bundle_service,
    phase11_canary_final_check_report_visibility_service,
    phase11_canary_rollback_restore_visibility_service,
    phase11_canary_usage_visibility_service,
    phase11_canary_usage_evidence_capture_service, phase11_canary_reject_session_ip_evidence_capture_service, phase11_canary_reject_counters_visibility_service, phase11_canary_worker_stratum_evidence_capture_service, phase11_external_canary_stratum_transcript_import_service, phase11_canary_abuse_coverage_visibility_service, phase11_canary_runtime_path_evidence_service, phase11_canary_acceptance_decision_service, phase11_limited_onboarding_gate_service, phase11_limited_onboarding_execution_gate_service,
    phase11_single_customer_staging_service,
    phase11_single_customer_firewall_plan_gate_service, phase11_single_customer_firewall_apply_gate_service, phase11_single_customer_firewall_apply_execution_service, phase11_single_customer_post_apply_evidence_service, phase11_single_customer_runtime_path_evidence_service, phase11_single_customer_stratum_transcript_evidence_service, phase11_single_customer_visibility_bundle_service,
    phase11_canary_evidence_pack_service,
    phase11_canary_db_visibility_activation_service,
    operator_execution_context_service,
)

app = typer.Typer(
    name="mpf",
    help="MPF safe CLI. Phase-gated read-only foundation commands; no production traffic mutation.",
    no_args_is_help=True,
    invoke_without_command=True,
)
config_app = typer.Typer(help="Configuration read-only commands.")
db_app = typer.Typer(help="Database read-only commands.")
lanes_app = typer.Typer(help="Lane DB-only commands. No firewall/NAT/runtime mutation.")
customer_app = typer.Typer(help="Customer DB-only commands. No firewall/NAT/runtime mutation.")
jobs_app = typer.Typer(help="Job read-only commands.")
proxy_app = typer.Typer(help="Proxy read-only planning and doctor commands.")
firewall_app = typer.Typer(help="Firewall dry-run planner commands only.")
events_app = typer.Typer(help="Global event read-only commands.")
phase6_app = typer.Typer(help="Phase 6 report-only gate commands.")
phase7_app = typer.Typer(help="Phase 7 report-only readiness commands.")
phase8_app = typer.Typer(help="Phase 8 report-only readiness commands.")
phase9_app = typer.Typer(help="Phase 9 report-only readiness commands.")
phase10_app = typer.Typer(help="Phase 10 report-only planning/readiness commands.")
production_app = typer.Typer(help="Phase 11 production readiness report-only commands.")
app.add_typer(config_app, name="config")
app.add_typer(db_app, name="db")
app.add_typer(lanes_app, name="lanes")
app.add_typer(customer_app, name="customer")
app.add_typer(jobs_app, name="jobs")
app.add_typer(proxy_app, name="proxy")
app.add_typer(firewall_app, name="firewall")
app.add_typer(events_app, name="events")
app.add_typer(phase6_app, name="phase6")
app.add_typer(phase7_app, name="phase7")
app.add_typer(phase8_app, name="phase8")
app.add_typer(phase9_app, name="phase9")
app.add_typer(phase10_app, name="phase10")
app.add_typer(production_app, name="production")


def _config_path(config: Path | None) -> Path:
    return config or DEFAULT_CONFIG_PATH


def _load(config: Path | None):
    return load_config(_config_path(config))




def _extract_current_state_block(phase_status_path: Path) -> str:
    try:
        content = phase_status_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError(f"phase status file not found: {phase_status_path}") from exc

    marker = "## Current State"
    marker_index = content.find(marker)
    if marker_index == -1:
        raise RuntimeError(f"missing section in phase status file: {marker}")

    section = content[marker_index + len(marker):]
    block_start = section.find("```text")
    if block_start == -1:
        raise RuntimeError("missing fenced text block under ## Current State")

    block_body_start = block_start + len("```text")
    block_end = section.find("```", block_body_start)
    if block_end == -1:
        raise RuntimeError("unterminated fenced text block under ## Current State")

    block = section[block_body_start:block_end].strip()
    if not block:
        raise RuntimeError("empty fenced text block under ## Current State")
    return block



def _load_optional_snapshot_file(live_snapshot_file: Path | None):
    if live_snapshot_file is None:
        return None
    if not live_snapshot_file.exists():
        typer.echo(f"ERROR: unable to read live snapshot file: {live_snapshot_file}: file does not exist")
        raise typer.Exit(1)
    if not live_snapshot_file.is_file():
        typer.echo(f"ERROR: unable to read live snapshot file: {live_snapshot_file}: not a file")
        raise typer.Exit(1)
    try:
        return firewall_snapshot_parser.parse_iptables_save_file(str(live_snapshot_file))
    except OSError as exc:
        typer.echo(f"ERROR: unable to read live snapshot file: {live_snapshot_file}: {exc}")
        raise typer.Exit(1)

def _emit_health_report(report: HealthReport) -> None:
    typer.echo(f"component: {report.component}")
    typer.echo(f"final_verdict: {report.final_verdict.value}")
    for check in report.checks:
        typer.echo(f"{check.status.value}\t{check.key}\t{check.message}")
        if check.remediation:
            typer.echo(f"  remediation: {check.remediation}")


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", help="Show version and exit.", is_eager=True),
) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit()


@app.command()
def doctor(config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml.")) -> None:
    """Run read-only diagnostics without mutating production traffic."""
    path = _config_path(config)
    result = doctor_service.run(path)
    typer.echo("MPF doctor")
    typer.echo(f"config_path: {result.config_path}")
    typer.echo(f"config: {'OK' if result.config_ok else 'ERROR'}")
    if result.config_ok:
        typer.echo(f"database: {'OK' if result.db_ok else 'ERROR'}")
        typer.echo(f"apply_mode: {result.apply_mode}")
        typer.echo(f"traffic_changes: {result.traffic_changes}")
        typer.echo(f"firewall_mutation: {result.firewall_mutation}")
        typer.echo(f"abuse_automation: {result.abuse_automation}")
    if not result.ok:
        typer.echo(f"message: {result.message}")
        raise typer.Exit(1)


@config_app.command("validate")
def config_validate(config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml.")) -> None:
    """Validate config without mutating anything."""
    ok, message = config_service.validate(_config_path(config))
    if ok:
        typer.echo("OK")
        return
    typer.echo(message)
    raise typer.Exit(1)


@config_app.command("show")
def config_show(config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml.")) -> None:
    """Show normalized safe config summary."""
    summary = config_service.show(_config_path(config))
    cfg = summary.config
    typer.echo(f"server.name: {cfg.server.name}")
    typer.echo(f"server.timezone: {cfg.server.timezone}")
    typer.echo(f"database.url: {cfg.database.url}")
    typer.echo(f"firewall.backend: {cfg.firewall.backend}")
    typer.echo(f"firewall.apply_mode: {cfg.firewall.apply_mode}")
    typer.echo(f"proxy.compose_file: {cfg.proxy.compose_file}")
    typer.echo(f"proxy.project_name: {cfg.proxy.project_name}")
    typer.echo(f"proxy.runtime_activation_allowed: {cfg.proxy.runtime_activation_allowed}")
    typer.echo(f"v2raya.ui_bind_host: {cfg.v2raya.ui_bind_host}")
    typer.echo(f"v2raya.ui_port: {cfg.v2raya.ui_port}")
    for lane_name, lane in sorted(cfg.lanes.items()):
        typer.echo(f"lane.{lane_name}: enabled={lane.enabled} backend_port={lane.backend_port} chain_prefix={lane.chain_prefix}")
        if lane.forwarder:
            typer.echo(f"lane.{lane_name}.forwarder: service_name={lane.forwarder.service_name} bind_host={lane.forwarder.bind_host} listen_port={lane.forwarder.listen_port or lane.backend_port}")
    typer.echo(f"abuse.enabled: {cfg.abuse.enabled}")
    typer.echo(f"abuse.threshold_sec: {cfg.abuse.threshold_sec}")
    typer.echo(f"abuse.grace_sec: {cfg.abuse.grace_sec}")


@db_app.command("ping")
def db_ping(config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml.")) -> None:
    """Ping PostgreSQL without creating schema or mutating state."""
    ok, message = db_service.ping(_load(config))
    if ok:
        typer.echo("OK")
        return
    typer.echo(message)
    raise typer.Exit(1)


@db_app.command("status")
def db_status(config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml.")) -> None:
    """Show read-only PostgreSQL schema/runtime status."""
    result = db_service.status(_load(config))
    if not result.ok:
        typer.echo(result.message)
        raise typer.Exit(1)
    typer.echo("database: OK")
    typer.echo(f"alembic_version: {result.alembic_version}")
    typer.echo(f"public_table_count: {result.public_table_count}")
    typer.echo(f"lanes: {result.lanes}")
    typer.echo(f"customers: {result.customers}")
    typer.echo(f"job_runs: {result.job_runs}")
    typer.echo(f"firewall_applies: {result.firewall_applies}")
    typer.echo(f"abuse_states: {result.abuse_states}")


@lanes_app.command("list")
def lanes_list(config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml.")) -> None:
    """List lanes read-only from DB, falling back to config if DB is empty."""
    result = lane_service.list_lane_status(_load(config))
    if not result.ok:
        typer.echo(result.message)
        raise typer.Exit(1)
    typer.echo(result.message)
    if not result.lanes:
        typer.echo("no lanes")
        return
    for lane in result.lanes:
        typer.echo(f"{lane.name}\tenabled={lane.enabled}\tbackend_port={lane.backend_port}\tchain_prefix={lane.chain_prefix}\tprotocol={lane.protocol}\tsource={lane.source}")


@customer_app.command("list")
def customer_list(config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml."), limit: int = typer.Option(100, "--limit", min=1, max=1000, help="Maximum rows to show."), lane: str | None = typer.Option(None, "--lane"), status: str | None = typer.Option(None, "--status"), include_deleted: bool = typer.Option(False, "--include-deleted")) -> None:
    """List customers read-only. Customer mutation belongs to Phase 5."""
    result = customer_read_service.list_customer_status(_load(config), lane=lane, status=status, include_deleted=include_deleted, limit=limit)
    if not result.ok:
        typer.echo(result.message)
        raise typer.Exit(1)
    if not result.customers:
        if not include_deleted and status is None:
            typer.echo("no non-deleted customers; use --include-deleted to show deleted rows")
        else:
            typer.echo("no customers")
    for customer in result.customers:
        line = f"{customer.id}	{customer.customer_key}	{customer.lane}	{customer.name}	port={customer.port}	status={customer.status}	activation_mode={customer.activation_mode}	expires_at={customer.expires_at}"
        if customer.deleted_at:
            line += f"	deleted_at={customer.deleted_at}"
        typer.echo(line)
    typer.echo("firewall_change: no")
    typer.echo("nat_change: no")
    typer.echo("runtime_change: no")


@customer_app.command("show")
def customer_show(config: Path | None = typer.Option(None, "--config", "-c"), customer_key: str | None = typer.Option(None, "--customer-key"), customer_id: int | None = typer.Option(None, "--id"), port: int | None = typer.Option(None, "--port")) -> None:
    if sum(x is not None for x in (customer_key, customer_id, port)) != 1:
        typer.echo("provide exactly one target: --customer-key or --id or --port")
        raise typer.Exit(1)
    result = customer_read_service.show_customer(_load(config), customer_key=customer_key, customer_id=customer_id, port=port)
    if not result.ok or not result.customer:
        typer.echo(result.message)
        raise typer.Exit(1)
    c = result.customer
    for k in ("id","customer_key","lane","name","port","status","activation_mode","service_days","activated_at","starts_at","expires_at","first_connected_at","expired_at","delete_eligible_at","deleted_at","auto_expire_enabled","auto_delete_enabled","lifecycle_note","miners","farms","maxconn","rate_per_min","burst","ips_mode","abuse_exempt","abuse_exempt_reason","abuse_exempt_until","abuse_exempt_by"):
        typer.echo(f"{k}: {getattr(c, k)}")
    if c.ips_mode == "whitelist":
        typer.echo(f"enabled_ip_pins: {','.join(c.enabled_ip_pins) if c.enabled_ip_pins else '-'}")
    typer.echo("firewall_change: no")
    typer.echo("nat_change: no")
    typer.echo("runtime_change: no")


@customer_app.command("next-port")
def customer_next_port(config: Path | None = typer.Option(None, "--config", "-c"), lane: str = typer.Option(..., "--lane"), start: int = typer.Option(20000, "--start"), end: int = typer.Option(59999, "--end")) -> None:
    result = customer_read_service.suggest_next_customer_port(_load(config), lane=lane, start=start, end=end)
    if not result.ok or not result.suggestion:
        typer.echo(result.message)
        raise typer.Exit(1)
    s = result.suggestion
    typer.echo(f"lane: {s.lane}")
    typer.echo(f"lane_enabled: {s.lane_enabled}")
    typer.echo(f"suggested_port: {s.suggested_port}")
    typer.echo(f"checked_range: {s.checked_range}")
    typer.echo(f"occupied_count: {s.occupied_count}")
    typer.echo(f"skipped_reserved_count: {s.skipped_reserved_count}")
    typer.echo("firewall_change: no")
    typer.echo("nat_change: no")
    typer.echo("runtime_change: no")


@customer_app.command("expiring")
def customer_expiring(config: Path | None = typer.Option(None, "--config", "-c"), within_days: int = typer.Option(7, "--within-days"), include_paused: bool = typer.Option(False, "--include-paused"), limit: int = typer.Option(100, "--limit")) -> None:
    result = customer_read_service.report_expiring_customers(_load(config), within_days=within_days, include_paused=include_paused, limit=limit)
    if not result.ok:
        typer.echo(result.message)
        raise typer.Exit(1)
    if not result.rows:
        typer.echo("no expiring customers in window")
    for r in result.rows:
        typer.echo(f"{r.customer_key}\t{r.lane}\t{r.name}\tport={r.port}\tstatus={r.status}\texpires_at={r.expires_at}\tdays_remaining={r.days_remaining}")
    typer.echo("firewall_change: no")
    typer.echo("nat_change: no")
    typer.echo("runtime_change: no")


@customer_app.command("expired")
def customer_expired(config: Path | None = typer.Option(None, "--config", "-c"), include_deleted: bool = typer.Option(False, "--include-deleted"), limit: int = typer.Option(100, "--limit")) -> None:
    result = customer_read_service.report_expired_customers(_load(config), include_deleted=include_deleted, limit=limit)
    if not result.ok:
        typer.echo(result.message)
        raise typer.Exit(1)
    if not result.rows:
        typer.echo("no expired customers")
    for r in result.rows:
        typer.echo(f"{r.customer_key}\t{r.lane}\t{r.name}\tport={r.port}\tstatus={r.status}\texpires_at={r.expires_at}\texpired_at={r.expired_at}")
    typer.echo("firewall_change: no")
    typer.echo("nat_change: no")
    typer.echo("runtime_change: no")


@customer_app.command("delete-eligible")
def customer_delete_eligible(config: Path | None = typer.Option(None, "--config", "-c"), limit: int = typer.Option(100, "--limit")) -> None:
    result = customer_read_service.report_delete_eligible_customers(_load(config), limit=limit)
    if not result.ok:
        typer.echo(result.message)
        raise typer.Exit(1)
    if not result.rows:
        typer.echo("no delete-eligible customers")
    for r in result.rows:
        typer.echo(f"{r.customer_key}\t{r.lane}\t{r.name}\tport={r.port}\tstatus={r.status}\texpires_at={r.expires_at}\tdelete_eligible_at={r.delete_eligible_at}")
    typer.echo("firewall_change: no")
    typer.echo("nat_change: no")
    typer.echo("runtime_change: no")


@customer_app.command("policies")
def customer_policies(config: Path | None = typer.Option(None, "--config", "-c"), customer_key: str | None = typer.Option(None, "--customer-key"), customer_id: int | None = typer.Option(None, "--id"), port: int | None = typer.Option(None, "--port"), limit: int = typer.Option(50, "--limit")) -> None:
    result = customer_read_service.customer_policy_history(_load(config), customer_key=customer_key, customer_id=customer_id, port=port, limit=limit)
    if not result.ok:
        typer.echo(result.message)
        raise typer.Exit(1)
    if not result.rows:
        typer.echo("no customer policy history")
    for r in result.rows:
        for k in ("customer_id", "customer_key", "lane", "port", "policy_id", "version", "is_current", "miners", "farms", "maxconn", "rate_per_min", "burst", "ips_mode", "abuse_exempt", "abuse_exempt_reason", "abuse_exempt_until", "abuse_exempt_by", "created_at", "created_by", "reason"):
            typer.echo(f"{k}: {r.get(k)}")
    typer.echo("firewall_change: no")
    typer.echo("nat_change: no")
    typer.echo("runtime_change: no")


@customer_app.command("events")
def customer_events(config: Path | None = typer.Option(None, "--config", "-c"), customer_key: str | None = typer.Option(None, "--customer-key"), customer_id: int | None = typer.Option(None, "--id"), port: int | None = typer.Option(None, "--port"), limit: int = typer.Option(50, "--limit")) -> None:
    result = customer_read_service.customer_events_history(_load(config), customer_key=customer_key, customer_id=customer_id, port=port, limit=limit)
    if not result.ok:
        typer.echo(result.message)
        raise typer.Exit(1)
    if not result.rows:
        typer.echo("no customer events")
    for r in result.rows:
        for k in ("id", "event_type", "severity", "subject_type", "subject_id", "message", "data_json", "created_at", "created_by", "correlation_id"):
            typer.echo(f"{k}: {r.get(k)}")
    typer.echo("firewall_change: no")
    typer.echo("nat_change: no")
    typer.echo("runtime_change: no")


@customer_app.command("audit")
def customer_audit(config: Path | None = typer.Option(None, "--config", "-c"), customer_key: str | None = typer.Option(None, "--customer-key"), customer_id: int | None = typer.Option(None, "--id"), port: int | None = typer.Option(None, "--port"), limit: int = typer.Option(50, "--limit")) -> None:
    result = customer_read_service.customer_audit_history(_load(config), customer_key=customer_key, customer_id=customer_id, port=port, limit=limit)
    if not result.ok:
        typer.echo(result.message)
        raise typer.Exit(1)
    if not result.rows:
        typer.echo("no customer audit history")
    for r in result.rows:
        for k in ("id", "actor_type", "actor_id", "action", "resource_type", "resource_id", "before_json", "after_json", "reason", "created_at", "correlation_id"):
            typer.echo(f"{k}: {r.get(k)}")
    typer.echo("firewall_change: no")
    typer.echo("nat_change: no")
    typer.echo("runtime_change: no")


def _guard_customer_write_local_peer(cfg, command_hint: str) -> None:
    message = write_local_peer_root_guard_message(cfg.database.url, command_hint=command_hint)
    if message:
        typer.echo(message)
        raise typer.Exit(1)


def _guard_customer_mutation(cfg, *, command_base: str, yes: bool) -> None:
    command_hint = f"{command_base} --yes" if yes else command_base
    _guard_customer_write_local_peer(cfg, command_hint)


def _emit_customer_mutation_result(result) -> None:
    typer.echo(f"ok: {result.ok}")
    typer.echo(f"message: {result.message}")
    typer.echo(f"firewall_change: {result.firewall_change}")
    typer.echo(f"nat_change: {result.nat_change}")
    typer.echo(f"runtime_change: {result.runtime_change}")
    typer.echo(f"customer_key: {result.customer_key}")
    typer.echo(f"customer_id: {result.customer_id}")
    typer.echo(f"would_create_customer: {result.would_create_customer}")
    typer.echo(f"would_mutate_customer: {result.would_mutate_customer}")
    typer.echo(f"would_create_policy_version: {result.would_create_policy_version}")
    typer.echo(f"would_mutate_ip_pins: {result.would_mutate_ip_pins}")
    typer.echo(f"would_create_event: {result.would_create_event}")
    typer.echo(f"would_create_audit: {result.would_create_audit}")


@customer_app.command("add")
def customer_add(config: Path | None = typer.Option(None, "--config", "-c"), lane: str = typer.Option(..., "--lane"), name: str = typer.Option(..., "--name"), customer_key: str = typer.Option(..., "--customer-key"), port: int = typer.Option(..., "--port"), miners: int = typer.Option(..., "--miners"), farms: int = typer.Option(..., "--farms"), maxconn: int = typer.Option(..., "--maxconn"), rate_per_min: int = typer.Option(..., "--rate-per-min"), burst: int = typer.Option(..., "--burst"), status: str = typer.Option("active", "--status"), activation_mode: str = typer.Option("immediate", "--activation-mode"), service_days: int = typer.Option(30, "--service-days"), ips_mode: str = typer.Option("any", "--ips-mode"), ip: list[str] = typer.Option(None, "--ip"), reason: str | None = typer.Option(None, "--reason"), lifecycle_note: str | None = typer.Option(None, "--lifecycle-note"), yes: bool = typer.Option(False, "--yes")) -> None:
    cfg = _load(config)
    _guard_customer_mutation(cfg, command_base="/usr/local/bin/mpf customer add ...", yes=yes)
    req = CustomerCreateRequest(lane=lane, name=name, customer_key=customer_key, port=port, status=status, policy=CustomerPolicyInput(miners=miners, farms=farms, maxconn=maxconn, rate_per_min=rate_per_min, burst=burst, ips_mode=ips_mode, ip_whitelist=ip or [], reason=reason), lifecycle=CustomerLifecycleInput(activation_mode=activation_mode, service_days=service_days, lifecycle_note=lifecycle_note))
    result = customer_mutation_service.create_db_only_customer(cfg, req, dry_run=not yes)
    _emit_customer_mutation_result(result)
    if not result.ok:
        raise typer.Exit(1)


@customer_app.command("update")
def customer_update(config: Path | None = typer.Option(None, "--config", "-c"), customer_key: str = typer.Option(..., "--customer-key"), lane: str | None = typer.Option(None, "--lane"), name: str | None = typer.Option(None, "--name"), status: str | None = typer.Option(None, "--status"), miners: int | None = typer.Option(None, "--miners"), farms: int | None = typer.Option(None, "--farms"), maxconn: int | None = typer.Option(None, "--maxconn"), rate_per_min: int | None = typer.Option(None, "--rate-per-min"), burst: int | None = typer.Option(None, "--burst"), reason: str | None = typer.Option(None, "--reason"), yes: bool = typer.Option(False, "--yes")) -> None:
    cfg = _load(config)
    _guard_customer_mutation(cfg, command_base="/usr/local/bin/mpf customer update ...", yes=yes)
    policy = None
    provided = [x is not None for x in (miners, farms, maxconn, rate_per_min, burst)]
    if any(provided) and not all(provided):
        typer.echo("policy update requires all fields together: --miners --farms --maxconn --rate-per-min --burst")
        raise typer.Exit(1)
    if all(provided):
        policy = CustomerPolicyInput(miners=miners, farms=farms, maxconn=maxconn, rate_per_min=rate_per_min, burst=burst, ips_mode="any", reason=reason)
    result = customer_mutation_service.update_db_only_customer(cfg, CustomerUpdateRequest(customer_key=customer_key, lane=lane, name=name, status=status, policy=policy), dry_run=not yes)
    _emit_customer_mutation_result(result)
    if not result.ok:
        raise typer.Exit(1)


@customer_app.command("renew")
def customer_renew(config: Path | None = typer.Option(None, "--config", "-c"), customer_key: str = typer.Option(..., "--customer-key"), service_days: int = typer.Option(..., "--service-days"), lifecycle_note: str | None = typer.Option(None, "--lifecycle-note"), yes: bool = typer.Option(False, "--yes")) -> None:
    cfg = _load(config)
    _guard_customer_mutation(cfg, command_base="/usr/local/bin/mpf customer renew ...", yes=yes)
    result = customer_mutation_service.renew_db_only_customer(cfg, CustomerRenewRequest(customer_key=customer_key, service_days=service_days, lifecycle_note=lifecycle_note), dry_run=not yes)
    _emit_customer_mutation_result(result)
    if not result.ok:
        raise typer.Exit(1)


@customer_app.command("disable")
def customer_disable(config: Path | None = typer.Option(None, "--config", "-c"), customer_key: str = typer.Option(..., "--customer-key"), reason: str | None = typer.Option(None, "--reason"), yes: bool = typer.Option(False, "--yes")) -> None:
    cfg = _load(config)
    _guard_customer_mutation(cfg, command_base="/usr/local/bin/mpf customer disable ...", yes=yes)
    result = customer_mutation_service.disable_db_only_customer(cfg, CustomerDisableRequest(customer_key=customer_key, reason=reason), dry_run=not yes)
    _emit_customer_mutation_result(result)
    if not result.ok:
        raise typer.Exit(1)


@customer_app.command("delete")
def customer_delete(config: Path | None = typer.Option(None, "--config", "-c"), customer_key: str = typer.Option(..., "--customer-key"), reason: str | None = typer.Option(None, "--reason"), yes: bool = typer.Option(False, "--yes")) -> None:
    cfg = _load(config)
    _guard_customer_mutation(cfg, command_base="/usr/local/bin/mpf customer delete ...", yes=yes)
    result = customer_mutation_service.soft_delete_db_only_customer(cfg, CustomerDeleteRequest(customer_key=customer_key, reason=reason), dry_run=not yes)
    _emit_customer_mutation_result(result)
    if not result.ok:
        raise typer.Exit(1)


@customer_app.command("set-ips")
def customer_set_ips(config: Path | None = typer.Option(None, "--config", "-c"), customer_key: str = typer.Option(..., "--customer-key"), ips_mode: str = typer.Option(..., "--ips-mode"), ip: list[str] = typer.Option(None, "--ip"), yes: bool = typer.Option(False, "--yes")) -> None:
    cfg = _load(config)
    _guard_customer_mutation(cfg, command_base="/usr/local/bin/mpf customer set-ips ...", yes=yes)
    result = customer_mutation_service.set_ips_db_only_customer(cfg, CustomerSetIpsRequest(customer_key=customer_key, ips_mode=ips_mode, ip_whitelist=ip or []), dry_run=not yes)
    _emit_customer_mutation_result(result)
    if not result.ok:
        raise typer.Exit(1)



@jobs_app.command("status")
def jobs_status(config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml."), limit: int = typer.Option(20, "--limit", min=1, max=100, help="Maximum rows to show.")) -> None:
    """Show recent job status read-only. Running jobs belongs to later phases."""
    result = job_service.list_job_status(_load(config), limit=limit)
    if not result.ok:
        typer.echo(result.message)
        raise typer.Exit(1)
    if not result.jobs:
        typer.echo("no job runs")
        return
    for job in result.jobs:
        typer.echo(f"{job.id}\t{job.job_name}\tstatus={job.status}\tstarted_at={job.started_at}\tfinished_at={job.finished_at}\tduration_ms={job.duration_ms}")


@proxy_app.command("doctor")
def proxy_doctor(config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml.")) -> None:
    """Run read-only Phase 4 proxy doctor checks."""
    _emit_health_report(proxy_doctor_service.run(_config_path(config)))


@proxy_app.command("status")
def proxy_status(config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml.")) -> None:
    """Inspect proxy status without starting or stopping containers."""
    _emit_health_report(proxy_doctor_service.status(_config_path(config)))


@proxy_app.command("config-check")
def proxy_config_check(config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml.")) -> None:
    """Validate proxy planning config without runtime activation."""
    _emit_health_report(proxy_doctor_service.config_check(_config_path(config)))




@firewall_app.command("apply-gate-readiness")
def firewall_apply_gate_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: str = typer.Option("human", "--output")) -> None:
    """Render non-authorizing Phase 6 apply gate readiness report (read-only)."""
    cfg = _load(config)
    report = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg, include_manual_canary_server_evidence_summary=True, include_phase6_final_acceptance_summary=True, include_phase6_final_acceptance_review_summary=True, include_phase6_operator_acceptance_decision_summary=True)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    for key in (
        "component","final_decision","future_gate","documentation_boundary_present","farm5_0_1_88_sync_evidence_present",
        "current_state_preserved","apply_mode_plan_only","runtime_activation_allowed","production_traffic","firewall_apply_allowed","abuse_automation_allowed",
        "live_firewall_read_allowed","live_firewall_write_allowed","iptables_save_allowed","iptables_restore_allowed",
        "real_adapter_allowed","subprocess_firewall_calls_allowed","customer_nat_allowed","customer_firewall_rules_allowed",
        "restore_lock_record_readiness_present","restore_lock_record_readiness_authorization_status","restore_lock_record_readiness_final_decision",
        "restore_lock_record_gate_present","restore_lock_record_gate_authorization_status","restore_lock_record_gate_final_decision","next_operator_action",
        "restore_lock_record_acceptance_gate_present","restore_lock_record_acceptance_gate_authorization_status","restore_lock_record_acceptance_gate_final_decision",
        "restore_lock_record_execution_gate_present", "restore_lock_record_execution_gate_authorization_status", "restore_lock_record_execution_gate_final_decision", "restore_lock_record_execution_gate_execution_allowed",
    ):
        value = report[key]
        if isinstance(value, bool):
            value = str(value).lower()
        typer.echo(f"{key}: {value}")
    missing = report["missing_requirements"]
    blockers = report["blockers"]
    typer.echo(f"missing_requirements: {', '.join(missing) if missing else '-'}")
    typer.echo(f"blockers: {', '.join(blockers) if blockers else '-'}")



@firewall_app.command("restore-lock-record-gate")
def firewall_restore_lock_record_gate(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    """Render report-only restore/lock/DB apply-record gate report for future gate review."""
    cfg = _load(config)
    report = firewall_restore_lock_record_gate_service.build_restore_lock_record_gate_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    for key in (
        "component", "final_decision", "authorization_status", "inspection_only", "report_only",
        "gate_status", "preflight_only",
        "proposal_boundary_present", "read_only_snapshot_evidence_present",
        "restore_point_write_allowed", "lock_acquisition_allowed", "db_apply_record_write_allowed",
        "iptables_restore_allowed", "customer_nat_allowed", "customer_firewall_rules_allowed",
        "apply_decision", "next_required_gate",
    ):
        value = report[key]
        if isinstance(value, bool):
            value = str(value).lower()
        typer.echo(f"{key}: {value}")
    for key in ("blockers", "warnings", "errors"):
        values = report[key]
        typer.echo(f"{key}: {', '.join(values) if values else '-'}")


@firewall_app.command("restore-lock-record-readiness")
def firewall_restore_lock_record_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    """Render report-only restore/lock/DB apply-record readiness for future gate review."""
    cfg = _load(config)
    report = firewall_restore_lock_record_readiness_service.build_restore_lock_record_readiness_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    for key in (
        "component", "final_decision", "authorization_status", "inspection_only", "report_only",
        "read_only_snapshot_gate_authorized", "read_only_snapshot_evidence_present",
        "restore_point_write_allowed", "lock_acquisition_allowed", "db_apply_record_write_allowed",
        "iptables_restore_allowed", "customer_nat_allowed", "customer_firewall_rules_allowed",
        "apply_decision", "next_required_gate",
    ):
        value = report[key]
        if isinstance(value, bool):
            value = str(value).lower()
        typer.echo(f"{key}: {value}")
    for key in ("blockers", "warnings", "errors"):
        values = report[key]
        typer.echo(f"{key}: {', '.join(values) if values else '-'}")


@firewall_app.command("restore-lock-record-execution-gate")
def firewall_restore_lock_record_execution_gate(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output"), execute_controlled_boundary: bool = typer.Option(False, "--execute-controlled-boundary"), operator: str | None = typer.Option(None, "--operator"), reason: str | None = typer.Option(None, "--reason"), yes: bool = typer.Option(False, "--yes")) -> None:
    """Render controlled boundary report or execute guarded restore/lock/db-apply-record writes."""
    cfg = _load(config)
    report = firewall_restore_lock_record_execution_gate_service.run_restore_lock_record_controlled_execution(cfg, execute_controlled_boundary=execute_controlled_boundary, operator=operator, reason=reason, yes=yes)
    if execute_controlled_boundary and (not operator or not reason or not yes):
        if output == "json":
            typer.echo(json.dumps(report, indent=2, sort_keys=True))
        else:
            typer.echo("controlled execution arguments are incomplete")
        raise typer.Exit(1)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    for key in (
        "component", "final_decision", "gate_status", "authorization_status", "inspection_only", "report_only", "preflight_only", "dry_run", "execute_controlled_boundary", "execution_allowed",
        "controlled_boundary_accepted", "farm5_time_sync_resolved",
        "restore_point_write_allowed", "restore_point_written", "lock_acquisition_allowed", "lock_acquired", "db_apply_record_write_allowed", "db_apply_record_written", "iptables_restore_allowed",
        "customer_nat_allowed", "customer_firewall_rules_allowed", "apply_decision", "next_required_gate",
    ):
        value = report[key]
        if isinstance(value, bool):
            value = str(value).lower()
        typer.echo(f"{key}: {value}")
    for key in ("blockers", "errors"):
        values = report[key]
        typer.echo(f"{key}: {', '.join(values) if values else '-'}")


@firewall_app.command("no-customer-apply-scaffold")
def firewall_no_customer_apply_scaffold(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    """Render report-only scaffold for future no-customer apply/verify/rollback lifecycle."""
    cfg = _load(config)
    report = firewall_no_customer_apply_scaffold_service.build_no_customer_apply_scaffold_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    for key in (
        "component",
        "final_decision",
        "authorization_status",
        "gate_status",
        "execution_allowed",
        "apply_decision",
        "verify_decision",
        "rollback_decision",
        "production_traffic",
        "firewall_apply_allowed",
        "live_snapshot_read_allowed",
        "restore_lock_record_execution_allowed",
        "customer_nat_allowed",
        "customer_firewall_rules_allowed",
        "iptables_restore_allowed",
    ):
        value = report[key]
        if isinstance(value, bool):
            value = str(value).lower()
        typer.echo(f"{key}: {value}")
    for key in ("blockers", "errors"):
        values = report[key]
        typer.echo(f"{key}: {', '.join(values) if values else '-'}")

@firewall_app.command("no-customer-apply-acceptance-gate")
def firewall_no_customer_apply_acceptance_gate(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    """Render report-only explicit acceptance gate for future no-customer apply/verify/rollback."""
    cfg = _load(config)
    report = firewall_no_customer_apply_acceptance_gate_service.build_no_customer_apply_acceptance_gate_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    for key in (
        "component","final_decision","authorization_status","gate_status","execution_allowed","apply_decision","verify_decision","rollback_decision",
        "production_traffic","firewall_apply_allowed","live_snapshot_read_allowed","restore_lock_record_execution_allowed",
        "no_customer_apply_scaffold_report_present","no_customer_apply_scaffold_blocked","no_customer_apply_scaffold_execution_disallowed",
        "no_customer_apply_scaffold_mutation_flags_false","customer_nat_allowed","customer_firewall_rules_allowed","iptables_restore_allowed",
    ):
        value = report[key]
        if isinstance(value, bool):
            value = str(value).lower()
        typer.echo(f"{key}: {value}")
    for key in ("blockers", "errors"):
        values = report[key]
        typer.echo(f"{key}: {', '.join(values) if values else '-'}")



@firewall_app.command("no-customer-apply-execution-gate")
def firewall_no_customer_apply_execution_gate(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    """Render report-only execution gate for future controlled no-customer apply/verify/rollback."""
    cfg = _load(config)
    report = firewall_no_customer_apply_execution_gate_service.build_no_customer_apply_execution_gate_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    for key in (
        "component","final_decision","authorization_status","gate_status","execution_allowed","apply_decision","verify_decision","rollback_decision",
        "production_traffic","firewall_apply_allowed","live_snapshot_read_allowed","restore_lock_record_execution_allowed",
        "no_customer_apply_scaffold_report_present","no_customer_apply_acceptance_gate_report_present","no_customer_apply_acceptance_gate_server_evidence_present",
        "no_customer_apply_scaffold_blocked","no_customer_apply_acceptance_gate_blocked","no_customer_apply_scaffold_execution_disallowed",
        "no_customer_apply_acceptance_gate_execution_disallowed","no_customer_apply_scaffold_mutation_flags_false","no_customer_apply_acceptance_gate_mutation_flags_false",
        "customer_nat_allowed","customer_firewall_rules_allowed","iptables_restore_allowed",
    ):
        value = report[key]
        if isinstance(value, bool):
            value = str(value).lower()
        typer.echo(f"{key}: {value}")
    for key in ("blockers", "errors"):
        values = report[key]
        typer.echo(f"{key}: {', '.join(values) if values else '-'}")


@firewall_app.command("no-customer-apply-package")
def firewall_no_customer_apply_package(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    cfg = _load(config)
    report = firewall_no_customer_apply_package_service.build_no_customer_apply_package_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True)); return
    for key in ("component","final_decision","authorization_status","package_status","execution_allowed","apply_decision","verify_decision","rollback_decision","payload_kind","payload_contains_customer_nat","payload_contains_customer_firewall_rules","payload_contains_production_traffic","payload_contains_iptables_restore","payload_contains_subprocess_call","payload_contains_db_write","payload_contains_file_write"):
        v=report[key]; typer.echo(f"{key}: {str(v).lower() if isinstance(v,bool) else v}")
    for key in ("blockers","errors"):
        vals=report[key]; typer.echo(f"{key}: {', '.join(vals) if vals else '-'}")

@firewall_app.command("no-customer-apply-execution-acceptance")
def firewall_no_customer_apply_execution_acceptance(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    cfg = _load(config)
    report = firewall_no_customer_apply_execution_acceptance_service.build_no_customer_apply_execution_acceptance_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True)); return
    for key in ("component","final_decision","authorization_status","gate_status","execution_allowed","apply_decision","verify_decision","rollback_decision","no_customer_apply_execution_gate_report_present","no_customer_apply_execution_gate_blocked","no_customer_apply_execution_gate_execution_disallowed","no_customer_apply_execution_gate_mutation_flags_false","no_customer_apply_package_report_present","no_customer_apply_package_blocked","no_customer_apply_package_execution_disallowed","no_customer_apply_package_mutation_flags_false","no_customer_apply_package_customer_safe","customer_nat_allowed","customer_firewall_rules_allowed","iptables_restore_allowed"):
        v=report[key]; typer.echo(f"{key}: {str(v).lower() if isinstance(v,bool) else v}")
    for key in ("blockers","errors"):
        vals=report[key]; typer.echo(f"{key}: {', '.join(vals) if vals else '-'}")


@firewall_app.command("no-customer-runtime-execution-approval")
def firewall_no_customer_runtime_execution_approval(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    cfg = _load(config)
    report = firewall_no_customer_runtime_execution_approval_service.build_no_customer_runtime_execution_approval_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True)); return
    for key in ("component","final_decision","authorization_status","gate_status","execution_allowed","operator_approval_required","fresh_farm5_runtime_execution_evidence_required","separate_runtime_execution_pr_required","apply_decision","verify_decision","rollback_decision","farm5_0_1_93_sync_evidence_present","gate_review_json_evidence_present","gate_review_json_blocked","gate_review_json_non_applyable","gate_review_json_live_apply_disallowed","no_customer_apply_package_present","no_customer_apply_package_customer_safe","no_customer_execution_acceptance_present","no_customer_execution_gate_present","apply_gate_readiness_blocked","customer_nat_allowed","customer_firewall_rules_allowed","iptables_restore_allowed"):
        v=report[key]; typer.echo(f"{key}: {str(v).lower() if isinstance(v,bool) else v}")
    for key in ("blockers","errors"):
        vals=report[key]; typer.echo(f"{key}: {', '.join(vals) if vals else '-'}")

@firewall_app.command("restore-lock-record-acceptance-gate")
def firewall_restore_lock_record_acceptance_gate(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    """Render report-only acceptance gate for controlled restore/lock/db-apply behavior."""
    cfg = _load(config)
    report = firewall_restore_lock_record_acceptance_gate_service.build_restore_lock_record_acceptance_gate_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    for key in (
        "component", "final_decision", "gate_status", "authorization_status", "inspection_only", "report_only", "preflight_only", "execution_allowed",
        "farm5_time_sync_evidence_present", "farm5_time_sync_resolved",
        "restore_point_write_allowed", "lock_acquisition_allowed", "db_apply_record_write_allowed", "iptables_restore_allowed",
        "customer_nat_allowed", "customer_firewall_rules_allowed", "apply_decision", "next_required_gate",
    ):
        value = report[key]
        if isinstance(value, bool):
            value = str(value).lower()
        typer.echo(f"{key}: {value}")
    for key in ("blockers", "errors"):
        values = report[key]
        typer.echo(f"{key}: {', '.join(values) if values else '-'}")

@firewall_app.command("live-snapshot-readiness")
def firewall_live_snapshot_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    """Render fail-closed, non-authorizing report for future live snapshot read gate."""
    cfg = _load(config)
    report = firewall_live_snapshot_read_service.build_live_snapshot_read_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    for key, value in report.items():
        if isinstance(value, bool):
            value = str(value).lower()
        if isinstance(value, list):
            value = ", ".join(value) if value else "-"
        typer.echo(f"{key}: {value}")


@firewall_app.command("live-snapshot-read")
def firewall_live_snapshot_read(
    config: Path | None = typer.Option(None, "--config", "-c"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    execute: bool = typer.Option(False, "--execute", help="Execute one explicit read-only iptables-save command."),
) -> None:
    """Render readiness or execute one explicitly-gated read-only live snapshot read."""
    cfg = _load(config)
    report = firewall_live_snapshot_read_service.build_live_snapshot_read_report(cfg, execute=execute)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        if report["final_decision"] in ("FAILED_READ_ONLY_SNAPSHOT", "BLOCKED"):
            raise typer.Exit(1)
        return
    for key, value in report.items():
        if isinstance(value, bool):
            value = str(value).lower()
        if isinstance(value, list):
            value = ", ".join(value) if value else "-"
        typer.echo(f"{key}: {value}")
    if report["final_decision"] in ("FAILED_READ_ONLY_SNAPSHOT", "BLOCKED"):
        raise typer.Exit(1)


@firewall_app.command("live-snapshot-scaffold")
def firewall_live_snapshot_scaffold(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    """Render fail-closed, non-authorizing scaffolding report for future live snapshot read gate."""
    cfg = _load(config)
    report = firewall_live_snapshot_scaffold_service.build_live_snapshot_scaffold_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    for key, value in report.items():
        if isinstance(value, bool):
            value = str(value).lower()
        if isinstance(value, list):
            value = ", ".join(value) if value else "-"
        typer.echo(f"{key}: {value}")

@firewall_app.command("plan")
def firewall_plan(config: Path | None = typer.Option(None, "--config", "-c"), output: str = typer.Option("human", "--output"), source: Literal["db-readonly", "config-only"] = typer.Option("db-readonly", "--source")) -> None:
    """Render a dry-run firewall plan only."""
    cfg = _load(config)
    if source == "config-only":
        result = firewall_planner_service.build_plan_from_config(cfg)
    else:
        try:
            result = firewall_planner_service.build_plan_from_db(cfg)
        except RuntimeError as exc:
            typer.echo(f"ERROR: {exc}")
            raise typer.Exit(1)
    if output == "json":
        typer.echo(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return
    typer.echo(result.to_human())


@firewall_app.command("diff")
def firewall_diff(config: Path | None = typer.Option(None, "--config", "-c"), output: str = typer.Option("human", "--output"), source: Literal["db-readonly", "config-only"] = typer.Option("db-readonly", "--source"), live_snapshot_file: Path | None = typer.Option(None, "--live-snapshot-file", help="Offline iptables-save snapshot file (no live reads).")) -> None:
    """Render a dry-run firewall diff only."""
    cfg = _load(config)
    snapshot = _load_optional_snapshot_file(live_snapshot_file)
    if source == "config-only":
        result = firewall_planner_service.build_plan_from_config_with_live_snapshot(cfg, snapshot) if snapshot is not None else firewall_planner_service.build_plan_from_config(cfg)
    else:
        try:
            result = firewall_planner_service.build_plan_from_db_with_live_snapshot(cfg, snapshot) if snapshot is not None else firewall_planner_service.build_plan_from_db(cfg)
        except RuntimeError as exc:
            typer.echo(f"ERROR: {exc}")
            raise typer.Exit(1)
    if output == "json":
        typer.echo(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return
    typer.echo(result.to_human())




@firewall_app.command("doctor")
def firewall_doctor(config: Path | None = typer.Option(None, "--config", "-c"), output: str = typer.Option("human", "--output"), source: Literal["db-readonly", "config-only"] = typer.Option("db-readonly", "--source"), live_snapshot_file: Path | None = typer.Option(None, "--live-snapshot-file", help="Offline iptables-save snapshot file (no live reads).")) -> None:
    """Render planner-only firewall doctor/coverage report."""
    cfg = _load(config)
    snapshot = _load_optional_snapshot_file(live_snapshot_file)
    if source == "config-only":
        result = firewall_planner_service.build_plan_from_config_with_live_snapshot(cfg, snapshot) if snapshot is not None else firewall_planner_service.build_plan_from_config(cfg)
    else:
        try:
            result = firewall_planner_service.build_plan_from_db_with_live_snapshot(cfg, snapshot) if snapshot is not None else firewall_planner_service.build_plan_from_db(cfg)
        except RuntimeError as exc:
            typer.echo(f"ERROR: {exc}")
            raise typer.Exit(1)
    report = firewall_doctor_service.build_doctor_report(result, snapshot_input="file" if snapshot is not None else "none")
    if output == "json":
        typer.echo(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return
    typer.echo(report.to_human())


@firewall_app.command("render-restore")
def firewall_render_restore(config: Path | None = typer.Option(None, "--config", "-c"), output: str = typer.Option("human", "--output"), source: Literal["db-readonly", "config-only"] = typer.Option("db-readonly", "--source")) -> None:
    """Render offline iptables-restore payload artifact only (no apply)."""
    cfg = _load(config)
    if source == "config-only":
        result = firewall_planner_service.build_plan_from_config(cfg)
    else:
        try:
            result = firewall_planner_service.build_plan_from_db(cfg)
        except RuntimeError as exc:
            typer.echo(f"ERROR: {exc}")
            raise typer.Exit(1)
    contract = firewall_restore_payload_renderer.render_restore_contract(result)
    if output == "payload":
        if not contract.renderable or contract.restore_payload is None:
            raise typer.Exit(1)
        typer.echo(contract.restore_payload.payload, nl=False)
        return
    if output == "json":
        data = contract.to_dict()
        if contract.restore_payload is not None:
            data["payload_sha256"] = contract.restore_payload.payload_sha256
            data["payload_line_count"] = contract.restore_payload.payload_line_count
        typer.echo(json.dumps(data, indent=2, sort_keys=True))
        if not contract.renderable:
            raise typer.Exit(1)
        return

    typer.echo("MPF firewall restore artifact (offline)")
    typer.echo(f"backend: {contract.backend}")
    typer.echo(f"apply_mode: {contract.apply_mode}")
    typer.echo(f"artifact_only: {str(contract.artifact_only).lower()}")
    typer.echo(f"live_apply_allowed: {str(contract.live_apply_allowed).lower()}")
    typer.echo(f"renderable: {str(contract.renderable).lower()}")
    typer.echo(f"firewall_change: {contract.safety_flags['firewall_change']}")
    typer.echo(f"nat_change: {contract.safety_flags['nat_change']}")
    typer.echo(f"runtime_change: {contract.safety_flags['runtime_change']}")
    chain_count = len(result.chains)
    rule_count = len(result.rules)
    typer.echo(f"chains: {chain_count}")
    typer.echo(f"rules: {rule_count}")
    typer.echo(f"warnings: {len(contract.warnings)}")
    typer.echo(f"errors: {len(contract.errors)}")
    if contract.restore_payload is not None:
        typer.echo(f"payload_sha256: {contract.restore_payload.payload_sha256}")
        typer.echo(f"payload_line_count: {contract.restore_payload.payload_line_count}")
    for w in contract.warnings:
        typer.echo(f"WARNING [{w.code}] {w.message}")
    for e in contract.errors:
        typer.echo(f"ERROR [{e.code}] {e.message}")
    if not contract.renderable:
        raise typer.Exit(1)


@firewall_app.command("apply-contract")
def firewall_apply_contract(config: Path | None = typer.Option(None, "--config", "-c"), output: str = typer.Option("human", "--output"), source: Literal["db-readonly", "config-only"] = typer.Option("db-readonly", "--source")) -> None:
    """Render offline apply-readiness contract only (no apply, no rollback, no verify execution)."""
    cfg = _load(config)
    if source == "config-only":
        result = firewall_planner_service.build_plan_from_config(cfg)
    else:
        try:
            result = firewall_planner_service.build_plan_from_db(cfg)
        except RuntimeError as exc:
            typer.echo(f"ERROR: {exc}")
            raise typer.Exit(1)
    restore_contract = firewall_restore_payload_renderer.render_restore_contract(result)
    contract = firewall_apply_contract_service.build_apply_readiness_contract(result, restore_contract)
    if output == "json":
        typer.echo(json.dumps(contract.to_dict(), indent=2, sort_keys=True))
        return

    typer.echo("MPF firewall apply contract (offline)")
    typer.echo(f"backend: {contract.backend}")
    typer.echo(f"apply_mode: {contract.apply_mode}")
    typer.echo(f"artifact_only: {str(contract.artifact_only).lower()}")
    typer.echo(f"live_apply_allowed: {str(contract.live_apply_allowed).lower()}")
    typer.echo(f"applyable: {str(contract.applyable).lower()}")
    typer.echo(f"readiness: {contract.readiness}")
    typer.echo(f"restore_point_required: {str(contract.restore_point_contract.restore_point_required).lower()}")
    typer.echo(f"lock_required_for_apply: {str(contract.lock_contract.lock_required_for_apply).lower()}")
    typer.echo(f"verify_required_after_apply: {str(contract.verify_contract.verify_required_after_apply).lower()}")
    typer.echo(f"rollback_artifact_required: {str(contract.rollback_contract.rollback_artifact_required).lower()}")
    typer.echo(f"firewall_change: {contract.safety_flags['firewall_change']}")
    typer.echo(f"nat_change: {contract.safety_flags['nat_change']}")
    typer.echo(f"runtime_change: {contract.safety_flags['runtime_change']}")
    typer.echo(f"warnings: {len(contract.warnings)}")
    typer.echo(f"errors: {len(contract.errors)}")




@firewall_app.command("render-rollback")
def firewall_render_rollback(config: Path | None = typer.Option(None, "--config", "-c"), snapshot_file: Path = typer.Option(..., "--snapshot-file", help="Offline iptables-save snapshot file (required)."), output: str = typer.Option("human", "--output")) -> None:
    """Render offline rollback artifact only (inspection-only, no execution)."""
    _ = _load(config)
    if output not in {"human", "json", "payload"}:
        raise typer.BadParameter("--output must be one of: human, json, payload")
    if not snapshot_file.exists() or not snapshot_file.is_file():
        typer.echo(f"ERROR: unable to read rollback snapshot file: {snapshot_file}: file does not exist")
        raise typer.Exit(code=1)
    try:
        snapshot = firewall_snapshot_parser.parse_iptables_save_file(str(snapshot_file))
    except Exception as exc:
        typer.echo(f"ERROR: unable to parse rollback snapshot file: {snapshot_file}: {exc}")
        raise typer.Exit(code=1)

    contract = firewall_rollback_artifact_renderer.render_rollback_artifact_from_snapshot(snapshot, source="offline_snapshot_file")
    if output == "payload":
        if not contract.renderable or contract.rollback_payload is None:
            raise typer.Exit(code=1)
        typer.echo(contract.rollback_payload.payload, nl=False)
        return
    if output == "json":
        typer.echo(json.dumps(contract.to_dict(), indent=2, sort_keys=True))
        if not contract.renderable:
            raise typer.Exit(code=1)
        return

    typer.echo("MPF firewall rollback artifact (offline)")
    typer.echo(f"backend: {contract.backend}")
    typer.echo(f"artifact_only: {str(contract.artifact_only).lower()}")
    typer.echo(f"inspection_only: {str(contract.inspection_only).lower()}")
    typer.echo(f"rollback_execution_allowed_now: {str(contract.rollback_execution_allowed_now).lower()}")
    typer.echo(f"live_apply_allowed: {str(contract.live_apply_allowed).lower()}")
    typer.echo(f"applyable: {str(contract.applyable).lower()}")
    typer.echo(f"source: {contract.source}")
    typer.echo(f"source_snapshot_sha256: {contract.source_snapshot_hash}")
    typer.echo(f"rollback_payload_sha256: {contract.rollback_payload_sha256}")
    typer.echo(f"rollback_payload_line_count: {contract.rollback_payload_line_count}")
    if contract.rollback_payload is not None:
        typer.echo(f"tables: {contract.rollback_payload.table_count}")
        typer.echo(f"chains: {contract.rollback_payload.chain_count}")
        typer.echo(f"rules: {contract.rollback_payload.rule_count}")
    typer.echo(f"firewall_change: {contract.safety_flags['firewall_change']}")
    typer.echo(f"nat_change: {contract.safety_flags['nat_change']}")
    typer.echo(f"runtime_change: {contract.safety_flags['runtime_change']}")
    typer.echo(f"warnings: {len(contract.warnings)}")
    typer.echo(f"errors: {len(contract.errors)}")
    for w in contract.warnings:
        typer.echo(f"WARNING [{w.code}] {w.message}")
    for e in contract.errors:
        typer.echo(f"ERROR [{e.code}] {e.message}")
    if not contract.renderable:
        raise typer.Exit(code=1)


@firewall_app.command("preflight")
def firewall_preflight(config: Path | None = typer.Option(None, "--config", "-c"), output: str = typer.Option("human", "--output"), source: Literal["db-readonly", "config-only"] = typer.Option("db-readonly", "--source"), rollback_snapshot_file: Path | None = typer.Option(None, "--rollback-snapshot-file", help="Explicit offline iptables-save snapshot file for rollback artifact status.")) -> None:
    """Render offline apply gate preflight/failure matrix (inspection-only)."""
    cfg = _load(config)
    if source == "config-only":
        result = firewall_planner_service.build_plan_from_config(cfg)
    else:
        try:
            result = firewall_planner_service.build_plan_from_db(cfg)
        except RuntimeError as exc:
            typer.echo(f"ERROR: {exc}")
            raise typer.Exit(1)

    rollback_artifact = None
    if rollback_snapshot_file is not None:
        if not rollback_snapshot_file.exists() or not rollback_snapshot_file.is_file():
            typer.echo(f"ERROR: unable to read rollback snapshot file: {rollback_snapshot_file}: file does not exist")
            raise typer.Exit(1)
        try:
            snapshot = firewall_snapshot_parser.parse_iptables_save_file(str(rollback_snapshot_file))
        except Exception as exc:
            typer.echo(f"ERROR: unable to parse rollback snapshot file: {rollback_snapshot_file}: {exc}")
            raise typer.Exit(1)
        rollback_artifact = firewall_rollback_artifact_renderer.render_rollback_artifact_from_snapshot(snapshot, source="offline_snapshot_file")

    report = firewall_preflight_service.build_preflight_report(result, rollback_artifact=rollback_artifact)
    if output == "json":
        typer.echo(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return

    typer.echo("MPF firewall preflight (offline)")
    for k in ("backend","apply_mode","preflight_version","artifact_only","inspection_only","live_apply_allowed","applyable","readiness","final_verdict"):
        v = getattr(report, k)
        typer.echo(f"{k}: {str(v).lower() if isinstance(v, bool) else v}")
    typer.echo(f"planner_customer_source: {report.planner_customer_source}")
    typer.echo(f"db_customer_input_loaded: {str(report.db_customer_input_loaded).lower()}")
    typer.echo(f"restore_payload_renderable: {str(report.restore_payload_renderable).lower()}")
    typer.echo(f"apply_contract_readiness: {report.apply_contract_readiness}")
    typer.echo(f"package_present: {str(report.package_present).lower()}")
    typer.echo(f"rollback_artifact_present: {str(report.rollback_artifact_present).lower()}")
    typer.echo(f"rollback_artifact_renderable: {str(report.rollback_artifact_renderable).lower()}")
    typer.echo(f"restore_point_required: {str(report.restore_point_required).lower()}")
    typer.echo(f"lock_required_for_apply: {str(report.lock_required_for_apply).lower()}")
    typer.echo(f"verify_required_after_apply: {str(report.verify_required_after_apply).lower()}")
    typer.echo(f"rollback_artifact_required: {str(report.rollback_artifact_required).lower()}")
    typer.echo(f"checks: total={report.check_count} ok={report.ok_count} warn={report.warn_count} blocked={report.blocked_count}")
    typer.echo(f"firewall_change: {report.safety_flags['firewall_change']}")
    typer.echo(f"nat_change: {report.safety_flags['nat_change']}")
    typer.echo(f"runtime_change: {report.safety_flags['runtime_change']}")
    for w in report.warnings:
        typer.echo(f"WARNING [{w.code}] {w.message}")
    for e in report.errors:
        typer.echo(f"ERROR [{e.code}] {e.message}")

@firewall_app.command("package")
def firewall_package(config: Path | None = typer.Option(None, "--config", "-c"), output: str = typer.Option("human", "--output"), source: Literal["db-readonly", "config-only"] = typer.Option("db-readonly", "--source")) -> None:
    """Render offline apply package/readiness report only (inspection-only, no apply)."""
    cfg = _load(config)
    if source == "config-only":
        result = firewall_planner_service.build_plan_from_config(cfg)
    else:
        try:
            result = firewall_planner_service.build_plan_from_db(cfg)
        except RuntimeError as exc:
            typer.echo(f"ERROR: {exc}")
            raise typer.Exit(1)
    package = firewall_apply_package_service.build_apply_package_report(result)
    if output == "json":
        typer.echo(json.dumps(package.to_dict(), indent=2, sort_keys=True))
        return

    typer.echo("MPF firewall apply package (offline)")
    typer.echo(f"backend: {package.backend}")
    typer.echo(f"apply_mode: {package.apply_mode}")
    typer.echo(f"package_version: {package.package_version}")
    typer.echo(f"artifact_only: {str(package.artifact_only).lower()}")
    typer.echo(f"inspection_only: {str(package.inspection_only).lower()}")
    typer.echo(f"live_apply_allowed: {str(package.live_apply_allowed).lower()}")
    typer.echo(f"applyable: {str(package.applyable).lower()}")
    typer.echo(f"readiness: {package.readiness}")
    typer.echo(f"planner_customer_source: {package.planner_customer_source}")
    typer.echo(f"db_customer_input_loaded: {str(package.db_customer_input_loaded).lower()}")
    typer.echo(f"chains: {package.chain_count}")
    typer.echo(f"rules: {package.rule_count}")
    typer.echo(f"warnings: {package.warning_count}")
    typer.echo(f"errors: {package.error_count}")
    if package.payload_sha256 is not None:
        typer.echo(f"payload_sha256: {package.payload_sha256}")
    typer.echo(f"payload_line_count: {package.payload_line_count}")
    readiness = package.apply_readiness_contract
    if readiness is not None:
        typer.echo(f"restore_point_required: {str(readiness.restore_point_contract.restore_point_required).lower()}")
        typer.echo(f"lock_required_for_apply: {str(readiness.lock_contract.lock_required_for_apply).lower()}")
        typer.echo(f"verify_required_after_apply: {str(readiness.verify_contract.verify_required_after_apply).lower()}")
        typer.echo(f"rollback_artifact_required: {str(readiness.rollback_contract.rollback_artifact_required).lower()}")
    typer.echo(f"firewall_change: {package.safety_flags['firewall_change']}")
    typer.echo(f"nat_change: {package.safety_flags['nat_change']}")
    typer.echo(f"runtime_change: {package.safety_flags['runtime_change']}")
    for w in package.warnings:
        typer.echo(f"WARNING [{w.code}] {w.message}")
    for e in package.errors:
        typer.echo(f"ERROR [{e.code}] {e.message}")




@firewall_app.command("no-customer-runtime-execution-evidence")
def firewall_no_customer_runtime_execution_evidence(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    """Render controlled no-customer runtime execution evidence package (report-only, non-executing)."""
    cfg = _load(config)
    report = firewall_no_customer_runtime_execution_evidence_service.build_no_customer_runtime_execution_evidence_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    for key in (
        "component", "final_decision", "authorization_status", "evidence_status", "execution_allowed",
        "operator_approval_required", "fresh_farm5_runtime_execution_evidence_required", "separate_runtime_execution_pr_required",
        "apply_decision", "verify_decision", "rollback_decision", "farm5_0_1_94_sync_evidence_present",
        "runtime_approval_report_present", "runtime_approval_report_blocked", "runtime_approval_execution_disallowed",
        "apply_gate_readiness_blocked", "gate_review_json_blocked", "gate_review_json_non_applyable",
        "gate_review_json_live_apply_disallowed", "customer_nat_allowed", "customer_firewall_rules_allowed", "iptables_restore_allowed",
    ):
        v = report.get(key)
        typer.echo(f"{key}: {str(v).lower() if isinstance(v, bool) else v}")
    typer.echo(f"blockers: {len(report.get('blockers', []))}")
    for b in report.get("blockers", []):
        typer.echo(f"BLOCKER: {b}")
    typer.echo(f"errors: {len(report.get('errors', []))}")
    for e in report.get("errors", []):
        typer.echo(f"ERROR: {e}")

@firewall_app.command("manual-canary-customer-proposal")
def firewall_manual_canary_customer_proposal(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    cfg = _load(config)
    report = firewall_manual_canary_customer_proposal_service.build_manual_canary_customer_proposal_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True)); return
    for key in ("component","final_decision","authorization_status","proposal_status","execution_allowed","customer_nat_authorized","customer_firewall_rules_authorized","production_traffic_authorized","operator_approval_required","separate_canary_acceptance_pr_required","fresh_farm5_canary_evidence_required","apply_decision","verify_decision","rollback_decision","farm5_0_1_95_sync_evidence_present","controlled_no_customer_runtime_evidence_present","controlled_no_customer_runtime_evidence_blocked","controlled_no_customer_runtime_evidence_execution_disallowed","apply_gate_readiness_blocked","customer_nat_allowed","customer_firewall_rules_allowed","iptables_restore_allowed"):
        v = report.get(key); typer.echo(f"{key}: {str(v).lower() if isinstance(v, bool) else v}")
    typer.echo(f"blockers: {', '.join(report.get('blockers', [])) if report.get('blockers') else '-'}")
    typer.echo(f"errors: {', '.join(report.get('errors', [])) if report.get('errors') else '-'}")


@firewall_app.command("manual-canary-customer-acceptance-readiness")
def firewall_manual_canary_customer_acceptance_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    cfg = _load(config)
    report = firewall_manual_canary_customer_acceptance_readiness_service.build_manual_canary_customer_acceptance_readiness_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True)); return
    for key in ("component","final_decision","authorization_status","acceptance_status","execution_allowed","customer_nat_authorized","customer_firewall_rules_authorized","production_traffic_authorized","operator_approval_required","separate_canary_server_evidence_pr_required","fresh_farm5_canary_evidence_required","apply_decision","verify_decision","rollback_decision","manual_canary_proposal_present","manual_canary_proposal_blocked","manual_canary_proposal_execution_disallowed","apply_gate_readiness_blocked","customer_nat_allowed","customer_firewall_rules_allowed","iptables_restore_allowed"):
        v = report.get(key); typer.echo(f"{key}: {str(v).lower() if isinstance(v, bool) else v}")
    typer.echo(f"blockers: {', '.join(report.get('blockers', [])) if report.get('blockers') else '-'}")
    typer.echo(f"errors: {', '.join(report.get('errors', [])) if report.get('errors') else '-'}")




@firewall_app.command("manual-canary-customer-server-evidence")
def firewall_manual_canary_customer_server_evidence(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    cfg = _load(config)
    report = firewall_manual_canary_customer_server_evidence_service.build_manual_canary_customer_server_evidence_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True)); return
    for key in ("component","final_decision","authorization_status","server_evidence_status","execution_allowed","customer_nat_authorized","customer_firewall_rules_authorized","production_traffic_authorized","operator_approval_required","fresh_farm5_canary_execution_evidence_required","separate_phase6_final_acceptance_pr_required","apply_decision","verify_decision","rollback_decision","farm5_0_1_96_sync_evidence_present","manual_canary_proposal_blocked","manual_canary_acceptance_readiness_blocked","no_non_deleted_customer_evidence_present","no_customer_nat_redirects_evidenced","no_mpf_customer_ipv4_firewall_references_evidenced","no_mpf_customer_ipv6_firewall_references_evidenced","customer_nat_allowed","customer_firewall_rules_allowed","iptables_restore_allowed"):
        v = report.get(key); typer.echo(f"{key}: {str(v).lower() if isinstance(v, bool) else v}")
    typer.echo(f"blockers: {', '.join(report.get('blockers', [])) if report.get('blockers') else '-'}")
    typer.echo(f"errors: {', '.join(report.get('errors', [])) if report.get('errors') else '-'}")


@phase6_app.command("final-acceptance-readiness")
def phase6_final_acceptance_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    cfg = _load(config)
    report = phase6_final_acceptance_readiness_service.build_phase6_final_acceptance_readiness_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True)); return
    for key in ("component","final_decision","acceptance_status","authorization_status","phase6_acceptance_allowed","execution_allowed","customer_nat_authorized","customer_firewall_rules_authorized","production_traffic_authorized","operator_approval_required","fresh_farm5_final_acceptance_evidence_required","separate_phase6_acceptance_pr_required","farm5_0_1_96_sync_evidence_present","manual_canary_server_evidence_present","manual_canary_server_evidence_blocked","manual_canary_actual_execution_missing","manual_canary_final_gate_not_accepted","abuse_invariant_preserved","phase7_not_started","phase8_not_started"):
        v = report.get(key); typer.echo(f"{key}: {str(v).lower() if isinstance(v, bool) else v}")
    typer.echo(f"blockers: {', '.join(report.get('blockers', [])) if report.get('blockers') else '-'}")
    typer.echo(f"errors: {', '.join(report.get('errors', [])) if report.get('errors') else '-'}")


@phase6_app.command("final-acceptance-review")
def phase6_final_acceptance_review(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    cfg = _load(config)
    report = phase6_final_acceptance_review_service.build_phase6_final_acceptance_review_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True)); return
    for key in ("component","final_decision","review_status","acceptance_status","authorization_status","phase6_acceptance_allowed","execution_allowed","customer_nat_authorized","customer_firewall_rules_authorized","production_traffic_authorized","operator_review_required","fresh_farm5_0_1_99_sync_evidence_required","separate_phase6_acceptance_pr_required","phase7_start_allowed","phase8_start_allowed","farm5_0_1_98_sync_evidence_present","phase5_accepted","phase6_working","manual_canary_server_evidence_done","phase6_final_acceptance_readiness_done","phase6_final_acceptance_readiness_blocked","manual_canary_actual_execution_missing","manual_canary_final_gate_not_accepted","apply_gate_readiness_blocked","gate_review_blocked","gate_review_non_applyable","gate_review_live_apply_disallowed","abuse_invariant_preserved"):
        v = report.get(key); typer.echo(f"{key}: {str(v).lower() if isinstance(v, bool) else v}")
    typer.echo(f"blockers: {', '.join(report.get('blockers', [])) if report.get('blockers') else '-'}")
    typer.echo(f"errors: {', '.join(report.get('errors', [])) if report.get('errors') else '-'}")



@phase6_app.command("operator-acceptance-decision")
def phase6_operator_acceptance_decision(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    cfg = _load(config)
    report = phase6_operator_acceptance_decision_service.build_phase6_operator_acceptance_decision_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True)); return
    for key in ("component","final_decision","acceptance_status","authorization_status","phase6_accepted","phase6_acceptance_allowed","next_phase","phase7_start_allowed","phase8_start_allowed","execution_allowed","customer_nat_authorized","customer_firewall_rules_authorized","production_traffic_authorized","firewall_apply_authorized","iptables_restore_authorized","usage_automation_authorized","abuse_automation_authorized","farm5_0_1_100_sync_evidence_present","phase6_runtime_gates_closed","production_traffic_none","firewall_apply_disallowed","customer_nat_disallowed","customer_firewall_rules_disallowed","abuse_invariant_preserved"):
        v = report.get(key); typer.echo(f"{key}: {str(v).lower() if isinstance(v, bool) else v}")
    typer.echo(f"blockers: {', '.join(report.get('blockers', [])) if report.get('blockers') else '-'}")
    typer.echo(f"errors: {', '.join(report.get('errors', [])) if report.get('errors') else '-'}")

@firewall_app.command("gate-review")
def firewall_gate_review(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output"), source: Literal["db-readonly", "config-only"] = typer.Option("db-readonly", "--source"), rollback_snapshot_file: Path | None = typer.Option(None, "--rollback-snapshot-file", help="Explicit offline iptables-save snapshot file for rollback artifact status.")) -> None:
    """Render offline Phase 6-C2 apply gate review report (inspection-only)."""
    cfg = _load(config)
    rollback_artifact = None
    if rollback_snapshot_file is not None:
        if not rollback_snapshot_file.exists():
            typer.echo(f"ERROR: unable to read rollback snapshot file: {rollback_snapshot_file}: file does not exist")
            raise typer.Exit(1)
        if not rollback_snapshot_file.is_file():
            typer.echo(f"ERROR: unable to read rollback snapshot file: {rollback_snapshot_file}: not a file")
            raise typer.Exit(1)
        try:
            snapshot = firewall_snapshot_parser.parse_iptables_save_file(str(rollback_snapshot_file))
        except Exception as exc:
            typer.echo(f"ERROR: unable to parse rollback snapshot file: {rollback_snapshot_file}: {exc}")
            raise typer.Exit(1)
        rollback_artifact = firewall_rollback_artifact_renderer.render_rollback_artifact_from_snapshot(snapshot, source="offline_snapshot_file")
    try:
        result = firewall_planner_service.build_plan_from_db(cfg) if source == "db-readonly" else firewall_planner_service.build_plan_from_config(cfg)
    except RuntimeError as exc:
        typer.echo(f"ERROR: {exc}")
        raise typer.Exit(code=1)
    evidence = firewall_evidence_service.build_evidence_bundle_report(result, rollback_artifact=rollback_artifact)
    apply_gate_readiness = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg, include_manual_canary_server_evidence_summary=True, include_phase6_final_acceptance_summary=True, include_phase6_final_acceptance_review_summary=True, include_phase6_operator_acceptance_decision_summary=True)
    no_customer_apply_scaffold = firewall_no_customer_apply_scaffold_service.build_no_customer_apply_scaffold_report(cfg)
    no_customer_apply_acceptance_gate = firewall_no_customer_apply_acceptance_gate_service.build_no_customer_apply_acceptance_gate_report(cfg)
    no_customer_apply_execution_gate = firewall_no_customer_apply_execution_gate_service.build_no_customer_apply_execution_gate_report(cfg)
    live_snapshot_scaffold = firewall_live_snapshot_scaffold_service.build_live_snapshot_scaffold_report(cfg)
    live_snapshot_read = firewall_live_snapshot_read_service.build_live_snapshot_read_report(cfg)
    restore_lock_record_gate = firewall_restore_lock_record_gate_service.build_restore_lock_record_gate_report(cfg)
    restore_lock_record_readiness = firewall_restore_lock_record_readiness_service.build_restore_lock_record_readiness_report(cfg)
    restore_lock_record_acceptance_gate = firewall_restore_lock_record_acceptance_gate_service.build_restore_lock_record_acceptance_gate_report(cfg)
    restore_lock_record_execution_gate = firewall_restore_lock_record_execution_gate_service.build_restore_lock_record_execution_gate_report(cfg)
    no_customer_runtime_execution_approval = firewall_no_customer_runtime_execution_approval_service.build_no_customer_runtime_execution_approval_report(cfg)
    report = firewall_gate_review_service.build_gate_review_report(
        evidence=evidence,
        apply_gate_readiness=apply_gate_readiness,
        no_customer_apply_scaffold=no_customer_apply_scaffold,
        no_customer_apply_acceptance_gate=no_customer_apply_acceptance_gate,
        no_customer_apply_execution_gate=no_customer_apply_execution_gate,
        no_customer_runtime_execution_approval=no_customer_runtime_execution_approval,
        live_snapshot_scaffold=live_snapshot_scaffold,
        live_snapshot_read=live_snapshot_read,
        restore_lock_record_gate=restore_lock_record_gate,
        restore_lock_record_readiness=restore_lock_record_readiness,
        restore_lock_record_acceptance_gate=restore_lock_record_acceptance_gate,
        restore_lock_record_execution_gate=restore_lock_record_execution_gate,
    )
    if output == "json":
        typer.echo(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return
    typer.echo("MPF firewall gate review (offline)")
    for k in ("review_version", "backend", "apply_mode", "inspection_only", "artifact_only", "live_apply_allowed", "applyable", "final_decision"):
        typer.echo(f"{k}: {str(getattr(report, k)).lower() if isinstance(getattr(report, k), bool) else getattr(report, k)}")
    pg = report.phase_gate_summary
    typer.echo(f"phase_gate: firewall_apply_allowed={pg['firewall_apply_allowed']} production_traffic={pg['production_traffic']} abuse_automation_allowed={pg['abuse_automation_allowed']}")
    typer.echo("evidence: present")
    rs = report.risk_summary
    typer.echo(f"risk_summary: total={rs['total']} critical={rs['critical']} high={rs['high']} medium={rs['medium']} low={rs['low']} blockers={rs['blockers']} warnings={rs['warnings']}")
    cs = report.checklist_summary
    typer.echo(f"checklist_summary: total={cs['total']} pass={cs['pass']} warn={cs['warn']} blocked={cs['blocked']}")
    typer.echo(f"rollback_readiness: {report.rollback_readiness_summary['status']}")
    typer.echo(f"manual_canary_proposal: {report.apply_gate_readiness_summary.get('manual_canary_customer_proposal_summary',{}).get('manual_canary_customer_proposal_final_decision','-')}")
    typer.echo(f"manual_canary_acceptance: {report.apply_gate_readiness_summary.get('manual_canary_customer_acceptance_readiness_summary',{}).get('manual_canary_customer_acceptance_readiness_final_decision','-')}")
    typer.echo(f"canary_readiness: {report.canary_readiness_summary['status']}")
    typer.echo(f"manual_canary_server_evidence: {report.apply_gate_readiness_summary.get('manual_canary_customer_server_evidence_summary',{}).get('manual_canary_customer_server_evidence_final_decision','-')}")
    typer.echo(f"phase6_final_acceptance_readiness: {report.apply_gate_readiness_summary.get('phase6_final_acceptance_readiness_summary',{}).get('phase6_final_acceptance_readiness_final_decision','-')}\nphase6_final_acceptance_review: {report.apply_gate_readiness_summary.get('phase6_final_acceptance_review_summary',{}).get('phase6_final_acceptance_review_final_decision','-')}")
    typer.echo(f"phase6_operator_acceptance_decision: {report.apply_gate_readiness_summary.get('phase6_operator_acceptance_decision_summary',{}).get('phase6_operator_acceptance_decision_final_decision','-')}")
    agr = report.apply_gate_readiness_summary
    typer.echo("apply_gate_readiness: summary")
    typer.echo(f"  final_decision: {agr.get('final_decision', 'BLOCKED')}")
    typer.echo(f"  documentation_boundary_present: {str(agr.get('documentation_boundary_present', False)).lower()}")
    typer.echo(f"  farm5_0_1_88_sync_evidence_present: {str(agr.get('farm5_0_1_88_sync_evidence_present', False)).lower()}")
    typer.echo(f"  current_state_preserved: {str(agr.get('current_state_preserved', False)).lower()}")
    typer.echo(f"  apply_mode_plan_only: {str(agr.get('apply_mode_plan_only', False)).lower()}")
    typer.echo(f"  runtime_activation_allowed: {str(agr.get('runtime_activation_allowed', False)).lower()}")
    typer.echo(f"  blockers: {len(agr.get('blockers', []))}")
    typer.echo(f"  missing_requirements: {len(agr.get('missing_requirements', []))}")
    ncap = report.apply_gate_readiness_summary.get("no_customer_apply_package_summary", {})
    typer.echo("no_customer_apply_package: summary")
    typer.echo(f"  present: {str(ncap.get('no_customer_apply_package_present', False)).lower()}")
    typer.echo(f"  final_decision: {ncap.get('no_customer_apply_package_final_decision', 'BLOCKED')}")
    typer.echo(f"  authorization_status: {ncap.get('no_customer_apply_package_authorization_status', 'PACKAGE_DEFINED_NOT_EXECUTABLE')}")
    typer.echo(f"  execution_allowed: {str(ncap.get('no_customer_apply_package_execution_allowed', False)).lower()}")
    typer.echo(f"  customer_safe: {str(ncap.get('no_customer_apply_package_customer_safe', True)).lower()}")
    ncaea = report.apply_gate_readiness_summary.get("no_customer_apply_execution_acceptance_summary", {})
    typer.echo("no_customer_apply_execution_acceptance: summary")
    typer.echo(f"  present: {str(ncaea.get('no_customer_apply_execution_acceptance_present', False)).lower()}")
    typer.echo(f"  final_decision: {ncaea.get('no_customer_apply_execution_acceptance_final_decision', 'BLOCKED')}")
    typer.echo(f"  authorization_status: {ncaea.get('no_customer_apply_execution_acceptance_authorization_status', 'EXECUTION_ACCEPTANCE_DEFINED_NOT_EXECUTABLE')}")
    typer.echo(f"  execution_allowed: {str(ncaea.get('no_customer_apply_execution_acceptance_execution_allowed', False)).lower()}")
    ncae = report.apply_gate_readiness_summary.get("no_customer_apply_execution_gate_summary", {})
    typer.echo("no_customer_apply_execution_gate: summary")
    typer.echo(f"  present: {str(ncae.get('no_customer_apply_execution_gate_present', False)).lower()}")
    typer.echo(f"  final_decision: {ncae.get('no_customer_apply_execution_gate_final_decision', 'BLOCKED')}")
    typer.echo(f"  authorization_status: {ncae.get('no_customer_apply_execution_gate_authorization_status', 'NOT_ACCEPTED_FOR_EXECUTION')}")
    typer.echo(f"  execution_allowed: {str(ncae.get('no_customer_apply_execution_gate_execution_allowed', False)).lower()}")
    ncas = report.apply_gate_readiness_summary.get("no_customer_apply_scaffold_summary", {})
    typer.echo("no_customer_apply_scaffold: summary")
    typer.echo(f"  present: {str(ncas.get('no_customer_apply_scaffold_present', False)).lower()}")
    typer.echo(f"  final_decision: {ncas.get('no_customer_apply_scaffold_final_decision', 'BLOCKED')}")
    typer.echo(f"  authorization_status: {ncas.get('no_customer_apply_scaffold_authorization_status', 'NOT_AUTHORIZED_FOR_APPLY')}")
    typer.echo(f"  execution_allowed: {str(ncas.get('no_customer_apply_scaffold_execution_allowed', False)).lower()}")
    ncag = report.apply_gate_readiness_summary.get("no_customer_apply_acceptance_gate_summary", {})
    typer.echo("no_customer_apply_acceptance_gate: summary")
    typer.echo(f"  present: {str(ncag.get('no_customer_apply_acceptance_gate_present', False)).lower()}")
    typer.echo(f"  final_decision: {ncag.get('no_customer_apply_acceptance_gate_final_decision', 'BLOCKED')}")
    typer.echo(f"  authorization_status: {ncag.get('no_customer_apply_acceptance_gate_authorization_status', 'ACCEPTANCE_GATE_DEFINED_NOT_EXECUTABLE')}")
    typer.echo(f"  execution_allowed: {str(ncag.get('no_customer_apply_acceptance_gate_execution_allowed', False)).lower()}")
    ncra = report.apply_gate_readiness_summary.get("no_customer_runtime_execution_approval_summary", {})
    typer.echo("no_customer_runtime_execution_approval: summary")
    typer.echo(f"  present: {str(ncra.get('no_customer_runtime_execution_approval_present', False)).lower()}")
    typer.echo(f"  final_decision: {ncra.get('no_customer_runtime_execution_approval_final_decision', 'BLOCKED')}")
    typer.echo(f"  authorization_status: {ncra.get('no_customer_runtime_execution_approval_authorization_status', 'RUNTIME_EXECUTION_APPROVAL_READY_BUT_NOT_GRANTED')}")
    typer.echo(f"  execution_allowed: {str(ncra.get('no_customer_runtime_execution_approval_execution_allowed', False)).lower()}")
    typer.echo(f"  operator_approval_required: {str(ncra.get('no_customer_runtime_execution_approval_operator_approval_required', True)).lower()}")
    typer.echo(f"  fresh_farm5_runtime_execution_evidence_required: {str(ncra.get('no_customer_runtime_execution_approval_fresh_farm5_runtime_execution_evidence_required', True)).lower()}")
    typer.echo(f"  separate_runtime_execution_pr_required: {str(ncra.get('no_customer_runtime_execution_approval_separate_runtime_execution_pr_required', True)).lower()}")
    ncree = report.apply_gate_readiness_summary.get("no_customer_runtime_execution_evidence_summary", {})
    typer.echo("no_customer_runtime_execution_evidence: summary")
    typer.echo(f"  present: {str(ncree.get('no_customer_runtime_execution_evidence_present', False)).lower()}")
    typer.echo(f"  final_decision: {ncree.get('no_customer_runtime_execution_evidence_final_decision', 'BLOCKED')}")
    typer.echo(f"  authorization_status: {ncree.get('no_customer_runtime_execution_evidence_authorization_status', 'CONTROLLED_NO_CUSTOMER_RUNTIME_EVIDENCE_DEFINED_NOT_EXECUTED')}")
    typer.echo(f"  execution_allowed: {str(ncree.get('no_customer_runtime_execution_evidence_execution_allowed', False)).lower()}")

    lss = report.live_snapshot_scaffold_summary
    typer.echo("live_snapshot_scaffold: summary")
    typer.echo(f"  component: {lss.get('component', '-')}")
    typer.echo(f"  final_decision: {lss.get('final_decision', 'BLOCKED')}")
    typer.echo(f"  authorization_status: {lss.get('authorization_status', 'NOT_AUTHORIZED')}")
    typer.echo(f"  live_firewall_read_executed: {str(lss.get('live_firewall_read_executed', False)).lower()}")
    typer.echo(f"  iptables_save_executed: {str(lss.get('iptables_save_executed', False)).lower()}")
    typer.echo(f"  subprocess_executed: {str(lss.get('subprocess_executed', False)).lower()}")
    typer.echo(f"  firewall_mutation: {str(lss.get('firewall_mutation', False)).lower()}")
    typer.echo(f"  db_mutation: {str(lss.get('db_mutation', False)).lower()}")
    typer.echo(f"  customer_nat_changed: {str(lss.get('customer_nat_changed', False)).lower()}")
    typer.echo(f"  customer_firewall_rules_changed: {str(lss.get('customer_firewall_rules_changed', False)).lower()}")
    typer.echo(f"  production_traffic_changed: {str(lss.get('production_traffic_changed', False)).lower()}")
    typer.echo(f"  blockers: {len(lss.get('blockers', []))}")
    rlr = report.restore_lock_record_gate_summary
    typer.echo("restore_lock_record_gate: summary")
    typer.echo(f"  final_decision: {rlr.get('final_decision', 'BLOCKED')}")
    typer.echo(f"  authorization_status: {rlr.get('authorization_status', 'NOT_ACCEPTED')}")
    rlra = report.restore_lock_record_acceptance_gate_summary
    typer.echo("restore_lock_record_acceptance_gate: summary")
    typer.echo(f"  final_decision: {rlra.get('final_decision', 'BLOCKED')}")
    typer.echo(f"  authorization_status: {rlra.get('authorization_status', 'NOT_ACCEPTED_FOR_EXECUTION')}")
    rlex = report.restore_lock_record_execution_gate_summary
    typer.echo("restore_lock_record_execution_gate: summary")
    typer.echo(f"  final_decision: {rlex.get('final_decision', 'BLOCKED')}")
    typer.echo(f"  authorization_status: {rlex.get('authorization_status', 'NOT_AUTHORIZED_FOR_EXECUTION')}")
    typer.echo(f"  execution_allowed: {str(rlex.get('execution_allowed', False)).lower()}")
    typer.echo(f"  controlled_boundary_accepted: {str(rlex.get('controlled_boundary_accepted', False)).lower()}")
    typer.echo(f"  dry_run: {str(rlex.get('dry_run', True)).lower()}")
    typer.echo(f"  execute_controlled_boundary: {str(rlex.get('execute_controlled_boundary', False)).lower()}")
    typer.echo(f"  restore_point_write_allowed: {str(rlex.get('restore_point_write_allowed', False)).lower()}")
    typer.echo(f"  lock_acquisition_allowed: {str(rlex.get('lock_acquisition_allowed', False)).lower()}")
    typer.echo(f"  db_apply_record_write_allowed: {str(rlex.get('db_apply_record_write_allowed', False)).lower()}")
    typer.echo(f"  report_only: {str(rlex.get('report_only', True)).lower()}")
    typer.echo(f"  preflight_only: {str(rlex.get('preflight_only', True)).lower()}")
    typer.echo(f"  apply_decision: {rlex.get('apply_decision', 'BLOCKED')}")
    typer.echo(f"  report_only: {str(rlr.get('report_only', True)).lower()}")
    typer.echo(f"  apply_decision: {rlr.get('apply_decision', 'BLOCKED')}")
    rlr_ready = report.restore_lock_record_readiness_summary
    typer.echo("restore_lock_record_readiness: summary")
    typer.echo(f"  final_decision: {rlr_ready.get('final_decision', 'BLOCKED')}")
    typer.echo(f"  authorization_status: {rlr_ready.get('authorization_status', 'NOT_AUTHORIZED_FOR_WRITES')}")
    typer.echo(f"  report_only: {str(rlr_ready.get('report_only', True)).lower()}")
    typer.echo(f"  apply_decision: {rlr_ready.get('apply_decision', 'BLOCKED')}")
    lsr = report.live_snapshot_read_summary
    typer.echo("live_snapshot_read: summary")
    typer.echo(f"  component: {lsr.get('component', '-')}")
    typer.echo(f"  final_decision: {lsr.get('final_decision', 'BLOCKED')}")
    typer.echo(f"  authorization_status: {lsr.get('authorization_status', 'NOT_AUTHORIZED')}")
    typer.echo(f"  live_firewall_read_executed: {str(lsr.get('live_firewall_read_executed', False)).lower()}")
    typer.echo(f"  iptables_save_executed: {str(lsr.get('iptables_save_executed', False)).lower()}")
    typer.echo(f"  subprocess_executed: {str(lsr.get('subprocess_executed', False)).lower()}")
    typer.echo(f"  blockers: {len(lsr.get('blockers', []))}")
    typer.echo("abuse_requirement: preserved")
    typer.echo(f"firewall_change: {report.safety_flags['firewall_change']}")
    typer.echo(f"nat_change: {report.safety_flags['nat_change']}")
    typer.echo(f"runtime_change: {report.safety_flags['runtime_change']}")
    for w in report.warnings:
        typer.echo(f"WARNING [{w.code}] {w.message}")
    for e in report.errors:
        typer.echo(f"ERROR [{e.code}] {e.message}")


@firewall_app.command("evidence")
def firewall_evidence(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output"), source: Literal["db-readonly", "config-only"] = typer.Option("db-readonly", "--source"), rollback_snapshot_file: Path | None = typer.Option(None, "--rollback-snapshot-file", help="Explicit offline iptables-save snapshot file for rollback artifact status.")) -> None:
    """Render offline Phase 6-B acceptance evidence bundle (inspection-only)."""
    cfg = _load(config)
    if source == "config-only":
        result = firewall_planner_service.build_plan_from_config(cfg)
    else:
        try:
            result = firewall_planner_service.build_plan_from_db(cfg)
        except RuntimeError as exc:
            typer.echo(f"ERROR: {exc}")
            raise typer.Exit(1)

    rollback_artifact = None
    if rollback_snapshot_file is not None:
        if not rollback_snapshot_file.exists():
            typer.echo(f"ERROR: unable to read rollback snapshot file: {rollback_snapshot_file}: file does not exist")
            raise typer.Exit(1)
        if not rollback_snapshot_file.is_file():
            typer.echo(f"ERROR: unable to read rollback snapshot file: {rollback_snapshot_file}: not a file")
            raise typer.Exit(1)
        try:
            snapshot = firewall_snapshot_parser.parse_iptables_save_file(str(rollback_snapshot_file))
        except Exception as exc:
            typer.echo(f"ERROR: unable to parse rollback snapshot file: {rollback_snapshot_file}: {exc}")
            raise typer.Exit(1)
        rollback_artifact = firewall_rollback_artifact_renderer.render_rollback_artifact_from_snapshot(snapshot, source="offline_snapshot_file")

    report = firewall_evidence_service.build_evidence_bundle_report(result, rollback_artifact=rollback_artifact)
    if output == "json":
        typer.echo(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return
    typer.echo("MPF firewall evidence bundle (offline)")
    for k in ("backend", "apply_mode", "evidence_version", "artifact_only", "inspection_only", "live_apply_allowed", "applyable", "readiness", "final_verdict"):
        v = getattr(report, k)
        typer.echo(f"{k}: {str(v).lower() if isinstance(v, bool) else v}")
    typer.echo(f"planner_customer_source: {report.planner_customer_source}")
    typer.echo(f"db_customer_input_loaded: {str(report.db_customer_input_loaded).lower()}")
    typer.echo(f"restore_payload_renderable: {str(report.restore_summary.get('renderable', False)).lower()}")
    typer.echo(f"apply_contract_readiness: {report.apply_contract_summary.get('readiness', 'blocked_for_live_apply')}")
    typer.echo(f"package_present: {str(report.package_summary.get('present', True)).lower()}")
    typer.echo(f"rollback_artifact_present: {str(report.rollback_summary.get('present', False)).lower()}")
    typer.echo(f"rollback_artifact_renderable: {str(report.rollback_summary.get('renderable', False)).lower()}")
    typer.echo(f"preflight_final_verdict: {report.preflight_summary.get('final_verdict', 'BLOCKED')}")
    typer.echo(f"sections: total={report.section_count} ok={report.ok_count} warn={report.warn_count} blocked={report.blocked_count}")
    typer.echo(f"firewall_change: {report.safety_flags['firewall_change']}")
    typer.echo(f"nat_change: {report.safety_flags['nat_change']}")
    typer.echo(f"runtime_change: {report.safety_flags['runtime_change']}")
    for w in report.warnings:
        typer.echo(f"WARNING [{w.code}] {w.message}")
    for e in report.errors:
        typer.echo(f"ERROR [{e.code}] {e.message}")

@events_app.command("latest")
def events_latest(config: Path | None = typer.Option(None, "--config", "-c"), limit: int = typer.Option(20, "--limit"), subject_type: str | None = typer.Option(None, "--subject-type"), severity: str | None = typer.Option(None, "--severity")) -> None:
    result = customer_read_service.latest_events(_load(config), limit=limit, subject_type=subject_type, severity=severity)
    if not result.ok:
        typer.echo(result.message)
        raise typer.Exit(1)
    if not result.rows:
        typer.echo("no events")
    for r in result.rows:
        for k in ("id", "event_type", "severity", "subject_type", "subject_id", "message", "created_at", "created_by", "correlation_id"):
            typer.echo(f"{k}: {r.get(k)}")
    typer.echo("firewall_change: no")
    typer.echo("nat_change: no")
    typer.echo("runtime_change: no")







@phase8_app.command("planning-readiness")
def phase8_planning_readiness(
    config: Path = typer.Option(Path("/etc/mpf/mpf.yaml"), "--config", help="Path to mpf.yaml."),
    output: str = typer.Option("human", "--output", help="human | json"),
) -> None:
    cfg = load_config(config)
    report = phase8_planning_readiness_service.build_phase8_planning_readiness_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2))
        return
    keys = [
        "component","final_decision","readiness_status","authorization_status","execution_allowed",
        "phase8_acceptance_allowed","abuse_automation_authorized","abuse_runner_authorized",
        "abuse_state_db_writes_authorized","abuse_event_db_writes_authorized","hard_block_authorized",
        "soft_block_authorized","pause_automation_authorized","production_traffic_authorized",
        "firewall_apply_authorized","iptables_restore_authorized","customer_nat_authorized",
        "customer_firewall_rules_authorized","phase7_accepted","phase8_working",
        "farm5_0_1_108_sync_evidence_present","ai_phase8_task_present","remaining_plan_phase8_aligned",
        "abuse_invariant_preserved","all_active_customers_coverage_required","no_silent_skip_required",
        "blockers","errors"
    ]
    for k in keys:
        typer.echo(f"{k}: {report.get(k)}")



@phase8_app.command("abuse-state-machine-contract")
def phase8_abuse_state_machine_contract(
    config: Path = typer.Option(Path("/etc/mpf/mpf.yaml"), "--config", help="Path to mpf.yaml."),
    output: str = typer.Option("human", "--output", help="human | json"),
) -> None:
    cfg = load_config(config)
    report = phase8_abuse_state_machine_contract_service.build_phase8_abuse_state_machine_contract_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    keys = [
        "component","final_decision","contract_status","authorization_status","execution_allowed",
        "phase8_acceptance_allowed","abuse_state_machine_contract_defined","abuse_state_path_defined",
        "abuse_transition_rules_defined","abuse_timing_contract_defined","abuse_hardening_contract_defined",
        "abuse_recovery_contract_defined","abuse_exemption_contract_defined","abuse_coverage_contract_defined",
        "abuse_runner_authorized","abuse_automation_authorized","abuse_state_db_writes_authorized",
        "abuse_event_db_writes_authorized","hard_block_authorized","soft_block_authorized",
        "pause_automation_authorized","production_traffic_authorized","firewall_apply_authorized",
        "iptables_restore_authorized","customer_nat_authorized","customer_firewall_rules_authorized","phase7_accepted",
        "phase8_working","farm5_0_1_110_sync_evidence_present","phase8_planning_readiness_present",
        "remaining_plan_state_machine_target_aligned","readme_current_gate_aligned","index_current_gate_aligned",
        "ai_coding_rules_current_gate_aligned","abuse_invariant_preserved",
        "state_path_normal_over_tracking_over_grace_hard","sustained_abuse_window_3600_seconds",
        "farms_over_alone_does_not_harden","worker_over_alone_does_not_harden",
        "all_active_customers_coverage_required","no_silent_skip_required","blockers","errors"
    ]
    for k in keys:
        typer.echo(f"{k}: {report.get(k)}")



@phase8_app.command("abuse-evidence-reporting-contract")
def phase8_abuse_evidence_reporting_contract(
    config: Path = typer.Option(Path("/etc/mpf/mpf.yaml"), "--config", help="Path to mpf.yaml."),
    output: str = typer.Option("human", "--output", help="human | json"),
) -> None:
    cfg = load_config(config)
    report = phase8_abuse_evidence_reporting_contract_service.build_phase8_abuse_evidence_reporting_contract_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    keys = [
        "component","final_decision","contract_status","authorization_status","execution_allowed",
        "phase8_acceptance_allowed","state_machine_contract_present","state_machine_contract_fail_closed",
        "evidence_reporting_contract_defined","evidence_source_contract_defined","evidence_snapshot_contract_defined",
        "customer_evaluation_report_contract_defined","coverage_report_contract_defined","missing_evidence_report_contract_defined",
        "operator_summary_contract_defined","failure_mode_report_contract_defined","abuse_runner_authorized",
        "abuse_automation_authorized","abuse_state_db_reads_authorized","abuse_state_db_writes_authorized",
        "usage_sample_db_reads_authorized","policy_event_db_reads_authorized","conntrack_live_read_authorized",
        "firewall_counter_live_read_authorized","hard_block_authorized","soft_block_authorized",
        "pause_automation_authorized","production_traffic_authorized","firewall_apply_authorized","iptables_restore_authorized",
        "customer_nat_authorized","customer_firewall_rules_authorized","phase7_accepted","phase8_working",
        "farm5_0_1_110_sync_evidence_present","no_farm5_0_1_111_sync_evidence_claimed","no_farm5_0_1_112_sync_evidence_claimed",
        "remaining_plan_evidence_reporting_target_aligned","abuse_invariant_preserved","all_active_customers_coverage_required",
        "missing_evidence_report_required","stale_evidence_report_required","no_silent_skip_required","blockers","errors"
    ]
    for k in keys:
        typer.echo(f"{k}: {report.get(k)}")



@phase8_app.command("abuse-dry-run-evaluator")
def phase8_abuse_dry_run_evaluator(
    config: Path = typer.Option(Path("/etc/mpf/mpf.yaml"), "--config", help="Path to mpf.yaml."),
    output: str = typer.Option("human", "--output", help="human | json"),
) -> None:
    cfg = load_config(config)
    report = phase8_abuse_dry_run_evaluator_service.build_phase8_abuse_dry_run_evaluator_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    keys = [
        "component","final_decision","dry_run_status","authorization_status","execution_allowed","phase8_acceptance_allowed",
        "state_machine_contract_present","state_machine_contract_fail_closed","evidence_reporting_contract_present","evidence_reporting_contract_fail_closed",
        "dry_run_evaluator_defined","pure_domain_evaluator_defined","synthetic_scenarios_defined","synthetic_scenarios_passed","transition_logic_defined",
        "hardening_proposal_logic_defined","missing_evidence_blocks_hardening","stale_evidence_blocks_hardening","farms_over_alone_does_not_harden",
        "worker_over_alone_does_not_harden","manual_unhard_future_gated","abuse_runner_authorized","abuse_automation_authorized",
        "abuse_state_db_reads_authorized","abuse_state_db_writes_authorized","usage_sample_db_reads_authorized","policy_event_db_reads_authorized",
        "conntrack_live_read_authorized","firewall_counter_live_read_authorized","hard_block_authorized","soft_block_authorized",
        "pause_automation_authorized","production_traffic_authorized","firewall_apply_authorized","iptables_restore_authorized",
        "customer_nat_authorized","customer_firewall_rules_authorized","phase7_accepted","phase8_working","farm5_0_1_110_sync_evidence_present",
        "no_farm5_0_1_111_sync_evidence_claimed","no_farm5_0_1_112_sync_evidence_claimed","no_farm5_0_1_113_sync_evidence_claimed",
        "remaining_plan_dry_run_target_aligned","abuse_invariant_preserved","all_active_customers_coverage_required","no_silent_skip_required","blockers","errors"
    ]
    for k in keys: typer.echo(f"{k}: {report.get(k)}")



@phase8_app.command("db-transition-readiness")
def phase8_db_transition_readiness(
    config: Path = typer.Option(Path("/etc/mpf/mpf.yaml"), "--config", help="Path to mpf.yaml."),
    output: str = typer.Option("human", "--output", help="human | json"),
) -> None:
    cfg = load_config(config)
    report = phase8_db_transition_readiness_service.build_phase8_db_transition_readiness_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    keys = [
        "component","final_decision","readiness_status","authorization_status","execution_allowed","phase8_acceptance_allowed",
        "state_machine_contract_present","state_machine_contract_fail_closed","evidence_reporting_contract_present","evidence_reporting_contract_fail_closed",
        "dry_run_evaluator_present","dry_run_evaluator_fail_closed","transition_plan_contract_defined","db_mutation_plan_contract_defined",
        "operator_approval_contract_defined","audit_payload_contract_defined","restore_reference_contract_defined","idempotency_contract_defined",
        "synthetic_transition_plan_scenarios_defined","synthetic_transition_plan_scenarios_passed","existing_abuse_models_detected","future_migration_required",
        "db_transition_execution_authorized","db_reads_authorized","db_writes_authorized","abuse_state_db_reads_authorized","abuse_state_db_writes_authorized",
        "abuse_event_db_writes_authorized","customer_db_reads_authorized","abuse_runner_authorized","abuse_automation_authorized",
        "conntrack_live_read_authorized","firewall_counter_live_read_authorized","hard_block_authorized","soft_block_authorized","pause_automation_authorized",
        "production_traffic_authorized","firewall_apply_authorized","iptables_restore_authorized","customer_nat_authorized","customer_firewall_rules_authorized",
        "phase7_accepted","phase8_working","farm5_0_1_110_sync_evidence_present","no_farm5_0_1_111_sync_evidence_claimed","no_farm5_0_1_112_sync_evidence_claimed",
        "no_farm5_0_1_113_sync_evidence_claimed","no_farm5_0_1_114_sync_evidence_claimed","remaining_plan_db_transition_target_aligned","abuse_invariant_preserved",
        "all_active_customers_coverage_required","no_silent_skip_required","blockers","errors"
    ]
    for k in keys: typer.echo(f"{k}: {report.get(k)}")


@phase8_app.command("db-transition-execution")
def phase8_db_transition_execution(
    config: Path = typer.Option(Path("/etc/mpf/mpf.yaml"), "--config", help="Path to mpf.yaml."),
    output: str = typer.Option("human", "--output", help="human | json"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    operator_confirmation: str | None = typer.Option(None, "--operator-confirmation"),
    request_source: str = typer.Option("explicit_manual_cli", "--request-source"),
    demo_scenario: str = typer.Option("synthetic_tracking", "--demo-scenario"),
) -> None:
    cfg = load_config(config)
    report = phase8_db_transition_execution_service.build_phase8_db_transition_execution_report(cfg)
    report["cli_dry_run"] = dry_run
    report["operator_confirmation_provided"] = bool(operator_confirmation)
    report["request_source"] = request_source
    report["demo_scenario"] = demo_scenario
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    keys=["component","final_decision","execution_status","authorization_status","execution_allowed","phase8_acceptance_allowed","farm5_0_1_114_sync_evidence_present","farm5_0_1_114_phase8_reports_evidence_present","no_farm5_0_1_115_sync_evidence_claimed","db_transition_execution_contract_defined","db_execution_request_contract_defined","db_execution_validation_defined","db_execution_result_contract_defined","repo_interface_defined","in_memory_repo_defined","idempotency_guard_defined","operator_confirmation_guard_defined","operator_approval_guard_defined","manual_unhard_future_gated","synthetic_execution_scenarios_passed","db_execution_authorized","db_writes_authorized","runtime_automation_authorized","abuse_runner_authorized","abuse_automation_authorized","firewall_apply_authorized","iptables_restore_authorized","customer_nat_authorized","customer_firewall_rules_authorized","production_traffic_authorized","hard_block_authorized","soft_block_authorized","pause_automation_authorized","future_farm5_sync_required_after_merge","future_operator_acceptance_required"]
    for k in keys: typer.echo(f"{k}: {report.get(k)}")
    typer.echo(f"blockers: {report.get('blockers', [])}")
    typer.echo(f"errors: {report.get('errors', [])}")


@phase8_app.command("runtime-worker-readiness")
def phase8_runtime_worker_readiness(
    config: Path = typer.Option(Path("/etc/mpf/mpf.yaml"), "--config", help="Path to mpf.yaml."),
    output: str = typer.Option("human", "--output", help="human | json"),
) -> None:
    cfg = load_config(config)
    report = phase8_runtime_worker_integration_readiness_service.build_phase8_runtime_worker_integration_readiness_report(cfg)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    keys=["component","final_decision","readiness_status","authorization_status","execution_allowed","phase8_acceptance_allowed","farm5_0_1_115_sync_evidence_present","farm5_0_1_115_db_execution_report_evidence_present","no_farm5_0_1_116_sync_evidence_claimed","db_transition_execution_present","db_transition_execution_fail_closed","worker_readiness_contract_defined","worker_loop_contract_defined","worker_failure_modes_defined","worker_synthetic_scenarios_passed","worker_default_disabled","scheduler_default_disabled","runtime_worker_authorized","scheduler_authorized","abuse_runner_authorized","real_customer_evaluation_authorized","production_db_execution_authorized","db_reads_authorized","db_writes_authorized","firewall_apply_authorized","customer_nat_authorized","customer_firewall_rules_authorized","production_traffic_authorized","hard_block_authorized","soft_block_authorized","pause_automation_authorized","future_worker_dry_run_harness_pr_required","future_farm5_sync_required_before_runtime_acceptance"]
    for k in keys: typer.echo(f"{k}: {report.get(k)}")
    typer.echo(f"blockers: {report.get('blockers', [])}")
    typer.echo(f"errors: {report.get('errors', [])}")

@phase7_app.command("summary")
def phase7_summary(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase7_reports_doctor_service.build_phase7_reports_summary(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    keys = ("component","final_decision","summary_status","authorization_status","execution_allowed","phase7_acceptance_allowed","usage_policy_readiness_clean","usage_accounting_contract_clean","policy_reject_accounting_contract_clean","latest_recorded_farm5_sync_evidence_present","no_fabricated_0_1_105_or_0_1_106_sync_evidence","remaining_plan_reports_doctor_target_aligned","ai_phase7_reports_doctor_present","production_traffic_authorized","firewall_apply_authorized","customer_nat_authorized","customer_firewall_rules_authorized","usage_automation_authorized","usage_collectors_authorized","policy_reject_collectors_authorized","abuse_automation_authorized","phase8_start_allowed","batched_farm5_sync_required_after_merge")
    for key in keys: typer.echo(f"{key}: {report.get(key)}")
    typer.echo(f"blockers: {report.get('blockers', [])}")
    typer.echo(f"errors: {report.get('errors', [])}")


@phase7_app.command("doctor")
def phase7_doctor(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase7_reports_doctor_service.build_phase7_doctor_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    keys = ("component","final_verdict","final_decision","doctor_status","authorization_status","execution_allowed","phase7_acceptance_allowed","usage_policy_readiness_clean","usage_accounting_contract_clean","policy_reject_accounting_contract_clean","latest_recorded_farm5_sync_evidence_present","no_fabricated_0_1_105_or_0_1_106_sync_evidence","production_traffic_authorized","firewall_apply_authorized","customer_nat_authorized","customer_firewall_rules_authorized","usage_automation_authorized","usage_collectors_authorized","policy_reject_collectors_authorized","abuse_automation_authorized","phase8_start_allowed","batched_farm5_sync_required_after_merge")
    for key in keys: typer.echo(f"{key}: {report.get(key)}")
    typer.echo(f"blockers: {report.get('blockers', [])}")
    typer.echo(f"errors: {report.get('errors', [])}")


@phase7_app.command("usage-accounting-contract")
def phase7_usage_accounting_contract(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    """Render Phase 7 usage accounting contract report (report-only, non-authorizing)."""
    report = phase7_usage_accounting_contract_service.build_phase7_usage_accounting_contract_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    keys = ("component","final_decision","contract_status","authorization_status","execution_allowed","phase7_acceptance_allowed","usage_accounting_contract_defined","usage_samples_contract_defined","usage_delta_contract_defined","usage_report_windows_defined","usage_doctor_contract_defined","usage_collector_runtime_authorized","usage_timer_authorized","usage_db_writes_authorized","usage_counter_live_read_authorized","firewall_counter_live_read_authorized","production_traffic_authorized","firewall_apply_authorized","iptables_restore_authorized","customer_nat_authorized","customer_firewall_rules_authorized","abuse_automation_authorized","phase8_start_allowed","farm5_0_1_104_sync_evidence_present","phase7_readiness_present","remaining_plan_usage_contract_target_aligned","abuse_invariant_preserved")
    for k in keys:
        typer.echo(f"{k}: {report.get(k)}")
    typer.echo(f"blockers: {report.get('blockers', [])}")
    typer.echo(f"errors: {report.get('errors', [])}")

@phase7_app.command("usage-policy-readiness")
def phase7_usage_policy_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    """Render Phase 7 usage/policy readiness report (report-only, non-authorizing)."""
    report = phase7_usage_policy_readiness_service.build_phase7_usage_policy_readiness_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    keys = ("component","final_decision","readiness_status","authorization_status","phase7_acceptance_allowed","execution_allowed","usage_automation_authorized","usage_collectors_authorized","policy_reject_collectors_authorized","policy_reject_accounting_authorized","customer_nat_authorized","customer_firewall_rules_authorized","production_traffic_authorized","firewall_apply_authorized","iptables_restore_authorized","abuse_automation_authorized","phase8_start_allowed","operator_review_required","fresh_farm5_sync_evidence_required_before_acceptance","separate_phase7_service_contract_pr_required","latest_recorded_farm5_sync_evidence_present","phase6_accepted","phase7_working","readme_phase7_aligned","ai_phase7_task_present","remaining_plan_phase7_aligned","apply_mode_plan_only","runtime_activation_disabled","abuse_invariant_preserved")
    for k in keys:
        typer.echo(f"{k}: {report.get(k)}")
    typer.echo(f"blockers: {report.get('blockers', [])}")
    typer.echo(f"errors: {report.get('errors', [])}")




@phase7_app.command("final-acceptance-readiness")
def phase7_final_acceptance_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase7_final_acceptance_readiness_service.build_phase7_final_acceptance_readiness_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    keys = ("component","final_decision","readiness_status","authorization_status","execution_allowed","phase7_acceptance_allowed","phase8_start_allowed","operator_review_required","operator_acceptance_pr_required","farm5_sync_version","farm5_0_1_107_sync_evidence_present","phase7_usage_policy_readiness_clean","phase7_usage_accounting_contract_clean","phase7_policy_reject_accounting_contract_clean","phase7_reports_summary_clean","phase7_doctor_ok","phase7_contract_stack_complete","production_traffic_none","firewall_apply_disallowed","customer_nat_disallowed","customer_firewall_rules_disallowed","usage_collectors_disallowed","policy_reject_collectors_disallowed","abuse_automation_disallowed","abuse_invariant_preserved")
    for k in keys: typer.echo(f"{k}: {report.get(k)}")
    typer.echo(f"blockers: {report.get('blockers', [])}")
    typer.echo(f"errors: {report.get('errors', [])}")


@phase7_app.command("operator-acceptance-decision")
def phase7_operator_acceptance_decision(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase7_operator_acceptance_decision_service.build_phase7_operator_acceptance_decision_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    keys = ("component","operator_decision","final_decision","acceptance_scope","recommended_next_phase_after_operator_acceptance","authorization_status","execution_allowed","phase7_acceptance_allowed","phase8_start_allowed","operator_review_required","operator_must_explicitly_accept_phase7","separate_phase_gate_update_pr_required","phase7_final_acceptance_readiness_clean","farm5_0_1_107_sync_evidence_present","phase7_doctor_ok","all_phase7_child_reports_clean","runtime_gates_closed","abuse_invariant_preserved","phase8_not_started")
    for k in keys: typer.echo(f"{k}: {report.get(k)}")
    typer.echo(f"blockers: {report.get('blockers', [])}")
    typer.echo(f"errors: {report.get('errors', [])}")
@phase7_app.command("policy-reject-accounting-contract")
def phase7_policy_reject_accounting_contract(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    """Render Phase 7 policy/reject accounting contract report (report-only, non-authorizing)."""
    report = phase7_policy_reject_accounting_contract_service.build_phase7_policy_reject_accounting_contract_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    keys = ("component","final_decision","contract_status","authorization_status","execution_allowed","phase7_acceptance_allowed","policy_reject_accounting_contract_defined","policy_events_contract_defined","reject_categories_defined","reject_explainability_contract_defined","reject_report_windows_defined","policy_reject_doctor_contract_defined","policy_reject_collector_runtime_authorized","policy_reject_timer_authorized","policy_reject_db_writes_authorized","policy_reject_live_counter_read_authorized","firewall_counter_live_read_authorized","production_traffic_authorized","firewall_apply_authorized","iptables_restore_authorized","customer_nat_authorized","customer_firewall_rules_authorized","abuse_automation_authorized","phase8_start_allowed","latest_recorded_farm5_sync_evidence_present","phase7_readiness_present","usage_accounting_contract_present","remaining_plan_policy_reject_contract_target_aligned","abuse_invariant_preserved")
    for k in keys:
        typer.echo(f"{k}: {report.get(k)}")
    typer.echo(f"blockers: {report.get('blockers', [])}")
    typer.echo(f"errors: {report.get('errors', [])}")

@app.command("phase-status")
def phase_status() -> None:
    """Print the current repository phase guard."""
    phase_status_path = Path("docs/PHASE_STATUS.md")
    try:
        block = _extract_current_state_block(phase_status_path)
    except RuntimeError as exc:
        typer.echo(f"ERROR: {exc}")
        raise typer.Exit(1)
    typer.echo(block)


@production_app.command("readiness")
def production_readiness(output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    """Render Phase 11A production readiness inventory report (report-only, non-authorizing)."""
    report = phase11_production_readiness_service.build_phase11_production_readiness_report()
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    typer.echo(f"component: {report['component']}")
    typer.echo(f"final_decision: {report['final_decision']}")
    typer.echo(f"authorization_status: {report['authorization_status']}")
    typer.echo(f"execution_allowed: {report['execution_allowed']}")
    safety_flags = report["safety_flags"]
    typer.echo(f"production_traffic_authorized: {safety_flags['production_traffic_authorized']}")
    typer.echo(f"firewall_apply_authorized: {safety_flags['firewall_apply_authorized']}")
    typer.echo(f"customer_nat_authorized: {safety_flags['customer_nat_authorized']}")
    typer.echo(f"abuse_automation_authorized: {safety_flags['abuse_automation_authorized']}")
    typer.echo(f"blockers: {report['blockers']}")




@production_app.command("canary-plan")
def production_canary_plan(
    lane: str = typer.Option("btc", "--lane"),
    customer_key: str | None = typer.Option("canary-btc-001", "--customer-key"),
    name: str | None = typer.Option("Phase 11 canary", "--name"),
    port: int | None = typer.Option(20001, "--port"),
    miners: int = typer.Option(1, "--miners"),
    farms: int = typer.Option(1, "--farms"),
    maxconn: int = typer.Option(1, "--maxconn"),
    rate_per_min: int = typer.Option(120, "--rate-per-min"),
    burst: int = typer.Option(240, "--burst"),
    ips_mode: str = typer.Option("any", "--ips-mode"),
    ip_whitelist: list[str] = typer.Option([], "--ip"),
    operator: str | None = typer.Option(None, "--operator"),
    reason: str | None = typer.Option(None, "--reason"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
) -> None:
    """Render Phase 11B canary plan report (report-only, non-authorizing)."""
    request = production_domain.CanaryPlanRequest(
        customer_key=customer_key, lane=lane, port=port, name=name,
        miners=miners, farms=farms, maxconn=maxconn, rate_per_min=rate_per_min, burst=burst,
        ips_mode=ips_mode, ip_whitelist=ip_whitelist, operator=operator, reason=reason,
    )
    report = phase11_canary_plan_service.build_phase11_canary_plan_report(request)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    typer.echo(f"component: {report['component']}")
    typer.echo(f"final_decision: {report['final_decision']}")
    typer.echo(f"authorization_status: {report['authorization_status']}")
    typer.echo(f"execution_allowed: {report['execution_allowed']}")
    typer.echo(f"report_only: {report['report_only']}")
    typer.echo(f"mutation_performed: {report['mutation_performed']}")
    typer.echo(f"blockers: {report['blockers']}")
    typer.echo(f"validation_errors: {report['validation_errors']}")



@production_app.command("activation-harness")
def production_activation_harness(
    lane: str = typer.Option("btc", "--lane"),
    customer_key: str | None = typer.Option("canary-btc-001", "--customer-key"),
    name: str | None = typer.Option("Phase 11 controlled canary", "--name"),
    port: int | None = typer.Option(20001, "--port"),
    miners: int = typer.Option(1, "--miners"),
    farms: int = typer.Option(1, "--farms"),
    maxconn: int = typer.Option(1, "--maxconn"),
    rate_per_min: int = typer.Option(120, "--rate-per-min"),
    burst: int = typer.Option(240, "--burst"),
    ips_mode: str = typer.Option("any", "--ips-mode"),
    ip_whitelist: list[str] = typer.Option([], "--ip"),
    operator: str | None = typer.Option(None, "--operator"),
    reason: str | None = typer.Option(None, "--reason"),
    requested_action: str = typer.Option("preflight", "--requested-action"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    require_operator_confirmation: bool = typer.Option(True, "--require-operator-confirmation/--no-require-operator-confirmation"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
) -> None:
    request = production_domain.ControlledActivationHarnessRequest(
        customer_key=customer_key, lane=lane, port=port, name=name,
        miners=miners, farms=farms, maxconn=maxconn, rate_per_min=rate_per_min, burst=burst,
        ips_mode=ips_mode, ip_whitelist=ip_whitelist, operator=operator, reason=reason,
        requested_action=requested_action, dry_run=dry_run, require_operator_confirmation=require_operator_confirmation,
    )
    report = phase11_controlled_activation_harness_service.build_phase11_controlled_activation_harness_report(request)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    typer.echo(f"component: {report['component']}")
    typer.echo(f"final_decision: {report['final_decision']}")
    typer.echo(f"authorization_status: {report['authorization_status']}")
    typer.echo(f"execution_allowed: {report['execution_allowed']}")
    typer.echo(f"harness_mode: {report['harness_mode']}")
    typer.echo(f"mutation_performed: {report['mutation_performed']}")
    typer.echo(f"blockers: {report['blockers']}")
    typer.echo(f"validation_errors: {report['validation_errors']}")



@production_app.command("canary-acceptance")
def production_canary_acceptance(
    lane: str = typer.Option("btc", "--lane"),
    customer_key: str | None = typer.Option("canary-btc-001", "--customer-key"),
    name: str | None = typer.Option("Phase 11 manual canary", "--name"),
    port: int | None = typer.Option(20001, "--port"),
    miners: int = typer.Option(1, "--miners"),
    farms: int = typer.Option(1, "--farms"),
    maxconn: int = typer.Option(1, "--maxconn"),
    rate_per_min: int = typer.Option(120, "--rate-per-min"),
    burst: int = typer.Option(240, "--burst"),
    ips_mode: str = typer.Option("any", "--ips-mode"),
    ip_whitelist: list[str] = typer.Option([], "--ip"),
    operator: str | None = typer.Option(None, "--operator"),
    reason: str | None = typer.Option(None, "--reason"),
    requested_action: str = typer.Option("package", "--requested-action"),
    require_operator_confirmation: bool = typer.Option(True, "--require-operator-confirmation/--no-require-operator-confirmation"),
    require_farm5_phase11c_evidence: bool = typer.Option(True, "--require-farm5-phase11c-evidence/--no-require-farm5-phase11c-evidence"),
    require_backup_reference: bool = typer.Option(True, "--require-backup-reference/--no-require-backup-reference"),
    require_restore_plan_reference: bool = typer.Option(True, "--require-restore-plan-reference/--no-require-restore-plan-reference"),
    require_rollback_plan: bool = typer.Option(True, "--require-rollback-plan/--no-require-rollback-plan"),
    require_no_customer_nat_baseline: bool = typer.Option(True, "--require-no-customer-nat-baseline/--no-require-no-customer-nat-baseline"),
    require_no_customer_firewall_baseline: bool = typer.Option(True, "--require-no-customer-firewall-baseline/--no-require-no-customer-firewall-baseline"),
    require_local_only_runtime_baseline: bool = typer.Option(True, "--require-local-only-runtime-baseline/--no-require-local-only-runtime-baseline"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
) -> None:
    request = production_domain.ManualCanaryAcceptanceRequest(
        customer_key=customer_key, lane=lane, port=port, name=name,
        miners=miners, farms=farms, maxconn=maxconn, rate_per_min=rate_per_min, burst=burst,
        ips_mode=ips_mode, ip_whitelist=ip_whitelist, operator=operator, reason=reason,
        requested_action=requested_action,
        require_operator_confirmation=require_operator_confirmation,
        require_farm5_phase11c_evidence=require_farm5_phase11c_evidence,
        require_backup_reference=require_backup_reference,
        require_restore_plan_reference=require_restore_plan_reference,
        require_rollback_plan=require_rollback_plan,
        require_no_customer_nat_baseline=require_no_customer_nat_baseline,
        require_no_customer_firewall_baseline=require_no_customer_firewall_baseline,
        require_local_only_runtime_baseline=require_local_only_runtime_baseline,
    )
    report = phase11_manual_canary_acceptance_service.build_phase11_manual_canary_acceptance_report(request)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    typer.echo(f"component: {report['component']}")
    typer.echo(f"final_decision: {report['final_decision']}")
    typer.echo(f"authorization_status: {report['authorization_status']}")
    typer.echo(f"execution_allowed: {report['execution_allowed']}")
    typer.echo(f"acceptance_package_mode: {report['acceptance_package_mode']}")
    typer.echo(f"mutation_performed: {report['mutation_performed']}")
    typer.echo(f"blockers: {report['blockers']}")
    typer.echo(f"validation_errors: {report['validation_errors']}")


@production_app.command("canary-execution-gate")
def production_canary_execution_gate(
    lane: str = typer.Option("btc", "--lane"),
    customer_key: str | None = typer.Option("canary-btc-001", "--customer-key"),
    name: str | None = typer.Option("Phase 11 manual canary execution", "--name"),
    port: int | None = typer.Option(20001, "--port"),
    miners: int = typer.Option(1, "--miners"),
    farms: int = typer.Option(1, "--farms"),
    maxconn: int = typer.Option(1, "--maxconn"),
    rate_per_min: int = typer.Option(120, "--rate-per-min"),
    burst: int = typer.Option(240, "--burst"),
    ips_mode: str = typer.Option("any", "--ips-mode"),
    ip_whitelist: list[str] = typer.Option([], "--ip"),
    operator: str | None = typer.Option(None, "--operator"),
    reason: str | None = typer.Option(None, "--reason"),
    requested_action: str = typer.Option("gate", "--requested-action"),
    require_operator_confirmation: bool = typer.Option(True, "--require-operator-confirmation/--no-require-operator-confirmation"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
) -> None:
    request = production_domain.ManualCanaryExecutionGateRequest(
        customer_key=customer_key, lane=lane, port=port, name=name, miners=miners, farms=farms, maxconn=maxconn,
        rate_per_min=rate_per_min, burst=burst, ips_mode=ips_mode, ip_whitelist=ip_whitelist, operator=operator, reason=reason,
        requested_action=requested_action, require_operator_confirmation=require_operator_confirmation,
    )
    report = phase11_manual_canary_execution_gate_service.build_phase11_manual_canary_execution_gate_report(request)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    typer.echo(f"component: {report['component']}")
    typer.echo(f"final_decision: {report['final_decision']}")
    typer.echo(f"authorization_status: {report['authorization_status']}")
    typer.echo(f"execution_allowed: {report['execution_allowed']}")
    typer.echo(f"mutation_performed: {report['mutation_performed']}")
    typer.echo(f"blockers: {report['blockers']}")
    typer.echo(f"validation_errors: {report['validation_errors']}")



@production_app.command("manual-canary-execute")
def production_manual_canary_execute(
    lane: str = typer.Option("btc", "--lane"),
    customer_key: str | None = typer.Option("canary-btc-001", "--customer-key"),
    name: str | None = typer.Option("Phase 11 manual canary execution", "--name"),
    port: int | None = typer.Option(20001, "--port"),
    miners: int = typer.Option(1, "--miners"),
    farms: int = typer.Option(1, "--farms"),
    maxconn: int = typer.Option(1, "--maxconn"),
    rate_per_min: int = typer.Option(120, "--rate-per-min"),
    burst: int = typer.Option(240, "--burst"),
    ips_mode: str = typer.Option("any", "--ips-mode"),
    ip_whitelist: list[str] = typer.Option([], "--ip"),
    operator: str | None = typer.Option(None, "--operator"),
    reason: str | None = typer.Option(None, "--reason"),
    requested_action: str = typer.Option("plan", "--requested-action"),
    expected_version: str | None = typer.Option(None, "--expected-version"),
    operator_confirmed: bool = typer.Option(False, "--operator-confirmed/--no-operator-confirmed"),
    understand_canary_customer: bool = typer.Option(False, "--i-understand-this-can-create-a-canary-customer"),
    understand_firewall_apply: bool = typer.Option(False, "--i-understand-this-can-apply-firewall"),
    reviewed_rollback: bool = typer.Option(False, "--i-have-reviewed-rollback"),
    fresh_farm5_sync_confirmed: bool = typer.Option(False, "--i-have-fresh-farm5-sync"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
) -> None:
    request = production_domain.ManualCanaryExecutionRunRequest(
        customer_key=customer_key, lane=lane, port=port, name=name, miners=miners, farms=farms, maxconn=maxconn,
        rate_per_min=rate_per_min, burst=burst, ips_mode=ips_mode, ip_whitelist=ip_whitelist, operator=operator, reason=reason,
        requested_action=requested_action, expected_version=expected_version, operator_confirmed=operator_confirmed,
        understand_canary_customer=understand_canary_customer, understand_firewall_apply=understand_firewall_apply,
        reviewed_rollback=reviewed_rollback, fresh_farm5_sync_confirmed=fresh_farm5_sync_confirmed,
    )
    adapters = phase11_manual_canary_execution_adapters.build_manual_canary_production_adapters()
    report = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(request, adapters=adapters)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    for key in ("component", "final_decision", "authorization_status", "execution_allowed", "mutation_performed", "blockers", "validation_errors"):
        typer.echo(f"{key}: {report[key]}")






@production_app.command("operator-context")
def production_operator_context(
    mode: Literal["read", "db-write"] = typer.Option("read", "--mode"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = operator_execution_context_service.build_operator_execution_context_report(_load(config), mode=mode)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    for k in ("component", "mode", "final_decision", "os_user", "database_url_is_local_peer", "blockers", "recommended_command_prefix"):
        typer.echo(f"{k}: {report[k]}")


@production_app.command("canary-usage-evidence-capture")
def production_canary_usage_evidence_capture(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    collect_live: bool = typer.Option(True, "--collect-live/--no-collect-live"),
    write_evidence_json: Path | None = typer.Option(None, "--write-evidence-json"),
    overwrite_evidence_json: bool = typer.Option(False, "--overwrite-evidence-json"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_canary_usage_evidence_capture_service.build_phase11_canary_usage_evidence_capture_report(_load(config), customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live)
    if write_evidence_json:
        phase11_canary_usage_evidence_capture_service.write_usage_evidence_json(report=report, path=write_evidence_json, overwrite=overwrite_evidence_json)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    for k in ("component", "final_decision", "blockers", "warnings", "next_required_step"):
        typer.echo(f"{k}: {report[k]}")



@production_app.command("canary-reject-session-ip-evidence-capture")
def production_canary_reject_session_ip_evidence_capture(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    collect_live: bool = typer.Option(True, "--collect-live/--no-collect-live"),
    write_evidence_json: Path | None = typer.Option(None, "--write-evidence-json"),
    overwrite_evidence_json: bool = typer.Option(False, "--overwrite-evidence-json"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_canary_reject_session_ip_evidence_capture_service.build_phase11_canary_reject_session_ip_evidence_capture_report(_load(config), customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live)
    if write_evidence_json:
        phase11_canary_reject_session_ip_evidence_capture_service.write_reject_session_ip_evidence_json(report=report, path=write_evidence_json, overwrite=overwrite_evidence_json)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    for k in ("component", "final_decision", "blockers", "warnings", "next_required_step"):
        typer.echo(f"{k}: {report[k]}")




@production_app.command("canary-reject-counters-visibility")
def production_canary_reject_counters_visibility(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    collect_live: bool = typer.Option(True, "--collect-live/--no-collect-live"),
    write_evidence_json: Path | None = typer.Option(None, "--write-evidence-json"),
    overwrite_evidence_json: bool = typer.Option(False, "--overwrite-evidence-json"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_canary_reject_counters_visibility_service.build_phase11_canary_reject_counters_visibility_report(_load(config), customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live)
    if write_evidence_json:
        phase11_canary_reject_counters_visibility_service.write_reject_counters_evidence_json(report=report, path=write_evidence_json, overwrite=overwrite_evidence_json)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    for k in ("component", "final_decision", "blockers", "warnings", "next_required_step"):
        typer.echo(f"{k}: {report[k]}")

@production_app.command("canary-evidence-collect")
def production_canary_evidence_collect(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    cfg = _load(config)
    report = phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report(
        cfg, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version
    )
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    for key in ("component", "final_decision", "blockers", "warnings", "commands_attempted", "commands_unavailable"):
        typer.echo(f"{key}: {report[key]}")



def _print_output(report: dict[str, object], output: str) -> None:
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    for k in ("component", "final_decision", "blockers", "warnings"):
        if k in report:
            typer.echo(f"{k}: {report[k]}")


@production_app.command("canary-worker-stratum-evidence-capture")
def production_canary_worker_stratum_evidence_capture(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    connect_host: str = typer.Option(..., "--connect-host"),
    connect_port: int = typer.Option(20001, "--connect-port"),
    worker_name: str = typer.Option("canary-btc-001.worker-001", "--worker-name"),
    timeout_seconds: int = typer.Option(8, "--timeout-seconds"),
    wait_notify_seconds: int = typer.Option(8, "--wait-notify-seconds"),
    collect_live: bool = typer.Option(True, "--collect-live/--no-collect-live"),
    write_evidence_json: Path | None = typer.Option(None, "--write-evidence-json"),
    overwrite_evidence_json: bool = typer.Option(False, "--overwrite-evidence-json"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_canary_worker_stratum_evidence_capture_service.build_phase11_canary_worker_stratum_evidence_capture_report(
        _load(config), customer_key=customer_key, lane=lane, port=port, expected_version=expected_version,
        farm5_baseline_version=farm5_baseline_version, connect_host=connect_host, connect_port=connect_port,
        worker_name=worker_name, timeout_seconds=timeout_seconds, wait_notify_seconds=wait_notify_seconds, collect_live=collect_live
    )
    if write_evidence_json:
        phase11_canary_worker_stratum_evidence_capture_service.write_worker_stratum_evidence_json(report=report, path=write_evidence_json, overwrite=overwrite_evidence_json)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    for k in ("component", "final_decision", "blockers", "warnings"):
        typer.echo(f"{k}: {report[k]}")

@production_app.command("canary-external-stratum-transcript-import")
def production_canary_external_stratum_transcript_import(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    transcript_json: Path = typer.Option(..., "--transcript-json"),
    collect_live: bool = typer.Option(False, "--collect-live/--no-collect-live"),
    write_evidence_json: Path | None = typer.Option(None, "--write-evidence-json"),
    overwrite_evidence_json: bool = typer.Option(False, "--overwrite-evidence-json"),
    output: str = typer.Option("human", "--output"),
    config_path: Path = typer.Option(Path("/etc/mpf/mpf.yaml"), "--config"),
) -> None:
    cfg = load_config(config_path)
    report = phase11_external_canary_stratum_transcript_import_service.build_phase11_external_canary_stratum_transcript_import_report(
        cfg, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, transcript_json=transcript_json, collect_live=collect_live
    )
    if write_evidence_json:
        phase11_external_canary_stratum_transcript_import_service.write_external_stratum_transcript_evidence_json(report=report, path=write_evidence_json, overwrite=overwrite_evidence_json)
    _print_output(report, output)


@production_app.command("canary-abuse-coverage-visibility")
def production_canary_abuse_coverage_visibility(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    collect_live: bool = typer.Option(False, "--collect-live/--no-collect-live"),
    write_evidence_json: Path | None = typer.Option(None, "--write-evidence-json"),
    overwrite_evidence_json: bool = typer.Option(False, "--overwrite-evidence-json"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_canary_abuse_coverage_visibility_service.build_phase11_canary_abuse_coverage_visibility_report(
        _load(config), customer_key=customer_key, lane=lane, port=port, expected_version=expected_version,
        farm5_baseline_version=farm5_baseline_version, collect_live=collect_live
    )
    if write_evidence_json:
        phase11_canary_abuse_coverage_visibility_service.write_abuse_coverage_visibility_evidence_json(report=report, path=write_evidence_json, overwrite=overwrite_evidence_json)
    _print_output(report, output)


@production_app.command("canary-final-check-report-visibility")
def production_canary_final_check_report_visibility(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    evidence_json: list[Path] = typer.Option([], "--evidence-json"),
    collect_live: bool = typer.Option(False, "--collect-live/--no-collect-live"),
    write_evidence_json: Path | None = typer.Option(None, "--write-evidence-json"),
    overwrite_evidence_json: bool = typer.Option(False, "--overwrite-evidence-json"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    cfg = _load(config)
    evidences = [phase11_canary_visibility_bundle_service.load_phase11_canary_visibility_evidence_json(path) for path in evidence_json]
    merged = phase11_canary_visibility_bundle_service.merge_phase11_canary_visibility_evidence(evidences, customer_key=customer_key, lane=lane, port=port) if evidences else None
    report = phase11_canary_final_check_report_visibility_service.build_phase11_canary_final_check_report_visibility_report(cfg, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live, evidence=merged)
    if write_evidence_json:
        phase11_canary_final_check_report_visibility_service.write_final_check_report_visibility_evidence_json(report=report, path=write_evidence_json, overwrite=overwrite_evidence_json)
    _print_output(report, output)


@production_app.command("canary-rollback-restore-visibility")
def production_canary_rollback_restore_visibility(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    collect_live: bool = typer.Option(False, "--collect-live/--no-collect-live"),
    write_evidence_json: Path | None = typer.Option(None, "--write-evidence-json"),
    overwrite_evidence_json: bool = typer.Option(False, "--overwrite-evidence-json"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_canary_rollback_restore_visibility_service.build_phase11_canary_rollback_restore_visibility_report(_load(config), customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live)
    if write_evidence_json:
        phase11_canary_rollback_restore_visibility_service.write_rollback_restore_visibility_evidence_json(report=report, path=write_evidence_json, overwrite=overwrite_evidence_json)
    _print_output(report, output)


@production_app.command("canary-acceptance-review")
def production_canary_acceptance_review(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    evidence_json: Path | None = typer.Option(None, "--evidence-json"),
    collect_live: bool = typer.Option(False, "--collect-live/--no-collect-live"),
    collect_visibility: bool = typer.Option(False, "--collect-visibility/--no-collect-visibility"),
    visibility_json: list[Path] = typer.Option([], "--visibility-json"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    cfg = _load(config)
    evidence = phase11_canary_acceptance_review_service.load_phase11_canary_acceptance_evidence_json(evidence_json) if evidence_json else None
    expected_backend_target: str | None = None
    if collect_live:
        live_report = phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report(
            cfg, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version
        )
        live_ev = phase11_canary_acceptance_review_service.Phase11CanaryAcceptanceEvidence.from_dict(live_report["evidence"])
        expected_backend_target = live_ev.canary_nat_target
        evidence = phase11_live_canary_evidence_collector_service.merge_phase11_evidence(live_ev, evidence) if evidence else live_ev
    if collect_visibility:
        visibility_evidences = [phase11_canary_visibility_bundle_service.load_phase11_canary_visibility_evidence_json(path) for path in visibility_json]
        visibility_evidence = phase11_canary_visibility_bundle_service.merge_phase11_canary_visibility_evidence(
            visibility_evidences,
            customer_key=customer_key,
            lane=lane,
            port=port,
            expected_backend_target=expected_backend_target,
        ) if visibility_evidences else None
        visibility_report = phase11_canary_visibility_bundle_service.build_phase11_canary_visibility_bundle_report(
            cfg, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live, evidence=visibility_evidence
        )
        vis = visibility_report["visibility"]
        base = evidence or phase11_canary_acceptance_review_service.Phase11CanaryAcceptanceEvidence()
        mapping = {
            "canary_customer_db_visibility": "canary_customer_db_visible",
            "usage_counters_visibility": "usage_visibility_ok",
            "reject_counters_visibility": "reject_visibility_ok",
            "active_recent_sessions_visibility": "session_visibility_ok",
            "unique_ips_visibility": "unique_ip_visibility_ok",
            "unique_workers_visibility": "worker_visibility_ok",
            "abuse_coverage_visibility": "abuse_coverage_ok",
            "final_check_report_visibility": "final_check_report_ok",
        }
        for k, fld in mapping.items():
            if vis.get(k, {}).get("status") == "PRESENT":
                setattr(base, fld, True)
        rr = vis.get("rollback_or_restore_plan_visibility", {})
        if rr.get("status") == "PRESENT":
            if not base.rollback_reference:
                base.rollback_reference = rr.get("reference")
        runtime = visibility_report.get("runtime_evidence", {})
        if isinstance(runtime, dict):
            for fld in ("conntrack_assured", "stratum_subscribe_ok", "stratum_authorize_ok", "stratum_set_difficulty_seen", "stratum_notify_seen", "forwarder_pool_seen", "bridge_loopback_seen"):
                if runtime.get(fld) is True:
                    setattr(base, fld, True)
        evidence = base
    report = phase11_canary_acceptance_review_service.build_phase11_canary_acceptance_review_report(
        cfg, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, evidence=evidence
    )
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    for key in ("component", "final_decision", "final_decision_reason", "no_onboarding_authorized", "blockers", "missing_visibility_primitives", "missing_evidence_primitives", "next_required_step"):
        typer.echo(f"{key}: {report[key]}")

@production_app.command("canary-usage-visibility")
def production_canary_usage_visibility(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    evidence_json: Path | None = typer.Option(None, "--evidence-json"),
    collect_live: bool = typer.Option(False, "--collect-live/--no-collect-live"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    cfg = _load(config)
    evidence = phase11_canary_usage_visibility_service.load_phase11_canary_usage_visibility_evidence_json(evidence_json) if evidence_json else None
    report = phase11_canary_usage_visibility_service.build_phase11_canary_usage_visibility_report(
        cfg, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live, evidence=evidence
    )
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    for key in ("component", "final_decision", "blockers", "warnings", "next_required_step"):
        typer.echo(f"{key}: {report[key]}")





@production_app.command("canary-acceptance-decision")
def production_canary_acceptance_decision(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    backend_target: str = typer.Option("172.18.0.3:60010", "--backend-target"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    evidence_pack_dir: Path = typer.Option(..., "--evidence-pack-dir"),
    evidence_archive_path: Path | None = typer.Option(None, "--evidence-archive-path"),
    expected_archive_sha256: str | None = typer.Option(None, "--expected-archive-sha256"),
    operator: str = typer.Option(..., "--operator"),
    reason: str = typer.Option(..., "--reason"),
    operator_confirmed: bool = typer.Option(False, "--operator-confirmed"),
    i_have_reviewed_evidence_pack: bool = typer.Option(False, "--i-have-reviewed-evidence-pack"),
    i_confirm_no_real_customer_onboarding: bool = typer.Option(False, "--i-confirm-no-real-customer-onboarding"),
    i_confirm_no_production_traffic_authorized: bool = typer.Option(False, "--i-confirm-no-production-traffic-authorized"),
    i_confirm_phase11_not_final_accepted: bool = typer.Option(False, "--i-confirm-phase11-not-final-accepted"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_canary_acceptance_decision_service.build_phase11_canary_acceptance_decision_report(
        _load(config), customer_key=customer_key, lane=lane, port=port, backend_target=backend_target,
        expected_version=expected_version, farm5_baseline_version=farm5_baseline_version,
        evidence_pack_dir=evidence_pack_dir, evidence_archive_path=evidence_archive_path,
        expected_archive_sha256=expected_archive_sha256, operator=operator, reason=reason,
        operator_confirmed=operator_confirmed, i_have_reviewed_evidence_pack=i_have_reviewed_evidence_pack,
        i_confirm_no_real_customer_onboarding=i_confirm_no_real_customer_onboarding,
        i_confirm_no_production_traffic_authorized=i_confirm_no_production_traffic_authorized,
        i_confirm_phase11_not_final_accepted=i_confirm_phase11_not_final_accepted,
    )
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    for key in ("component", "final_decision", "phase11d_canary_accepted", "phase11_accepted", "limited_onboarding_allowed", "production_traffic_enabled", "no_onboarding_authorized", "next_required_step", "blockers"):
        typer.echo(f"{key}: {report.get(key)}")


@production_app.command("limited-onboarding-gate")
def production_limited_onboarding_gate(
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    canary_acceptance_decision_json: Path = typer.Option(..., "--canary-acceptance-decision-json"),
    operator: str = typer.Option(..., "--operator"),
    reason: str = typer.Option(..., "--reason"),
    operator_confirmed: bool = typer.Option(False, "--operator-confirmed"),
    i_understand_no_real_customer_onboarding_yet: bool = typer.Option(False, "--i-understand-no-real-customer-onboarding-yet"),
    i_understand_no_production_traffic_yet: bool = typer.Option(False, "--i-understand-no-production-traffic-yet"),
    i_understand_phase11e_requires_separate_execution_gate: bool = typer.Option(False, "--i-understand-phase11e-requires-separate-execution-gate"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_limited_onboarding_gate_service.build_phase11_limited_onboarding_gate_report(
        _load(config), expected_version=expected_version, farm5_baseline_version=farm5_baseline_version,
        canary_acceptance_decision_json=canary_acceptance_decision_json, operator=operator, reason=reason,
        operator_confirmed=operator_confirmed, i_understand_no_real_customer_onboarding_yet=i_understand_no_real_customer_onboarding_yet,
        i_understand_no_production_traffic_yet=i_understand_no_production_traffic_yet,
        i_understand_phase11e_requires_separate_execution_gate=i_understand_phase11e_requires_separate_execution_gate,
    )
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    for key in ("component", "final_decision", "phase11d_canary_accepted", "phase11e_gate_ready", "phase11e_execution_allowed", "phase11_accepted", "limited_onboarding_allowed", "production_traffic_enabled", "no_onboarding_authorized", "next_required_step", "blockers"):
        typer.echo(f"{key}: {report.get(key)}")



@production_app.command("limited-onboarding-execution-gate")
def production_limited_onboarding_execution_gate(
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    limited_onboarding_gate_json: Path = typer.Option(..., "--limited-onboarding-gate-json"),
    candidate_customer_key: str = typer.Option(..., "--candidate-customer-key"),
    candidate_lane: str = typer.Option("btc", "--candidate-lane"),
    candidate_public_port: int = typer.Option(..., "--candidate-public-port"),
    candidate_backend_target: str = typer.Option("172.18.0.3:60010", "--candidate-backend-target"),
    candidate_description: str = typer.Option(..., "--candidate-description"),
    operator: str = typer.Option(..., "--operator"),
    reason: str = typer.Option(..., "--reason"),
    operator_confirmed: bool = typer.Option(False, "--operator-confirmed"),
    i_understand_this_does_not_onboard_customer: bool = typer.Option(False, "--i-understand-this-does-not-onboard-customer"),
    i_understand_no_firewall_apply_yet: bool = typer.Option(False, "--i-understand-no-firewall-apply-yet"),
    i_understand_no_production_traffic_yet: bool = typer.Option(False, "--i-understand-no-production-traffic-yet"),
    i_understand_next_pr_must_execute_controlled_single_customer: bool = typer.Option(False, "--i-understand-next-pr-must-execute-controlled-single-customer"),
    i_confirm_rollback_plan_required: bool = typer.Option(False, "--i-confirm-rollback-plan-required"),
    i_confirm_restart_test_required: bool = typer.Option(False, "--i-confirm-restart-test-required"),
    i_confirm_abuse_1h_coverage_required: bool = typer.Option(False, "--i-confirm-abuse-1h-coverage-required"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_limited_onboarding_execution_gate_service.build_phase11_limited_onboarding_execution_gate_report(
        _load(config), expected_version=expected_version, farm5_baseline_version=farm5_baseline_version,
        limited_onboarding_gate_json=limited_onboarding_gate_json, candidate_customer_key=candidate_customer_key,
        candidate_lane=candidate_lane, candidate_public_port=candidate_public_port,
        candidate_backend_target=candidate_backend_target, candidate_description=candidate_description,
        operator=operator, reason=reason, operator_confirmed=operator_confirmed,
        i_understand_this_does_not_onboard_customer=i_understand_this_does_not_onboard_customer,
        i_understand_no_firewall_apply_yet=i_understand_no_firewall_apply_yet,
        i_understand_no_production_traffic_yet=i_understand_no_production_traffic_yet,
        i_understand_next_pr_must_execute_controlled_single_customer=i_understand_next_pr_must_execute_controlled_single_customer,
        i_confirm_rollback_plan_required=i_confirm_rollback_plan_required,
        i_confirm_restart_test_required=i_confirm_restart_test_required,
        i_confirm_abuse_1h_coverage_required=i_confirm_abuse_1h_coverage_required,
    )
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    for key in ("component", "final_decision", "phase11e_execution_gate_ready", "phase11e_execution_allowed", "candidate_customer_key", "candidate_lane", "candidate_public_port", "customer_created", "limited_onboarding_allowed", "production_traffic_enabled", "mutation_performed", "next_required_step", "blockers"):
        typer.echo(f"{key}: {report.get(key)}")



@production_app.command("single-customer-staging")
def production_single_customer_staging(
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    execution_gate_json: Path = typer.Option(..., "--execution-gate-json"),
    candidate_customer_key: str = typer.Option(..., "--candidate-customer-key"),
    candidate_lane: str = typer.Option("btc", "--candidate-lane"),
    candidate_public_port: int = typer.Option(..., "--candidate-public-port"),
    candidate_backend_target: str = typer.Option("172.18.0.3:60010", "--candidate-backend-target"),
    candidate_description: str = typer.Option(..., "--candidate-description"),
    mode: Literal["plan", "execute-db-only"] = typer.Option("plan", "--mode"),
    operator: str = typer.Option(..., "--operator"),
    reason: str = typer.Option(..., "--reason"),
    operator_confirmed: bool = typer.Option(False, "--operator-confirmed"),
    i_understand_db_only_staging: bool = typer.Option(False, "--i-understand-db-only-staging"),
    i_understand_no_firewall_apply: bool = typer.Option(False, "--i-understand-no-firewall-apply"),
    i_understand_no_nat_apply: bool = typer.Option(False, "--i-understand-no-nat-apply"),
    i_understand_no_production_traffic: bool = typer.Option(False, "--i-understand-no-production-traffic"),
    i_understand_single_customer_limit: bool = typer.Option(False, "--i-understand-single-customer-limit"),
    i_confirm_port_not_live_until_firewall_gate: bool = typer.Option(False, "--i-confirm-port-not-live-until-firewall-gate"),
    i_confirm_rollback_plan_required: bool = typer.Option(False, "--i-confirm-rollback-plan-required"),
    i_confirm_restart_test_required_before_traffic: bool = typer.Option(False, "--i-confirm-restart-test-required-before-traffic"),
    i_confirm_abuse_1h_required_before_traffic: bool = typer.Option(False, "--i-confirm-abuse-1h-required-before-traffic"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_single_customer_staging_service.build_phase11_single_customer_staging_report(
        _load(config), expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, execution_gate_json=execution_gate_json,
        candidate_customer_key=candidate_customer_key, candidate_lane=candidate_lane, candidate_public_port=candidate_public_port,
        candidate_backend_target=candidate_backend_target, candidate_description=candidate_description, mode=mode, operator=operator, reason=reason,
        operator_confirmed=operator_confirmed, i_understand_db_only_staging=i_understand_db_only_staging, i_understand_no_firewall_apply=i_understand_no_firewall_apply,
        i_understand_no_nat_apply=i_understand_no_nat_apply, i_understand_no_production_traffic=i_understand_no_production_traffic,
        i_understand_single_customer_limit=i_understand_single_customer_limit, i_confirm_port_not_live_until_firewall_gate=i_confirm_port_not_live_until_firewall_gate,
        i_confirm_rollback_plan_required=i_confirm_rollback_plan_required, i_confirm_restart_test_required_before_traffic=i_confirm_restart_test_required_before_traffic,
        i_confirm_abuse_1h_required_before_traffic=i_confirm_abuse_1h_required_before_traffic,
    )
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    for key in ("component", "final_decision", "mode", "candidate_customer_key", "candidate_lane", "candidate_public_port", "phase11e_single_customer_staging_ready", "phase11e_db_staging_allowed", "customer_created", "customer_updated", "db_mutation_performed", "firewall_mutation_performed", "nat_mutation_performed", "production_traffic_enabled", "limited_onboarding_allowed", "mutation_performed", "next_required_step", "blockers"):
        typer.echo(f"{key}: {report.get(key)}")



@production_app.command("single-customer-firewall-plan-gate")
def production_single_customer_firewall_plan_gate(
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    staging_execute_json: Path = typer.Option(..., "--staging-execute-json"),
    candidate_customer_key: str = typer.Option("limited-btc-001", "--candidate-customer-key"),
    candidate_lane: str = typer.Option("btc", "--candidate-lane"),
    candidate_public_port: int = typer.Option(20101, "--candidate-public-port"),
    candidate_backend_target: str = typer.Option("172.18.0.3:60010", "--candidate-backend-target"),
    operator: str = typer.Option(..., "--operator"),
    reason: str = typer.Option(..., "--reason"),
    operator_confirmed: bool = typer.Option(False, "--operator-confirmed"),
    i_understand_plan_only: bool = typer.Option(False, "--i-understand-plan-only"),
    i_understand_no_firewall_apply: bool = typer.Option(False, "--i-understand-no-firewall-apply"),
    i_understand_no_nat_apply: bool = typer.Option(False, "--i-understand-no-nat-apply"),
    i_understand_no_production_traffic: bool = typer.Option(False, "--i-understand-no-production-traffic"),
    i_understand_no_miner_traffic_yet: bool = typer.Option(False, "--i-understand-no-miner-traffic-yet"),
    i_confirm_restore_point_required_before_apply: bool = typer.Option(False, "--i-confirm-restore-point-required-before-apply"),
    i_confirm_lock_required_before_apply: bool = typer.Option(False, "--i-confirm-lock-required-before-apply"),
    i_confirm_rollback_plan_required_before_apply: bool = typer.Option(False, "--i-confirm-rollback-plan-required-before-apply"),
    i_confirm_restart_test_required_before_traffic: bool = typer.Option(False, "--i-confirm-restart-test-required-before-traffic"),
    i_confirm_abuse_1h_required_before_traffic: bool = typer.Option(False, "--i-confirm-abuse-1h-required-before-traffic"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_single_customer_firewall_plan_gate_service.build_phase11_single_customer_firewall_plan_gate_report(
        _load(config), expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, staging_execute_json=staging_execute_json,
        candidate_customer_key=candidate_customer_key, candidate_lane=candidate_lane, candidate_public_port=candidate_public_port,
        candidate_backend_target=candidate_backend_target, operator=operator, reason=reason, operator_confirmed=operator_confirmed,
        i_understand_plan_only=i_understand_plan_only, i_understand_no_firewall_apply=i_understand_no_firewall_apply,
        i_understand_no_nat_apply=i_understand_no_nat_apply, i_understand_no_production_traffic=i_understand_no_production_traffic,
        i_understand_no_miner_traffic_yet=i_understand_no_miner_traffic_yet,
        i_confirm_restore_point_required_before_apply=i_confirm_restore_point_required_before_apply,
        i_confirm_lock_required_before_apply=i_confirm_lock_required_before_apply,
        i_confirm_rollback_plan_required_before_apply=i_confirm_rollback_plan_required_before_apply,
        i_confirm_restart_test_required_before_traffic=i_confirm_restart_test_required_before_traffic,
        i_confirm_abuse_1h_required_before_traffic=i_confirm_abuse_1h_required_before_traffic,
    )
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    for key in ("component", "final_decision", "candidate_customer_key", "candidate_public_port", "phase11e_firewall_plan_gate_ready", "firewall_plan_generated", "firewall_apply_allowed", "nat_apply_allowed", "iptables_restore_authorized", "production_traffic_enabled", "miner_traffic_allowed", "mutation_performed", "next_required_step", "blockers"):
        typer.echo(f"{key}: {report.get(key)}")


@production_app.command("single-customer-firewall-apply-gate")
def production_single_customer_firewall_apply_gate(
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    firewall_plan_gate_json: Path = typer.Option(..., "--firewall-plan-gate-json"),
    candidate_customer_key: str = typer.Option("limited-btc-001", "--candidate-customer-key"),
    candidate_lane: str = typer.Option("btc", "--candidate-lane"),
    candidate_public_port: int = typer.Option(20101, "--candidate-public-port"),
    candidate_backend_target: str = typer.Option("172.18.0.3:60010", "--candidate-backend-target"),
    operator: str = typer.Option(..., "--operator"),
    reason: str = typer.Option(..., "--reason"),
    operator_confirmed: bool = typer.Option(False, "--operator-confirmed"),
    i_understand_apply_gate_only: bool = typer.Option(False, "--i-understand-apply-gate-only"),
    i_understand_no_firewall_apply_in_this_pr: bool = typer.Option(False, "--i-understand-no-firewall-apply-in-this-pr"),
    i_understand_no_nat_apply_in_this_pr: bool = typer.Option(False, "--i-understand-no-nat-apply-in-this-pr"),
    i_understand_no_iptables_restore_in_this_pr: bool = typer.Option(False, "--i-understand-no-iptables-restore-in-this-pr"),
    i_understand_no_production_traffic: bool = typer.Option(False, "--i-understand-no-production-traffic"),
    i_understand_no_miner_traffic_yet: bool = typer.Option(False, "--i-understand-no-miner-traffic-yet"),
    i_confirm_limited_single_customer_scope: bool = typer.Option(False, "--i-confirm-limited-single-customer-scope"),
    i_confirm_restore_point_required_before_apply: bool = typer.Option(False, "--i-confirm-restore-point-required-before-apply"),
    i_confirm_operator_lock_required_before_apply: bool = typer.Option(False, "--i-confirm-operator-lock-required-before-apply"),
    i_confirm_rollback_artifact_required_before_apply: bool = typer.Option(False, "--i-confirm-rollback-artifact-required-before-apply"),
    i_confirm_pre_apply_snapshot_required_before_apply: bool = typer.Option(False, "--i-confirm-pre-apply-snapshot-required-before-apply"),
    i_confirm_post_apply_verification_required: bool = typer.Option(False, "--i-confirm-post-apply-verification-required"),
    i_confirm_runtime_path_evidence_required_after_apply: bool = typer.Option(False, "--i-confirm-runtime-path-evidence-required-after-apply"),
    i_confirm_abuse_1h_evidence_required_before_customer_traffic: bool = typer.Option(False, "--i-confirm-abuse-1h-evidence-required-before-customer-traffic"),
    i_confirm_restart_container_order_evidence_required_before_customer_traffic: bool = typer.Option(False, "--i-confirm-restart-container-order-evidence-required-before-customer-traffic"),
    live_snapshot_file: Path | None = typer.Option(None, "--live-snapshot-file"),
    collect_live: bool = typer.Option(False, "--collect-live/--no-collect-live"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_single_customer_firewall_apply_gate_service.build_phase11_single_customer_firewall_apply_gate_report(
        _load(config), expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, firewall_plan_gate_json=firewall_plan_gate_json,
        candidate_customer_key=candidate_customer_key, candidate_lane=candidate_lane, candidate_public_port=candidate_public_port, candidate_backend_target=candidate_backend_target,
        operator=operator, reason=reason, operator_confirmed=operator_confirmed, i_understand_apply_gate_only=i_understand_apply_gate_only,
        i_understand_no_firewall_apply_in_this_pr=i_understand_no_firewall_apply_in_this_pr, i_understand_no_nat_apply_in_this_pr=i_understand_no_nat_apply_in_this_pr,
        i_understand_no_iptables_restore_in_this_pr=i_understand_no_iptables_restore_in_this_pr, i_understand_no_production_traffic=i_understand_no_production_traffic,
        i_understand_no_miner_traffic_yet=i_understand_no_miner_traffic_yet, i_confirm_limited_single_customer_scope=i_confirm_limited_single_customer_scope,
        i_confirm_restore_point_required_before_apply=i_confirm_restore_point_required_before_apply, i_confirm_operator_lock_required_before_apply=i_confirm_operator_lock_required_before_apply,
        i_confirm_rollback_artifact_required_before_apply=i_confirm_rollback_artifact_required_before_apply, i_confirm_pre_apply_snapshot_required_before_apply=i_confirm_pre_apply_snapshot_required_before_apply,
        i_confirm_post_apply_verification_required=i_confirm_post_apply_verification_required, i_confirm_runtime_path_evidence_required_after_apply=i_confirm_runtime_path_evidence_required_after_apply,
        i_confirm_abuse_1h_evidence_required_before_customer_traffic=i_confirm_abuse_1h_evidence_required_before_customer_traffic,
        i_confirm_restart_container_order_evidence_required_before_customer_traffic=i_confirm_restart_container_order_evidence_required_before_customer_traffic,
        live_snapshot_file=live_snapshot_file, collect_live=collect_live,
    )
    if output == "json": typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    for key in ("component", "final_decision", "candidate_customer_key", "candidate_public_port", "phase11e_firewall_apply_gate_ready", "firewall_apply_execution_allowed", "firewall_apply_allowed", "nat_apply_allowed", "iptables_restore_authorized", "production_traffic_enabled", "miner_traffic_allowed", "mutation_performed", "apply_gate_package_generated", "firewall_plan_gate_json_sha256", "plan_summary_sha256", "next_required_step", "blockers"):
        typer.echo(f"{key}: {report.get(key)}")



@production_app.command("single-customer-firewall-apply-execute")
def production_single_customer_firewall_apply_execute(
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    apply_gate_json: Path = typer.Option(..., "--apply-gate-json"),
    apply_gate_json_file_sha256: str | None = typer.Option(None, "--apply-gate-json-file-sha256"),
    operator: str = typer.Option(..., "--operator"), reason: str = typer.Option(..., "--reason"),
    operator_confirmed: bool = typer.Option(False, "--operator-confirmed"),
    i_understand_single_customer_apply_execution: bool = typer.Option(False, "--i-understand-single-customer-apply-execution"),
    i_understand_firewall_nat_apply_will_mutate_host_in_execute_mode: bool = typer.Option(False, "--i-understand-firewall-nat-apply-will-mutate-host-in-execute-mode"),
    i_understand_no_production_traffic_acceptance: bool = typer.Option(False, "--i-understand-no-production-traffic-acceptance"),
    i_understand_no_miner_traffic_acceptance: bool = typer.Option(False, "--i-understand-no-miner-traffic-acceptance"),
    i_confirm_pre_apply_snapshot_taken: bool = typer.Option(False, "--i-confirm-pre-apply-snapshot-taken"),
    i_confirm_restore_point_created: bool = typer.Option(False, "--i-confirm-restore-point-created"),
    i_confirm_operator_lock_acquired: bool = typer.Option(False, "--i-confirm-operator-lock-acquired"),
    i_confirm_rollback_artifact_created: bool = typer.Option(False, "--i-confirm-rollback-artifact-created"),
    i_confirm_canary_20001_must_be_preserved: bool = typer.Option(False, "--i-confirm-canary-20001-must-be-preserved"),
    i_confirm_post_apply_verification_required: bool = typer.Option(False, "--i-confirm-post-apply-verification-required"),
    i_confirm_runtime_path_evidence_required_after_apply: bool = typer.Option(False, "--i-confirm-runtime-path-evidence-required-after-apply"),
    i_confirm_abuse_1h_evidence_required_before_customer_traffic: bool = typer.Option(False, "--i-confirm-abuse-1h-evidence-required-before-customer-traffic"),
    i_confirm_restart_container_order_evidence_required_before_limited_acceptance: bool = typer.Option(False, "--i-confirm-restart-container-order-evidence-required-before-limited-acceptance"),
    pre_apply_snapshot_file: Path | None = typer.Option(None, "--pre-apply-snapshot-file"),
    rollback_artifact_file: Path | None = typer.Option(None, "--rollback-artifact-file"),
    restore_point_path: Path | None = typer.Option(None, "--restore-point-path"),
    operator_lock_id: str | None = typer.Option(None, "--operator-lock-id"),
    live_snapshot_file: Path | None = typer.Option(None, "--live-snapshot-file"), collect_live: bool = typer.Option(False, "--collect-live/--no-collect-live"), execute: bool = typer.Option(False, "--execute/--no-execute"), output: Literal["human","json"] = typer.Option("human", "--output"), config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_single_customer_firewall_apply_execution_service.build_phase11_single_customer_firewall_apply_execution_report(_load(config), expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, apply_gate_json=apply_gate_json, apply_gate_json_file_sha256=apply_gate_json_file_sha256, operator=operator, reason=reason, operator_confirmed=operator_confirmed, i_understand_single_customer_apply_execution=i_understand_single_customer_apply_execution, i_understand_firewall_nat_apply_will_mutate_host_in_execute_mode=i_understand_firewall_nat_apply_will_mutate_host_in_execute_mode, i_understand_no_production_traffic_acceptance=i_understand_no_production_traffic_acceptance, i_understand_no_miner_traffic_acceptance=i_understand_no_miner_traffic_acceptance, i_confirm_pre_apply_snapshot_taken=i_confirm_pre_apply_snapshot_taken, i_confirm_restore_point_created=i_confirm_restore_point_created, i_confirm_operator_lock_acquired=i_confirm_operator_lock_acquired, i_confirm_rollback_artifact_created=i_confirm_rollback_artifact_created, i_confirm_canary_20001_must_be_preserved=i_confirm_canary_20001_must_be_preserved, i_confirm_post_apply_verification_required=i_confirm_post_apply_verification_required, i_confirm_runtime_path_evidence_required_after_apply=i_confirm_runtime_path_evidence_required_after_apply, i_confirm_abuse_1h_evidence_required_before_customer_traffic=i_confirm_abuse_1h_evidence_required_before_customer_traffic, i_confirm_restart_container_order_evidence_required_before_limited_acceptance=i_confirm_restart_container_order_evidence_required_before_limited_acceptance, pre_apply_snapshot_file=pre_apply_snapshot_file, rollback_artifact_file=rollback_artifact_file, restore_point_path=restore_point_path, operator_lock_id=operator_lock_id, live_snapshot_file=live_snapshot_file, collect_live=collect_live, execute=execute)
    if output == "json": typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    for key in ("component","final_decision","apply_execution_ready","execute_requested","firewall_apply_execution_allowed","iptables_restore_authorized","mutation_performed","generated_apply_payload_sha256","next_required_step","blockers"):
        typer.echo(f"{key}: {report.get(key)}")


@production_app.command("single-customer-post-apply-evidence")
def production_single_customer_post_apply_evidence(
    expected_version: str = typer.Option("0.1.205", "--expected-version"),
    execution_json: Path = typer.Option(..., "--execution-json"),
    execution_json_sha256: str = typer.Option("bd8f3900db3d3fb2647ead8cec47c870f4cd00ebaf52b68bc329a065a65b880b", "--execution-json-sha256"),
    pre_apply_snapshot_file: Path = typer.Option(..., "--pre-apply-snapshot-file"),
    pre_apply_snapshot_sha256: str = typer.Option("3a493643f796f10f37443152e99adda928f30c82067fc98a4a748f52d2767494", "--pre-apply-snapshot-sha256"),
    post_apply_snapshot_file: Path = typer.Option(..., "--post-apply-snapshot-file"),
    post_apply_snapshot_sha256: str = typer.Option("c6330a80954f7268ccec311750751b45464c84c2efd627509d1ecee274eec27b", "--post-apply-snapshot-sha256"),
    apply_gate_json: Path = typer.Option(..., "--apply-gate-json"),
    apply_gate_json_sha256: str = typer.Option("500978bf2b156a5da6a1b299e41d346cadf2b20b15280212c607c51c9a307b1a", "--apply-gate-json-sha256"),
    plan_gate_json: Path = typer.Option(..., "--plan-gate-json"),
    plan_gate_json_sha256: str = typer.Option("0893d1d63b7cb7f60a3473ad9f922c3f65bc9b3e6ff8d5b84aecfa701d45c438", "--plan-gate-json-sha256"),
    candidate_customer_key: str = typer.Option("limited-btc-001", "--candidate-customer-key"),
    candidate_lane: str = typer.Option("btc", "--candidate-lane"),
    candidate_public_port: int = typer.Option(20101, "--candidate-public-port"),
    candidate_backend_target: str = typer.Option("172.18.0.3:60010", "--candidate-backend-target"),
    operator: str = typer.Option(..., "--operator"), reason: str = typer.Option(..., "--reason"),
    operator_confirmed: bool = typer.Option(False, "--operator-confirmed"),
    i_understand_post_apply_evidence_only: bool = typer.Option(False, "--i-understand-post-apply-evidence-only"),
    i_understand_no_additional_firewall_apply: bool = typer.Option(False, "--i-understand-no-additional-firewall-apply"),
    i_understand_no_production_traffic_acceptance: bool = typer.Option(False, "--i-understand-no-production-traffic-acceptance"),
    i_understand_no_miner_traffic_acceptance: bool = typer.Option(False, "--i-understand-no-miner-traffic-acceptance"),
    i_confirm_runtime_path_evidence_required_next: bool = typer.Option(False, "--i-confirm-runtime-path-evidence-required-next"),
    i_confirm_stratum_transcript_required_next: bool = typer.Option(False, "--i-confirm-stratum-transcript-required-next"),
    i_confirm_visibility_bundle_required_next: bool = typer.Option(False, "--i-confirm-visibility-bundle-required-next"),
    i_confirm_abuse_1h_required_before_customer_traffic: bool = typer.Option(False, "--i-confirm-abuse-1h-required-before-customer-traffic"),
    i_confirm_restart_container_order_required_before_limited_acceptance: bool = typer.Option(False, "--i-confirm-restart-container-order-required-before-limited-acceptance"),
    live_snapshot_file: Path | None = typer.Option(None, "--live-snapshot-file"),
    collect_live: bool = typer.Option(False, "--collect-live/--no-collect-live"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_single_customer_post_apply_evidence_service.build_phase11_single_customer_post_apply_evidence_report(_load(config), expected_version=expected_version, execution_json=execution_json, execution_json_sha256=execution_json_sha256, pre_apply_snapshot_file=pre_apply_snapshot_file, pre_apply_snapshot_sha256=pre_apply_snapshot_sha256, post_apply_snapshot_file=post_apply_snapshot_file, post_apply_snapshot_sha256=post_apply_snapshot_sha256, apply_gate_json=apply_gate_json, apply_gate_json_sha256=apply_gate_json_sha256, plan_gate_json=plan_gate_json, plan_gate_json_sha256=plan_gate_json_sha256, candidate_customer_key=candidate_customer_key, candidate_lane=candidate_lane, candidate_public_port=candidate_public_port, candidate_backend_target=candidate_backend_target, operator=operator, reason=reason, operator_confirmed=operator_confirmed, i_understand_post_apply_evidence_only=i_understand_post_apply_evidence_only, i_understand_no_additional_firewall_apply=i_understand_no_additional_firewall_apply, i_understand_no_production_traffic_acceptance=i_understand_no_production_traffic_acceptance, i_understand_no_miner_traffic_acceptance=i_understand_no_miner_traffic_acceptance, i_confirm_runtime_path_evidence_required_next=i_confirm_runtime_path_evidence_required_next, i_confirm_stratum_transcript_required_next=i_confirm_stratum_transcript_required_next, i_confirm_visibility_bundle_required_next=i_confirm_visibility_bundle_required_next, i_confirm_abuse_1h_required_before_customer_traffic=i_confirm_abuse_1h_required_before_customer_traffic, i_confirm_restart_container_order_required_before_limited_acceptance=i_confirm_restart_container_order_required_before_limited_acceptance, live_snapshot_file=live_snapshot_file, collect_live=collect_live)
    if output == "json": typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    for key in ("component","final_decision","post_apply_evidence_ready","controlled_apply_recorded","next_required_step","blockers"):
        typer.echo(f"{key}: {report.get(key)}")


@production_app.command("single-customer-runtime-path-evidence")
def production_single_customer_runtime_path_evidence(
    expected_version: str = typer.Option("0.1.206", "--expected-version"),
    post_apply_evidence_json: Path = typer.Option(..., "--post-apply-evidence-json"),
    post_apply_evidence_json_sha256: str = typer.Option(..., "--post-apply-evidence-json-sha256"),
    operator: str = typer.Option(..., "--operator"), reason: str = typer.Option(..., "--reason"),
    operator_confirmed: bool = typer.Option(False, "--operator-confirmed"),
    i_understand_runtime_evidence_only: bool = typer.Option(False, "--i-understand-runtime-evidence-only"),
    i_understand_no_production_traffic_acceptance: bool = typer.Option(False, "--i-understand-no-production-traffic-acceptance"),
    i_understand_no_miner_traffic_acceptance: bool = typer.Option(False, "--i-understand-no-miner-traffic-acceptance"),
    i_understand_no_db_activation: bool = typer.Option(False, "--i-understand-no-db-activation"),
    i_confirm_stratum_transcript_required: bool = typer.Option(False, "--i-confirm-stratum-transcript-required"),
    i_confirm_visibility_bundle_required: bool = typer.Option(False, "--i-confirm-visibility-bundle-required"),
    i_confirm_abuse_1h_required_before_customer_traffic: bool = typer.Option(False, "--i-confirm-abuse-1h-required-before-customer-traffic"),
    i_confirm_restart_container_order_required_before_limited_acceptance: bool = typer.Option(False, "--i-confirm-restart-container-order-required-before-limited-acceptance"),
    live_snapshot_file: Path | None = typer.Option(None, "--live-snapshot-file"),
    conntrack_snapshot_file: Path | None = typer.Option(None, "--conntrack-snapshot-file"),
    forwarder_log_file: Path | None = typer.Option(None, "--forwarder-log-file"),
    bridge_log_file: Path | None = typer.Option(None, "--bridge-log-file"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_single_customer_runtime_path_evidence_service.build_phase11_single_customer_runtime_path_evidence_report(_load(config), expected_version=expected_version, post_apply_evidence_json=post_apply_evidence_json, post_apply_evidence_json_sha256=post_apply_evidence_json_sha256, operator=operator, reason=reason, operator_confirmed=operator_confirmed, i_understand_runtime_evidence_only=i_understand_runtime_evidence_only, i_understand_no_production_traffic_acceptance=i_understand_no_production_traffic_acceptance, i_understand_no_miner_traffic_acceptance=i_understand_no_miner_traffic_acceptance, i_understand_no_db_activation=i_understand_no_db_activation, i_confirm_stratum_transcript_required=i_confirm_stratum_transcript_required, i_confirm_visibility_bundle_required=i_confirm_visibility_bundle_required, i_confirm_abuse_1h_required_before_customer_traffic=i_confirm_abuse_1h_required_before_customer_traffic, i_confirm_restart_container_order_required_before_limited_acceptance=i_confirm_restart_container_order_required_before_limited_acceptance, live_snapshot_file=live_snapshot_file, conntrack_snapshot_file=conntrack_snapshot_file, forwarder_log_file=forwarder_log_file, bridge_log_file=bridge_log_file)
    if output == "json": typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    for key in ("component","final_decision","runtime_path_evidence_ready","next_required_step","blockers"): typer.echo(f"{key}: {report.get(key)}")

@production_app.command("single-customer-stratum-transcript-evidence")
def production_single_customer_stratum_transcript_evidence(transcript_json: Path = typer.Option(..., "--transcript-json"), output: Literal["human", "json"] = typer.Option("human", "--output"), config: Path | None = typer.Option(None, "--config", "-c")) -> None:
    report = phase11_single_customer_stratum_transcript_evidence_service.build_phase11_single_customer_stratum_transcript_evidence_report(_load(config), transcript_json=transcript_json)
    if output == "json": typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    for key in ("component","final_decision","stratum_transcript_ready","blockers"): typer.echo(f"{key}: {report.get(key)}")

@production_app.command("single-customer-visibility-bundle")
def production_single_customer_visibility_bundle(runtime_path_evidence_json: Path = typer.Option(..., "--runtime-path-evidence-json"), runtime_path_evidence_json_sha256: str | None = typer.Option(None, "--runtime-path-evidence-json-sha256"), stratum_transcript_evidence_json: Path = typer.Option(..., "--stratum-transcript-evidence-json"), stratum_transcript_evidence_json_sha256: str | None = typer.Option(None, "--stratum-transcript-evidence-json-sha256"), output: Literal["human", "json"] = typer.Option("human", "--output"), config: Path | None = typer.Option(None, "--config", "-c")) -> None:
    report = phase11_single_customer_visibility_bundle_service.build_phase11_single_customer_visibility_bundle_report(_load(config), runtime_path_evidence_json=runtime_path_evidence_json, runtime_path_evidence_json_sha256=runtime_path_evidence_json_sha256, stratum_transcript_evidence_json=stratum_transcript_evidence_json, stratum_transcript_evidence_json_sha256=stratum_transcript_evidence_json_sha256)
    if output == "json": typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    for key in ("component","final_decision","visibility_bundle_ready","next_required_step","blockers"): typer.echo(f"{key}: {report.get(key)}")

@production_app.command("canary-evidence-pack")
def production_canary_evidence_pack(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    backend_target: str | None = typer.Option(None, "--backend-target"),
    pool_host: str = typer.Option("bitcoin.viabtc.io", "--pool-host"),
    pool_port: int = typer.Option(3333, "--pool-port"),
    bridge_target: str = typer.Option("127.0.0.1:20170", "--bridge-target"),
    out_dir: Path = typer.Option(..., "--out-dir"),
    overwrite_out_dir: bool = typer.Option(False, "--overwrite-out-dir/--no-overwrite-out-dir"),
    collect_live: bool = typer.Option(True, "--collect-live/--no-collect-live"),
    observation_seconds: int = typer.Option(60, "--observation-seconds"),
    observation_interval_seconds: int = typer.Option(2, "--observation-interval-seconds"),
    max_observation_seconds: int = typer.Option(300, "--max-observation-seconds"),
    source_ip: str | None = typer.Option(None, "--source-ip"),
    source_port: int | None = typer.Option(None, "--source-port"),
    external_stratum_transcript_json: list[Path] = typer.Option([], "--external-stratum-transcript-json"),
    connect_host: str | None = typer.Option(None, "--connect-host"),
    connect_port: int = typer.Option(20001, "--connect-port"),
    worker_name: str | None = typer.Option(None, "--worker-name"),
    worker_password: str = typer.Option("x", "--worker-password"),
    skip_worker_probe: bool = typer.Option(True, "--skip-worker-probe/--no-skip-worker-probe"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    report = phase11_canary_evidence_pack_service.build_phase11_canary_evidence_pack_report(
        _load(config), customer_key=customer_key, lane=lane, port=port, expected_version=expected_version,
        farm5_baseline_version=farm5_baseline_version, backend_target=backend_target, pool_host=pool_host, pool_port=pool_port,
        bridge_target=bridge_target, out_dir=out_dir, overwrite_out_dir=overwrite_out_dir, collect_live=collect_live,
        observation_seconds=observation_seconds, observation_interval_seconds=observation_interval_seconds, max_observation_seconds=max_observation_seconds,
        source_ip=source_ip, source_port=source_port, external_stratum_transcript_json=external_stratum_transcript_json,
        connect_host=connect_host, connect_port=connect_port, worker_name=worker_name, worker_password=worker_password, skip_worker_probe=skip_worker_probe,
    )
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    for key in ("component", "visibility_bundle_final_decision", "acceptance_review_final_decision", "missing_visibility_primitives", "missing_evidence_primitives", "next_required_step", "out_dir"):
        typer.echo(f"{key}: {report.get(key)}")

@production_app.command("canary-runtime-path-evidence")
def production_canary_runtime_path_evidence(
    config: Path | None = typer.Option(None, "--config", "-c"),
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    source_ip: str | None = typer.Option(None, "--source-ip"),
    source_port: int | None = typer.Option(None, "--source-port"),
    pool_host: str = typer.Option("bitcoin.viabtc.io", "--pool-host"),
    pool_port: int = typer.Option(3333, "--pool-port"),
    backend_target: str | None = typer.Option(None, "--backend-target"),
    bridge_target: str = typer.Option("127.0.0.1:20170", "--bridge-target"),
    collect_live: bool = typer.Option(False, "--collect-live/--no-collect-live"),
    conntrack_file: Path | None = typer.Option(None, "--conntrack-file"),
    forwarder_log_file: Path | None = typer.Option(None, "--forwarder-log-file"),
    bridge_log_file: Path | None = typer.Option(None, "--bridge-log-file"),
    write_evidence_json: Path | None = typer.Option(None, "--write-evidence-json"),
    overwrite_evidence_json: bool = typer.Option(False, "--overwrite-evidence-json"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
) -> None:
    cfg = _load(config)
    report = phase11_canary_runtime_path_evidence_service.build_phase11_canary_runtime_path_evidence_report(
        cfg, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version,
        source_ip=source_ip, source_port=source_port, pool_host=pool_host, pool_port=pool_port, backend_target=backend_target, bridge_target=bridge_target,
        collect_live=collect_live, conntrack_file=conntrack_file, forwarder_log_file=forwarder_log_file, bridge_log_file=bridge_log_file,
    )
    if write_evidence_json is not None:
        phase11_canary_runtime_path_evidence_service.write_runtime_path_evidence_json(report=report, path=write_evidence_json, overwrite=overwrite_evidence_json)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True)); return
    typer.echo(f"component: {report.get('component')}")
    typer.echo(f"final_decision: {report.get('final_decision')}")
    typer.echo(f"backend_target: {report.get('backend_target')}")
    typer.echo(f"blockers: {', '.join(report.get('blockers', [])) if report.get('blockers') else '-'}")

@production_app.command("canary-visibility-bundle")
def production_canary_visibility_bundle(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    expected_version: str = typer.Option(__version__, "--expected-version"),
    farm5_baseline_version: str = typer.Option("0.1.168", "--farm5-baseline-version"),
    evidence_json: list[Path] = typer.Option([], "--evidence-json"),
    collect_live: bool = typer.Option(False, "--collect-live/--no-collect-live"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    cfg = _load(config)
    expected_backend_target: str | None = None
    if collect_live:
        live_report = phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report(
            cfg, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version
        )
        expected_backend_target = phase11_canary_acceptance_review_service.Phase11CanaryAcceptanceEvidence.from_dict(
            live_report.get("evidence", {})
        ).canary_nat_target
    evidences = [phase11_canary_visibility_bundle_service.load_phase11_canary_visibility_evidence_json(path) for path in evidence_json]
    evidence = phase11_canary_visibility_bundle_service.merge_phase11_canary_visibility_evidence(
        evidences,
        customer_key=customer_key,
        lane=lane,
        port=port,
        expected_backend_target=expected_backend_target,
    ) if evidences else None
    report = phase11_canary_visibility_bundle_service.build_phase11_canary_visibility_bundle_report(
        cfg, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live, evidence=evidence
    )
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    for key in ("component", "final_decision", "blockers", "warnings", "missing_visibility_primitives", "missing_evidence_primitives", "next_required_step"):
        typer.echo(f"{key}: {report[key]}")


@production_app.command("canary-db-visibility-activate")
def production_canary_db_visibility_activate(
    customer_key: str = typer.Option("canary-btc-001", "--customer-key"),
    lane: str = typer.Option("btc", "--lane"),
    port: int = typer.Option(20001, "--port"),
    name: str = typer.Option("Phase 11 controlled canary DB visibility", "--name"),
    miners: int = typer.Option(1, "--miners"),
    farms: int = typer.Option(1, "--farms"),
    maxconn: int = typer.Option(1, "--maxconn"),
    rate_per_min: int = typer.Option(120, "--rate-per-min"),
    burst: int = typer.Option(240, "--burst"),
    requested_action: str = typer.Option("plan", "--requested-action"),
    expected_version: str = typer.Option("0.1.180", "--expected-version"),
    operator: str | None = typer.Option(None, "--operator"),
    reason: str | None = typer.Option(None, "--reason"),
    operator_confirmed: bool = typer.Option(False, "--operator-confirmed/--no-operator-confirmed"),
    understand_db_only_canary: bool = typer.Option(False, "--i-understand-db-only-canary"),
    understand_no_firewall_or_nat: bool = typer.Option(False, "--i-understand-no-firewall-or-nat"),
    reviewed_rollback: bool = typer.Option(False, "--i-have-reviewed-rollback"),
    fresh_farm5_sync_confirmed: bool = typer.Option(False, "--i-have-fresh-farm5-sync"),
    output: str = typer.Option("human", "--output"),
    config: Path | None = typer.Option(None, "--config", "-c"),
) -> None:
    req = production_domain.Phase11CanaryDbVisibilityActivationRequest(customer_key=customer_key,lane=lane,port=port,name=name,miners=miners,farms=farms,maxconn=maxconn,rate_per_min=rate_per_min,burst=burst,requested_action=requested_action,expected_version=expected_version,operator=operator,reason=reason,operator_confirmed=operator_confirmed,understand_db_only_canary=understand_db_only_canary,understand_no_firewall_or_nat=understand_no_firewall_or_nat,reviewed_rollback=reviewed_rollback,fresh_farm5_sync_confirmed=fresh_farm5_sync_confirmed)
    report = phase11_canary_db_visibility_activation_service.build_phase11_canary_db_visibility_activation_report(_load(config), req)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for k, v in report.items(): typer.echo(f"{k}: {v}")
@production_app.command("canary-execution-run-prep")
def production_canary_execution_run_preparation(
    lane: str = typer.Option("btc", "--lane"),
    customer_key: str | None = typer.Option("canary-btc-001", "--customer-key"),
    name: str | None = typer.Option("Phase 11 manual canary execution run", "--name"),
    port: int | None = typer.Option(20001, "--port"),
    miners: int = typer.Option(1, "--miners"),
    farms: int = typer.Option(1, "--farms"),
    maxconn: int = typer.Option(1, "--maxconn"),
    rate_per_min: int = typer.Option(120, "--rate-per-min"),
    burst: int = typer.Option(240, "--burst"),
    ips_mode: str = typer.Option("any", "--ips-mode"),
    ip_whitelist: list[str] = typer.Option([], "--ip"),
    operator: str | None = typer.Option(None, "--operator"),
    reason: str | None = typer.Option(None, "--reason"),
    requested_action: str = typer.Option("prepare", "--requested-action"),
    require_operator_confirmation: bool = typer.Option(True, "--require-operator-confirmation/--no-require-operator-confirmation"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
) -> None:
    request = production_domain.ManualCanaryExecutionRunPreparationRequest(
        customer_key=customer_key, lane=lane, port=port, name=name, miners=miners, farms=farms, maxconn=maxconn,
        rate_per_min=rate_per_min, burst=burst, ips_mode=ips_mode, ip_whitelist=ip_whitelist, operator=operator, reason=reason,
        requested_action=requested_action, require_operator_confirmation=require_operator_confirmation,
    )
    report = phase11_manual_canary_execution_run_preparation_service.build_phase11_manual_canary_execution_run_preparation_report(request)
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    typer.echo(f"component: {report['component']}")
    typer.echo(f"final_decision: {report['final_decision']}")
    typer.echo(f"authorization_status: {report['authorization_status']}")
    typer.echo(f"execution_allowed: {report['execution_allowed']}")
    typer.echo(f"mutation_performed: {report['mutation_performed']}")
    typer.echo(f"blockers: {report['blockers']}")
    typer.echo(f"validation_errors: {report['validation_errors']}")

@lanes_app.command("sync-config")
def lanes_sync_config(config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml."), yes: bool = typer.Option(False, "--yes", help="Apply DB writes (default is dry-run).")) -> None:
    """Sync config lanes into DB only. No firewall/NAT/runtime mutation."""
    result = lane_sync_service.sync_lane_config_db_only(_load(config), dry_run=not yes, yes=yes, command_hint="/usr/local/bin/mpf lanes sync-config --yes")
    if not result.ok:
        typer.echo(result.message)
        raise typer.Exit(1)
    typer.echo(f"firewall_change: {result.firewall_change}")
    typer.echo(f"nat_change: {result.nat_change}")
    typer.echo(f"runtime_change: {result.runtime_change}")
    typer.echo(f"would_create_lanes: {result.would_create_lanes}")
    typer.echo(f"would_update_lanes: {result.would_update_lanes}")
    typer.echo(f"stale_db_lanes: {result.stale_db_lanes}")
    typer.echo(f"created_lanes: {result.created_lanes or []}")
    typer.echo(f"updated_lanes: {result.updated_lanes or []}")
    typer.echo(f"stale_lanes: {result.stale_lanes or []}")


@phase8_app.command("runtime-worker-dry-run-harness")
def phase8_runtime_worker_dry_run_harness(
    config: Path | None = typer.Option(None, "--config", "-c"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
) -> None:
    report = phase8_runtime_worker_dry_run_harness_service.build_phase8_runtime_worker_dry_run_harness_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    keys=["component","final_decision","harness_status","authorization_status","execution_allowed","phase8_acceptance_allowed","latest_recorded_farm5_sync_evidence","no_farm5_0_1_116_sync_evidence_claimed","no_farm5_0_1_117_sync_evidence_claimed","runtime_worker_readiness_present","runtime_worker_readiness_fail_closed","worker_dry_run_harness_defined","worker_cycle_contract_defined","worker_item_contract_defined","worker_result_contract_defined","synthetic_worker_cycles_passed","explicit_skip_reporting_defined","no_work_reporting_defined","kill_switch_behavior_defined","lock_contention_behavior_defined","idempotency_duplicate_behavior_defined","batch_limit_behavior_defined","failure_mode_behavior_defined","runtime_worker_authorized","scheduler_authorized","abuse_runner_authorized","real_customer_evaluation_authorized","production_db_execution_authorized","db_reads_authorized","db_writes_authorized","firewall_apply_authorized","customer_nat_authorized","customer_firewall_rules_authorized","production_traffic_authorized","hard_block_authorized","soft_block_authorized","pause_automation_authorized","future_controlled_worker_pre_acceptance_pr_required","future_farm5_sync_required_before_runtime_acceptance","blockers","errors"]
    for k in keys:
        typer.echo(f"{k}: {report.get(k)}")



@phase8_app.command("controlled-worker-dry-run-gate")
def phase8_controlled_worker_dry_run_gate(
    config: Path = typer.Option(DEFAULT_CONFIG_PATH, "--config", exists=True, readable=True),
    output: str = typer.Option("human", "--output", help="human|json"),
) -> None:
    report = phase8_controlled_worker_dry_run_gate_service.build_phase8_controlled_worker_dry_run_gate_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    keys=["component","final_decision","gate_status","authorization_status","execution_allowed","phase8_acceptance_allowed","repository_version","latest_recorded_farm5_sync_evidence","farm5_0_1_118_batch_sync_evidence_present","farm5_0_1_119_sync_required_before_controlled_worker_dry_run","current_state_preserved","phase7_accepted","phase8_working","phase8_not_accepted","controlled_worker_dry_run_gate_doc_present","controlled_worker_dry_run_gate_prepared","operator_approval_required","kill_switch_required","lock_required","idempotency_required","explicit_skip_required","no_silent_skip_required","no_work_reporting_required","failure_mode_reporting_required","runtime_worker_authorized","worker_start_authorized","scheduler_authorized","timer_authorized","abuse_runner_authorized","real_customer_evaluation_authorized","production_db_execution_authorized","db_reads_authorized","db_writes_authorized","firewall_apply_authorized","iptables_restore_authorized","customer_nat_authorized","customer_firewall_rules_authorized","customer_policy_mutation_authorized","hard_block_authorized","soft_block_authorized","pause_automation_authorized","production_traffic_authorized","future_controlled_worker_dry_run_requires_operator","future_controlled_worker_dry_run_requires_0_1_119_sync","future_controlled_worker_dry_run_pr_required","future_phase8_final_acceptance_pr_required","blockers","errors"]
    _print_kv(report, keys)


@phase8_app.command("controlled-worker-dry-run")
def phase8_controlled_worker_dry_run(
    config: Path | None = typer.Option(None, "--config", "-c"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
    operator_confirmed: bool = typer.Option(False, "--operator-confirmed"),
    batch_limit: int = typer.Option(5, "--batch-limit"),
) -> None:
    report = phase8_controlled_worker_dry_run_service.build_phase8_controlled_worker_dry_run_report(_load(config), operator_confirmed=operator_confirmed, batch_limit=batch_limit)
    if output == "json": typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    keys=["component","final_decision","dry_run_status","authorization_status","execution_allowed","production_side_effects_allowed","phase8_acceptance_allowed","repository_version","latest_recorded_farm5_sync_evidence","farm5_0_1_120_sync_evidence_present","farm5_0_1_121_sync_required_before_farm5_dry_run_evidence","operator_confirmed","explicit_dry_run","batch_limit","synthetic_item_count","synthetic_scenarios_passed","all_items_have_no_side_effects","runtime_worker_authorized","worker_start_authorized","background_worker_authorized","scheduler_authorized","timer_authorized","abuse_runner_authorized","real_customer_evaluation_authorized","production_db_execution_authorized","db_reads_authorized","db_writes_authorized","firewall_apply_authorized","customer_policy_mutation_authorized","hard_block_authorized","soft_block_authorized","pause_automation_authorized","production_traffic_authorized","future_farm5_dry_run_evidence_requires_0_1_121_sync","future_phase8_final_acceptance_pr_required","blockers","errors"]
    for k in keys: typer.echo(f"{k}: {report[k]}")

@phase8_app.command("controlled-worker-pre-acceptance")
def phase8_controlled_worker_pre_acceptance(
    config: Path | None = typer.Option(None, "--config", "-c"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
) -> None:
    report = phase8_controlled_worker_pre_acceptance_service.build_phase8_controlled_worker_pre_acceptance_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
        return
    keys=["component","final_decision","pre_acceptance_status","authorization_status","execution_allowed","phase8_acceptance_allowed","latest_recorded_farm5_sync_evidence","repository_version","no_farm5_0_1_116_sync_evidence_claimed","no_farm5_0_1_117_sync_evidence_claimed","no_farm5_0_1_118_sync_evidence_claimed","farm5_sync_required_before_worker_dry_run","batch_sync_recommended_for_0_1_116_0_1_117_0_1_118","runtime_worker_dry_run_harness_present","runtime_worker_dry_run_harness_fail_closed","pre_acceptance_contract_defined","pre_acceptance_evaluator_defined","operator_approval_contract_defined","kill_switch_contract_required","lock_contract_required","no_silent_skip_contract_required","fresh_sync_contract_required","synthetic_pre_acceptance_scenarios_passed","controlled_worker_dry_run_allowed_now","runtime_worker_authorized","scheduler_authorized","timer_authorized","abuse_runner_authorized","real_customer_evaluation_authorized","production_db_execution_authorized","db_reads_authorized","db_writes_authorized","firewall_apply_authorized","customer_nat_authorized","customer_firewall_rules_authorized","production_traffic_authorized","hard_block_authorized","soft_block_authorized","pause_automation_authorized","future_farm5_batch_sync_required","future_controlled_worker_dry_run_pr_required","future_operator_acceptance_required","future_phase8_final_acceptance_pr_required","blockers","errors"]
    for k in keys:
        typer.echo(f"{k}: {report.get(k)}")




@phase8_app.command("final-acceptance")
def phase8_final_acceptance(
    config: Path | None = typer.Option(None, "--config", "-c"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
) -> None:
    report = phase8_final_acceptance_service.build_phase8_final_acceptance_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    keys=["component","final_decision","acceptance_status","authorization_status","execution_allowed","phase8_accepted","production_activation_allowed","repository_version","latest_recorded_farm5_sync_evidence","farm5_0_1_123_sync_evidence_present","farm5_final_acceptance_readiness_evidence_present","phase8_final_acceptance_evidence_doc_present","current_state_phase8_accepted","phase9_working","abuse_invariant_preserved","state_path_normal_over_tracking_over_grace_hard","sustained_abuse_window_3600_seconds","farms_over_alone_does_not_harden","worker_over_alone_does_not_harden","missing_evidence_does_not_harden","stale_evidence_does_not_harden","db_failure_does_not_harden","firewall_failure_does_not_harden","explicit_skip_required","no_silent_skip_required","all_active_customers_in_enabled_lanes_must_be_covered","dry_run_evidence_synthetic_only","dry_run_synthetic_item_count","dry_run_all_items_have_no_side_effects","runtime_worker_authorized","worker_start_authorized","background_worker_authorized","scheduler_authorized","timer_authorized","abuse_runner_authorized","production_db_execution_authorized","db_reads_authorized","db_writes_authorized","firewall_apply_authorized","customer_nat_authorized","customer_firewall_rules_authorized","hard_block_authorized","soft_block_authorized","pause_automation_authorized","production_traffic_authorized","next_phase","future_production_activation_gate_required","future_phase9_readiness_pr_required","blockers","warnings","errors"]
    for k in keys: typer.echo(f"{k}: {report.get(k)}")

@phase8_app.command("final-acceptance-readiness")
def phase8_final_acceptance_readiness(
    config: Path | None = typer.Option(None, "--config", "-c"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
) -> None:
    report = phase8_final_acceptance_readiness_service.build_phase8_final_acceptance_readiness_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False)); return
    keys=["component","final_decision","readiness_status","authorization_status","execution_allowed","phase8_acceptance_allowed","phase8_accepted_by_this_pr","repository_version","latest_recorded_farm5_sync_evidence","farm5_0_1_121_sync_evidence_present","farm5_controlled_worker_dry_run_evidence_present","current_state_preserved","phase7_accepted","phase8_working","phase8_not_accepted","abuse_invariant_preserved","state_path_normal_over_tracking_over_grace_hard","sustained_abuse_window_3600_seconds","farms_over_alone_does_not_harden","worker_over_alone_does_not_harden","missing_evidence_does_not_harden","stale_evidence_does_not_harden","db_failure_does_not_harden","firewall_failure_does_not_harden","explicit_skip_required","no_silent_skip_required","dry_run_evidence_synthetic_only","dry_run_synthetic_item_count","dry_run_all_items_have_no_side_effects","dry_run_execution_allowed","dry_run_production_side_effects_allowed","dry_run_phase8_acceptance_allowed","runtime_worker_authorized","worker_start_authorized","scheduler_authorized","timer_authorized","abuse_runner_authorized","production_db_execution_authorized","db_reads_authorized","db_writes_authorized","firewall_apply_authorized","customer_policy_mutation_authorized","hard_block_authorized","soft_block_authorized","pause_automation_authorized","production_traffic_authorized","future_phase8_final_acceptance_pr_required","future_sync_required_before_final_acceptance","blockers","warnings","errors"]
    for k in keys: typer.echo(f"{k}: {report.get(k)}")



@phase9_app.command("readiness")
def phase9_readiness(
    config: Path | None = typer.Option(None, "--config", "-c"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
) -> None:
    report = phase9_readiness_service.build_phase9_readiness_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, ensure_ascii=False, indent=2))
        return
    _emit_key_values(report, ["component","final_decision","readiness_status","authorization_status","execution_allowed","phase_gate_status","doctor_config_database_expectations","proxy_runtime_diagnostics_expectations","customer_diagnostics_readiness","abuse_status_visibility_readiness","usage_accounting_visibility_readiness","policy_reject_visibility_readiness","evidence_pack_readiness","troubleshooting_final_verdict_readiness","runtime_worker_authorized","abuse_runner_authorized","production_db_execution_authorized","db_writes_authorized","firewall_apply_authorized","iptables_restore_authorized","customer_nat_authorized","customer_firewall_rules_authorized","hard_block_authorized","soft_block_authorized","pause_automation_authorized","production_traffic_authorized","ui_authorized","telegram_authorized","blockers","warnings","errors"])

@phase9_app.command("final-verdict")
def phase9_final_verdict(
    config: Path | None = typer.Option(None, "--config", "-c"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
) -> None:
    report = phase9_final_verdict_diagnostics_service.build_phase9_final_verdict_diagnostics_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, ensure_ascii=False, indent=2))
        return
    _emit_key_values(report, ["component","final_decision","final_verdict_readiness","authorization_status","execution_allowed","phase_gate_status","latest_recorded_farm5_sync_evidence","phase8_final_acceptance_status","phase9_readiness_status","doctor_config_database_expectations","proxy_runtime_diagnostics_expectations","customer_diagnostics_readiness","abuse_status_visibility_readiness","usage_accounting_visibility_readiness","policy_reject_visibility_readiness","evidence_pack_readiness","troubleshooting_final_verdict_readiness","operator_final_verdict_readiness","all_dangerous_authorization_flags_false","runtime_worker_authorized","abuse_runner_authorized","production_db_execution_authorized","db_writes_authorized","firewall_apply_authorized","iptables_restore_authorized","customer_nat_authorized","customer_firewall_rules_authorized","hard_block_authorized","soft_block_authorized","pause_automation_authorized","production_traffic_authorized","ui_authorized","telegram_authorized","blockers","warnings","errors"])



@phase9_app.command("diagnostics")
def phase9_diagnostics(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase9_diagnostics_bundle_service.build_phase9_diagnostics_bundle_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, ensure_ascii=False, indent=2)); return
    _emit_key_values(report, ["component","final_decision","current_phase_gate","repository_version","latest_recorded_farm5_sync_evidence","next_required_operator_evidence","all_dangerous_authorization_flags_false","blockers","warnings","errors"])


@phase9_app.command("final-acceptance-readiness")
def phase9_final_acceptance_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase9_final_acceptance_readiness_service.build_phase9_final_acceptance_readiness_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, ensure_ascii=False, indent=2)); return
    _emit_key_values(report, ["component","final_decision","final_acceptance_readiness","authorization_status","report_only","inspection_only","execution_allowed","repository_version","current_phase_gate_status","latest_recorded_farm5_sync_evidence","next_required_operator_evidence","all_dangerous_authorization_flags_false","blockers","warnings","errors"])

@phase9_app.command("final-acceptance")
def phase9_final_acceptance(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase9_final_acceptance_service.build_phase9_final_acceptance_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, ensure_ascii=False, indent=2)); return
    _emit_key_values(report, ["component","final_decision","acceptance_status","authorization_status","report_only","inspection_only","execution_allowed","repository_version","current_phase_gate_status","latest_recorded_farm5_sync_evidence","farm5_0_1_127_sync_test_evidence_present","phase8_final_acceptance_status","phase9_readiness_status","phase9_final_verdict_diagnostics_status","phase9_diagnostics_bundle_status","phase9_final_acceptance_readiness_status","next_phase","post_merge_required_operator_evidence","all_dangerous_authorization_flags_false","blockers","warnings","errors"])

@phase9_app.command("customer-diagnostics")
def phase9_customer_diagnostics(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase9_customer_diagnostics_service.build_phase9_customer_diagnostics_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else str(report))

@phase9_app.command("abuse-visibility")
def phase9_abuse_visibility(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase9_abuse_visibility_service.build_phase9_abuse_visibility_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else str(report))

@phase9_app.command("usage-visibility")
def phase9_usage_visibility(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase9_usage_visibility_service.build_phase9_usage_visibility_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else str(report))

@phase9_app.command("policy-reject-visibility")
def phase9_policy_reject_visibility(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase9_policy_reject_visibility_service.build_phase9_policy_reject_visibility_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else str(report))

@phase9_app.command("proxy-runtime-diagnostics")
def phase9_proxy_runtime_diagnostics(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase9_proxy_runtime_diagnostics_service.build_phase9_proxy_runtime_diagnostics_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else str(report))

@phase9_app.command("evidence-pack")
def phase9_evidence_pack(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase9_evidence_pack_service.build_phase9_evidence_pack_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else str(report))

@phase9_app.command("troubleshooting-summary")
def phase9_troubleshooting_summary(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase9_troubleshooting_summary_service.build_phase9_troubleshooting_summary_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else str(report))
@phase8_app.command("farm5-dry-run-evidence-collection")
def phase8_farm5_dry_run_evidence_collection(
    config: Path | None = typer.Option(None, "--config", "-c"),
    output: Literal["human", "json"] = typer.Option("human", "--output"),
) -> None:
    report = phase8_farm5_dry_run_evidence_collection_service.build_phase8_farm5_dry_run_evidence_collection_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return
    keys = ["component","final_decision","evidence_collection_status","authorization_status","execution_allowed","phase8_acceptance_allowed","dry_run_evidence_claimed","repository_version","latest_recorded_farm5_sync_evidence","farm5_0_1_120_sync_evidence_present","farm5_0_1_121_sync_required_before_dry_run_evidence","current_state_preserved","phase7_accepted","phase8_working","phase8_not_accepted","dry_run_evidence_collection_runbook_present","runbook_status_not_executed","operator_invocation_required","default_command_requires_operator_confirmation","operator_confirmed_command_remains_no_side_effect","synthetic_only_required","no_silent_skip_required","no_work_reporting_required","failure_mode_reporting_required","idempotency_reporting_required","runtime_worker_authorized","worker_start_authorized","background_worker_authorized","scheduler_authorized","timer_authorized","abuse_runner_authorized","real_customer_evaluation_authorized","production_db_execution_authorized","db_reads_authorized","db_writes_authorized","firewall_apply_authorized","iptables_restore_authorized","customer_nat_authorized","customer_firewall_rules_authorized","customer_policy_mutation_authorized","hard_block_authorized","soft_block_authorized","pause_automation_authorized","production_traffic_authorized","future_farm5_dry_run_evidence_pr_required","future_phase8_final_acceptance_pr_required","blockers","errors"]
    for k in keys:
        typer.echo(f"{k}: {report.get(k)}")


@phase10_app.command("readiness")
def phase10_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_readiness_service.build_phase10_readiness_report(_load(config))
    if output == "json":
        typer.echo(json.dumps(report, ensure_ascii=False, indent=2)); return
    _emit_key_values(report,["component","final_decision","readiness_status","authorization_status","execution_allowed","latest_recorded_farm5_sync_evidence","farm5_0_1_128_sync_test_evidence_present","phase9_final_acceptance_status","next_required_operator_evidence","all_dangerous_authorization_flags_false","aggregate_dangerous_authorization_flag","blockers","warnings","errors"])

@phase10_app.command("session-readiness")
def phase10_session_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_session_readiness_service.build_session_readiness_report(_load(config))
    if output == "json": typer.echo(json.dumps(report, ensure_ascii=False, indent=2)); return
    _emit_key_values(report,["component","final_decision","authorization_status","execution_allowed","session_readiness","blockers","warnings","errors"])

@phase10_app.command("worker-policy-readiness")
def phase10_worker_policy_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_worker_policy_readiness_service.build_worker_policy_readiness_report(_load(config))
    if output == "json": typer.echo(json.dumps(report, ensure_ascii=False, indent=2)); return
    _emit_key_values(report,["component","final_decision","authorization_status","execution_allowed","worker_policy_readiness","blockers","warnings","errors"])


@phase10_app.command("session-model-readiness")
def phase10_session_model_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_session_model_readiness_service.build_session_model_readiness_report(_load(config))
    if output == "json": typer.echo(json.dumps(report, ensure_ascii=False, indent=2)); return
    typer.echo(str(report))


@phase10_app.command("worker-identity-readiness")
def phase10_worker_identity_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_worker_identity_readiness_service.build_worker_identity_readiness_report(_load(config))
    if output == "json": typer.echo(json.dumps(report, ensure_ascii=False, indent=2)); return
    typer.echo(str(report))


@phase10_app.command("worker-policy-contract-readiness")
def phase10_worker_policy_contract_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_worker_policy_contract_readiness_service.build_worker_policy_contract_readiness_report(_load(config))
    if output == "json": typer.echo(json.dumps(report, ensure_ascii=False, indent=2)); return
    typer.echo(str(report))


@phase10_app.command("implementation-readiness")
def phase10_implementation_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_implementation_readiness_service.build_phase10_implementation_readiness_report(_load(config))
    if output == "json": typer.echo(json.dumps(report, ensure_ascii=False, indent=2)); return
    typer.echo(str(report))

@phase10_app.command("share-timeline-readiness")
def phase10_share_timeline_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_share_timeline_readiness_service.build_share_timeline_readiness_report(_load(config))
    if output == "json": typer.echo(json.dumps(report, ensure_ascii=False, indent=2)); return
    _emit_key_values(report,["component","final_decision","authorization_status","execution_allowed","share_timeline_readiness","blockers","warnings","errors"])



@phase10_app.command("share-timeline-model-readiness")
def phase10_share_timeline_model_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_share_timeline_model_readiness_service.build_share_timeline_model_readiness_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else f"component: {report['component']}\nfinal_decision: {report['final_decision']}")


@phase10_app.command("collector-dry-run-gate-readiness")
def phase10_collector_dry_run_gate_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_collector_dry_run_gate_service.build_collector_dry_run_gate_readiness_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else f"component: {report['component']}\nfinal_decision: {report['final_decision']}")


@phase10_app.command("collector-dry-run-plan")
def phase10_collector_dry_run_plan(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_collector_dry_run_plan_service.build_collector_dry_run_plan_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else f"component: {report['component']}\nfinal_decision: {report['final_decision']}")


@phase10_app.command("runtime-worker-dry-run-readiness")
def phase10_runtime_worker_dry_run_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_runtime_worker_dry_run_readiness_service.build_runtime_worker_dry_run_readiness_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else f"component: {report['component']}\nfinal_decision: {report['final_decision']}")


@phase10_app.command("scheduler-dry-run-readiness")
def phase10_scheduler_dry_run_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_scheduler_dry_run_readiness_service.build_scheduler_dry_run_readiness_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else f"component: {report['component']}\nfinal_decision: {report['final_decision']}")


@phase10_app.command("worker-cycle-dry-run-plan")
def phase10_worker_cycle_dry_run_plan(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_worker_cycle_dry_run_plan_service.build_worker_cycle_dry_run_plan_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else f"component: {report['component']}\nfinal_decision: {report['final_decision']}")



@phase10_app.command("final-acceptance-readiness")
def phase10_final_acceptance_readiness(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_final_acceptance_readiness_service.build_phase10_final_acceptance_readiness_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else str(report))


@phase10_app.command("final-acceptance")
def phase10_final_acceptance(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_final_acceptance_service.build_phase10_final_acceptance_report(_load(config))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2) if output == "json" else str(report))

@phase10_app.command("enforcement-boundary")
def phase10_enforcement_boundary(config: Path | None = typer.Option(None, "--config", "-c"), output: Literal["human", "json"] = typer.Option("human", "--output")) -> None:
    report = phase10_enforcement_boundary_service.build_enforcement_boundary_report(_load(config))
    if output == "json": typer.echo(json.dumps(report, ensure_ascii=False, indent=2)); return
    _emit_key_values(report,["component","final_decision","authorization_status","execution_allowed","enforcement_boundary_readiness","blockers","warnings","errors"])
