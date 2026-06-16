from pathlib import Path

from mpf import __version__
from mpf.services import phase11_production_customer_lifecycle_execution_service as svc
from mpf.services.phase11_production_customer_lifecycle_execution_readiness_service import build_phase11_production_customer_lifecycle_execution_readiness_report
from mpf.services.phase11_operational_completion_gap_inventory_service import build_phase11_operational_completion_gap_inventory_report


def test_package_hash_mismatch_fails_preflight_before_db(monkeypatch, tmp_path):
    pkg={"component":"phase11_production_customer_lifecycle_execution_package","repository_version":__version__,"package_id":"p","target":{"customer_key":"limited-btc-001","lane":"btc","port":20101},"expected_before_state":{"customer_key":"limited-btc-001","lane":"btc","port":20101,"status":"active"},"package_sha256":"bad"}
    p=tmp_path/"pkg.json"; import json; p.write_text(json.dumps(pkg))
    monkeypatch.setattr(svc, "_connect", lambda *_: (_ for _ in ()).throw(RuntimeError("no db")))
    out=svc.preflight(p)
    assert "package_hash_mismatch" in out["blockers"]
    assert out["mutation_performed"] is False
    assert out["firewall_apply_performed"] is False


def test_execute_requires_confirmation_flags(tmp_path):
    p=tmp_path/"pkg.json"; p.write_text("{}")
    out=svc.execute(p, operator="op", reason="test")
    assert out["final_decision"] == "BLOCKED_CONFIRMATION_REQUIRED"
    assert out["db_mutation_performed"] is False
    assert out["phase12_start_allowed"] is False


def test_verify_fails_if_backup_artifact_missing(tmp_path, monkeypatch):
    ev={"backup_path":str(tmp_path/"missing.json"),"backup_sha256":"x","backup_id":1,"restore_point_id":2,"event_id":3,"audit_id":4,"customer_id":5,"firewall_apply_performed":False,"conntrack_flush_performed":False,"docker_restart_performed":False,"systemd_restart_performed":False,"phase12_start_allowed":False}
    p=tmp_path/"ev.json"; import json; p.write_text(json.dumps(ev))
    monkeypatch.setattr(svc, "_connect", lambda *_: (_ for _ in ()).throw(RuntimeError("no db")))
    out=svc.verify(p)
    assert "backup_artifact_missing" in out["blockers"]
    assert out["final_decision"] == "BLOCKED"


def test_readiness_consumes_valid_verifier_evidence_only_for_item_two():
    report=build_phase11_production_customer_lifecycle_execution_readiness_report(lifecycle_execution_evidence={"final_decision":svc.READY})
    assert report["production_customer_lifecycle_execution"] == "controlled_execution_evidence_ready"
    statuses={c["name"]:c["status"] for c in report["checks"]}
    assert statuses["audit_event_path_availability"] == "ready"
    assert statuses["backup_restore_point_requirement"] == "ready"
    assert report["backup_restore_drill"] == "missing_or_partial"
    assert report["full_cli_production_operations"] == "missing_or_partial"
    assert report["phase12_start_allowed"] is False
    assert report["worker_enforcement_allowed"] == "no"
    assert report["ui_allowed"] == "no"
    assert report["telegram_allowed"] == "no"


def test_gap_inventory_advances_next_step_without_accepting_full_gate():
    report=build_phase11_operational_completion_gap_inventory_report(lifecycle_execution_evidence_json=None)
    assert report["full_cli_production_operations"] == "missing_or_partial"
    assert report["phase12_start_allowed"] is False
