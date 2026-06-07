"""Controlled Phase 11 two-customer firewall artifact reapply primitives.

The module is intentionally service-layer only: plan/package/verify/evidence are
read-only and the execute path is operator-gated, drift-checked, and uses only
argv-based iptables-restore invocations supplied by injected adapters in tests.
"""
from __future__ import annotations

import fcntl
import hashlib
import ipaddress
import json
import os
import socket
import subprocess
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Iterable

from mpf import __version__
from mpf.services import firewall_planner_service
from mpf.domain.firewall import FirewallRuleIntent
from mpf.services.firewall_restore_payload_renderer import render_restore_contract

SCOPE = (
    {"customer_key": "canary-btc-001", "lane": "btc", "public_port": 20001},
    {"customer_key": "limited-btc-001", "lane": "btc", "public_port": 20101},
)
SCOPE_KEYS = {item["customer_key"] for item in SCOPE}
SCOPE_PORTS = {item["public_port"] for item in SCOPE}
BACKEND_CONTAINER = "mpf-forwarder-btc"
COMPOSE_PROJECT = "mpf-proxy"
DOCKER_NETWORK = "mpf-proxy-internal"
BACKEND_PORT = 60010
PHASE_SCOPE = "Phase 11 operational completion — Full CLI Production Operations"
PACKAGE_READY = "CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_READY"
NO_REAPPLY = "NO_CONTROLLED_ARTIFACT_REAPPLY_REQUIRED"
PACKAGE_BLOCKED = "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_PACKAGE"
EXECUTED_PENDING_REVIEW = "CONTROLLED_ARTIFACT_REAPPLY_EXECUTED_PENDING_FARM5_EVIDENCE_REVIEW"
REQUIRED_PHASE_FLAGS = (
    "current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5",
    "current_working_phase: Phase 11 operational completion — Full CLI Production Operations",
    "production_traffic: controlled_cli_limited",
    "customer_onboarding_allowed: controlled_cli_limited",
    "firewall_apply_allowed: controlled",
    "phase12_start_allowed: no",
    "worker_enforcement_allowed: no",
    "ui_allowed: no",
    "telegram_allowed: no",
)
_TRANSIENT_PACKAGE_KEYS = {"__package_file_sha256"}


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def _package_content_for_hash(package: dict[str, object]) -> dict[str, object]:
    return {k: v for k, v in package.items() if k not in {"package_sha256", *_TRANSIENT_PACKAGE_KEYS}}


def _phase_gate_blockers(phase_status_text: str) -> list[str]:
    return [f"phase_gate_missing:{flag}" for flag in REQUIRED_PHASE_FLAGS if flag not in phase_status_text]


def _text_sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _hostname() -> str:
    return socket.gethostname()


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


class SubprocessCommandAdapter:
    def run(self, argv: list[str], input_text: str | None = None) -> CommandResult:
        completed = subprocess.run(argv, shell=False, check=False, capture_output=True, text=True, input=input_text)
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


class ProductionIptablesRestoreRunner(SubprocessCommandAdapter):
    production_ready = True
    allowed = {
        ("iptables-save",),
        ("ip6tables-save",),
        ("iptables-restore", "--test", "--noflush"),
        ("iptables-restore", "--noflush"),
    }

    def run(self, argv: list[str], input_text: str | None = None) -> CommandResult:
        if tuple(argv) not in self.allowed:
            return CommandResult(126, "", f"command_not_allowed:{argv!r}")
        return super().run(argv, input_text=input_text)


class SocketReachabilityAdapter:
    def connect_ok(self, host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=1.5):
                return True
        except OSError:
            return False


def _run_stdout(runner: Any, argv: list[str], input_text: str | None = None) -> CommandResult:
    try:
        if hasattr(runner, "run"):
            try:
                result = runner.run(argv, input_text=input_text)
            except TypeError:
                result = runner.run(argv)
        else:
            result = runner(argv)
    except FileNotFoundError as exc:
        return CommandResult(127, "", str(exc))
    if isinstance(result, CommandResult):
        return result
    return CommandResult(int(getattr(result, "returncode", 1)), str(getattr(result, "stdout", "")), str(getattr(result, "stderr", "")))


def _valid_backend_ipv4(raw: str) -> tuple[bool, str | None]:
    try:
        ip = ipaddress.ip_address(raw)
    except ValueError:
        return False, "invalid_backend_ipv4"
    if not isinstance(ip, ipaddress.IPv4Address):
        return False, "backend_target_not_ipv4"
    if raw == "172.18.0.3":
        return False, "historical_backend_target_forbidden"
    if ip.is_loopback:
        return False, "loopback_backend_target_forbidden"
    if ip.is_link_local:
        return False, "link_local_backend_target_forbidden"
    if ip.is_multicast:
        return False, "multicast_backend_target_forbidden"
    if ip.is_unspecified:
        return False, "unspecified_backend_target_forbidden"
    if not ip.is_private:
        return False, "public_backend_target_forbidden"
    return True, None


