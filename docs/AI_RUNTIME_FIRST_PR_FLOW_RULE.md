# AI Runtime-First PR Flow Rule

Status: active AI agent process rule

This rule applies to Codex, Copilot, ChatGPT-assisted patches, and any AI coding agent working on this repository.

## Rule

AI agents must not create a chain of report-only, docs-only, evidence-only, or readiness-only PRs when the next safe runtime, verifier, doctor, package, execution gate, or acceptance-review primitive is already known.

For Phase 11 operational completion and later phases, once farm5 evidence, `docs/PHASE_STATUS.md`, a verifier, a doctor, or progression code names a concrete blocker, the next AI-generated PR must do one of these:

- close that blocker;
- add the smallest safe runtime, verifier, doctor, package, execution-gate, or acceptance-review primitive that directly advances it;
- create a coherent runtime-first bundle that advances multiple related deliverables under the same operational gate;
- use the evidence/docs exception and name why runtime-first work is unsafe, blocked, or technically impossible plus the exact next runtime-first PR that must follow.

## Mandatory PR body validation before PR creation

AI agents must validate the pull request body before creating any PR in this repository.

Required flow:

```bash
cat > /tmp/pr_body.md <<'EOF'
# final runtime-first PR body
EOF
python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md
gh pr create --body-file /tmp/pr_body.md
```

Rules:

- Do not create a PR with a generic `Motivation` / `Description` / `Testing`-only body.
- Do not run `gh pr create --body` with an unvalidated generated summary.
- Do not replace the validated `/tmp/pr_body.md` content with an auto-generated summary.
- If `python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md` fails, fix `/tmp/pr_body.md` and rerun it before creating the PR.
- The PR body must contain exactly one checked PR class and all required runtime-first sections.
- This local validation is mandatory even though CI validates the PR body again.

## No repeated report-only PRs

Docs-only, evidence-only, report-only, or readiness-only PRs are allowed only as a single exception between runtime-first steps.

Repeated report-only/docs-only/evidence-only PRs are forbidden when the known blocker and `next_required_step` are already available.

Changing wording, restating evidence, or updating phase status without closing or directly advancing the known blocker is not progress.

## Known blocker and next_required_step

Every AI-generated PR must state:

```text
Current blocker(s) being addressed
next_required_step before this PR
next_required_step after this PR
```

After a known blocker exists, the next PR must target that blocker, advance it through a runtime-first bundle, or explain why it is technically unsafe or impossible to do so now.

## Readiness-only counts as report-only

A readiness-only PR counts as report-only unless it creates at least one operator-reviewable runtime artifact, such as:

- a package;
- a verifier;
- a doctor check;
- an execution gate;
- an acceptance-review artifact.

A PR that only says the system is ready, updates wording, or records status without creating one of those artifacts is evidence/report-only for this rule.

## Runtime-first bundle PRs

Runtime-first bundle PRs are allowed and preferred over unnecessary tiny PRs when they reduce churn and keep the change coherent, tested, reviewable, and inside the current accepted safety gate.

AI agents must not split one coherent runtime-first task into multiple small report/docs/readiness PRs to appear incremental. A safe bundle may advance multiple related runtime, verifier, doctor, package, execution-gate, and acceptance-review deliverables in one standard PR.

## Allowed evidence/docs exception

A report-only, docs-only, or evidence-only PR is allowed when it is one focused step that preserves important farm5 evidence or corrects stale operator guidance before the next change and the PR body names the hard blocker plus exact next runtime-first PR.

Examples:

```text
record fresh farm5 sync/test evidence required before a dangerous controlled operation
record canary NAT / Stratum evidence that gates an acceptance review
fix stale runbook text that could cause unsafe operator action
preserve evidence before an acceptance-review PR
```

## Forbidden pattern

Do not produce multiple consecutive broad report-only PRs that avoid a real canary, runtime, verifier, doctor, rollback, visibility, package, execution-gate, or acceptance-review task.

Do not use documentation churn to postpone an already identified blocker.

Do not change Phase Status wording to imply progress while runtime evidence still points to an unresolved blocker.

## Phase 11 application

For Phase 11 work, AI agents should prefer the shortest safe path from evidence to controlled canary validation, visibility checks, package/verifier/doctor hardening, acceptance review, or the exact runtime primitive required by the latest farm5 output.

Real customer onboarding, abuse automation, UI, Telegram, scheduler, worker enforcement, and broad production traffic remain forbidden until their explicit gates are accepted.
