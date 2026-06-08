from __future__ import annotations

import pytest

from mpf import __version__
from mpf.domain.phase11_controlled_filter_packet_path import EXPECTED_VERSION
from mpf.services.phase11_controlled_filter_packet_path_bundle_service import _cross_check_manifest
from mpf.services.phase11_controlled_filter_packet_path_decision_service import (
    _rule_applies,
    _unsupported_match_blocker,
    _walk_chain,
)


_PACKET = {
    "protocol": "tcp",
    "destination": "172.30.0.5",
    "destination_port": 60010,
    "out_interface": "br-abcdef123456",
    "ingress_interface_known": False,
}


def _rule(*argv: str, target: str = "DOCKER-USER", index: int = 0) -> dict[str, object]:
    return {
        "table": "filter",
        "chain": "FORWARD",
        "rule_index": index,
        "argv": ["-A", "FORWARD", *argv],
        "jump_target": target,
        "jump_kind": "jump",
        "rule_hash": "0" * 64,
        "match": {},
    }


def test_known_match_grammar_remains_supported() -> None:
    rule = _rule("-p", "tcp", "-m", "tcp", "-d", "172.30.0.5/32", "--dport", "60010", "-j", "DOCKER-USER")
    rule["match"] = {
        "protocol": "tcp",
        "destination": "172.30.0.5/32",
        "destination_port": 60010,
    }
    assert _unsupported_match_blocker(rule) is False
    assert _rule_applies(rule, _PACKET, target_is_hook=True) is True


@pytest.mark.parametrize(
    ("argv", "match"),
    [
        (("-p", "all", "-j", "DOCKER-USER"), {"protocol": "all"}),
        (("-p", "6", "-j", "DOCKER-USER"), {"protocol": "6"}),
        (("-o", "br-+", "-j", "DOCKER-USER"), {"out_interface": "br-+"}),
        (("-p", "tcp", "-m", "tcp", "--dport", "60000:60020", "-j", "DOCKER-USER"), {"protocol": "tcp", "destination_port": "60000:60020"}),
    ],
)
def test_supported_protocol_interface_and_port_forms_apply(argv: tuple[str, ...], match: dict[str, object]) -> None:
    rule = _rule(*argv)
    rule["match"] = match
    assert _unsupported_match_blocker(rule) is False
    assert _rule_applies(rule, _PACKET, target_is_hook=True) is True


@pytest.mark.parametrize(
    "unknown_tokens",
    [
        ("-p", "tcp", "-m", "tcp", "--sport", "12345", "-j", "DOCKER-USER"),
        ("-p", "tcp", "-m", "tcp", "--tcp-option", "2", "-j", "DOCKER-USER"),
        ("-p", "tcp", "-m", "tcp", "--syn", "-j", "DOCKER-USER"),
        ("-f", "-j", "DOCKER-USER"),
        ("--protocol", "tcp", "-j", "DOCKER-USER"),
    ],
)
def test_unmodelled_match_tokens_fail_closed(unknown_tokens: tuple[str, ...]) -> None:
    rule = _rule(*unknown_tokens)
    assert _unsupported_match_blocker(rule) is True
    assert _rule_applies(rule, _PACKET, target_is_hook=True) == "unresolved"


def test_unknown_target_semantics_fail_closed() -> None:
    rule = _rule("-j", "NFQUEUE", target="NFQUEUE")
    flow = _walk_chain(
        "FORWARD",
        0,
        {"FORWARD": [rule]},
        {"FORWARD": "DROP"},
        set(),
        _PACKET,
        hook_seen=False,
        call_stack=[],
        steps=0,
    )
    assert flow.accepts == []
    assert flow.hook_seen_any is False
    assert flow.unresolved == ["unsupported_target_semantics:FORWARD:0:NFQUEUE"]


def test_manifest_cross_check_rejects_non_object_nested_backend_target() -> None:
    blockers: list[str] = []
    decision = {"final_decision": "BLOCKED_CONTROLLED_FILTER_PACKET_PATH_PROOF"}
    evidence = {
        "repository_version": __version__,
        "expected_version": EXPECTED_VERSION,
        "collection_id": "collection-1",
        "hostname": "host-1",
        "collected_at": "2026-06-08T00:00:00Z",
        "phase_status_sha256": "0" * 64,
        "backend_target": [],
    }
    parsed = {"ipv4": {"source_sha256": "a" * 64}, "ipv6": {"source_sha256": "b" * 64}}
    manifest = {
        "repository_version": __version__,
        "expected_version": EXPECTED_VERSION,
        "collection_id": "collection-1",
        "hostname": "host-1",
        "collection_timestamp": "2026-06-08T00:00:00Z",
        "backend_target_fingerprint": None,
        "phase_state_hash": "0" * 64,
        "final_decision": decision["final_decision"],
        "decision_hash": "",
        "graph_hash": "",
        "ipv4_ruleset_hash": "a" * 64,
        "ipv6_ruleset_hash": "b" * 64,
    }
    raw = {
        "decision.json": b"",
        "packet-path-graph.json": b"",
        "iptables-save.txt": b"",
        "ip6tables-save.txt": b"",
    }
    docs = {
        "decision.json": decision,
        "packet-path-graph.json": {},
        "parsed-firewall.json": parsed,
        "sanitized-backend-target.json": {},
        "sanitized-docker-network.json": {},
        "host-network-topology.json": {},
    }

    _cross_check_manifest(manifest, evidence, decision, {}, parsed, docs, raw, blockers)

    assert "evidence_backend_target_schema_invalid" in blockers
