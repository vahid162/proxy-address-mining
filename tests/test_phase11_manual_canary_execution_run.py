from __future__ import annotations

import json

from typer.testing import CliRunner

from mpf import __version__
from mpf.domain.production import ManualCanaryExecutionRunRequest
from mpf.interfaces.cli import app
from mpf.services import phase11_manual_canary_execution_run_service
from mpf.services.phase11_single_canary_host_apply_primitive import SingleCanaryHostApplyPrimitive

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
    def __init__(self, ok=True): self.ok = ok
    def check_readiness(self, report): return {"status": "ok"} if self.ok else {"status": "error", "error": "readiness failed"}


class _FakeRestore:
    def __init__(self, fail_on: str | None = None): self.fail_on = fail_on
    def create_restore_point(self, report): return {"status": "error", "error": "restore failed"} if self.fail_on == "restore" else {"status": "ok", "restore_point": {"id": "rp-1"}}
    def create_iptables_save_backup(self, report): return {"status": "error", "error": "backup failed"} if self.fail_on == "backup" else {"status": "ok", "iptables_save_backup": {"id": "bk-1"}}


class _FakeLock:
    def __init__(self, acquire=True): self.acquire_ok = acquire; self.released = False
    def acquire(self, report): return {"acquired": self.acquire_ok, "error": "lock fail" if not self.acquire_ok else None}
    def release(self, report): self.released = True; return {"released": True}


class _FakeCustomer:
    def __init__(self, status="ok"): self.status = status; self.count = 0
    def ensure_customer(self, report): self.count += 1; return {"status": self.status, "error": "customer failed" if self.status != "ok" else None, "idempotent": self.count > 1}


class _FakeFirewall:
    def __init__(self, build="ok", diff="ok", apply="ok"):
        self.build = build; self.diff = diff; self.apply = apply; self.called = []
    def build_plan(self, report): self.called.append("build"); return {"status": self.build, "error": "build failed" if self.build != "ok" else None}
    def render_diff(self, report): self.called.append("diff"); return {"status": self.diff, "error": "diff failed" if self.diff != "ok" else None}
    def apply_plan(self, report): self.called.append("apply"); return {"status": self.apply, "error": "apply failed" if self.apply != "ok" else None}


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
    def emit_evidence(self, report): return {"status": "ok", "saved": False}


def _adapters(**kwargs):
    return {
        "readiness": kwargs.get("readiness", _FakeReadiness()),
        "restore": kwargs.get("restore", _FakeRestore()),
        "lock": kwargs.get("lock", _FakeLock()),
        "customer": kwargs.get("customer", _FakeCustomer()),
        "firewall": kwargs.get("firewall", _FakeFirewall()),
        "verify": kwargs.get("verify", _FakeVerify()),
        "evidence": kwargs.get("evidence", _FakeEvidence()),
    }


def test_execute_version_validation() -> None:
    assert any("expected_version must be" in e for e in _approved_execute_request("0.1.153").validate(expected_repo_version=__version__))
    assert any("expected_version must be" in e for e in _approved_execute_request("0.1.154").validate(expected_repo_version=__version__))
    assert _approved_execute_request(__version__).validate(expected_repo_version=__version__) == []


def test_plan_mode_safe_flags_false() -> None:
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(ManualCanaryExecutionRunRequest())
    assert r["final_decision"] == "PLAN_READY_FOR_FARM5_SYNC_EVIDENCE"
    assert all(v is False for v in r["safety_flags"].values())


def test_execute_blocked_without_adapters() -> None:
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(_approved_execute_request())
    assert r["final_decision"] == "BLOCKED"
    assert r["execution_allowed"] is False


def test_preflight_fail_keeps_flags_false() -> None:
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(_approved_execute_request(), adapters=_adapters(readiness=_FakeReadiness(ok=False)))
    assert r["final_decision"] == "BLOCKED"
    assert r["execution_allowed"] is False
    assert all(v is False for v in r["safety_flags"].values())


def test_restore_fail_keeps_flags_false() -> None:
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(_approved_execute_request(), adapters=_adapters(restore=_FakeRestore(fail_on="restore")))
    assert r["final_decision"] == "BLOCKED"
    assert all(v is False for v in r["safety_flags"].values())


def test_lock_fail_keeps_flags_false() -> None:
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(_approved_execute_request(), adapters=_adapters(lock=_FakeLock(acquire=False)))
    assert r["final_decision"] == "BLOCKED"
    assert all(v is False for v in r["safety_flags"].values())


def test_customer_failure_stops_before_firewall() -> None:
    fw = _FakeFirewall()
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(_approved_execute_request(), adapters=_adapters(customer=_FakeCustomer(status="error"), firewall=fw))
    assert r["final_decision"] == "EXECUTION_FAILED"
    assert fw.called == []


