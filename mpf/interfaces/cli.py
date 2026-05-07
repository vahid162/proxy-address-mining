from __future__ import annotations

from pathlib import Path

import typer

from mpf import __version__
from mpf.config import DEFAULT_CONFIG_PATH, load_config, validate_config
from mpf.db import ping_database

app = typer.Typer(
    name="mpf",
    help="MPF safe CLI skeleton. Safe smoke commands only; phase-gated; no production traffic mutation.",
    no_args_is_help=True,
    invoke_without_command=True,
)
config_app = typer.Typer(help="Configuration smoke commands.")
db_app = typer.Typer(help="Database smoke commands.")
app.add_typer(config_app, name="config")
app.add_typer(db_app, name="db")


def _config_path(config: Path | None) -> Path:
    return config or DEFAULT_CONFIG_PATH


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version and exit.",
        is_eager=True,
    ),
) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit()


@app.command()
def doctor(
    config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml."),
) -> None:
    """Run read-only diagnostics without mutating production traffic."""
    path = _config_path(config)
    ok, message = validate_config(path)
    typer.echo("MPF doctor")
    typer.echo(f"config_path: {path}")
    typer.echo(f"config: {'OK' if ok else 'ERROR'}")
    if not ok:
        typer.echo(f"config_error: {message}")
        raise typer.Exit(1)

    cfg = load_config(path)
    typer.echo(f"apply_mode: {cfg.firewall.apply_mode}")
    typer.echo("traffic_changes: none")
    typer.echo("firewall_mutation: disabled")
    typer.echo("abuse_automation: disabled")


@config_app.command("validate")
def config_validate(
    config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml."),
) -> None:
    """Validate config without mutating anything."""
    path = _config_path(config)
    ok, message = validate_config(path)
    if ok:
        typer.echo("OK")
        return
    typer.echo(message)
    raise typer.Exit(1)


@config_app.command("show")
def config_show(
    config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml."),
) -> None:
    """Show normalized safe config summary."""
    path = _config_path(config)
    cfg = load_config(path)
    typer.echo(f"server.name: {cfg.server.name}")
    typer.echo(f"server.timezone: {cfg.server.timezone}")
    typer.echo(f"database.url: {cfg.database.url}")
    typer.echo(f"firewall.backend: {cfg.firewall.backend}")
    typer.echo(f"firewall.apply_mode: {cfg.firewall.apply_mode}")
    for lane_name, lane in sorted(cfg.lanes.items()):
        typer.echo(
            f"lane.{lane_name}: enabled={lane.enabled} backend_port={lane.backend_port} chain_prefix={lane.chain_prefix}"
        )
    typer.echo(f"abuse.enabled: {cfg.abuse.enabled}")
    typer.echo(f"abuse.threshold_sec: {cfg.abuse.threshold_sec}")
    typer.echo(f"abuse.grace_sec: {cfg.abuse.grace_sec}")


@db_app.command("ping")
def db_ping(
    config: Path | None = typer.Option(None, "--config", "-c", help="Path to mpf.yaml."),
) -> None:
    """Ping PostgreSQL without creating schema or mutating state."""
    cfg = load_config(_config_path(config))
    result = ping_database(cfg)
    if result.ok:
        typer.echo("OK")
        return
    typer.echo(result.message)
    raise typer.Exit(1)


@app.command("phase-status")
def phase_status() -> None:
    """Print the current repository phase guard."""
    typer.echo("current_accepted_phase: Phase 1 — Preflight + Bootstrap Without Traffic Changes")
    typer.echo("current_working_phase: Phase 2 — PostgreSQL + Config + Domain Model")
    typer.echo("server_state: farm5 phase 1 bootstrapped and verified")
    typer.echo("production_traffic: none")
    typer.echo("firewall_apply_allowed: no")
    typer.echo("abuse_automation_allowed: no")
    typer.echo("customer_onboarding_allowed: no")
    typer.echo("ui_allowed: no")
    typer.echo("telegram_allowed: no")
