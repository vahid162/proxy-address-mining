from __future__ import annotations

import json
from pathlib import Path

from mpf import __version__
from mpf.services.phase11_controlled_artifact_reapply_core import (
    PACKAGE_READY,
    CommandResult,
    ControlledBackendTargetResolver,
    build_package_from_plan,
    build_plan,
    classify_controlled_artifacts,
    execute_package,
    render_payload,
)

PHASE = "current_working_phase: Phase 11 operational completion — Full CLI Production Operations"


def container(ip="172.19.0.5", *, project="mpf-proxy", running=True, health="healthy", public_publish=False, cid="abc"):
    return [{
        "Id": cid,
        "Name": "/mpf-forwarder-btc",
        "State": {"Running": running, "Health": {"Status": health}},
        "Config": {"Labels": {"com.docker.compose.project": project}},
        "NetworkSettings": {
            "Ports": {"60010/tcp": ([{"HostIp": "0.0.0.0", "HostPort": "60010"}] if public_publish else None)},
            "Networks": {"mpf-proxy-internal": {"IPAddress": ip, "NetworkID": "net1"}},
        },
    }]


class Runner:
    def __init__(self, inspect):
        self.inspect = inspect
        self.calls = []
    def run(self, argv):
        self.calls.append(argv)
        if argv[:2] == ["docker", "inspect"]:
            return CommandResult(0, json.dumps(self.inspect), "")
        if argv[0] == "ss":
            return CommandResult(0, "State Recv-Q Send-Q Local Address:Port Peer Address:Port\nLISTEN 0 10 127.0.0.1:60010 0.0.0.0:*\n", "")
        if argv[0] == "iptables-restore":
            return CommandResult(0, "", "")
        return CommandResult(1, "", "bad")


class Reach:
    def __init__(self, ok=True): self.ok = ok
    def connect_ok(self, host, port): return self.ok


def target(ip="172.19.0.5", cid="abc"):
    return ControlledBackendTargetResolver(runner=Runner(container(ip, cid=cid)), reachability=Reach(), hostname="farm5").resolve()


def lanes():
    return [{"name": "btc", "enabled": True, "backend_port": 60010}]


def customers(extra=False, status="active", policy=True):
    p = {"miners": 1, "farms": 1, "maxconn": 10, "rate_per_min": 60, "burst": 10, "ips_mode": "any"} if policy else {}
    out = [
        {"id": 1, "customer_key": "canary-btc-001", "lane": "btc", "port": 20001, "status": status, "policy": p},
        {"id": 2, "customer_key": "limited-btc-001", "lane": "btc", "port": 20101, "status": status, "policy": p},
    ]
    if extra:
        out.append({"id": 3, "customer_key": "extra-btc-001", "lane": "btc", "port": 20201, "status": "active", "policy": p})
    return out


def test_backend_resolver_healthy_private_current_target_and_fingerprint():
    report = target()
    assert report["status"] == "ok"
    assert report["resolved_ipv4"] == "172.19.0.5"
    assert report["target_fingerprint"] == target()["target_fingerprint"]
    assert report["mutation_performed"] is False


def test_backend_resolver_blocks_bad_runtime_conditions():
    assert ControlledBackendTargetResolver(runner=Runner(container(running=False)), reachability=Reach(), hostname="farm5").resolve()["status"] == "blocked"
    assert "backend_container_unhealthy" in ControlledBackendTargetResolver(runner=Runner(container(health="unhealthy")), reachability=Reach(), hostname="farm5").resolve()["blockers"]
    assert "backend_container_compose_project_mismatch" in ControlledBackendTargetResolver(runner=Runner(container(project="wrong")), reachability=Reach(), hostname="farm5").resolve()["blockers"]
    assert "backend_target_tcp_unreachable" in ControlledBackendTargetResolver(runner=Runner(container()), reachability=Reach(False), hostname="farm5").resolve()["blockers"]
    assert "backend_docker_publish_public" in ControlledBackendTargetResolver(runner=Runner(container(public_publish=True)), reachability=Reach(), hostname="farm5").resolve()["blockers"]


def test_backend_resolver_blocks_invalid_ip_classes_and_recreation_changes_fingerprint():
    for ip in ["127.0.0.1", "8.8.8.8", "169.254.1.1", "224.0.0.1", "0.0.0.0"]:
        assert ControlledBackendTargetResolver(runner=Runner(container(ip)), reachability=Reach(), hostname="farm5").resolve()["status"] == "blocked"
    assert target(cid="old")["target_fingerprint"] != target(cid="new")["target_fingerprint"]


def test_plan_absent_state_produces_reviewable_dynamic_package_without_historical_ip():
    plan = build_plan(lanes=lanes(), customers=customers(), backend_target=target(), iptables_save_text="", ip6tables_save_text="", phase_status_text=PHASE)
    assert plan["final_decision"] == PACKAGE_READY
    assert "172.18.0.3" not in plan["payload"]
    pkg = build_package_from_plan(plan)
    assert pkg["final_decision"] == PACKAGE_READY
    assert pkg["rollback_plan"]["automatic_rollback_execution_available"] is False
    assert pkg["rollback_plan"]["manual_review_required"] is True


