from __future__ import annotations

from dataclasses import dataclass

from mpf.config import MPFConfig
from mpf.repositories.lane_repo import LaneRecord, list_lanes


@dataclass(frozen=True)
class LaneList:
    ok: bool
    message: str
    lanes: list[LaneRecord]


def list_lane_status(config: MPFConfig) -> LaneList:
    ok, records, message = list_lanes(config)
    return LaneList(ok=ok, message=message, lanes=records)
