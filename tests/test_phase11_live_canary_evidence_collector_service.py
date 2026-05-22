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
        return _CP('*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\n-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.3:60010\nCOMMIT\n')
    if "-vnL" in line:
        return _CP('num  pkts bytes target prot opt in out source destination\n1 9 666 DNAT tcp -- * * 0.0.0.0/0 0.0.0.0/0 tcp dpt:20001 /* mpf:canary-btc-001:customer_nat_redirect */ to:172.18.0.3:60010\n')
    if line.startswith("conntrack"):
        return _CP('tcp 6 431999 ESTABLISHED src=1.1.1.1 dst=2.2.2.2 sport=1000 dport=20001 [ASSURED]')
    return _CP('', 1)


def test_collect_nat_and_conntrack(monkeypatch):
    from mpf.config import load_config

    monkeypatch.setattr(svc.shutil, "which", lambda _: "/usr/bin/x")
    monkeypatch.setattr(svc.subprocess, "run", _fake_run)
    monkeypatch.setattr(svc.proxy_doctor_service, "run", lambda: type("R", (), {"final_verdict": type("V", (), {"value": "ok"})(), "checks": []})())
    rep = svc.build_phase11_live_canary_evidence_collector_report(load_config(Path("configs/mpf.example.yaml")), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.171", farm5_baseline_version="0.1.168")
    ev = rep["evidence"]
    assert ev["mpf_nat_pre_exists"] is True
    assert ev["canary_nat_rule_count"] == 1
    assert ev["canary_nat_target"] == "172.18.0.3:60010"
    assert ev["nat_counter_packets"] == 9
    assert ev["conntrack_assured"] is True


def test_cli_collect_live_smoke(monkeypatch):
    monkeypatch.setattr(svc, "build_phase11_live_canary_evidence_collector_report", lambda *a, **k: {"component": "phase11_live_canary_evidence_collector", "final_decision": "PARTIAL_EVIDENCE", "blockers": [], "warnings": [], "commands_attempted": [], "commands_unavailable": [], "evidence": {}})
    res = CliRunner().invoke(app, ["production", "canary-evidence-collect", "--output", "json", "--config", "configs/mpf.example.yaml"])
    assert res.exit_code == 0
    assert 'phase11_live_canary_evidence_collector' in res.stdout
