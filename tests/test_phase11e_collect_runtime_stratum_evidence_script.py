from pathlib import Path


def test_helper_waits_for_transcript_after_runtime_capture() -> None:
    t = Path('scripts/phase11e_collect_runtime_stratum_evidence.sh').read_text(encoding='utf-8')
    assert '--wait-for-transcript-seconds' in t
    assert '--capture-delay-seconds' in t
    assert 'iptables-save > "$OUT_DIR/live-iptables-save.txt"' in t
    assert 'conntrack -L > "$OUT_DIR/conntrack.txt"' in t
    wait_pos = t.index('for ((i=0; i<=WAIT_FOR_TRANSCRIPT_SECONDS; i++)); do')
    cap_pos = t.index('conntrack -L > "$OUT_DIR/conntrack.txt"')
    assert cap_pos < wait_pos


def test_helper_contains_no_activation_or_apply_commands() -> None:
    t = Path('scripts/phase11e_collect_runtime_stratum_evidence.sh').read_text(encoding='utf-8')
    forbidden = ['iptables-restore', ' mpf firewall apply', 'mpf production activate', 'mining.submit']
    for marker in forbidden:
        assert marker not in t
