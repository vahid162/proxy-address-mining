# Copilot Instructions

This repository is in Phase 11 production/customer activation planning-readiness for a Python-first mining proxy control plane.

## Mandatory Reading
- `AGENTS.md`
- `docs/AI_CODING_RULES.md`
- `docs/PHASE_STATUS.md`
- `docs/AI_SAFE_RUNTIME_FIRST.md`
- `docs/AI_RUNTIME_FIRST_PR_FLOW_RULE.md`

## Priorities
- Safety first: no production traffic operations before the matching accepted gate.
- Keep changes aligned with lane model and PostgreSQL source-of-truth design.
- Prefer testable service-layer architecture over CLI-embedded logic.
- Prefer runtime-first progress after evidence is recorded.

## Guardrails
- Do not create direct NAT/firewall live changes without plan/verify/rollback and an explicit accepted gate.
- Keep `firewall.apply_mode` in planning mode unless an explicit future gate changes it.
- Do not create multiple consecutive report-only/docs-only PRs when the next safe runtime, verifier, doctor, or acceptance-review primitive is already known.
- After an evidence/report PR, the next PR should move toward the smallest safe runtime-first step, verifier/doctor hardening, acceptance review, or exact farm5-reported missing primitive.

## Mandatory PR creation contract for AI agents
- Do not create a pull request with a generic `Motivation` / `Description` / `Testing`-only body.
- Before creating any pull request, write the final pull request body to `/tmp/pr_body.md`.
- Run `python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md`.
- If validation fails, fix `/tmp/pr_body.md` and rerun the validator.
- To recover from a failed validation, run `python scripts/validate_runtime_first_pr_body.py --print-template`, fill the printed template, and validate again.
- If GitHub Actions fails at `Validate runtime-first PR body`, copy the template printed in the CI log, update the PR body, and do not create a code-only commit just to fix the body.
- Only create the pull request after the validator passes.
- AI agents must not call `gh pr create` directly.
- The only allowed AI-agent PR creation path is `scripts/create_runtime_first_pr.sh /tmp/pr_body.md --title "..." --base main --head <branch>`.
- Explicitly forbidden for AI agents outside the wrapper: `gh pr create`, `gh pr create --fill`, `gh pr create --body "..."`, and direct `gh pr create --body-file ...`.
- If the wrapper cannot be run, do not create the PR; report the exact blocker.
- Do not replace the validated body with an auto-generated summary.
- Approximate PR templates are forbidden; use the exact canonical template printed by `python scripts/validate_runtime_first_pr_body.py --print-template`.
- AI agents must not change the PR class taxonomy. The only official classes are `implementation`, `controlled-runtime`, `verifier-doctor-package`, `runtime-first bundle`, `acceptance-review`, and `evidence/docs exception`.
- Unofficial PR classes such as `docs/evidence-only`, `test-only`, and `refactor-only` are forbidden.
- If validation fails, fix `/tmp/pr_body.md` before creating or updating the PR.
- A merged PR with approximate taxonomy is not precedent; the validator must reject that shape going forward.
