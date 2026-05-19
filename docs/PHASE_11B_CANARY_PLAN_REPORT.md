# Phase 11B — CLI Canary Plan Report (Report-Only)

Phase 11B adds `mpf production canary-plan` as a **report-only, non-authorizing** planning surface.

## Scope

- This is **Phase 11B**.
- Canary **plan/report only**.
- Does **not** execute canary.
- Does **not** apply firewall.
- Does **not** create real customer NAT/rules.
- Does **not** authorize production traffic.

`docs/PHASE_STATUS.md` remains authoritative.

## Command

```bash
mpf production canary-plan --output json
```

The command returns a deterministic report with fail-closed flags (`execution_allowed=false`, `report_only=true`, `mutation_performed=false`) and preview-only metadata for desired-model/NAT/firewall/rollback planning.

## Post-merge farm5 evidence commands

```bash
sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
mpf --version
mpf phase-status
mpf config validate
mpf doctor
mpf db status
mpf proxy doctor
mpf production readiness --output json
mpf production canary-plan --output json
bash scripts/verify_current_phase_gate.sh
python -m pytest -q
```

Do not claim these commands were run on farm5 unless real operator output is recorded.