def _ss_listener_public(stdout: str, port: int) -> tuple[bool, list[dict[str, object]]]:
    listeners: list[dict[str, object]] = []
    public = False
    for line in stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("State"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        local = parts[3]
        if f":{port}" not in local:
            continue
        host = local.rsplit(":", 1)[0].strip("[]")
        is_local = host in {"127.0.0.1", "::1", "localhost"} or host.startswith("127.")
        listeners.append({"local_address": host, "port": port, "local_only": is_local, "raw": line})
        if not is_local:
            public = True
    return public, listeners


def _docker_publishes_public(network_settings: dict[str, Any], port: int) -> tuple[bool, list[dict[str, object]]]:
    ports = network_settings.get("Ports", {}) if isinstance(network_settings.get("Ports"), dict) else {}
    bindings = ports.get(f"{port}/tcp") or []
    public = False
    out: list[dict[str, object]] = []
    for item in bindings or []:
        host_ip = str(item.get("HostIp", "")).strip()
        host_port = str(item.get("HostPort", "")).strip()
        is_public = host_ip in {"0.0.0.0", "::"} or not (host_ip.startswith("127.") or host_ip in {"127.0.0.1", "::1", "localhost", ""})
        out.append({"host_ip": host_ip, "host_port": host_port, "public": is_public})
        if is_public:
            public = True
    return public, out


class ControlledBackendTargetResolver:
    def __init__(self, *, runner: Any | None = None, reachability: Any | None = None, hostname: str | None = None) -> None:
        self.runner = runner or SubprocessCommandAdapter()
        self.reachability = reachability or SocketReachabilityAdapter()
        self.hostname = hostname or _hostname()

    def resolve(self, *, expected_version: str = __version__) -> dict[str, object]:
        blockers: list[str] = []
        warnings: list[str] = []
        collected_at = _now()
        inspect = _run_stdout(self.runner, ["docker", "inspect", BACKEND_CONTAINER])
        container: dict[str, Any] = {}
        if inspect.returncode != 0:
            blockers.append("backend_container_inspect_failed")
        else:
            try:
                parsed = json.loads(inspect.stdout)
                if not isinstance(parsed, list) or not parsed:
                    blockers.append("backend_container_missing")
                else:
                    container = parsed[0] if isinstance(parsed[0], dict) else {}
            except json.JSONDecodeError:
                blockers.append("backend_container_inspect_invalid_json")
        state = container.get("State", {}) if isinstance(container.get("State"), dict) else {}
        labels = container.get("Config", {}).get("Labels", {}) if isinstance(container.get("Config"), dict) else {}
        network_settings = container.get("NetworkSettings", {}) if isinstance(container.get("NetworkSettings"), dict) else {}
        networks = network_settings.get("Networks", {}) if isinstance(network_settings.get("Networks"), dict) else {}
        network = networks.get(DOCKER_NETWORK, {}) if isinstance(networks.get(DOCKER_NETWORK), dict) else {}
        running = state.get("Running") is True
        health = state.get("Health", {}).get("Status") if isinstance(state.get("Health"), dict) else None
        if container:
            if not running:
                blockers.append("backend_container_not_running")
            if health is not None and health != "healthy":
                blockers.append("backend_container_unhealthy")
            project = labels.get("com.docker.compose.project")
            if project != COMPOSE_PROJECT:
                blockers.append("backend_container_compose_project_mismatch")
            if DOCKER_NETWORK not in networks:
                blockers.append("backend_container_expected_network_missing")
        ip_raw = str(network.get("IPAddress", "")).strip()
        ip_ok = False
        if not ip_raw:
            if container:
                blockers.append("backend_target_ipv4_missing")
        else:
            ip_ok, ip_blocker = _valid_backend_ipv4(ip_raw)
            if ip_blocker:
                blockers.append(ip_blocker)
        reachable = False
        if ip_ok:
            reachable = bool(self.reachability.connect_ok(ip_raw, BACKEND_PORT) if hasattr(self.reachability, "connect_ok") else self.reachability(ip_raw, BACKEND_PORT))
            if not reachable:
                blockers.append("backend_target_tcp_unreachable")
        ss = _run_stdout(self.runner, ["ss", "-ltn", "sport", "=", f":{BACKEND_PORT}"])
        listener_public, listeners = (True, []) if ss.returncode != 0 else _ss_listener_public(ss.stdout, BACKEND_PORT)
        if ss.returncode != 0:
            blockers.append("backend_listener_read_failed")
        if not listeners or listener_public:
            blockers.append("backend_host_listener_missing_or_not_local_only")
        publish_public, publishes = _docker_publishes_public(network_settings, BACKEND_PORT)
        if publish_public:
            blockers.append("backend_docker_publish_public")
        net_id = network.get("NetworkID") or network.get("EndpointID")
        fingerprint_input = {
            "repository_version": __version__,
            "hostname": self.hostname,
            "container_name": container.get("Name", BACKEND_CONTAINER),
            "container_id": container.get("Id"),
            "network_name": DOCKER_NETWORK,
            "network_id": net_id,
            "resolved_ipv4": ip_raw,
            "backend_port": BACKEND_PORT,
        }
        fingerprint = _canonical_sha(fingerprint_input)
        if expected_version != __version__:
            blockers.append("wrong_expected_version")
        return {
            "component": "phase11_controlled_backend_target_resolver",
            "status": "ok" if not blockers else "blocked",
            "repository_version": __version__,
            "expected_version": expected_version,
            "hostname": self.hostname,
            "container_name": BACKEND_CONTAINER,
            "container_id": container.get("Id"),
            "compose_project": labels.get("com.docker.compose.project"),
            "network_name": DOCKER_NETWORK,
            "network_id": net_id,
            "resolved_ipv4": ip_raw or None,
            "target_host": ip_raw or None,
            "target_port": BACKEND_PORT,
            "health_status": health,
            "running": running,
            "listener_classification": {"listeners": listeners, "public": listener_public, "local_only": bool(listeners) and not listener_public},
            "publish_classification": {"bindings": publishes, "public": publish_public},
            "reachability": {"tcp_connect_ok": reachable},
            "backend_public_exposure": listener_public or publish_public,
            "collected_at": collected_at,
            "blockers": sorted(set(blockers)),
            "warnings": sorted(set(warnings)),
            "mutation_performed": False,
            "target_fingerprint_input": fingerprint_input,
            "target_fingerprint": fingerprint,
        }


def build_controlled_desired_state(*, lanes: list[dict[str, Any]], customers: list[dict[str, Any]], backend_target: dict[str, object], expected_version: str = __version__) -> dict[str, object]:
    blockers: list[str] = []
    if expected_version != __version__:
        blockers.append("wrong_expected_version")
    if backend_target.get("status") != "ok":
        blockers.append("backend_target_unresolved")
    if backend_target.get("target_port") != BACKEND_PORT:
        blockers.append("btc_backend_port_mismatch")
    resolved_ip = str(backend_target.get("resolved_ipv4") or backend_target.get("target_host") or "")
    ok_ip, ip_blocker = _valid_backend_ipv4(resolved_ip) if resolved_ip else (False, "backend_target_ipv4_missing")
    if ip_blocker:
        blockers.append(ip_blocker)
    lane_map = {str(l.get("name")): l for l in lanes}
    if not lane_map.get("btc", {}).get("enabled"):
        blockers.append("btc_lane_not_enabled")
    if int(lane_map.get("btc", {}).get("backend_port", -1)) != BACKEND_PORT:
        blockers.append("btc_backend_port_mismatch")
    scope_customers = [c for c in customers if c.get("customer_key") in SCOPE_KEYS]
    if len(scope_customers) != 2:
        blockers.append("exact_two_controlled_customers_required")
    seen_ports: set[int] = set()
    for item in SCOPE:
        matches = [c for c in customers if c.get("customer_key") == item["customer_key"]]
        if len(matches) != 1:
            blockers.append(f"controlled_customer_count_mismatch:{item['customer_key']}")
            continue
        c = matches[0]
        seen_ports.add(int(c.get("port", -1)))
        if c.get("lane") != item["lane"] or int(c.get("port", -1)) != item["public_port"]:
            blockers.append(f"controlled_customer_scope_mismatch:{item['customer_key']}")
        if c.get("status") != "active":
            blockers.append(f"controlled_customer_not_active:{item['customer_key']}")
        policy = c.get("policy") if isinstance(c.get("policy"), dict) else None
        missing = [f for f in ("miners", "farms", "maxconn", "rate_per_min", "burst", "ips_mode") if policy is None or policy.get(f) is None]
        if missing:
            blockers.append(f"controlled_customer_policy_incomplete:{item['customer_key']}:{','.join(missing)}")
    if len(seen_ports) != 2 or seen_ports != SCOPE_PORTS:
        blockers.append("controlled_customer_port_collision_or_mismatch")
    extra_active_btc = [c.get("customer_key") for c in customers if c.get("status") == "active" and c.get("lane") == "btc" and c.get("customer_key") not in SCOPE_KEYS]
    if extra_active_btc:
        blockers.append("third_customer_enters_controlled_reapply_scope")
    plan = firewall_planner_service.build_plan(lanes=lanes, customers=scope_customers, backend_exposed=bool(backend_target.get("backend_public_exposure")), planner_customer_source="postgresql_snapshot", db_customer_input_loaded=True)
    if plan.errors:
        blockers.extend(f"planner_error:{e.code}" for e in plan.errors)
    artifact_lines, renderer_blockers = _artifact_lines(plan, resolved_ip)
    blockers.extend(renderer_blockers)
    if not artifact_lines:
        blockers.append("controlled_policy_artifact_graph_unavailable")
    desired = {
        "component": "phase11_controlled_artifact_reapply_desired_state",
        "repository_version": __version__,
        "scope": list(SCOPE),
        "backend_target": {"resolved_ipv4": resolved_ip, "port": BACKEND_PORT, "fingerprint": backend_target.get("target_fingerprint")},
        "planner": plan.to_dict(),
        "artifact_lines": artifact_lines,
        "artifact_count": len(artifact_lines),
        "desired_state_hash": _canonical_sha({"scope": list(SCOPE), "backend": resolved_ip, "artifact_lines": artifact_lines}),
        "blockers": sorted(set(blockers)),
        "final_decision": "CONTROLLED_ARTIFACT_DESIRED_STATE_READY" if not blockers else "BLOCKED_CONTROLLED_ARTIFACT_DESIRED_STATE",
        "mutation_performed": False,
    }
    return desired


def _artifact_lines(plan: Any, resolved_ip: str) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    try:
        typed_plan = plan
        typed_plan.rules = [
            replace(rule, action_json={**rule.action_json, "target_backend_host": resolved_ip})
            if rule.rule_kind == "customer_nat_redirect" else rule
            for rule in typed_plan.rules
        ]
        contract = render_restore_contract(typed_plan)
    except Exception as exc:  # noqa: BLE001
        return [], [f"controlled_artifact_renderer_failed:{exc}"]
    blockers.extend(f"renderer_error:{e.code}" for e in contract.errors)
    if not contract.restore_payload:
        return [], blockers or ["controlled_artifact_renderer_payload_missing"]
    lines: list[str] = []
    # Global hooks are required exact prerequisites: the controlled package verifies
    # them read-only and only renders them when they are absent from an otherwise
    # exact-safe partial graph.
    lines.append('nat:-A PREROUTING -p tcp -m comment --comment "mpf:hook:nat_prerouting" -j MPF_NAT_PRE')
    lines.append('filter:-A INPUT -p tcp -m comment --comment "mpf:hook:filter_input" -j MPF_INPUT')
    for table in contract.restore_payload.tables:
        for chain in table.chains:
            lines.append(f"{table.name}:-N {chain.chain}")
        for rule in table.rules:
            lines.append(f"{table.name}:{rule.line}")
    return lines, blockers


def _present_lines(iptables_save_text: str) -> list[str]:
    present: list[str] = []
    current_table = "filter"
    for raw in iptables_save_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("*"):
            current_table = line[1:]
            continue
        if line == "COMMIT":
            continue
        if line.startswith(":"):
            parts = line.split()
            present.append(f"{current_table}:-N {parts[0][1:]}")
        elif line.startswith("-N ") or line.startswith("-A "):
            inferred_table = current_table
            if any(token in line for token in ("MPF_NAT_PRE", "MPF_NAT_POST", " PREROUTING ")):
                inferred_table = "nat"
            present.append(f"{inferred_table}:{line}")
    return present


def classify_controlled_artifacts(*, iptables_save_text: str, ip6tables_save_text: str, desired_state: dict[str, object]) -> dict[str, object]:
    blockers: list[str] = []
    desired = list(desired_state.get("artifact_lines", [])) if isinstance(desired_state.get("artifact_lines"), list) else []
    present = _present_lines(iptables_save_text)
    missing = [line for line in desired if line not in present]
    exact_present = [line for line in desired if line in present]
    unknown: list[str] = []
    stale: list[str] = []
    duplicates: list[str] = []
    for p in sorted(set(present)):
        count = present.count(p)
        if count > 1 and p in desired:
            duplicates.append(p)
    target = desired_state.get("backend_target", {}) if isinstance(desired_state.get("backend_target"), dict) else {}
    current = f"{target.get('resolved_ipv4')}:{BACKEND_PORT}"
    desired_set = set(desired)
    for raw in iptables_save_text.splitlines():
        line = raw.strip()
        if not any(token in line for token in ("MPF", "mpf:", "customer_")):
            continue
        normalized = f"nat:{line}" if any(token in f" {line} " for token in (" MPF_NAT_PRE ", " MPF_NAT_POST ")) or line in {":MPF_NAT_PRE - [0:0]", "-N MPF_NAT_PRE", ":MPF_NAT_POST - [0:0]", "-N MPF_NAT_POST"} else f"filter:{line}"
        if normalized not in desired_set:
            unknown.append(line)
        customer_ok = any(str(item["customer_key"]) in line for item in SCOPE) or "mpf:hook:" in line or "mpf:backend_guard:" in line
        chain_ok = any(chain in line for chain in ("INPUT", "PREROUTING", "MPF_INPUT", "MPF_CUSTOMERS", "MPF_GUARD", "MPF_ACCT_IN", "MPF_ACCT_OUT", "MPF_NAT_PRE", "MPF_NAT_POST", "MPFL_btc", "MPFC_20001", "MPFO_20001", "MPFC_20101", "MPFO_20101"))
        if "--to-destination" in line and current not in line:
            stale.append(line)
        if not customer_ok and "mpf:" in line:
            unknown.append(line)
        if (line.startswith(":MPF") or line.startswith("-N MPF") or line.startswith("-A MPF")) and not chain_ok:
            unknown.append(line)
    if any(token.lower() in ip6tables_save_text.lower() for token in ("mpf", "customer_")):
        unknown.append("ipv6_mpf_or_customer_artifact_detected")
    if unknown:
        blockers.append("unknown_mpf_artifacts_detected")
    if stale:
        blockers.append("stale_target_detected")
    if duplicates:
        blockers.append("duplicate_controlled_artifact_detected")
    status = "exact_present" if desired and not missing and not blockers else "exact_missing" if desired and not exact_present and not blockers else "safe_exact_partial" if desired and exact_present and missing and not blockers else "blocked"
    return {"component": "phase11_controlled_artifact_reapply_classification", "status": status, "exact_present": exact_present, "exact_missing": missing, "unknown_mpf": sorted(set(unknown)), "stale_target": stale, "duplicate_exact": duplicates, "blockers": sorted(set(blockers)), "classification_hash": _canonical_sha({"status": status, "present": exact_present, "missing": missing, "unknown": unknown, "stale": stale, "duplicates": duplicates}), "mutation_performed": False}


def render_payload(missing_artifacts: list[str]) -> tuple[str, str, list[str]]:
    blockers: list[str] = []
    by_table: dict[str, list[str]] = {"filter": [], "nat": []}
    for item in missing_artifacts:
        table, line = item.split(":", 1)
        if table not in by_table:
            blockers.append("payload_table_not_allowed")
            continue
        if any(bad in line for bad in (" -F", " -X", "*raw", "*mangle", "shell", "systemctl", "docker", "conntrack")):
            blockers.append("payload_forbidden_operation_detected")
        by_table[table].append(line)
    parts: list[str] = []
    for table in ("filter", "nat"):
        if by_table[table]:
            parts.append(f"*{table}")
            parts.extend(by_table[table])
            parts.append("COMMIT")
    payload = "\n".join(parts) + ("\n" if parts else "")
    if "172.18.0.3" in payload:
        blockers.append("historical_backend_target_forbidden")
    return payload, _text_sha(payload), sorted(set(blockers))


def build_plan(*, lanes: list[dict[str, Any]], customers: list[dict[str, Any]], backend_target: dict[str, object], iptables_save_text: str = "", ip6tables_save_text: str = "", phase_status_text: str = "", expected_version: str = __version__) -> dict[str, object]:
    desired = build_controlled_desired_state(lanes=lanes, customers=customers, backend_target=backend_target, expected_version=expected_version)
    classification = classify_controlled_artifacts(iptables_save_text=iptables_save_text, ip6tables_save_text=ip6tables_save_text, desired_state=desired)
    missing = list(classification.get("exact_missing", []))
    payload, payload_hash, payload_blockers = render_payload(missing)
    blockers = [*desired.get("blockers", []), *classification.get("blockers", []), *payload_blockers]
    if backend_target.get("backend_public_exposure"):
        blockers.append("backend_public_exposure_detected")
    phase_blockers = _phase_gate_blockers(phase_status_text)
    if phase_blockers:
        blockers.extend(phase_blockers)
    decision = PACKAGE_BLOCKED
    if not blockers and classification["status"] == "exact_present":
        decision = NO_REAPPLY
    elif not blockers and classification["status"] in {"exact_missing", "safe_exact_partial"}:
        decision = PACKAGE_READY
    snapshot_hashes = {"iptables_save_sha256": _text_sha(iptables_save_text), "ip6tables_save_sha256": _text_sha(ip6tables_save_text)}
    return {"component": "phase11_controlled_artifact_reapply_plan", "repository_version": __version__, "expected_version": expected_version, "hostname": _hostname(), "phase_status": PHASE_SCOPE, "scope": list(SCOPE), "backend_target": backend_target, "desired_state": desired, "artifact_classification": classification, "payload": payload, "payload_sha256": payload_hash, "snapshot_hashes": snapshot_hashes, "db_customer_policy_snapshot_hash": _canonical_sha({"lanes": lanes, "customers": customers}), "desired_state_hash": desired.get("desired_state_hash"), "artifact_classification_hash": classification.get("classification_hash"), "blockers": sorted(set(blockers)), "warnings": [], "final_decision": decision, "mutation_performed": False, "next_required_step": "sync_and_collect_controlled_artifact_reapply_package_evidence_on_farm5"}


def build_package_from_plan(plan: dict[str, object]) -> dict[str, object]:
    package_id = f"phase11-controlled-artifact-reapply-{plan.get('repository_version')}-{_canonical_sha(plan)[:12]}"
    ready = plan.get("final_decision") == PACKAGE_READY
    missing_delta = []
    classification = plan.get("artifact_classification") if isinstance(plan.get("artifact_classification"), dict) else {}
    for line in classification.get("exact_missing", []) if isinstance(classification.get("exact_missing"), list) else []:
        missing_delta.append({"added_artifact": line, "safe_inverse": "operator_review_required", "automatic_execution": False})
    rollback_plan = {"automatic_rollback_execution_available": False, "manual_review_required": True, "rollback_scope": list(SCOPE), "exact_inverse_delta": missing_delta, "instructions": ["Review pre-apply iptables/ip6tables backups.", "Use the generated exact missing-artifact rollback plan; do not broad-restore host firewall without separate approval."]}
    package = {"component": "phase11_controlled_artifact_reapply_package", "package_id": package_id, "repository_version": __version__, "hostname": plan.get("hostname"), "phase_status": plan.get("phase_status"), "scope": plan.get("scope"), "db_customer_policy_snapshot_hash": plan.get("db_customer_policy_snapshot_hash"), "backend_target_fingerprint": (plan.get("backend_target") or {}).get("target_fingerprint") if isinstance(plan.get("backend_target"), dict) else None, "iptables_save_sha256": (plan.get("snapshot_hashes") or {}).get("iptables_save_sha256") if isinstance(plan.get("snapshot_hashes"), dict) else None, "ip6tables_save_sha256": (plan.get("snapshot_hashes") or {}).get("ip6tables_save_sha256") if isinstance(plan.get("snapshot_hashes"), dict) else None, "desired_state_hash": plan.get("desired_state_hash"), "artifact_classification_hash": plan.get("artifact_classification_hash"), "payload": plan.get("payload", ""), "payload_sha256": plan.get("payload_sha256"), "backup_requirements": {"required": True, "base_dir": "/var/backups/mpf/phase11-controlled-artifact-reapply"}, "restore_point_requirements": {"required": True}, "lock_requirements": {"exclusive_lock_required": True}, "rollback_plan": rollback_plan, "operator_confirmations": ["--execute", "--yes", "--package-json", "--package-sha256", "--package-id", "--operator", "--reason"], "forbidden_operations": ["docker_restart", "systemd_action", "conntrack_flush", "customer_mutation", "policy_mutation", "abuse_mutation"], "plan": plan, "blockers": [] if ready else ["plan_not_ready"], "final_decision": PACKAGE_READY if ready else plan.get("final_decision", PACKAGE_BLOCKED), "mutation_performed": False}
    package["package_sha256"] = _canonical_sha(_package_content_for_hash(package))
    return package


def _package_shape_blockers(package: dict[str, object], *, expected_hostname: str | None = None) -> list[str]:
    blockers: list[str] = []
    if package.get("component") != "phase11_controlled_artifact_reapply_package":
        blockers.append("package_type_mismatch")
    if package.get("repository_version") != __version__:
        blockers.append("package_version_mismatch")
    if expected_hostname is not None and package.get("hostname") != expected_hostname:
        blockers.append("package_hostname_mismatch")
    if package.get("final_decision") != PACKAGE_READY:
        if package.get("final_decision") == NO_REAPPLY:
            blockers.append("no_reapply_package_cannot_execute")
        elif package.get("final_decision") == PACKAGE_BLOCKED:
            blockers.append("blocked_package_cannot_execute")
        else:
            blockers.append("package_not_ready")
    scope = package.get("scope")
    if scope != list(SCOPE):
        blockers.append("package_scope_mismatch")
    payload = str(package.get("payload", ""))
    if not payload.strip():
        blockers.append("package_payload_empty")
    if package.get("payload_sha256") != _text_sha(payload):
        blockers.append("package_payload_sha256_mismatch")
    rollback = package.get("rollback_plan") if isinstance(package.get("rollback_plan"), dict) else {}
    if rollback.get("manual_review_required") is not True or "exact_inverse_delta" not in rollback:
        blockers.append("reviewed_exact_rollback_plan_missing")
    embedded = package.get("package_sha256")
    calculated = _canonical_sha(_package_content_for_hash(package))
    if embedded != calculated:
        blockers.append("package_canonical_sha256_mismatch")
    return blockers


def verify_package(package: dict[str, object], *, live_plan: dict[str, object] | None = None) -> dict[str, object]:
    blockers: list[str] = _package_shape_blockers(package)
    plan = live_plan
    if plan is None:
        blockers.append("live_plan_required_for_verification")
    else:
        plan_blockers = plan.get("blockers", []) if isinstance(plan.get("blockers"), list) else []
        blockers.extend(str(blocker) for blocker in plan_blockers)
        if plan.get("final_decision") not in {PACKAGE_READY, NO_REAPPLY}:
            blockers.append("live_plan_not_safe")
        if plan.get("artifact_classification", {}).get("blockers"):
            blockers.append("live_artifact_classification_blocked")
        if plan.get("payload_sha256") != package.get("payload_sha256"):
            blockers.append("payload_hash_mismatch")
    return {"component": "phase11_controlled_artifact_reapply_verification", "repository_version": __version__, "package_id": package.get("package_id"), "blockers": sorted(set(blockers)), "final_decision": "CONTROLLED_ARTIFACT_REAPPLY_VERIFY_READY" if not blockers else "BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_VERIFY", "mutation_performed": False, "phase12_start_allowed": False, "worker_enforcement_allowed": "no", "ui_allowed": "no", "telegram_allowed": "no"}


class NoopOperationalMetadataRepo:
    def __init__(self) -> None:
        self.writes: list[str] = []
    def record_intent(self, package: dict[str, object], operator: str, reason: str) -> None:
        self.writes.append("events.audit_log.firewall_applies.intent")
    def record_result(self, package: dict[str, object], decision: str) -> None:
        self.writes.append("events.audit_log.firewall_applies.result")


class FileBackupAdapter:
    production_ready = True

    def __init__(self, base_dir: Path | str = "/var/backups/mpf/phase11-controlled-artifact-reapply") -> None:
        self.base_dir = Path(base_dir)
    def prepare(self, package: dict[str, object], *, iptables_save: str, ip6tables_save: str) -> dict[str, object]:
        if not iptables_save.strip() or not ip6tables_save.strip():
            raise RuntimeError("empty_firewall_backup_snapshot_forbidden")
        path = self.base_dir / str(package["package_id"])
        path.mkdir(mode=0o700, parents=True, exist_ok=False)
        files = {"iptables-save.txt": iptables_save, "ip6tables-save.txt": ip6tables_save, "package.json": json.dumps(package, indent=2, sort_keys=True), "package-file-sha256.txt": str(package.get("__package_file_sha256", "")), "canonical-package-sha256.txt": str(package.get("package_sha256", "")), "payload.restore": str(package.get("payload", "")), "target-evidence.json": json.dumps((package.get("plan") or {}).get("backend_target", {}), indent=2, sort_keys=True), "db-snapshot-hash.txt": str(package.get("db_customer_policy_snapshot_hash", "")), "pre-apply-classification.json": json.dumps((package.get("plan") or {}).get("artifact_classification", {}), indent=2, sort_keys=True), "rollback-plan.json": json.dumps(package.get("rollback_plan", {}), indent=2, sort_keys=True)}
        manifest = {}
        for name, text in files.items():
            p = path / name
            tmp = p.with_suffix(p.suffix + ".tmp")
            tmp.write_text(text, encoding="utf-8")
            tmp.chmod(0o600)
            os.replace(tmp, p)
            manifest[name] = _text_sha(text)
        manifest_path = path / "manifest.sha256.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        manifest_path.chmod(0o600)
        try:
            fd = os.open(path, os.O_RDONLY)
            os.fsync(fd)
            os.close(fd)
        except OSError:
            pass
        return {"backup_dir": str(path), "manifest": manifest}


class MemoryLock:
    def __init__(self) -> None:
        self.acquired = False
    def acquire(self) -> bool:
        if self.acquired:
            return False
        self.acquired = True
        return True
    def release(self) -> None:
        self.acquired = False


class FlockHostLock:
    production_ready = True

    def __init__(self, path: Path | str = "/run/lock/mpf-phase11-controlled-artifact-reapply.lock") -> None:
        self.path = Path(path)
        self._fh = None

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a+")
        try:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self._fh.close()
            self._fh = None
            return False
        return True

    def release(self) -> None:
        if self._fh is not None:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
            self._fh.close()
            self._fh = None


def execute_package(*, package: dict[str, object], package_sha256: str, package_id: str, operator: str, reason: str, execute: bool = False, yes: bool = False, expected_version: str = __version__, live_plan_builder: Callable[[], dict[str, object]] | None = None, runner: Any | None = None, backup: Any | None = None, metadata_repo: Any | None = None, lock: Any | None = None, env: dict[str, str] | None = None, current_hostname: str | None = None) -> dict[str, object]:
    blockers: list[str] = []
    restore_test_invoked = False
    apply_invoked = False
    apply_succeeded = False
    backup_result: dict[str, object] | None = None
    if not execute:
        blockers.append("execute_mode_required")
    if not yes:
        blockers.append("yes_confirmation_required")
    runtime_env = os.environ if env is None else env
    if runtime_env.get("CI"):
        blockers.append("ci_execution_blocked")
    if runtime_env.get("MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY") != "allow":
        blockers.append("controlled_artifact_reapply_env_gate_missing")
    if runtime_env.get("MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE") != "allow":
        blockers.append("controlled_artifact_reapply_execute_env_gate_missing")
    if expected_version != __version__ or package.get("repository_version") != __version__:
        blockers.append("version_mismatch")
    if package.get("package_id") != package_id:
        blockers.append("package_id_mismatch")
    if not operator.strip() or not reason.strip():
        blockers.append("operator_and_reason_required")

    file_hash = str(package.get("__package_file_sha256") or "")
    if not file_hash:
        blockers.append("package_file_sha256_required")
    elif file_hash != package_sha256:
        blockers.append("package_file_sha256_mismatch")
    embedded = package.get("package_sha256")
    calculated = _canonical_sha(_package_content_for_hash(package))
    if embedded != calculated:
        blockers.append("package_canonical_sha256_mismatch")
    blockers.extend(_package_shape_blockers(package, expected_hostname=current_hostname or _hostname()))

    # Production execution must never fall back to package-self verification or test-only adapters.
    if live_plan_builder is None:
        blockers.append("live_plan_builder_required")
    if lock is None or lock.__class__.__name__ == "MemoryLock" or getattr(lock, "production_ready", False) is not True:
        blockers.append("real_host_lock_required")
    if backup is None or getattr(backup, "production_ready", False) is not True:
        blockers.append("real_firewall_backup_adapter_required")
    if metadata_repo is None or isinstance(metadata_repo, NoopOperationalMetadataRepo) or getattr(metadata_repo, "production_ready", False) is not True:
        blockers.append("real_postgresql_operational_metadata_repo_required")
    if runner is None or getattr(runner, "production_ready", False) is not True:
        blockers.append("real_iptables_restore_runner_required")

    if blockers:
        return {"component": "phase11_controlled_artifact_reapply_executor", "final_decision": "FAILED_PRE_APPLY", "blockers": sorted(set(blockers)), "firewall_mutation_performed": False, "iptables_restore_invoked": restore_test_invoked or apply_invoked, "restore_test_invoked": restore_test_invoked, "apply_invoked": apply_invoked, "apply_succeeded": apply_succeeded, "partial_apply_possible": False, "rollback_required": False}

    live_plan = live_plan_builder()
    drift = []
    if live_plan.get("db_customer_policy_snapshot_hash") != package.get("db_customer_policy_snapshot_hash"):
        drift.append("db_customer_policy_snapshot_drift")
    if (live_plan.get("backend_target") or {}).get("target_fingerprint") != package.get("backend_target_fingerprint"):
        drift.append("backend_target_fingerprint_drift")
    if (live_plan.get("snapshot_hashes") or {}).get("iptables_save_sha256") != package.get("iptables_save_sha256"):
        drift.append("iptables_snapshot_drift")
    if live_plan.get("artifact_classification", {}).get("blockers"):
        drift.append("live_artifact_classification_blocked")
    if drift:
        return {"component": "phase11_controlled_artifact_reapply_executor", "final_decision": "FAILED_PRE_APPLY", "blockers": sorted(drift), "firewall_mutation_performed": False, "iptables_restore_invoked": restore_test_invoked or apply_invoked, "restore_test_invoked": restore_test_invoked, "apply_invoked": apply_invoked, "apply_succeeded": apply_succeeded, "partial_apply_possible": False, "rollback_required": False}

    if not lock.acquire():
        return {"component": "phase11_controlled_artifact_reapply_executor", "final_decision": "FAILED_PRE_APPLY", "blockers": ["exclusive_lock_unavailable"], "firewall_mutation_performed": False, "iptables_restore_invoked": restore_test_invoked or apply_invoked, "restore_test_invoked": restore_test_invoked, "apply_invoked": apply_invoked, "apply_succeeded": apply_succeeded, "partial_apply_possible": False, "rollback_required": False}
    try:
        # A second live preflight must be collected after the lock.
        post_lock_plan = live_plan_builder()
        if post_lock_plan.get("snapshot_hashes") != live_plan.get("snapshot_hashes") or post_lock_plan.get("db_customer_policy_snapshot_hash") != live_plan.get("db_customer_policy_snapshot_hash"):
            return {"component": "phase11_controlled_artifact_reapply_executor", "final_decision": "FAILED_PRE_APPLY", "blockers": ["post_lock_live_preflight_drift"], "firewall_mutation_performed": False, "iptables_restore_invoked": restore_test_invoked or apply_invoked, "restore_test_invoked": restore_test_invoked, "apply_invoked": apply_invoked, "apply_succeeded": apply_succeeded, "partial_apply_possible": False, "rollback_required": False}
        iptables_text = str(post_lock_plan.get("iptables_save_text", ""))
        ip6tables_text = str(post_lock_plan.get("ip6tables_save_text", ""))
        backup_result = backup.prepare(package, iptables_save=iptables_text, ip6tables_save=ip6tables_text)
        metadata_repo.record_intent(package, operator, reason)
        pre_restore_plan = live_plan_builder()
        if pre_restore_plan.get("snapshot_hashes") != post_lock_plan.get("snapshot_hashes") or pre_restore_plan.get("db_customer_policy_snapshot_hash") != post_lock_plan.get("db_customer_policy_snapshot_hash"):
            metadata_repo.record_result(package, "FAILED_PRE_APPLY")
            return {"component": "phase11_controlled_artifact_reapply_executor", "final_decision": "FAILED_PRE_APPLY", "blockers": ["pre_restore_live_preflight_drift"], "firewall_mutation_performed": False, "iptables_restore_invoked": restore_test_invoked or apply_invoked, "restore_test_invoked": restore_test_invoked, "apply_invoked": apply_invoked, "apply_succeeded": apply_succeeded, "partial_apply_possible": False, "rollback_required": False, "backup": backup_result}
        payload = str(package.get("payload", ""))
        test = _run_stdout(runner, ["iptables-restore", "--test", "--noflush"], input_text=payload)
        restore_test_invoked = True
        if test.returncode != 0:
            metadata_repo.record_result(package, "FAILED_PRE_APPLY")
            return {"component": "phase11_controlled_artifact_reapply_executor", "final_decision": "FAILED_PRE_APPLY", "blockers": ["iptables_restore_test_failed"], "firewall_mutation_performed": False, "iptables_restore_invoked": restore_test_invoked or apply_invoked, "restore_test_invoked": restore_test_invoked, "apply_invoked": apply_invoked, "apply_succeeded": apply_succeeded, "partial_apply_possible": False, "rollback_required": False, "backup": backup_result, "payload_bytes": len(payload)}
        apply = _run_stdout(runner, ["iptables-restore", "--noflush"], input_text=payload)
        apply_invoked = True
        apply_succeeded = apply.returncode == 0
        if apply.returncode != 0:
            metadata_repo.record_result(package, "FAILED_APPLY")
            return {"component": "phase11_controlled_artifact_reapply_executor", "final_decision": "FAILED_APPLY", "blockers": ["iptables_restore_apply_failed"], "firewall_mutation_performed": False, "iptables_restore_invoked": restore_test_invoked or apply_invoked, "restore_test_invoked": restore_test_invoked, "apply_invoked": apply_invoked, "apply_succeeded": apply_succeeded, "partial_apply_possible": True, "rollback_required": True, "backup": backup_result}
        verify = verify_package(package, live_plan=live_plan_builder())
        if verify["blockers"]:
            metadata_repo.record_result(package, "FAILED_POST_APPLY_VERIFICATION")
            return {"component": "phase11_controlled_artifact_reapply_executor", "final_decision": "FAILED_POST_APPLY_VERIFICATION", "blockers": verify["blockers"], "firewall_mutation_performed": True, "iptables_restore_invoked": restore_test_invoked or apply_invoked, "restore_test_invoked": restore_test_invoked, "apply_invoked": apply_invoked, "apply_succeeded": apply_succeeded, "partial_apply_possible": True, "rollback_required": True, "backup": backup_result, "rollback_plan": package.get("rollback_plan")}
        metadata_repo.record_result(package, EXECUTED_PENDING_REVIEW)
        return {"component": "phase11_controlled_artifact_reapply_executor", "final_decision": EXECUTED_PENDING_REVIEW, "blockers": [], "firewall_mutation_performed": True, "iptables_restore_invoked": restore_test_invoked or apply_invoked, "restore_test_invoked": restore_test_invoked, "apply_invoked": apply_invoked, "apply_succeeded": apply_succeeded, "partial_apply_possible": False, "rollback_required": False, "backup": backup_result}
    except Exception as exc:  # noqa: BLE001 - production executor must report fail-closed evidence.
        if apply_succeeded:
            return {"component": "phase11_controlled_artifact_reapply_executor", "final_decision": "FAILED_POST_APPLY_VERIFICATION", "blockers": ["post_apply_dependency_failed"], "error": str(exc), "firewall_mutation_performed": True, "iptables_restore_invoked": True, "restore_test_invoked": restore_test_invoked, "apply_invoked": apply_invoked, "apply_succeeded": apply_succeeded, "partial_apply_possible": True, "rollback_required": True, "backup": backup_result, "rollback_plan": package.get("rollback_plan")}
        return {"component": "phase11_controlled_artifact_reapply_executor", "final_decision": "FAILED_PRE_APPLY", "blockers": ["controlled_execution_pre_apply_dependency_failed"], "error": str(exc), "firewall_mutation_performed": False, "iptables_restore_invoked": restore_test_invoked or apply_invoked, "restore_test_invoked": restore_test_invoked, "apply_invoked": apply_invoked, "apply_succeeded": apply_succeeded, "partial_apply_possible": False, "rollback_required": False}
    finally:
        lock.release()


def collect_evidence_bundle(*, plan: dict[str, object] | None = None, package: dict[str, object] | None = None) -> dict[str, object]:
    evidence = {"component": "phase11_controlled_artifact_reapply_evidence", "repository_version": __version__, "collected_at": _now(), "plan": plan, "package": package, "mutation_performed": False}
    evidence["sha256_manifest"] = {k: _canonical_sha(v) for k, v in evidence.items() if k not in {"sha256_manifest"}}
    return evidence
