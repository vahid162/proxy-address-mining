from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

DEFAULT_CONFIG_PATH = Path("/etc/mpf/mpf.yaml")
EXAMPLE_CONFIG_PATH = Path("configs/mpf.example.yaml")
CURRENT_PHASE_REQUIRES_PLAN_ONLY = True


class ServerConfig(BaseModel):
    name: str
    timezone: str = "Europe/Berlin"


class PathsConfig(BaseModel):
    app: Path = Path("/opt/mpf-py")
    data: Path = Path("/var/lib/mpf")
    logs: Path = Path("/var/log/mpf")
    backups: Path = Path("/var/backups/mpf")


class DatabaseConfig(BaseModel):
    url: str = "postgresql:///mpf"

    @field_validator("url")
    @classmethod
    def require_postgresql(cls, value: str) -> str:
        if not value.startswith(("postgresql://", "postgresql+psycopg://", "postgresql:///")):
            raise ValueError("database.url must be PostgreSQL; SQLite/flat-file production state is forbidden")
        return value


class FirewallConfig(BaseModel):
    backend: Literal["iptables"] = "iptables"
    apply_mode: Literal["plan_only", "manual_apply", "atomic_apply"] = "plan_only"
    lock_path: Path = Path("/run/mpf-firewall.lock")


class ProxyConfig(BaseModel):
    compose_file: Path = Path("/opt/mpf-py-src/compose/mpf-proxy.compose.yaml")
    project_name: str = "mpf-proxy"
    runtime_activation_allowed: bool = False


class V2RayAConfig(BaseModel):
    ui_bind_host: str = "127.0.0.1"
    ui_port: int = Field(default=2014, gt=0, le=65535)


class UpstreamConfig(BaseModel):
    host: str
    port: int = Field(gt=0, le=65535)


class ForwarderConfig(BaseModel):
    service_name: str
    bind_host: str = "127.0.0.1"
    listen_port: int | None = Field(default=None, gt=0, le=65535)
    upstream_socks: str | None = None


class LaneConfig(BaseModel):
    enabled: bool = False
    backend_port: int = Field(gt=0, le=65535)
    chain_prefix: str
    upstreams: list[UpstreamConfig] = Field(default_factory=list)
    forwarder: ForwarderConfig | None = None


class AbuseConfig(BaseModel):
    enabled: bool = True
    threshold_sec: int = Field(default=3600, ge=3600)
    grace_sec: int = Field(default=900, ge=60)


class MPFConfig(BaseModel):
    server: ServerConfig
    paths: PathsConfig = Field(default_factory=PathsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    firewall: FirewallConfig = Field(default_factory=FirewallConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    v2raya: V2RayAConfig = Field(default_factory=V2RayAConfig)
    lanes: dict[str, LaneConfig]
    abuse: AbuseConfig = Field(default_factory=AbuseConfig)

    @model_validator(mode="after")
    def validate_current_phase_safety(self) -> "MPFConfig":
        if "btc" not in self.lanes:
            raise ValueError("btc lane is required")
        if self.lanes["btc"].backend_port != 60010:
            raise ValueError("btc backend_port must be 60010 during the initial architecture")

        enabled_backend_ports: dict[int, str] = {}
        for lane_name, lane in self.lanes.items():
            if lane.forwarder and lane.forwarder.listen_port not in {None, lane.backend_port}:
                raise ValueError(
                    f"lane {lane_name!r} forwarder.listen_port must match backend_port {lane.backend_port}"
                )
            if not lane.enabled:
                continue
            owner = enabled_backend_ports.get(lane.backend_port)
            if owner:
                raise ValueError(f"enabled lanes {owner!r} and {lane_name!r} share backend_port {lane.backend_port}")
            enabled_backend_ports[lane.backend_port] = lane_name

        if CURRENT_PHASE_REQUIRES_PLAN_ONLY and self.firewall.apply_mode != "plan_only":
            raise ValueError("current phase safety gate requires firewall.apply_mode=plan_only")

        if self.proxy.runtime_activation_allowed:
            raise ValueError("current phase safety gate requires proxy.runtime_activation_allowed=false")

        return self


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"config file not found: {path}") from exc

    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError(f"config file must contain a YAML object: {path}")
    return data


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> MPFConfig:
    return MPFConfig.model_validate(load_yaml(path))


def validate_config(path: Path = DEFAULT_CONFIG_PATH) -> tuple[bool, str]:
    try:
        load_config(path)
    except (FileNotFoundError, ValueError, ValidationError) as exc:
        return False, str(exc)
    return True, "OK"
