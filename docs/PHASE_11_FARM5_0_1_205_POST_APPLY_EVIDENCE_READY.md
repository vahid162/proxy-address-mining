# Phase 11 farm5 0.1.205 post-apply evidence READY

Version: 0.1.205

- Sync/test summary: pytest 1340 passed, mpf doctor OK, db status OK, proxy doctor OK, gates unchanged (production_traffic none, firewall_apply_allowed no, abuse_automation_allowed no, customer_onboarding_allowed db_only, ui/telegram no).
- Post-apply evidence command executed for limited-btc-001/btc/20101 -> 172.18.0.3:60010 as provided by operator.
- Output summary: final_decision PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY; controlled_apply_recorded true; runtime/stratum/visibility ready flags false.
- Evidence file hash: `/tmp/phase11-single-customer-post-apply-evidence-0.1.205.json` sha256 `REPLACE_WITH_SHA256SUM_OUTPUT`.

Boundary:
- Controlled apply is recorded.
- Runtime path evidence is NOT ready.
- Stratum transcript is NOT ready.
- Visibility bundle is NOT ready.
- Production/miner traffic remains blocked.
- DB activation remains blocked.
- Phase 11 remains not accepted.
