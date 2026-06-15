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


def target(ip="172.19.0.5", cid="abc", *, ss_stdout=None, filter_proven=True):
    runner = Runner(container(ip, cid=cid), ss_stdout=ss_stdout) if ss_stdout is not None else Runner(container(ip, cid=cid))
    report = ControlledBackendTargetResolver(runner=runner, reachability=Reach(), hostname="farm5").resolve()
    if filter_proven:
        report["filter_packet_path"] = "docker_user_forward_verified"
    return report


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


def test_plan_blocks_without_verified_filter_packet_path_and_ready_with_proof():
    unresolved = build_plan(lanes=lanes(), customers=customers(), backend_target=target(filter_proven=False), iptables_save_text="", ip6tables_save_text="", phase_status_text=PHASE)
    assert "controlled_filter_packet_path_unresolved" in unresolved["blockers"]
    assert unresolved["final_decision"] == PACKAGE_BLOCKED
    plan = build_plan(lanes=lanes(), customers=customers(), backend_target=target(), iptables_save_text="", ip6tables_save_text="", phase_status_text=PHASE)
    assert plan["final_decision"] == PACKAGE_READY
    assert plan["blockers"] == []
    assert "--connlimit-above" in plan["payload"]
    assert "--hashlimit-above" in plan["payload"]
    assert "--to-destination 172.19.0.5:60010" in plan["payload"]
    assert "127.0.0.1" not in plan["payload"]
    assert "172.18.0.3" not in plan["payload"]
    pkg = build_package_from_plan(plan)
    assert pkg["final_decision"] == PACKAGE_READY


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
    assert "historical_backend_target_forbidden" not in hist


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


def test_whitelist_and_policy_values_are_source_backed_and_rendered():
    plan = build_plan(lanes=lanes(), customers=customers(whitelist=True), backend_target=target(), phase_status_text=PHASE)
    planner_customers = plan["desired_state"]["planner"]["rules"]
    assert any(rule.get("rule_kind") == "customer_whitelist_allow" for rule in planner_customers)
    assert plan["blockers"] == []
    assert "-s 203.0.113.10/32" in plan["payload"]
    assert "-s 203.0.113.11/32" in plan["payload"]


def test_current_artifact_gate_requires_explicit_target_and_blocks_stale_default():
    from mpf.services.phase11_current_controlled_artifact_gate_service import build_phase11_current_controlled_artifact_gate_report
    line = '-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.19.0.5:60010'
    ok = build_phase11_current_controlled_artifact_gate_report(iptables_save_text=line, phase_status_text=PHASE, expected_backend_target="172.19.0.5:60010")
    assert ok["final_decision"] == "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS"
    implicit = build_phase11_current_controlled_artifact_gate_report(iptables_save_text=line, phase_status_text=PHASE)
    assert "expected_backend_target_required" in implicit["blockers"]
    stale = build_phase11_current_controlled_artifact_gate_report(iptables_save_text=line, phase_status_text=PHASE, expected_backend_target="172.19.0.6:60010")
    assert "unknown_mpf_artifacts_detected" in stale["blockers"]


def _iptables_from_artifacts(artifacts):
    return "\n".join(item.split(":", 1)[1] for item in artifacts)


def test_classifier_accepts_full_expected_chain_set_and_nat_post_table():
    plan = build_plan(lanes=lanes(), customers=customers(), backend_target=target(), phase_status_text=PHASE)
    desired = plan["desired_state"]
    expected = {
        "filter:-N MPF_INPUT",
        "filter:-N MPF_CUSTOMERS",
        "filter:-N MPF_GUARD",
        "filter:-N MPF_ACCT_IN",
        "filter:-N MPF_ACCT_OUT",
        "nat:-N MPF_NAT_PRE",
        "nat:-N MPF_NAT_POST",
        "filter:-N MPFL_btc",
        "filter:-N MPFC_20001",
        "filter:-N MPFO_20001",
        "filter:-N MPFC_20101",
        "filter:-N MPFO_20101",
    }
    assert expected.issubset(set(desired["artifact_lines"]))
    assert any("customer_nat_redirect" in line and "172.19.0.5:60010" in line for line in desired["artifact_lines"])
    classification = classify_controlled_artifacts(
        iptables_save_text=_iptables_from_artifacts(desired["artifact_lines"]),
        ip6tables_save_text="",
        desired_state=desired,
    )
    assert classification["status"] == "exact_present"
    assert classification["unknown_mpf"] == []
    assert classification["blockers"] == []


