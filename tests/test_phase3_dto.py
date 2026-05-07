from __future__ import annotations

from dataclasses import dataclass

from mpf.domain.dto import ReadOnlyResponse


@dataclass(frozen=True)
class SampleRecord:
    name: str
    port: int


def test_read_only_response_has_stable_top_level_shape() -> None:
    response = ReadOnlyResponse(
        ok=True,
        message="OK",
        correlation_id="corr-1",
        data={"items": [SampleRecord("btc", 60010)]},
    ).to_dict()
    assert set(response) == {"ok", "message", "correlation_id", "data"}
    assert response["ok"] is True
    assert response["message"] == "OK"
    assert response["correlation_id"] == "corr-1"
    assert response["data"]["items"][0] == {"name": "btc", "port": 60010}
