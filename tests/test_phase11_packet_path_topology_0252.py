from __future__ import annotations

import json

from mpf.domain.phase11_controlled_filter_packet_path import BLOCKED, INVALID, READY
from mpf.services.phase11_controlled_artifact_taxonomy import classify_controlled_artifact
from mpf.services.phase11_controlled_filter_packet_path_bundle_service import verify_packet_path_bundle, write_packet_path_bundle
from mpf.services.phase11_packet_path_topology_resolver import resolve_docker_bridge, validate_backend_ipv4, verify_backend_membership
from tests.test_phase11_controlled_filter_packet_path import FakeAdapter, PHASE, _collect, container, network


def test_live_shape_derived_bridge_two_interfaces_new_established_ready(monkeypatch):
    import mpf.services.phase11_controlled_filter_packet_path_service as svc
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "1")
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
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "1")
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
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "1")
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
    monkeypatch.setattr(svc, "_read_proc_value", lambda path, optional=False: "1")
    bundle=_collect(adapter=FakeAdapter(), phase_status_text=PHASE, write_dir=None)["bundle"]
    write_packet_path_bundle(bundle, tmp_path/"b")
    assert verify_packet_path_bundle(tmp_path/"b")["bundle_integrity_valid"] is True
    legacy=dict(bundle); legacy["evidence"]=dict(bundle["evidence"]); legacy["evidence"].pop("packet_path_schema_version")
    write_packet_path_bundle(legacy, tmp_path/"legacy")
    res=verify_packet_path_bundle(tmp_path/"legacy")
    assert res["final_decision"] == INVALID
    assert "legacy_packet_path_schema_recollection_required" in res["blockers"]
