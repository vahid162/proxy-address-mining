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


def test_no_hardcoded_controlled_paths_in_generic_service():
    text=Path('mpf/services/phase11_generic_real_customer_activation_service.py').read_text()
    for forbidden in ('20001','20101','60045','canary-btc-001','limited-btc-001'):
        assert forbidden not in text
