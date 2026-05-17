from __future__ import annotations

from pathlib import Path

DANGEROUS_AUTHORIZATION_FLAGS = [
    "execution_allowed",
    "production_activation_allowed",
    "runtime_worker_authorized",
    "worker_start_authorized",
    "scheduler_authorized",
    "timer_authorized",
    "abuse_runner_authorized",
    "real_customer_evaluation_authorized",
    "production_db_execution_authorized",
    "db_writes_authorized",
    "firewall_apply_authorized",
    "iptables_restore_authorized",
    "customer_nat_authorized",
    "customer_firewall_rules_authorized",
    "hard_block_authorized",
    "soft_block_authorized",
    "pause_automation_authorized",
    "production_traffic_authorized",
    "ui_authorized",
    "telegram_authorized",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def false_flags() -> dict[str, bool]:
    return {key: False for key in DANGEROUS_AUTHORIZATION_FLAGS}


def all_flags_false(report: dict[str, object]) -> bool:
    return all(report.get(key) is False for key in DANGEROUS_AUTHORIZATION_FLAGS)
