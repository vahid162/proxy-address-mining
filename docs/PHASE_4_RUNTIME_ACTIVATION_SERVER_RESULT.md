# Phase 4 Runtime Activation Server Result — Limited Proxy Runtime Startup

Status: accepted server evidence pending final phase-status promotion

Server: `farm5`

Evidence timestamp:

```text
2026-05-09T16:25:09+03:30
```

## Scope

A limited Phase 4 proxy runtime activation was executed on `farm5` using the guarded operator script:

```bash
sudo bash /opt/mpf-py-src/scripts/phase4_runtime_activation_execute.sh start
```

This result accepts only the limited proxy runtime startup evidence.
It does not authorize production customer traffic, customer NAT redirects, customer firewall rules, firewall apply, usage timers, abuse automation, UI, Telegram, or customer mutation.

## Accepted Runtime Evidence

```text
server source aligned with GitHub ZIP
pytest passed: 60 passed
mpf config validate OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf proxy config-check final_verdict: OK
mpf-v2raya container started
mpf-forwarder-btc container started
mpf-v2raya health: healthy
mpf-forwarder-btc health: healthy
v2rayA UI host/operator listener: 127.0.0.1:2015
v2rayA UI container target port: 2017
BTC backend listener: 127.0.0.1:60010
BTC backend internal reachability: OK
Docker Compose profile: phase4-runtime
Docker image source for v2rayA: mzz2017/v2raya:latest
Docker image source for forwarder: ginuerzh/gost:latest
```

## Safety Evidence

```text
production_traffic: none
customers: 0
job_runs: 0
firewall_applies: 0
abuse_states: 0
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
no MPF/customer firewall references detected
no MPF customer NAT redirects detected
no customer firewall chains detected
no usage timers activated
no abuse automation activated
no UI service activated
no Telegram bot activated
no public v2rayA UI exposure detected
no public BTC backend exposure detected
```

## Listener Evidence

```text
127.0.0.1:2015 -> mpf-v2raya container port 2017
127.0.0.1:60010 -> mpf-forwarder-btc container port 60010
```

No `0.0.0.0:2015`, `0.0.0.0:60010`, `[::]:2015`, or `[::]:60010` listener was observed.

## Docker Firewall Notes

Docker created local publish rules for the local-only listeners:

```text
127.0.0.1:2015 -> 172.18.0.2:2017
127.0.0.1:60010 -> 172.18.0.3:60010
```

These are Docker-managed local publish rules, not MPF customer NAT redirects.
They are accepted only because listener binding checks confirmed local-only exposure.

MPF/customer chains remain absent:

```text
MPF
MPFBTC
MPFC_
MPFO_
```

## Backup Artifact

The runtime activation script created this backup:

```text
/var/backups/mpf/phase4-runtime-activation-20260509T125512Z
```

The sync step before runtime created this backup:

```text
/var/backups/mpf/source-before-zip-sync-20260509T125458Z
```

## Remaining Proxy Doctor Warning

`mpf proxy status` and `mpf proxy doctor` still reported `WARN` because the repository phase guard still described runtime activation as review-only at the time of evidence capture.

The warning is expected for that code state and should be resolved by the follow-up phase-status/proxy-doctor promotion patch after CI is green.

## Still Forbidden After This Result

```text
customer CRUD mutation
customer NAT redirects
customer firewall rules
firewall apply
iptables-restore
usage timers
hash-rate/share collectors
abuse automation
block/pause automation
local UI service
buyer UI service
Telegram bot
production customer import
worker enforcement
public API binding
public v2rayA UI exposure
public backend exposure
```

## Next Step

Promote the repository phase state from runtime activation review to accepted limited Phase 4 runtime activation, then begin Phase 5 planning for DB-only customer CRUD.

Phase 5 must remain DB-only until a later firewall/NAT phase is accepted.
