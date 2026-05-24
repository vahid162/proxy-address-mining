from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service

_PHASE_STATUS_PATH = Path("docs/PHASE_STATUS.md")
_REQUIRED_PHASE_FLAGS = (
    "live_snapshot_read_allowed: iptables_save_read_only",
    "production_traffic: none",
    "firewall_apply_allowed: no",
    "abuse_automation_allowed: no",
    "customer_onboarding_allowed: db_only",
    "ui_allowed: no",
    "telegram_allowed: no",
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _blocked_report(**k: object) -> dict[str, object]:
    return {
        "component": "phase11_single_customer_firewall_apply_gate",
        "expected_version": k.get("expected_version"),
        "repository_version": __version__,
        "candidate_customer_key": k.get("candidate_customer_key", ""),
        "candidate_lane": k.get("candidate_lane", ""),
        "candidate_public_port": k.get("candidate_public_port"),
        "candidate_backend_target": k.get("candidate_backend_target", ""),
        "phase11e_firewall_apply_gate_ready": False,
        "firewall_apply_execution_allowed": False,
        "firewall_apply_allowed": False,
        "nat_apply_allowed": False,
        "iptables_restore_authorized": False,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "phase11_accepted": False,
        "limited_onboarding_allowed": False,
        "db_mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "docker_mutation_performed": False,
        "mutation_performed": False,
        "apply_gate_package_generated": False,
        "firewall_plan_gate_json_sha256": k.get("firewall_plan_gate_json_sha256"),
        "plan_summary_sha256": k.get("plan_summary_sha256"),
        "live_firewall_summary": k.get("live_firewall_summary", {}),
        "required_pre_apply_artifacts": [],
        "required_post_apply_evidence": [],
        "intended_apply_scope": {},
        "blockers": sorted(set(k.get("blockers", []))),
        "warnings": [],
        "next_required_step": "none",
        "final_decision": "BLOCKED",
    }


def _phase_snapshot_read_authorized() -> bool:
    try:
        text = _PHASE_STATUS_PATH.read_text(encoding="utf-8")
    except Exception:
        return False
    return all(flag in text for flag in _REQUIRED_PHASE_FLAGS)


def _read_live_snapshot(live_snapshot_file: Path | None, collect_live: bool, snapshot_reader=None) -> str:
    if live_snapshot_file is not None:
        return live_snapshot_file.read_text(encoding="utf-8")
    if not collect_live:
        raise ValueError("live_firewall_snapshot_missing")
    if not _phase_snapshot_read_authorized():
        raise ValueError("live_snapshot_read_not_authorized")
    if snapshot_reader is not None:
        return str(snapshot_reader())
    cp = subprocess.run(["iptables-save"], capture_output=True, text=True, check=False, timeout=5)
    if cp.returncode != 0:
        raise RuntimeError("iptables-save failed")
    return cp.stdout


def _parse_live_snapshot(snapshot_text: str) -> tuple[dict[str, object], list[str]]:
    blockers: list[str] = []
    lines = snapshot_text.splitlines()

    has_nat_chain = ":MPF_NAT_PRE" in snapshot_text
    has_canary_chain = ":MPFC_20001" in snapshot_text

    canary_nat_rules = [
        line for line in lines
        if "MPF_NAT_PRE" in line and "--dport 20001" in line and "-j DNAT" in line
    ]
    exact_target_rules = [line for line in canary_nat_rules if "--to-destination 172.18.0.3:60010" in line]
    loopback_rules = [line for line in canary_nat_rules if "--to-destination 127.0.0.1:60010" in line]
    has_canary_comment = any("mpf:canary-btc-001:customer_nat_redirect" in line for line in canary_nat_rules)
    has_limited_ref = "limited-btc-001" in snapshot_text
    has_chain_20101 = "MPFC_20101" in snapshot_text
    has_dnat_20101 = any("--dport 20101" in line and "-j DNAT" in line for line in lines)

    canary_exact_ok = has_nat_chain and has_canary_chain and len(canary_nat_rules) == 1 and len(exact_target_rules) == 1 and not loopback_rules and has_canary_comment
    if not canary_exact_ok:
        blockers.append("live_canary_20001_artifact_missing_or_ambiguous")
    if has_chain_20101 or has_dnat_20101:
        blockers.append("live_20101_rule_already_exists")
    if has_limited_ref:
        blockers.append("live_firewall_unexpected_limited_customer_reference")

    return {
        "canary_nat_chain_present": has_nat_chain,
        "canary_customer_chain_present": has_canary_chain,
        "canary_20001_nat_rule_count": len(canary_nat_rules),
        "canary_20001_exact_target_rule_count": len(exact_target_rules),
        "canary_20001_loopback_rule_count": len(loopback_rules),
        "canary_comment_present": has_canary_comment,
        "limited_20101_chain_present": has_chain_20101,
        "limited_20101_dnat_present": has_dnat_20101,
        "limited_customer_reference_present": has_limited_ref,
    }, blockers


def build_phase11_single_customer_firewall_apply_gate_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    blockers: list[str] = []
    expected_version = str(kwargs.get("expected_version", __version__))
    farm5_baseline_version = str(kwargs.get("farm5_baseline_version", "0.1.168"))
    candidate_customer_key = str(kwargs.get("candidate_customer_key", "")).strip()
    candidate_lane = str(kwargs.get("candidate_lane", "")).strip().lower()
    candidate_public_port = kwargs.get("candidate_public_port")
    candidate_backend_target = str(kwargs.get("candidate_backend_target", "")).strip()
    operator = str(kwargs.get("operator", "")).strip()
    reason = str(kwargs.get("reason", "")).strip()
    collect_live = bool(kwargs.get("collect_live", False))
    live_snapshot_file = kwargs.get("live_snapshot_file")
    plan_json_path = Path(str(kwargs.get("firewall_plan_gate_json", "")))

    if expected_version != __version__: blockers.append("expected_version_mismatch")
    if farm5_baseline_version != "0.1.168": blockers.append("farm5_baseline_version_mismatch")
    if candidate_customer_key != "limited-btc-001": blockers.append("candidate_customer_key_invalid")
    if candidate_lane != "btc": blockers.append("candidate_lane_invalid")
    if candidate_public_port != 20101: blockers.append("candidate_public_port_invalid")
    if candidate_backend_target != "172.18.0.3:60010": blockers.append("candidate_backend_target_invalid")
    if kwargs.get("operator_confirmed") is not True or not operator or not reason: blockers.append("operator_not_confirmed")

    confirmations = {
        "i_understand_apply_gate_only": "apply_gate_only_boundary_not_confirmed",
        "i_understand_no_firewall_apply_in_this_pr": "no_firewall_apply_boundary_not_confirmed",
        "i_understand_no_nat_apply_in_this_pr": "no_nat_apply_boundary_not_confirmed",
        "i_understand_no_iptables_restore_in_this_pr": "no_iptables_restore_boundary_not_confirmed",
        "i_understand_no_production_traffic": "no_production_traffic_boundary_not_confirmed",
        "i_understand_no_miner_traffic_yet": "no_miner_traffic_boundary_not_confirmed",
        "i_confirm_limited_single_customer_scope": "limited_single_customer_scope_not_confirmed",
        "i_confirm_restore_point_required_before_apply": "restore_point_requirement_not_confirmed",
        "i_confirm_operator_lock_required_before_apply": "operator_lock_requirement_not_confirmed",
        "i_confirm_rollback_artifact_required_before_apply": "rollback_artifact_requirement_not_confirmed",
        "i_confirm_pre_apply_snapshot_required_before_apply": "pre_apply_snapshot_requirement_not_confirmed",
        "i_confirm_post_apply_verification_required": "post_apply_verification_requirement_not_confirmed",
        "i_confirm_runtime_path_evidence_required_after_apply": "runtime_path_evidence_requirement_not_confirmed",
        "i_confirm_abuse_1h_evidence_required_before_customer_traffic": "abuse_1h_requirement_not_confirmed",
        "i_confirm_restart_container_order_evidence_required_before_customer_traffic": "restart_container_order_requirement_not_confirmed",
    }
    for key, blocker in confirmations.items():
        if kwargs.get(key) is not True:
            blockers.append(blocker)

    data = None
    plan_gate_hash = None
    plan_summary_hash = None
    if not plan_json_path.exists() or not plan_json_path.is_file():
        blockers.append("firewall_plan_gate_json_missing")
    else:
        raw = plan_json_path.read_bytes()
        plan_gate_hash = _sha256_bytes(raw)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            blockers.append("firewall_plan_gate_json_invalid")

    if data is not None:
        required = {
            "component": "phase11_single_customer_firewall_plan_gate", "expected_version": "0.1.202", "repository_version": "0.1.202",
            "candidate_customer_key": "limited-btc-001", "candidate_lane": "btc", "candidate_public_port": 20101,
            "candidate_backend_target": "172.18.0.3:60010", "phase11e_firewall_plan_gate_ready": True, "firewall_plan_generated": True,
            "next_required_step": "phase11e_firewall_apply_gate_pr", "final_decision": "PHASE11_SINGLE_CUSTOMER_FIREWALL_PLAN_GATE_READY",
        }
        if any(data.get(k) != v for k, v in required.items()) or data.get("blockers") != [] or data.get("warnings") != []:
            blockers.append("firewall_plan_gate_not_ready")
        if any(data.get(k) is not False for k in ("firewall_apply_allowed", "nat_apply_allowed", "iptables_restore_authorized", "production_traffic_enabled", "miner_traffic_allowed", "phase11_accepted", "limited_onboarding_allowed")):
            blockers.append("firewall_plan_gate_safety_boundary_open")
        if any(data.get(k) is not False for k in ("db_mutation_performed", "firewall_mutation_performed", "nat_mutation_performed", "conntrack_mutation_performed", "docker_mutation_performed", "mutation_performed")):
            blockers.append("firewall_plan_gate_mutation_detected")
        s = data.get("firewall_plan_summary")
        if not isinstance(s, dict): blockers.append("firewall_plan_summary_missing")
        else:
            sreq = {"intended_chain": "MPFC_20101", "intended_nat_chain": "MPF_NAT_PRE", "intended_public_port": 20101, "intended_backend_target": "172.18.0.3:60010", "intended_customer_key": "limited-btc-001", "intended_lane": "btc"}
            saf = s.get("safety", {}) if isinstance(s.get("safety"), dict) else {}
            ok = all(s.get(k) == v for k, v in sreq.items()) and saf.get("iptables_restore_authorized") is False and saf.get("apply_command_approved") is False and saf.get("mutation_performed") is False and saf.get("existing_canary_20001_artifact_modified") is False and saf.get("production_traffic_enabled") is False
            if not ok: blockers.append("firewall_plan_summary_scope_mismatch")
            plan_summary_hash = _sha256_bytes(json.dumps(s, sort_keys=True, separators=(",", ":")).encode("utf-8"))

    if not blockers:
        try:
            customers = customer_read_service.list_customer_status(config, include_deleted=False, limit=5000)
        except Exception:
            customers = customer_read_service.CustomerList(ok=False, message="exception", customers=[])
        if not customers.ok: blockers.append("db_read_failed")
        else:
            rows = customers.customers
            staged = [r for r in rows if r.customer_key == "limited-btc-001"]
            if len(staged) == 0: blockers.append("staged_customer_missing")
            elif len(staged) > 1: blockers.append("staged_customer_duplicate")
            else:
                s = staged[0]
                if s.lane != "btc" or s.port != 20101: blockers.append("staged_customer_scope_mismatch")
                if str(getattr(s, "status", "")).strip().lower() != "paused": blockers.append("staged_customer_not_paused")
            if [r for r in rows if r.port == 20101 and r.customer_key != "limited-btc-001"]: blockers.append("candidate_port_collision")

    live_summary: dict[str, object] = {}
    if not blockers:
        try:
            snap = _read_live_snapshot(Path(str(live_snapshot_file)) if live_snapshot_file else None, collect_live, kwargs.get("live_snapshot_reader"))
        except ValueError as e:
            blockers.append(str(e))
            snap = ""
        except Exception:
            blockers.append("live_firewall_read_failed")
            snap = ""
        if snap:
            parsed_summary, parsed_blockers = _parse_live_snapshot(snap)
            live_summary = {
                "snapshot_source": "file" if live_snapshot_file else "live",
                **parsed_summary,
            }
            blockers.extend(parsed_blockers)

    if blockers:
        return _blocked_report(expected_version=expected_version, candidate_customer_key=candidate_customer_key, candidate_lane=candidate_lane, candidate_public_port=candidate_public_port, candidate_backend_target=candidate_backend_target, blockers=blockers, firewall_plan_gate_json_sha256=plan_gate_hash, plan_summary_sha256=plan_summary_hash, live_firewall_summary=live_summary)

    return {
        "component": "phase11_single_customer_firewall_apply_gate",
        "expected_version": expected_version,
        "repository_version": __version__,
        "candidate_customer_key": candidate_customer_key,
        "candidate_lane": candidate_lane,
        "candidate_public_port": candidate_public_port,
        "candidate_backend_target": candidate_backend_target,
        "phase11e_firewall_apply_gate_ready": True,
        "firewall_apply_execution_allowed": False,
        "firewall_apply_allowed": False,
        "nat_apply_allowed": False,
        "iptables_restore_authorized": False,
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "phase11_accepted": False,
        "limited_onboarding_allowed": False,
        "db_mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "docker_mutation_performed": False,
        "mutation_performed": False,
        "apply_gate_package_generated": True,
        "firewall_plan_gate_json_sha256": plan_gate_hash,
        "plan_summary_sha256": plan_summary_hash,
        "required_pre_apply_artifacts": ["pre_apply_iptables_save", "restore_point", "operator_lock", "rollback_artifact", "canary_20001_preservation_check", "exact_plan_hash_or_summary", "firewall_plan_gate_json_sha256", "plan_summary_sha256"],
        "required_post_apply_evidence": ["post_apply_iptables_save", "verify MPFC_20101 exists", "verify DNAT 20101 -> 172.18.0.3:60010", "verify canary 20001 still exists", "runtime path evidence for 20101", "Stratum transcript evidence for 20101", "visibility bundle evidence", "rollback readiness evidence", "abuse 1h coverage evidence before allowing customer traffic", "restart/container-order evidence before limited production acceptance"],
        "intended_apply_scope": {"single_customer_only": True, "customer_key": "limited-btc-001", "port": 20101, "backend": "172.18.0.3:60010", "canary_20001_must_not_be_modified": True, "no_broad_apply": True, "no_unrestricted_onboarding": True},
        "live_firewall_summary": live_summary,
        "blockers": [],
        "warnings": [],
        "next_required_step": "phase11e_single_customer_firewall_apply_execution_pr",
        "final_decision": "PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_GATE_READY",
    }
