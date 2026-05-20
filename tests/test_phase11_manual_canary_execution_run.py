from __future__ import annotations

import json

from typer.testing import CliRunner

from mpf import __version__
from mpf.domain.production import ManualCanaryExecutionRunRequest
from mpf.interfaces.cli import app
from mpf.services import phase11_manual_canary_execution_run_service

RUNNER = CliRunner()


def _approved_execute_request(version: str | None = None) -> ManualCanaryExecutionRunRequest:
    return ManualCanaryExecutionRunRequest(
        requested_action="execute",
        expected_version=version or __version__,
        operator_confirmed=True,
        understand_canary_customer=True,
        understand_firewall_apply=True,
        reviewed_rollback=True,
        fresh_farm5_sync_confirmed=True,
    )


class _FakeReadiness:
    def check_readiness(self, report):
        return {"status": "ok"}


class _FakeRestore:
    def create_restore_point(self, report):
        return {"status": "ok", "restore_point": {"id": "rp-1"}}

    def create_iptables_save_backup(self, report):
        return {"status": "ok", "iptables_save_backup": {"id": "bk-1"}}


class _FakeLock:
    def __init__(self):
        self.released = False

    def acquire(self, report):
        return {"acquired": True}

    def release(self, report):
        self.released = True
        return {"released": True}


class _FakeCustomer:
    def __init__(self):
        self.count = 0

    def ensure_customer(self, report):
        self.count += 1
        return {"status": "ok", "idempotent": self.count > 1}


class _FakeFirewall:
    def build_plan(self, report):
        return {"status": "ok", "plan_id": "p1"}

    def render_diff(self, report):
        return {"status": "ok", "human": "diff", "json": {}}

    def apply_plan(self, report):
        return {"status": "ok"}


class _FakeVerify:
    def verify_post_apply(self, report): return {"status": "ok"}
    def verify_canary_connection(self, report): return {"status": "instruction_required"}
    def verify_nat_hit(self, report): return {"status": "ok"}
    def verify_usage(self, report): return {"status": "ok"}
    def verify_reject(self, report): return {"status": "ok"}
    def verify_session_worker(self, report): return {"status": "ok"}
    def verify_abuse_coverage(self, report): return {"status": "ok"}
    def rollback_readiness(self, report): return {"status": "ok"}


class _FakeEvidence:
    def emit_evidence(self, report):
        return {"status": "ok", "saved": False}


def _adapters(lock=None, customer=None):
    return {"readiness": _FakeReadiness(), "restore": _FakeRestore(), "lock": lock or _FakeLock(), "customer": customer or _FakeCustomer(), "firewall": _FakeFirewall(), "verify": _FakeVerify(), "evidence": _FakeEvidence()}


def test_dto_defaults_validate_plan() -> None:
    assert ManualCanaryExecutionRunRequest().validate() == []


def test_execute_version_validation() -> None:
    assert any("expected_version must be" in e for e in _approved_execute_request("0.1.153").validate(expected_repo_version=__version__))
    assert any("expected_version must be" in e for e in _approved_execute_request("0.1.154").validate(expected_repo_version=__version__))
    assert _approved_execute_request(__version__).validate(expected_repo_version=__version__) == []


def test_plan_mode_safe_flags_false() -> None:
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(ManualCanaryExecutionRunRequest())
    assert r["final_decision"] == "PLAN_READY_FOR_FARM5_SYNC_EVIDENCE"
    assert r["mutation_performed"] is False
    assert all(v is False for v in r["safety_flags"].values())


def test_execute_blocked_without_adapters() -> None:
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(_approved_execute_request())
    assert r["final_decision"] == "BLOCKED"


def test_execute_success_fake_and_lock_release() -> None:
    lock = _FakeLock()
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(_approved_execute_request(), adapters=_adapters(lock=lock))
    assert r["final_decision"] == "EXECUTION_COMPLETED_PENDING_REVIEW"
    assert lock.released is True


def test_wrong_scope_blocked() -> None:
    assert phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(ManualCanaryExecutionRunRequest(requested_action="execute", lane="zec"))["final_decision"] == "BLOCKED"
    assert phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(ManualCanaryExecutionRunRequest(requested_action="execute", port=20002))["final_decision"] == "BLOCKED"
    assert phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(ManualCanaryExecutionRunRequest(requested_action="execute", customer_key="bad"))["final_decision"] == "BLOCKED"


def test_cli_plan_json() -> None:
    result = RUNNER.invoke(app, ["production", "manual-canary-execute", "--output", "json"])
    assert result.exit_code == 0
    assert json.loads(result.output)["component"] == "phase11_manual_canary_execution_run"
