from __future__ import annotations

from typer.testing import CliRunner

from mpf.interfaces.cli import app

RUNNER = CliRunner()


def assert_command_forbidden(args: list[str]) -> None:
    result = RUNNER.invoke(app, args)
    assert result.exit_code != 0


def test_customer_mutation_commands_are_not_available_in_phase3() -> None:
    forbidden = [
        ["customer", "add", "btc", "alice", "23138"],
        ["customer", "edit", "alice"],
        ["customer", "delete", "alice"],
        ["customer", "renew", "alice", "--days", "30"],
        ["customer", "set-ips", "alice", "1.2.3.4"],
    ]
    for args in forbidden:
        assert_command_forbidden(args)


def test_firewall_commands_are_not_available_in_phase3() -> None:
    forbidden = [
        ["firewall", "apply", "--yes"],
        ["firewall", "rollback", "1", "--yes"],
    ]
    for args in forbidden:
        assert_command_forbidden(args)


def test_abuse_and_job_run_commands_are_not_available_in_phase3() -> None:
    forbidden = [
        ["abuse", "run"],
        ["abuse", "hard", "alice", "--yes"],
        ["abuse", "unhard", "alice", "--yes"],
        ["jobs", "run", "abuse"],
        ["jobs", "run", "usage-snapshot"],
    ]
    for args in forbidden:
        assert_command_forbidden(args)


def test_no_public_ui_or_telegram_commands_exist_in_phase3() -> None:
    forbidden = [
        ["ui", "serve"],
        ["telegram", "start"],
        ["telegram", "run"],
    ]
    for args in forbidden:
        assert_command_forbidden(args)
