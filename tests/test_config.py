from __future__ import annotations

from pathlib import Path

import pytest

from mpf.config import load_config, validate_config


EXAMPLE_CONFIG = Path("configs/mpf.example.yaml")


def test_example_config_is_valid() -> None:
    ok, message = validate_config(EXAMPLE_CONFIG)
    assert ok, message


def test_example_config_keeps_phase1_plan_only() -> None:
    cfg = load_config(EXAMPLE_CONFIG)
    assert cfg.firewall.apply_mode == "plan_only"


def test_btc_lane_backend_port_is_frozen() -> None:
    cfg = load_config(EXAMPLE_CONFIG)
    assert cfg.lanes["btc"].enabled is True
    assert cfg.lanes["btc"].backend_port == 60010


def test_rejects_non_postgresql_database(tmp_path: Path) -> None:
    config_path = tmp_path / "mpf.yaml"
    config_path.write_text(
        """
server:
  name: test
lanes:
  btc:
    enabled: true
    backend_port: 60010
    chain_prefix: MPFBTC
    upstreams: []
database:
  url: sqlite:///tmp/mpf.sqlite
firewall:
  apply_mode: plan_only
""".strip(),
        encoding="utf-8",
    )

    ok, message = validate_config(config_path)
    assert not ok
    assert "PostgreSQL" in message


def test_rejects_non_plan_only_during_phase1(tmp_path: Path) -> None:
    config_path = tmp_path / "mpf.yaml"
    config_path.write_text(
        """
server:
  name: test
lanes:
  btc:
    enabled: true
    backend_port: 60010
    chain_prefix: MPFBTC
    upstreams: []
firewall:
  apply_mode: atomic_apply
""".strip(),
        encoding="utf-8",
    )

    ok, message = validate_config(config_path)
    assert not ok
    assert "plan_only" in message
