# Operator Troubleshooting Evidence Contract

Status: Phase 5-F1 contract (documentation-only)

## Scope and phase gate

Phase 5 is **DB-only**: `current_working_phase: Phase 5 — Customer CRUD in DB Only`.
This document defines an operator-facing troubleshooting evidence contract for future phases; it does **not** authorize runtime evidence collection in Phase 5.

- Runtime impact: none.
- Firewall impact: none.
- Database migration impact: none in the current phase.

Strictly forbidden in Phase 5:
- no migration
- no model changes
- no collector
- no packet capture
- no conntrack/tcpdump job
- no firewall/NAT
- no iptables path
- no systemd timer
- no usage collector
- no worker scanner
- no abuse automation
- no UI/Telegram/public API
- no DB mutation
- no runtime evidence collection

## Ownership and future placement

- Phase 6 owns firewall planner evidence.
- Phase 7 owns usage/policy/reject accounting.
- Phase 8 owns abuse runtime.
- Phase 9 owns check/report/diagnostic verdicts.
- Phase 10 owns session/worker/policy timeline.

Future commands to consume this contract:
- `mpf check <customer>`
- `mpf report <customer>`
- `mpf monitor port <customer>`
- `mpf diag <customer>`
- `mpf workers <customer>`
- `mpf timeline <customer>`

## Evidence confidence classes

Each future evidence record and verdict must include `evidence_confidence`:
- `observed`
- `inferred`
- `sampled`
- `operator_reported`
- `untrusted`

## Data references (future runtime tables/services)

Tables/concepts referenced by this contract:
- `customers`
- `customer_policies`
- `customer_ip_pins`
- `usage_samples`
- `policy_events`
- `flow_sessions`
- `flow_events`
- `worker_events`
- `customer_workers`
- `worker_identities`
- `abuse_states`
- `abuse_events`
- `firewall_applies`
- `firewall_rules_desired`
- `firewall_rules_live`
- `share_events` (future-only)
- hashrate samples (future-only)

Service owners (future):
- `customer_service`
- `firewall_service`
- `usage_service`
- `policy_event_service`
- flow/session service
- `worker_observation_service`
- `abuse_service`
- report/check service

## Scenario contract matrix (future-only)

For every scenario below, operator verdicts are defined now, but runtime collection starts only in later accepted phases.

1) customer cannot connect  
Required evidence: customer status/policy, lane/port mapping, latest flow/session attempt, policy events.  
Future table(s): `customers`, `customer_policies`, `flow_sessions`, `flow_events`, `policy_events`.  
Future service owner: `customer_service`, flow/session service, report/check service.  
Future command: `mpf check <customer>`, `mpf diag <customer>`.  
Phase placement: 9/10.  
Forbidden in Phase 5: no runtime probes/collectors.  
Expected verdict: connection denied due to missing/inactive policy OR no observed session evidence yet.

2) customer connects from unexpected IP  
Required evidence: source IP observation vs IP pin/allow list, timestamped policy version.  
Future table(s): `customer_ip_pins`, `flow_sessions`, `flow_events`, `policy_events`.  
Future service owner: `customer_service`, flow/session service, report/check service.  
Future command: `mpf report <customer>`, `mpf diag <customer>`.  
Phase placement: 9/10.  
Forbidden in Phase 5: no runtime IP evidence collector.  
Expected verdict: unexpected source IP observed, policy action required.

3) whitelist reject  
Required evidence: reject reason classification and policy snapshot.  
Future table(s): `policy_events`, `flow_events`, `customer_ip_pins`.  
Future service owner: `firewall_service`, `policy_event_service`, report/check service.  
Future command: `mpf check <customer>`, `mpf report <customer>`.  
Phase placement: 7/9.  
Forbidden in Phase 5: no reject runtime accounting path.  
Expected verdict: reject was whitelist-related, not backend outage.