def test_build_plan_failure_stops_before_diff_apply() -> None:
    fw = _FakeFirewall(build="error")
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(_approved_execute_request(), adapters=_adapters(firewall=fw))
    assert r["final_decision"] == "EXECUTION_FAILED"
    assert fw.called == ["build"]


def test_render_diff_failure_stops_before_apply() -> None:
    fw = _FakeFirewall(diff="error")
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(_approved_execute_request(), adapters=_adapters(firewall=fw))
    assert r["final_decision"] == "EXECUTION_FAILED"
    assert fw.called == ["build", "diff"]


def test_apply_failure_exec_failed_release_lock_and_flags_false() -> None:
    lock = _FakeLock()
    fw = _FakeFirewall(apply="error")
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(_approved_execute_request(), adapters=_adapters(lock=lock, firewall=fw))
    assert r["final_decision"] == "EXECUTION_FAILED"
    assert r["execution_allowed"] is False
    assert lock.released is True
    assert all(v is False for v in r["safety_flags"].values())


def test_missing_adapter_method_returns_structured_failure() -> None:
    class BadCustomer: pass
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(_approved_execute_request(), adapters=_adapters(customer=BadCustomer()))
    assert r["final_decision"] == "EXECUTION_FAILED"
    assert any("adapter method missing" in b for b in r["blockers"])


def test_adapter_exception_returns_structured_failure_and_releases_lock() -> None:
    class ExplosiveFirewall(_FakeFirewall):
        def apply_plan(self, report):
            raise RuntimeError("boom")
    lock = _FakeLock()
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(_approved_execute_request(), adapters=_adapters(lock=lock, firewall=ExplosiveFirewall()))
    assert r["final_decision"] == "EXECUTION_FAILED"
    assert any("adapter call failed" in b for b in r["blockers"])
    assert lock.released is True


def test_execute_success_fake_and_lock_release() -> None:
    lock = _FakeLock()
    r = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(_approved_execute_request(), adapters=_adapters(lock=lock))
    assert r["final_decision"] == "EXECUTION_COMPLETED_PENDING_REVIEW"
    assert r["execution_completed"] is True
    assert lock.released is True
    assert r["customer_db_mutation_performed"] is False


