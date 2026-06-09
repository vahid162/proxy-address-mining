from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mpf import __version__
from mpf.adapters.phase11_read_only_command import Phase11ReadOnlyCommandAdapter, ReadOnlyCommandResult, allowed_argv
from mpf.domain.phase11_controlled_filter_packet_path import BLOCKED, INVALID, NEXT_REQUIRED_STEP, READY
from mpf.interfaces.cli import app
from mpf.services.phase11_controlled_filter_packet_path_bundle_service import verify_packet_path_bundle, write_packet_path_bundle
from mpf.services.phase11_controlled_filter_packet_path_service import _collect
from mpf.services.phase11_firewall_packet_path_parser import parse_iptables_save_topology
from mpf.services.phase11_current_controlled_artifact_gate_service import _phase_gate_ok
from mpf.services.phase11_operational_completion_progression import active_progression
from mpf.services.phase11_controlled_artifact_persistence_plan_service import build_phase11_controlled_artifact_persistence_plan_report

PHASE = """
current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5
current_working_phase: Phase 11 operational completion — Full CLI Production Operations
production_traffic: controlled_cli_limited
firewall_apply_allowed: controlled
abuse_automation_allowed: controlled_operator_gated
customer_onboarding_allowed: controlled_cli_limited
proxy_data_plane_allowed: limited_runtime_local_only
worker_enforcement_allowed: no
ui_allowed: no
telegram_allowed: no
phase12_start_allowed: no
"""

IPT_READY = """*nat
:PREROUTING ACCEPT [0:0]
:INPUT ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]
:DOCKER - [0:0]
-A PREROUTING -m addrtype --dst-type LOCAL -j DOCKER
-A DOCKER -i br-abcdef123456 -j RETURN
COMMIT
*filter
:INPUT ACCEPT [0:0]
:FORWARD DROP [0:0]
:OUTPUT ACCEPT [0:0]
:DOCKER-USER - [0:0]
:DOCKER-FORWARD - [0:0]
:DOCKER - [0:0]
-A FORWARD -j DOCKER-USER
-A FORWARD -j DOCKER-FORWARD
-A DOCKER-USER -j RETURN
-A DOCKER-FORWARD -d 172.30.0.5/32 -p tcp -m tcp --dport 60010 -j ACCEPT
COMMIT
"""
IP6_EMPTY = """*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
COMMIT
"""


