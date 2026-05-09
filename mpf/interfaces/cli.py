from __future__ import annotations

from pathlib import Path

import typer

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, load_config
from mpf.domain.health import HealthReport
from mpf.services import (
    config_service,
    customer_read_service,
    db_service,
    doctor_service,
    job_service,
    lane_service,
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
lanes_app = typer.Typer(help="Lane read-only commands.")
customer_app = typer.Typer(help="Customer read-only commands.")
jobs_app = typer.Typer(help="Job read-only commands.")
proxy_app = typer.Typer(help="Proxy read-only planning and doctor commands.")
app.add_typer(config_app, name="config")
app.add_typer(db_app, name="db")
app.add_typer(lanes_app, name="lanes")
app.add_typer(customer_app, name="customer")
app.add_typer(jobs_app, name="jobs")
app.add_typer(proxy_app, name="proxy")


def _config_path(config: Path | None) -> Path:
    return config or DEFAULT_CONFIG_PATH


def _load(config: Path | None):
    return load_config(_config_path(config))


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
def customer_list(config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml."), limit: int = typer.Option(100, "--limit", min=1, max=1000, help="Maximum rows to show.")) -> None:
    """List customers read-only. Customer mutation belongs to Phase 5."""
    result = customer_read_service.list_customer_status(_load(config), limit=limit)
    if not result.ok:
        typer.echo(result.message)
        raise typer.Exit(1)
    if not result.customers:
        typer.echo("no customers")
        return
    for customer in result.customers:
        typer.echo(f"{customer.id}\t{customer.lane}\t{customer.name}\tport={customer.port}\tstatus={customer.status}\texpires_at={customer.expires_at}")


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


@app.command("phase-status")
def phase_status() -> None:
    """Print the current repository phase guard."""
    typer.echo("current_accepted_phase: Phase 4 Runtime Activation — Limited Proxy Runtime Startup accepted on farm5")
    typer.echo("current_working_phase: Phase 5 — Customer CRUD in DB Only")
    typer.echo("server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active")
    typer.echo("production_traffic: none")
    typer.echo("firewall_apply_allowed: no")
    typer.echo("abuse_automation_allowed: no")
    typer.echo("customer_onboarding_allowed: db_only_after_phase5_gate")
    typer.echo("proxy_data_plane_allowed: limited_runtime_local_only")
    typer.echo("ui_allowed: no")
    typer.echo("telegram_allowed: no")
    typer.echo("compatibility_previous_current_accepted_phase: Phase 4.2 — Runtime Activation Runbook Planning, synced and verified on farm5")
    typer.echo("compatibility_previous_current_working_phase: Phase 4 Runtime Activation Execution Review")
    typer.echo("compatibility_previous_proxy_data_plane_allowed: planning_only")
