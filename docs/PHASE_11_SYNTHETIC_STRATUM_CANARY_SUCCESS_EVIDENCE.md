# Phase 11 Synthetic Stratum Canary Success Evidence (farm5, 0.1.167)

Status: recorded evidence only (non-authorizing)
Date: 2026-05-21

This document records real farm5 evidence after PR #180 / version 0.1.167.

## Scope and boundary

- This is an evidence recording step only.
- No runtime behavior is changed by this document.
- Phase 11 remains not accepted.
- Real customer onboarding remains forbidden (`customer_onboarding_allowed: db_only`).
- Abuse automation remains closed (`abuse_automation_allowed: no`).
- UI remains closed (`ui_allowed: no`).
- Telegram remains closed (`telegram_allowed: no`).

## 0.1.167 farm5 sync/test baseline

- `VERSION`: `0.1.167`
- `mpf --version`: `0.1.167`
- `python -m pytest -q`: `870 passed`
- `mpf doctor`: `OK`
- `mpf db status`: `OK`
- `mpf proxy doctor`: `OK`

## Bridge runtime and route-safe path baseline

- `proxy_container_state` is `OK` and includes `mpf-v2raya-socks-bridge`.
- `mpf-v2raya-socks-bridge` is `Up / healthy`.
- `docker exec mpf-forwarder-btc nc -zv mpf-v2raya 22070` returned `rc=0`.
- v2rayA UI remained local-only.
- BTC backend remained local-only.
- SOCKS bridge had no host publish.
- Route-safe single-canary NAT path remained active and controlled.

## Synthetic Stratum evidence (Windows)

Client connection target:

- `85.198.11.110:20001`

Request 1:

```json
{"id":1,"method":"mining.subscribe","params":["mpf-canary-windows-test/0.1"]}
```

Response 1:

```json
{"id": 1, "result": [[["mining.set_difficulty", "..."], ["mining.notify", "..."]], "...", 4], "error": null}
```

Request 2:

```json
{"id":2,"method":"mining.authorize","params":["canary-test.worker","x"]}
```

Response 2:

```json
{"id": 2, "result": true, "error": null}
```

Additional notifications observed:

- `mining.set_difficulty`
- `mining.notify`

## Post-test farm5 dataplane evidence

- `MPF_NAT_PRE` counter increased to `14 packets / 696 bytes`.
- conntrack showed an `ASSURED` flow:
  - `src=213.195.38.238 dst=85.198.11.110 sport=47806 dport=20001`
  - `src=172.18.0.3 dst=213.195.38.238 sport=60010 dport=47806`
  - `[ASSURED]`
- `mpf-forwarder-btc` logs showed:
  - `213.195.38.238:47806 -> 172.18.0.3:60010`
  - `213.195.38.238:47806 <-> bitcoin.viabtc.io:3333`
- `mpf-v2raya-socks-bridge` logs showed:
  - `172.18.0.3 -> 172.18.0.2:22070`
  - `172.18.0.3 <-> 127.0.0.1:20170`

## Health remained OK after test

- `mpf doctor`: `OK`
- `mpf db status`: `OK`
- `mpf proxy doctor`: `OK`

## Gate outcome

Strong canary evidence is now recorded for synthetic Stratum subscribe/authorize success across the controlled path. This evidence is necessary for review, but by itself it is not full Phase 11 acceptance.
