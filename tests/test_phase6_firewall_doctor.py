from mpf.domain.firewall import FirewallPlanMessage
from mpf.services.firewall_doctor_service import build_doctor_report
from mpf.services.firewall_planner_service import build_plan


def _policy(ips_mode: str = "open") -> dict:
    return {"miners": 1, "farms": 1, "maxconn": 100, "rate_per_min": 1000, "burst": 2000, "ips_mode": ips_mode}


def test_clean_plan_verdict_ok() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"id": 1, "customer_key": "c1", "lane": "BTC", "port": 20001, "status": "active", "policy": _policy()}], planner_customer_source="db_readonly", db_customer_input_loaded=True)
    r = build_doctor_report(p).to_dict()
    assert r["final_verdict"] == "OK"
    assert r["safety"]["live_firewall_read"] is False
    assert r["safety"]["live_firewall_write"] is False


def test_warnings_verdict_warn() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"id": 1, "customer_key": "c1", "lane": "BTC", "port": 20001, "status": "active", "policy": _policy()}], planner_customer_source="db_readonly", db_customer_input_loaded=True)
    p.warnings.append(FirewallPlanMessage(code="test_warning", message="x", severity="warning"))
    r = build_doctor_report(p).to_dict()
    assert r["final_verdict"] == "WARN"


def test_errors_verdict_critical() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[{"customer_key": "x", "lane": "LTC", "port": 20001, "status": "active", "policy": _policy()}], planner_customer_source="db_readonly", db_customer_input_loaded=True)
    r = build_doctor_report(p).to_dict()
    assert r["final_verdict"] == "CRITICAL"


def test_config_only_warn_and_counts() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[], planner_customer_source="config_only", db_customer_input_loaded=False)
    r = build_doctor_report(p).to_dict()
    assert r["final_verdict"] == "WARN"
    assert r["counts"]["accounting_coverage"] == 0


def test_backend_exposure_nat_mismatch_duplicate_are_critical() -> None:
    p = build_plan(lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}], customers=[], backend_exposed=True)
    p.errors.append(FirewallPlanMessage(code="nat_target_mismatch", message="x", severity="error"))
    p.errors.append(FirewallPlanMessage(code="duplicate_rule_key", message="x", severity="error"))
    p.finalize()
    r = build_doctor_report(p).to_dict()
    assert r["final_verdict"] == "CRITICAL"


def test_placeholder_nat_and_accounting_counts() -> None:
    p = build_plan(
        lanes=[{"name": "BTC", "enabled": True, "backend_port": 60010}],
        customers=[
            {"id": 1, "customer_key": "a", "lane": "BTC", "port": 20001, "status": "active", "policy": _policy()},
            {"id": 2, "customer_key": "p", "lane": "BTC", "port": 20002, "status": "paused"},
            {"id": 3, "customer_key": "e", "lane": "BTC", "port": 20003, "status": "expired"},
        ],
        planner_customer_source="db_readonly",
        db_customer_input_loaded=True,
    )
    r = build_doctor_report(p).to_dict()
    assert r["counts"]["placeholder_intents"] >= 2
    assert r["counts"]["nat_redirect_intents"] == 1
    assert r["counts"]["accounting_coverage"] == 1
