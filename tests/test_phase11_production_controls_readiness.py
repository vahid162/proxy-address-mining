import json
from types import SimpleNamespace

from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.repositories import customer_repo
from mpf.repositories.customer_write_repo import CustomerMutationResult
from mpf.services import phase11_operational_completion_gap_inventory_service as gap
from mpf.services import phase11_production_controls_pause_block_expire_readiness_service as svc
from mpf.domain.customer_lifecycle import ALLOWED_CUSTOMER_STATUSES


def test_controls_readiness_service(monkeypatch):
    monkeypatch.setattr(svc.customer_read_service, "show_customer", lambda cfg, customer_key: SimpleNamespace(ok=True, customer=object(), message="OK"))
    monkeypatch.setattr(svc.customer_mutation_service, "disable_db_only_customer", lambda cfg, req, dry_run: CustomerMutationResult(ok=True, message="DRY_RUN_OK", customer_key=req.customer_key, would_mutate_customer=True, would_create_event=True, would_create_audit=True))
    monkeypatch.setattr(svc.customer_mutation_service, "update_db_only_customer", lambda cfg, req, dry_run: CustomerMutationResult(ok=True, message="DRY_RUN_OK", customer_key=req.customer_key, would_mutate_customer=True, would_create_event=True, would_create_audit=True))
    r = svc.build_phase11_production_controls_pause_block_expire_readiness_report(SimpleNamespace())
    assert r["pause_preflight"]["ready"] is True
    assert r["expire_run_preflight"]["ready"] is True
    assert r["block_preflight"]["ready"] is False
    assert "block_capability_not_defined" in r["block_preflight"]["blockers"]
    assert r["production_controls_pause_block_expire"] == "missing_or_partial"
    assert r["production_controls_pause_block_expire_ready"] is False
    assert r["mutation_performed"] is False and r["db_mutation_performed"] is False
    assert r["phase12_start_allowed"] is False
    assert r["worker_enforcement_allowed"] == r["ui_allowed"] == r["telegram_allowed"] == "no"
    assert "READY" not in r["final_decision"]


def test_controls_cli_json(monkeypatch):
    monkeypatch.setattr(svc, "run_phase11_production_controls_pause_block_expire_readiness_report", lambda *a, **k: {
        "component":"phase11_production_controls_pause_block_expire_readiness", "pause_preflight":{}, "expire_run_preflight":{}, "block_preflight":{"ready":False}, "production_controls_pause_block_expire_ready":False, "final_decision":"BLOCKED"})
    res = CliRunner().invoke(app, ["production", "production-controls-pause-block-expire-readiness", "--output", "json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert "pause_preflight" in data and "expire_run_preflight" in data and "block_preflight" in data
    assert data["production_controls_pause_block_expire_ready"] is False


def test_customer_show_optional_int_mapping_blank_and_invalid():
    base={"id":1,"customer_key":"limited-btc-001","lane":"btc","name":"n","port":20101,"status":"active","activation_mode":"first_connect","service_days":None,"activated_at":None,"starts_at":None,"expires_at":None,"first_connected_at":None,"expired_at":None,"delete_eligible_at":None,"deleted_at":None,"auto_expire_enabled":False,"auto_delete_enabled":False,"lifecycle_note":None,"miners":"","farms":"   ","maxconn":"30","rate_per_min":None,"burst":1,"ips_mode":"any","abuse_exempt":None,"abuse_exempt_reason":None,"abuse_exempt_until":None,"abuse_exempt_by":None}
    assert customer_repo._map_show({**base, "service_days": None}).service_days is None
    assert customer_repo._map_show({**base, "service_days": ""}).service_days is None
    assert customer_repo._map_show({**base, "service_days": "   "}).service_days is None
    assert customer_repo._map_show({**base, "service_days": "30"}).service_days == 30
    assert customer_repo._map_show(base).maxconn == 30
    try:
        customer_repo._map_show({**base, "service_days": "bad"})
    except customer_repo.CustomerMappingError as exc:
        assert "invalid optional integer for service_days" in str(exc)
    else:
        raise AssertionError("expected controlled mapping error")


def test_gap_inventory_embeds_controls(monkeypatch):
    readiness={"component":"phase11_production_controls_pause_block_expire_readiness","production_controls_pause_block_expire":"missing_or_partial","block_preflight":{"blockers":["block_capability_not_defined"]}}
    monkeypatch.setattr(gap, "run_phase11_production_controls_pause_block_expire_readiness_report", lambda *a, **k: readiness)
    monkeypatch.setattr(gap, "run_phase11_production_customer_lifecycle_execution_readiness_report", lambda *a, **k: {"production_customer_lifecycle_execution":"missing_or_partial"})
    r=gap.build_phase11_operational_completion_gap_inventory_report()
    assert r["production_controls_pause_block_expire"] == "missing_or_partial"
    assert r["production_controls_pause_block_expire_readiness"] is readiness
    assert "block_capability_not_defined" in r["production_controls_pause_block_expire_readiness"]["block_preflight"]["blockers"]
    assert r["backup_restore_drill"] == "missing_or_partial"
    assert r["full_cli_production_operations"] == "missing_or_partial"
    assert r["phase12_start_allowed"] is False


def test_blocked_status_still_invalid():
    assert "blocked" not in ALLOWED_CUSTOMER_STATUSES
