# Contributing

This repository uses governance, safety, and runtime-first checks so every change is reviewable and machine-verifiable.

## Authority and safety

- Start with [`AGENTS.md`](AGENTS.md), [`docs/INDEX.md`](docs/INDEX.md), [`docs/PRD.md`](docs/PRD.md), [`docs/GUIDELINES.md`](docs/GUIDELINES.md), [`docs/SAFETY.md`](docs/SAFETY.md), and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for routing, product scope, engineering, safety, and architecture rules.
- Current phase, active gate, runtime authorization, and next required step live only in [`docs/PHASE_STATUS.md`](docs/PHASE_STATUS.md).
- Long-term product evolution lives in [`docs/ROADMAP.md`](docs/ROADMAP.md), and architectural decisions live in [`docs/ADR/`](docs/ADR/).
- Historical documents under [`docs/history/`](docs/history/) are audit context only. They are not operational authority and must not override current active documents.
- Do not mutate production runtime, PostgreSQL, firewall, Docker, systemd, conntrack, customer state, abuse execution, workers, UI, Telegram, scheduling, or server configuration unless the active gate in `docs/PHASE_STATUS.md` explicitly authorizes that exact operation.
- Do not directly mutate database or firewall state outside the service, repository, adapter, event, audit, planner, verifier, and restore-point boundaries defined by the architecture and safety contracts.

## Commit and PR rules

- Use Conventional Commit titles: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, or `test:` with an optional scope, for example `chore(ci): add document contract validation`.
- Deliver one complete outcome per PR. Do not mix unrelated runtime, documentation, refactor, and tooling outcomes.
- Use the repository runtime-first PR body validator before delivery:
  - Strict runtime-first work: `python scripts/validate_runtime_first_pr_body.py --print-template`
  - Completed governance/documentation outcomes: `python scripts/validate_runtime_first_pr_body.py --print-template governance-documentation`
  - Final validation: `python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md`
- Fill the required PR body sections and choose exactly one PR class. Do not use `governance-documentation` for runtime/evidence work or to bypass active runtime-first blockers.
- When repository policy requires the validated PR wrapper, create PRs with [`scripts/create_runtime_first_pr.sh`](scripts/create_runtime_first_pr.sh) instead of calling `gh pr create` directly.

## Version and changelog

- When a change bumps the version, keep `VERSION`, `pyproject.toml`, `mpf/__init__.py`, and `CHANGELOG.md` synchronized.
- Add an accurate changelog entry for the new version. State safety boundaries clearly when a release does not change runtime authorization or server mutation behavior.

## Testing before delivery

Run the narrowest relevant tests for the changed files, then run the full suite before delivery. A typical final sequence is:

```bash
git diff --check
python scripts/validate_document_contract.py .
python -m pytest -q tests/test_document_contract.py
python -m pytest -q
python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md
```

Keep pytest independently visible even when PR-body validation fails.
