from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services import customer_read_service
from mpf.services.phase11_single_customer_post_apply_evidence_service import build_phase11_single_customer_post_apply_evidence_report


def _cfg():
    return load_config(Path("configs/mpf.example.yaml"))


def _rows(*r):
    return customer_read_service.CustomerList(ok=True, message="ok", customers=list(r))


def _staged(status="paused", lane="btc", port=20101, key="limited-btc-001"):
    return SimpleNamespace(customer_key=key, lane=lane, port=port, status=status)


def _pre():
    return "*nat\n:MPF_NAT_PRE - [0:0]\n-A MPF_NAT_PRE -p tcp -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" --dport 20001 -j DNAT --to-destination 172.18.0.3:60010\n*filter\n:MPFC_20001 - [0:0]\n"


def _post(extra=""):
    return _pre() + ":MPFC_20101 - [0:0]\n-A MPF_NAT_PRE -p tcp -m comment --comment \"mpf:limited-btc-001:customer_nat_redirect\" --dport 20101 -j DNAT --to-destination 172.18.0.3:60010\n-A MPFC_20101 -p tcp --dport 20101 -m connlimit --connlimit-above 120 -m comment --comment \"mpf:limited-btc-001:customer_connlimit_reject\" -j REJECT\n-A MPFC_20101 -p tcp --dport 20101 -m hashlimit --hashlimit-above 40/sec --hashlimit-burst 80 --hashlimit-mode srcip --hashlimit-name mpf_20101 -m comment --comment \"mpf:limited-btc-001:customer_hashlimit_reject\" -j REJECT\n" + extra


def _write(tmp, n, t):
    p = tmp / n
    p.write_text(t)
    return p


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _exec(**u):
    d = {
        "final_decision": "PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_EXECUTED_PENDING_REVIEW",
        "execute_requested": True,
        "apply_execution_ready": True,
        "firewall_apply_execution_allowed": True,
        "iptables_restore_authorized": True,
        "mutation_performed": True,
        "firewall_mutation_performed": True,
        "nat_mutation_performed": True,
        "blockers": [],
        "warnings": [],
        "next_required_step": "phase11e_post_apply_runtime_evidence_pr",
        "candidate_customer_key": "limited-btc-001",
        "candidate_lane": "btc",
        "candidate_public_port": 20101,
        "candidate_backend_target": "172.18.0.3:60010",
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "phase11_accepted": False,
        "post_apply_verification": {
            "mpf_nat_pre_exists": True,
            "mpfc_20001_exists": True,
            "mpfc_20101_exists": True,
            "canary_20001_exact_artifact_preserved": True,
            "dnat_20101_exact_target_count": 1,
            "dnat_20101_loopback_count": 0,
            "unrelated_customer_nat_rule_count": 0,
            "limited_20101_connlimit_reject_rule_count": 1,
            "limited_20101_hashlimit_reject_rule_count": 1,
            "limited_20101_filter_primitives_verified": True,
        },
    }
    d.update(u)
    return d


def _apply_gate_fixture():
    return {
        "component": "phase11_single_customer_firewall_apply_gate",
        "expected_version": "0.1.203",
        "candidate_customer_key": "limited-btc-001",
        "candidate_lane": "btc",
        "candidate_public_port": 20101,
        "candidate_backend_target": "172.18.0.3:60010",
        "final_decision": "PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_GATE_READY",
        "blockers": [],
        "warnings": [],
    }


def _plan_gate_fixture():
    return {
        "component": "phase11_single_customer_firewall_plan_gate",
        "expected_version": "0.1.202",
        "candidate_customer_key": "limited-btc-001",
        "candidate_lane": "btc",
        "candidate_public_port": 20101,
        "candidate_backend_target": "172.18.0.3:60010",
        "final_decision": "PHASE11_SINGLE_CUSTOMER_FIREWALL_PLAN_GATE_READY",
        "blockers": [],
        "warnings": [],
    }


