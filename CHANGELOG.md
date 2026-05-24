# Changelog

## 0.1.207
- Add Phase 11E single-customer runtime probe diagnostics and record 0.1.206 runtime-path BLOCKED evidence.

## 0.1.206
- Add Phase 11E single-customer runtime path, Stratum transcript, and visibility bundle evidence classifiers and CLI (read-only).
## 0.1.205
- record farm5 0.1.204 controlled single-customer firewall/NAT apply execution evidence
- add non-mutating post-apply evidence classifier service + CLI + tests

## 0.1.204
- add controlled single-customer firewall apply execution package/execute path with strict guards.


## 0.1.203
- feat(phase11): record farm5 0.1.202 sync/test and firewall plan gate evidence and add non-mutating single-customer firewall apply gate package while preserving closed apply/traffic gates.

## 0.1.202
- test(phase11): isolate single-customer staging create-failure test from real farm5 DB state after DB-only staging while preserving closed firewall/NAT/traffic gates.

## 0.1.201
- feat(phase11): record farm5 0.1.200 single-customer DB-only staging evidence and add non-mutating single-customer firewall/NAT plan gate while preserving closed apply/traffic gates.

## 0.1.199
- feat(phase11): record farm5 0.1.198 limited onboarding readiness evidence and add non-mutating Phase 11E limited onboarding execution gate package while preserving closed production/onboarding gates.

## 0.1.198
- feat(phase11): record farm5 0.1.197 controlled canary acceptance decision evidence and add non-mutating Phase 11E limited onboarding gate readiness command while preserving closed production/onboarding gates.

## 0.1.197
- feat(phase11): add non-mutating operator-controlled canary acceptance decision gate for exact farm5 0.1.195 evidence-pack validation while preserving closed Phase 11 production/onboarding gates.

## 0.1.196
- docs(phase11): record farm5 0.1.195 live canary evidence-pack showing runtime path, visibility bundle, and acceptance-review readiness while preserving closed production/onboarding gates.

## 0.1.195
- fix(phase11): support NAT-aware conntrack proof and multiline forwarder local-port correlation for canary runtime path evidence while preserving fail-closed Phase 11 gates.

## 0.1.194
- fix(phase11): build final check and rollback visibility from merged evidence pack state with source-backed READY evidence gating and fail-closed acceptance mapping.

## 0.1.193
- fix(phase11): merge PRESENT usage visibility evidence into canary evidence-pack visibility bundle while preserving fail-closed scope checks and no-mutation safety flags.

## 0.1.192

- fix(phase11): wire canary evidence-pack generated source-backed artifacts into visibility services/bundle (usage, session/IP, final-check, rollback/restore), add UTF-8 BOM transcript import tolerance, and improve forwarder correlation diagnostics while keeping Phase 11 fail-closed.

## 0.1.190

- fix(phase11): preserve independently proven runtime path evidence primitives while keeping canary runtime-path final decision blocked until all required evidence is present.

## 0.1.189

- add source-backed read-only Phase 11 canary runtime path evidence classifiers for conntrack, forwarder-pool, and bridge-loopback evidence.

## 0.1.188
- add source-backed Phase 11 canary final check report visibility command and evidence export
- add source-backed Phase 11 canary rollback/restore plan visibility command and evidence export

## 0.1.187
- feat(phase11): add source-backed canary abuse coverage visibility command/evidence and harden external transcript --collect-live canary DB validation via customer_read_service exact-scope checks.


## 0.1.186
- feat(phase11): add source-backed `mpf production canary-external-stratum-transcript-import` for fail-closed external transcript evidence import and visibility/acceptance integration.
- fix(phase11): correct forwarder pool evidence classification to avoid requiring worker names in forwarder logs.

