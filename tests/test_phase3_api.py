from __future__ import annotations

from pathlib import Path

from mpf.domain.taxonomy import ActorType, RequestContext
from mpf.repositories.customer_repo import CustomerRecord
from mpf.repositories.job_repo import JobRunRecord
from mpf.repositories.lane_repo import LaneRecord
from mpf.services.db_service import DatabaseStatus

CONFIG_PATH = Path("configs/mpf.example.yaml")


def test_api_db_status_uses_service_and_stable_response(monkeypatch) -> None:
    from mpf.interfaces import api

    monkeypatch.setattr(
        api.db_service,
        "status",
        lambda config: DatabaseStatus(
            ok=True,
            message="OK",
            alembic_version="0001_phase2_initial_schema",
            public_table_count=64,
            lanes=0,
            customers=0,
            job_runs=0,
            firewall_applies=0,
            abuse_states=0,
        ),
    )
    context = RequestContext(correlation_id="corr-db", actor_type=ActorType.INTERNAL_API)
    response = api.get_db_status(CONFIG_PATH, context=context)
    assert response["ok"] is True
    assert response["message"] == "OK"
    assert response["correlation_id"] == "corr-db"
    assert response["data"]["public_table_count"] == 64


def test_api_lanes_uses_service_and_serializes_dto(monkeypatch) -> None:
    from mpf.interfaces import api

    class FakeLaneList:
        ok = True
        message = "OK"
        lanes = [LaneRecord("btc", True, 60010, "MPFBTC", "stratum", "db")]

    monkeypatch.setattr(api.lane_service, "list_lane_status", lambda config: FakeLaneList())
    response = api.list_lanes(CONFIG_PATH, context=RequestContext(correlation_id="corr-lane"))
    assert response["correlation_id"] == "corr-lane"
    assert response["data"]["lanes"][0]["name"] == "btc"
    assert response["data"]["lanes"][0]["backend_port"] == 60010


def test_api_customers_uses_read_service(monkeypatch) -> None:
    from mpf.interfaces import api

    class FakeCustomerList:
        ok = True
        message = "OK"
        customers = [CustomerRecord(1, "btc", "alice", 23138, "active", None)]

    monkeypatch.setattr(api.customer_read_service, "list_customer_status", lambda config, limit=100: FakeCustomerList())
    response = api.list_customers(CONFIG_PATH, limit=100, context=RequestContext(correlation_id="corr-customer"))
    assert response["correlation_id"] == "corr-customer"
    assert response["data"]["customers"][0]["name"] == "alice"
    assert response["data"]["customers"][0]["port"] == 23138


def test_api_jobs_uses_job_service(monkeypatch) -> None:
    from mpf.interfaces import api

    class FakeJobList:
        ok = True
        message = "OK"
        jobs = [JobRunRecord(1, "phase3_check", "succeeded", "2026-05-07", None, 12)]

    monkeypatch.setattr(api.job_service, "list_job_status", lambda config, limit=20: FakeJobList())
    response = api.list_jobs(CONFIG_PATH, limit=20, context=RequestContext(correlation_id="corr-job"))
    assert response["correlation_id"] == "corr-job"
    assert response["data"]["jobs"][0]["job_name"] == "phase3_check"
    assert response["data"]["jobs"][0]["status"] == "succeeded"
