from __future__ import annotations

import json

from mpf.domain.phase11_controlled_filter_packet_path import BLOCKED, INVALID, READY
from mpf.services.phase11_controlled_artifact_taxonomy import classify_controlled_artifact
from mpf.services.phase11_controlled_filter_packet_path_bundle_service import verify_packet_path_bundle, write_packet_path_bundle
from mpf.services.phase11_packet_path_topology_resolver import resolve_docker_bridge, validate_backend_ipv4, verify_backend_membership
from tests.test_phase11_controlled_filter_packet_path import FakeAdapter, PHASE, _collect, container, network


def test_live_shape_derived_bridge_two_interfaces_new_established_ready(monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    no_option = json.loads(network())
    no_option[0]["Options"] = {}
    outputs = {
        "docker_network_inspect": json.dumps(no_option),
        "ip_address": json.dumps([
            {"ifname":"uplink_a", "addr_info":[{"family":"inet","local":"203.0.113.10","prefixlen":24}]},
            {"ifname":"uplink_b", "addr_info":[{"family":"inet","local":"203.0.113.11","prefixlen":24}]},
        ]),
    }
    result = _collect(adapter=FakeAdapter(outputs=outputs), phase_status_text=PHASE, write_dir=None)
    summary = result["summary"]
    assert summary["final_decision"] == READY
    decision_graph = result["bundle"]["graph"]
    scenarios = decision_graph["packet_scenarios"]
    assert {s["conntrack_state"] for s in scenarios} == {"NEW", "ESTABLISHED"}
    assert {s["ingress_interface"] for s in scenarios} == {"uplink_a", "uplink_b"}
    assert summary["decision"]["current_renderer_binding_compatible"] is False
    assert summary["artifact_graph_binding_ready"] is False
    assert summary["production_execution_available"] is False


def test_bridge_resolution_safety_cases():
    links=[{"ifname":"br-abcdef123456","flags":["UP"],"operstate":"UP"}]
    routes=[{"dst":"172.30.0.0/24","dev":"br-abcdef123456"}]
    parsed={"rules":[{"match":{"out_interface":"br-abcdef123456"}}]}
    base={"network_id":"abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890","ipv4_subnet":"172.30.0.0/24"}
    ok = resolve_docker_bridge(network=base, links=links, routes=routes, parsed_ipv4=parsed)
    assert ok["bridge_name"] == "br-abcdef123456" and ok["bridge_name_verified"] is True
    assert resolve_docker_bridge(network={**base, "network_id":"short"}, links=links, routes=routes, parsed_ipv4=parsed)["bridge_name_verified"] is False
    assert resolve_docker_bridge(network={**base, "endpoint_id":base["network_id"]}, links=links, routes=routes, parsed_ipv4=parsed)["bridge_name_verified"] is False
    assert resolve_docker_bridge(network={**base, "bridge_name_explicit":"br-deadbeef0000", "bridge_name":"br-deadbeef0000"}, links=links, routes=routes, parsed_ipv4=parsed)["bridge_name_verified"] is False


def test_membership_requires_exact_correlation_and_allows_one_verified_method():
    backend={"mac_address":"02:42:ac:1e:00:05","resolved_ipv4":"172.30.0.5"}
    links=[{"ifname":"veth0","ifindex":10,"master":"br-abcdef123456"}]
    good_fdb=[{"mac":"02:42:ac:1e:00:05","dev":"veth0"}]
    bad_fdb=[{"mac":"02:42:ac:1e:00:99","dev":"veth0"}]
    assert verify_backend_membership(bridge_name="br-abcdef123456", backend=backend, links=links, fdb_entries=good_fdb)["verified"] is True
    assert verify_backend_membership(bridge_name="br-abcdef123456", backend=backend, links=links, fdb_entries=bad_fdb)["verified"] is False
    netns_link=[{"ifname":"eth0","address":"02:42:ac:1e:00:05","iflink":10}]
    netns_addr=[{"ifname":"eth0","addr_info":[{"family":"inet","local":"172.30.0.5"}]}]
    assert verify_backend_membership(bridge_name="br-abcdef123456", backend=backend, links=links, netns_link=netns_link, netns_addr=netns_addr)["verified"] is True


def test_backend_dynamic_dot3_allowed_but_hardcoded_fallback_rejected(monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    _, blockers = validate_backend_ipv4("172.18.0.3", source="docker_inspect_verified")
    assert blockers == []
    _, blocked = validate_backend_ipv4("172.18.0.3", source="historical_hardcoded_fallback")
    assert any("backend_target_source_rejected" in b for b in blocked)
    c = container(ip="172.18.0.3")
    n = json.loads(network()); n[0]["IPAM"]["Config"][0] = {"Subnet":"172.18.0.0/24","Gateway":"172.18.0.1"}; n[0]["Containers"]["cid123"]["IPv4Address"]="172.18.0.3/24"
    from tests.test_phase11_controlled_filter_packet_path import IPT_READY
    outputs={"docker_inspect_backend": c, "docker_network_inspect": json.dumps(n), "ip_route_get_backend": json.dumps([{"dst":"172.18.0.3","dev":"br-abcdef123456"}]), "ip_route_all": json.dumps([{"dst":"172.18.0.0/24","dev":"br-abcdef123456"}]), "iptables_save": IPT_READY.replace("172.30.0.5", "172.18.0.3").replace("172.30.0.99", "172.18.0.99")}
    assert _collect(adapter=FakeAdapter(outputs=outputs), phase_status_text=PHASE, write_dir=None)["summary"]["final_decision"] == READY


def test_backend_health_missing_blocks(monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    raw=json.loads(container()); del raw[0]["State"]["Health"]
    summary=_collect(adapter=FakeAdapter(outputs={"docker_inspect_backend": json.dumps(raw)}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == BLOCKED
    assert "backend_target_not_healthy" in summary["blockers"]


def test_taxonomy_exact_only():
    assert classify_controlled_artifact(chain="MPF_NAT_PRE") == "official_phase11_controlled_artifact"
    assert classify_controlled_artifact(chain="MPF_UNKNOWN") == "unknown_mpf_artifact"
    assert classify_controlled_artifact(chain="MPFC_19999") == "unknown_mpf_artifact"
    assert classify_controlled_artifact(chain="INPUT", comment="note mentioning mpf-ish") == "not_mpf_artifact"


def test_verifier_rejects_legacy_schema_and_duplicate_scenario(tmp_path, monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    bundle=_collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    write_packet_path_bundle(bundle, tmp_path/"b")
    assert verify_packet_path_bundle(tmp_path/"b")["bundle_integrity_valid"] is True
    legacy=dict(bundle); legacy["evidence"]=dict(bundle["evidence"]); legacy["evidence"].pop("packet_path_schema_version")
    write_packet_path_bundle(legacy, tmp_path/"legacy")
    res=verify_packet_path_bundle(tmp_path/"legacy")
    assert res["bundle_integrity_valid"] is True
    assert res["readiness_eligible"] is False
    assert res["recollection_required"] is True
    assert "legacy_packet_path_schema_recollection_required" in res["blockers"]

DOCKER_REAL_TOPOLOGY = """*nat
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
:DOCKER-CT - [0:0]
:DOCKER-BRIDGE - [0:0]
:DOCKER - [0:0]
:DOCKER-ISOLATION-STAGE-1 - [0:0]
:DOCKER-ISOLATION-STAGE-2 - [0:0]
-A FORWARD -j DOCKER-USER
-A FORWARD -j DOCKER-FORWARD
-A DOCKER-USER -j RETURN
-A DOCKER-FORWARD -j DOCKER-CT
-A DOCKER-FORWARD -j DOCKER-ISOLATION-STAGE-1
-A DOCKER-FORWARD -j DOCKER-BRIDGE
-A DOCKER-CT -o br-abcdef123456 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A DOCKER-ISOLATION-STAGE-1 -i br-abcdef123456 ! -o br-abcdef123456 -j DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-1 -j RETURN
-A DOCKER-ISOLATION-STAGE-2 -o br-abcdef123456 -j DROP
-A DOCKER-ISOLATION-STAGE-2 -j RETURN
-A DOCKER-BRIDGE -o br-abcdef123456 -j DOCKER
-A DOCKER -d 172.30.0.5/32 ! -i br-abcdef123456 -o br-abcdef123456 -p tcp -m tcp --dport 60010 -j ACCEPT
-A DOCKER ! -i br-abcdef123456 -o br-abcdef123456 -j DROP
COMMIT
"""


def test_real_redacted_docker_topology_requires_per_ingress_routes(monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    outputs = {
        "iptables_save": DOCKER_REAL_TOPOLOGY,
        "ip_address": json.dumps([
            {"ifname":"uplink_a", "addr_info":[{"family":"inet","local":"203.0.113.10","prefixlen":24}]},
            {"ifname":"uplink_b", "addr_info":[{"family":"inet","local":"203.0.113.11","prefixlen":24}]},
        ]),
    }
    result = _collect(adapter=FakeAdapter(outputs=outputs), phase_status_text=PHASE, write_dir=None)
    assert result["summary"]["final_decision"] == READY
    command_ids = {c["command_id"] for c in result["bundle"]["command_results"]}
    assert "ip_route_get_backend_ingress:uplink_a" in command_ids
    assert "ip_route_get_backend_ingress:uplink_b" in command_ids
    scenarios = result["bundle"]["graph"]["packet_scenarios"]
    assert len(scenarios) == 4
    assert {s["conntrack_state"] for s in scenarios} == {"NEW", "ESTABLISHED"}


def test_one_ingress_route_mismatch_blocks(monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    outputs = {
        "iptables_save": DOCKER_REAL_TOPOLOGY,
        "ip_address": json.dumps([
            {"ifname":"uplink_a", "addr_info":[{"family":"inet","local":"203.0.113.10","prefixlen":24}]},
            {"ifname":"uplink_b", "addr_info":[{"family":"inet","local":"203.0.113.11","prefixlen":24}]},
        ]),
        "ip_route_get_backend_ingress:uplink_b": json.dumps([{"dst":"172.30.0.5","dev":"eth-other"}]),
    }
    summary = _collect(adapter=FakeAdapter(outputs=outputs), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == BLOCKED
    assert "route_get_backend_device_mismatch:uplink_b" in summary["blockers"]


def test_missing_per_ingress_route_blocks(monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    summary = _collect(adapter=FakeAdapter(outputs={"ip_route_get_backend_ingress": ""}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert summary["final_decision"] == INVALID
    assert any("ip_route_get_backend_ingress" in b for b in summary["blockers"])


def test_policy_routing_fail_closed_unknown_and_noncanonical():
    from mpf.services.phase11_packet_path_policy_routing import policy_routing_blockers
    topology = {"host_addresses": [{"local":"203.0.113.10"}], "external_ingress_interfaces": [{"ifname":"uplink_a"}], "route_get_backend_by_ingress": {"uplink_a": [{"dev":"br-abcdef123456"}]}}
    blockers, warnings = policy_routing_blockers(topology={**topology, "policy_rules": [{"priority":100,"table":"100"}]}, bridge="br-abcdef123456")
    assert "policy_routing_noncanonical_selector_free_rule" in blockers
    blockers, _ = policy_routing_blockers(topology={**topology, "policy_rules": [{"priority":100,"table":"100", "mystery":"x"}]}, bridge="br-abcdef123456")
    assert "policy_routing_unknown_field:mystery" in blockers
    blockers, warnings = policy_routing_blockers(topology={**topology, "policy_rules": [{"priority":87,"table":"87", "from":"203.0.113.10/32"}, {"priority":0,"table":"local"}, {"priority":32766,"table":"main"}, {"priority":32767,"table":"default"}]}, bridge="br-abcdef123456")
    assert not blockers
    assert any("host_local_source" in w for w in warnings)


def test_verifier_rejects_ready_zero_missing_mismatched_scenarios(tmp_path, monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    for name, edit, blocker in [
        ("zero", lambda b: b["graph"].update({"packet_scenarios": []}), "ready_packet_scenarios_empty"),
        ("missing_results", lambda b: b["graph"].pop("scenario_results", None), "scenario_results_schema_invalid"),
        ("mismatch", lambda b: b["graph"]["scenario_results"][0].update({"scenario_id": "wrong"}), "scenario_result_id_mismatch"),
        ("missing_route_cmd", lambda b: b.update({"command_results": [c for c in b["command_results"] if not str(c.get("command_id")).startswith("ip_route_get_backend_ingress:")]}), "scenario_route_command_missing"),
        ("missing_fdb_cmd", lambda b: b.update({"command_results": [c for c in b["command_results"] if c.get("command_id") != "bridge_fdb_backend"]}), "fdb_membership_required_commands_missing"),
    ]:
        mutated = {k: (dict(v) if isinstance(v, dict) else list(v) if isinstance(v, list) else v) for k, v in bundle.items()}
        mutated["graph"] = json.loads(json.dumps(bundle["graph"]))
        mutated["command_results"] = json.loads(json.dumps(bundle["command_results"]))
        edit(mutated)
        write_packet_path_bundle(mutated, tmp_path / name)
        res = verify_packet_path_bundle(tmp_path / name)
        assert res["final_decision"] == INVALID
        assert any(str(b).startswith(blocker) for b in res["blockers"])


def test_rp_filter_and_firewall_backend_fail_closed(monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "1" if "rp_filter" in path else "1")
    strict = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["summary"]
    assert strict["final_decision"] == BLOCKED
    assert any("rp_filter_strict" in b for b in strict["blockers"])
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    mixed = _collect(adapter=FakeAdapter(outputs={"ip6tables_version":"ip6tables v1.8.9 (legacy)\n"}), phase_status_text=PHASE, write_dir=None)["summary"]
    assert "firewall_backend_mixed" in mixed["blockers"]


def test_nat_insertion_analysis_and_complete_taxonomy(monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    from mpf.services.phase11_controlled_artifact_taxonomy import OFFICIAL_CONTROLLED_CHAINS
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    nat = bundle["host_topology"]["nat_insertion_analysis"]
    assert nat["proposed_nat_parent_chain"] == "PREROUTING"
    assert nat["proposed_nat_insertion_mode"] == "append_after_existing_docker_jump"
    assert nat["nat_binding_ready"] is False
    for chain in {"MPF_INPUT","MPF_CUSTOMERS","MPF_GUARD","MPF_ACCT_IN","MPF_ACCT_OUT","MPF_NAT_PRE","MPF_NAT_POST","MPFL_btc","MPFC_20001","MPFO_20001","MPFC_20101","MPFO_20101"}:
        assert chain in OFFICIAL_CONTROLLED_CHAINS


def test_taxonomy_unknown_comment_on_official_chain_is_not_laundered():
    assert classify_controlled_artifact(chain="MPFC_20001", comment="mpf:canary-btc-001:unexpected_action") == "unknown_mpf_artifact"


def test_verifier_binds_route_projection_to_command_stdout(tmp_path, monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    for command in bundle["command_results"]:
        if command["command_id"].startswith("ip_route_get_backend_ingress:"):
            command["stdout"] = json.dumps([{"dst":"172.30.0.5","dev":"eth-tampered"}])
            command["stdout_sha256"] = "0" * 64
            break
    write_packet_path_bundle(bundle, tmp_path / "route_stdout_tamper")
    result = verify_packet_path_bundle(tmp_path / "route_stdout_tamper")
    assert result["final_decision"] == INVALID
    assert any("scenario_route_projection_stdout_mismatch" in b for b in result["blockers"])


def test_verifier_binds_fdb_membership_to_command_stdout(tmp_path, monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    for command in bundle["command_results"]:
        if command["command_id"] == "bridge_fdb_backend":
            command["stdout"] = json.dumps([{"mac":"02:42:ac:1e:00:99","dev":"veth0"}])
            command["stdout_sha256"] = "0" * 64
    write_packet_path_bundle(bundle, tmp_path / "fdb_stdout_tamper")
    result = verify_packet_path_bundle(tmp_path / "fdb_stdout_tamper")
    assert result["final_decision"] == INVALID
    assert "fdb_membership_source_record_mismatch" in result["blockers"]


def test_legacy_0251_manifest_integrity_stays_valid_despite_version_mismatch(tmp_path, monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    bundle["evidence"] = dict(bundle["evidence"])
    bundle["evidence"].pop("packet_path_schema_version", None)
    bundle["evidence"]["repository_version"] = "0.1.251"
    bundle["evidence"]["expected_version"] = "0.1.251"
    # Simulate a real legacy bundle by writing with old manifest version fields
    # while preserving all manifest/file hashes.
    write_packet_path_bundle(bundle, tmp_path / "legacy0251")
    manifest_path = tmp_path / "legacy0251" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["repository_version"] = "0.1.251"
    manifest["expected_version"] = "0.1.251"
    from mpf.services.phase11_controlled_filter_packet_path_bundle_service import canonical_json_bytes, sha256_bytes
    raw = canonical_json_bytes(manifest)
    manifest_path.write_bytes(raw)
    (tmp_path / "legacy0251" / "manifest.sha256").write_text(f"{sha256_bytes(raw)}  manifest.json\n")
    result = verify_packet_path_bundle(tmp_path / "legacy0251")
    assert result["bundle_integrity_valid"] is True
    assert result["readiness_eligible"] is False
    assert result["recollection_required"] is True


def test_zero_stdout_hash_is_invalid_for_ready_bundle(tmp_path, monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    for command in bundle["command_results"]:
        if command["command_id"].startswith("ip_route_get_backend_ingress:"):
            command["stdout_sha256"] = "0" * 64
            break
    write_packet_path_bundle(bundle, tmp_path / "zero_hash")
    result = verify_packet_path_bundle(tmp_path / "zero_hash")
    assert result["final_decision"] == INVALID
    assert any("command_stdout_hash_zero" in b for b in result["blockers"])


def test_route_and_fdb_stdout_hash_mismatch_are_invalid(tmp_path, monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "2" if "rp_filter" in path else "1")
    for dirname, command_prefix in [("route_hash", "ip_route_get_backend_ingress:"), ("fdb_hash", "bridge_fdb_backend")]:
        bundle = _collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
        for command in bundle["command_results"]:
            if str(command["command_id"]).startswith(command_prefix):
                command["stdout_sha256"] = "f" * 64
                break
        write_packet_path_bundle(bundle, tmp_path / dirname)
        result = verify_packet_path_bundle(tmp_path / dirname)
        assert result["final_decision"] == INVALID
        assert any("command_stdout_hash_mismatch" in b for b in result["blockers"])


def test_official_taxonomy_accepts_all_rendered_planner_comments_and_blocks_stale_comment():
    import shlex
    from tests.test_phase11_controlled_artifact_reapply import PHASE as REAPPLY_PHASE, build_plan, customers, lanes, target
    plan = build_plan(lanes=lanes(), customers=customers(whitelist=True), backend_target=target(), phase_status_text=REAPPLY_PHASE)
    comments = set()
    for artifact in plan["desired_state"]["artifact_lines"]:
        line = artifact.split(":", 1)[1]
        if "--comment" not in line:
            continue
        tokens = shlex.split(line)
        comments.add(tokens[tokens.index("--comment") + 1])
    assert comments
    for comment in comments:
        assert classify_controlled_artifact(chain="MPF_CUSTOMERS", comment=comment) == "official_phase11_controlled_artifact"
    assert classify_controlled_artifact(chain="MPF_CUSTOMERS", comment="mpf:canary-btc-001:customer_old_stale") == "unknown_mpf_artifact"