## 0.1.185
- Corrective note: 0.1.185 also introduced canary worker/Stratum evidence capture (PR #199); this history is retained alongside restore-payload notes.


- fix(phase11): make exact single-canary restore payload idempotent by emitting filter-only `MPFC_20001` reject counter source when the controlled canary NAT rule already exists, avoiding duplicate NAT append.

## 0.1.183

- fix(phase11): populate read-only `live_nat_prerequisites` in manual single-canary execute path before exact restore payload rendering when NAT hook already exists, preserving fail-closed bootstrap behavior when hook is missing.

## 0.1.182
- feat(phase11): add exact controlled canary filter reject counter source in single-canary restore payload (`MPFC_20001` with `customer_connlimit_reject`/`customer_hashlimit_reject` comments) so reject visibility remains fail-closed and becomes PRESENT only when exact source exists.

## 0.1.181
- add read-only Phase 11 canary reject counters visibility capture and CLI command.

## 0.1.180
- fix(phase11): merge multiple canary visibility evidence artifacts (`--evidence-json` / `--visibility-json` repeated) so usage/session/IP source-backed primitives are aggregated fail-closed without opening runtime gates.

## 0.1.179
- Add read-only Phase 11 canary reject/session/IP evidence capture and CLI, keeping Phase 11 unaccepted and all runtime gates closed.

## 0.1.178
- Added Phase 11 canary usage evidence capture + operator execution context guard (root read vs mpf DB-write).

- hotfix: fix Phase 11 canary DB visibility execute create path to use valid lifecycle `activation_mode="first_connect"` (instead of invalid `manual`) so execute no longer fails pre-DB-write on lifecycle validation.
- add regression coverage for exact-canary execute create request lifecycle validation and keep DB-only/non-runtime mutation flags and plan-only behavior unchanged.

## 0.1.172

- hotfix: normalize Phase 11 live canary proxy evidence status mapping to canonical uppercase `HealthStatus` values so proxy evidence fields align with proxy doctor `OK` verdicts without changing NAT parsing or introducing mutation.

## 0.1.169
- Record farm5 0.1.167 synthetic Stratum canary success evidence while keeping Phase 11 unaccepted and real onboarding forbidden.

## 0.1.167
- Fix proxy doctor runtime container expectations to require `mpf-v2raya-socks-bridge`, add a runtime-state test for missing bridge CRITICAL verdict, and keep Phase 11 unaccepted with onboarding still forbidden.

## 0.1.166
- Record farm5 0.1.164 route-safe single-canary NAT success evidence while keeping Phase 11 unaccepted and real onboarding forbidden.

## 0.1.164
- Add route-safe Docker backend target resolution for the Phase 11 exact single-canary DNAT path, replacing the previous loopback `127.0.0.1:60010` target with a runtime-discovered Docker container IPv4 target.
- Harden renderer, executor, and verifier to reject loopback/public/mismatched targets, preserve exact canary scope, and keep onboarding, abuse automation, UI, Telegram, and Phase 11 acceptance closed.
- Record farm5 0.1.163 failure evidence: loopback DNAT hit counters but external connection timed out; failed rule was manually removed.

## 0.1.163
- Add the exact Phase 11 single-canary NAT hook bootstrap boundary for `MPF_NAT_PRE` and `PREROUTING -> MPF_NAT_PRE`, guarded by explicit env flags, restore/backup, lock, `iptables-restore --test --noflush`, and terminal bootstrap review behavior without automatic final canary DNAT.
- Record farm5 0.1.162 sync/safe-check evidence while keeping Phase 11 unaccepted, production traffic disabled, limited onboarding forbidden, and abuse/UI/Telegram gates closed.

## 0.1.159
- add single-canary real restore point + iptables-save backup boundary for execute path only
- record farm5 0.1.158 sync/test evidence

## 0.1.158
- Implement accepted single-canary host apply primitive boundary for Phase 11 manual canary execution exact-scoped to `canary-btc-001` / `btc` / `20001 -> 60010`, with non-placeholder restore/backup/lock/diff/context gates, fail-closed blockers, idempotency checks, mutation-accurate reporting, and no broad production activation.

## 0.1.157
- Add a fail-closed Phase 11F single-canary firewall apply adapter boundary for `canary-btc-001` (`btc`/`20001 -> 60010`) with exact-scope checks, restore/backup/lock/diff gates, structured blockers, and blocked-by-default host apply primitive reporting (`unsafe_firewall_apply_boundary`) without enabling broad production activation.

## 0.1.156
- Implement the Phase 11D single-canary operator-approved execution workflow and farm5 runbook for `canary-btc-001` on BTC port 20001, fix stale manual-canary expected-version validation, keep plan mode non-mutating by default, require explicit approvals for execute mode, leave farm5 execution evidence pending, keep limited real customer onboarding forbidden, and keep Phase 11 unaccepted.

## 0.1.154
- Record farm5 0.1.153 sync/test evidence for the Phase 11D actual operator-approved manual canary execution run package while keeping actual canary execution unperformed, Phase 11 unaccepted, limited real customer onboarding forbidden, and production/firewall/customer/abuse/UI/Telegram gates closed.

## 0.1.153
- Add the Phase 11D actual operator-approved manual canary execution run package and `mpf production manual-canary-execute --output json`, with fail-closed plan mode, explicit execution approvals, service-layer adapter boundaries, rollback/evidence requirements, and no PR-time canary execution or production activation.

## 0.1.152
- Record farm5 0.1.151 sync/test evidence for the Phase 11D operator-reviewed manual canary execution run preparation package while keeping actual canary execution, production traffic, firewall apply, customer DB mutation, customer NAT/rules, abuse automation, UI, and Telegram gates closed.

## 0.1.151
- Add the Phase 11D operator-reviewed manual canary execution run preparation package and `mpf production canary-execution-run-prep --output json` while keeping actual canary execution, production traffic, firewall apply, customer DB mutation, customer NAT/rules, abuse automation, UI, and Telegram gates closed.

## 0.1.150
- Record farm5 0.1.149 sync/test evidence for the Phase 11D manual canary execution gate package and harden the current phase safety gate script for absolute-path execution while keeping actual canary execution, production traffic, firewall apply, customer DB mutation, customer NAT/rules, abuse automation, UI, and Telegram gates closed.

## 0.1.149
- Add the Phase 11D manual canary execution gate package and `mpf production canary-execution-gate --output json` while keeping actual canary execution, production traffic, firewall apply, customer DB mutation, customer NAT/rules, abuse automation, UI, and Telegram gates closed.

## 0.1.148
- Record farm5 0.1.147 sync/test evidence for Phase 11D manual canary acceptance package while keeping Phase 11D execution, production traffic, firewall apply, customer DB mutation, customer NAT/rules, abuse automation, UI, and Telegram gates closed.

## 0.1.147
- Add Phase 11D manual canary customer acceptance package, evidence requirements, execution boundary, and `mpf production canary-acceptance --output json` while keeping manual canary execution, production traffic, firewall apply, customer DB mutation, customer NAT/rules, abuse automation, UI, and Telegram gates closed.

## 0.1.146
- Record farm5 0.1.145 sync/test evidence for Phase 11C controlled activation harness while keeping production traffic, firewall apply, customer DB mutation, customer NAT/rules, abuse automation, UI, and Telegram gates closed.

## 0.1.145
- Add Phase 11C controlled activation harness, preflight, activation package, execution boundary, and `mpf production activation-harness --output json` while keeping production traffic, firewall apply, customer DB mutation, customer NAT/rules, abuse automation, UI, and Telegram gates closed.

## 0.1.144
- Record farm5 0.1.143 sync/test evidence for Phase 11A production readiness and Phase 11B canary plan report while keeping production traffic, firewall apply, customer NAT/rules, abuse automation, UI, and Telegram gates closed.

## 0.1.143
- Add Phase 11B canary plan/report-only service and `mpf production canary-plan --output json` while keeping canary execution, production traffic, firewall apply, customer NAT/rules, abuse automation, UI, and Telegram gates closed.

## 0.1.142
- Add Phase 11A production readiness inventory report and `mpf production readiness --output json` while keeping production/firewall/canary/customer/abuse/UI/Telegram gates closed.

## 0.1.141
- Align AI-safe Runtime-first documentation reading paths across AGENTS, README, INDEX, AI_CODING_RULES, ROADMAP, and REMAINING_PHASE_PLAN while keeping all production/firewall/canary/runtime/abuse/UI/Telegram gates closed.

## 0.1.140
- Define the Phase 11 AI-safe Runtime-first operating principle, clarify the controlled real-customer-sales target for final Phase 11 acceptance, and keep production/firewall/canary/runtime/abuse/UI/Telegram gates closed until explicit evidence-backed acceptance.

## 0.1.139
- Move historical compatibility anchors out of README into dedicated historical documentation, keep active docs focused on Phase 10 accepted / Phase 11 planning-readiness, and preserve all production/firewall/canary/runtime/abuse/UI/Telegram gates closed.

## 0.1.138
- Minimally align current-state documentation and version metadata with Phase 10 accepted / Phase 11 Production Customer Activation Gate planning-readiness, while preserving historical docs, evidence, changelog history, and all production/firewall/canary/runtime/UI/Telegram gates closed.

## 0.1.137
- Accept Phase 10 Session / Worker / Policy / Share Timeline after farm5 0.1.136 sync/test evidence, open Phase 11 production/customer activation planning-readiness, and keep production activation, controlled CLI canary, firewall, runtime, abuse automation, UI, and Telegram gates closed.

## 0.1.136
- Add Phase 10 final-acceptance-readiness gate, record farm5 0.1.135 sync/test evidence, and keep Phase 10 final acceptance, Phase 11 production activation, runtime, scheduler, firewall, abuse automation, UI, and Telegram gates closed.

## 0.1.135
- Add Phase 10F runtime worker and scheduler dry-run readiness contracts, record farm5 0.1.134 sync/test evidence, and keep all runtime daemon, scheduler/timer, firewall, production, abuse automation, collector daemon, UI, and Telegram gates closed.

## 0.1.134
- Add Phase 10D share timeline and Phase 10E collector dry-run gate readiness contracts, record farm5 0.1.133 sync/test evidence, and keep all runtime, firewall, production, abuse automation, scheduler, collector daemon, UI, and Telegram gates closed.

## 0.1.133
- Record farm5 0.1.132 sync/test evidence, refresh Phase 10 evidence wording, and keep production, firewall, abuse, worker runtime, UI, and Telegram gates closed.

## 0.1.130
- Align the remaining roadmap to a backend-first order: Phase 11 Production / Customer Activation Gate, Phase 12 Worker Policy Enforcement, Phase 13 Local UI, Phase 14 Operator UI Actions, and Phase 15 Telegram, without opening runtime gates.

## 0.1.129
- Add Phase 10 report-only planning/readiness foundation CLI/services, record farm5 0.1.128 sync/test evidence, and keep all dangerous authorization flags false and non-mutating.

## 0.1.128
- Accept Phase 9 final diagnostics on farm5 with a new phase9 final-acceptance report/CLI, record farm5 0.1.127 sync/test evidence, advance active target to Phase 10 planning/readiness, and keep all dangerous authorization flags false/non-mutating.

## 0.1.127
- Add Phase 9 final-acceptance-readiness report/CLI, record farm5 0.1.126 sync evidence, and keep all dangerous authorization flags false with report-only non-mutating gates.

## 0.1.126
- Add Phase 9 diagnostics bundle report with focused report-only subcommands/services, keep all dangerous authorization flags false/fail-closed, and update docs target to require post-merge farm5 0.1.126 sync/test evidence.

## 0.1.125
- Add Phase 9 final-verdict report-only diagnostics CLI/report, record farm5 0.1.124 sync/test evidence, and keep all mutation/automation authorization flags false.

## 0.1.124
- Add Phase 9 report-only readiness CLI/report, record farm5 0.1.123 sync/test evidence, and fix Phase 8 final-acceptance docs-token matching without opening runtime gates.

## 0.1.123
- Record farm5 0.1.122 sync evidence, accept Phase 8 Abuse 1h Core on farm5, and open Phase 9 Check / Report / Diagnostics planning/readiness while keeping production traffic, firewall apply, abuse automation, customer NAT/rules, production DB execution, hard/soft block automation, pause automation, UI, and Telegram gates closed.

## 0.1.122
- Record farm5 0.1.121 sync evidence and controlled worker dry-run evidence, refresh stale Phase 8 report surfaces, and add final Abuse 1h acceptance readiness/review while keeping Phase 8 not accepted and all runtime, scheduler, abuse runner, production DB, firewall, customer, hard/soft block, pause, UI, Telegram, and production traffic gates closed.

## 0.1.121
- Record farm5 0.1.120 sync evidence and prepare the Phase 8 farm5 controlled worker dry-run evidence collection package while keeping Phase 8 not accepted and all scheduler, daemon, abuse runner, real-customer, production DB, firewall, customer, hard/soft block, pause, UI, Telegram, and production traffic gates closed.

## 0.1.120
- Record farm5 0.1.119 sync evidence and add the Phase 8 operator-invoked controlled worker dry-run package while keeping Phase 8 not accepted and all scheduler, daemon, abuse runner, real-customer, production DB, firewall, customer, hard/soft block, pause, UI, Telegram, and production traffic gates closed.

## 0.1.119
- Record farm5 batched sync evidence for Phase 8 versions 0.1.116, 0.1.117, and 0.1.118, and add the controlled worker dry-run gate preparation package while keeping Phase 8 not accepted and all worker, scheduler, abuse runner, DB execution, firewall, customer, hard/soft block, pause, UI, Telegram, and production traffic gates closed.

## 0.1.118
- Add the Phase 8 controlled worker pre-acceptance package with fail-closed worker preflight, operator approval, sync boundary, kill-switch, evidence, lock, no-silent-skip, and acceptance contracts while keeping all runtime, scheduler, abuse runner, real-customer, production DB, firewall, customer, and production traffic gates closed.

## 0.1.117
- Add the Phase 8 runtime worker dry-run harness package with synthetic worker-cycle simulation, in-memory lock/idempotency behavior, kill-switch and failure-mode reporting, and a report-only CLI while keeping all runtime, scheduler, abuse runner, real customer, production DB, firewall, customer, and production traffic gates closed.

## 0.1.116
- Record farm5 0.1.115 sync evidence, align Phase 8 DB transition readiness with the accepted 0.1.114/0.1.115 sync state, and add the Phase 8 runtime/worker integration readiness package while keeping all runtime, scheduler, firewall, customer, DB execution, and abuse automation gates closed.

## 0.1.115
- Add the Phase 8 DB-only controlled transition execution package with manual confirmation, idempotency, operator approval validation, dry-run default CLI, named safety checklist items, and farm5 0.1.114 evidence recording while keeping runtime, firewall, customer, and abuse automation gates closed.

## 0.1.114
- Add the Phase 8 DB-only controlled transition readiness package with non-executing transition intent, DB mutation plan, audit, restore-reference, and operator approval contracts while keeping all runtime, DB, firewall, customer, and abuse automation gates closed.

## 0.1.113
- Add the Phase 8 abuse dry-run evaluator package with pure offline state-transition evaluation and report-only CLI while keeping all runtime, DB, firewall, customer, and abuse automation gates closed.

## 0.1.112
- Add the Phase 8 abuse evidence/reporting report-only contract service and CLI while keeping all runtime, DB, firewall, customer, and abuse automation gates closed.

## 0.1.111
- Record farm5 0.1.110 sync evidence and add the Phase 8 abuse state-machine report-only contract service and CLI while keeping all runtime gates closed.

## 0.1.110
- Fix offline zip sync gate validation after Phase 7 acceptance so the server can sync Phase 7 accepted / Phase 8 planning-readiness zips without opening runtime gates.

## 0.1.109
- Accept Phase 7 as report-only/service-contract/readiness after farm5 0.1.108 evidence; start Phase 8 planning/readiness with report-only service/CLI and keep all runtime gates closed.

## 0.1.108
- Record farm5 0.1.107 batched sync evidence and add Phase 7 final acceptance readiness/operator decision report-only services and CLI.

## 0.1.107
- Add Phase 7 read-only reports summary/doctor service and CLI commands; keep all runtime gates closed.

## 0.1.106
- Add Phase 7 policy/reject accounting report-only service-contract package and CLI; keep all runtime gates closed.

## 0.1.105 - 2026-05-15
- Add Phase 7 usage accounting report-only contract service and CLI and align sync evidence/runbook docs.

## 0.1.104 - 2026-05-15
- Fix Phase 7 readiness detector alignment with current docs/AI_PHASE_7_TASK.md semantics and keep reports blocked/non-authorizing.

## 0.1.103 - 2026-05-15
- Add Phase 7 report-only usage/policy readiness service and CLI, align README/phase docs, and record farm5 0.1.102 sync evidence while keeping runtime/customer/production gates closed.

## 0.1.102 - 2026-05-15
- Normalize Phase 6/7 planning docs wording, preserve legacy compatibility anchors, and keep safety/runtime gates unchanged.

## 0.1.101 - 2026-05-15
- Accept Phase 6 as planner/reporting-only on farm5, record 0.1.100 sync evidence, and open Phase 7 planning/readiness while keeping runtime/customer/production gates closed.

## 0.1.100
- Add Phase 6 operator acceptance decision report/CLI, integrate gate summaries, and record farm5 0.1.99 sync evidence while keeping runtime/customer/production gates closed.

## 0.1.99
- Add report-only Phase 6 final acceptance review service/CLI, integrate summaries into apply-gate-readiness and gate-review, and align docs with farm5 0.1.98 sync evidence.

## 0.1.98
- Fix Phase 6 documentation compatibility anchors in docs/AI_PHASE_6_TASK.md and keep test suite green after 0.1.97 rollout.

## 0.1.97
- Add report-only manual canary server evidence and Phase 6 final acceptance readiness services/CLI, integrate summaries, and align Phase 6 docs with farm5 0.1.96 sync evidence.

## 0.1.96
- Add report-only manual canary customer proposal and acceptance-readiness services/CLI and Phase 6 docs sync to farm5 0.1.95 evidence.

## 0.1.95
- Add controlled no-customer runtime execution evidence service/CLI and integrated summaries; record farm5 0.1.94 sync evidence docs updates.

## 0.1.94
- Add report-only no-customer runtime execution approval readiness service/CLI and integrate compact summaries into readiness/review outputs.

## 0.1.93 - 2026-05-14
- Fix gate-review JSON serialization by adding FirewallPlanMessage.to_dict() so config-only warnings/errors render without crashing.

## 0.1.92 - 2026-05-14
- Refine Phase 6 docs wording in place, clarify repo 0.1.92 vs last farm5 sync 0.1.90, and tighten current-state validation.

## 0.1.91 - 2026-05-14
- Add report-only no-customer apply package and execution acceptance services plus CLI surfaces, and record PR #98 farm5 execution-gate sync evidence.

## 0.1.90 - 2026-05-13
- Include non-authorizing apply gate readiness summary in Phase 6 firewall gate review while preserving closed runtime/customer/production gates and the abuse 1h invariant.

## 0.1.89 - 2026-05-13
- Add non-authorizing Phase 6 apply gate readiness report and read-only firewall apply-gate readiness CLI command.

## 0.1.88 - 2026-05-13
- Add Future Dedicated Phase 6 Apply Gate Proposal/Review contract as documentation/test-only and non-authorizing while preserving closed gates and abuse 1h invariant.

## 0.1.87 - 2026-05-13
- Record farm5 0.1.86 sync evidence for Slice 3 and Slice 4 documentation/test-only boundaries and align next planning target.

## 0.1.86 - 2026-05-13
- Add concise Apply Slice 4 manual canary apply gate proposal contract and index Slice 4 documentation, without introducing live behavior.

## 0.1.85 - 2026-05-13
- Add concise Apply Slice 3 controlled no-customer harness contract, index Slice 3 documentation, and preserve closed gates and abuse 1h invariant.

## Historical entries before 0.1.85
- Retained in git history; this changelog remains headed by the active release chain and the Phase 6+ safety/roadmap record.

## 0.1.191
- add read-only Phase 11 canary evidence pack observation runner and CLI orchestration.