def test_classifier_blocks_extra_unknown_chain_known_customer_unknown_action_and_duplicates():
    plan = build_plan(lanes=lanes(), customers=customers(), backend_target=target(), phase_status_text=PHASE)
    desired = plan["desired_state"]
    unknown_chain = _iptables_from_artifacts(desired["artifact_lines"]) + "\n-N MPF_SURPRISE"
    assert "unknown_mpf_artifacts_detected" in classify_controlled_artifacts(iptables_save_text=unknown_chain, ip6tables_save_text="", desired_state=desired)["blockers"]
    unknown_action = _iptables_from_artifacts(desired["artifact_lines"]) + '\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:unexpected_action" -j ACCEPT'
    assert "unknown_mpf_artifacts_detected" in classify_controlled_artifacts(iptables_save_text=unknown_action, ip6tables_save_text="", desired_state=desired)["blockers"]
    duplicated_chain = _iptables_from_artifacts([desired["artifact_lines"][0], desired["artifact_lines"][0]])
    assert "duplicate_controlled_artifact_detected" in classify_controlled_artifacts(iptables_save_text=duplicated_chain, ip6tables_save_text="", desired_state=desired)["blockers"]
    duplicated_rule = '-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.19.0.5:60010\n' * 2
    assert "duplicate_controlled_artifact_detected" in classify_controlled_artifacts(iptables_save_text=duplicated_rule, ip6tables_save_text="", desired_state=desired)["blockers"]


def _executable_live_plan(pkg):
    plan = dict(pkg["plan"])
    plan["final_decision"] = PACKAGE_READY
    plan["blockers"] = []
    backend = dict(plan.get("backend_target") or {})
    backend["target_fingerprint"] = pkg["backend_target_fingerprint"]
    plan["backend_target"] = backend
    plan["db_customer_policy_snapshot_hash"] = pkg["db_customer_policy_snapshot_hash"]
    plan["snapshot_hashes"] = {
        "iptables_save_sha256": pkg["iptables_save_sha256"],
        "ip6tables_save_sha256": pkg["ip6tables_save_sha256"],
    }
    plan["artifact_classification"] = {"blockers": []}
    plan["payload_sha256"] = pkg["payload_sha256"]
    plan["iptables_save_text"] = "*filter\nCOMMIT\n"
    plan["ip6tables_save_text"] = "*filter\nCOMMIT\n"
    return plan


class ProductionRunner:
    production_ready = True

    def __init__(self, *, test_returncode=0, apply_returncode=0):
        self.test_returncode = test_returncode
        self.apply_returncode = apply_returncode
        self.calls = []

    def run(self, argv, input_text=None):
        self.calls.append(argv)
        if argv == ["iptables-restore", "--test", "--noflush"]:
            return CommandResult(self.test_returncode, "", "test failed" if self.test_returncode else "")
        if argv == ["iptables-restore", "--noflush"]:
            return CommandResult(self.apply_returncode, "", "apply failed" if self.apply_returncode else "")
        return CommandResult(1, "", "unexpected")


class ProductionLock:
    production_ready = True

    def __init__(self):
        self.acquired = False

    def acquire(self):
        self.acquired = True
        return True

    def release(self):
        self.acquired = False


class ProductionBackup:
    production_ready = True

    def prepare(self, package, *, iptables_save, ip6tables_save):
        assert iptables_save.strip()
        assert ip6tables_save.strip()
        return {"backup_dir": "/tmp/mpf-test-backup", "manifest": {"iptables-save.txt": "sha"}}


class ProductionMetadata:
    production_ready = True

    def __init__(self, *, fail_result=False):
        self.fail_result = fail_result
        self.writes = []

    def record_intent(self, package, operator, reason, **kwargs):
        self.writes.append(("intent", operator, reason, kwargs))
        return {"firewall_apply_id": 1, "backup_id": 2}

    def record_result(self, package, decision, **kwargs):
        self.writes.append(("result", decision, kwargs))
        if self.fail_result:
            raise RuntimeError("metadata result failed")
        return {"snapshot_after_id": 3}


