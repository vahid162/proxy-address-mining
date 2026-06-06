from __future__ import annotations

import json
from pathlib import Path

from mpf import __version__
from mpf.services.phase11_controlled_artifact_reapply_core import (
    PACKAGE_BLOCKED,
    PACKAGE_READY,
    CommandResult,
    ControlledBackendTargetResolver,
    FileBackupAdapter,
    _canonical_sha,
    _package_content_for_hash,
    _text_sha,
    build_package_from_plan,
    build_plan,
    classify_controlled_artifacts,
    execute_package,
    render_payload,
)

PHASE = Path("docs/PHASE_STATUS.md").read_text(encoding="utf-8")


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
    production_ready = False
    def __init__(self, inspect, *, ss_stdout="State Recv-Q Send-Q Local Address:Port Peer Address:Port\nLISTEN 0 10 127.0.0.1:60010 0.0.0.0:*\n"):
        self.inspect = inspect
        self.ss_stdout = ss_stdout
        self.calls = []
    def run(self, argv, input_text=None):
        self.calls.append(argv)
        if argv[:2] == ["docker", "inspect"]:
            return CommandResult(0, json.dumps(self.inspect), "")
        if argv[0] == "ss":
            return CommandResult(0, self.ss_stdout, "")
        if argv[0] == "iptables-restore":
            return CommandResult(0, "", "")
        return CommandResult(1, "", "bad")


class Reach:
    def __init__(self, ok=True): self.ok = ok
    def connect_ok(self, host, port): return self.ok


def target(ip="172.19.0.5", cid="abc", *, ss_stdout=None):
    runner = Runner(container(ip, cid=cid), ss_stdout=ss_stdout) if ss_stdout is not None else Runner(container(ip, cid=cid))
    return ControlledBackendTargetResolver(runner=runner, reachability=Reach(), hostname="farm5").resolve()


def lanes(extra_collision=False):
    out = [{"name": "btc", "enabled": True, "backend_port": 60010}]
    if extra_collision:
        out.append({"name": "zec", "enabled": True, "backend_port": 60010})
    return out


def customers(extra=False, status="active", policy=True, whitelist=False):
    p = {"miners": 1, "farms": 1, "maxconn": 10, "rate_per_min": 60, "burst": 10, "ips_mode": "whitelist" if whitelist else "any"} if policy else {}
    out = [
        {"id": 1, "customer_key": "canary-btc-001", "lane": "btc", "port": 20001, "status": status, "policy": p, "ip_whitelist": ["203.0.113.10"] if whitelist else []},
        {"id": 2, "customer_key": "limited-btc-001", "lane": "btc", "port": 20101, "status": status, "policy": p, "ip_whitelist": ["203.0.113.11"] if whitelist else []},
    ]
    if extra:
        out.append({"id": 3, "customer_key": "extra-btc-001", "lane": "btc", "port": 20201, "status": "active", "policy": p})
    return out


def readyish_package():
    plan = build_plan(lanes=lanes(), customers=customers(), backend_target=target(), phase_status_text=PHASE)
    pkg = build_package_from_plan(plan)
    pkg.update({
        "final_decision": PACKAGE_READY,
        "hostname": __import__("socket").gethostname(),
        "payload": "*filter\nCOMMIT\n",
        "payload_sha256": _text_sha("*filter\nCOMMIT\n"),
        "rollback_plan": {"manual_review_required": True, "automatic_rollback_execution_available": False, "exact_inverse_delta": []},
    })
    pkg["package_sha256"] = _canonical_sha(_package_content_for_hash(pkg))
    pkg["__package_file_sha256"] = "file-sha"
    return pkg


def test_backend_resolver_healthy_private_current_target_and_fingerprint():
    report = target()
    assert report["status"] == "ok"
    assert report["resolved_ipv4"] == "172.19.0.5"
    assert report["target_fingerprint"] == target()["target_fingerprint"]
    assert report["mutation_performed"] is False


def test_backend_resolver_blocks_bad_runtime_conditions_and_missing_listener():
    assert ControlledBackendTargetResolver(runner=Runner(container(running=False)), reachability=Reach(), hostname="farm5").resolve()["status"] == "blocked"
    assert "backend_container_unhealthy" in ControlledBackendTargetResolver(runner=Runner(container(health="unhealthy")), reachability=Reach(), hostname="farm5").resolve()["blockers"]
    assert "backend_container_compose_project_mismatch" in ControlledBackendTargetResolver(runner=Runner(container(project="wrong")), reachability=Reach(), hostname="farm5").resolve()["blockers"]
    assert "backend_target_tcp_unreachable" in ControlledBackendTargetResolver(runner=Runner(container()), reachability=Reach(False), hostname="farm5").resolve()["blockers"]
    assert "backend_docker_publish_public" in ControlledBackendTargetResolver(runner=Runner(container(public_publish=True)), reachability=Reach(), hostname="farm5").resolve()["blockers"]
    missing = ControlledBackendTargetResolver(runner=Runner(container(), ss_stdout="State Recv-Q Send-Q Local Address:Port Peer Address:Port\n"), reachability=Reach(), hostname="farm5").resolve()
    assert "backend_host_listener_missing_or_not_local_only" in missing["blockers"]


