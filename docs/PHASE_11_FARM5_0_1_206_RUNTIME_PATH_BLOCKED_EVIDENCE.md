# Phase 11 farm5 0.1.206 runtime-path evidence BLOCKED

Version: 0.1.206

## Scope
Single-customer runtime-path evidence attempt for `limited-btc-001` / `btc` / `20101` -> `172.18.0.3:60010`.

## Sync/test baseline
- previous full pytest after sync: 1349 passed
- mpf doctor: OK
- db status: OK
- proxy doctor: OK
- phase gates unchanged: production_traffic none, firewall_apply_allowed no, abuse_automation_allowed no, customer_onboarding_allowed db_only, ui/telegram no

## Evidence directory and hashes
- directory: `/var/backups/mpf/phase11e-limited-btc-001-20101-runtime-evidence-20260524T165006Z`
- live-iptables-save.txt: `299d0da6488cafdd0cc2551e27245698ccaef3b0a78d8e6221fe681acdf9b8c0`
- conntrack-snapshot.txt: `f44c1407bef98d5405a92f5e4a0646f89f43b970a74b6db68dd87307da97ce8b`
- docker-container-names.txt: `f0b9ea644580ceffc01661ce8e13441d57b033ab73259b2a42cd00f78b34f6cb`
- forwarder-log.txt: `70ff475f832dc6bbca3f98bfd9ade1e8cb094bd638d484169f6f8bb67eb9f227`
- bridge-log.txt: `70ff475f832dc6bbca3f98bfd9ade1e8cb094bd638d484169f6f8bb67eb9f227`
- runtime-logs.txt: `70ff475f832dc6bbca3f98bfd9ade1e8cb094bd638d484169f6f8bb67eb9f227`

## Runtime classifier command summary
Runtime classifier executed with expected version `0.1.206` and post-apply evidence `/tmp/phase11-single-customer-post-apply-evidence-0.1.205.json` (`19ef5602af8ad36267ce34c3ca21e660e32d8970b0a81d69bc80b8a206d41ead`) plus live snapshot/conntrack/forwarder/bridge evidence files.

## Runtime classifier output summary
- output file: `/tmp/phase11-single-customer-runtime-path-evidence-0.1.206-probe.json`
- final_decision: `BLOCKED`
- post_apply_evidence_ready: true
- controlled_apply_recorded: true
- runtime_path_evidence_ready: false
- conntrack_assured_seen: false
- forwarder_pool_seen: true
- bridge_loopback_seen: true
- blockers: `missing_conntrack_runtime_signal`

## Interpretation
- post-apply evidence is ready.
- controlled apply is recorded.
- firewall/NAT artifacts remain present.
- forwarder and bridge evidence are present.
- conntrack ASSURED signal is missing.
- runtime-path evidence remains BLOCKED.

## Explicit boundary
- no production/miner traffic acceptance
- no DB activation
- no Phase 11 acceptance
- no additional firewall apply
- next step: controlled runtime probe diagnostics and stronger conntrack/runtime evidence collection


## Diagnostics/acceptance boundary
- SYN_SENT/UNREPLIED is useful diagnostics evidence but not runtime acceptance.
- ASSURED candidate still does not activate runtime path by itself; runtime-path evidence classifier remains the acceptance classifier.
- The diagnostics service never sets `runtime_path_evidence_ready` to true.
- Production/miner traffic remains blocked.