def _execute_with_production_fakes(pkg, *, runner=None, live_plan_builder=None, metadata=None):
    return execute_package(
        package=pkg,
        package_sha256="file-sha",
        package_id=pkg["package_id"],
        operator="op",
        reason="reason",
        execute=True,
        yes=True,
        env={"MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY":"allow", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE":"allow"},
        current_hostname=pkg["hostname"],
        live_plan_builder=live_plan_builder or (lambda: _executable_live_plan(pkg)),
        runner=runner or ProductionRunner(),
        lock=ProductionLock(),
        backup=ProductionBackup(),
        metadata_repo=metadata or ProductionMetadata(),
    )


def test_executor_failed_restore_test_records_no_apply_invocation():
    pkg = readyish_package()
    runner = ProductionRunner(test_returncode=1)
    result = _execute_with_production_fakes(pkg, runner=runner)
    assert result["final_decision"] == "FAILED_PRE_APPLY"
    assert result["restore_test_invoked"] is True
    assert result["apply_invoked"] is False
    assert result["apply_succeeded"] is False
    assert result["firewall_mutation_performed"] is False
    assert ["iptables-restore", "--noflush"] not in runner.calls


def test_executor_failed_apply_reports_apply_invoked_and_rollback_required():
    pkg = readyish_package()
    result = _execute_with_production_fakes(pkg, runner=ProductionRunner(apply_returncode=1))
    assert result["final_decision"] == "FAILED_APPLY"
    assert result["restore_test_invoked"] is True
    assert result["apply_invoked"] is True
    assert result["apply_succeeded"] is False
    assert result["partial_apply_possible"] is True
    assert result["rollback_required"] is True


def test_executor_apply_success_live_verification_exception_is_post_apply_failure():
    pkg = readyish_package()
    calls = {"count": 0}

    def live_plan_builder():
        calls["count"] += 1
        if calls["count"] >= 4:
            raise RuntimeError("verification source failed")
        return _executable_live_plan(pkg)

    result = _execute_with_production_fakes(pkg, live_plan_builder=live_plan_builder)
    assert result["final_decision"] == "FAILED_POST_APPLY_VERIFICATION"
    assert result["firewall_mutation_performed"] is True
    assert result["apply_succeeded"] is True
    assert result["partial_apply_possible"] is True
    assert result["rollback_required"] is True
    assert result["backup"]["backup_dir"] == "/tmp/mpf-test-backup"
    assert result["rollback_plan"] == pkg["rollback_plan"]


def test_executor_apply_success_metadata_result_exception_is_post_apply_failure():
    pkg = readyish_package()
    result = _execute_with_production_fakes(pkg, metadata=ProductionMetadata(fail_result=True))
    assert result["final_decision"] == "FAILED_POST_APPLY_VERIFICATION"
    assert result["firewall_mutation_performed"] is True
    assert result["apply_succeeded"] is True
    assert result["partial_apply_possible"] is True
    assert result["rollback_required"] is True


def test_public_verification_service_builds_read_only_live_plan(monkeypatch):
    from mpf.services import phase11_controlled_artifact_reapply_verification_service as service

    pkg = readyish_package()

    def fake_live_plan(config_path, *, expected_version):
        assert expected_version == __version__
        return {
            **_executable_live_plan(pkg),
            "final_decision": PACKAGE_BLOCKED,
            "blockers": ["controlled_policy_artifact_semantics_unresolved"],
        }

    monkeypatch.setattr(service, "run_controlled_artifact_reapply_plan", fake_live_plan)
    report = service.build_controlled_artifact_reapply_verify_report(package=pkg)
    assert report["live_plan_source"] == "fresh_read_only_preflight"
    assert "controlled_policy_artifact_semantics_unresolved" in report["blockers"]
    assert report["final_decision"] == "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_VERIFY"


def test_executor_generated_ready_package_verifies_post_apply_exact_present_no_reapply():
    pre_plan = build_plan(lanes=lanes(), customers=customers(), backend_target=target(), iptables_save_text="*filter\nCOMMIT\n", ip6tables_save_text="*filter\nCOMMIT\n", phase_status_text=PHASE)
    pre_plan["iptables_save_text"] = "*filter\nCOMMIT\n"
    pre_plan["ip6tables_save_text"] = "*filter\nCOMMIT\n"
    assert pre_plan["final_decision"] == PACKAGE_READY
    pkg = build_package_from_plan(pre_plan)
    pkg["hostname"] = __import__("socket").gethostname()
    pkg["package_sha256"] = _canonical_sha(_package_content_for_hash(pkg))
    pkg["__package_file_sha256"] = "file-sha"
    exact_text = _iptables_from_artifacts(pre_plan["desired_state"]["artifact_lines"])
    post_plan = build_plan(lanes=lanes(), customers=customers(), backend_target=target(), iptables_save_text=exact_text, ip6tables_save_text="*filter\nCOMMIT\n", phase_status_text=PHASE)
    post_plan["iptables_save_text"] = exact_text
    post_plan["ip6tables_save_text"] = "*filter\nCOMMIT\n"
    assert post_plan["final_decision"] == "NO_CONTROLLED_ARTIFACT_REAPPLY_REQUIRED"
    calls = {"count": 0}
    def live_plan_builder():
        calls["count"] += 1
        return pre_plan if calls["count"] <= 3 else post_plan
    result = _execute_with_production_fakes(pkg, live_plan_builder=live_plan_builder)
    assert result["final_decision"] == "CONTROLLED_ARTIFACT_REAPPLY_EXECUTED_PENDING_FARM5_EVIDENCE_REVIEW"
    assert result["rollback_required"] is False


def _live_ready_package_via_builder(tmp_path, monkeypatch):
    import hashlib
    from mpf.services import phase11_live_ready_reapply_package_service as live_svc
    from tests.test_phase11_live_ready_reapply_package import CUSTOMERS as LIVE_CUSTOMERS, LANES as LIVE_LANES
    from tests.test_phase11_verified_filter_hook_binding import _ready_bundle

    bundle = _ready_bundle(tmp_path, monkeypatch)
    out = tmp_path / "live-ready"
    report = live_svc.build_live_ready_reapply_package_report(packet_path_evidence_dir=bundle, lanes=LIVE_LANES, customers=LIVE_CUSTOMERS, phase_status_text=PHASE, output_dir=out)
    assert report["final_decision"] == live_svc.READY
    package_path = out / "controlled-artifact-reapply-package.json"
    package_bytes = package_path.read_bytes()
    package = json.loads(package_bytes.decode("utf-8"))
    package["__package_file_sha256"] = hashlib.sha256(package_bytes).hexdigest()
    return package


def _live_ready_package_with_snapshots(tmp_path, monkeypatch):
    import hashlib
    from mpf.services import phase11_live_ready_reapply_package_service as live_svc
    from tests.test_phase11_live_ready_reapply_package import CUSTOMERS as LIVE_CUSTOMERS, LANES as LIVE_LANES
    from tests.test_phase11_verified_filter_hook_binding import _ready_bundle

    snapshot = "*filter\nCOMMIT\n"
    bundle = _ready_bundle(tmp_path, monkeypatch)
    report = live_svc.build_live_ready_reapply_package_report(
        packet_path_evidence_dir=bundle,
        lanes=LIVE_LANES,
        customers=LIVE_CUSTOMERS,
        iptables_save_text=snapshot,
        ip6tables_save_text=snapshot,
        phase_status_text=PHASE,
    )
    assert report["final_decision"] == live_svc.READY
    package = report["package"] if "package" in report else None
    if package is None:
        # The public report intentionally keeps the package in output files only;
        # rebuild the same package directly from the embedded plan helper path.
        out = tmp_path / "live-ready-snapshots"
        live_svc.build_live_ready_reapply_package_report(
            packet_path_evidence_dir=bundle,
            lanes=LIVE_LANES,
            customers=LIVE_CUSTOMERS,
            iptables_save_text=snapshot,
            ip6tables_save_text=snapshot,
            phase_status_text=PHASE,
            output_dir=out,
        )
        package = json.loads((out / "controlled-artifact-reapply-package.json").read_text())
    package["__package_file_sha256"] = hashlib.sha256(json.dumps(package, sort_keys=True).encode()).hexdigest()
    return package, snapshot


def test_executor_plain_plan_reproduces_live_ready_binding_drift(tmp_path, monkeypatch):
    pkg, snapshot = _live_ready_package_with_snapshots(tmp_path, monkeypatch)
    plain_target = target(filter_proven=False)
    plain_plan = build_plan(
        lanes=lanes(),
        customers=customers(),
        backend_target=plain_target,
        iptables_save_text=snapshot,
        ip6tables_save_text=snapshot,
        phase_status_text=PHASE,
    )
    runner = ProductionRunner()
    result = execute_package(
        package=pkg,
        package_sha256=pkg["__package_file_sha256"],
        package_id=pkg["package_id"],
        operator="op",
        reason="review",
        execute=True,
        yes=True,
        env={"MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY": "allow", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE": "allow"},
        current_hostname=pkg["hostname"],
        live_plan_builder=lambda: plain_plan,
        runner=runner,
        lock=ProductionLock(),
        backup=ProductionBackup(),
        metadata_repo=ProductionMetadata(),
    )
    assert result["final_decision"] == "FAILED_PRE_APPLY"
    assert "live_plan_blocked" in result["blockers"]
    assert "controlled_filter_packet_path_unresolved" in plain_plan["blockers"]
    assert result["iptables_restore_invoked"] is False
    assert runner.calls == []


def test_execution_time_live_ready_plan_revalidates_bound_semantics(tmp_path, monkeypatch):
    from mpf.services import phase11_controlled_artifact_reapply_executor_service as executor_svc

    pkg, snapshot = _live_ready_package_with_snapshots(tmp_path, monkeypatch)

    from tests.test_phase11_live_ready_reapply_package import CUSTOMERS as LIVE_CUSTOMERS, LANES as LIVE_LANES

    class Loaded:
        ok = True
        lanes = LIVE_LANES
        customers = LIVE_CUSTOMERS
        message = "ok"

    bound_target = pkg["plan"]["backend_target"]
    monkeypatch.setattr(executor_svc.firewall_planner_read_repo, "load_firewall_planner_input", lambda cfg: Loaded())
    monkeypatch.setattr(executor_svc, "build_controlled_backend_target_report", lambda expected_version: dict(bound_target))
    monkeypatch.setattr(executor_svc, "_phase_text", lambda: PHASE)
    monkeypatch.setattr(executor_svc, "load_config", lambda path: object())
    monkeypatch.setattr(executor_svc, "_cmd", lambda argv: type("R", (), {"argv": argv, "command": argv[0], "returncode": 0, "stdout": snapshot, "stderr": "", "ok": True})())

    live_plan = executor_svc.build_execution_time_live_ready_reapply_plan(package=pkg)
    assert live_plan["final_decision"] == PACKAGE_READY
    assert live_plan["execution_precondition_fingerprint"] == pkg["execution_precondition_fingerprint"]
    assert live_plan["live_ready_binding_revalidated"] is True
    assert live_plan["backend_target"]["controlled_artifact_graph_binding_mode"] == executor_svc.BOUND_PACKET_PATH_MODE

    result = execute_package(
        package=pkg,
        package_sha256=pkg["__package_file_sha256"],
        package_id=pkg["package_id"],
        operator="op",
        reason="reason",
        execute=True,
        yes=True,
        env={"MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY": "allow", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE": "allow"},
        current_hostname=pkg["hostname"],
        live_plan_builder=lambda: live_plan,
        runner=ProductionRunner(),
        lock=ProductionLock(),
        backup=ProductionBackup(),
        metadata_repo=ProductionMetadata(),
    )
    assert result["restore_test_invoked"] is True
    assert result["apply_invoked"] is True


def test_execution_time_live_ready_plan_accepts_same_identity_with_different_raw_fingerprint_source(tmp_path, monkeypatch):
    from mpf.services import phase11_controlled_artifact_reapply_executor_service as executor_svc
    from tests.test_phase11_live_ready_reapply_package import CUSTOMERS as LIVE_CUSTOMERS, LANES as LIVE_LANES

    pkg, snapshot = _live_ready_package_with_snapshots(tmp_path, monkeypatch)

    class Loaded:
        ok = True
        lanes = LIVE_LANES
        customers = LIVE_CUSTOMERS
        message = "ok"

    bound_target = pkg["plan"]["backend_target"]
    runtime_target = dict(bound_target)
    runtime_target["backend_target_source"] = "docker_inspect_verified_runtime_shape"
    runtime_target["target_fingerprint_input"] = {
        "runtime_source_shape": "farm5_execute_time",
        "resolved_ipv4": bound_target["resolved_ipv4"],
        "target_port": bound_target["target_port"],
        "network_id": bound_target["network_id"],
        "endpoint_id": bound_target.get("endpoint_id"),
    }
    runtime_target["target_fingerprint"] = "a" * 64

    monkeypatch.setattr(executor_svc.firewall_planner_read_repo, "load_firewall_planner_input", lambda cfg: Loaded())
    monkeypatch.setattr(executor_svc, "build_controlled_backend_target_report", lambda expected_version: runtime_target)
    monkeypatch.setattr(executor_svc, "_phase_text", lambda: PHASE)
    monkeypatch.setattr(executor_svc, "load_config", lambda path: object())
    monkeypatch.setattr(executor_svc, "_cmd", lambda argv: type("R", (), {"argv": argv, "command": argv[0], "returncode": 0, "stdout": snapshot, "stderr": "", "ok": True})())

    live_plan = executor_svc.build_execution_time_live_ready_reapply_plan(package=pkg)
    assert live_plan["final_decision"] == PACKAGE_READY
    assert live_plan["execution_precondition_fingerprint"] == pkg["execution_precondition_fingerprint"]
    assert live_plan["canonical_backend_binding_identity_match"] is True
    assert live_plan["live_backend_target_fingerprint"] == runtime_target["target_fingerprint"]
    assert live_plan["backend_target"]["target_fingerprint"] == pkg["backend_target_fingerprint"]
    assert "backend_target_fingerprint_drift" not in live_plan.get("blockers", [])
    assert "backend_target_binding_identity_drift" not in live_plan.get("blockers", [])


def test_execution_time_live_ready_plan_ignores_package_placeholder_backend_metadata(tmp_path, monkeypatch):
    from mpf.services import phase11_controlled_artifact_reapply_executor_service as executor_svc
    from tests.test_phase11_live_ready_reapply_package import CUSTOMERS as LIVE_CUSTOMERS, LANES as LIVE_LANES

    pkg, snapshot = _live_ready_package_with_snapshots(tmp_path, monkeypatch)

    class Loaded:
        ok = True
        lanes = LIVE_LANES
        customers = LIVE_CUSTOMERS
        message = "ok"

    bound_target = pkg["plan"]["backend_target"]
    package_target = dict(
        bound_target,
        network_id="verified_packet_path_bundle",
        endpoint_id="verified_packet_path_endpoint",
        compose_project=None,
    )
    package_target["reachability"] = dict(package_target.get("reachability") or {}, tcp_connect_ok=None)
    pkg["plan"]["backend_target"] = package_target
    runtime_target = dict(bound_target, network_id="real-docker-network", endpoint_id="real-docker-endpoint", compose_project="mpf-proxy")
    runtime_target["reachability"] = dict(runtime_target.get("reachability") or {}, tcp_connect_ok=True)
    runtime_target["target_fingerprint"] = "b" * 64

    monkeypatch.setattr(executor_svc.firewall_planner_read_repo, "load_firewall_planner_input", lambda cfg: Loaded())
    monkeypatch.setattr(executor_svc, "build_controlled_backend_target_report", lambda expected_version: runtime_target)
    monkeypatch.setattr(executor_svc, "_phase_text", lambda: PHASE)
    monkeypatch.setattr(executor_svc, "load_config", lambda path: object())
    monkeypatch.setattr(executor_svc, "_cmd", lambda argv: type("R", (), {"argv": argv, "command": argv[0], "returncode": 0, "stdout": snapshot, "stderr": "", "ok": True})())

    live_plan = executor_svc.build_execution_time_live_ready_reapply_plan(package=pkg)
    assert live_plan["final_decision"] == PACKAGE_READY
    assert live_plan["canonical_backend_binding_identity_match"] is True
    assert "backend_target_binding_identity_drift" not in live_plan.get("blockers", [])
    comparison = live_plan["drift_comparison"]
    assert comparison["hard_identity_mismatched_fields"] == []
    assert comparison["informational_mismatched_fields"] == []
    assert comparison["ignored_package_placeholder_fields"] == ["compose_project", "endpoint_id", "network_id", "tcp_connect_ok"]
    assert comparison["compared_stable_fields"]["network_id"]["ignored_package_placeholder"] is True
    assert comparison["compared_stable_fields"]["tcp_connect_ok"]["ignored_package_placeholder"] is True


def test_execution_time_live_ready_plan_fails_closed_on_binding_mismatch(tmp_path, monkeypatch):
    from mpf.services import phase11_controlled_artifact_reapply_executor_service as executor_svc

    pkg, snapshot = _live_ready_package_with_snapshots(tmp_path, monkeypatch)
    pkg["plan"]["backend_target"]["controlled_artifact_graph_binding_mode"] = "plain"
    pkg["package_sha256"] = _canonical_sha(_package_content_for_hash(pkg))

    class Loaded:
        ok = True
        lanes = lanes()
        customers = customers()
        message = "ok"

    monkeypatch.setattr(executor_svc.firewall_planner_read_repo, "load_firewall_planner_input", lambda cfg: Loaded())
    monkeypatch.setattr(executor_svc, "build_controlled_backend_target_report", lambda expected_version: dict(pkg["plan"]["backend_target"]))
    monkeypatch.setattr(executor_svc, "load_config", lambda path: object())
    monkeypatch.setattr(executor_svc, "_cmd", lambda argv: type("R", (), {"argv": argv, "command": argv[0], "returncode": 0, "stdout": snapshot, "stderr": "", "ok": True})())

    live_plan = executor_svc.build_execution_time_live_ready_reapply_plan(package=pkg)
    assert live_plan["final_decision"] == PACKAGE_BLOCKED
    assert "live_ready_binding_revalidation_failed" in live_plan["blockers"]
    assert "packet_path_binding_mode_mismatch" in live_plan["blockers"]


def test_execution_time_live_ready_plan_fails_closed_on_public_or_unhealthy_backend(tmp_path, monkeypatch):
    from mpf.services import phase11_controlled_artifact_reapply_executor_service as executor_svc
    from tests.test_phase11_live_ready_reapply_package import CUSTOMERS as LIVE_CUSTOMERS, LANES as LIVE_LANES

    pkg, snapshot = _live_ready_package_with_snapshots(tmp_path, monkeypatch)

    class Loaded:
        ok = True
        lanes = LIVE_LANES
        customers = LIVE_CUSTOMERS
        message = "ok"

    monkeypatch.setattr(executor_svc.firewall_planner_read_repo, "load_firewall_planner_input", lambda cfg: Loaded())
    monkeypatch.setattr(executor_svc, "load_config", lambda path: object())
    monkeypatch.setattr(executor_svc, "_cmd", lambda argv: type("R", (), {"argv": argv, "command": argv[0], "returncode": 0, "stdout": snapshot, "stderr": "", "ok": True})())

    for runtime_target, blocker in (
        (dict(pkg["plan"]["backend_target"], backend_public_exposure=True), "forbidden_public_runtime_exposure"),
        (dict(pkg["plan"]["backend_target"], health_status="unhealthy"), "backend_target_health_not_verified"),
    ):
        monkeypatch.setattr(executor_svc, "build_controlled_backend_target_report", lambda expected_version, runtime_target=runtime_target: runtime_target)
        live_plan = executor_svc.build_execution_time_live_ready_reapply_plan(package=pkg)
        assert live_plan["final_decision"] == PACKAGE_BLOCKED
        assert blocker in live_plan["blockers"]
        assert live_plan["canonical_backend_binding_identity_match"] is False


def test_execution_time_live_ready_plan_fails_closed_on_backend_identity_drift(tmp_path, monkeypatch):
    from mpf.services import phase11_controlled_artifact_reapply_executor_service as executor_svc
    from tests.test_phase11_live_ready_reapply_package import CUSTOMERS as LIVE_CUSTOMERS, LANES as LIVE_LANES

    pkg, snapshot = _live_ready_package_with_snapshots(tmp_path, monkeypatch)

    class Loaded:
        ok = True
        lanes = LIVE_LANES
        customers = LIVE_CUSTOMERS
        message = "ok"

    bound_target = pkg["plan"]["backend_target"]
    drifted_target = dict(bound_target, resolved_ipv4="172.19.0.6", target_host="172.19.0.6", target_fingerprint="f" * 64)
    monkeypatch.setattr(executor_svc.firewall_planner_read_repo, "load_firewall_planner_input", lambda cfg: Loaded())
    monkeypatch.setattr(executor_svc, "build_controlled_backend_target_report", lambda expected_version: drifted_target)
    monkeypatch.setattr(executor_svc, "load_config", lambda path: object())
    monkeypatch.setattr(executor_svc, "_cmd", lambda argv: type("R", (), {"argv": argv, "command": argv[0], "returncode": 0, "stdout": snapshot, "stderr": "", "ok": True})())

    live_plan = executor_svc.build_execution_time_live_ready_reapply_plan(package=pkg)
    assert live_plan["final_decision"] == PACKAGE_BLOCKED
    assert "live_ready_binding_revalidation_failed" in live_plan["blockers"]
    assert "backend_target_binding_identity_drift" in live_plan["blockers"]
    assert live_plan["root_cause_blocker"] == "backend_target_binding_identity_drift"
    assert live_plan["canonical_backend_binding_identity_match"] is False
    assert live_plan["drift_comparison"]["mismatched_fields"]
    assert live_plan["drift_comparison"]["hard_identity_mismatched_fields"] == ["resolved_ipv4", "target_host"]

    runner = ProductionRunner()
    result = execute_package(
        package=pkg,
        package_sha256=pkg["__package_file_sha256"],
        package_id=pkg["package_id"],
        operator="op",
        reason="review",
        execute=True,
        yes=True,
        env={"MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY": "allow", "MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE": "allow"},
        current_hostname=pkg["hostname"],
        live_plan_builder=lambda: live_plan,
        runner=runner,
        lock=ProductionLock(),
        backup=ProductionBackup(),
        metadata_repo=ProductionMetadata(),
    )
    assert result["final_decision"] == "FAILED_PRE_APPLY"
    assert "live_plan_blocked" in result["blockers"]
    assert "backend_target_binding_identity_drift" in result["blockers"]
    assert result["root_cause_blocker"] == "backend_target_binding_identity_drift"
    assert result["live_plan_final_decision"] == PACKAGE_BLOCKED
    assert result["package_backend_target_fingerprint"] == pkg["backend_target_fingerprint"]
    assert result["live_backend_target_fingerprint"] == drifted_target["target_fingerprint"]
    assert result["drift_comparison"]["canonical_backend_binding_identity_match"] is False
    assert result["iptables_restore_invoked"] is False
    assert runner.calls == []


def test_execution_time_live_ready_plan_fails_closed_on_backend_port_drift(tmp_path, monkeypatch):
    from mpf.services import phase11_controlled_artifact_reapply_executor_service as executor_svc
    from tests.test_phase11_live_ready_reapply_package import CUSTOMERS as LIVE_CUSTOMERS, LANES as LIVE_LANES

    pkg, snapshot = _live_ready_package_with_snapshots(tmp_path, monkeypatch)

    class Loaded:
        ok = True
        lanes = LIVE_LANES
        customers = LIVE_CUSTOMERS
        message = "ok"

    bound_target = pkg["plan"]["backend_target"]
    drifted_target = dict(bound_target, target_port=60011, target_fingerprint="c" * 64)
    monkeypatch.setattr(executor_svc.firewall_planner_read_repo, "load_firewall_planner_input", lambda cfg: Loaded())
    monkeypatch.setattr(executor_svc, "build_controlled_backend_target_report", lambda expected_version: drifted_target)
    monkeypatch.setattr(executor_svc, "load_config", lambda path: object())
    monkeypatch.setattr(executor_svc, "_cmd", lambda argv: type("R", (), {"argv": argv, "command": argv[0], "returncode": 0, "stdout": snapshot, "stderr": "", "ok": True})())

    live_plan = executor_svc.build_execution_time_live_ready_reapply_plan(package=pkg)
    assert live_plan["final_decision"] == PACKAGE_BLOCKED
    assert "backend_target_binding_identity_drift" in live_plan["blockers"]
    assert live_plan["canonical_backend_binding_identity_match"] is False
    assert live_plan["drift_comparison"]["hard_identity_mismatched_fields"] == ["btc_backend_port", "target_port"]


def test_executor_generated_live_ready_package_preflight_only_operator_gates(tmp_path, monkeypatch):
    pkg = _live_ready_package_via_builder(tmp_path, monkeypatch)
    result = execute_package(
        package=pkg,
        package_sha256=pkg["__package_file_sha256"],
        package_id=pkg["package_id"],
        operator="op",
        reason="review",
        execute=False,
        yes=False,
        env={},
        current_hostname=pkg["hostname"],
        live_plan_builder=lambda: pkg["plan"],
        runner=ProductionRunner(),
        lock=ProductionLock(),
        backup=ProductionBackup(),
        metadata_repo=ProductionMetadata(),
    )
    assert result["final_decision"] == "FAILED_PRE_APPLY"
    assert result["blockers"] == [
        "controlled_artifact_reapply_env_gate_missing",
        "controlled_artifact_reapply_execute_env_gate_missing",
        "execute_mode_required",
        "yes_confirmation_required",
    ]
    for absent in ["package_canonical_sha256_mismatch", "version_mismatch", "package_version_mismatch", "package_file_sha256_mismatch"]:
        assert absent not in result["blockers"]
    assert result["firewall_mutation_performed"] is False
    assert result["iptables_restore_invoked"] is False
    assert result["restore_test_invoked"] is False
    assert result["apply_invoked"] is False
    assert result["apply_succeeded"] is False
    assert result["rollback_required"] is False


def test_executor_generated_live_ready_package_tamper_preserved_embedded_hash_fails(tmp_path, monkeypatch):
    pkg = _live_ready_package_via_builder(tmp_path, monkeypatch)
    embedded = pkg["package_sha256"]
    pkg["payload"] = str(pkg["payload"]) + "# tamper\n"
    pkg["package_sha256"] = embedded
    result = execute_package(
        package=pkg,
        package_sha256=pkg["__package_file_sha256"],
        package_id=pkg["package_id"],
        operator="op",
        reason="review",
        execute=False,
        yes=False,
        env={},
        current_hostname=pkg["hostname"],
    )
    assert "package_canonical_sha256_mismatch" in result["blockers"]
    assert result["firewall_mutation_performed"] is False
    assert result["iptables_restore_invoked"] is False


def test_executor_generated_live_ready_package_wrong_file_sha_fails(tmp_path, monkeypatch):
    pkg = _live_ready_package_via_builder(tmp_path, monkeypatch)
    result = execute_package(package=pkg, package_sha256="wrong", package_id=pkg["package_id"], operator="op", reason="review", execute=False, yes=False, env={}, current_hostname=pkg["hostname"])
    assert "package_file_sha256_mismatch" in result["blockers"]


def test_executor_generated_live_ready_package_wrong_package_id_fails(tmp_path, monkeypatch):
    pkg = _live_ready_package_via_builder(tmp_path, monkeypatch)
    result = execute_package(package=pkg, package_sha256=pkg["__package_file_sha256"], package_id="wrong", operator="op", reason="review", execute=False, yes=False, env={}, current_hostname=pkg["hostname"])
    assert "package_id_mismatch" in result["blockers"]


def test_backend_target_fingerprint_is_recomputed_for_desired_state():
    good = target()
    ok = build_plan(lanes=lanes(), customers=customers(), backend_target=good, phase_status_text=PHASE)
    assert "backend_target_fingerprint_mismatch" not in ok["blockers"]
    tampered_fingerprint = dict(good)
    tampered_fingerprint["target_fingerprint"] = "0" * 64
    bad = build_plan(lanes=lanes(), customers=customers(), backend_target=tampered_fingerprint, phase_status_text=PHASE)
    assert "backend_target_fingerprint_mismatch" in bad["blockers"]
    tampered_input = dict(good)
    tampered_input["target_fingerprint_input"] = dict(good["target_fingerprint_input"], resolved_ipv4="172.19.0.6")
    bad_input = build_plan(lanes=lanes(), customers=customers(), backend_target=tampered_input, phase_status_text=PHASE)
    assert "backend_target_fingerprint_mismatch" in bad_input["blockers"]


def test_manual_backend_target_requires_valid_complete_fingerprint():
    manual = {
        "component": "phase11_controlled_backend_target_resolver",
        "status": "ok",
        "backend_target_source": "docker_inspect_verified",
        "network_id": "net1",
        "endpoint_id": "endpoint1",
        "health_status": "healthy",
        "running": True,
        "target_port": 60010,
        "resolved_ipv4": "172.19.0.5",
        "target_host": "172.19.0.5",
        "backend_public_exposure": False,
        "filter_packet_path": "docker_user_forward_verified",
    }
    missing = build_plan(lanes=lanes(), customers=customers(), backend_target=manual, phase_status_text=PHASE)
    assert "backend_target_fingerprint_missing" in missing["blockers"]
    fingerprint_input = {
        "repository_version": __version__,
        "hostname": "manual",
        "container_name": "/mpf-forwarder-btc",
        "container_id": "abc",
        "network_name": "mpf-proxy-internal",
        "network_id": "net1",
        "endpoint_id": "endpoint1",
        "backend_target_source": "docker_inspect_verified",
        "resolved_ipv4": "172.19.0.5",
        "backend_port": 60010,
    }
    valid = dict(manual, target_fingerprint_input=fingerprint_input, target_fingerprint=_canonical_sha(fingerprint_input))
    ok = build_plan(lanes=lanes(), customers=customers(), backend_target=valid, phase_status_text=PHASE)
    assert "backend_target_fingerprint_missing" not in ok["blockers"]
    assert "backend_target_fingerprint_mismatch" not in ok["blockers"]
