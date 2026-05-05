# Copilot Instructions

This repository is in Phase 0/1 planning for a Python-first mining proxy control plane.

## Priorities
- Safety first: no production traffic operations in bootstrap phases.
- Keep changes aligned with lane model and PostgreSQL source-of-truth design.
- Prefer testable service-layer architecture over CLI-embedded logic.

## Guardrails
- Do not create direct NAT/firewall live changes without plan/verify/rollback.
- Keep `firewall.apply_mode` in planning mode during early phases.
