from mpf.services.firewall_snapshot_parser import parse_iptables_save_text


def test_parse_iptables_save_text_extracts_mpf_chains_rules_and_nat_target() -> None:
    text = """
*filter
:INPUT ACCEPT [0:0]
:MPF_INPUT - [0:0]
-A MPF_INPUT -p tcp --dport 20001 -m comment --comment "mpf:c1:customer_dispatch" -j ACCEPT
COMMIT
*nat
:PREROUTING ACCEPT [0:0]
:MPF_NAT_PRE - [0:0]
-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:c1:customer_nat_redirect" -j REDIRECT --to-ports 60010
COMMIT
"""
    snap = parse_iptables_save_text(text)
    assert ("filter", "MPF_INPUT") in snap.chains
    assert ("nat", "MPF_NAT_PRE") in snap.chains
    keys = {r.rule_key for r in snap.rules}
    assert "mpf:c1:customer_dispatch" in keys
    nat = [r for r in snap.rules if r.rule_key == "mpf:c1:customer_nat_redirect"][0]
    assert nat.match_json["port"] == 20001
    assert nat.action_json["target_backend"] == 60010
