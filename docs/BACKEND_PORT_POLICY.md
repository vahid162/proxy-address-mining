# Backend Port Policy

0.1.251 note: controlled artifact reapply resolves the current BTC backend target from the running `mpf-forwarder-btc` container on `mpf-proxy-internal`; historical Docker IPs are compatibility evidence only and are not current runtime truth. Host listener `60010` must remain local-only and public Docker publishes block execution.


Status: active firewall and proxy contract

Backend ports are internal service ports used by MPF lanes.

The first backend port is:

```text
BTC backend: 60010
```

Future lanes such as ZEC and LTC will have their own backend ports.

## Core Invariant

Backend ports must be closed to direct external/public access, but they must remain reachable from valid internal server and Docker paths.

Required state:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Both checks are mandatory. Passing one does not replace the other.

## Why This Matters

The MPF data path requires the backend to be reachable internally:

```text
customer_port
  -> firewall policy
  -> NAT redirect
  -> lane backend port
  -> forwarder/gost
  -> v2rayA
  -> pool
```

If the backend is blocked from inside the server, then legitimate customer traffic redirected by MPF cannot reach the forwarder.

If the backend is exposed from outside, attackers can bypass customer-facing policy and connect directly to the backend.

## Required Behavior

Backend ports must be:

```text
reachable from loopback when intentionally bound there
reachable from required local server paths
reachable from required Docker/internal bridge paths
reachable from MPF-owned NAT redirect path, once that phase is active
not reachable by direct external/public interface access
not published publicly by Docker
not exposed through v2rayA UI or unrelated service bindings
```

## Forbidden Firewall Behavior

Do not hide backend ports by breaking internal routing.

Forbidden:

```text
OUTPUT drops for backend ports as a normal guard
blocking loopback access to backend ports
blocking required Docker/internal bridge access
blocking MPF-owned NAT redirect path
marking internal reachability failure as healthy
allowing public inbound access to backend ports
publishing backend ports on 0.0.0.0 through Docker
```

## Required Doctor Checks

Proxy/firewall doctor must report these separately:

```text
backend_internal_reachability
backend_external_exposure
backend_docker_publish_mode
backend_listener_bind_address
backend_nat_path_readiness
```

Expected verdicts:

```text
backend_internal_reachability = OK
backend_external_exposure = OK when no exposure exists
backend_docker_publish_mode = OK only when no public publish exists
```

Critical failures:

```text
internal backend is unreachable from required internal path
backend is reachable from a public interface directly
Docker publishes backend port publicly
v2rayA UI is reachable publicly
NAT path points to the wrong backend
```

## Phase 4 Requirements

Before starting proxy data-plane containers, Phase 4 planning must define:

```text
listener bind address for each backend
Docker Compose port publish strategy
local-only v2rayA UI bind strategy
internal reachability probe
external exposure probe
stop/rollback plan
```

During Phase 4 runtime activation, no customer NAT redirect may be created yet.

## Firewall Planner Requirements

When Phase 6 firewall planner is implemented, it must preserve this distinction:

```text
external direct backend access is rejected or dropped
internal path remains usable
```

The planner must not generate rules that make the backend unreachable from legitimate internal paths.

## Tests Required

Minimum tests before backend guard acceptance:

```text
public backend exposure is detected
localhost/internal backend reachability is detected
Docker public publish is detected
Docker localhost-only publish is accepted when appropriate
internal reachability failure is critical
external exposure failure is critical
backend guard does not use normal OUTPUT drops
wrong backend NAT target is detected
```

## Operator Output Requirement

Any doctor/check output must use clear wording:

```text
Internal backend reachability: OK/CRITICAL
External backend exposure: OK/CRITICAL
```

Do not collapse these into one vague backend status.


0.1.251 controlled runtime-forward note: the source-backed controlled artifact renderer, schema-faithful metadata wiring, and production adapters are implemented, but the filter packet path remains fail-closed until source-backed farm5 evidence proves the correct hook for exactly `canary-btc-001/btc/20001` and `limited-btc-001/btc/20101`. No farm5 mutation was performed, no live `iptables-restore` was executed during PR development or CI, and no READY farm5 package has been collected. Progression is now `read_only_reapply_foundation_implemented=true`, `desired_artifact_semantics_complete=false`, `production_execution_available=false`, `live_ready_package_available=false`, and `controlled_artifact_reapply_package_evidence_ready=false`. The exact next step is `sync_and_collect_controlled_filter_packet_path_evidence_on_farm5`; server sync is allowed only for read-only package/evidence collection first, and controlled execution requires separate package review. `restart_autostart_proof` remains `missing_or_partial`; Full CLI Production Operations remains unaccepted; `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, timers, and daemons remain blocked.
