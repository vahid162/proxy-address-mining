# Phase 11 farm5 0.1.252 controlled filter packet-path READY evidence

Status: sanitized source-backed evidence summary only. Raw bundle files, MAC addresses, live interface dumps, and sensitive topology dumps are intentionally not committed.

## Evidence identity

- collection id: `controlled-filter-packet-path-20260613T064606Z`
- repository_version: `0.1.252`
- plan_final_decision: `READY_CONTROLLED_FILTER_PACKET_PATH_PROOF`
- collect_final_decision: `READY_CONTROLLED_FILTER_PACKET_PATH_PROOF`
- verify_final_decision: `READY_CONTROLLED_FILTER_PACKET_PATH_PROOF`
- manifest_sha256: `b545cfeef084b911fb442a045248d25d2b049e6008dd841dd4a3944ea60c35e9`
- archive_sha256: `87cae5854c0ed2b26bacbd8233939b88bab0e3ab2667dd7aaad62da71abbe7a9`

## Verified packet-path facts

- verified hook: `DOCKER-USER`
- builtin filter path: `FORWARD`
- packet view at hook: `post_dnat_forward_filter`
- backend container: `mpf-forwarder-btc`
- backend port: `60010`
- backend bridge membership: verified through FDB evidence
- ingress/state scenario matrix: READY for `ens192 + NEW`, `ens192 + ESTABLISHED`, `ens224 + NEW`, and `ens224 + ESTABLISHED`
- DOCKER-USER reached exactly once per scenario
- DOCKER-USER precedes all relevant ACCEPT paths

## Safety boundary

- mutation_performed: `false`
- runtime_packet_observed: `false`
- post_apply_runtime_verified: `false`
- package execution: still blocked
- iptables-restore: not executed by this repository change
- Phase 12, worker enforcement, UI, Telegram, unrestricted production, and public backend exposure remain blocked.
