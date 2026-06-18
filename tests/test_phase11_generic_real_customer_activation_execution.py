import json
from pathlib import Path
from typer.testing import CliRunner

from mpf.interfaces.cli import app
from mpf.services import phase11_generic_real_customer_activation_service as svc


def pkg(port=23456, key="generic-btc-xyz"):
    return {"customer_key": key, "lane": "btc", "public_port": port, "resolved_backend_target": "172.18.0.2:60010", "restore_payload": f"*nat\n-A PREROUTING -p tcp --dport {port} -j DNAT --to-destination 172.18.0.2:60010\nCOMMIT\n*filter\n-N MPFC_{port}\nCOMMIT\n", "package_id": "p1", "package_sha256": "sha"}


def test_apply_without_restore_runner_blocks():
    r = svc.apply_activation_package(pkg(), execute=True, confirmed_package_sha256="sha", confirmed_customer_key="generic-btc-xyz", confirmed_public_port=23456, pre_apply_snapshot_path="/tmp/before", rollback_artifact_path="/tmp/rb", operator_lock_id="lock")
    assert r["final_decision"].startswith("BLOCKED")
    assert "restore_runner_required_for_apply_execution" in r["blockers"]
    assert not r["mutation_performed"]


def test_mock_restore_runner_two_calls_success():
    calls=[]
    def runner(payload, *, test, noflush):
        calls.append((test, noflush, payload))
        return {"returncode": 0, "test": test, "noflush": noflush, "stdout": "", "stderr": ""}
    r=svc.apply_activation_package(pkg(), execute=True, confirmed_package_sha256="sha", confirmed_customer_key="generic-btc-xyz", confirmed_public_port=23456, pre_apply_snapshot_path="/tmp/before", rollback_artifact_path="/tmp/rb", operator_lock_id="lock", restore_runner=runner)
    assert [(c[0], c[1]) for c in calls] == [(True, True), (False, True)]
    assert r["iptables_restore_invoked"] is True
    assert r["firewall_mutation_performed"] is True
    assert r["nat_mutation_performed"] is True


def test_failed_test_blocks_apply():
    calls=[]
    def runner(payload, *, test, noflush):
        calls.append(test)
        if test: raise RuntimeError("bad test")
    r=svc.apply_activation_package(pkg(), execute=True, confirmed_package_sha256="sha", confirmed_customer_key="generic-btc-xyz", confirmed_public_port=23456, pre_apply_snapshot_path="/tmp/before", rollback_artifact_path="/tmp/rb", operator_lock_id="lock", restore_runner=runner)
    assert calls == [True]
    assert r["iptables_restore_invoked"] is False
    assert not r["mutation_performed"]
    assert "iptables_restore_test_failed" in r["blockers"]


def test_failed_apply_reports_no_successful_mutation():
    def runner(payload, *, test, noflush):
        if not test: raise RuntimeError("bad apply")
        return {"returncode":0}
    r=svc.apply_activation_package(pkg(), execute=True, confirmed_package_sha256="sha", confirmed_customer_key="generic-btc-xyz", confirmed_public_port=23456, pre_apply_snapshot_path="/tmp/before", rollback_artifact_path="/tmp/rb", operator_lock_id="lock", restore_runner=runner)
    assert r["iptables_restore_invoked"] is False
    assert r["firewall_mutation_performed"] is False
    assert "iptables_restore_apply_failed" in r["blockers"]


def test_cli_apply_without_env_gate_blocks(tmp_path):
    p=tmp_path/"pkg.json"; p.write_text(json.dumps({"package": pkg()}))
    res=CliRunner().invoke(app,["production","real-customer-activation-apply","--package-file",str(p),"--execute","--confirm-package-sha256","sha","--confirm-customer-key","generic-btc-xyz","--confirm-public-port","23456","--pre-apply-snapshot","/tmp/before","--rollback-artifact","/tmp/rb","--operator-lock-id","lock","--output","json"])
    assert res.exit_code == 0
    data=json.loads(res.stdout)
    assert "operator_env_gate_required_for_real_restore_runner" in data["blockers"]
    assert data["iptables_restore_invoked"] is False if "iptables_restore_invoked" in data else True


def test_iptables_save_converter_and_verify_arbitrary_port():
    snap=svc.snapshot_from_iptables_save(':PREROUTING ACCEPT [0:0]\n:MPFC_23456 - [0:0]\n-A PREROUTING -p tcp --dport 23456 -j DNAT --to-destination 172.18.0.2:60010\n')
    r=svc.verify_activation(pkg(), snap)
    assert r["final_decision"] == "GENERIC_REAL_CUSTOMER_ACTIVATION_VERIFY_READY"


