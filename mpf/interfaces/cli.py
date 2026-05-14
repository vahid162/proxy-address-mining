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
from mpf.services import (
    firewall_apply_gate_readiness_service,
    firewall_live_snapshot_scaffold_service,
    firewall_live_snapshot_read_service,
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
app.add_typer(config_app, name="config")
app.add_typer(db_app, name="db")
app.add_typer(lanes_app, name="lanes")
app.add_typer(customer_app, name="customer")
app.add_typer(jobs_app, name="jobs")
app.add_typer(proxy_app, name="proxy")
app.add_typer(firewall_app, name="firewall")
app.add_typer(events_app, name="events")


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
    report = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg)
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
    apply_gate_readiness = firewall_apply_gate_readiness_service.build_apply_gate_readiness_report(cfg)
    live_snapshot_scaffold = firewall_live_snapshot_scaffold_service.build_live_snapshot_scaffold_report(cfg)
    live_snapshot_read = firewall_live_snapshot_read_service.build_live_snapshot_read_report(cfg)
    restore_lock_record_gate = firewall_restore_lock_record_gate_service.build_restore_lock_record_gate_report(cfg)
    restore_lock_record_readiness = firewall_restore_lock_record_readiness_service.build_restore_lock_record_readiness_report(cfg)
    restore_lock_record_acceptance_gate = firewall_restore_lock_record_acceptance_gate_service.build_restore_lock_record_acceptance_gate_report(cfg)
    restore_lock_record_execution_gate = firewall_restore_lock_record_execution_gate_service.build_restore_lock_record_execution_gate_report(cfg)
    report = firewall_gate_review_service.build_gate_review_report(
        evidence=evidence,
        apply_gate_readiness=apply_gate_readiness,
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
    typer.echo(f"canary_readiness: {report.canary_readiness_summary['status']}")
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
