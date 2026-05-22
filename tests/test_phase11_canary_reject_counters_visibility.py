from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.repositories.customer_repo import CustomerRecord
from mpf.services import customer_read_service
from mpf.services.phase11_canary_reject_counters_visibility_service import build_phase11_canary_reject_counters_visibility_report


def _cfg():
    from mpf.config import load_config
    return load_config(Path("configs/mpf.example.yaml"))


def _active():
    return CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)


def _live_ok():
    return {"evidence": {"canary_nat_rule_present": True, "canary_nat_rule_count": 1, "no_extra_customer_nat_rules": True, "no_unexpected_mpf_firewall_references": True, "proxy_doctor_ok": True, "canary_nat_target": "172.18.0.3:60010"}}


def test_missing_source_reports_missing(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[_active()]))
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: _live_ok())
    monkeypatch.setattr("shutil.which", lambda _: "/usr/sbin/iptables")
    monkeypatch.setattr("subprocess.run", lambda *a, **k: type("R", (), {"returncode": 0, "stdout": ""})())
    r = build_phase11_canary_reject_counters_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.181", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["reject_evidence"]["reject_visibility_ok"] is False
    assert r["next_required_step"] == "reject_counters_visibility"


def test_exact_zero_counts_present(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[_active()]))
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: _live_ok())
    monkeypatch.setattr("shutil.which", lambda _: "/usr/sbin/iptables")
    out = 'num  pkts bytes target prot opt in out source destination\n1 0 0 REJECT tcp -- * * 0.0.0.0/0 0.0.0.0/0 /* mpf:canary-btc-001:customer_connlimit_reject */\n2 0 0 REJECT tcp -- * * 0.0.0.0/0 0.0.0.0/0 /* mpf:canary-btc-001:customer_hashlimit_reject */\n3 0 0 REJECT tcp -- * * 0.0.0.0/0 0.0.0.0/0 /* mpf:canary-btc-001:customer_pause_reject */\n4 0 0 REJECT tcp -- * * 0.0.0.0/0 0.0.0.0/0 /* mpf:canary-btc-001:customer_block_reject */\n'
    monkeypatch.setattr("subprocess.run", lambda *a, **k: type("R", (), {"returncode": 0, "stdout": out})())
    r = build_phase11_canary_reject_counters_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.181", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["reject_evidence"]["reject_visibility_ok"] is True
    assert r["reject_evidence"]["total_reject_count"] == 0
    assert r["next_required_step"] == "unique_workers_visibility"


def test_cli_smoke():
    res = CliRunner().invoke(app, ["production", "canary-reject-counters-visibility", "--output", "json", "--config", "configs/mpf.example.yaml", "--no-collect-live"])
    assert res.exit_code == 0
    assert '"component": "phase11_canary_reject_counters_visibility"' in res.stdout