def _kw(tmp, **u):
    e = _write(tmp, "e.json", json.dumps(_exec()))
    pre = _write(tmp, "pre.txt", _pre())
    post = _write(tmp, "post.txt", _post())
    a = _write(tmp, "a.json", json.dumps(_apply_gate_fixture()))
    p = _write(tmp, "p.json", json.dumps(_plan_gate_fixture()))
    d = dict(
        execution_json=e,
        execution_json_sha256=_sha(e),
        pre_apply_snapshot_file=pre,
        pre_apply_snapshot_sha256=_sha(pre),
        post_apply_snapshot_file=post,
        post_apply_snapshot_sha256=_sha(post),
        apply_gate_json=a,
        apply_gate_json_sha256=_sha(a),
        plan_gate_json=p,
        plan_gate_json_sha256=_sha(p),
        operator="vahid",
        reason="ok",
        operator_confirmed=True,
        i_understand_post_apply_evidence_only=True,
        i_understand_no_additional_firewall_apply=True,
        i_understand_no_production_traffic_acceptance=True,
        i_understand_no_miner_traffic_acceptance=True,
        i_confirm_runtime_path_evidence_required_next=True,
        i_confirm_stratum_transcript_required_next=True,
        i_confirm_visibility_bundle_required_next=True,
        i_confirm_abuse_1h_required_before_customer_traffic=True,
        i_confirm_restart_container_order_required_before_limited_acceptance=True,
    )
    d.update(u)
    return d


def _run(tmp, mp, **u):
    mp.setattr(customer_read_service, "list_customer_status", lambda *a, **k: _rows(_staged()))
    return build_phase11_single_customer_post_apply_evidence_report(_cfg(), **_kw(tmp, **u))