def test_transcript_import_accepts_and_rejects_scope():
    good={"connect_host":"85.198.11.110","connect_port":23456,"worker_name":"generic-btc-xyz.win","subscribe_result":[1],"authorize_result":True,"mining_notify_received":True}
    r=svc.import_transcript_evidence(pkg(), good)
    assert r["final_decision"] == "GENERIC_REAL_CUSTOMER_ACTIVATION_TRANSCRIPT_EVIDENCE_READY"
    bad={**good, "connect_port": 23457, "worker_name":"other.win"}
    rb=svc.import_transcript_evidence(pkg(), bad)
    assert "transcript_public_port_mismatch" in rb["blockers"]
    assert "worker_scope_does_not_match_customer" in rb["blockers"]


def test_run_iptables_restore_requires_env_gate_before_subprocess(monkeypatch):
    called = False

    def fake_run(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("subprocess.run must not be invoked without env gate")

    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("MPF_PHASE11_GENERIC_ACTIVATION_APPLY", raising=False)
    monkeypatch.setattr(svc.subprocess, "run", fake_run)
    try:
        svc.run_iptables_restore("payload", test=True, noflush=True)
    except RuntimeError as exc:
        assert str(exc) == "operator_env_gate_required_for_iptables_restore"
    else:
        raise AssertionError("expected RuntimeError")
    assert called is False


def test_run_iptables_restore_ci_blocks_even_with_env_gate(monkeypatch):
    called = False

    def fake_run(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("subprocess.run must not be invoked in CI")

    monkeypatch.setenv("CI", "1")
    monkeypatch.setenv("MPF_PHASE11_GENERIC_ACTIVATION_APPLY", "1")
    monkeypatch.setattr(svc.subprocess, "run", fake_run)
    try:
        svc.run_iptables_restore("payload", test=True, noflush=True)
    except RuntimeError as exc:
        assert str(exc) == "real_iptables_restore_forbidden_in_ci"
    else:
        raise AssertionError("expected RuntimeError")
    assert called is False



def valid_customer(deleted_at=None, key="vahid-btc-real-60046", port=60046):
    return {"customer_key": key, "lane": "btc", "public_port": port, "status": "active", "deleted_at": deleted_at}


def valid_repo(deleted_at=None, extra_customers=None):
    customers = {"vahid-btc-real-60046": valid_customer(deleted_at)}
    if extra_customers:
        customers.update(extra_customers)
    return svc.StaticActivationRepository(
        customers=customers,
        lanes={"btc": {"enabled": True, "backend_port": 60010}},
        policies={"vahid-btc-real-60046": {"miners": 1, "farms": 1, "maxconn": 10, "rate": 60, "burst": 20}},
    )


def backend_ok():
    return {"resolved_ipv4": "172.18.0.2", "target_port": 60010, "backend_public_exposure": False, "forbidden_public_runtime_exposure": False}


def accepted_controlled_snapshot_text():
    return """*nat
:PREROUTING ACCEPT [0:0]
:MPF_NAT_PRE - [0:0]
:MPF_NAT_POST - [0:0]
:MPFL_btc - [0:0]
:MPFC_60046 - [0:0]
:MPFO_60046 - [0:0]
-A PREROUTING -m comment --comment "mpf:hook:nat_prerouting" -j MPF_NAT_PRE
-A MPF_NAT_PRE -p tcp --dport 60046 -m comment --comment "mpf:vahid-btc-real-60046:customer_nat_redirect" -j DNAT --to-destination 172.18.0.2:60010
COMMIT
*filter
:INPUT ACCEPT [0:0]
:MPF_INPUT - [0:0]
:MPF_CUSTOMERS - [0:0]
:MPF_GUARD - [0:0]
:MPF_ACCT - [0:0]
:MPF_ACCT_IN - [0:0]
:MPF_ACCT_OUT - [0:0]
-A INPUT -m comment --comment "mpf:hook:filter_input" -j MPF_INPUT
-A DOCKER-USER -m comment --comment "mpf:hook:verified_user_forward_post_dnat:customers" -j MPF_CUSTOMERS
-A MPF_CUSTOMERS -p tcp --dport 60046 -m comment --comment "mpf:vahid-btc-real-60046:dispatch" -j MPFC_60046
-A MPFC_60046 -m comment --comment "mpf:vahid-btc-real-60046:accounting" -j MPF_ACCT_IN
-A MPFC_60046 -m comment --comment "mpf:vahid-btc-real-60046:connlimit" -j RETURN
-A MPFC_60046 -m comment --comment "mpf:vahid-btc-real-60046:hashlimit" -j RETURN
-A MPF_ACCT_OUT -m comment --comment "MPF customer=vahid-btc-real-60046 port=60046" -j RETURN
COMMIT
"""


def clean_snapshot():
    return svc.snapshot_from_iptables_save(accepted_controlled_snapshot_text())


def test_deleted_at_nullish_values_do_not_mark_customer_deleted():
    for deleted_at in (None, "", "   ", "None", "null", "NULL"):
        report = svc.build_activation_package(valid_repo(deleted_at), "vahid-btc-real-60046", backend_resolver=backend_ok, live_snapshot=clean_snapshot())
        assert "customer_deleted" not in report["blockers"]


def test_deleted_at_real_timestamp_marks_customer_deleted():
    report = svc.build_activation_package(valid_repo("2026-06-18T00:00:00Z"), "vahid-btc-real-60046", backend_resolver=backend_ok, live_snapshot=clean_snapshot())
    assert "customer_deleted" in report["blockers"]


def test_active_port_conflict_deleted_at_normalization():
    conflict = {"other": valid_customer("", key="other", port=60046)}
    report = svc.build_activation_package(valid_repo("", conflict), "vahid-btc-real-60046", backend_resolver=backend_ok, live_snapshot=clean_snapshot())
    assert "duplicate_active_port_conflict" in report["blockers"]
    deleted_conflict = {"other": valid_customer("2026-06-18T00:00:00Z", key="other", port=60046)}
    report = svc.build_activation_package(valid_repo("", deleted_conflict), "vahid-btc-real-60046", backend_resolver=backend_ok, live_snapshot=clean_snapshot())
    assert "duplicate_active_port_conflict" not in report["blockers"]


def test_snapshot_accepts_controlled_phase11_generic_artifacts():
    snap = clean_snapshot()
    assert snap["unknown_mpf_artifacts"] == []
    for chain in ("MPF_CUSTOMERS", "MPF_NAT_PRE", "MPF_NAT_POST", "MPF_INPUT", "MPF_GUARD", "MPF_ACCT_IN", "MPF_ACCT_OUT", "MPFL_btc", "MPFC_60046", "MPFO_60046"):
        assert chain in snap["chains"]


def test_unknown_artifact_still_blocks_package_and_preflight():
    snap = svc.snapshot_from_iptables_save(accepted_controlled_snapshot_text() + "\n:MPF_UNKNOWN_CHAIN - [0:0]\n-A MPF_UNKNOWN_CHAIN -m comment --comment \"mpf:unknown-action\" -j RETURN\n")
    assert snap["unknown_mpf_artifacts"]
    report = svc.build_activation_package(valid_repo(""), "vahid-btc-real-60046", backend_resolver=backend_ok, live_snapshot=snap)
    assert "unknown_live_mpf_artifact" in report["blockers"]
    package = pkg(port=60046, key="vahid-btc-real-60046")
    preflight = svc.preflight_activation_package(package, live_snapshot=snap, confirmed_package_sha256="sha", operator_context="operator-reviewed")
    assert "unknown_live_mpf_artifact" in preflight["blockers"]


def test_generic_real_customer_package_ready_for_valid_db_backed_case():
    report = svc.build_activation_package(valid_repo(""), "vahid-btc-real-60046", backend_resolver=backend_ok, live_snapshot=clean_snapshot())
    assert report["final_decision"] == "GENERIC_REAL_CUSTOMER_ACTIVATION_PACKAGE_READY"
    assert report["production_generic_real_customer_activation"] == svc.PACKAGE_READY
    assert report["blockers"] == []


def test_generic_real_customer_preflight_ready_for_valid_package():
    package_report = svc.build_activation_package(valid_repo(""), "vahid-btc-real-60046", backend_resolver=backend_ok, live_snapshot=clean_snapshot())
    preflight = svc.preflight_activation_package(package_report["package"], live_snapshot=clean_snapshot(), confirmed_package_sha256=package_report["package"]["package_sha256"], operator_context="operator-reviewed")
    assert preflight["final_decision"] == "GENERIC_REAL_CUSTOMER_ACTIVATION_PREFLIGHT_READY"
    assert preflight["production_generic_real_customer_activation"] == svc.PREFLIGHT_READY
    assert preflight["blockers"] == []


def test_package_and_preflight_alone_do_not_mark_full_readiness_ready():
    package_report = svc.build_activation_package(valid_repo(""), "vahid-btc-real-60046", backend_resolver=backend_ok, live_snapshot=clean_snapshot())
    preflight = svc.preflight_activation_package(package_report["package"], live_snapshot=clean_snapshot(), confirmed_package_sha256=package_report["package"]["package_sha256"], operator_context="operator-reviewed")
    readiness = svc.readiness_from_evidence(package=package_report, preflight=preflight, activation_mode="first_connect")
    assert readiness["production_generic_real_customer_activation"] == svc.MISSING
    assert readiness["final_decision"] == "BLOCKED_PRODUCTION_GENERIC_REAL_CUSTOMER_ACTIVATION_EVIDENCE"


def test_phase11_docs_guard_ten_item_matrix_mentions_generic_before_final_acceptance():
    gate = Path("docs/PHASE_11_OPERATIONAL_COMPLETION_GATE.md").read_text()
    agents = Path("AGENTS.md").read_text()
    for text in (gate, agents):
        generic = text.index("production generic real-customer activation")
        final = text.index("final acceptance")
        assert generic < final
        assert "10-item" in text
        assert "production_generic_real_customer_activation" in text

def test_no_hardcoded_controlled_paths_in_generic_service():
    text=Path('mpf/services/phase11_generic_real_customer_activation_service.py').read_text()
    for forbidden in ('20001','20101','60045','canary-btc-001','limited-btc-001'):
        assert forbidden not in text
