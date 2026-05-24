# PHASE_11E_SINGLE_CUSTOMER_RUNTIME_PROBE_DIAGNOSTICS

## Purpose
Provide a non-mutating diagnostics classifier for limited-btc-001 runtime probe signals while keeping runtime acceptance closed.

## Scope
- customer: limited-btc-001
- lane: btc
- public_port: 20101
- backend_target: 172.18.0.3:60010

## Prerequisites
- post-apply evidence READY JSON + sha256
- live iptables snapshot, conntrack snapshot, forwarder log, bridge log
- all operator safety confirmations

## Exact evidence inputs
- `--post-apply-evidence-json` + `--post-apply-evidence-json-sha256`
- `--live-snapshot-file` (+ optional hash)
- `--conntrack-snapshot-file` (+ optional hash)
- `--forwarder-log-file` (+ optional hash)
- `--bridge-log-file` (+ optional hash)

## Command example
```bash
mpf production single-customer-runtime-probe-diagnostics \
  --expected-version 0.1.207 \
  --post-apply-evidence-json /tmp/phase11-single-customer-post-apply-evidence-0.1.205.json \
  --post-apply-evidence-json-sha256 19ef5602af8ad36267ce34c3ca21e660e32d8970b0a81d69bc80b8a206d41ead \
  --live-snapshot-file "$RTE_DIR/live-iptables-save.txt" \
  --conntrack-snapshot-file "$RTE_DIR/conntrack-snapshot.txt" \
  --forwarder-log-file "$RTE_DIR/forwarder-log.txt" \
  --bridge-log-file "$RTE_DIR/bridge-log.txt" \
  --operator vahid \
  --reason "Phase11E runtime probe diagnostics" \
  --operator-confirmed \
  --i-understand-probe-diagnostics-only \
  --i-understand-no-runtime-acceptance \
  --i-understand-no-production-traffic-acceptance \
  --i-understand-no-miner-traffic-acceptance \
  --i-understand-no-db-activation \
  --i-confirm-stratum-transcript-required \
  --i-confirm-visibility-bundle-required \
  --i-confirm-abuse-1h-required-before-customer-traffic \
  --i-confirm-restart-container-order-required-before-limited-acceptance \
  --output json
```

## Interpretation
- `conntrack_assured_seen`: handshake-level ASSURED runtime signal exists.
- `conntrack_20101_unreplied_seen`: attempted probe path seen (SYN_SENT/UNREPLIED), not handshake proof.
- `conntrack_backend_nat_seen`: 20101-related conntrack tuple includes backend NAT mapping (`172.18.0.3:60010`).
- `forwarder_pool_seen`: forwarder log indicates limited customer/pool path evidence.
- `bridge_loopback_seen`: bridge-side evidence indicates loopback/bridge runtime path visibility.

## Warning
SYN_SENT/UNREPLIED is attempted path/probe evidence only and is **not** runtime acceptance.

## Next operator step
Collect stronger runtime evidence (external probe or controlled Stratum transcript) that produces ASSURED conntrack evidence.

## Safety semantics
- This diagnostics service never sets `runtime_path_evidence_ready` to true.
- SYN_SENT/UNREPLIED is useful diagnostics evidence only; it is not runtime acceptance.
- ASSURED candidate output does not activate runtime path by itself; runtime-path evidence classifier remains the acceptance classifier.
- Production/miner traffic remains blocked and DB activation remains blocked.
