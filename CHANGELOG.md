# Changelog

## 0.1.33 - 2026-05-11

- Hardened planner safety validation: active customers on unknown/disabled lanes or with missing/incomplete current policy now produce planner errors and no forwarding intent.
- Validated firewall CLI `--source` to only accept `db-readonly|config-only` and kept planner dry-run only behavior unchanged.

## 0.1.31 - 2026-05-11

- Aligned Phase 6-A1 PR metadata and verification notes with the finalized branch state (title/body consistency with `fix(firewall): enforce backend collision check and explicit planner source`, test evidence `python -m pytest -q` = 191 passed). This is metadata-only and introduces no live firewall, NAT, runtime, usage, abuse, UI, or Telegram behavior.

## 0.1.30 - 2026-05-11

- Added Phase 6-A1 follow-up safety: detect `customer_backend_port_collision` (active customer port equals enabled lane backend port) and mark plans non-applyable; also made CLI planner output explicit as `planner_customer_source=config_only` and `db_customer_input_loaded=false` to avoid silent DB-customer ambiguity. Planner-only change with no live firewall, NAT, runtime, usage, abuse, UI, or Telegram behavior.

## 0.1.29 - 2026-05-11

- Implemented Phase 6-A1 planner-only firewall foundation: desired/plan domain objects, dry-run planner service, and read-only `mpf firewall plan|diff` rendering (human/JSON) with safety checks for collisions/exposure and no live firewall, NAT, runtime, usage, abuse, UI, or Telegram behavior.

## 0.1.28 - 2026-05-11

- Required Python 3.12 in package metadata to align the project with the accepted Ubuntu 24.04 server baseline and existing GitHub Actions CI runtime. This is metadata-only and introduces no live firewall, NAT, runtime, usage, abuse, UI, or Telegram behavior.

## 0.1.27 - 2026-05-11

- Cleaned current phase documentation before Phase 6 implementation by aligning `README.md` and `docs/PHASE_STATUS.md` to Phase 5 accepted / Phase 6 working state, added `docs/AI_PHASE_6_TASK.md` for planner-first boundaries, and kept all runtime, firewall apply, NAT, usage, abuse, UI, and Telegram behavior disabled.

## 0.1.26 - 2026-05-10

- Fixed current sync gate NAT verification to avoid false failures on Docker-managed local-only DNAT publish rules (127.0.0.1:2015 and 127.0.0.1:60010) while preserving MPF/customer firewall reference blocking and local-only listener safety checks.

## 0.1.25 - 2026-05-10

- Replaced sync final gate invocation with `scripts/verify_current_phase_gate.sh` for Phase 5 accepted / Phase 6 working verification, kept `verify_phase4_planning_gate.sh` as historical-only, and updated sync/runbook tests/docs accordingly.

## 0.1.24 - 2026-05-10

- Fixed `mpf phase-status` to read the authoritative `## Current State` text block from `docs/PHASE_STATUS.md` (with clear non-zero error behavior if missing), added alignment/safety regression tests, and introduced `scripts/mpf_sync_main_zip_bootstrap.sh` to always execute sync from extracted ZIP source.

## 0.1.23 - 2026-05-10

- Fixed `scripts/sync_main_zip_on_server.sh` phase gate expectations to require Phase 5 accepted / Phase 6 working status and updated related safety assertions/tests without changing runtime behavior.

## 0.1.22 - 2026-05-10

- Closed Phase 5 with final acceptance evidence on farm5, advanced working phase to Phase 6 (Firewall Planner), and added documentation tests to enforce Phase 5 closure gates without introducing runtime behavior.

## 0.1.21 - 2026-05-10

- Added Phase 5-F2 Product Roles and UX Journey Contract documentation and test guards (docs-only; no UI, Telegram, API, runtime, DB mutation, firewall, or NAT behavior).

## 0.1.20 - 2026-05-10

- Completed Phase 5-F1 troubleshooting contract template consistency across all 18 scenarios and strengthened template-enforcement tests.

## 0.1.19 - 2026-05-10

- Added Phase 5-F1 Operator Troubleshooting Evidence Contract documentation and test guards (docs-only; no runtime collection).

## 0.1.18 - 2026-05-10

- Phase 5-E3: add DB-only read-only customer history visibility commands (`customer policies`, `customer events`, `customer audit`, `events latest`) backed by PostgreSQL SELECT/WITH queries only, with no DB mutation and no firewall/NAT/runtime side effects.

## 0.1.17 - 2026-05-10

- Phase 5-E2b: add DB-only read-only customer lifecycle helper/report commands (`customer next-port`, `customer expiring`, `customer expired`, `customer delete-eligible`) with no DB mutation and no firewall/NAT/runtime side effects.

## 0.1.16 - 2026-05-10

- Clarified PR scope/metadata for Phase 5-E2a (show/list only), no additional runtime features.

## 0.1.15 - 2026-05-10

- Phase 5-E2a: fix boolean parsing for read-only customer show mapping in local-peer/psql CSV fallback and add regression tests.

## 0.1.14 - 2026-05-10

- Fix DB-only customer show/list visibility boundaries (service/repo filtering, local-peer read helper fallback, nullable lifecycle mapping, clearer list empty message).

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