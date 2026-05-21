from __future__ import annotations

from subprocess import CompletedProcess

from mpf import __version__
from mpf.domain.production import ManualCanaryExecutionRunRequest
from mpf.services.phase11_manual_canary_execution_adapters import _FirewallAdapter
from mpf.services.phase11_manual_canary_execution_run_service import build_phase11_manual_canary_execution_run_report
from mpf.services.phase11_single_canary_nat_hook_bootstrap import Phase11SingleCanaryNatHookBootstrapService


def _approved_request() -> ManualCanaryExecutionRunRequest:
    return ManualCanaryExecutionRunRequest(
        requested_action="execute",
        expected_version=__version__,
        operator_confirmed=True,
        understand_canary_customer=True,
        understand_firewall_apply=True,
        reviewed_rollback=True,
        fresh_farm5_sync_confirmed=True,
    )


def _bootstrap_report() -> dict[str, object]:
    return {
        "scope": {"single_canary_only": True},
        "request": _approved_request().as_dict(),
        "preflight_results": {
            "phase_gate": "OK",
            "mpf_doctor": "OK",
            "db_status": "OK",
            "proxy_doctor": "OK",
            "no_customer_nat_baseline": "OK",
            "no_customer_firewall_baseline": "OK",
            "local_only_runtime_baseline": "OK",
        },
        "restore_point": {"id": "rp-1"},
        "iptables_save_backup": {"id": "bk-1"},
        "lock": {"acquired": True},
        "firewall_diff": {"json_diff": {"customer_port": 20001, "backend_port": 60010}},
    }


def _cp(stdout: str = "", returncode: int = 0) -> CompletedProcess[str]:
    return CompletedProcess(["iptables-save"], returncode, stdout, "")


def test_nat_hook_bootstrap_reports_needs_bootstrap_without_guard(monkeypatch) -> None:
    def fake_run(self, argv, **kwargs):
        return _cp("*nat\n-A DOCKER -p tcp -m tcp --dport 60010 -j DNAT --to-destination 127.0.0.1:60010\nCOMMIT\n")

    monkeypatch.setattr(Phase11SingleCanaryNatHookBootstrapService, "_run", fake_run)
    monkeypatch.delenv("MPF_PHASE11_SINGLE_CANARY_NAT_HOOK_BOOTSTRAP", raising=False)
    result = Phase11SingleCanaryNatHookBootstrapService().run(_bootstrap_report())
    assert result["status"] == "ok"
    assert result["action"] == "needs_bootstrap"
    assert result["mutation_performed"] is False
    assert result["docker_local_publish_seen"] is True


def test_nat_hook_bootstrap_blocks_duplicate_hook(monkeypatch) -> None:
    def fake_run(self, argv, **kwargs):
        return _cp("*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\n-A PREROUTING -j MPF_NAT_PRE\nCOMMIT\n")

    monkeypatch.setattr(Phase11SingleCanaryNatHookBootstrapService, "_run", fake_run)
    result = Phase11SingleCanaryNatHookBootstrapService().run(_bootstrap_report())
    assert result["status"] == "blocked"
    assert result["error"] == "duplicate_nat_hook_detected"


def test_nat_hook_bootstrap_payload_is_chain_hook_only() -> None:
    service = Phase11SingleCanaryNatHookBootstrapService()
    analysis = service._analyze("*nat\n-A DOCKER -p tcp -m tcp --dport 60010 -j DNAT --to-destination 127.0.0.1:60010\nCOMMIT\n")
    payload = service._render_bootstrap_payload(analysis)
    assert ":MPF_NAT_PRE" in payload
    assert "-A PREROUTING -j MPF_NAT_PRE" in payload
    assert "--dport 20001" not in payload
    assert "--to-destination" not in payload
    assert "DOCKER" not in payload
    assert "-F" not in payload
    assert service._validate_bootstrap_payload(payload) is True


def test_firewall_adapter_does_not_override_needs_bootstrap_status(monkeypatch) -> None:
    class NeedsBootstrap:
        def run(self, report):
            return {"status": "ok", "action": "needs_bootstrap", "mutation_performed": False, "production_traffic_enabled": False}

    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_NAT_HOOK_BOOTSTRAP", "allow")
    out = _FirewallAdapter(nat_hook_bootstrap=NeedsBootstrap()).apply_plan(_bootstrap_report())
    assert out["status"] == "blocked"
    assert out["error"] == "single_canary_nat_hook_bootstrap_required"
    assert out["action"] == "needs_bootstrap"
    assert out["mutation_performed"] is False


class _ReadinessOK:
    def check_readiness(self, report):
        return {"status": "ok"}


class _RestoreOK:
    def create_restore_point(self, report):
        return {"status": "ok", "restore_point": {"id": "rp-1"}}

    def create_iptables_save_backup(self, report):
        return {"status": "ok", "iptables_save_backup": {"id": "bk-1"}}


class _LockOK:
    def __init__(self):
        self.released = False

    def acquire(self, report):
        return {"acquired": True}

    def release(self, report):
        self.released = True
        return {"released": True}


class _CustomerOK:
    def ensure_customer(self, report):
        return {"status": "ok", "idempotent": True}


class _BootstrapOnlyFirewall:
    def build_plan(self, report):
        return {"status": "ok"}

    def render_diff(self, report):
        return {"status": "ok", "json_diff": {"customer_port": 20001, "backend_port": 60010}}

    def apply_plan(self, report):
        return {
            "status": "ok",
            "bootstrap_completed": True,
            "applied": False,
            "iptables_restore_used": True,
            "mutation_performed": True,
            "firewall_mutation_performed": True,
            "nat_mutation_performed": True,
            "production_traffic_enabled": False,
            "pre_bootstrap_nat_sha256": "before",
            "post_bootstrap_nat_sha256": "after",
        }


class _VerifyShouldNotRun:
    def verify_post_apply(self, report):
        raise AssertionError("bootstrap-only path must stop before final canary verification")


class _EvidenceShouldNotRun:
    def emit_evidence(self, report):
        raise AssertionError("bootstrap-only path must stop before final canary evidence emission")


def test_bootstrap_completed_is_terminal_and_not_actual_canary_execution() -> None:
    lock = _LockOK()
    report = build_phase11_manual_canary_execution_run_report(
        _approved_request(),
        adapters={
            "readiness": _ReadinessOK(),
            "restore": _RestoreOK(),
            "lock": lock,
            "customer": _CustomerOK(),
            "firewall": _BootstrapOnlyFirewall(),
            "verify": _VerifyShouldNotRun(),
            "evidence": _EvidenceShouldNotRun(),
        },
    )
    assert report["final_decision"] == "BOOTSTRAP_COMPLETED_PENDING_REVIEW"
    assert report["actual_canary_execution_performed"] is False
    assert report["production_traffic_enabled"] is False
    assert report["mutation_performed"] is True
    assert report["firewall_mutation_performed"] is True
    assert report["nat_mutation_performed"] is True
    assert report["safety_flags"]["production_traffic_authorized"] is False
    assert report["safety_flags"]["customer_nat_apply_authorized"] is False
    assert lock.released is True
