from __future__ import annotations

import os

from mpf.services import phase11_generic_real_customer_activation_service as svc


def repo(customer=None, lane=None, policy=None):
    c = customer or {"customer_key":"alpha-btc-23456","lane":"btc","public_port":23456,"status":"active","deleted_at":None}
    return svc.StaticActivationRepository({c["customer_key"]: c}, {"btc": lane or {"enabled": True}}, {c["customer_key"]: policy or {"miners":1,"farms":1,"maxconn":10,"rate":60,"burst":5}})


def backend():
    return {"resolved_ipv4":"172.18.0.2","target_port":60010,"backend_public_exposure":False,"target_fingerprint":"x"}


def test_package_uses_arbitrary_db_customer_port_and_backend_resolver():
    r = svc.build_activation_package(repo(), "alpha-btc-23456", backend_resolver=backend, live_snapshot={"unknown_mpf_artifacts":[]})
    assert r["production_generic_real_customer_activation"] == svc.PACKAGE_READY
    assert r["public_port"] == 23456
    assert "23456" in r["restore_payload"]
    assert "20101" not in r["restore_payload"] and "60045" not in r["restore_payload"]
    assert r["resolved_backend_target"] == "172.18.0.2:60010"
    assert r["package_sha256"]


def test_eligibility_blocks_deleted_paused_expired_disabled_missing_policy_reserved_conflict():
    cases = [
        ({"customer_key":"c","lane":"btc","public_port":23456,"status":"active","deleted_at":"x"}, "customer_deleted"),
        ({"customer_key":"c","lane":"btc","public_port":23456,"status":"active","deleted_at":None,"paused":True}, "customer_paused"),
        ({"customer_key":"c","lane":"btc","public_port":23456,"status":"active","deleted_at":None,"expired":True}, "customer_expired"),
        ({"customer_key":"c","lane":"btc","public_port":60010,"status":"active","deleted_at":None}, "customer_port_reserved"),
    ]
    for customer, blocker in cases:
        r = svc.build_activation_package(repo(customer=customer), customer["customer_key"], backend_resolver=backend)
        assert blocker in r["blockers"]
    disabled = svc.build_activation_package(repo(lane={"enabled": False}), "alpha-btc-23456", backend_resolver=backend)
    assert "lane_disabled" in disabled["blockers"]
    missing_policy_repo = svc.StaticActivationRepository({"c":{"customer_key":"c","lane":"btc","public_port":23456,"status":"active","deleted_at":None}}, {"btc":{"enabled":True}}, {})
    assert "current_policy_missing" in svc.build_activation_package(missing_policy_repo, "c", backend_resolver=backend)["blockers"]
    conflict_repo = svc.StaticActivationRepository({"c":{"customer_key":"c","lane":"btc","public_port":23456,"status":"active","deleted_at":None},"d":{"customer_key":"d","lane":"btc","public_port":23456,"status":"active","deleted_at":None}}, {"btc":{"enabled":True}}, {"c":{"miners":1,"farms":1,"maxconn":1,"rate":1,"burst":1}})
    assert "duplicate_active_port_conflict" in svc.build_activation_package(conflict_repo, "c", backend_resolver=backend)["blockers"]


def test_live_artifacts_preflight_apply_verify_runtime_and_abuse_contracts(monkeypatch):
    pkg = svc.build_activation_package(repo(), "alpha-btc-23456", backend_resolver=backend)["package"]
    assert "unknown_live_mpf_artifact" in svc.build_activation_package(repo(), "alpha-btc-23456", backend_resolver=backend, live_snapshot={"unknown_mpf_artifacts":["x"]})["blockers"]
    assert "iptables_snapshot_required" in svc.preflight_activation_package(pkg, live_snapshot=None, confirmed_package_sha256=pkg["package_sha256"], operator_context="op")["blockers"]
    assert svc.preflight_activation_package(pkg, live_snapshot={"unknown_mpf_artifacts":[]}, confirmed_package_sha256=pkg["package_sha256"], operator_context="op")["production_generic_real_customer_activation"] == svc.PREFLIGHT_READY
    monkeypatch.setenv("CI", "1")
    assert "execute_flag_required" in svc.apply_activation_package(pkg)["blockers"]
    no_runner = svc.apply_activation_package(pkg, execute=True, confirmed_package_sha256=pkg["package_sha256"], confirmed_customer_key="alpha-btc-23456", confirmed_public_port=23456, pre_apply_snapshot_path="pre", rollback_artifact_path="rb", operator_lock_id="lock")
    assert "restore_runner_required_for_apply_execution" in no_runner["blockers"]
    assert no_runner.get("iptables_restore_invoked") is not True
    assert no_runner["firewall_mutation_performed"] is False
    assert no_runner["nat_mutation_performed"] is False
    assert no_runner["mutation_performed"] is False
    calls=[]
    applied = svc.apply_activation_package(pkg, execute=True, confirmed_package_sha256=pkg["package_sha256"], confirmed_customer_key="alpha-btc-23456", confirmed_public_port=23456, pre_apply_snapshot_path="pre", rollback_artifact_path="rb", operator_lock_id="lock", restore_runner=lambda *a, **k: calls.append((a,k)))
    assert applied["iptables_restore_invoked"] is True and len(calls) == 2
    good = {"dnat_by_port":{"23456":["172.18.0.2:60010"]}, "chains":["MPFC_23456"], "unknown_mpf_artifacts":[], "backend_public_exposure":False}
    assert svc.verify_activation(pkg, good)["final_decision"] == "GENERIC_REAL_CUSTOMER_ACTIVATION_VERIFY_READY"
    dup = {**good, "dnat_by_port":{"23456":["172.18.0.2:60010", "172.18.0.2:60010"]}}
    assert "dnat_count_not_exactly_one" in svc.verify_activation(pkg, dup)["blockers"]
    stale = {**good, "dnat_by_port":{"23456":["127.0.0.1:60010"]}}
    assert "stale_or_loopback_dnat_target" in svc.verify_activation(pkg, stale)["blockers"]
    assert svc.runtime_evidence(pkg, external_reachable=True, appears_in_reports=True)["production_generic_real_customer_activation"] == svc.READY
    assert svc.abuse_coverage_readiness(repo(), "alpha-btc-23456")["production_generic_real_customer_activation_abuse_coverage"] == "ready"
