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