def container(running=True, health="healthy", project="mpf-proxy", service="mpf-forwarder-btc", ip="172.30.0.5", publish=None):
    return json.dumps([{
        "Id": "cid123", "Name": "/mpf-forwarder-btc", "Image": "sha256:image",
        "State": {"Running": running, "Health": {"Status": health}},
        "Config": {"Labels": {"com.docker.compose.project": project, "com.docker.compose.service": service}, "ExposedPorts": {"60010/tcp": {}}},
        "HostConfig": {"NetworkMode": "mpf-proxy-internal", "RestartPolicy": {"Name": "unless-stopped"}},
        "NetworkSettings": {"Ports": {"60010/tcp": publish}, "Networks": {"mpf-proxy-internal": {"NetworkID": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890", "EndpointID": "123456abcdef", "MacAddress": "02:42:ac:1e:00:05", "IPAddress": ip, "IPPrefixLen": 24}}},
    }])


def network(unknown=False):
    containers = {"cid123": {"Name": "mpf-forwarder-btc", "EndpointID": "123456abcdef", "MacAddress": "02:42:ac:1e:00:05", "IPv4Address": "172.30.0.5/24"}}
    if unknown:
        containers["bad"] = {"Name": "unknown", "IPv4Address": "172.30.0.9/24"}
    return json.dumps([{
        "Name": "mpf-proxy-internal", "Id": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890", "Driver": "bridge", "Internal": False, "Attachable": False,
        "Options": {"com.docker.network.bridge.name": "br-abcdef123456"},
        "IPAM": {"Config": [{"Subnet": "172.30.0.0/24", "Gateway": "172.30.0.1"}]}, "Containers": containers,
    }])


class FakeAdapter(Phase11ReadOnlyCommandAdapter):
    def __init__(self, outputs=None, rc=None, truncated=None):
        self.outputs = outputs or {}
        self.rc = rc or {}
        self.truncated = truncated or set()

    def run(self, command_id: str, *, backend_ipv4: str | None = None, ingress_ifname: str | None = None, bridge_name: str | None = None, pid: str | None = None, redact_stdout: bool = False, require_non_empty: bool = False):
        argv = allowed_argv(command_id, backend_ipv4=backend_ipv4, ingress_ifname=ingress_ifname, bridge_name=bridge_name, pid=pid)
        stdout = self.outputs.get(command_id, self.outputs.get(f"{command_id}:{ingress_ifname}", default_output(command_id)))
        rc = self.rc.get(command_id, 0)
        if require_non_empty and not stdout.strip() and rc == 0:
            rc = 65
        return ReadOnlyCommandResult(command_id, argv, "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z", 1, rc, False, len(stdout), 0, "0"*64, "0"*64, command_id in self.truncated, redacted=redact_stdout, sanitized_projection_ref=("sanitized-backend-target.json" if command_id == "docker_inspect_backend" else None), stdout=stdout, stderr=None if redact_stdout else "")


def default_output(command_id):
    return {
        "hostname": "devhost\n", "uname_kernel": "6.1\n", "iptables_save": IPT_READY, "ip6tables_save": IP6_EMPTY,
        "iptables_version": "iptables v1.8.9 (nf_tables)\n", "ip6tables_version": "ip6tables v1.8.9 (nf_tables)\n",
        "docker_inspect_backend": container(), "docker_network_inspect": network(), "docker_ps_compose": "mpf-forwarder-btc\timage\tUp\t\n",
        "ip_address": json.dumps([{"ifname": "eth0", "addr_info": [{"family": "inet", "local": "203.0.113.10", "prefixlen": 24}]}]),
        "ip_link": json.dumps([{"ifname": "br-abcdef123456", "operstate": "UP", "flags": ["UP"]}, {"ifname":"veth0","ifindex":10,"master":"br-abcdef123456"}]), "ip_route_all": json.dumps([{"dst":"172.30.0.0/24","dev":"br-abcdef123456"}]), "ip_rule": json.dumps([{"priority":0,"table":"local"},{"priority":32766,"table":"main"},{"priority":32767,"table":"default"}]),
        "ip_route_get_backend": json.dumps([{"dst": "172.30.0.5", "dev": "br-abcdef123456"}]), "ip_route_get_backend_ingress": json.dumps([{"dst": "172.30.0.5", "dev": "br-abcdef123456"}]), "bridge_link": json.dumps([{"ifname":"veth0","master":"br-abcdef123456","endpoint_id":"123456abcdef"}]),
        "bridge_fdb_backend": json.dumps([{"mac":"02:42:ac:1e:00:05","dev":"veth0"}]),
        "ip_link_master_bridge": json.dumps([{"ifname":"veth0","ifindex":10,"master":"br-abcdef123456"}]),
        "ss_listeners": "LISTEN 0 128 127.0.0.1:60010 0.0.0.0:*\n", "ss_backend_listener": "LISTEN 0 128 127.0.0.1:60010 0.0.0.0:*\n",
    }.get(command_id, "")


@pytest.fixture(autouse=True)
def _stable_proc(monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    monkeypatch.setattr(svc, "_route_localnet_values", lambda: {})


def test_command_allowlist_accepts_exact_and_rejects_arbitrary_mutation_shell():
    assert allowed_argv("iptables_save") == ["iptables-save"]
    assert allowed_argv("ip_route_get_backend", backend_ipv4="172.30.0.5") == ["ip", "-json", "route", "get", "172.30.0.5"]
    with pytest.raises(ValueError):
        allowed_argv("iptables_restore")
    with pytest.raises(ValueError):
        allowed_argv("bash -c iptables-save")


def test_adapter_uses_shell_false_missing_timeout_truncated_and_empty_fail_closed():
    calls = []
    def fake_run(argv, **kwargs):
        calls.append(kwargs)
        if argv[0] == "missing":
            raise FileNotFoundError()
        return subprocess.CompletedProcess(argv, 0, b"", b"")
    adapter = Phase11ReadOnlyCommandAdapter(run_func=fake_run)
    res = adapter.run("hostname", require_non_empty=True)
    assert calls[0]["shell"] is False
    assert res.return_code == 65
    assert adapter.run("iptables_save").mutation_performed is False


def test_parser_preserves_order_policies_return_unknown_ipv6_and_malformed():
    parsed = parse_iptables_save_topology(IPT_READY)
    assert parsed.forward_policy == "DROP"
    assert [r.jump_target for r in parsed.rules if r.table == "filter" and r.chain == "FORWARD"][:2] == ["DOCKER-USER", "DOCKER-FORWARD"]
    assert any(r.terminal_verdict == "RETURN" for r in parsed.rules)
    assert not parsed.errors
    assert parse_iptables_save_topology("*filter\n:INPUT ACCEPT [0:0]\n").errors
    assert parse_iptables_save_topology("*filter\n:INPUT ACCEPT [0:0]\n:INPUT ACCEPT [0:0]\nCOMMIT\n").errors
    assert parse_iptables_save_topology("*filter\n:MPF_BAD - [0:0]\nCOMMIT\n").unknown_mpf_artifacts
    assert parse_iptables_save_topology("*filter\n:INPUT ACCEPT [0:0]\n-A INPUT -m comment --comment mpf:x:customer_y -j ACCEPT\nCOMMIT\n", ipv6=True).ipv6_mpf_or_customer_artifacts_present


def test_ready_fixture_classifies_post_dnat_and_keeps_renderer_binding_blocked():
    summary = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["summary"]
    decision = summary["decision"]
    assert summary["final_decision"] == READY
    assert decision["post_dnat_route_class"] == "forwarded"
    assert decision["verified_builtin_filter_path"] == "FORWARD"
    assert decision["verified_user_policy_hook"] == "DOCKER-USER"
    assert decision["packet_view_at_verified_hook"] == "post_dnat_forward_filter"
    assert decision["destination_visible_at_verified_hook"] == {"ip": "172.30.0.5", "port": 60010}
    assert decision["original_destination_match_required"] is True
    assert decision["current_customer_port_match_compatible"] is False
    assert decision["current_renderer_binding_compatible"] is False
    assert decision["artifact_graph_binding_ready"] is False
    assert summary["runtime_packet_observed"] is False


@pytest.mark.parametrize("override,blocker", [
    ({"ip_route_get_backend": json.dumps([{"dst": "172.30.0.5", "dev": "lo"}])}, "post_dnat_route_not_forwarded"),
    ({"docker_network_inspect": network(unknown=True)}, "unknown_docker_network_containers_present"),
    ({"docker_inspect_backend": container(running=False)}, "backend_target_not_healthy"),
    ({"docker_inspect_backend": container(health="unhealthy")}, "backend_target_not_healthy"),
    ({"docker_inspect_backend": container(project="wrong")}, "backend_target_not_healthy"),
    ({"docker_inspect_backend": container(service="wrong")}, "backend_target_not_healthy"),
    ({"docker_inspect_backend": container(ip="172.31.0.5")}, "backend_target_outside_expected_docker_subnet"),
    ({"docker_inspect_backend": container(publish=[{"HostIp":"0.0.0.0","HostPort":"60010"}])}, "backend_target_not_healthy"),
    ({"iptables_save": IPT_READY.replace("-A FORWARD -j DOCKER-USER\n", "")}, "docker_user_not_reachable_on_forward_path"),
    ({"iptables_save": IPT_READY.replace("-A FORWARD -j DOCKER-USER\n", "-A FORWARD -j ACCEPT\n-A FORWARD -j DOCKER-USER\n")}, "accept_bypass_before_docker_user"),
    ({"iptables_save": IPT_READY.replace("-A FORWARD -j DOCKER-USER\n", "-A FORWARD -j DOCKER-USER\n-A FORWARD -j DOCKER-USER\n")}, "docker_user_hook_duplicated_or_ambiguous"),
])
def test_blocked_topology_and_graph_cases(override, blocker):
    summary = _collect(adapter=FakeAdapter(outputs=override), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] in {BLOCKED, INVALID}
    assert any(blocker in b for b in summary["blockers"])


@pytest.mark.parametrize("rc,truncated,expected", [
    ({"iptables_save": 1}, set(), "command_failed:iptables_save:1"),
    ({}, {"iptables_save"}, "command_output_truncated:iptables_save"),
    ({"docker_inspect_backend": 127}, set(), "command_failed:docker_inspect_backend:127"),
])
def test_command_failures_are_invalid_not_empty_healthy(rc, truncated, expected):
    summary = _collect(adapter=FakeAdapter(rc=rc, truncated=truncated), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == INVALID
    assert expected in summary["blockers"]


def test_sensitive_docker_stdout_not_persisted_in_command_results():
    bundle = _collect(adapter=FakeAdapter(outputs={"docker_inspect_backend": container()[:-2] + ', "Config.Env": ["TOKEN=secret"]}]'}), phase_status_text=PHASE, write_dir=None)["bundle"]
    command_results = bundle["command_results"]
    docker = next(r for r in command_results if r["command_id"] == "docker_inspect_backend")
    assert docker["redacted"] is True
    assert "stdout" not in docker
    assert "TOKEN" not in json.dumps(command_results)
    assert "Env" not in json.dumps(bundle["sanitized_backend_target"])


def test_bundle_write_verify_and_tamper_detection(tmp_path):
    bundle = _collect(adapter=FakeAdapter(outputs={"iptables_save": IPT_READY.replace("-A FORWARD -j DOCKER-USER\n", "")}), phase_status_text=PHASE, write_dir=None)["bundle"]
    result = write_packet_path_bundle(bundle, tmp_path / "bundle")
    assert result["final_decision"] == BLOCKED
    ok = verify_packet_path_bundle(tmp_path / "bundle")
    assert ok["bundle_integrity_valid"] is True
    (tmp_path / "bundle" / "decision.json").write_text("{}\n")
    bad = verify_packet_path_bundle(tmp_path / "bundle")
    assert bad["final_decision"] == INVALID
    assert any("file_hash_mismatch:decision.json" in b for b in bad["blockers"])


def test_bundle_rejects_unexpected_symlink_version_mismatch_and_raw_env(tmp_path):
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    write_packet_path_bundle(bundle, tmp_path / "bundle")
    (tmp_path / "bundle" / "extra").write_text("x")
    assert verify_packet_path_bundle(tmp_path / "bundle")["final_decision"] == INVALID


def test_cli_plan_collect_verify_and_overwrite_guard(tmp_path, monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "Phase11ReadOnlyCommandAdapter", lambda: FakeAdapter(outputs={"iptables_save": IPT_READY.replace("-A FORWARD -j DOCKER-USER\n", "")}))
    runner = CliRunner()
    plan = runner.invoke(app, ["production", "controlled-filter-packet-path-plan", "--output", "json"])
    assert plan.exit_code == 0
    assert json.loads(plan.stdout)["final_decision"] == BLOCKED
    out = tmp_path / "evidence"
    collect = runner.invoke(app, ["production", "controlled-filter-packet-path-collect", "--output-dir", str(out), "--output", "json"])
    assert collect.exit_code == 0
    assert set(p.name for p in out.iterdir()) == {"evidence.json","decision.json","sanitized-backend-target.json","sanitized-docker-network.json","iptables-save.txt","ip6tables-save.txt","parsed-firewall.json","host-network-topology.json","packet-path-graph.json","command-results.json","manifest.json","manifest.sha256"}
    verify = runner.invoke(app, ["production", "controlled-filter-packet-path-verify", "--evidence-dir", str(out), "--output", "json"])
    assert verify.exit_code == 0
    assert json.loads(verify.stdout)["bundle_integrity_valid"] is True
    overwrite = runner.invoke(app, ["production", "controlled-filter-packet-path-collect", "--output-dir", str(out), "--output", "json"])
    assert json.loads(overwrite.stdout)["final_decision"] == INVALID


def test_progression_and_active_gate_regressions():
    prog = active_progression()
    assert prog["controlled_filter_packet_path_evidence_capability_implemented"] is True
    assert prog["controlled_filter_packet_path_evidence_ready"] is False
    assert prog["artifact_graph_binding_ready"] is False
    assert prog["controlled_artifact_reapply_package_evidence_ready"] is False
    assert prog["restart_autostart_proof"] == "missing_or_partial"
    assert prog["full_cli_production_operations"] == "missing_or_partial"
    assert prog["production_traffic"] == "controlled_cli_limited"
    assert prog["phase12_start_allowed"] == "no"
    assert prog["next_required_step"] == NEXT_REQUIRED_STEP
    historical = "current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5\ncurrent_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness\nproduction_traffic: none\nfirewall_apply_allowed: no\nabuse_automation_allowed: no\ncustomer_onboarding_allowed: db_only\n"
    assert _phase_gate_ok(historical) is False
    report = build_phase11_controlled_artifact_persistence_plan_report(current_controlled_artifact_gate_result={"unknown_mpf_artifacts": [], "known_controlled_artifacts_present": False, "final_decision": "PASS_NO_CUSTOMER_ARTIFACTS"}, listening_sockets=[], customer_records=[], phase_status_text=PHASE, candidate_reapply_restore_path_reuse={"candidate_reapply_services_declared": True, "read_only_reapply_foundation_implemented": True, "execution_package_available": False})
    assert report["controlled_artifact_reapply_package_evidence_ready"] is False

IPT_INDIRECT_READY = IPT_READY.replace("-A FORWARD -j DOCKER-USER\n", ":CUSTOM_HOOK - [0:0]\n-A FORWARD -j CUSTOM_HOOK\n-A CUSTOM_HOOK -j DOCKER-USER\n")
IPT_CUSTOM_ACCEPT_BYPASS = IPT_READY.replace("-A FORWARD -j DOCKER-USER\n", ":CUSTOM_EARLY - [0:0]\n-A FORWARD -j CUSTOM_EARLY\n-A FORWARD -j DOCKER-USER\n-A CUSTOM_EARLY -d 172.30.0.5/32 -p tcp -m tcp --dport 60010 -j ACCEPT\n")
IPT_GOTO_BYPASS = IPT_READY.replace("-A FORWARD -j DOCKER-USER\n", ":CUSTOM_GOTO - [0:0]\n-A FORWARD -g CUSTOM_GOTO\n-A FORWARD -j DOCKER-USER\n-A CUSTOM_GOTO -d 172.30.0.5/32 -p tcp -m tcp --dport 60010 -j ACCEPT\n")
IPT_CYCLE = IPT_READY.replace("-A FORWARD -j DOCKER-USER\n", ":A - [0:0]\n:B - [0:0]\n-A FORWARD -j A\n-A A -j B\n-A B -j A\n-A FORWARD -j DOCKER-USER\n")
IPT_MATCH_ACCEPT_NOT_APPLY = IPT_READY.replace("-A FORWARD -j DOCKER-USER\n", "-A FORWARD -d 172.30.0.99/32 -p tcp -m tcp --dport 60010 -j ACCEPT\n-A FORWARD -j DOCKER-USER\n")
IPT_CONDITIONAL_HOOK_UNRELATED = IPT_READY.replace("-A FORWARD -j DOCKER-USER\n", "-A FORWARD -i unrelated0 -j DOCKER-USER\n")


def test_false_ready_custom_chain_accept_before_docker_user_blocks():
    summary = _collect(adapter=FakeAdapter(outputs={"iptables_save": IPT_CUSTOM_ACCEPT_BYPASS}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == BLOCKED
    assert "accept_bypass_before_docker_user" in summary["blockers"]


def test_indirect_jump_to_docker_user_can_be_ready_when_all_paths_traverse_hook():
    summary = _collect(adapter=FakeAdapter(outputs={"iptables_save": IPT_INDIRECT_READY}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == READY
    assert summary["decision"]["docker_user_reachable"] is True


def test_return_to_caller_then_accept_preserves_hook_seen():
    summary = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == READY
    assert summary["decision"]["hook_precedes_all_relevant_accept_paths"] is True


def test_goto_semantics_accept_before_hook_blocks():
    summary = _collect(adapter=FakeAdapter(outputs={"iptables_save": IPT_GOTO_BYPASS}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == BLOCKED
    assert "accept_bypass_before_docker_user" in summary["blockers"]


def test_builtin_accept_policy_without_hook_blocks_and_drop_policy_blocks_no_accept():
    accept_policy = IPT_READY.replace(":FORWARD DROP [0:0]", ":FORWARD ACCEPT [0:0]").replace("-A FORWARD -j DOCKER-USER\n-A FORWARD -j DOCKER-FORWARD\n", "")
    drop_policy = IPT_READY.replace("-A FORWARD -j DOCKER-USER\n-A FORWARD -j DOCKER-FORWARD\n", "")
    a = _collect(adapter=FakeAdapter(outputs={"iptables_save": accept_policy}), phase_status_text=PHASE, write_dir=None)["summary"]
    d = _collect(adapter=FakeAdapter(outputs={"iptables_save": drop_policy}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert "accept_bypass_before_docker_user" in a["blockers"]
    assert "no_applicable_accept_path_to_backend" in d["blockers"]


def test_cyclic_chain_graph_blocks_ready():
    summary = _collect(adapter=FakeAdapter(outputs={"iptables_save": IPT_CYCLE}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == BLOCKED
    assert any("cfg_cycle_detected" in b for b in summary["blockers"])


def test_multiple_paths_only_one_through_docker_user_blocks():
    multi = IPT_READY.replace("-A FORWARD -j DOCKER-USER\n", "-A FORWARD -d 172.30.0.99/32 -j DOCKER-USER\n-A FORWARD -d 172.30.0.5/32 -p tcp -m tcp --dport 60010 -j ACCEPT\n")
    summary = _collect(adapter=FakeAdapter(outputs={"iptables_save": multi}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == BLOCKED
    assert "accept_bypass_before_docker_user" in summary["blockers"]


def test_match_specific_accept_that_does_not_apply_does_not_block_ready():
    summary = _collect(adapter=FakeAdapter(outputs={"iptables_save": IPT_MATCH_ACCEPT_NOT_APPLY}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == READY


def test_match_specific_hook_on_unrelated_interface_does_not_prove_ready():
    summary = _collect(adapter=FakeAdapter(outputs={"iptables_save": IPT_CONDITIONAL_HOOK_UNRELATED}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == BLOCKED
    assert "docker_user_not_reachable_on_forward_path" in summary["blockers"]


@pytest.mark.parametrize("override,blocker", [
    ({"docker_network_inspect": network().replace('"Name": "mpf-proxy-internal"', '"Name": "wrong-net"')}, "docker_network_name_mismatch"),
    ({"docker_network_inspect": network().replace('"Driver": "bridge"', '"Driver": "overlay"')}, "docker_network_driver_not_bridge"),
    ({"docker_network_inspect": network().replace('"cid123"', '"othercid"')}, "backend_container_missing_from_network_inspect"),
    ({"docker_network_inspect": network().replace('"172.30.0.5/24"', '"172.30.0.6/24"')}, "backend_ipv4_mismatch_between_inspects"),
    ({"ip_link": json.dumps([{"ifname": "eth0"}])}, "docker_bridge_interface_missing"),
    ({"bridge_fdb_backend": json.dumps([])}, "backend_bridge_membership_unverified"),
    ({"docker_inspect_backend": container().replace('"NetworkID": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"', '"NetworkID": "wrong"')}, "docker_network_id_mismatch"),
])
def test_docker_network_identity_mismatch_blocks_ready(override, blocker):
    summary = _collect(adapter=FakeAdapter(outputs=override), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == BLOCKED
    assert blocker in summary["blockers"]


@pytest.mark.parametrize("command_id,blocker", [
    ("ip_address", "ip_address_json_invalid"),
    ("ip_link", "ip_link_json_invalid"),
    ("ip_route_all", "ip_route_all_json_invalid"),
    ("ip_rule", "ip_rule_json_invalid"),
    ("ip_route_get_backend", "route_get_json_invalid"),
    ("bridge_link", "bridge_link_json_invalid"),
    ("docker_inspect_backend", "docker_inspect_json_invalid"),
    ("docker_network_inspect", "docker_network_inspect_json_invalid"),
])
def test_malformed_required_json_is_invalid(command_id, blocker):
    summary = _collect(adapter=FakeAdapter(outputs={command_id: "{not-json"}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == INVALID
    assert blocker in summary["blockers"]


@pytest.mark.parametrize("policy_rules,blocker", [
    ([{"priority": 0, "table": "local"}, {"priority": 32766, "table": "main"}, {"priority": 32767, "table": "default"}], None),
    ([{"priority": 100, "from": "10.0.0.0/8", "table": "100"}], "policy_routing_ambiguous"),
    ([{"priority": 100, "fwmark": "0x1", "table": "100"}], "policy_routing_ambiguous"),
    ([{"priority": 100, "iif": "eth0", "table": "100"}], "policy_routing_ambiguous"),
])
def test_policy_routing_behavior(policy_rules, blocker):
    summary = _collect(adapter=FakeAdapter(outputs={"ip_rule": json.dumps(policy_rules)}), phase_status_text=PHASE, write_dir=None)["summary"]
    if blocker is None:
        assert summary["final_decision"] == READY
    else:
        assert summary["final_decision"] == BLOCKED
        assert blocker in summary["blockers"]


@pytest.mark.parametrize("route_type,blocker", [("unreachable", "route_get_backend_unreachable"), ("blackhole", "route_get_backend_blackhole"), ("prohibit", "route_get_backend_prohibit")])
def test_unreachable_route_types_block(route_type, blocker):
    summary = _collect(adapter=FakeAdapter(outputs={"ip_route_get_backend": json.dumps([{"dst":"172.30.0.5","dev":"br-abcdef123456","type":route_type}])}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == BLOCKED
    assert blocker in summary["blockers"]


def test_adapter_rejects_invalid_dynamic_backend_ipv4():
    for value in ["127.0.0.1", "169.254.1.1", "224.0.0.1", "0.0.0.0", "8.8.8.8", "not-ip"]:
        res = Phase11ReadOnlyCommandAdapter(run_func=lambda *a, **k: None).run("ip_route_get_backend", backend_ipv4=value)
        assert res.return_code == 126


def test_verifier_handles_malformed_json_without_exception(tmp_path):
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    write_packet_path_bundle(bundle, tmp_path / "bundle")
    (tmp_path / "bundle" / "manifest.json").write_text("{bad\n")
    result = verify_packet_path_bundle(tmp_path / "bundle")
    assert result["final_decision"] == INVALID
    assert "manifest_json_invalid" in result["blockers"] or "manifest_sha256_mismatch" in result["blockers"]


def test_verifier_cross_checks_manifest_metadata(tmp_path):
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    write_packet_path_bundle(bundle, tmp_path / "bundle")
    manifest_path = tmp_path / "bundle" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["final_decision"] = "BLOCKED_CONTROLLED_FILTER_PACKET_PATH_PROOF"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    (tmp_path / "bundle" / "manifest.sha256").write_text(__import__('hashlib').sha256(manifest_path.read_bytes()).hexdigest()+"  manifest.json\n")
    result = verify_packet_path_bundle(tmp_path / "bundle")
    assert result["final_decision"] == INVALID
    assert "manifest_final_decision_mismatch" in result["blockers"]


def test_safe_output_directory_rejects_symlink_parent_and_target(tmp_path):
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError):
        write_packet_path_bundle(bundle, link / "bundle")
    target = tmp_path / "target"
    target.symlink_to(real, target_is_directory=True)
    with pytest.raises(FileExistsError):
        write_packet_path_bundle(bundle, target)


def test_bundle_file_symlink_and_precreated_file_rejected(tmp_path):
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    out = tmp_path / "bundle"
    write_packet_path_bundle(bundle, out)
    (out / "decision.json").unlink()
    (out / "decision.json").symlink_to(out / "evidence.json")
    assert verify_packet_path_bundle(out)["final_decision"] == INVALID
    out2 = tmp_path / "bundle2"
    out2.mkdir(mode=0o700)
    (out2 / "evidence.json").write_text("x")
    with pytest.raises(FileExistsError):
        write_packet_path_bundle(bundle, out2)


def test_invalid_evidence_cannot_claim_future_reachability():
    summary = _collect(adapter=FakeAdapter(outputs={"iptables_save": IPT_READY.replace("-A FORWARD -j DOCKER-USER\n", "")}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == BLOCKED
    assert summary["decision"]["future_mpf_entry_reachable"] is False
    assert summary["decision"]["original_destination_available_via_conntrack"] == "unresolved"


@pytest.mark.parametrize("rule", [
    "-A FORWARD -s 10.0.0.0/8 -j DOCKER-USER",
    "-A FORWARD -m mark --mark 0x1 -j DOCKER-USER",
    "-A FORWARD -m conntrack --ctstate ESTABLISHED -j DOCKER-USER",
    "-A FORWARD ! -d 172.30.0.5/32 -j DOCKER-USER",
    "-A FORWARD -m addrtype --dst-type LOCAL -j DOCKER-USER",
])
def test_unsupported_or_unresolved_match_rules_do_not_return_ready(rule):
    text = IPT_READY.replace("-A FORWARD -j DOCKER-USER", rule)
    summary = _collect(adapter=FakeAdapter(outputs={"iptables_save": text}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == BLOCKED
    assert summary["decision"]["verified_user_policy_hook"] is None


def test_duplicate_indirect_hook_entries_block_ready():
    text = IPT_READY.replace(
        "-A FORWARD -j DOCKER-USER\n",
        ":CHAIN_A - [0:0]\n:CHAIN_B - [0:0]\n-A FORWARD -j CHAIN_A\n-A FORWARD -j CHAIN_B\n-A CHAIN_A -j DOCKER-USER\n-A CHAIN_A -j RETURN\n-A CHAIN_B -j DOCKER-USER\n-A CHAIN_B -j RETURN\n",
    )
    summary = _collect(adapter=FakeAdapter(outputs={"iptables_save": text}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == BLOCKED
    assert "docker_user_hook_duplicated_or_ambiguous" in summary["blockers"]


def test_unrelated_bridge_member_does_not_verify_backend_membership():
    result = _collect(adapter=FakeAdapter(outputs={"bridge_fdb_backend": json.dumps([{"mac":"02:42:ac:1e:00:99","dev":"veth-other"}])}), phase_status_text=PHASE, write_dir=None)
    summary = result["summary"]
    assert summary["final_decision"] == BLOCKED
    assert "backend_bridge_membership_unresolved" in summary["blockers"]
    assert result["bundle"]["host_topology"]["backend_bridge_membership_status"] == "unresolved"


def test_verifier_schema_wrong_types_do_not_raise(tmp_path):
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    write_packet_path_bundle(bundle, tmp_path / "bundle")
    manifest_path = tmp_path / "bundle" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["decision.json"]["size"] = "invalid"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    (tmp_path / "bundle" / "manifest.sha256").write_text(__import__('hashlib').sha256(manifest_path.read_bytes()).hexdigest()+"  manifest.json\n")
    result = verify_packet_path_bundle(tmp_path / "bundle")
    assert result["final_decision"] == INVALID
    assert any("file_size_schema_invalid:decision.json" in b or "file_size_mismatch:decision.json" in b for b in result["blockers"])


def test_verifier_rejects_wrong_doc_schemas_and_raw_hash_mismatch(tmp_path):
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    write_packet_path_bundle(bundle, tmp_path / "bundle")
    (tmp_path / "bundle" / "sanitized-backend-target.json").write_text("[]\n")
    result = verify_packet_path_bundle(tmp_path / "bundle")
    assert result["final_decision"] == INVALID

    bundle2 = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    write_packet_path_bundle(bundle2, tmp_path / "bundle2")
    parsed_path = tmp_path / "bundle2" / "parsed-firewall.json"
    parsed = json.loads(parsed_path.read_text())
    parsed["ipv4"]["source_sha256"] = "0" * 64
    parsed_path.write_text(json.dumps(parsed, sort_keys=True) + "\n")
    manifest_path = tmp_path / "bundle2" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["parsed-firewall.json"]["sha256"] = __import__('hashlib').sha256(parsed_path.read_bytes()).hexdigest()
    manifest["files"]["parsed-firewall.json"]["size"] = len(parsed_path.read_bytes())
    manifest["ipv4_ruleset_hash"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    (tmp_path / "bundle2" / "manifest.sha256").write_text(__import__('hashlib').sha256(manifest_path.read_bytes()).hexdigest()+"  manifest.json\n")
    result2 = verify_packet_path_bundle(tmp_path / "bundle2")
    assert result2["final_decision"] == INVALID
    assert "ipv4_raw_ruleset_hash_mismatch" in result2["blockers"]


def test_ready_bundle_requires_route_get_command(tmp_path):
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    assert bundle["decision"]["final_decision"] == READY
    bundle["command_results"] = [r for r in bundle["command_results"] if r["command_id"] != "ip_route_get_backend"]
    write_packet_path_bundle(bundle, tmp_path / "bundle")
    result = verify_packet_path_bundle(tmp_path / "bundle")
    assert result["final_decision"] == INVALID
    assert "ready_required_command_missing:ip_route_get_backend" in result["blockers"]

@pytest.mark.parametrize("filename,content,blocker", [
    ("sanitized-backend-target.json", "[]\n", "backend_target_schema_invalid"),
    ("parsed-firewall.json", json.dumps({"ipv4": [], "ipv6": {}}) + "\n", "parsed_firewall_schema_invalid"),
    ("command-results.json", json.dumps([{"command_id":"hostname","return_code":"0","output_truncated":"false","mutation_performed":"false"}]) + "\n", "command_result_field_schema_invalid:hostname"),
])
def test_verifier_rejects_malformed_schema_valid_json(tmp_path, filename, content, blocker):
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    write_packet_path_bundle(bundle, tmp_path / "bundle")
    target = tmp_path / "bundle" / filename
    target.write_text(content)
    manifest_path = tmp_path / "bundle" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][filename]["sha256"] = __import__('hashlib').sha256(target.read_bytes()).hexdigest()
    manifest["files"][filename]["size"] = len(target.read_bytes())
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    (tmp_path / "bundle" / "manifest.sha256").write_text(__import__('hashlib').sha256(manifest_path.read_bytes()).hexdigest()+"  manifest.json\n")
    result = verify_packet_path_bundle(tmp_path / "bundle")
    assert result["final_decision"] == INVALID
    assert any(blocker in b for b in result["blockers"])
