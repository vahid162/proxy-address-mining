# Phase 11 Route-safe Single-Canary NAT Success Evidence (farm5, 0.1.164)

Status: recorded evidence (pending review)
Date: 2026-05-21

This document records farm5 evidence for one explicit operator-approved route-safe single-canary DNAT execution after sync to version `0.1.164`.

## Scope and Gate Safety

- Current accepted phase remains **Phase 10**.
- Current working phase remains **Phase 11 planning/readiness**.
- This evidence does **not** mark Phase 11 accepted.
- This evidence does **not** authorize limited real customer onboarding.
- abuse_automation_allowed remains `no`.
- ui_allowed remains `no`.
- telegram_allowed remains `no`.

## Execution Command

```bash
MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP=allow MPF_PHASE11_SINGLE_CANARY_HOST_APPLY=allow MPF_PHASE11_SINGLE_CANARY_HOST_APPLY_EXECUTE=allow MPF_PHASE11_SINGLE_CANARY_NAT_HOOK_BOOTSTRAP=allow mpf production manual-canary-execute   --requested-action execute   --customer-key canary-btc-001   --lane btc   --port 20001   --miners 1   --farms 1   --maxconn 1   --expected-version 0.1.164   --operator-confirmed   --i-understand-this-can-create-a-canary-customer   --i-understand-this-can-apply-firewall   --i-have-reviewed-rollback   --i-have-fresh-farm5-sync   --operator "vahid"   --reason "Phase 11 route-safe single-canary DNAT apply after 0.1.164 sync"   --output json
```

## Execution Result

- `final_decision=EXECUTION_COMPLETED_PENDING_REVIEW`
- `actual_canary_execution_performed=true`
- `mutation_performed=true`
- `firewall_mutation_performed=true`
- `nat_mutation_performed=true`
- `production_traffic_enabled=true`
- `customer_db_mutation_performed=false`
- `abuse_automation_authorized=false`
- `ui_authorized=false`
- `telegram_authorized=false`

### Route-safe Resolver Target

- `container_name=mpf-forwarder-btc`
- `target_host=172.18.0.3`
- `target_port=60010`
- `target_kind=docker_container_ipv4`
- `backend_public_exposure=false`
- `host_backend_reachability=true`

### Rendered DNAT Payload

```text
-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.3:60010
```

## Final NAT Evidence

- `MPF_NAT_PRE` exists.
- `PREROUTING -> MPF_NAT_PRE` exists.
- Exactly one canary rule exists: `--dport 20001 -> 172.18.0.3:60010`.
- No `127.0.0.1:60010` canary target remains.
- Docker local publish remains informational: `127.0.0.1:60010 -> 172.18.0.3:60010`.
- Backend listener remains local-only: `127.0.0.1:60010`.
- v2rayA UI remains local-only: `127.0.0.1:2015`.
- Docker bridge target allow rule exists for `172.18.0.3:60010`.

## External TCP Validation

Command:

```powershell
Test-NetConnection 85.198.11.110 -Port 20001 -InformationLevel Detailed
```

Result:

- `TcpTestSucceeded=True`

## Post-test Runtime Evidence

- `MPF_NAT_PRE` counter increased: `2 packets / 104 bytes`.
- conntrack showed ASSURED flow:
  - `src=213.195.38.216 dst=85.198.11.110 sport=46776 dport=20001`
  - `src=172.18.0.3 dst=213.195.38.216 sport=60010 dport=46776`
  - `[ASSURED]`

## Backup Evidence

- backup path:
  `/var/backups/mpf/phase11-single-canary/iptables-save-farm5-20260521T135345Z.txt`
- sha256:
  `61d669d302e57a3136e2cf49c3052546a5cf2b2d18d9139daeaacb3dc3bd4367`

## Interpretation

This is **route-safe TCP/NAT success evidence** for one explicit single canary under controlled approval flags. It is **not** full Phase 11 acceptance. Next validation must include miner/Stratum canary behavior and usage/reject/session visibility evidence before any limited real customer onboarding is reviewed.
