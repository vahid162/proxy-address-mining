"""Typed DTOs for Phase 11 controlled filter packet-path evidence."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

READY = "READY_CONTROLLED_FILTER_PACKET_PATH_PROOF"
BLOCKED = "BLOCKED_CONTROLLED_FILTER_PACKET_PATH_PROOF"
INVALID = "INVALID_CONTROLLED_FILTER_PACKET_PATH_EVIDENCE"
PROOF_SCOPE = "static_pre_apply_topology_and_ruleset"
NEXT_REQUIRED_STEP = "sync_and_collect_controlled_filter_packet_path_evidence_on_farm5"
FUTURE_READY_RECOMMENDATION = "review_and_bind_verified_filter_hook_and_match_semantics_to_controlled_artifact_graph"

EXPECTED_VERSION = "0.1.252"
PREVIOUS_VERSION = "0.1.251"
BACKEND_CONTAINER = "mpf-forwarder-btc"
COMPOSE_PROJECT = "mpf-proxy"
COMPOSE_SERVICE = "mpf-forwarder-btc"
DOCKER_NETWORK = "mpf-proxy-internal"
BACKEND_PORT = 60010
CONTROLLED_CUSTOMERS = (
    {"customer_key": "canary-btc-001", "lane": "btc", "public_port": 20001},
    {"customer_key": "limited-btc-001", "lane": "btc", "public_port": 20101},
)

REQUIRED_PHASE_FLAGS = {
    "current_accepted_phase": "Phase 11 — Production / Customer Activation Gate accepted on farm5",
    "current_working_phase": "Phase 11 operational completion — Full CLI Production Operations",
    "production_traffic": "controlled_cli_limited",
    "customer_onboarding_allowed": "controlled_cli_limited",
    "firewall_apply_allowed": "controlled",
    "abuse_automation_allowed": "controlled_operator_gated",
    "proxy_data_plane_allowed": "limited_runtime_local_only",
    "worker_enforcement_allowed": "no",
    "ui_allowed": "no",
    "telegram_allowed": "no",
    "phase12_start_allowed": "no",
}

REQUIRED_BUNDLE_FILES = (
    "evidence.json",
    "decision.json",
    "sanitized-backend-target.json",
    "sanitized-docker-network.json",
    "iptables-save.txt",
    "ip6tables-save.txt",
    "parsed-firewall.json",
    "host-network-topology.json",
    "packet-path-graph.json",
    "command-results.json",
    "manifest.json",
    "manifest.sha256",
)
MANIFESTED_EVIDENCE_FILES = tuple(name for name in REQUIRED_BUNDLE_FILES if name not in {"manifest.json", "manifest.sha256"})


@dataclass(frozen=True)
class PacketPathNode:
    id: str
    type: str
    label: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PacketPathEdge:
    source: str
    target: str
    type: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PacketPathGraph:
    collection_id: str
    hostname: str
    nodes: list[PacketPathNode]
    edges: list[PacketPathEdge]
    proposed_review_only_graph: list[str] = field(default_factory=list)
    mutation_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PacketPathDecision:
    final_decision: Literal[
        "READY_CONTROLLED_FILTER_PACKET_PATH_PROOF",
        "BLOCKED_CONTROLLED_FILTER_PACKET_PATH_PROOF",
        "INVALID_CONTROLLED_FILTER_PACKET_PATH_EVIDENCE",
    ]
    proof_scope: str = PROOF_SCOPE
    runtime_packet_observed: bool = False
    post_apply_runtime_verified: bool = False
    post_dnat_route_class: str = "unresolved"
    verified_builtin_filter_path: str | None = None
    candidate_user_policy_hook: str | None = "DOCKER-USER"
    verified_user_policy_hook: str | None = None
    input_path_applicable: bool = False
    forward_path_applicable: bool = False
    docker_user_reachable: bool = False
    hook_precedes_all_relevant_accept_paths: bool = False
    bypass_path_detected: bool = False
    future_mpf_entry_reachable: bool = False
    packet_view_at_verified_hook: str = "unknown"
    destination_visible_at_verified_hook: dict[str, Any] = field(default_factory=dict)
    original_destination_available_via_conntrack: str = "unresolved"
    original_destination_match_required: bool = False
    current_customer_port_match_compatible: bool = False
    current_renderer_binding_compatible: bool = False
    renderer_binding_blockers: list[str] = field(default_factory=list)
    artifact_graph_binding_ready: bool = False
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence_hashes: dict[str, str] = field(default_factory=dict)
    future_ready_recommendation: str = FUTURE_READY_RECOMMENDATION
    mutation_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
