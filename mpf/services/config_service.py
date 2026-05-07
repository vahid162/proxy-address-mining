from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mpf.config import MPFConfig, load_config, validate_config


@dataclass(frozen=True)
class ConfigSummary:
    path: Path
    config: MPFConfig


def validate(path: Path) -> tuple[bool, str]:
    return validate_config(path)


def show(path: Path) -> ConfigSummary:
    return ConfigSummary(path=path, config=load_config(path))
