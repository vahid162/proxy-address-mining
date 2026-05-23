from pathlib import Path

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.domain.production import Phase11CanaryDbVisibilityActivationRequest
from mpf.interfaces.cli import app
from mpf.repositories.customer_repo import CustomerRecord
from mpf.services import customer_read_service, operator_execution_context_service, phase11_canary_usage_evidence_capture_service
from mpf.services.phase11_canary_db_visibility_activation_service import build_phase11_canary_db_visibility_activation_report
from mpf.services.phase11_canary_usage_visibility_service import build_phase11_canary_usage_visibility_report
from mpf.services.phase11_canary_visibility_bundle_service import build_phase11_canary_visibility_bundle_report
from mpf.services.phase11_canary_acceptance_review_service import build_phase11_canary_acceptance_review_report, Phase11CanaryAcceptanceEvidence


def _cfg():
    return load_config(Path("configs/mpf.example.yaml"))


def _active_canary():
    return CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)


def test_operator_context_effective_root_read_ok(monkeypatch):
    monkeypatch.setattr("os.geteuid", lambda: 0)
    monkeypatch.setattr("pwd.getpwuid", lambda _uid: type("P", (), {"pw_name": "root"})())
    monkeypatch.setattr("getpass.getuser", lambda: "root")
    r = operator_execution_context_service.build_operator_execution_context_report(_cfg(), mode="read")
    assert r["final_decision"] == "OK_FOR_READ"


def test_operator_context_effective_root_db_write_blocked(monkeypatch):
    monkeypatch.setattr("os.geteuid", lambda: 0)
    monkeypatch.setattr("pwd.getpwuid", lambda _uid: type("P", (), {"pw_name": "root"})())
    monkeypatch.setattr("getpass.getuser", lambda: "root")
    r = operator_execution_context_service.build_operator_execution_context_report(_cfg(), mode="db-write")
    assert r["final_decision"] == "BLOCKED"
    assert "db_write_requires_mpf_os_user" in r["blockers"]


def test_operator_context_effective_mpf_db_write_ok(monkeypatch):
    monkeypatch.setattr("os.geteuid", lambda: 999)
    monkeypatch.setattr("pwd.getpwuid", lambda _uid: type("P", (), {"pw_name": "mpf"})())
    monkeypatch.setattr("getpass.getuser", lambda: "mpf")
    r = operator_execution_context_service.build_operator_execution_context_report(_cfg(), mode="db-write")
    assert r["final_decision"] == "OK_FOR_DB_WRITE"


def test_operator_context_env_mpf_but_effective_root_blocked(monkeypatch):
    monkeypatch.setattr("os.geteuid", lambda: 0)
    monkeypatch.setattr("pwd.getpwuid", lambda _uid: type("P", (), {"pw_name": "root"})())
    monkeypatch.setattr("getpass.getuser", lambda: "mpf")
    r = operator_execution_context_service.build_operator_execution_context_report(_cfg(), mode="db-write")
    assert r["final_decision"] == "BLOCKED"
    assert r["env_user"] == "mpf"


def test_operator_context_non_local_peer_not_blocked(monkeypatch):
    cfg = _cfg()
    cfg.database.url = "postgresql://u:p@127.0.0.1:5432/mpf"
    monkeypatch.setattr("os.geteuid", lambda: 0)
    monkeypatch.setattr("pwd.getpwuid", lambda _uid: type("P", (), {"pw_name": "root"})())
    monkeypatch.setattr("getpass.getuser", lambda: "root")
    r = operator_execution_context_service.build_operator_execution_context_report(cfg, mode="db-write")
    assert r["final_decision"] == "OK_FOR_DB_WRITE"


