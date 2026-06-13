# Phase 11 Controlled Filter Packet-Path Evidence Runbook

Status: version 0.1.252 read-only topology-proof evidence capability; legacy 0.1.251 bundles remain integrity-verifiable but require recollection for readiness. `docs/PHASE_STATUS.md` remains authoritative.

## Boundary

This runbook is for collecting a static pre-apply topology and ruleset proof bundle for exactly:

- `canary-btc-001 / btc / 20001`
- `limited-btc-001 / btc / 20101`
- backend container `mpf-forwarder-btc` on Docker network `mpf-proxy-internal`
- backend port `60010`

The command path is read-only. It must not mutate firewall, Docker, systemd, conntrack, PostgreSQL, customers, policies, blocks, pauses, or abuse state. It must not generate traffic or observe runtime packets. `runtime_packet_observed=false` and `post_apply_runtime_verified=false` are mandatory.

## Commands

```bash
mpf production controlled-filter-packet-path-plan --output json
mpf production controlled-filter-packet-path-collect --output-dir /path/to/new-empty-dir --output json
mpf production controlled-filter-packet-path-verify --evidence-dir /path/to/new-empty-dir --output json
```

Optional helper, after choosing an explicit evidence root:

```bash
scripts/phase11_collect_controlled_filter_packet_path_evidence.sh /path/to/evidence-root
```

The helper calls only the official `mpf` CLI. It does not run Docker, iptables, route, bridge, systemd, conntrack, DB, or parser commands itself.

## Evidence semantics

A READY packet-path proof only means the static topology and ruleset evidence proves a stable user-policy hook for review. It does not make the controlled artifact package READY. `artifact_graph_binding_ready=false` remains required until a later reviewed PR binds the verified hook and post-DNAT/original-destination match semantics into the controlled artifact graph.

This PR collected no farm5 packet-path evidence, observed no runtime packet, proved no farm5 hook, changed no renderer hook, and changed no customer filter match semantics.

## Current progression

- `controlled_filter_packet_path_evidence_capability_implemented=true`
- `controlled_filter_packet_path_evidence_ready=false`
- `controlled_filter_packet_path_verified=false`
- `artifact_graph_binding_ready=false`
- `desired_artifact_semantics_complete=false`
- `production_execution_available=false`
- `controlled_artifact_reapply_package_evidence_ready=false`
- `restart_autostart_proof=missing_or_partial`
- `full_cli_production_operations=missing_or_partial`
- `next_required_step=sync_and_collect_controlled_filter_packet_path_evidence_on_farm5`

A future READY bundle must recommend `review_and_bind_verified_filter_hook_and_match_semantics_to_controlled_artifact_graph`, not direct execution. Phase 12, worker enforcement, UI, Telegram, timers, and daemons remain blocked.


## 0.1.252 collection semantics

The collector records independent component statuses, verifies Docker bridge identity from an explicit option or from the verified NetworkID-derived default, keeps NetworkID and EndpointID separate, correlates backend MAC/IP membership through FDB and optional namespace evidence, and evaluates per-ingress/per-conntrack-state packet scenarios. Missing bridge-nf sysctls are recorded as unavailable evidence rather than fabricated blockers for an otherwise routed Docker FORWARD path. This remains read-only and does not bind the renderer or enable package execution.


## 0.1.253 verified binding/package evidence update

A source-backed 0.1.252 farm5 packet-path READY bundle may now be consumed by `mpf production verified-filter-hook-binding-plan` to bind the verified `DOCKER-USER` / `FORWARD` / `post_dnat_forward_filter` hook to explicit Phase 11 controlled artifact graph semantics. `mpf production controlled-artifact-reapply-package-plan` and `mpf production controlled-artifact-reapply-package-verify` generate and verify package evidence only. Execution remains blocked: `production_execution_available=false`, `iptables_restore_invocation_allowed=false`, `runtime_packet_observed=false`, `post_apply_runtime_verified=false`, `restart_autostart_proof=missing_or_partial`, `full_cli_production_operations=missing_or_partial`, and Phase 12/worker/UI/Telegram remain blocked.
