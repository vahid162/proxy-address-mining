# Phase 11 v2rayA SOCKS Reachability Blocker (farm5)

Status: evidence record (Phase 11 remains unaccepted)

## Summary

Route-safe single-canary NAT is working, but synthetic Stratum validation fails after reaching `mpf-forwarder-btc` because the configured upstream SOCKS endpoint was unreachable.

## Observed blocker evidence

- `mpf-forwarder-btc` log showed `dial tcp 172.18.0.2:22070: connect: connection refused`.
- Forwarder config used `-F=socks5://mpf-v2raya:22070`.
- v2rayA SOCKS inbound was present only on `127.0.0.1:20170` inside the container and was not reachable from `mpf-forwarder-btc`.
- Connectivity checks from forwarder container showed `mpf-v2raya:22070` unreachable.

## Runtime-readiness fix intent

- Standardize forwarder upstream to Docker-network reachable SOCKS endpoint `v2raya:20170`.
- Keep host exposure safe:
  - v2rayA UI local-only (`127.0.0.1:2015:2017`)
  - BTC backend local-only (`127.0.0.1:60010:60010`)
  - no SOCKS host public publish

## Gate statement

This document does **not** accept Phase 11 and does **not** open production traffic, real onboarding, abuse automation, UI, Telegram, scheduler, worker enforcement, or firewall apply.