def test_canary_db_visibility_execute_blocks_before_db_write_on_effective_root(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    monkeypatch.setattr("mpf.services.operator_execution_context_service.build_operator_execution_context_report", lambda *a, **k: {"database_url_is_local_peer": True, "os_user": "root"})
    called = {"create": False}

    def _fake_create(*a, **k):
        called["create"] = True
        raise AssertionError("must not attempt db write")

    monkeypatch.setattr("mpf.services.customer_mutation_service.create_db_only_customer", _fake_create)
    req = Phase11CanaryDbVisibilityActivationRequest(requested_action="execute", expected_version="0.1.186", operator_confirmed=True, understand_db_only_canary=True, understand_no_firewall_or_nat=True, reviewed_rollback=True, fresh_farm5_sync_confirmed=True)
    r = build_phase11_canary_db_visibility_activation_report(_cfg(), req)
    assert r["final_decision"] == "BLOCKED"
    assert "db_write_requires_mpf_os_user" in r["blockers"]
    assert called["create"] is False


def test_canary_db_visibility_plan_allowed_as_root(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    monkeypatch.setattr("mpf.services.operator_execution_context_service.build_operator_execution_context_report", lambda *a, **k: {"database_url_is_local_peer": True, "os_user": "root"})
    req = Phase11CanaryDbVisibilityActivationRequest(requested_action="plan", expected_version="0.1.186")
    r = build_phase11_canary_db_visibility_activation_report(_cfg(), req)
    assert r["final_decision"] == "DB_VISIBILITY_PLAN_READY"


def test_usage_capture_missing_db_visibility_not_ready(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: {"evidence": {"canary_nat_rule_present": True, "canary_nat_rule_count": 1, "no_extra_customer_nat_rules": True, "no_unexpected_mpf_firewall_references": True, "proxy_doctor_ok": True, "nat_counter_packets": 1, "nat_counter_bytes": 10, "canary_nat_target": "172.18.0.3:60010"}})
    r = phase11_canary_usage_evidence_capture_service.build_phase11_canary_usage_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.186", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["final_decision"] in {"BLOCKED", "MISSING_USAGE_EVIDENCE"}


def test_usage_capture_clean_live_ready_and_non_mutating(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[_active_canary()]))
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: {"evidence": {"canary_nat_rule_present": True, "canary_nat_rule_count": 1, "no_extra_customer_nat_rules": True, "no_unexpected_mpf_firewall_references": True, "proxy_doctor_ok": True, "nat_counter_packets": 0, "nat_counter_bytes": 696, "canary_nat_target": "172.18.0.3:60010"}})
    r = phase11_canary_usage_evidence_capture_service.build_phase11_canary_usage_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.186", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["final_decision"] == "USAGE_EVIDENCE_READY"
    assert r["usage_evidence"]["usage_visibility_ok"] is True
    assert r["usage_evidence"]["usage_reference"]
    assert r["usage_evidence"]["total_bytes"] > 0
    assert r["mutation_performed"] is False and r["db_mutation_performed"] is False and r["firewall_mutation_performed"] is False


def test_usage_capture_zero_counters_missing(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[_active_canary()]))
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: {"evidence": {"canary_nat_rule_present": True, "canary_nat_rule_count": 1, "no_extra_customer_nat_rules": True, "no_unexpected_mpf_firewall_references": True, "proxy_doctor_ok": True, "nat_counter_packets": 0, "nat_counter_bytes": 0, "canary_nat_target": "172.18.0.3:60010"}})
    r = phase11_canary_usage_evidence_capture_service.build_phase11_canary_usage_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.186", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["final_decision"] == "MISSING_USAGE_EVIDENCE"


def test_usage_capture_duplicate_nat_rule_blocked(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[_active_canary()]))
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: {"evidence": {"canary_nat_rule_present": True, "canary_nat_rule_count": 2, "no_extra_customer_nat_rules": False, "no_unexpected_mpf_firewall_references": True, "proxy_doctor_ok": True, "nat_counter_packets": 1, "nat_counter_bytes": 1, "canary_nat_target": "172.18.0.3:60010"}})
    r = phase11_canary_usage_evidence_capture_service.build_phase11_canary_usage_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.186", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["final_decision"] == "BLOCKED"


