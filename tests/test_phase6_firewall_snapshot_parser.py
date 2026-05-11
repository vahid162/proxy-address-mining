from mpf.services.firewall_snapshot_parser import parse_iptables_save_text


def _rules_by_key(text: str):
    snap = parse_iptables_save_text(text)
    return snap, {r.rule_key: r for r in snap.rules}


def test_parses_mpf_chains_from_filter_and_nat_and_ignores_non_mpf() -> None:
    text = """
*filter
:INPUT ACCEPT [0:0]
:MPF_INPUT - [0:0]
:NOT_MPF - [0:0]
COMMIT
*nat
:PREROUTING ACCEPT [0:0]
:MPF_NAT_PRE - [0:0]
COMMIT
"""
    snap = parse_iptables_save_text(text)
    assert ("filter", "MPF_INPUT") in snap.chains
    assert ("nat", "MPF_NAT_PRE") in snap.chains
    assert all(chain.startswith("MPF") for _, chain in snap.chains)


def test_parses_double_and_single_quoted_comment_rule_keys() -> None:
    text = """
*filter
:MPF_INPUT - [0:0]
-A MPF_INPUT -m comment --comment "mpf:c1:double" -j ACCEPT
-A MPF_INPUT -m comment --comment 'mpf:c2:single' -j ACCEPT
COMMIT
"""
    _, rules = _rules_by_key(text)
    assert "mpf:c1:double" in rules
    assert "mpf:c2:single" in rules


def test_parses_table_chain_protocol_ports_and_source_variants() -> None:
    text = """
*filter
:MPF_GUARD - [0:0]
-A MPF_GUARD -p tcp -s 10.0.0.1/32 --dport 60010 -m comment --comment "mpf:k1" -j REJECT
-A MPF_GUARD -p udp --source 10.0.0.2/32 --destination-port 60011 -m comment --comment "mpf:k2" -j REJECT
COMMIT
"""
    _, rules = _rules_by_key(text)
    r1 = rules["mpf:k1"]
    assert r1.table == "filter"
    assert r1.chain == "MPF_GUARD"
    assert r1.match_json["protocol"] == "tcp"
    assert r1.match_json["port"] == 60010
    assert r1.match_json["source"] == "10.0.0.1/32"

    r2 = rules["mpf:k2"]
    assert r2.match_json["protocol"] == "udp"
    assert r2.match_json["port"] == 60011
    assert r2.match_json["source"] == "10.0.0.2/32"


def test_parses_nat_target_backend_variants_and_unknown_string() -> None:
    text = """
*nat
:MPF_NAT_PRE - [0:0]
-A MPF_NAT_PRE -m comment --comment "mpf:r" -j REDIRECT --to-ports 60010
-A MPF_NAT_PRE -m comment --comment "mpf:d1" -j DNAT --to-destination 127.0.0.1:60011
-A MPF_NAT_PRE -m comment --comment "mpf:d2" -j DNAT --to-destination 60012
-A MPF_NAT_PRE -m comment --comment "mpf:d3" -j DNAT --to-destination backend-service
COMMIT
"""
    _, rules = _rules_by_key(text)
    assert rules["mpf:r"].action_json["target_backend"] == 60010
    assert rules["mpf:d1"].action_json["target_backend"] == 60011
    assert rules["mpf:d2"].action_json["target_backend"] == 60012
    assert rules["mpf:d3"].action_json["target_backend"] == "backend-service"


def test_creates_deterministic_synthetic_key_when_comment_absent() -> None:
    line = "-A MPF_INPUT -p tcp --dport 20001 -j ACCEPT"
    text = f"*filter\n:MPF_INPUT - [0:0]\n{line}\nCOMMIT\n"
    snap1 = parse_iptables_save_text(text)
    snap2 = parse_iptables_save_text(text)
    assert len(snap1.rules) == 1
    assert snap1.rules[0].rule_key == snap2.rules[0].rule_key
    assert snap1.rules[0].rule_key.startswith("mpf:auto:filter:MPF_INPUT:0:")


def test_handles_unrelated_and_malformed_lines_without_crashing() -> None:
    text = """
random text
*filter
:MPF_INPUT - [0:0]
-A MPF_INPUT -m comment --comment "mpf:ok" -j ACCEPT
-A MPF_INPUT -m comment --comment "broken
-A MPF_INPUT --comment
COMMIT
"""
    snap = parse_iptables_save_text(text)
    keys = {r.rule_key for r in snap.rules}
    assert "mpf:ok" in keys


def test_returns_empty_snapshot_for_empty_or_non_mpf_content() -> None:
    empty = parse_iptables_save_text("")
    assert empty.chains == []
    assert empty.rules == []

    non_mpf = parse_iptables_save_text("*filter\n:INPUT ACCEPT [0:0]\n-A INPUT -j ACCEPT\nCOMMIT\n")
    assert non_mpf.chains == []
    assert non_mpf.rules == []
