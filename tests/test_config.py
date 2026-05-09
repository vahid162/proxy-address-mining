from __future__ import annotations

from pathlib import Path

from mpf.config import load_config, validate_config


EXAMPLE_CONFIG = Path("configs/mpf.example.yaml")


def test_example_config_is_valid() -> None:
    ok, message = validate_config(EXAMPLE_CONFIG)
    assert ok, message


def test_example_config_keeps_current_phase_plan_only() -> None:
    cfg = load_config(EXAMPLE_CONFIG)
    assert cfg.firewall.apply_mode == "plan_only"


def test_example_config_has_phase4_proxy_planning_contract() -> None:
    cfg = load_config(EXAMPLE_CONFIG)
    assert cfg.proxy.project_name == "mpf-proxy"
    assert str(cfg.proxy.compose_file).endswith("mpf-proxy.compose.yaml")
    assert cfg.proxy.runtime_activation_allowed is False
    assert cfg.v2raya.ui_bind_host == "127.0.0.1"
    assert cfg.v2raya.ui_port == 2015


def test_btc_lane_backend_port_is_frozen() -> None:
    cfg = load_config(EXAMPLE_CONFIG)
    assert cfg.lanes["btc"].enabled is True
    assert cfg.lanes["btc"].backend_port == 60010
    assert cfg.lanes["btc"].forwarder is not None
    assert cfg.lanes["btc"].forwarder.service_name == "mpf-forwarder-btc"
    assert cfg.lanes["btc"].forwarder.listen_port == 60010


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


def test_rejects_non_plan_only_during_current_phase(tmp_path: Path) -> None:
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
    assert "current phase safety gate" in message
    assert "plan_only" in message


def test_rejects_proxy_runtime_activation_during_current_phase(tmp_path: Path) -> None:
    config_path = tmp_path / "mpf.yaml"
    config_path.write_text(
        """
server:
  name: test
firewall:
  apply_mode: plan_only
proxy:
  runtime_activation_allowed: true
lanes:
  btc:
    enabled: true
    backend_port: 60010
    chain_prefix: MPFBTC
    upstreams: []
""".strip(),
        encoding="utf-8",
    )

    ok, message = validate_config(config_path)
    assert not ok
    assert "runtime_activation_allowed=false" in message


def test_rejects_forwarder_listen_port_mismatch(tmp_path: Path) -> None:
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
    forwarder:
      service_name: mpf-forwarder-btc
      bind_host: 127.0.0.1
      listen_port: 60011
    upstreams: []
firewall:
  apply_mode: plan_only
""".strip(),
        encoding="utf-8",
    )

    ok, message = validate_config(config_path)
    assert not ok
    assert "forwarder.listen_port must match backend_port" in message
