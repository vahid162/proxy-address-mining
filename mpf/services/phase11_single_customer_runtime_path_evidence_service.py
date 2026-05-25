from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service
from mpf.services.phase11_single_customer_firewall_apply_gate_service import _read_live_snapshot
from mpf.services.phase11_single_customer_post_apply_evidence_service import _parse_snapshot

EXPECTED = {"customer_key": "limited-btc-001", "lane": "btc", "public_port": 20101, "backend_target": "172.18.0.3:60010"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def build_phase11_single_customer_runtime_path_evidence_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    blockers: list[str] = []
    expected_version = str(kwargs.get("expected_version", __version__))
    candidate_customer_key = str(kwargs.get("candidate_customer_key", EXPECTED["customer_key"]))
    candidate_lane = str(kwargs.get("candidate_lane", EXPECTED["lane"]))
    candidate_public_port = int(kwargs.get("candidate_public_port", EXPECTED["public_port"]))
    candidate_backend_target = str(kwargs.get("candidate_backend_target", EXPECTED["backend_target"]))

    confirmations = {
        "operator_confirmed": "operator_not_confirmed",
        "i_understand_runtime_evidence_only": "runtime_evidence_only_not_confirmed",
        "i_understand_no_production_traffic_acceptance": "no_production_traffic_not_confirmed",
        "i_understand_no_miner_traffic_acceptance": "no_miner_traffic_not_confirmed",
        "i_understand_no_db_activation": "no_db_activation_not_confirmed",
        "i_confirm_stratum_transcript_required": "stratum_transcript_required_not_confirmed",
        "i_confirm_visibility_bundle_required": "visibility_bundle_required_not_confirmed",
        "i_confirm_abuse_1h_required_before_customer_traffic": "abuse_1h_required_not_confirmed",
        "i_confirm_restart_container_order_required_before_limited_acceptance": "restart_container_order_required_not_confirmed",
    }
    for f, b in confirmations.items():
        if kwargs.get(f) is not True:
            blockers.append(b)

    if (candidate_customer_key, candidate_lane, candidate_public_port, candidate_backend_target) != (
        EXPECTED["customer_key"], EXPECTED["lane"], EXPECTED["public_port"], EXPECTED["backend_target"]
    ):
        blockers.append("candidate_scope_mismatch")

    post_apply_json = Path(str(kwargs.get("post_apply_evidence_json", "")))
    if not post_apply_json.exists():
        blockers.append("post_apply_evidence_json_missing")
        post = {}
    else:
        if _sha256(post_apply_json) != str(kwargs.get("post_apply_evidence_json_sha256", "")):
            blockers.append("post_apply_evidence_json_hash_mismatch")
        try:
            loaded = json.loads(post_apply_json.read_text(encoding="utf-8"))
        except Exception:
            loaded = None
            blockers.append("post_apply_evidence_json_invalid")
        if loaded is not None and not isinstance(loaded, dict):
            blockers.append("post_apply_evidence_json_invalid")
            post = {}
        else:
            post = loaded or {}

    if post:
        if post.get("final_decision") != "PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY":
            blockers.append("post_apply_evidence_not_ready")
        if post.get("controlled_apply_recorded") is not True:
            blockers.append("post_apply_evidence_not_ready")
        if (
            post.get("candidate_customer_key") != EXPECTED["customer_key"]
            or post.get("candidate_lane") != EXPECTED["lane"]
            or post.get("candidate_public_port") != EXPECTED["public_port"]
            or post.get("candidate_backend_target") != EXPECTED["backend_target"]
        ):
            blockers.append("post_apply_evidence_scope_mismatch")
        if post.get("blockers") != [] or post.get("warnings") != []:
            blockers.append("post_apply_evidence_safety_boundary_open")
        for flag in ("production_traffic_enabled", "miner_traffic_allowed", "phase11_accepted", "db_activation_allowed", "mutation_performed"):
            if post.get(flag) is not False:
                blockers.append("post_apply_evidence_safety_boundary_open")
                break
        if post.get("has_20101_chain") is not True or post.get("has_20101_ref") is not True:
            blockers.append("post_apply_evidence_not_ready")

    try:
        db = customer_read_service.list_customer_status(config, include_deleted=False, limit=5000)
    except Exception:
        db = customer_read_service.CustomerList(ok=False, message="exception", customers=[])
    if not db.ok:
        blockers.append("db_read_failed")
    else:
        rows = [r for r in db.customers if r.customer_key == EXPECTED["customer_key"]]
        if len(rows) != 1:
            blockers.append("db_candidate_not_exactly_once")
        elif rows[0].lane != EXPECTED["lane"] or rows[0].port != EXPECTED["public_port"] or str(rows[0].status).lower() != "paused":
            blockers.append("db_candidate_state_invalid")

    live_snapshot_file = kwargs.get("live_snapshot_file")
    collect_live = bool(kwargs.get("collect_live", False))
    if live_snapshot_file or collect_live:
        try:
            snap = _read_live_snapshot(Path(str(live_snapshot_file)) if live_snapshot_file else None, collect_live, kwargs.get("live_snapshot_reader"))
            cls = _parse_snapshot(snap)
            if not cls.get("has_canary_20001"):
                blockers.append("missing_canary_20001")
            if int(cls.get("dnat_20101_exact_target_count", 0)) != 1:
                blockers.append("dnat_20101_count_invalid")
            if int(cls.get("dnat_20101_loopback_count", 0)) != 0:
                blockers.append("dnat_20101_loopback_detected")
            if int(cls.get("unrelated_customer_nat_rule_count", 0)) != 0:
                blockers.append("unrelated_customer_nat_detected")
            if cls.get("limited_20101_filter_primitives_verified") is not True:
                blockers.append("missing_20101_filter_primitives")
        except Exception:
            blockers.append("live_snapshot_read_failed")

    conntrack_text = _read(kwargs.get("conntrack_snapshot_file"))
    forwarder_text = _read(kwargs.get("forwarder_log_file"))
    bridge_text = _read(kwargs.get("bridge_log_file"))
    conn_lines = conntrack_text.splitlines()
    conn_assured_seen = any(
        ("ASSURED" in line)
        and ("dport=20101" in line)
        and ("172.18.0.3" in line)
        and ("sport=60010" in line)
        for line in conn_lines
    )
    conntrack_20101_unreplied_seen = bool(re.search(r"(SYN_SENT|UNREPLIED).*(dport=20101)", conntrack_text))
    conntrack_backend_nat_seen = any(
        ("dport=20101" in line) and ("172.18.0.3" in line) and ("sport=60010" in line)
        for line in conn_lines
    )
    conn_ok = conn_assured_seen
    fwd_ok = ("172.18.0.3:60010" in forwarder_text) or ("<->" in forwarder_text and "bitcoin.viabtc.io:3333" in forwarder_text)
    bridge_ok = ("127.0.0.1:20170" in bridge_text and "172.18.0.3" in bridge_text) or ("172.18.0.3:60010" in bridge_text)
    if not conn_ok:
        blockers.append("missing_conntrack_assured_runtime_signal")
    if not fwd_ok:
        blockers.append("missing_forwarder_runtime_signal")
    if not bridge_ok:
        blockers.append("missing_bridge_runtime_signal")

    ready = not blockers
    return {
        "component": "phase11_single_customer_runtime_path_evidence",
        "expected_version": expected_version,
        "repository_version": __version__,
        "candidate_customer_key": candidate_customer_key,
        "candidate_lane": candidate_lane,
        "candidate_public_port": candidate_public_port,
        "candidate_backend_target": candidate_backend_target,
        "post_apply_evidence_ready": post.get("post_apply_evidence_ready") is True,
        "controlled_apply_recorded": post.get("controlled_apply_recorded") is True,
        "runtime_path_evidence_ready": ready,
        "stratum_transcript_ready": False,
        "visibility_bundle_ready": False,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "phase11_accepted": False,
        "db_activation_allowed": False,
        "mutation_performed": False,
        "conntrack_assured_seen": conn_assured_seen,
        "conntrack_backend_nat_seen": conntrack_backend_nat_seen,
        "conntrack_20101_unreplied_seen": conntrack_20101_unreplied_seen,
        "forwarder_pool_seen": fwd_ok,
        "bridge_loopback_seen": bridge_ok,
        "next_required_step": "phase11e_single_customer_stratum_visibility_bundle_pr" if ready else "none",
        "blockers": sorted(set(blockers)),
        "warnings": [],
        "final_decision": "PHASE11_SINGLE_CUSTOMER_RUNTIME_PATH_EVIDENCE_READY" if ready else "BLOCKED",
    }
