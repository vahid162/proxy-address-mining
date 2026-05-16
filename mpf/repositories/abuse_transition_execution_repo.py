from __future__ import annotations

from typing import Protocol, Any


class AbuseTransitionExecutionRepo(Protocol):
    def has_idempotency_key(self, idempotency_key: str) -> bool: ...
    def write_abuse_state_transition(self, payload: dict[str, Any]) -> dict[str, Any]: ...
    def write_abuse_event(self, payload: dict[str, Any]) -> dict[str, Any]: ...


class InMemoryAbuseTransitionExecutionRepo:
    def __init__(self) -> None:
        self.abuse_states: list[dict[str, Any]] = []
        self.abuse_events: list[dict[str, Any]] = []
        self._keys: set[str] = set()

    def has_idempotency_key(self, idempotency_key: str) -> bool:
        return idempotency_key in self._keys

    def write_abuse_state_transition(self, payload: dict[str, Any]) -> dict[str, Any]:
        key = str(payload.get("idempotency_key", ""))
        if key:
            self._keys.add(key)
        rec = dict(payload)
        rec["storage"] = "in_memory_fake_repo"
        self.abuse_states.append(rec)
        return rec

    def write_abuse_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        rec = dict(payload)
        rec["storage"] = "in_memory_fake_repo"
        self.abuse_events.append(rec)
        return rec