def test_01_ready(tmp_path, monkeypatch): assert _run(tmp_path, monkeypatch)["final_decision"] == "PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY"
def test_02_missing_exec(tmp_path, monkeypatch): assert "execution_json_missing" in _run(tmp_path, monkeypatch, execution_json=tmp_path / "x")["blockers"]
def test_03_invalid_exec(tmp_path, monkeypatch): p = _write(tmp_path, "bad.json", "{"); assert "execution_json_invalid" in _run(tmp_path, monkeypatch, execution_json=p)["blockers"]
def test_04_exec_hash_mismatch(tmp_path, monkeypatch): assert "execution_json_hash_mismatch" in _run(tmp_path, monkeypatch, execution_json_sha256="x")["blockers"]
def test_05_exec_not_success(tmp_path, monkeypatch): p = _write(tmp_path, "e2.json", json.dumps(_exec(final_decision="X"))); assert "execution_json_not_success" in _run(tmp_path, monkeypatch, execution_json=p, execution_json_sha256=_sha(p))["blockers"]
def test_06_scope_mismatch(tmp_path, monkeypatch): p = _write(tmp_path, "e3.json", json.dumps(_exec(candidate_lane="zec"))); assert "execution_json_scope_mismatch" in _run(tmp_path, monkeypatch, execution_json=p, execution_json_sha256=_sha(p))["blockers"]
def test_07_safety_open(tmp_path, monkeypatch): p = _write(tmp_path, "e4.json", json.dumps(_exec(blockers=["x"]))); assert "execution_json_safety_boundary_open" in _run(tmp_path, monkeypatch, execution_json=p, execution_json_sha256=_sha(p))["blockers"]
def test_08_missing_post_apply_verification(tmp_path, monkeypatch): p = _write(tmp_path, "e5.json", json.dumps(_exec(post_apply_verification=None))); assert "execution_json_post_apply_verification_missing" in _run(tmp_path, monkeypatch, execution_json=p, execution_json_sha256=_sha(p))["blockers"]
def test_09_failed_post_apply_verification(tmp_path, monkeypatch): p = _write(tmp_path, "e6.json", json.dumps(_exec(post_apply_verification={}))); assert "execution_json_post_apply_verification_failed" in _run(tmp_path, monkeypatch, execution_json=p, execution_json_sha256=_sha(p))["blockers"]
def test_10_pre_hash_mismatch(tmp_path, monkeypatch): assert "pre_apply_snapshot_hash_mismatch" in _run(tmp_path, monkeypatch, pre_apply_snapshot_sha256="x")["blockers"]
def test_11_post_hash_mismatch(tmp_path, monkeypatch): assert "post_apply_snapshot_hash_mismatch" in _run(tmp_path, monkeypatch, post_apply_snapshot_sha256="x")["blockers"]
def test_12_pre_has_20101(tmp_path, monkeypatch): p = _write(tmp_path, "pre2.txt", _post()); assert "pre_apply_snapshot_unexpected_20101_present" in _run(tmp_path, monkeypatch, pre_apply_snapshot_file=p, pre_apply_snapshot_sha256=_sha(p))["blockers"]
def test_13_post_missing_20101(tmp_path, monkeypatch): p = _write(tmp_path, "post2.txt", _pre()); assert "post_apply_snapshot_missing_20101" in _run(tmp_path, monkeypatch, post_apply_snapshot_file=p, post_apply_snapshot_sha256=_sha(p))["blockers"]
def test_14_post_missing_canary(tmp_path, monkeypatch): p = _write(tmp_path, "post3.txt", ":MPFC_20101\n"); assert "post_apply_snapshot_missing_canary_20001" in _run(tmp_path, monkeypatch, post_apply_snapshot_file=p, post_apply_snapshot_sha256=_sha(p))["blockers"]
def test_15_post_duplicate_20101(tmp_path, monkeypatch): p = _write(tmp_path, "post4.txt", _post("\n-A MPF_NAT_PRE -p tcp -m comment --comment \"mpf:limited-btc-001:customer_nat_redirect\" --dport 20101 -j DNAT --to-destination 172.18.0.3:60010")); assert "post_apply_snapshot_duplicate_20101" in _run(tmp_path, monkeypatch, post_apply_snapshot_file=p, post_apply_snapshot_sha256=_sha(p))["blockers"]
def test_16_post_loopback_20101(tmp_path, monkeypatch): p = _write(tmp_path, "post5.txt", _post("\n-A MPF_NAT_PRE -p tcp --dport 20101 -j DNAT --to-destination 127.0.0.1:60010")); assert "post_apply_snapshot_loopback_20101" in _run(tmp_path, monkeypatch, post_apply_snapshot_file=p, post_apply_snapshot_sha256=_sha(p))["blockers"]
def test_17_unrelated_nat(tmp_path, monkeypatch): p = _write(tmp_path, "post6.txt", _post("\n-A MPF_NAT_PRE -p tcp -m comment --comment \"mpf:other:customer_nat_redirect\" --dport 30000 -j DNAT --to-destination 1.1.1.1:1")); assert "post_apply_snapshot_unrelated_customer_nat" in _run(tmp_path, monkeypatch, post_apply_snapshot_file=p, post_apply_snapshot_sha256=_sha(p))["blockers"]
def test_18_db_fail(tmp_path, monkeypatch): monkeypatch.setattr(customer_read_service, "list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=False, message="x", customers=[])); assert "db_read_failed" in build_phase11_single_customer_post_apply_evidence_report(_cfg(), **_kw(tmp_path))["blockers"]
def test_19_missing_customer(tmp_path, monkeypatch): monkeypatch.setattr(customer_read_service, "list_customer_status", lambda *a, **k: _rows()); assert "staged_customer_missing" in build_phase11_single_customer_post_apply_evidence_report(_cfg(), **_kw(tmp_path))["blockers"]
def test_20_duplicate_customer(tmp_path, monkeypatch): monkeypatch.setattr(customer_read_service, "list_customer_status", lambda *a, **k: _rows(_staged(), _staged())); assert "staged_customer_duplicate" in build_phase11_single_customer_post_apply_evidence_report(_cfg(), **_kw(tmp_path))["blockers"]
def test_21_wrong_lane_port(tmp_path, monkeypatch): monkeypatch.setattr(customer_read_service, "list_customer_status", lambda *a, **k: _rows(_staged(lane="zec"))); assert "staged_customer_scope_mismatch" in build_phase11_single_customer_post_apply_evidence_report(_cfg(), **_kw(tmp_path))["blockers"]
def test_22_not_paused(tmp_path, monkeypatch): monkeypatch.setattr(customer_read_service, "list_customer_status", lambda *a, **k: _rows(_staged(status="active"))); assert "staged_customer_not_paused" in build_phase11_single_customer_post_apply_evidence_report(_cfg(), **_kw(tmp_path))["blockers"]
def test_23_port_collision(tmp_path, monkeypatch): monkeypatch.setattr(customer_read_service, "list_customer_status", lambda *a, **k: _rows(_staged(), _staged(key="x"))); assert "candidate_port_collision" in build_phase11_single_customer_post_apply_evidence_report(_cfg(), **_kw(tmp_path))["blockers"]
def test_24_missing_operator(tmp_path, monkeypatch): assert "operator_not_confirmed" in _run(tmp_path, monkeypatch, operator_confirmed=False)["blockers"]
def test_25_missing_evidence_only_confirm(tmp_path, monkeypatch): assert "post_apply_evidence_only_not_confirmed" in _run(tmp_path, monkeypatch, i_understand_post_apply_evidence_only=False)["blockers"]
def test_26_missing_no_additional_apply_confirm(tmp_path, monkeypatch): assert "no_additional_firewall_apply_not_confirmed" in _run(tmp_path, monkeypatch, i_understand_no_additional_firewall_apply=False)["blockers"]
def test_27_missing_remaining_confirms(tmp_path, monkeypatch): r = _run(tmp_path, monkeypatch, i_confirm_runtime_path_evidence_required_next=False, i_confirm_stratum_transcript_required_next=False, i_confirm_visibility_bundle_required_next=False, i_confirm_abuse_1h_required_before_customer_traffic=False, i_confirm_restart_container_order_required_before_limited_acceptance=False); assert "runtime_path_required_not_confirmed" in r["blockers"]
def test_28_live_snapshot_match(tmp_path, monkeypatch): p = _write(tmp_path, "live.txt", _post()); assert _run(tmp_path, monkeypatch, live_snapshot_file=p)["final_decision"] == "PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY"
def test_29_live_mismatch_blocks(tmp_path, monkeypatch): p = _write(tmp_path, "live2.txt", _pre()); assert "live_snapshot_mismatch" in _run(tmp_path, monkeypatch, live_snapshot_file=p)["blockers"]
def test_30_output_never_authorizes(tmp_path, monkeypatch): r = _run(tmp_path, monkeypatch); assert r["production_traffic_enabled"] is False and r["miner_traffic_allowed"] is False and r["phase11_accepted"] is False and r["additional_firewall_apply_allowed"] is False
def test_31_apply_gate_missing(tmp_path, monkeypatch): assert "apply_gate_json_missing" in _run(tmp_path, monkeypatch, apply_gate_json=tmp_path / "z")["blockers"]
def test_32_apply_gate_hash_mismatch(tmp_path, monkeypatch): assert "apply_gate_json_hash_mismatch" in _run(tmp_path, monkeypatch, apply_gate_json_sha256="x")["blockers"]
def test_33_plan_gate_missing(tmp_path, monkeypatch): assert "plan_gate_json_missing" in _run(tmp_path, monkeypatch, plan_gate_json=tmp_path / "z")["blockers"]
def test_34_plan_gate_hash_mismatch(tmp_path, monkeypatch): assert "plan_gate_json_hash_mismatch" in _run(tmp_path, monkeypatch, plan_gate_json_sha256="x")["blockers"]
def test_35_wrong_candidate_input(tmp_path, monkeypatch): assert "candidate_scope_mismatch" in _run(tmp_path, monkeypatch, candidate_lane="zec")["blockers"]
def test_36_post_missing_connlimit(tmp_path, monkeypatch): p = _write(tmp_path, "post7.txt", _post().replace("customer_connlimit_reject", "x")); assert "post_apply_snapshot_missing_filter_primitives" in _run(tmp_path, monkeypatch, post_apply_snapshot_file=p, post_apply_snapshot_sha256=_sha(p))["blockers"]
def test_37_post_missing_hashlimit(tmp_path, monkeypatch): p = _write(tmp_path, "post8.txt", _post().replace("customer_hashlimit_reject", "x")); assert "post_apply_snapshot_missing_filter_primitives" in _run(tmp_path, monkeypatch, post_apply_snapshot_file=p, post_apply_snapshot_sha256=_sha(p))["blockers"]
def test_38_pre_missing_canary(tmp_path, monkeypatch): p = _write(tmp_path, "pre3.txt", "*nat\n"); assert "pre_apply_snapshot_missing_canary_20001" in _run(tmp_path, monkeypatch, pre_apply_snapshot_file=p, pre_apply_snapshot_sha256=_sha(p))["blockers"]


def test_39_cli_json(tmp_path, monkeypatch):
    monkeypatch.setattr(customer_read_service, "list_customer_status", lambda *a, **k: _rows(_staged()))
    d = _kw(tmp_path)
    r = CliRunner().invoke(app, [
        "production", "single-customer-post-apply-evidence",
        "--execution-json", str(d["execution_json"]), "--execution-json-sha256", d["execution_json_sha256"],
        "--pre-apply-snapshot-file", str(d["pre_apply_snapshot_file"]), "--pre-apply-snapshot-sha256", d["pre_apply_snapshot_sha256"],
        "--post-apply-snapshot-file", str(d["post_apply_snapshot_file"]), "--post-apply-snapshot-sha256", d["post_apply_snapshot_sha256"],
        "--apply-gate-json", str(d["apply_gate_json"]), "--apply-gate-json-sha256", d["apply_gate_json_sha256"],
        "--plan-gate-json", str(d["plan_gate_json"]), "--plan-gate-json-sha256", d["plan_gate_json_sha256"],
        "--operator", "vahid", "--reason", "ok", "--operator-confirmed",
        "--i-understand-post-apply-evidence-only", "--i-understand-no-additional-firewall-apply",
        "--i-understand-no-production-traffic-acceptance", "--i-understand-no-miner-traffic-acceptance",
        "--i-confirm-runtime-path-evidence-required-next", "--i-confirm-stratum-transcript-required-next",
        "--i-confirm-visibility-bundle-required-next", "--i-confirm-abuse-1h-required-before-customer-traffic",
        "--i-confirm-restart-container-order-required-before-limited-acceptance",
        "--output", "json", "--config", "configs/mpf.example.yaml",
    ])
    assert r.exit_code == 0


def test_40_cli_human(tmp_path, monkeypatch):
    monkeypatch.setattr(customer_read_service, "list_customer_status", lambda *a, **k: _rows(_staged()))
    d = _kw(tmp_path)
    r = CliRunner().invoke(app, [
        "production", "single-customer-post-apply-evidence",
        "--execution-json", str(d["execution_json"]), "--execution-json-sha256", d["execution_json_sha256"],
        "--pre-apply-snapshot-file", str(d["pre_apply_snapshot_file"]), "--pre-apply-snapshot-sha256", d["pre_apply_snapshot_sha256"],
        "--post-apply-snapshot-file", str(d["post_apply_snapshot_file"]), "--post-apply-snapshot-sha256", d["post_apply_snapshot_sha256"],
        "--apply-gate-json", str(d["apply_gate_json"]), "--apply-gate-json-sha256", d["apply_gate_json_sha256"],
        "--plan-gate-json", str(d["plan_gate_json"]), "--plan-gate-json-sha256", d["plan_gate_json_sha256"],
        "--operator", "vahid", "--reason", "ok", "--operator-confirmed",
        "--i-understand-post-apply-evidence-only", "--i-understand-no-additional-firewall-apply",
        "--i-understand-no-production-traffic-acceptance", "--i-understand-no-miner-traffic-acceptance",
        "--i-confirm-runtime-path-evidence-required-next", "--i-confirm-stratum-transcript-required-next",
        "--i-confirm-visibility-bundle-required-next", "--i-confirm-abuse-1h-required-before-customer-traffic",
        "--i-confirm-restart-container-order-required-before-limited-acceptance",
        "--output", "human", "--config", "configs/mpf.example.yaml",
    ])
    assert r.exit_code == 0
