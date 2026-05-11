from mpf.services import firewall_snapshot_parser
from mpf.services.firewall_rollback_artifact_renderer import render_rollback_artifact_from_snapshot


def test_rollback_contract_flags() -> None:
    snap = firewall_snapshot_parser.parse_iptables_save_text("*filter\n:MPF_INPUT - [0:0]\nCOMMIT\n")
    contract = render_rollback_artifact_from_snapshot(snap, source="offline_snapshot_file")
    assert contract.artifact_only is True
    assert contract.inspection_only is True
    assert contract.rollback_execution_allowed_now is False
    assert contract.live_apply_allowed is False
    assert contract.applyable is False
    assert contract.safety_flags["iptables_save_executed"] is False
    assert contract.safety_flags["iptables_restore_executed"] is False


def test_rollback_deterministic_payload_hash() -> None:
    text = "*filter\n:MPF_INPUT - [0:0]\n-A MPF_INPUT -m comment --comment \"mpf:a\" -j RETURN\nCOMMIT\n"
    snap = firewall_snapshot_parser.parse_iptables_save_text(text)
    c1 = render_rollback_artifact_from_snapshot(snap)
    c2 = render_rollback_artifact_from_snapshot(snap)
    assert c1.rollback_payload is not None and c2.rollback_payload is not None
    assert c1.rollback_payload.payload_sha256 == c2.rollback_payload.payload_sha256
    assert c1.source_snapshot_hash == c2.source_snapshot_hash
    assert "*filter" in c1.rollback_payload.payload
    assert "COMMIT" in c1.rollback_payload.payload
    assert '-A MPF_INPUT -m comment --comment "mpf:a" -j RETURN' in c1.rollback_payload.payload


def test_rollback_invalid_empty_snapshot() -> None:
    snap = firewall_snapshot_parser.parse_iptables_save_text("")
    contract = render_rollback_artifact_from_snapshot(snap)
    assert contract.renderable is False
    assert contract.errors


def test_rollback_source_hash_changes_when_snapshot_body_changes() -> None:
    t1 = "*filter\n:MPF_GUARD - [0:0]\n-A MPF_GUARD -m comment --comment \"mpf:backend_guard:btc:60010\" -j RETURN\nCOMMIT\n"
    t2 = "*filter\n:MPF_GUARD - [0:0]\n-A MPF_GUARD -m comment --comment \"mpf:backend_guard:btc:60010\" -j DROP\nCOMMIT\n"
    c1 = render_rollback_artifact_from_snapshot(firewall_snapshot_parser.parse_iptables_save_text(t1))
    c2 = render_rollback_artifact_from_snapshot(firewall_snapshot_parser.parse_iptables_save_text(t2))
    assert c1.source_snapshot_hash != c2.source_snapshot_hash
