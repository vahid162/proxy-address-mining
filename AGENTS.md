# AGENTS.md

## Purpose

This file is the canonical, concise GPT/Codex entrypoint for this repository. It routes AI agents to the current project authorities without duplicating dynamic phase state or historical gate details.

## Canonical Sources

- `docs/PHASE_STATUS.md` is the only authority for dynamic project state.
- Do not infer current phase, gate, or next_required_step from README, release notes, historical evidence, archived documents, or AGENTS.md history.
- `docs/INDEX.md` is the documentation map.
- `docs/PRD.md` defines product scope.
- `docs/GUIDELINES.md` defines engineering rules.
- `docs/SAFETY.md` defines safety constraints.
- `docs/ARCHITECTURE.md` defines architecture boundaries.
- `docs/ROADMAP.md` defines long-term product evolution.
- `docs/ADR/` records architectural decisions.
- `docs/history/` is non-authorizing historical context.

## Required Reading

Before edits, read only the documents needed for the requested task, in this order:

1. `AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/INDEX.md`
4. task-scope contract: `docs/PRD.md`, `docs/GUIDELINES.md`, `docs/SAFETY.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, or `docs/ADR/` as relevant
5. task-specific domain documents
6. active gate/task documents named by `docs/PHASE_STATUS.md`

Do not require every AI task to read all domain documents.

## Task Routing

- Product-scope work routes to `docs/PRD.md`; engineering-rule work routes to `docs/GUIDELINES.md`; architecture work routes to `docs/ARCHITECTURE.md`; safety work routes to `docs/SAFETY.md`; roadmap work routes to `docs/ROADMAP.md`; ADR work routes to `docs/ADR/`.
- Keep interfaces thin; route business logic through services, repositories, adapters, events, and audit.
- For firewall, abuse, runtime, production, customer, worker, UI, Telegram, or scheduling work, follow the active gate/task documents named by `docs/PHASE_STATUS.md`, including `docs/AI_SAFE_RUNTIME_FIRST.md` when it is named by the active gate.
- For documentation-only governance work, preserve historical context without making archived material authoritative.
- If instructions conflict, follow the stricter safety rule and the current dynamic state in `docs/PHASE_STATUS.md`.

## Non-Negotiable Safety Rules

- Do not mutate production runtime, database, firewall, Docker, systemd, conntrack, customer state, or scheduler state unless the active gate explicitly authorizes that exact operation.
- Do not open Phase 12, worker enforcement, UI, Telegram, public exposure, unrestricted onboarding, or uncontrolled production traffic unless `docs/PHASE_STATUS.md` explicitly authorizes it.
- Do not bypass service-layer validation, audit, restore-point, planner, verifier, or evidence requirements.
- Never commit secrets.

## Validation and Delivery

- Run the narrowest relevant tests plus any required validators for the changed files.
- Keep version metadata and changelog entries consistent when a release/version bump is required.
- PR bodies must pass the repository runtime-first PR validator when required. Use `python scripts/validate_runtime_first_pr_body.py --print-template` for strict runtime-first work, or `python scripts/validate_runtime_first_pr_body.py --print-template governance-documentation` only for completed CI/template/validator/AI-governance/documentation-contract work.
- The `governance-documentation` PR class cannot be used for runtime/evidence work or to bypass active runtime-first work. Runtime-first blockers still require strict runtime-first classes or a valid evidence/docs exception.
- Runtime-forward PR rule: AI agents must not call `gh pr create` directly; use `scripts/create_runtime_first_pr.sh` when repository policy requires the PR wrapper. No two consecutive PRs in the same active phase/subphase may be report-only unless the second PR records a real blocker and exact next implementation scope.
- CI PR body validation failures must not suppress pytest; test results must remain visible even when PR body validation fails.

## Historical Reference

The former root `AGENTS.md` content is preserved unchanged, with a non-authorizing notice, at `docs/history/AGENTS_LEGACY_0.1.298.md`. It is historical context only and must not override the current root `AGENTS.md` or `docs/PHASE_STATUS.md`.
