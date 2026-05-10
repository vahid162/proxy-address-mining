# Changelog

## 0.1.18 - 2026-05-10

- Phase 5-E3: add DB-only read-only customer history visibility commands (`customer policies`, `customer events`, `customer audit`, `events latest`) backed by PostgreSQL SELECT/WITH queries only, with no DB mutation and no firewall/NAT/runtime side effects.

## 0.1.17 - 2026-05-10

- Phase 5-E2b: add DB-only read-only customer lifecycle helper/report commands (`customer next-port`, `customer expiring`, `customer expired`, `customer delete-eligible`) with no DB mutation and no firewall/NAT/runtime side effects.

## 0.1.16 - 2026-05-10

- Clarified PR scope/metadata for Phase 5-E2a (show/list only), no additional runtime features.

## 0.1.15 - 2026-05-10

- Phase 5-E2a: fix boolean parsing for read-only customer show mapping in local-peer/psql CSV fallback and add regression tests.

## 0.1.14 - 2026-05-10

- Phase 5-E2a: fix DB-only customer show/list visibility boundaries (service/repo filtering, local-peer read helper fallback, nullable lifecycle mapping, clearer list empty message).

## 0.1.13 - 2026-05-10

- Phase 5-E2: add DB-only read-only customer visibility/report commands (`customer show`, extended `customer list`) with no firewall/NAT/runtime mutation.

## 0.1.12 - 2026-05-10
- Added Phase 5-E1 DB-only `mpf customer` mutation CLI commands (`add/update/renew/disable/delete/set-ips`) with dry-run default, `--yes` write gate, root local-peer safety guard, and no firewall/NAT/runtime mutations.

## 0.1.11 - 2026-05-10
- Fixed Phase 5-E0.1 local-peer DB write guard for lane sync: clear root/operator instruction (`sudo -u mpf ...`) while keeping dry-run default and DB-only safety boundaries.

## 0.1.10 - 2026-05-10
- Added Phase 5-E0 DB-only lane config sync (dry-run default + --yes write), lane sync service/repository path, event/audit writes, and tests.

## 0.1.9 - 2026-05-10
- Implemented Phase 5-D DB-only customer update/renew/disable/soft-delete/set-ips service+repository path with policy versioning, dry-run, event/audit writes, and tests.

## 0.1.8 - 2026-05-10
- Added Phase 5-C DB-only create-only customer mutation service path with write repository, dry-run contract, policy v1, IP pins, event/audit, and tests.

## 0.1.7 - 2026-05-10
- Fixed Phase 5-B lifecycle field placement by keeping lifecycle columns only on `Customer`, added regression tests for unrelated models, and aligned `CustomerSetIpsRequest` validation for `ips_mode=any`.

## 0.1.6 - 2026-05-10
- Added Phase 5-B customer lifecycle schema migration, model fields, and DB-only domain validation DTO foundations.

## 0.1.5 - 2026-05-07
- Accepted Phase 3 CLI + Internal API Foundation on `farm5`.
- Added `docs/PHASE_3_SERVER_RESULT.md`.
- Updated phase guard to Phase 3 accepted / Phase 4 planning.
- Kept production traffic, firewall apply, NAT redirects, proxy data-plane, customer mutation, usage timers, abuse automation, UI, and Telegram disabled.

## 0.1.4 - 2026-05-07
- Added Phase 3 read-only CLI/API foundation.
- Added read-only DB status, lane list, customer list, and job status commands through service/repository boundaries.
- Added internal API foundation with stable read-only response DTOs.
- Added taxonomy and request context foundation.
- Added forbidden command tests for Phase 3 safety boundaries.

## 0.1.3 - 2026-05-05
- Replaced `AGENTS.md` with the requested full AI agent instructions and mandatory architecture/firewall rules.

## 0.1.2 - 2026-05-05
- Added requested documentation structure (`docs/`, `docs/source/`), `AGENTS.md`, and `.github/copilot-instructions.md`.

## 0.1.1 - 2026-05-05
- Optimized README with explicit Phase 0/1 execution scope, production-safety warnings, near-term outputs, and abuse testability criteria.

## 0.1.0 - 2026-05-05
- Replaced README.md with a comprehensive architecture, roadmap, and guardrails document for Proxy Address Mining.
