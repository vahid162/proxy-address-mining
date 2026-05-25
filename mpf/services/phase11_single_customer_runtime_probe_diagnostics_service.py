from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service
from mpf.services.phase11_single_customer_post_apply_evidence_service import _parse_snapshot

EXPECTED = {"customer_key": "limited-btc-001", "lane": "btc", "public_port": 20101, "backend_target": "172.18.0.3:60010"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _check_hash(path: Path | None, expected: str | None, missing: str, mismatch: str, blockers: list[str]) -> None:
    if path is None or not path.exists():
        blockers.append(missing)
        return
    if expected and _sha256(path) != expected:
        blockers.append(mismatch)


def build_phase11_single_customer_runtime_probe_diagnostics_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    blockers: list[str] = []
    expected_version = str(kwargs.get("expected_version", "0.1.209"))
    candidate_customer_key = str(kwargs.get("candidate_customer_key", EXPECTED["customer_key"]))
    candidate_lane = str(kwargs.get("candidate_lane", EXPECTED["lane"]))
    candidate_public_port = int(kwargs.get("candidate_public_port", EXPECTED["public_port"]))
    candidate_backend_target = str(kwargs.get("candidate_backend_target", EXPECTED["backend_target"]))

    confirmations = {
        "operator_confirmed": "operator_not_confirmed",
        "i_understand_probe_diagnostics_only": "probe_diagnostics_only_not_confirmed",
        "i_understand_no_runtime_acceptance": "no_runtime_acceptance_not_confirmed",
        "i_understand_no_production_traffic_acceptance": "no_production_traffic_not_confirmed",
        "i_understand_no_miner_traffic_acceptance": "no_miner_traffic_not_confirmed",
        "i_understand_no_db_activation": "no_db_activation_not_confirmed",
        "i_confirm_stratum_transcript_required": "stratum_transcript_required_not_confirmed",
        "i_confirm_visibility_bundle_required": "visibility_bundle_required_not_confirmed",
        "i_confirm_abuse_1h_required_before_customer_traffic": "abuse_1h_required_not_confirmed",
        "i_confirm_restart_container_order_required_before_limited_acceptance": "restart_container_order_required_not_confirmed",
    }
    for field, blocker in confirmations.items():
        if kwargs.get(field) is not True:
            blockers.append(blocker)

    if (candidate_customer_key, candidate_lane, candidate_public_port, candidate_backend_target) != (
        EXPECTED["customer_key"], EXPECTED["lane"], EXPECTED["public_port"], EXPECTED["backend_target"]
    ):
        blockers.append("candidate_scope_mismatch")

    post_apply_json = Path(str(kwargs.get("post_apply_evidence_json", "")))
    post: dict[str, object] = {}
    if not post_apply_json.exists():
        blockers.append("post_apply_evidence_json_missing")
    else:
        if _sha256(post_apply_json) != str(kwargs.get("post_apply_evidence_json_sha256", "")):
            blockers.append("post_apply_evidence_json_hash_mismatch")
        try:
            loaded = json.loads(post_apply_json.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                blockers.append("post_apply_evidence_json_invalid")
            else:
                post = loaded
        except Exception:
            blockers.append("post_apply_evidence_json_invalid")

    if post:
        if post.get("final_decision") != "PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY" or post.get("controlled_apply_recorded") is not True:
            blockers.append("post_apply_evidence_not_ready")
        if (
            post.get("candidate_customer_key") != EXPECTED["customer_key"]
            or post.get("candidate_lane") != EXPECTED["lane"]
            or post.get("candidate_public_port") != EXPECTED["public_port"]
            or post.get("candidate_backend_target") != EXPECTED["backend_target"]
        ):
            blockers.append("post_apply_evidence_scope_mismatch")
        for flag in ("production_traffic_enabled", "miner_traffic_allowed", "phase11_accepted", "db_activation_allowed", "mutation_performed"):
            if post.get(flag) is not False:
                blockers.append("post_apply_evidence_safety_boundary_open")
                break

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

    live = Path(str(kwargs.get("live_snapshot_file", ""))) if kwargs.get("live_snapshot_file") else None
    _check_hash(live, kwargs.get("live_snapshot_sha256"), "live_snapshot_missing", "live_snapshot_hash_mismatch", blockers)
    if live and live.exists():
        try:
            cls = _parse_snapshot(live.read_text(encoding="utf-8"))
            if int(cls.get("dnat_20101_exact_target_count", 0)) == 0:
                blockers.append("live_snapshot_missing_20101")
            if not cls.get("has_canary_20001"):
                blockers.append("live_snapshot_missing_canary_20001")
            if int(cls.get("dnat_20101_exact_target_count", 0)) > 1:
                blockers.append("live_snapshot_duplicate_20101")
            if int(cls.get("dnat_20101_loopback_count", 0)) > 0:
                blockers.append("live_snapshot_loopback_20101")
            if int(cls.get("unrelated_customer_nat_rule_count", 0)) > 0:
                blockers.append("live_snapshot_unrelated_customer_nat")
            if cls.get("limited_20101_filter_primitives_verified") is not True:
                blockers.append("live_snapshot_invalid")
        except Exception:
            blockers.append("live_snapshot_invalid")

    conntrack = Path(str(kwargs.get("conntrack_snapshot_file", ""))) if kwargs.get("conntrack_snapshot_file") else None
    forwarder = Path(str(kwargs.get("forwarder_log_file", ""))) if kwargs.get("forwarder_log_file") else None
    bridge = Path(str(kwargs.get("bridge_log_file", ""))) if kwargs.get("bridge_log_file") else None
    _check_hash(conntrack, kwargs.get("conntrack_snapshot_sha256"), "conntrack_snapshot_missing", "conntrack_snapshot_hash_mismatch", blockers)
    _check_hash(forwarder, kwargs.get("forwarder_log_sha256"), "forwarder_log_missing", "forwarder_log_hash_mismatch", blockers)
    _check_hash(bridge, kwargs.get("bridge_log_sha256"), "bridge_log_missing", "bridge_log_hash_mismatch", blockers)

    conn_text, fwd_text, br_text = _read(conntrack), _read(forwarder), _read(bridge)
    conntrack_assured_seen = bool(re.search(r"ASSURED.*(dport=20101|sport=20101|172\.18\.0\.3.*sport=60010)", conn_text))
    conntrack_20101_unreplied_seen = bool(re.search(r"(SYN_SENT|UNREPLIED).*(dport=20101)", conn_text))
    conntrack_backend_nat_seen = bool(re.search(r"dport=20101.*172\.18\.0\.3.*sport=60010", conn_text))
    forwarder_pool_seen = ("limited-btc-001" in fwd_text and "20101" in fwd_text) or ("172.18.0.3:60010" in fwd_text)
    forwarder_backend_seen = ("127.0.0.1:60010" in fwd_text) or ("172.18.0.3:60010" in fwd_text)
    bridge_loopback_seen = (("127.0.0.1:20170" in br_text and "172.18.0.3" in br_text) or ("172.18.0.3:60010" in br_text))

    if not conntrack_assured_seen and not conntrack_20101_unreplied_seen and not conntrack_backend_nat_seen:
        blockers.append("missing_conntrack_probe_signal")
    if conntrack_assured_seen and not forwarder_pool_seen:
        blockers.append("missing_forwarder_probe_signal")
    if not forwarder_pool_seen and not forwarder_backend_seen:
        blockers.append("missing_forwarder_probe_signal")
    if not bridge_loopback_seen:
        blockers.append("missing_bridge_probe_signal")

    blockers = sorted(set(blockers))
    base_valid = not blockers
    meaningful_signal = conntrack_assured_seen or conntrack_20101_unreplied_seen or conntrack_backend_nat_seen or forwarder_pool_seen or forwarder_backend_seen or bridge_loopback_seen
    probe_ready = base_valid and meaningful_signal

    if probe_ready and not conntrack_assured_seen:
        final = "PHASE11_SINGLE_CUSTOMER_RUNTIME_PROBE_DIAGNOSTICS_READY_BLOCKED_RUNTIME"
    elif probe_ready and conntrack_assured_seen and forwarder_pool_seen and bridge_loopback_seen:
        final = "PHASE11_SINGLE_CUSTOMER_RUNTIME_PROBE_DIAGNOSTICS_READY_ASSURED_CANDIDATE"
    else:
        final = "BLOCKED"
        if not blockers:
            blockers = ["missing_probe_diagnostics_signal"]
            probe_ready = False

    return {
        "component": "phase11_single_customer_runtime_probe_diagnostics",
        "expected_version": expected_version,
        "repository_version": __version__,
        "candidate_customer_key": candidate_customer_key,
        "candidate_lane": candidate_lane,
        "candidate_public_port": candidate_public_port,
        "candidate_backend_target": candidate_backend_target,
        "post_apply_evidence_ready": post.get("post_apply_evidence_ready") is True,
        "controlled_apply_recorded": post.get("controlled_apply_recorded") is True,
        "probe_diagnostics_ready": probe_ready,
        "runtime_path_evidence_ready": False,
        "conntrack_assured_seen": conntrack_assured_seen,
        "conntrack_20101_unreplied_seen": conntrack_20101_unreplied_seen,
        "conntrack_backend_nat_seen": conntrack_backend_nat_seen,
        "forwarder_pool_seen": forwarder_pool_seen,
        "forwarder_backend_seen": forwarder_backend_seen,
        "bridge_loopback_seen": bridge_loopback_seen,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "phase11_accepted": False,
        "db_activation_allowed": False,
        "mutation_performed": False,
        "blockers": blockers,
        "warnings": [],
        "next_required_step": "collect_stronger_runtime_probe_evidence" if probe_ready else "none",
        "final_decision": final,
    }
