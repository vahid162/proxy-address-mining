# Phase 11D Farm5 Manual Canary Execution Runbook

## Prerequisites
- Sync latest `main` on farm5.
- Confirm version is `0.1.173`.
- Do **not** onboard real customers.

## Preflight
- `python -m pytest -q`
- `bash scripts/verify_current_phase_gate.sh`
- `mpf phase-status`
- `mpf doctor`
- `mpf db status`
- `mpf proxy doctor`

## Plan mode (default)
- `mpf production manual-canary-execute --output json > canary-plan.json`

## Execute mode (single explicit canary only)
```bash
MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP=allow \
mpf production manual-canary-execute \
  --requested-action execute \
  --customer-key canary-btc-001 \
  --lane btc \
  --port 20001 \
  --miners 1 \
  --farms 1 \
  --maxconn 1 \
  --expected-version 0.1.173 \
  --operator-confirmed \
  --i-understand-this-can-create-a-canary-customer \
  --i-understand-this-can-apply-firewall \
  --i-have-reviewed-rollback \
  --i-have-fresh-farm5-sync \
  --operator "<operator-name>" \
  --reason "Phase 11D single canary execution on farm5" \
  --output json > canary-execute.json
```

## Evidence to collect
- `canary-plan.json`
- `canary-execute.json`
- `mpf doctor`, `mpf phase-status`, `mpf db status`, `mpf proxy doctor`
- listener/NAT/firewall status outputs required by reviewer.

## Failure / rollback
- Stop immediately on `BLOCKED` or `EXECUTION_FAILED`.
- Use restore/backup references in JSON output.
- Send failure evidence for review before any new attempt.

## Safety reminders
- Phase 11 remains unaccepted until evidence is reviewed and accepted.
- Limited real customer onboarding remains forbidden until canary evidence is accepted.

> Note: This command is a readiness contract and is expected to return BLOCKED when real production execution adapters are not wired yet.

## Phase 11E adapter wiring note
- Execute mode is now wired to production service-layer adapters.
- Actual host apply remains BLOCKED in this PR; no real host apply executor is wired in production.
- Do **not** run real customer onboarding.

## Restore/backup context guard

- execute-control now requires `MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP=allow` in addition to exact scope, expected version, approvals, and phase safety checks.
- plan command:
  - `mpf production manual-canary-execute --output json`
- execute-control command:
  - `MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP=allow mpf production manual-canary-execute --requested-action execute --customer-key canary-btc-001 --lane btc --port 20001 --miners 1 --farms 1 --maxconn 1 --expected-version 0.1.173 --operator-confirmed --i-understand-this-can-create-a-canary-customer --i-understand-this-can-apply-firewall --i-have-reviewed-rollback --i-have-fresh-farm5-sync --operator "<operator-name>" --reason "Phase 11H restore backup boundary check" --output json`
- exact payload renderer behavior: execute path now renders deterministic exact payload for canary-btc-001/btc/20001->60010 after restore+backup+diff checks.
- expected blocker without host-apply context guard: `single_canary_host_apply_context_not_confirmed`.
- expected blocker with both restore-backup and host-apply context guards enabled: `accepted_single_canary_host_apply_execution_missing`.
- warning: no production traffic, no real customer onboarding, no abuse automation, no UI/Telegram, and no host apply in this PR.

## Two execute-control checks (required)

1) Renderer-only execute-control (host apply context NOT enabled)

```bash
MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP=allow \
mpf production manual-canary-execute \
  --requested-action execute \
  --customer-key canary-btc-001 \
  --lane btc \
  --port 20001 \
  --miners 1 \
  --farms 1 \
  --maxconn 1 \
  --expected-version 0.1.173 \
  --operator-confirmed \
  --i-understand-this-can-create-a-canary-customer \
  --i-understand-this-can-apply-firewall \
  --i-have-reviewed-rollback \
  --i-have-fresh-farm5-sync \
  --operator "<operator-name>" \
  --reason "Phase 11I renderer-only execute-control check" \
  --output json
```

Expected: `restore_payload_renderer.status=ok`, `firewall_plan.restore_payload` present, `final_decision=BLOCKED`, blocker `single_canary_host_apply_context_not_confirmed`, all mutation flags false, all safety flags false.

2) Pre-host-apply missing-executor execute-control (both guards enabled)

```bash
MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP=allow \
MPF_PHASE11_SINGLE_CANARY_HOST_APPLY=allow \
mpf production manual-canary-execute \
  --requested-action execute \
  --customer-key canary-btc-001 \
  --lane btc \
  --port 20001 \
  --miners 1 \
  --farms 1 \
  --maxconn 1 \
  --expected-version 0.1.173 \
  --operator-confirmed \
  --i-understand-this-can-create-a-canary-customer \
  --i-understand-this-can-apply-firewall \
  --i-have-reviewed-rollback \
  --i-have-fresh-farm5-sync \
  --operator "<operator-name>" \
  --reason "Phase 11I pre-host-apply missing-executor check" \
  --output json
```

Expected: `restore_payload_renderer.status=ok`, `firewall_plan.restore_payload` present, `final_decision=BLOCKED`, blocker `accepted_single_canary_host_apply_execution_missing`, `missing_primitive=accepted_single_canary_host_apply_execution`, all mutation flags false, all safety flags false.

