from pathlib import Path

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.repositories.customer_repo import CustomerRecord
from mpf.services import customer_read_service
from mpf.services.phase11_canary_reject_session_ip_evidence_capture_service import (
    build_phase11_canary_reject_session_ip_evidence_capture_report,
    write_reject_session_ip_evidence_json,
)
from mpf.services.phase11_canary_visibility_bundle_service import load_phase11_canary_visibility_evidence_json


def _cfg():
    from mpf.config import load_config

    return load_config(Path("configs/mpf.example.yaml"))


def _active():
    return CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)


def _live_ok():
    return {"evidence": {"canary_nat_rule_present": True, "canary_nat_rule_count": 1, "no_extra_customer_nat_rules": True, "no_unexpected_mpf_firewall_references": True, "proxy_doctor_ok": True, "canary_nat_target": "172.18.0.3:60010"}}


def test_missing_source_not_present(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[_active()]))
    monkeypatch.setattr("shutil.which", lambda _: None)
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: _live_ok())
    r = build_phase11_canary_reject_session_ip_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.197", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["reject_evidence"]["reject_visibility_ok"] is False
    assert "missing_source_backed_canary_reject_counters" in r["blockers"]


def test_conntrack_empty_can_set_session_ip_but_not_reject(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[_active()]))
    monkeypatch.setattr("shutil.which", lambda _: "/usr/sbin/conntrack")
    monkeypatch.setattr("subprocess.run", lambda *a, **k: type("R", (), {"returncode": 0, "stdout": ""})())
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: _live_ok())
    r = build_phase11_canary_reject_session_ip_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.197", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["reject_evidence"]["reject_visibility_ok"] is False
    assert r["session_ip_evidence"]["session_visibility_ok"] is True
    assert r["session_ip_evidence"]["unique_ip_visibility_ok"] is True
    assert r["final_decision"] == "PARTIAL_REJECT_SESSION_IP_EVIDENCE"
    assert r["next_required_step"] == "reject_counters_visibility"


def test_broad_backend_dport_not_counted_for_unique_ips(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[_active()]))
    monkeypatch.setattr("shutil.which", lambda _: "/usr/sbin/conntrack")
    # only backend dport=60010; should be ignored by exact-scope filter
    out = "tcp 6 100 ESTABLISHED src=8.8.8.8 dst=172.18.0.3 sport=3344 dport=60010 [ASSURED]"
    monkeypatch.setattr("subprocess.run", lambda *a, **k: type("R", (), {"returncode": 0, "stdout": out})())
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: _live_ok())
    r = build_phase11_canary_reject_session_ip_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.197", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["session_ip_evidence"]["unique_ip_count"] == 0


def test_private_src_not_counted_as_unique_customer_ip(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[_active()]))
    monkeypatch.setattr("shutil.which", lambda _: "/usr/sbin/conntrack")
    out = "tcp 6 100 ESTABLISHED src=172.18.0.22 dst=1.1.1.1 sport=3456 dport=20001 [ASSURED]"
    monkeypatch.setattr("subprocess.run", lambda *a, **k: type("R", (), {"returncode": 0, "stdout": out})())
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: _live_ok())
    r = build_phase11_canary_reject_session_ip_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.197", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["session_ip_evidence"]["unique_ip_count"] == 0


def test_explicit_reject_evidence_json_can_lift_in_bundle(tmp_path, monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[_active()]))
    monkeypatch.setattr("shutil.which", lambda _: "/usr/sbin/conntrack")
    monkeypatch.setattr("subprocess.run", lambda *a, **k: type("R", (), {"returncode": 0, "stdout": ""})())
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: _live_ok())
    r = build_phase11_canary_reject_session_ip_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.197", farm5_baseline_version="0.1.168", collect_live=True)
    p = tmp_path / "ev.json"
    write_reject_session_ip_evidence_json(report=r, path=p)
    txt = p.read_text(encoding="utf-8")
    assert '"component"' not in txt
    # simulate exact explicit reject evidence source in machine-generated JSON
    import json
    obj = json.loads(txt)
    obj["reject_visibility_ok"] = True
    obj["reject_reference"] = "iptables_filter_counter:canary-btc-001:btc:20001"
    p.write_text(json.dumps(obj), encoding="utf-8")
    ev = load_phase11_canary_visibility_evidence_json(p)
    assert ev.reject_visibility_ok is True


def test_mutation_flags_false(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[_active()]))
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: _live_ok())
    r = build_phase11_canary_reject_session_ip_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.197", farm5_baseline_version="0.1.168", collect_live=False)
    assert r["mutation_performed"] is False
    assert r["db_mutation_performed"] is False
    assert r["firewall_mutation_performed"] is False
    assert r["nat_mutation_performed"] is False
    assert r["conntrack_mutation_performed"] is False
    assert r["docker_mutation_performed"] is False


def test_cli_smoke():
    res = CliRunner().invoke(app, ["production", "canary-reject-session-ip-evidence-capture", "--output", "json", "--config", "configs/mpf.example.yaml", "--no-collect-live"])
    assert res.exit_code == 0
    assert '"component": "phase11_canary_reject_session_ip_evidence_capture"' in res.stdout
