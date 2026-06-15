<!--
AI agents: do not create this PR with a generic body or approximate body.
Use the exact canonical template printed by:
python scripts/validate_runtime_first_pr_body.py --print-template
Do not change the official PR class taxonomy; approximate classes such as docs/evidence-only, test-only, and refactor-only are forbidden.
Before creating the PR, write the final body to /tmp/pr_body.md, run:
python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md
Then create the PR only through the validated wrapper:
scripts/create_runtime_first_pr.sh /tmp/pr_body.md --title "..." --base main --head <branch>
Do not replace the validated body with an auto-generated summary.
-->

## Why

## What

## How to test

Version: X.Y.Z -> A.B.C

Risk + Rollback

## PR class
- [ ] implementation
- [ ] controlled-runtime
- [ ] verifier-doctor-package
- [ ] runtime-first bundle
- [ ] acceptance-review
- [ ] evidence/docs exception

## Current blocker(s) being addressed

## next_required_step before this PR

## next_required_step after this PR

## Runtime deliverable(s) in this PR

## Why this is not another report-only PR

## If evidence/docs exception
- Why runtime-first work is unsafe, blocked, or technically impossible:
- Exact next runtime-first PR that must follow:
