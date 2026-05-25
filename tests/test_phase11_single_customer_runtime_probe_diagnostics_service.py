from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services import customer_read_service
from mpf.services import phase11_single_customer_runtime_probe_diagnostics_service as svc


def _cfg(): return load_config(Path("configs/mpf.example.yaml"))
def _sha(p: Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def _w(p: Path, t: str): p.write_text(t, encoding="utf-8"); return p


def _rows(*rows):
    return customer_read_service.CustomerList(ok=True, message="ok", customers=list(rows))


def _row(status="paused", key="limited-btc-001", lane="btc", port=20101):
    return SimpleNamespace(customer_key=key, lane=lane, port=port, status=status)


def _files(tmp: Path, *, conn: str, fwd: str, bridge: str, live: str | None = None, post_obj: object | None = None):
    post_obj = post_obj if post_obj is not None else {
        "final_decision": "PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY", "post_apply_evidence_ready": True,
        "controlled_apply_recorded": True, "production_traffic_enabled": False, "miner_traffic_allowed": False,
        "phase11_accepted": False, "db_activation_allowed": False, "mutation_performed": False,
        "candidate_customer_key": "limited-btc-001", "candidate_lane": "btc", "candidate_public_port": 20101,
        "candidate_backend_target": "172.18.0.3:60010",
    }
    live = live or ":MPFC_20001 - [0:0]\n:MPFC_20101 - [0:0]\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20001 -m comment --comment mpf:canary-btc-001 -j DNAT --to-destination 172.18.0.3:60010\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20101 -m comment --comment mpf:limited-btc-001 -j DNAT --to-destination 172.18.0.3:60010\n-A MPFC_20001 -p tcp -m tcp --dport 20001 -m comment --comment canary-btc-001 -j REJECT\n-A MPFC_20101 -p tcp -m tcp --dport 20101 -m connlimit --connlimit-above 10 -m comment --comment mpf:limited-btc-001:customer_connlimit_reject -j REJECT\n-A MPFC_20101 -p tcp -m tcp --dport 20101 -m hashlimit --hashlimit-upto 100/min --hashlimit-burst 100 --hashlimit-mode srcip --hashlimit-name x -m comment --comment mpf:limited-btc-001:customer_hashlimit_reject -j REJECT"
    return (
        _w(tmp / "post.json", json.dumps(post_obj)), _w(tmp / "live.txt", live),
        _w(tmp / "conn.txt", conn), _w(tmp / "fwd.txt", fwd), _w(tmp / "bridge.txt", bridge)
    )


def _run(tmp: Path, monkeypatch, patch_db: bool = True, **overrides):
    if patch_db:
        monkeypatch.setattr(customer_read_service, "list_customer_status", lambda *a, **k: _rows(_row()))
    conn = overrides.pop("conn", "tcp SYN_SENT src=172.18.0.2 dport=20101 [UNREPLIED] src=172.18.0.3 sport=60010")
    fwd = overrides.pop("fwd", "limited-btc-001 20101 172.18.0.3:60010 127.0.0.1:60010")
    bridge = overrides.pop("bridge", "127.0.0.1:20170 -> 172.18.0.3 172.18.0.3:60010")
    live = overrides.pop("live", None)
    post_obj = overrides.pop("post_obj", None)
    post, livef, connf, fwdf, bridgef = _files(tmp, conn=conn, fwd=fwd, bridge=bridge, live=live, post_obj=post_obj)
    kw = dict(
        expected_version="0.1.209", post_apply_evidence_json=post, post_apply_evidence_json_sha256=_sha(post),
        live_snapshot_file=livef, live_snapshot_sha256=_sha(livef), conntrack_snapshot_file=connf, conntrack_snapshot_sha256=_sha(connf),
        forwarder_log_file=fwdf, forwarder_log_sha256=_sha(fwdf), bridge_log_file=bridgef, bridge_log_sha256=_sha(bridgef),
        operator="op", reason="r", operator_confirmed=True, i_understand_probe_diagnostics_only=True,
        i_understand_no_runtime_acceptance=True, i_understand_no_production_traffic_acceptance=True,
        i_understand_no_miner_traffic_acceptance=True, i_understand_no_db_activation=True,
        i_confirm_stratum_transcript_required=True, i_confirm_visibility_bundle_required=True,
        i_confirm_abuse_1h_required_before_customer_traffic=True,
        i_confirm_restart_container_order_required_before_limited_acceptance=True,
    )
    kw.update(overrides)
    return svc.build_phase11_single_customer_runtime_probe_diagnostics_report(_cfg(), **kw)


def test_syn_unreplied_ready_blocked_runtime(tmp_path, monkeypatch):
    r = _run(tmp_path, monkeypatch)
    assert r["final_decision"] == "PHASE11_SINGLE_CUSTOMER_RUNTIME_PROBE_DIAGNOSTICS_READY_BLOCKED_RUNTIME"
    assert r["probe_diagnostics_ready"] is True and r["runtime_path_evidence_ready"] is False and r["blockers"] == []
    assert r["conntrack_20101_unreplied_seen"] is True and r["conntrack_backend_nat_seen"] is True and r["conntrack_assured_seen"] is False


def test_assured_ready_candidate(tmp_path, monkeypatch):
    r = _run(tmp_path, monkeypatch, conn="tcp ASSURED dport=20101 src=172.18.0.3 sport=60010")
    assert r["final_decision"] == "PHASE11_SINGLE_CUSTOMER_RUNTIME_PROBE_DIAGNOSTICS_READY_ASSURED_CANDIDATE"
    assert r["probe_diagnostics_ready"] is True and r["runtime_path_evidence_ready"] is False and r["blockers"] == []


def test_assured_missing_forwarder_blocked(tmp_path, monkeypatch):
    r = _run(tmp_path, monkeypatch, conn="tcp ASSURED dport=20101 src=172.18.0.3 sport=60010", fwd="no signal")
    assert r["final_decision"] == "BLOCKED" and "missing_forwarder_probe_signal" in r["blockers"]


def test_assured_missing_bridge_blocked(tmp_path, monkeypatch):
    r = _run(tmp_path, monkeypatch, conn="tcp ASSURED dport=20101 src=172.18.0.3 sport=60010", bridge="none")
    assert r["final_decision"] == "BLOCKED" and "missing_bridge_probe_signal" in r["blockers"]


def test_no_conntrack_signal_blocked(tmp_path, monkeypatch):
    r = _run(tmp_path, monkeypatch, conn="random no 20101")
    assert r["final_decision"] == "BLOCKED" and "missing_conntrack_probe_signal" in r["blockers"]


def test_invalid_and_non_object_post_json(tmp_path, monkeypatch):
    monkeypatch.setattr(customer_read_service, "list_customer_status", lambda *a, **k: _rows(_row()))
    post, livef, connf, fwdf, brf = _files(tmp_path, conn="x", fwd="x", bridge="x")
    post.write_text("{")
    r = svc.build_phase11_single_customer_runtime_probe_diagnostics_report(_cfg(), post_apply_evidence_json=post, post_apply_evidence_json_sha256="x", live_snapshot_file=livef, conntrack_snapshot_file=connf, forwarder_log_file=fwdf, bridge_log_file=brf)
    assert "post_apply_evidence_json_invalid" in r["blockers"]
    post.write_text("[1]")
    r2 = svc.build_phase11_single_customer_runtime_probe_diagnostics_report(_cfg(), post_apply_evidence_json=post, post_apply_evidence_json_sha256="x", live_snapshot_file=livef, conntrack_snapshot_file=connf, forwarder_log_file=fwdf, bridge_log_file=brf)
    assert "post_apply_evidence_json_invalid" in r2["blockers"]


def test_hash_mismatch_blockers(tmp_path, monkeypatch):
    r = _run(tmp_path, monkeypatch, post_apply_evidence_json_sha256="bad", live_snapshot_sha256="bad", conntrack_snapshot_sha256="bad", forwarder_log_sha256="bad", bridge_log_sha256="bad")
    for b in ("post_apply_evidence_json_hash_mismatch", "live_snapshot_hash_mismatch", "conntrack_snapshot_hash_mismatch", "forwarder_log_hash_mismatch", "bridge_log_hash_mismatch"):
        assert b in r["blockers"]


def test_live_snapshot_failures(tmp_path, monkeypatch):
    assert "live_snapshot_missing_20101" in _run(tmp_path, monkeypatch, live="-A PREROUTING -p tcp --dport 20001")["blockers"]
    dup = ":MPFC_20001 - [0:0]\n:MPFC_20101 - [0:0]\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20001 -m comment --comment mpf:canary-btc-001 -j DNAT --to-destination 172.18.0.3:60010\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20101 -m comment --comment mpf:limited-btc-001 -j DNAT --to-destination 172.18.0.3:60010\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20101 -m comment --comment mpf:limited-btc-001 -j DNAT --to-destination 172.18.0.3:60010\n-A MPFC_20101 -p tcp -m tcp --dport 20101 -m connlimit --connlimit-above 10 -m comment --comment mpf:limited-btc-001:customer_connlimit_reject -j REJECT\n-A MPFC_20101 -p tcp -m tcp --dport 20101 -m hashlimit --hashlimit-upto 100/min --hashlimit-burst 100 --hashlimit-mode srcip --hashlimit-name x -m comment --comment mpf:limited-btc-001:customer_hashlimit_reject -j REJECT"
    assert "live_snapshot_duplicate_20101" in _run(tmp_path, monkeypatch, live=dup)["blockers"]
    loop = ":MPFC_20001 - [0:0]\n:MPFC_20101 - [0:0]\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20001 -m comment --comment mpf:canary-btc-001 -j DNAT --to-destination 172.18.0.3:60010\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20101 -m comment --comment mpf:limited-btc-001 -j DNAT --to-destination 127.0.0.1:60010\n-A MPFC_20101 -p tcp -m tcp --dport 20101 -m connlimit --connlimit-above 10 -m comment --comment mpf:limited-btc-001:customer_connlimit_reject -j REJECT\n-A MPFC_20101 -p tcp -m tcp --dport 20101 -m hashlimit --hashlimit-upto 100/min --hashlimit-burst 100 --hashlimit-mode srcip --hashlimit-name x -m comment --comment mpf:limited-btc-001:customer_hashlimit_reject -j REJECT"
    assert "live_snapshot_loopback_20101" in _run(tmp_path, monkeypatch, live=loop)["blockers"]
    unr = ":MPFC_20001 - [0:0]\n:MPFC_20101 - [0:0]\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20001 -m comment --comment mpf:canary-btc-001 -j DNAT --to-destination 172.18.0.3:60010\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20101 -m comment --comment mpf:limited-btc-001 -j DNAT --to-destination 172.18.0.3:60010\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20222 -m comment --comment mpf:other-customer -j DNAT --to-destination 172.18.0.3:60010\n-A MPFC_20101 -p tcp -m tcp --dport 20101 -m connlimit --connlimit-above 10 -m comment --comment mpf:limited-btc-001:customer_connlimit_reject -j REJECT\n-A MPFC_20101 -p tcp -m tcp --dport 20101 -m hashlimit --hashlimit-upto 100/min --hashlimit-burst 100 --hashlimit-mode srcip --hashlimit-name x -m comment --comment mpf:limited-btc-001:customer_hashlimit_reject -j REJECT"
    assert "live_snapshot_unrelated_customer_nat" in _run(tmp_path, monkeypatch, live=unr)["blockers"]
    nof = ":MPFC_20001 - [0:0]\n:MPFC_20101 - [0:0]\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20001 -m comment --comment mpf:canary-btc-001 -j DNAT --to-destination 172.18.0.3:60010\n-A MPF_NAT_PRE -p tcp -m tcp --dport 20101 -m comment --comment mpf:limited-btc-001 -j DNAT --to-destination 172.18.0.3:60010"
    assert "live_snapshot_invalid" in _run(tmp_path, monkeypatch, live=nof)["blockers"]


def test_db_failures(tmp_path, monkeypatch):
    monkeypatch.setattr(customer_read_service, "list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=False, message="x", customers=[]))
    assert "db_read_failed" in _run(tmp_path, monkeypatch, patch_db=False)["blockers"]
    monkeypatch.setattr(customer_read_service, "list_customer_status", lambda *a, **k: _rows())
    assert "db_candidate_not_exactly_once" in _run(tmp_path, monkeypatch, patch_db=False)["blockers"]
    monkeypatch.setattr(customer_read_service, "list_customer_status", lambda *a, **k: _rows(_row(status="active")))
    assert "db_candidate_state_invalid" in _run(tmp_path, monkeypatch, patch_db=False)["blockers"]


def test_missing_confirmations_and_safety_flags(tmp_path, monkeypatch):
    r = _run(tmp_path, monkeypatch, operator_confirmed=False, i_understand_probe_diagnostics_only=False, i_understand_no_runtime_acceptance=False)
    assert "operator_not_confirmed" in r["blockers"]
    assert "probe_diagnostics_only_not_confirmed" in r["blockers"]
    assert "no_runtime_acceptance_not_confirmed" in r["blockers"]
    for k in ("production_traffic_enabled", "miner_traffic_allowed", "phase11_accepted", "db_activation_allowed", "mutation_performed"):
        assert r[k] is False
    assert r["runtime_path_evidence_ready"] is False
    if r["final_decision"] == "BLOCKED":
        assert r["blockers"]


def test_cli_smoke_json_human_and_hash_options(tmp_path, monkeypatch):
    monkeypatch.setattr(customer_read_service, "list_customer_status", lambda *a, **k: _rows(_row()))
    post, livef, connf, fwdf, brf = _files(tmp_path, conn="tcp SYN_SENT dport=20101 [UNREPLIED] src=172.18.0.3 sport=60010", fwd="limited-btc-001 20101 172.18.0.3:60010", bridge="127.0.0.1:20170 172.18.0.3")
    base = [
        "production", "single-customer-runtime-probe-diagnostics", "--expected-version", "0.1.209", "--post-apply-evidence-json", str(post),
        "--post-apply-evidence-json-sha256", _sha(post), "--live-snapshot-file", str(livef), "--live-snapshot-sha256", _sha(livef),
        "--conntrack-snapshot-file", str(connf), "--conntrack-snapshot-sha256", _sha(connf), "--forwarder-log-file", str(fwdf),
        "--forwarder-log-sha256", _sha(fwdf), "--bridge-log-file", str(brf), "--bridge-log-sha256", _sha(brf), "--operator", "x", "--reason", "y",
        "--operator-confirmed", "--i-understand-probe-diagnostics-only", "--i-understand-no-runtime-acceptance",
        "--i-understand-no-production-traffic-acceptance", "--i-understand-no-miner-traffic-acceptance", "--i-understand-no-db-activation",
        "--i-confirm-stratum-transcript-required", "--i-confirm-visibility-bundle-required", "--i-confirm-abuse-1h-required-before-customer-traffic",
        "--i-confirm-restart-container-order-required-before-limited-acceptance", "--config", "configs/mpf.example.yaml",
    ]
    runner = CliRunner()
    assert runner.invoke(app, base + ["--output", "json"]).exit_code == 0
    assert runner.invoke(app, base + ["--output", "human"]).exit_code == 0