4) maxconn/connlimit issue  
Required evidence: concurrent session count and connlimit reject reason.  
Future table(s): `usage_samples`, `flow_sessions`, `flow_events`, `policy_events`.  
Future service owner: `usage_service`, flow/session service, report/check service.  
Future command: `mpf monitor port <customer>`, `mpf diag <customer>`.  
Phase placement: 7/9/10.  
Forbidden in Phase 5: no session counter collector.  
Expected verdict: connection rejected by maxconn/connlimit policy.

5) hashlimit/rate issue  
Required evidence: per-window rate checks and reject reason.  
Future table(s): `usage_samples`, `flow_events`, `policy_events`.  
Future service owner: `usage_service`, `policy_event_service`, report/check service.  
Future command: `mpf monitor port <customer>`, `mpf report <customer>`.  
Phase placement: 7/9.  
Forbidden in Phase 5: no runtime rate accounting.  
Expected verdict: connection throttled/rejected by hashlimit/rate policy.

6) backend reachable but pool/upstream issue  
Required evidence: internal backend reachable = OK, upstream/pool unavailable or failing.  
Future table(s): `flow_events`, `policy_events`.  
Future service owner: flow/session service, report/check service.  
Future command: `mpf check <customer>`, `mpf diag <customer>`.  
Phase placement: 9/10.  
Forbidden in Phase 5: no upstream health runtime collector.  
Expected verdict: backend internal path healthy, upstream/pool problem likely.

7) worker mismatch  
Required evidence: worker authorize identity mismatch with expected customer mapping.  
Future table(s): `worker_events`, `customer_workers`, `worker_identities`, `flow_sessions`.  
Future service owner: `worker_observation_service`, flow/session service, report/check service.  
Future command: `mpf workers <customer>`, `mpf timeline <customer>`.  
Phase placement: 10.  
Forbidden in Phase 5: no worker scanner/runtime parser.  
Expected verdict: worker identity mismatch detected.

8) multiple IPs/workers over time  
Required evidence: time-windowed IP and worker timeline.  
Future table(s): `flow_sessions`, `worker_events`, `customer_workers`, `worker_identities`.  
Future service owner: flow/session service, `worker_observation_service`, report/check service.  
Future command: `mpf timeline <customer>`, `mpf workers <customer>`.  
Phase placement: 10.  
Forbidden in Phase 5: no multi-source runtime timeline collector.  
Expected verdict: multi-IP/multi-worker pattern observed with confidence class.

9) first-connect activation evidence  
Required evidence: first seen session marker and activation trail.  
Future table(s): `flow_sessions`, `policy_events`, `customers`.  
Future service owner: flow/session service, `customer_service`, report/check service.  
Future command: `mpf timeline <customer>`, `mpf report <customer>`.  
Phase placement: 10.  
Forbidden in Phase 5: no first-connect runtime detector.  
Expected verdict: first-connect activation observed (future-only runtime).

10) accepted/rejected share and hash-rate evidence  
Required evidence: accepted/rejected share events and derived hashrate samples.  
Future table(s): `share_events` and hashrate samples (future-only concepts).  
Future service owner: `worker_observation_service`, `usage_service`, report/check service.  
Future command: `mpf report <customer>`, `mpf workers <customer>`.  
Phase placement: 9/10 (after retention/partition review).  
Forbidden in Phase 5: no share/hashrate runtime collector.  
Expected verdict: shares/hashrate trend indicates normal/reject-heavy behavior.

11) abuse evidence timeline  
Required evidence: over-threshold timestamps, state transitions, policy version, restore point linkage at hard action time.  
Future table(s): `abuse_states`, `abuse_events`, `flow_sessions`, `worker_events`, `policy_events`.  
Future service owner: `abuse_service`, `policy_event_service`, report/check service.  
Future command: `mpf timeline <customer>`, `mpf diag <customer>`.  
Phase placement: 8/10.  
Forbidden in Phase 5: no abuse runtime automation.  
Expected verdict: normal -> over_tracking -> over_grace -> hard timeline.

