# PHASE_11E_SINGLE_CUSTOMER_RUNTIME_STRATUM_EVIDENCE_RUNBOOK

Status: Phase 11E planning/readiness only (fail-closed, non-activating).

## Purpose

Provide an operator-safe, repeatable workflow to collect single-customer runtime + external Stratum evidence for the exact single-customer scope:

- customer: `limited-btc-001`
- lane: `btc`
- public port: `20101`
- backend target expectation: `172.18.0.3:60010`

This runbook **does not** authorize or perform production activation, DB activation, customer activation, or Phase 11 acceptance.

## Hard safety boundary

- Keep all gates closed (`production_traffic: none`, `customer_onboarding_allowed: db_only`, `firewall_apply_allowed: no`).
- Do not claim ASSURED unless it is present in collected conntrack snapshot.
- External Stratum probe must run from outside farm5 (no self/hairpin probe).
- Runtime acceptance remains fail-closed until evidence classifiers independently return READY.

## Step 1) Confirm version and gate

```bash
mpf --version
bash scripts/verify_current_phase_gate.sh
```

Expected:
- version `0.1.210`
- accepted phase still Phase 10
- working phase still Phase 11 planning/readiness
- closed production/miner/customer activation gates
- if phase gate reports existing controlled MPF artifacts for Phase 11 canary/20101, stop and send the full output for review (do not bypass).

## Step 2) Prepare evidence directory

```bash
export RTE_DIR="/tmp/phase11e-20101-runtime-stratum-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RTE_DIR"
```

## Step 3) Start long-lived external Stratum probe (outside farm5)

Run from an external machine (not farm5):

```bash
# Example shape; use your approved external probe tool.
# Keep TCP open long enough to observe ASSURED (typically 180-240s).
external-stratum-probe \
  --host <farm5-public-ip> \
  --port 20101 \
  --worker limited-btc-001.worker01 \
  --hold-seconds 240 \
  --json-out /tmp/limited-btc-001-20101-transcript.json
```

Transcript JSON must satisfy the existing classifier contract:
- `connect_port = 20101`
- worker includes `limited-btc-001` (or operator-mapped worker includes it)
- `mining.subscribe` response present
- `mining.authorize` result true
- `mining.set_difficulty` or `mining.notify` present

## Step 4) While probe is connected, capture synchronized runtime artifacts on farm5

```bash
sudo iptables-save > "$RTE_DIR/live-iptables-save.txt"
sudo conntrack -L > "$RTE_DIR/conntrack.txt"

# Pick one logging path used on farm5; keep exact command/output recorded.
docker logs --since 15m mpf-forwarder > "$RTE_DIR/forwarder.log" || true

docker logs --since 15m mpf-v2raya-socks-bridge > "$RTE_DIR/bridge.log" || true
```

Copy the external transcript JSON into `$RTE_DIR`, for example:

```bash
cp /path/from/external/limited-btc-001-20101-transcript.json "$RTE_DIR/stratum-transcript.json"
```

## Step 5) Compute sha256 for every artifact

```bash
sha256sum "$RTE_DIR/live-iptables-save.txt" > "$RTE_DIR/live-iptables-save.txt.sha256"
sha256sum "$RTE_DIR/conntrack.txt" > "$RTE_DIR/conntrack.txt.sha256"
sha256sum "$RTE_DIR/forwarder.log" > "$RTE_DIR/forwarder.log.sha256"
sha256sum "$RTE_DIR/bridge.log" > "$RTE_DIR/bridge.log.sha256"
sha256sum "$RTE_DIR/stratum-transcript.json" > "$RTE_DIR/stratum-transcript.json.sha256"
```

## Step 6) Run runtime probe diagnostics

```bash
mpf production single-customer-runtime-probe-diagnostics \
  --expected-version 0.1.210 \
  --post-apply-evidence-json /tmp/phase11-single-customer-post-apply-evidence-0.1.205.json \
  --post-apply-evidence-json-sha256 19ef5602af8ad36267ce34c3ca21e660e32d8970b0a81d69bc80b8a206d41ead \
  --live-snapshot-file "$RTE_DIR/live-iptables-save.txt" \
  --live-snapshot-sha256 "$(cut -d' ' -f1 "$RTE_DIR/live-iptables-save.txt.sha256")" \
  --conntrack-snapshot-file "$RTE_DIR/conntrack.txt" \
  --conntrack-snapshot-sha256 "$(cut -d' ' -f1 "$RTE_DIR/conntrack.txt.sha256")" \
  --forwarder-log-file "$RTE_DIR/forwarder.log" \
  --forwarder-log-sha256 "$(cut -d' ' -f1 "$RTE_DIR/forwarder.log.sha256")" \
  --bridge-log-file "$RTE_DIR/bridge.log" \
  --bridge-log-sha256 "$(cut -d' ' -f1 "$RTE_DIR/bridge.log.sha256")" \
  --operator <operator> \
  --reason "phase11e runtime evidence collection" \
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
  --output json > "$RTE_DIR/runtime-probe-diagnostics.json"
```

