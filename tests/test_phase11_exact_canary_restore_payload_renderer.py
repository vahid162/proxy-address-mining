from mpf.services.phase11_exact_canary_restore_payload_renderer import Phase11ExactCanaryRestorePayloadRenderer


def _report():
    return {
        "scope": {"single_canary_only": True},
        "request": {
            "requested_action": "execute", "expected_version": "0.1.213", "customer_key": "canary-btc-001", "lane": "btc", "port": 20001,
            "operator_confirmed": True, "understand_canary_customer": True, "understand_firewall_apply": True, "reviewed_rollback": True, "fresh_farm5_sync_confirmed": True,
        },
        "preflight_results": {k: "OK" for k in ("phase_gate", "mpf_doctor", "db_status", "proxy_doctor", "no_customer_nat_baseline", "no_customer_firewall_baseline", "local_only_runtime_baseline")},
        "restore_point": {"id": "rp-1"},
        "iptables_save_backup": {"id": "bk-1"},
        "lock": {"acquired": True},
        "firewall_plan": {"status": "ok", "lane": "btc", "customer_port": 20001, "backend_port": 60010},
        "firewall_diff": {"json_diff": {"customer_port": 20001, "backend_port": 60010}},
        "live_nat_prerequisites": {"mpf_nat_pre_chain_exists": True, "prerouting_hook_to_mpf_nat_pre_count": 1},
        "single_canary_backend_target": {"status": "ok", "target_host": "172.18.0.3", "target_port": 60010, "target_kind": "docker_container_ipv4"},
    }


def test_renderer_ok_exact_payload() -> None:
    out = Phase11ExactCanaryRestorePayloadRenderer().render(_report())
    assert out["status"] == "ok"
    p = out["restore_payload"]
    assert p.count("--dport 20001") == 3
    assert ":MPFC_20001 - [0:0]" in p
    assert "mpf:canary-btc-001:customer_connlimit_reject" in p
    assert "mpf:canary-btc-001:customer_hashlimit_reject" in p
    assert "--to-destination 172.18.0.3:60010" in p
    assert "canary-btc-001" in p
    assert "--dport 20002" not in p
    assert out["mutation_performed"] is False


def test_renderer_blocks_wrong_scope() -> None:
    r = _report(); r["request"]["customer_key"] = "x"
    assert Phase11ExactCanaryRestorePayloadRenderer().render(r)["status"] == "blocked"


def test_renderer_existing_nat_renders_filter_only() -> None:
    r = _report()
    r["live_nat_prerequisites"]["canary_rule_exists"] = True
    out = Phase11ExactCanaryRestorePayloadRenderer().render(r)
    assert out["status"] == "ok"
    p = out["restore_payload"]
    assert "*nat" not in p
    assert "customer_nat_redirect" not in p
    assert p.count("--dport 20001") == 2
    assert "*filter" in p
