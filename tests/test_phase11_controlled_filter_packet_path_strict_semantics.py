from __future__ import annotations

import pytest

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