## Step 7) Run runtime-path evidence classifier

```bash
mpf production single-customer-runtime-path-evidence \
  --expected-version 0.1.210 \
  --post-apply-evidence-json /tmp/phase11-single-customer-post-apply-evidence-0.1.205.json \
  --post-apply-evidence-json-sha256 19ef5602af8ad36267ce34c3ca21e660e32d8970b0a81d69bc80b8a206d41ead \
  --live-snapshot-file "$RTE_DIR/live-iptables-save.txt" \
  --conntrack-snapshot-file "$RTE_DIR/conntrack.txt" \
  --forwarder-log-file "$RTE_DIR/forwarder.log" \
  --bridge-log-file "$RTE_DIR/bridge.log" \
  --operator <operator> \
  --reason "phase11e runtime path evidence" \
  --operator-confirmed \
  --i-understand-runtime-evidence-only \
  --i-understand-no-production-traffic-acceptance \
  --i-understand-no-miner-traffic-acceptance \
  --i-understand-no-db-activation \
  --i-confirm-stratum-transcript-required \
  --i-confirm-visibility-bundle-required \
  --i-confirm-abuse-1h-required-before-customer-traffic \
  --i-confirm-restart-container-order-required-before-limited-acceptance \
  --output json > "$RTE_DIR/runtime-path-evidence.json"
```

## Step 8) Run Stratum transcript evidence classifier

```bash
mpf production single-customer-stratum-transcript-evidence \
  --transcript-json "$RTE_DIR/stratum-transcript.json" \
  --output json > "$RTE_DIR/stratum-transcript-evidence.json"
```

Note: transcript sha256 is still required as operator evidence/checklist artifact in this runbook, even though the current transcript-evidence CLI does not accept a transcript hash flag.

## Step 9) If both runtime-path + Stratum are READY, build visibility bundle

```bash
mpf production single-customer-visibility-bundle \
  --runtime-path-evidence-json "$RTE_DIR/runtime-path-evidence.json" \
  --runtime-path-evidence-json-sha256 "$(sha256sum "$RTE_DIR/runtime-path-evidence.json" | cut -d' ' -f1)" \
  --stratum-transcript-evidence-json "$RTE_DIR/stratum-transcript-evidence.json" \
  --stratum-transcript-evidence-json-sha256 "$(sha256sum "$RTE_DIR/stratum-transcript-evidence.json" | cut -d' ' -f1)" \
  --output json > "$RTE_DIR/visibility-bundle.json"
```

## Step 10) Record outputs and checklist

- Save all command outputs in `$RTE_DIR`.
- Confirm conntrack snapshot has source-backed `ASSURED` entry for 20101 before claiming runtime ready.
- Confirm no step activated production/miner traffic or DB activation.
- Attach artifact file list + `.sha256` files in evidence report PR/issue.

## Operator checklist (must all be YES)

- [ ] Version is `0.1.210`.
- [ ] Current phase gate remains Phase 10 accepted / Phase 11 planning.
- [ ] Probe was external (not farm5 hairpin/self path).
- [ ] Long-lived probe stayed open sufficiently for ASSURED observation attempt.
- [ ] Synchronized artifacts captured: `live-iptables-save.txt`, `conntrack.txt`, `forwarder.log`, `bridge.log`, `stratum-transcript.json`.
- [ ] sha256 files computed for every artifact.
- [ ] Runtime probe diagnostics executed and archived.
- [ ] Runtime-path evidence executed and archived.
- [ ] Stratum transcript evidence executed and archived.
- [ ] Visibility bundle executed only if both prerequisite classifiers are READY.
- [ ] No DB activation, no customer activation, no production/miner traffic activation performed.
- [ ] Phase 11 acceptance is still not claimed in this step.

This runbook does not authorize or perform production activation.
