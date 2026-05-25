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

## Primary two-terminal workflow (beginner-friendly)

### Step 1) Verify version and gate (farm5)

```bash
mpf --version
bash scripts/verify_current_phase_gate.sh
```

Expected:
- version `0.1.216`
- accepted phase still Phase 10
- working phase still Phase 11 planning/readiness
- closed production/miner/customer activation gates
- if phase gate reports existing controlled MPF artifacts for Phase 11 canary/20101, stop and send the full output for review (do not bypass).

### Step 2) External machine terminal (NOT farm5)

Run this from **outside farm5**.
Do **not** run this from farm5.
No hairpin/self-probe is allowed.

```bash
python3 scripts/phase11e_external_stratum_probe.py   --host <farm5-public-ip>   --port 20101   --worker limited-btc-001.worker01   --password x   --hold-seconds 600   --json-out /tmp/limited-btc-001-20101-transcript.json
```

Wait until the probe prints:

```text
READY_TO_COPY_TRANSCRIPT while connection remains open
```

Keep this probe process running while farm5 captures evidence.

Current recorded evidence status: Windows external probe succeeded (`CONNECTED`, `SUBSCRIBE_AUTHORIZE_SENT`, `READY_TO_COPY_TRANSCRIPT`) and transcript copy to farm5 succeeded.

### Step 3) Copy transcript while connection remains open

While the external probe is still running and holding the connection open, copy transcript JSON to farm5:

```bash
scp /tmp/limited-btc-001-20101-transcript.json root@<farm5-public-ip>:/tmp/limited-btc-001-20101-transcript.json
```

### Step 4) Farm5 terminal (primary execution path)

```bash
cd /opt/mpf-py-src
sudo scripts/phase11e_collect_runtime_stratum_evidence.sh   --operator vahid   --reason "phase11e external runtime stratum evidence collection"   --post-apply-evidence-json /tmp/phase11-single-customer-post-apply-evidence-0.1.205.json   --post-apply-evidence-json-sha256 19ef5602af8ad36267ce34c3ca21e660e32d8970b0a81d69bc80b8a206d41ead   --transcript-json /tmp/limited-btc-001-20101-transcript.json   --wait-for-transcript-seconds 300   --capture-delay-seconds 0   --expected-version 0.1.216

# optional when ASSURED is missing: collect repeated conntrack snapshots
sudo scripts/phase11e_collect_runtime_stratum_evidence.sh   --operator vahid   --reason "phase11e external runtime stratum evidence collection (repeat conntrack)"   --post-apply-evidence-json /tmp/phase11-single-customer-post-apply-evidence-0.1.205.json   --post-apply-evidence-json-sha256 19ef5602af8ad36267ce34c3ca21e660e32d8970b0a81d69bc80b8a206d41ead   --transcript-json /tmp/limited-btc-001-20101-transcript.json   --wait-for-transcript-seconds 300   --capture-delay-seconds 0   --conntrack-repeat-count 5   --conntrack-repeat-delay-seconds 2   --expected-version 0.1.216
```

### Step 5) Review evidence output on farm5

- The helper prints `OK: evidence directory: <path>` on success.
- Review artifacts and `manifest.json` in that output directory.
- `forwarder.log` and `bridge.log` in the artifact directory are the evidence source of truth (captured from docker logs stdout/stderr); do not rely on terminal-visible docker log output.
- Confirm `no_activation_performed=true` and gates remain closed.
- If helper returns `BLOCKED_*`, do not retry blindly; report full output and evidence directory.

## Troubleshooting/reference only (manual classifier path)

Use this section only for troubleshooting. Primary path remains the helper above.

Transcript JSON classifier contract:
- `connect_port = 20101`
- worker includes `limited-btc-001` (or operator-mapped worker includes it)
- `mining.subscribe` response present
- `mining.authorize` result true
- `mining.set_difficulty` or `mining.notify` present

## Operator checklist (must all be YES)

- [ ] Version is `0.1.216`.
- [ ] Current phase gate remains Phase 10 accepted / Phase 11 planning.
- [ ] Probe was external (outside farm5, no hairpin/self path).
- [ ] Probe remained running while farm5 evidence helper captured runtime artifacts.
- [ ] Transcript was copied while connection remained open.
- [ ] `scripts/phase11e_collect_runtime_stratum_evidence.sh` completed or produced explicit BLOCKED evidence.
- [ ] `manifest.json` exists in helper output directory.
- [ ] No DB activation, no customer activation, no production/miner traffic activation performed.
- [ ] Phase 11 acceptance is still not claimed in this step.

This runbook does not authorize or perform production activation.


## Troubleshooting: `BLOCKED_NO_STRATUM_RESPONSE`

Meaning:
- External TCP connect succeeded, but no line-delimited Stratum response arrived before `--ready-timeout-seconds`.

Operator action:
- Do **not** run the farm5 helper yet.
- Send the probe JSON transcript plus full probe stdout/stderr output for review.
- Possible causes include backend not answering Stratum, routing/forwarder bridge issue, pool upstream not responding, wrong worker path, or script/protocol mismatch.