def test_backend_resolver_blocks_invalid_ip_classes_and_recreation_changes_fingerprint():
    for ip in ["127.0.0.1", "8.8.8.8", "169.254.1.1", "224.0.0.1", "0.0.0.0"]:
        assert ControlledBackendTargetResolver(runner=Runner(container(ip)), reachability=Reach(), hostname="farm5").resolve()["status"] == "blocked"
    assert target(cid="old")["target_fingerprint"] != target(cid="new")["target_fingerprint"]


def test_plan_fails_closed_until_policy_artifact_semantics_are_resolved():
    plan = build_plan(lanes=lanes(), customers=customers(), backend_target=target(), iptables_save_text="", ip6tables_save_text="", phase_status_text=PHASE)
    assert plan["final_decision"] == PACKAGE_BLOCKED
    assert "controlled_policy_artifact_semantics_unresolved" in plan["blockers"]
    pkg = build_package_from_plan(plan)
    assert pkg["final_decision"] == PACKAGE_BLOCKED


def test_strict_phase_gate_and_scope_policy_collisions_block():
    assert any(str(b).startswith("phase_gate_missing:") for b in build_plan(lanes=lanes(), customers=customers(), backend_target=target(), phase_status_text="current_working_phase: Phase 11 operational completion — Full CLI Production Operations")["blockers"])
    assert "third_customer_enters_controlled_reapply_scope" in build_plan(lanes=lanes(), customers=customers(extra=True), backend_target=target(), phase_status_text=PHASE)["blockers"]
    assert "controlled_customer_not_active:canary-btc-001" in build_plan(lanes=lanes(), customers=customers(status="paused"), backend_target=target(), phase_status_text=PHASE)["blockers"]
    assert any(str(b).startswith("controlled_customer_policy_incomplete") for b in build_plan(lanes=lanes(), customers=customers(policy=False), backend_target=target(), phase_status_text=PHASE)["blockers"])
    assert any(str(b).startswith("planner_error:lane_backend_collision") for b in build_plan(lanes=lanes(extra_collision=True), customers=customers(), backend_target=target(), phase_status_text=PHASE)["blockers"])


def test_strict_classifier_blocks_unknown_known_customer_rule_stale_duplicate_ipv6():
    plan = build_plan(lanes=lanes(), customers=customers(), backend_target=target(), phase_status_text=PHASE)
    desired = plan["desired_state"]
    stale = '-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.3:60010'
    assert "stale_target_detected" in classify_controlled_artifacts(iptables_save_text=stale, ip6tables_save_text="", desired_state=desired)["blockers"]
    unknown_known_customer = '-A MPFC_20001 -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:unexpected" -j ACCEPT'
    assert "unknown_mpf_artifacts_detected" in classify_controlled_artifacts(iptables_save_text=unknown_known_customer, ip6tables_save_text="", desired_state=desired)["blockers"]
    first = desired["artifact_lines"][0].split(":", 1)[1]
    assert "duplicate_controlled_artifact_detected" in classify_controlled_artifacts(iptables_save_text=f"{first}\n{first}\n", ip6tables_save_text="", desired_state=desired)["blockers"]
    assert "unknown_mpf_artifacts_detected" in classify_controlled_artifacts(iptables_save_text="", ip6tables_save_text=":MPF6 - [0:0]", desired_state=desired)["blockers"]


def test_payload_validation_blocks_historical_target_and_forbidden_operations():
    _, _, bad = render_payload(["nat:-A MPF_NAT_PRE -F"])
    assert "payload_forbidden_operation_detected" in bad
    _, _, hist = render_payload(["nat:-A MPF_NAT_PRE -p tcp --dport 20001 -j DNAT --to-destination 172.18.0.3:60010"])
    assert "historical_backend_target_forbidden" in hist


def test_executor_blocks_without_real_production_adapters_and_never_invokes_restore():
    pkg = readyish_package()
    runner = Runner(container())
    result = execute_package(package=pkg, package_sha256="file-sha", package_id=pkg["package_id"], operator="op", reason="r", execute=True, yes=True, env={}, runner=runner)
    assert "live_plan_builder_required" in result["blockers"]
    assert "real_host_lock_required" in result["blockers"]
    assert result["iptables_restore_invoked"] is False
    assert not any(call and call[0] == "iptables-restore" for call in runner.calls)


