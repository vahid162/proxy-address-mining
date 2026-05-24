# Phase 11 farm5 0.1.204 single-customer firewall apply execution evidence

Scope: controlled single-customer apply evidence record for limited-btc-001/btc/20101 -> 172.18.0.3:60010.

Version: 0.1.204, sync commit d924b30447ecd8182d0a745b87fa597b52e23b45.

Dry-run evidence and pre-apply artifacts/hashes were recorded exactly as provided, including execution JSON sha256 `bd8f3900db3d3fb2647ead8cec47c870f4cd00ebaf52b68bc329a065a65b880b` and post-apply snapshot sha256 `c6330a80954f7268ccec311750751b45464c84c2efd627509d1ecee274eec27b`.

Execution output summary: `PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_EXECUTED_PENDING_REVIEW`, blockers/warnings empty, mutation performed true, next step `phase11e_post_apply_runtime_evidence_pr`.

Post-apply verification summary: canary 20001 preserved, MPFC_20101 present, exact DNAT 20101 target count 1, no loopback 20101, no unrelated customer NAT.

Boundary: This records a controlled single-customer firewall/NAT apply only; it does not accept Phase 11, does not accept production/miner traffic, does not enable unrestricted onboarding/abuse automation/UI/Telegram, and does not prove runtime path or Stratum transcript. Runtime-path evidence, abuse 1h coverage evidence, and restart/container-order evidence are still required before any customer traffic acceptance.