def test_exact_present_no_reapply_and_safe_partial_only_adds_missing():
    plan = build_plan(lanes=lanes(), customers=customers(), backend_target=target(), iptables_save_text="", ip6tables_save_text="", phase_status_text=PHASE)
    present = "\n".join(x.split(":", 1)[1] for x in plan["desired_state"]["artifact_lines"])
    full = build_plan(lanes=lanes(), customers=customers(), backend_target=target(), iptables_save_text=present, phase_status_text=PHASE)
    assert full["final_decision"] == "NO_CONTROLLED_ARTIFACT_REAPPLY_REQUIRED"
    partial_text = "\n".join(present.splitlines()[:2])
    partial = build_plan(lanes=lanes(), customers=customers(), backend_target=target(), iptables_save_text=partial_text, phase_status_text=PHASE)
    assert partial["final_decision"] == PACKAGE_READY
    assert len(partial["artifact_classification"]["exact_missing"]) < len(plan["desired_state"]["artifact_lines"])


def test_stale_duplicate_unknown_ipv6_and_scope_mismatch_block():
    plan = build_plan(lanes=lanes(), customers=customers(), backend_target=target(), phase_status_text=PHASE)
    stale = '-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.3:60010'
    assert "stale_target_detected" in build_plan(lanes=lanes(), customers=customers(), backend_target=target(), iptables_save_text=stale, phase_status_text=PHASE)["blockers"]
    first = plan["desired_state"]["artifact_lines"][0].split(":", 1)[1]
    assert "duplicate_controlled_artifact_detected" in build_plan(lanes=lanes(), customers=customers(), backend_target=target(), iptables_save_text=f"{first}\n{first}\n", phase_status_text=PHASE)["blockers"]
    assert "unknown_mpf_artifacts_detected" in build_plan(lanes=lanes(), customers=customers(), backend_target=target(), iptables_save_text=":MPF_BAD - [0:0]", phase_status_text=PHASE)["blockers"]
    assert "unknown_mpf_artifacts_detected" in classify_controlled_artifacts(iptables_save_text="", ip6tables_save_text=":MPF6 - [0:0]", desired_state=plan["desired_state"])["blockers"]
    assert "third_customer_enters_controlled_reapply_scope" in build_plan(lanes=lanes(), customers=customers(extra=True), backend_target=target(), phase_status_text=PHASE)["blockers"]
    assert "controlled_customer_not_active:canary-btc-001" in build_plan(lanes=lanes(), customers=customers(status="paused"), backend_target=target(), phase_status_text=PHASE)["blockers"]
    assert any(str(b).startswith("controlled_customer_policy_incomplete") for b in build_plan(lanes=lanes(), customers=customers(policy=False), backend_target=target(), phase_status_text=PHASE)["blockers"])


def test_payload_validation_scope_and_no_forbidden_operations():
    payload, _, blockers = render_payload(["nat:-A MPF_NAT_PRE -p tcp --dport 20001 -j DNAT --to-destination 172.19.0.5:60010"])
    assert blockers == []
    assert "--noflush" not in payload
    bad_payload, _, bad = render_payload(["nat:-A MPF_NAT_PRE -p tcp --dport 20001 -j DNAT --to-destination 172.18.0.3:60010"])
    assert "historical_backend_target_forbidden" in bad


def test_executor_guards_drift_ci_test_before_apply_and_metadata_writes(tmp_path, monkeypatch):
    plan = build_plan(lanes=lanes(), customers=customers(), backend_target=target(), phase_status_text=PHASE)
    pkg = build_package_from_plan(plan)
    sha = pkg["package_sha256"]
    assert execute_package(package=pkg, package_sha256=sha, package_id=pkg["package_id"], operator="op", reason="r")["final_decision"] == "FAILED_PRE_APPLY"
    assert "ci_execution_blocked" in execute_package(package=pkg, package_sha256=sha, package_id=pkg["package_id"], operator="op", reason="r", execute=True, yes=True, env={"CI": "1"})["blockers"]
    drift = dict(plan); drift["db_customer_policy_snapshot_hash"] = "drift"
    assert "db_customer_policy_snapshot_drift" in execute_package(package=pkg, package_sha256=sha, package_id=pkg["package_id"], operator="op", reason="r", execute=True, yes=True, env={}, live_plan_builder=lambda: drift)["blockers"]

    class Backup:
        def prepare(self, package, **kwargs): return {"backup_dir": str(tmp_path)}
    class Repo:
        def __init__(self): self.writes=[]
        def record_intent(self,*a): self.writes.append("intent")
        def record_result(self,*a): self.writes.append("result")
    repo=Repo()
    ok = execute_package(package=pkg, package_sha256=sha, package_id=pkg["package_id"], operator="op", reason="r", execute=True, yes=True, env={}, live_plan_builder=lambda: plan, runner=Runner(container()), backup=Backup(), metadata_repo=repo)
    assert ok["final_decision"] == "CONTROLLED_ARTIFACT_REAPPLY_EXECUTED_PENDING_FARM5_EVIDENCE_REVIEW"
    assert repo.writes == ["intent", "result"]


def test_current_artifact_gate_accepts_explicit_dynamic_target_and_blocks_stale_or_unresolved():
    from mpf.services.phase11_current_controlled_artifact_gate_service import build_phase11_current_controlled_artifact_gate_report
    line = '-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.19.0.5:60010'
    phase_text = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")
    ok = build_phase11_current_controlled_artifact_gate_report(iptables_save_text=line, phase_status_text=phase_text, expected_backend_target="172.19.0.5:60010")
    assert ok["final_decision"] == "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS"
    stale = build_phase11_current_controlled_artifact_gate_report(iptables_save_text=line, phase_status_text=phase_text, expected_backend_target="172.19.0.6:60010")
    assert "unknown_mpf_artifacts_detected" in stale["blockers"]
    unresolved = build_phase11_current_controlled_artifact_gate_report(iptables_save_text=line, phase_status_text=phase_text, expected_backend_target=None)
    assert "expected_backend_target_required" in unresolved["blockers"]
