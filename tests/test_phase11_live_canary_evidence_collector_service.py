from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services import phase11_live_canary_evidence_collector_service as svc


class _CP:
    def __init__(self, out: str, code: int = 0):
        self.stdout = out
        self.returncode = code


def _fake_run(cmd, check, capture_output, text):
    line = " ".join(cmd)
    if line.startswith("iptables-save"):
        return _CP('*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.3:60010\nCOMMIT\n')
    if "-vnL" in line:
        return _CP('num  pkts bytes target prot opt in out source destination\n1 9 666 DNAT tcp -- * * 0.0.0.0/0 0.0.0.0/0 tcp dpt:20001 /* mpf:canary-btc-001:customer_nat_redirect */ to:172.18.0.3:60010\n')
    if line.startswith("conntrack"):
        return _CP('tcp 6 431999 ESTABLISHED src=1.1.1.1 dst=2.2.2.2 sport=1000 dport=20001 [ASSURED]')
    return _CP('', 1)


def _fake_proxy_doctor_report_ok():
    class _Status:
        def __init__(self, value):
            self.value = value

    class _Check:
        def __init__(self, key, status):
            self.key = key
            self.status = _Status(status)

    class _Report:
        final_verdict = _Status("OK")
        checks = [
            _Check("proxy_container_state", "OK"),
            _Check("v2raya_ui_local_only", "OK"),
            _Check("v2raya_ui_listener_state", "OK"),
            _Check("backend_docker_publish_mode.btc", "OK"),
            _Check("lane.btc.backend_listener_state", "OK"),
            _Check("lane.btc.backend_internal_reachability", "OK"),
            _Check("backend_docker_publish_mode.v2raya_socks", "OK"),
            _Check("v2raya_socks_bridge_host_publish", "OK"),
            _Check("lane.btc.forwarder_upstream_socks", "OK"),
        ]

    return _Report()


def test_collect_nat_and_conntrack_with_real_farm5_syntax(monkeypatch):
    from mpf.config import load_config

    monkeypatch.setattr(svc.shutil, "which", lambda _: "/usr/bin/x")
    monkeypatch.setattr(svc.subprocess, "run", _fake_run)
    monkeypatch.setattr(svc.proxy_doctor_service, "run", _fake_proxy_doctor_report_ok)

    rep = svc.build_phase11_live_canary_evidence_collector_report(
        load_config(Path("configs/mpf.example.yaml")),
        customer_key="canary-btc-001",
        lane="btc",
        port=20001,
        expected_version="0.1.193",
        farm5_baseline_version="0.1.168",
    )
    ev = rep["evidence"]
    assert ev["canary_nat_rule_present"] is True
    assert ev["canary_nat_rule_count"] == 1
    assert ev["canary_nat_target"] == "172.18.0.3:60010"
    assert ev["no_extra_customer_nat_rules"] is True
    assert ev["no_unexpected_mpf_firewall_references"] is True
    assert ev["nat_counter_packets"] == 9
    assert ev["conntrack_assured"] is True


def test_proxy_doctor_key_mapping(monkeypatch):
    from mpf.config import load_config

    monkeypatch.setattr(svc.shutil, "which", lambda _: None)
    monkeypatch.setattr(svc.proxy_doctor_service, "run", _fake_proxy_doctor_report_ok)

    rep = svc.build_phase11_live_canary_evidence_collector_report(
        load_config(Path("configs/mpf.example.yaml")),
        customer_key="canary-btc-001",
        lane="btc",
        port=20001,
        expected_version="0.1.193",
        farm5_baseline_version="0.1.168",
    )
    ev = rep["evidence"]
    assert ev["proxy_doctor_ok"] is True
    assert ev["bridge_healthy"] is True
    assert ev["bridge_reachable_from_forwarder"] is True
    assert ev["v2raya_ui_local_only"] is True
    assert ev["btc_backend_local_only"] is True
    assert ev["bridge_no_host_publish"] is True
    assert ev["forwarder_uses_bridge_upstream"] is True
    assert ev["direct_v2raya_20170_blocked"] is True


def test_cli_collect_live_smoke(monkeypatch):
    monkeypatch.setattr(svc, "build_phase11_live_canary_evidence_collector_report", lambda *a, **k: {"component": "phase11_live_canary_evidence_collector", "final_decision": "PARTIAL_EVIDENCE", "blockers": [], "warnings": [], "commands_attempted": [], "commands_unavailable": [], "evidence": {}})
    res = CliRunner().invoke(app, ["production", "canary-evidence-collect", "--output", "json", "--config", "configs/mpf.example.yaml"])
    assert res.exit_code == 0
    assert 'phase11_live_canary_evidence_collector' in res.stdout
