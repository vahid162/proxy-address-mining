from pathlib import Path


def test_helper_waits_for_transcript_after_runtime_capture() -> None:
    t = Path('scripts/phase11e_collect_runtime_stratum_evidence.sh').read_text(encoding='utf-8')
    assert '--wait-for-transcript-seconds' in t
    assert '--capture-delay-seconds' in t
    assert 'iptables-save > "$OUT_DIR/live-iptables-save.txt"' in t
    assert '--conntrack-repeat-count' in t
    assert '--conntrack-repeat-delay-seconds' in t
    assert 'conntrack -L >> "$OUT_DIR/conntrack.txt"' in t
    wait_pos = t.index('for ((i=0; i<=WAIT_FOR_TRANSCRIPT_SECONDS; i++)); do')
    cap_pos = t.index('conntrack -L >> "$OUT_DIR/conntrack.txt"')
    assert cap_pos < wait_pos


def test_helper_contains_no_activation_or_apply_commands() -> None:
    t = Path('scripts/phase11e_collect_runtime_stratum_evidence.sh').read_text(encoding='utf-8')
    forbidden = ['iptables-restore', ' mpf firewall apply', 'mpf production activate', 'mining.submit']
    for marker in forbidden:
        assert marker not in t


def test_helper_uses_forwarder_btc_and_captures_stderr_logs() -> None:
    t = Path('scripts/phase11e_collect_runtime_stratum_evidence.sh').read_text(encoding='utf-8')
    assert 'FORWARDER_CONTAINER="mpf-forwarder-btc"' in t
    assert 'docker logs --since 15m "$FORWARDER_CONTAINER" > "$OUT_DIR/forwarder.log" 2>&1' in t
    assert 'docker logs --since 15m "$BRIDGE_CONTAINER" > "$OUT_DIR/bridge.log" 2>&1' in t
    assert 'FORWARDER_CONTAINER="mpf-forwarder"' not in t


def test_helper_passes_expected_version_to_visibility_bundle() -> None:
    t = Path('scripts/phase11e_collect_runtime_stratum_evidence.sh').read_text(encoding='utf-8')
    assert 'single-customer-visibility-bundle --expected-version "$EXPECTED_VERSION"' in t


def test_helper_derives_expected_version_from_version_file() -> None:
    t = Path('scripts/phase11e_collect_runtime_stratum_evidence.sh').read_text(encoding='utf-8')
    assert 'EXPECTED_VERSION="0.1.216"' not in t
    assert 'EXPECTED_VERSION="0.1.218"' not in t
    assert 'VERSION_FILE="$REPO_ROOT/VERSION"' in t
    assert 'CRITICAL: VERSION file missing or empty: $VERSION_FILE' in t
    assert "EXPECTED_VERSION=\"$(tr -d" in t
    assert "< \"$VERSION_FILE\")\"" in t
    assert 'CRITICAL: expected version is empty after reading VERSION' in t
