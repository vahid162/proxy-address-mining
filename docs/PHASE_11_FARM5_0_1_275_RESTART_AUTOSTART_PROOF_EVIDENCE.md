# Phase 11 farm5 0.1.275 Restart/Autostart Proof Evidence

This document centralizes the farm5 `0.1.275` restart/autostart proof evidence that motivated the `0.1.276` strict JSON evidence fix.

## Evidence source

- farm5 version: `0.1.275`
- evidence directory: `/tmp/phase11-restart-autostart-proof-0.1.275-20260615T190637Z`
- backend target: `172.18.0.2:60010`

## Current controlled artifact gate

The farm5 `current-controlled-artifact-gate.json` evidence reported:

- `final_decision=PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS`
- `expected_backend_target=172.18.0.2:60010`
- `known_controlled_artifacts_present=true`
- `unknown_mpf_artifacts=[]`
- `duplicate_controlled_artifact_count=0`
- `duplicate_nat_redirect_count=0`
- `forbidden_public_runtime_exposure=false`
- `production_gates_remain_closed=true`

## Restart/autostart proof payload

The `proof-report.json` payload showed `restart_autostart_proof=ready` and represented the official restart/autostart proof as READY.

However, the file was not strict machine-readable JSON because shell provenance comment lines were prepended before the JSON object:

```text
# command: /usr/local/bin/mpf production restart-autostart-proof --evidence-dir /tmp/phase11-restart-autostart-proof-0.1.275-20260615T190637Z --output json
# captured_at_utc: 2026-06-15T19:06:52Z
{
  "component": "phase11_restart_autostart_proof",
  "repository_version": "0.1.275",
  "restart_autostart_proof": "ready"
}
```

As a result, `python3 -m json.tool proof-report.json` failed with `Expecting value: line 1 column 1 (char 0)` even though the proof itself was READY.

## 0.1.276 fix

Version `0.1.276` keeps command provenance out of official `.json` evidence files and writes provenance for JSON captures to sidecar `.meta.txt` files instead. The official JSON artifacts are intended to remain parseable by `python3 -m json.tool`, including:

- `controlled-backend-target.json`
- `current-controlled-artifact-gate.json`
- `proof-report.json`
- `proof_report.json`

Phase 11 operational completion is still not accepted. `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, and Telegram remain closed.

The next runtime step after READY restart/autostart proof is production customer lifecycle execution.
