# AI Phase 9 Task — Check / Report / Diagnostics

Status: Current / Planning-Readiness / Report-Only

## Scope

Phase 9 should improve operator visibility and diagnostics after Phase 8 acceptance.

Expected future capabilities:
- check/report final verdict
- customer diagnostics
- abuse status visibility
- usage/accounting status visibility
- policy/reject visibility
- proxy/runtime diagnostic summary
- evidence-pack readiness
- troubleshooting summaries
- no production mutation

## Stop Conditions

Phase 9 readiness must not:
- enable production traffic
- enable firewall apply
- enable iptables-restore
- enable customer NAT/customer firewall rules
- enable abuse automation runner
- start background workers
- start scheduler/timer
- evaluate real production customers
- execute production DB transitions
- write production abuse state
- apply hard/soft blocks
- apply pause automation
- enable UI
- enable Telegram

## First Phase 9 PR

The next explicit Phase 9 diagnostics PR should be:
Phase 9 diagnostics bundle report-only package.

It should add mpf phase9 diagnostics plus focused report-only diagnostics components: customer-diagnostics, abuse-visibility, usage-visibility, policy-reject-visibility, proxy-runtime-diagnostics, evidence-pack, troubleshooting-summary.

It must remain fail-closed and require fresh farm5 0.1.127 sync/test evidence after merge before final acceptance.


Current Phase 9 completed report surfaces:
- readiness
- final-verdict
- diagnostics bundle

Current target:
- final acceptance readiness
