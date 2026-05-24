# Phase 11E single-customer post-apply evidence

Purpose: classify already-executed controlled apply evidence for limited-btc-001/btc/20101 and prepare next runtime-evidence PR without any mutation.

Candidate: `limited-btc-001 / btc / 20101 / 172.18.0.3:60010`

Prerequisite evidence hashes:
- execution json sha256: `bd8f3900db3d3fb2647ead8cec47c870f4cd00ebaf52b68bc329a065a65b880b`
- pre snapshot sha256: `3a493643f796f10f37443152e99adda928f30c82067fc98a4a748f52d2767494`
- post snapshot sha256: `c6330a80954f7268ccec311750751b45464c84c2efd627509d1ecee274eec27b`
- apply gate json sha256: `500978bf2b156a5da6a1b299e41d346cadf2b20b15280212c607c51c9a307b1a`
- plan gate json sha256: `0893d1d63b7cb7f60a3473ad9f922c3f65bc9b3e6ff8d5b84aecfa701d45c438`

Boundaries: non-mutating only; no production/miner traffic; no extra firewall apply; no DB activation; no Phase 11 acceptance.

Command example:
`mpf production single-customer-post-apply-evidence --execution-json ... --pre-apply-snapshot-file ... --post-apply-snapshot-file ... --apply-gate-json ... --plan-gate-json ... --operator ... --reason ... --operator-confirmed --i-understand-post-apply-evidence-only --i-understand-no-additional-firewall-apply --i-understand-no-production-traffic-acceptance --i-understand-no-miner-traffic-acceptance --i-confirm-runtime-path-evidence-required-next --i-confirm-stratum-transcript-required-next --i-confirm-visibility-bundle-required-next --i-confirm-abuse-1h-required-before-customer-traffic --i-confirm-restart-container-order-required-before-limited-acceptance --output json`

Expected positive output: `PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY`.
Expected blocked output: `BLOCKED` with specific blockers.
Next step: `phase11e_single_customer_runtime_path_evidence_pr`.
