# AI Runtime-First PR Flow Rule

Status: active AI agent process rule

This rule applies to Codex, Copilot, ChatGPT-assisted patches, and any AI coding agent working on this repository.

## Rule

AI agents must not create a chain of report-only, docs-only, or evidence-only PRs when the next safe runtime, verifier, doctor, or acceptance-review primitive is already known.

## Allowed report-only PRs

A report-only, docs-only, or evidence-only PR is allowed when it is one focused step that preserves important farm5 evidence or corrects stale operator guidance before the next change.

Examples:

```text
record fresh farm5 sync/test evidence
record canary NAT / Stratum evidence
fix stale runbook text that could cause unsafe operator action
preserve evidence before an acceptance-review PR
```

## Required next step after evidence

After one evidence/report-only PR, the next PR should move toward the smallest safe runtime-first step, verifier/doctor hardening, acceptance review, or exact missing primitive reported by farm5.

If another report-only PR is proposed, the PR body must explain why runtime-first work is currently unsafe, blocked, or not yet identifiable.

## Forbidden pattern

Do not produce multiple consecutive broad report-only PRs that avoid a real canary, runtime, verifier, doctor, rollback, visibility, or acceptance task.

Do not use documentation churn to postpone an already identified blocker.

Do not change Phase Status wording to imply progress while runtime evidence still points to an unresolved blocker.

## Phase 11 application

For Phase 11 work, AI agents should prefer the shortest safe path from evidence to controlled canary validation, visibility checks, acceptance review, or the exact runtime/doctor/verifier hardening required by the latest farm5 output.

Real customer onboarding, abuse automation, UI, Telegram, scheduler, worker enforcement, and broad production traffic remain forbidden until their explicit gates are accepted.
