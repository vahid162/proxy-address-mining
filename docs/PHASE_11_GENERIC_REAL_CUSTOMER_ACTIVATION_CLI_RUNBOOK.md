# Phase 11 Generic Real-Customer Activation CLI Runbook

Version target after sync: `0.1.297`.

This runbook is the focused farm5 next step for `vahid-btc-real-60046` / BTC / public port `60046`. This PR does not authorize uncontrolled production expansion, does not accept Full CLI Production Operations, does not set `production_traffic=cli_production`, and does not open Phase 12, worker enforcement, UI, or Telegram. 60046 is the only current generic real-customer activation candidate.

Any failure must stop and produce evidence. Do not repair iptables manually unless a separate reviewed rollback or emergency procedure explicitly authorizes it. Do not test 60046 externally until controlled apply succeeds and verify passes.

## 0.1.297 verify classifier note

Version 0.1.297 fixes the generic activation verifier so Docker bridge-internal backend ACCEPT rules for `172.18.0.2/32` on `-o br-*` and backend port `60010` do not count as public backend exposure. Real public backend `60010` exposure remains fail-closed. For the already-applied `60046` state, keep the controlled order: verify first, use the existing transcript evidence, run first-connect DB evidence only after verify is READY, rerun abuse coverage, rerun readiness, then stop before final acceptance. This runbook explicitly does not accept Phase 11 or Full CLI Production Operations.

## Commands

Use an evidence directory for all artifacts:

```bash
export EVIDENCE_DIR=/tmp/phase11-generic-activation-0.1.297-vahid-btc-real-60046-$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$EVIDENCE_DIR"
```

Capture a pre-apply read-only `iptables-save` snapshot:

```bash
sudo iptables-save > "$EVIDENCE_DIR/pre-apply.iptables-save"
```

Convert that existing snapshot to official MPF JSON without running live `iptables-save` through MPF:

```bash
mpf production generic-activation-snapshot \
  --iptables-save-file "$EVIDENCE_DIR/pre-apply.iptables-save" \
  --output json > "$EVIDENCE_DIR/pre-apply.snapshot.json"
```

Rebuild the generic activation package through the official CLI:

```bash
mpf production generic-activation-package \
  --customer-key vahid-btc-real-60046 \
  --live-snapshot-file "$EVIDENCE_DIR/pre-apply.snapshot.json" \
  --output json > "$EVIDENCE_DIR/package.json"
```

Record and review the package SHA before continuing:

```bash
jq -r '.package_sha256' "$EVIDENCE_DIR/package.json"
```

Run preflight through the official CLI:

```bash
mpf production generic-activation-preflight \
  --package-file "$EVIDENCE_DIR/package.json" \
  --live-snapshot-file "$EVIDENCE_DIR/pre-apply.snapshot.json" \
  --confirmed-package-sha256 '<PACKAGE_SHA256_FROM_PACKAGE_JSON>' \
  --operator-context 'farm5-reviewed-generic-activation-60046' \
  --output json > "$EVIDENCE_DIR/preflight.json"
```

Build rollback readiness as a contract artifact only:

```bash
mpf production generic-activation-rollback-readiness \
  --package-file "$EVIDENCE_DIR/package.json" \
  --pre-apply-snapshot-file "$EVIDENCE_DIR/pre-apply.snapshot.json" \
  --output json > "$EVIDENCE_DIR/rollback-readiness.json"
```

Stop and review `package.json`, `preflight.json`, and `rollback-readiness.json`. Continue only if the package, preflight, and rollback readiness decisions are READY and the package SHA, customer key, public port, backend target, and snapshot are exactly expected.

Run controlled apply only after review and with every confirmation present:

```bash
MPF_PHASE11_GENERIC_ACTIVATION_APPLY=1 mpf production generic-activation-apply \
  --package-file "$EVIDENCE_DIR/package.json" \
  --preflight-report-file "$EVIDENCE_DIR/preflight.json" \
  --confirmed-package-sha256 '<PACKAGE_SHA256_FROM_PACKAGE_JSON>' \
  --confirmed-customer-key vahid-btc-real-60046 \
  --confirmed-public-port 60046 \
  --pre-apply-snapshot-file "$EVIDENCE_DIR/pre-apply.snapshot.json" \
  --rollback-artifact-path "$EVIDENCE_DIR/rollback-readiness.json" \
  --operator-lock-id 'farm5-generic-activation-60046-<UTC_TIMESTAMP>' \
  --execute \
  --yes \
  --output json > "$EVIDENCE_DIR/apply.json"
```

Capture a post-apply read-only snapshot:

```bash
sudo iptables-save > "$EVIDENCE_DIR/post-apply.iptables-save"
mpf production generic-activation-snapshot \
  --iptables-save-file "$EVIDENCE_DIR/post-apply.iptables-save" \
  --output json > "$EVIDENCE_DIR/post-apply.snapshot.json"
```

Verify the applied DNAT/filter evidence through the official CLI:

```bash
mpf production generic-activation-verify \
  --package-file "$EVIDENCE_DIR/package.json" \
  --live-snapshot-file "$EVIDENCE_DIR/post-apply.snapshot.json" \
  --output json > "$EVIDENCE_DIR/verify.json"
```

Only after verify passes, collect the external Stratum transcript evidence for `85.198.11.110:60046` and save it as JSON:

```bash
cat > "$EVIDENCE_DIR/transcript.json" <<'JSON'
{
  "connect_host": "85.198.11.110",
  "connect_port": 60046,
  "worker_name": "vahid-btc-real-60046.<worker>",
  "authorize_result": true,
  "subscribe_result": ["present"],
  "mining_notify_received": true
}
JSON
```

Import transcript evidence:

```bash
mpf production generic-activation-transcript-import \
  --package-file "$EVIDENCE_DIR/package.json" \
  --transcript-file "$EVIDENCE_DIR/transcript.json" \
  --output json > "$EVIDENCE_DIR/transcript-report.json"
```

Run the first-connect DB evidence update as the `mpf` OS user only after transcript evidence is accepted:

```bash
sudo -u mpf mpf production generic-activation-first-connect-db \
  --customer-key vahid-btc-real-60046 \
  --evidence-sha256 '<TRANSCRIPT_REPORT_EVIDENCE_SHA256>' \
  --operator '<OPERATOR_NAME>' \
  --reason 'Phase 11 generic activation first-connect evidence accepted for 60046' \
  --yes \
  --output json > "$EVIDENCE_DIR/first-connect-db.json"
```

Run abuse coverage readiness:

```bash
mpf production generic-activation-abuse-coverage \
  --customer-key vahid-btc-real-60046 \
  --output json > "$EVIDENCE_DIR/abuse-coverage.json"
```

Assemble final generic activation readiness evidence:

```bash
mpf production generic-activation-readiness \
  --package-report-file "$EVIDENCE_DIR/package.json" \
  --preflight-report-file "$EVIDENCE_DIR/preflight.json" \
  --apply-report-file "$EVIDENCE_DIR/apply.json" \
  --verify-report-file "$EVIDENCE_DIR/verify.json" \
  --transcript-report-file "$EVIDENCE_DIR/transcript-report.json" \
  --first-connect-db-report-file "$EVIDENCE_DIR/first-connect-db.json" \
  --abuse-report-file "$EVIDENCE_DIR/abuse-coverage.json" \
  --activation-mode first_connect \
  --output json > "$EVIDENCE_DIR/readiness.json"
```

Stop before final Phase 11 acceptance. Send the complete evidence directory for review; do not mark Full CLI Production Operations accepted in this runbook.