def test_cli_plan_json() -> None:
    result = RUNNER.invoke(app, ["production", "manual-canary-execute", "--output", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["component"] == "phase11_manual_canary_execution_run"
    assert payload["adapter_mode"] == "production_service_layer"


def test_cli_execute_uses_production_adapters_and_blocks_on_missing_real_apply() -> None:
    args = [
        "production", "manual-canary-execute", "--requested-action", "execute",
        "--customer-key", "canary-btc-001", "--lane", "btc", "--port", "20001",
        "--miners", "1", "--farms", "1", "--maxconn", "1",
        "--expected-version", __version__,
        "--operator-confirmed",
        "--i-understand-this-can-create-a-canary-customer",
        "--i-understand-this-can-apply-firewall",
        "--i-have-reviewed-rollback",
        "--i-have-fresh-farm5-sync",
        "--operator", "tester",
        "--reason", "test",
        "--output", "json",
    ]
    result = RUNNER.invoke(app, args)
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["adapter_mode"] == "production_service_layer"
    assert payload["real_adapters_wired"] is True
    assert payload["final_decision"] == "BLOCKED"
    assert "single_canary_restore_backup_context_not_confirmed" in payload["blockers"]
    assert all(v is False for v in payload["safety_flags"].values())


def test_single_canary_primitive_blocks_without_real_apply_executor(monkeypatch) -> None:
    primitive = SingleCanaryHostApplyPrimitive()
    report = {
        "scope": {"single_canary_only": True},
        "request": _approved_execute_request().as_dict(),
        "preflight_results": {"phase_gate": "OK", "mpf_doctor": "OK", "db_status": "OK", "proxy_doctor": "OK", "no_customer_nat_baseline": "OK", "no_customer_firewall_baseline": "OK", "local_only_runtime_baseline": "OK"},
        "restore_point": {"id": "rp-1"},
        "iptables_save_backup": {"id": "bk-1"},
        "lock": {"acquired": True},
        "firewall_diff": {"json_diff": {"customer_port": 20001, "backend_port": 60010}},
        "firewall_plan": {"restore_payload": "*nat\n-A MPF_NAT_PRE -p tcp --dport 20001 -j DNAT --to-destination 172.18.0.3:60010\nCOMMIT\n"},
    }
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY_EXECUTE", "allow")
    monkeypatch.delenv("CI", raising=False)
    out = primitive.execute(report)
    assert out["status"] == "blocked"
    assert out["error"] == "accepted_single_canary_host_apply_execution_missing"


def test_single_canary_primitive_blocks_without_verifier(monkeypatch) -> None:
    def _ok_apply(report, payload):
        return {"status": "ok", "applied": True}
    primitive = SingleCanaryHostApplyPrimitive(host_apply_executor=_ok_apply, post_apply_verifier=None)
    report = {
        "scope": {"single_canary_only": True},
        "request": _approved_execute_request().as_dict(),
        "preflight_results": {"phase_gate": "OK", "mpf_doctor": "OK", "db_status": "OK", "proxy_doctor": "OK", "no_customer_nat_baseline": "OK", "no_customer_firewall_baseline": "OK", "local_only_runtime_baseline": "OK"},
        "restore_point": {"id": "rp-1"},
        "iptables_save_backup": {"id": "bk-1"},
        "lock": {"acquired": True},
        "firewall_diff": {"json_diff": {"customer_port": 20001, "backend_port": 60010}},
        "firewall_plan": {"restore_payload": "*nat\n-A MPF_NAT_PRE -p tcp --dport 20001 -j DNAT --to-destination 172.18.0.3:60010\nCOMMIT\n"},
    }
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY_EXECUTE", "allow")
    monkeypatch.delenv("CI", raising=False)
    out = primitive.execute(report)
    assert out["status"] == "blocked"
    assert out["error"] == "single_canary_post_apply_verification_missing"




class _RestoreOKNoIptables:
    def create_restore_point(self, report):
        return {"status": "ok", "restore_point": {"id": "rp-test", "mode": "single_canary_restore_backup_boundary"}}

    def create_iptables_save_backup(self, report):
        return {"status": "ok", "iptables_save_backup": {"id": "bk-test", "mode": "single_canary_restore_backup_boundary", "path": "/tmp/mock", "sha256": "abc"}}




def _patch_resolver_ok(monkeypatch) -> None:
    monkeypatch.setattr(
        "mpf.services.phase11_single_canary_backend_target_resolver.Phase11SingleCanaryBackendTargetResolver.resolve",
        lambda self, report: {"status": "ok", "target_host": "172.18.0.3", "target_port": 60010, "target_kind": "docker_container_ipv4"},
    )



def _patch_nat_hook_ready(monkeypatch) -> None:
    from subprocess import CompletedProcess

    def fake_run(self, argv, **kwargs):
        return CompletedProcess(argv, 0, "*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\nCOMMIT\n", "")

    monkeypatch.setattr(
        "mpf.services.phase11_single_canary_nat_hook_bootstrap.Phase11SingleCanaryNatHookBootstrapService._run",
        fake_run,
    )
def _production_like_adapters_without_iptables_save():
    from mpf.services.phase11_manual_canary_execution_adapters import build_manual_canary_production_adapters

    adapters = build_manual_canary_production_adapters()
    adapters["restore"] = _RestoreOKNoIptables()
    return adapters


def test_execute_restore_guard_path_renderer_ok_then_host_apply_context_blocked(monkeypatch) -> None:
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "allow")
    monkeypatch.delenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY", raising=False)
    monkeypatch.delenv("CI", raising=False)
    _patch_resolver_ok(monkeypatch)
    _patch_nat_hook_ready(monkeypatch)
    _patch_nat_hook_ready(monkeypatch)
    report = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(
        _approved_execute_request(), adapters=_production_like_adapters_without_iptables_save()
    )
    assert report["final_decision"] == "BLOCKED"
    assert "single_canary_host_apply_context_not_confirmed" in report["blockers"]
    assert report["restore_payload_renderer"]["status"] == "ok"
    payload = report["restore_payload_renderer"]["restore_payload"]
    assert "*filter" in payload
    assert ":MPFC_20001 - [0:0]" in payload
    assert "mpf:canary-btc-001:customer_connlimit_reject" in payload
    assert "mpf:canary-btc-001:customer_hashlimit_reject" in payload
    assert report["mutation_performed"] is False
    assert report["customer_db_mutation_performed"] is False
    assert report["firewall_mutation_performed"] is False
    assert report["nat_mutation_performed"] is False
    assert report["production_traffic_enabled"] is False
    assert all(v is False for v in report["safety_flags"].values())


def test_execute_both_guards_renderer_ok_then_missing_host_apply_executor_blocked(monkeypatch) -> None:
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY", "allow")
    monkeypatch.delenv("CI", raising=False)
    _patch_resolver_ok(monkeypatch)
    _patch_nat_hook_ready(monkeypatch)
    report = phase11_manual_canary_execution_run_service.build_phase11_manual_canary_execution_run_report(
        _approved_execute_request(), adapters=_production_like_adapters_without_iptables_save()
    )
    assert report["final_decision"] == "BLOCKED"
    assert "single_canary_host_apply_execution_not_confirmed" in report["blockers"]
    assert report["mutation_performed"] is False
    assert report["customer_db_mutation_performed"] is False
    assert report["firewall_mutation_performed"] is False
    assert report["nat_mutation_performed"] is False
    assert report["production_traffic_enabled"] is False
    assert all(v is False for v in report["safety_flags"].values())