def test_usage_capture_proxy_doctor_false_not_ready(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[_active_canary()]))
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: {"evidence": {"canary_nat_rule_present": True, "canary_nat_rule_count": 1, "no_extra_customer_nat_rules": True, "no_unexpected_mpf_firewall_references": True, "proxy_doctor_ok": False, "nat_counter_packets": 1, "nat_counter_bytes": 1, "canary_nat_target": "172.18.0.3:60010"}})
    r = phase11_canary_usage_evidence_capture_service.build_phase11_canary_usage_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.186", farm5_baseline_version="0.1.168", collect_live=True)
    assert r["final_decision"] in {"BLOCKED", "MISSING_USAGE_EVIDENCE"}


def test_write_evidence_json_object_only_and_overwrite_guard(tmp_path, monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[_active_canary()]))
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: {"evidence": {"canary_nat_rule_present": True, "canary_nat_rule_count": 1, "no_extra_customer_nat_rules": True, "no_unexpected_mpf_firewall_references": True, "proxy_doctor_ok": True, "nat_counter_packets": 0, "nat_counter_bytes": 100, "canary_nat_target": "172.18.0.3:60010"}})
    r = phase11_canary_usage_evidence_capture_service.build_phase11_canary_usage_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.186", farm5_baseline_version="0.1.168", collect_live=True)
    p = tmp_path / "evidence.json"
    phase11_canary_usage_evidence_capture_service.write_usage_evidence_json(report=r, path=p)
    txt = p.read_text(encoding="utf-8")
    assert '"usage_visibility_ok"' in txt
    assert '"component"' not in txt
    try:
        phase11_canary_usage_evidence_capture_service.write_usage_evidence_json(report=r, path=p)
        assert False
    except ValueError:
        pass
    phase11_canary_usage_evidence_capture_service.write_usage_evidence_json(report=r, path=p, overwrite=True)


def test_generated_usage_evidence_integration_visibility_bundle_acceptance(monkeypatch):
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[_active_canary()]))
    monkeypatch.setattr("mpf.services.phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report", lambda *a, **k: {"evidence": {"canary_nat_rule_present": True, "canary_nat_rule_count": 1, "no_extra_customer_nat_rules": True, "no_unexpected_mpf_firewall_references": True, "proxy_doctor_ok": True, "nat_counter_packets": 0, "nat_counter_bytes": 696, "canary_nat_target": "172.18.0.3:60010"}})
    cap = phase11_canary_usage_evidence_capture_service.build_phase11_canary_usage_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.186", farm5_baseline_version="0.1.168", collect_live=True)
    ev = cap["usage_evidence"]
    usage = build_phase11_canary_usage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.186", farm5_baseline_version="0.1.168", evidence=type("E", (), ev)() if False else None)
    # easier: use class loader
    from mpf.services.phase11_canary_usage_visibility_service import Phase11CanaryUsageVisibilityEvidence
    usage = build_phase11_canary_usage_visibility_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.186", farm5_baseline_version="0.1.168", evidence=Phase11CanaryUsageVisibilityEvidence.from_dict(ev))
    assert usage["usage_counters_visibility"]["status"] == "PRESENT"

    from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence
    bundle = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.186", farm5_baseline_version="0.1.168", evidence=Phase11CanaryVisibilityEvidence.from_dict(ev))
    assert bundle["visibility"]["usage_counters_visibility"]["status"] == "PRESENT"
    for k in ("reject_counters_visibility", "active_recent_sessions_visibility", "unique_ips_visibility", "unique_workers_visibility", "abuse_coverage_visibility", "final_check_report_visibility", "rollback_or_restore_plan_visibility"):
        assert bundle["visibility"][k]["status"] != "PRESENT"

    acc = build_phase11_canary_acceptance_review_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.186", farm5_baseline_version="0.1.168", evidence=Phase11CanaryAcceptanceEvidence(canary_customer_db_visible=True, usage_visibility_ok=True))
    assert "usage_counters_visibility" not in acc["missing_visibility_primitives"]
    assert acc["next_required_step"] == "reject_counters_visibility"


def test_usage_capture_cli_smoke():
    res = CliRunner().invoke(app, ["production", "canary-usage-evidence-capture", "--output", "json", "--config", "configs/mpf.example.yaml", "--no-collect-live"])
    assert res.exit_code == 0
    assert '"component": "phase11_canary_usage_evidence_capture"' in res.output
