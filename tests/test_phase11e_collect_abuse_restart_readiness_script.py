from pathlib import Path


def test_script_real_source_collection_enforced():
    t = Path('scripts/phase11e_collect_abuse_restart_readiness_evidence.sh').read_text()
    banned = [
        "iptables_save_text=''",
        "ip6tables_save_text=''",
        "required_containers_running':True",
        "v2raya_running_before_forwarder_check':True",
        "socks_bridge_ready_before_forwarder_check':True",
        "forwarder_ready':True",
        "bridge_ready':True",
        "backend_60010_local_or_internal_reachable':True",
        "public_v2raya_ui_exposed':False",
        "backend_60010_publicly_exposed':False",
    ]
    for x in banned:
        assert x not in t
    for x in ['docker-ps.txt', 'ss-listen.txt', 'required_names', 'backend_public', 'public_v2raya_ui', 'controlled_order_test_performed', 'iptables-save', 'ip6tables-save']:
        assert x in t


def test_script_uses_customer_list_customers_and_python_bin():
    t = Path('scripts/phase11e_collect_abuse_restart_readiness_evidence.sh').read_text()
    assert 'cust_res.customers' in t
    assert 'cust_res.rows' not in t
    assert 'PYTHON_BIN="${MPF_PYTHON:-$REPO_ROOT/.venv/bin/python}"' in t
    assert 'if [[ ! -x "$PYTHON_BIN" ]]; then' in t
    assert '"$PYTHON_BIN" - <<\'PY\'' in t


def test_script_has_no_hardcoded_helper_customers_or_forbidden_mutations():
    t = Path('scripts/phase11e_collect_abuse_restart_readiness_evidence.sh').read_text()
    for s in ['limited-btc-001', 'canary-btc-001']:
        assert s not in t
    for cmd in [
        'iptables-restore', 'conntrack -F', 'docker restart', 'docker compose up', 'docker compose down',
        'docker compose restart', 'systemctl restart', 'systemctl enable', 'mpf abuse hard',
        'mpf abuse unhard', 'mpf customer activate',
    ]:
        assert cmd not in t


def test_script_writes_manifest_with_required_fields():
    t = Path('scripts/phase11e_collect_abuse_restart_readiness_evidence.sh').read_text()
    for s in [
        'manifest.json',
        '"expected_version"',
        '"generated_at"',
        '"visibility_bundle_json"',
        '"visibility_bundle_sha256"',
        '"source_evidence_json"',
        '"artifact_gate_json"',
        '"abuse_readiness_json"',
        '"restart_readiness_json"',
        '"limited_acceptance_precheck_json"',
        '"sha256_manifest"',
        '"final_summary"',
        '"next_required_step"',
    ]:
        assert s in t