12) customer exists but has no future firewall eligibility  
Required evidence: policy eligibility checks and lane/port validity.  
Future table(s): `customers`, `customer_policies`, `policy_events`, `firewall_rules_desired`.  
Future service owner: `customer_service`, `firewall_service`, report/check service.  
Future command: `mpf check <customer>`.  
Phase placement: 6/9.  
Forbidden in Phase 5: no firewall planning/apply runtime mutation.  
Expected verdict: customer record exists but policy is not eligible for future firewall realization.

13) expired/paused/deleted customer attempts connection  
Required evidence: lifecycle status and observed attempts timeline.  
Future table(s): `customers`, `flow_sessions`, `flow_events`, `policy_events`.  
Future service owner: `customer_service`, flow/session service, report/check service.  
Future command: `mpf check <customer>`, `mpf timeline <customer>`.  
Phase placement: 9/10.  
Forbidden in Phase 5: no runtime status-enforcement collector.  
Expected verdict: runtime attempt conflicts with customer lifecycle state.

14) backend internal reachable but external backend exposure detected  
Required evidence: internal_backend_reachable = OK and external_backend_exposed = YES/NO split.  
Future table(s): `firewall_rules_live`, `firewall_applies`, `policy_events`.  
Future service owner: `firewall_service`, report/check service.  
Future command: `mpf check <customer>`, `mpf diag <customer>`.  
Phase placement: 6/9.  
Forbidden in Phase 5: no live firewall apply/exposure mutation path.  
Expected verdict: internal reachability preserved while external exposure is denied.

15) wrong customer port / port collision diagnosis  
Required evidence: lane port map, collision record, customer-supplied port vs assigned port.  
Future table(s): `customers`, `customer_policies`, `policy_events`, `firewall_rules_desired`.  
Future service owner: `customer_service`, `firewall_service`, report/check service.  
Future command: `mpf check <customer>`, `mpf report <customer>`.  
Phase placement: 5/6/9.  
Forbidden in Phase 5: no runtime traffic diagnosis collector.  
Expected verdict: wrong/duplicate port assignment caused connect failure.

16) duplicate worker names from multiple source IPs  
Required evidence: same worker label across distinct source IP sessions.  
Future table(s): `worker_events`, `worker_identities`, `flow_sessions`, `customer_workers`.  
Future service owner: `worker_observation_service`, flow/session service, report/check service.  
Future command: `mpf workers <customer>`, `mpf timeline <customer>`.  
Phase placement: 10.  
Forbidden in Phase 5: no worker/IP runtime correlation collector.  
Expected verdict: duplicate worker name observed across multiple IPs.

17) stale sessions after policy change or future abuse hard  
Required evidence: session start/end vs policy change/hard timestamp and cleanup evidence.  
Future table(s): `flow_sessions`, `policy_events`, `abuse_events`, `firewall_applies`.  
Future service owner: flow/session service, `abuse_service`, `firewall_service`, report/check service.  
Future command: `mpf timeline <customer>`, `mpf diag <customer>`.  
Phase placement: 8/10.  
Forbidden in Phase 5: no conntrack/session cleanup runtime job.  
Expected verdict: stale sessions persisted/cleared after policy transition.

18) time-sync-dependent evidence warning  
Required evidence: clock health and evidence timestamp drift checks.  
Future table(s): `policy_events`, `flow_events`, `worker_events`, `abuse_events`.  
Future service owner: report/check service, `policy_event_service`.  
Future command: `mpf diag <customer>`, `mpf report <customer>`.  
Phase placement: 9/10.  
Forbidden in Phase 5: no runtime time-sync enforcement job.  
Expected verdict: timestamps are trusted OR warning: time sync quality insufficient.

## Safety invariants

- Active customers must remain abuse-evaluable in all enabled lanes; no troubleshooting path may silently exclude them.
- Troubleshooting evidence must not create any path that excludes active customers from future abuse evaluation.
- Worker identity must not be treated as firewall-only.
- Backend ports must remain internal-only, while valid internal reachability must remain allowed.

## Retention and high-volume guard

No high-volume collector may be activated without retention policy.
Troubleshooting evidence must define retention class before runtime collection.