def test_executor_strict_hash_blocks_tampered_payload_with_preserved_embedded_hash():
    pkg = readyish_package()
    original_hash = pkg["package_sha256"]
    pkg["payload"] = "*filter\n-A MPFC_20001 -j ACCEPT\nCOMMIT\n"
    pkg["payload_sha256"] = _text_sha(str(pkg["payload"]))
    pkg["package_sha256"] = original_hash
    runner = Runner(container())
    result = execute_package(package=pkg, package_sha256="file-sha", package_id=pkg["package_id"], operator="op", reason="r", execute=True, yes=True, env={}, runner=runner)
    assert "package_canonical_sha256_mismatch" in result["blockers"]
    assert result["iptables_restore_invoked"] is False
    assert not any(call and call[0] == "iptables-restore" for call in runner.calls)


def test_executor_rejects_arbitrary_blocked_no_reapply_wrong_scope_and_hostname_packages():
    arbitrary = {"component": "bad", "package_id": "x", "repository_version": __version__, "final_decision": PACKAGE_READY, "scope": [], "payload": "x", "payload_sha256": _text_sha("x"), "rollback_plan": {}}
    arbitrary["package_sha256"] = _canonical_sha(_package_content_for_hash(arbitrary))
    arbitrary["__package_file_sha256"] = "sha"
    assert "package_type_mismatch" in execute_package(package=arbitrary, package_sha256="sha", package_id="x", operator="op", reason="r", execute=True, yes=True, env={})["blockers"]
    for decision, blocker in [(PACKAGE_BLOCKED, "blocked_package_cannot_execute"), ("NO_CONTROLLED_ARTIFACT_REAPPLY_REQUIRED", "no_reapply_package_cannot_execute")]:
        pkg = readyish_package(); pkg["final_decision"] = decision; pkg["package_sha256"] = _canonical_sha(_package_content_for_hash(pkg))
        assert blocker in execute_package(package=pkg, package_sha256="file-sha", package_id=pkg["package_id"], operator="op", reason="r", execute=True, yes=True, env={})["blockers"]
    pkg = readyish_package(); pkg["scope"] = [{"customer_key": "evil", "lane": "btc", "public_port": 1}]; pkg["package_sha256"] = _canonical_sha(_package_content_for_hash(pkg))
    assert "package_scope_mismatch" in execute_package(package=pkg, package_sha256="file-sha", package_id=pkg["package_id"], operator="op", reason="r", execute=True, yes=True, env={})["blockers"]
    pkg = readyish_package(); pkg["hostname"] = "wrong"; pkg["package_sha256"] = _canonical_sha(_package_content_for_hash(pkg))
    assert "package_hostname_mismatch" in execute_package(package=pkg, package_sha256="file-sha", package_id=pkg["package_id"], operator="op", reason="r", execute=True, yes=True, env={})["blockers"]


def test_empty_backup_snapshot_and_audit_unavailable_block_before_apply(tmp_path):
    pkg = readyish_package()
    try:
        FileBackupAdapter(tmp_path).prepare(pkg, iptables_save="", ip6tables_save="")
    except RuntimeError as exc:
        assert "empty_firewall_backup_snapshot_forbidden" in str(exc)
    else:
        raise AssertionError("empty backup snapshot should block")
    result = execute_package(package=pkg, package_sha256="file-sha", package_id=pkg["package_id"], operator="op", reason="r", execute=True, yes=True, env={}, live_plan_builder=lambda: {}, lock=object(), backup=object(), metadata_repo=None)
    assert "real_postgresql_operational_metadata_repo_required" in result["blockers"]


def test_whitelist_and_policy_values_remain_source_backed_but_semantics_block_ready():
    plan = build_plan(lanes=lanes(), customers=customers(whitelist=True), backend_target=target(), phase_status_text=PHASE)
    planner_customers = plan["desired_state"]["planner"]["rules"]
    assert any(rule.get("rule_kind") == "customer_whitelist_allow" for rule in planner_customers)
    assert "controlled_policy_artifact_semantics_unresolved" in plan["blockers"]


def test_current_artifact_gate_requires_explicit_target_and_blocks_stale_default():
    from mpf.services.phase11_current_controlled_artifact_gate_service import build_phase11_current_controlled_artifact_gate_report
    line = '-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.19.0.5:60010'
    ok = build_phase11_current_controlled_artifact_gate_report(iptables_save_text=line, phase_status_text=PHASE, expected_backend_target="172.19.0.5:60010")
    assert ok["final_decision"] == "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS"
    implicit = build_phase11_current_controlled_artifact_gate_report(iptables_save_text=line, phase_status_text=PHASE)
    assert "expected_backend_target_required" in implicit["blockers"]
    stale = build_phase11_current_controlled_artifact_gate_report(iptables_save_text=line, phase_status_text=PHASE, expected_backend_target="172.19.0.6:60010")
    assert "unknown_mpf_artifacts_detected" in stale["blockers"]