No real host apply executor is wired in production in this PR.

Warnings remain: no production traffic, no real customer onboarding, no abuse automation, no UI, no Telegram, and no host apply implementation in this PR.

## Route-safe successful evidence (farm5, 0.1.164)

- Recorded in `docs/PHASE_11_ROUTE_SAFE_CANARY_NAT_SUCCESS_EVIDENCE.md`.
- External TCP test succeeded to `85.198.11.110:20001` and conntrack showed `ASSURED` flow to `172.18.0.3:60010`.
- NAT evidence confirms exact single-canary DNAT rule and no loopback canary target.

### Important boundary clarification

- TCP/NAT success is **not** full Phase 11 acceptance.
- Current State in `docs/PHASE_STATUS.md` remains authoritative and unchanged (`production_traffic: none`, `customer_onboarding_allowed: db_only`, `abuse_automation_allowed: no`, `ui_allowed: no`, `telegram_allowed: no`).
- Limited real customer onboarding remains forbidden until canary evidence is formally accepted.

### Next required validation before onboarding review

- miner/Stratum canary validation on the same controlled single-canary scope
- usage visibility evidence
- reject visibility evidence
- session visibility evidence
- reviewer sign-off that Phase 11 remains unaccepted until all required evidence is accepted


### v2rayA SOCKS reachability check

```bash
docker exec mpf-forwarder-btc sh -c 'nc -zv mpf-v2raya 22070; echo rc=$?'
```

Expected: `rc=0` before synthetic Stratum validation.


## Successful synthetic Stratum canary evidence (farm5 0.1.167)

This section records a successful synthetic Stratum validation path and can be reused for reviewer-facing evidence collection. It does not, by itself, mark Phase 11 as accepted.

### Windows PowerShell raw ASCII test

```powershell
$client = New-Object System.Net.Sockets.TcpClient("85.198.11.110", 20001)
$stream = $client.GetStream()
$writer = New-Object System.IO.StreamWriter($stream, [System.Text.Encoding]::ASCII)
$writer.NewLine = "`n"
$writer.AutoFlush = $true
$reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::ASCII)

$writer.WriteLine('{"id":1,"method":"mining.subscribe","params":["mpf-canary-windows-test/0.1"]}')
$resp1 = $reader.ReadLine()
$writer.WriteLine('{"id":2,"method":"mining.authorize","params":["canary-test.worker","x"]}')
$resp2 = $reader.ReadLine()

"subscribe response: $resp1"
"authorize response: $resp2"

1..4 | ForEach-Object { if ($stream.DataAvailable) { "notify: " + $reader.ReadLine() } }

$reader.Close(); $writer.Close(); $stream.Close(); $client.Close()
```

### Farm5 evidence commands

```bash
mpf phase-status
mpf doctor
mpf db status
mpf proxy doctor

docker exec mpf-forwarder-btc sh -c 'nc -zv mpf-v2raya 22070; echo rc=$?'
docker exec mpf-forwarder-btc sh -c 'iptables -t nat -L MPF_NAT_PRE -n -v --line-numbers'
docker exec mpf-forwarder-btc sh -c 'conntrack -L | grep 20001 || true'
docker logs --tail 200 mpf-forwarder-btc
docker logs --tail 200 mpf-v2raya-socks-bridge
```

### Interpretation boundary

- Synthetic Stratum subscribe/authorize success with NAT + conntrack ASSURED + forwarder/bridge evidence is strong canary evidence.
- It is still not full Phase 11 acceptance by itself.
- Keep Current State unchanged: `production_traffic: none`, `firewall_apply_allowed: no`, `customer_onboarding_allowed: db_only`, `abuse_automation_allowed: no`, `ui_allowed: no`, `telegram_allowed: no`.


Historical executed-evidence note (farm5 0.1.167): `--expected-version 0.1.167` was used for the successful synthetic Stratum evidence capture.


## Canary acceptance review verifier (read-only / non-mutating)

Run:

```bash
mpf production canary-acceptance-review --customer-key canary-btc-001 --lane btc --port 20001 --expected-version 0.1.173 --farm5-baseline-version 0.1.168 --output json
```

Optional evidence JSON input (`--evidence-json /path/to/evidence.json`):

```json
{
  "evidence_reference": "farm5-2026-05-22-canary-evidence",
  "nat_counter_packets": 14,
  "nat_counter_bytes": 696,
  "conntrack_assured": true,
  "stratum_subscribe_ok": true,
  "stratum_authorize_ok": true,
  "stratum_set_difficulty_seen": true,
  "stratum_notify_seen": true,
  "forwarder_pool_seen": true,
  "bridge_loopback_seen": true,
  "proxy_doctor_ok": true,
  "bridge_healthy": true
}
```

This command is read-only and non-mutating: it does not apply firewall, does not run `iptables-restore`, does not flush conntrack, and does not modify customer/firewall/NAT state.


## Read-only live canary evidence collector

```bash
mpf production canary-evidence-collect --customer-key canary-btc-001 --lane btc --port 20001 --expected-version 0.1.173 --farm5-baseline-version 0.1.168 --output json
```

```bash
mpf production canary-acceptance-review --customer-key canary-btc-001 --lane btc --port 20001 --expected-version 0.1.173 --farm5-baseline-version 0.1.168 --collect-live --output json
```
