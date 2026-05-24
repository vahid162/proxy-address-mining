# Phase 11D farm5 0.1.197 Controlled Canary Acceptance Decision Evidence

- version: 0.1.197
- farm5 baseline: 0.1.168
- operator: vahid

## Exact command summary
`mpf production canary-acceptance-decision --expected-version 0.1.197 --farm5-baseline-version 0.1.168 --customer-key canary-btc-001 --lane btc --port 20001 --backend-target 172.18.0.3:60010 --evidence-pack-dir /tmp/phase11-canary-evidence-pack-0.1.195-live --evidence-archive-path /tmp/phase11-canary-evidence-pack-0.1.195-live.tar.gz --expected-archive-sha256 ebd1832d374dcf907aa54b0628d6ab022f9e8b988779ab1953f5e072e254fc51 --operator "vahid" --reason "Accept Phase 11D controlled canary evidence-pack after farm5 0.1.195 live evidence review" --operator-confirmed --i-have-reviewed-evidence-pack --i-confirm-no-real-customer-onboarding --i-confirm-no-production-traffic-authorized --i-confirm-phase11-not-final-accepted --output json`

- evidence pack path: `/tmp/phase11-canary-evidence-pack-0.1.195-live`
- evidence archive path: `/tmp/phase11-canary-evidence-pack-0.1.195-live.tar.gz`
- expected archive sha256: `ebd1832d374dcf907aa54b0628d6ab022f9e8b988779ab1953f5e072e254fc51`
- actual archive sha256: `ebd1832d374dcf907aa54b0628d6ab022f9e8b988779ab1953f5e072e254fc51`

## Exact canary scope
- customer_key: canary-btc-001
- lane: btc
- public_port: 20001
- backend_target: 172.18.0.3:60010

## Accepted evidence summary
- runtime_path_final_decision: RUNTIME_PATH_EVIDENCE_READY
- visibility_bundle_final_decision: VISIBILITY_READY
- acceptance_review_final_decision: ACCEPTANCE_REVIEW_READY
- conntrack_assured: true
- forwarder_pool_seen: true
- bridge_loopback_seen: true
- stratum_subscribe_ok: true
- stratum_authorize_ok: true
- stratum_set_difficulty_seen: true
- stratum_notify_seen: true

## Decision
- final_decision: CANARY_ACCEPTANCE_DECISION_ACCEPTED
- phase11d_canary_accepted: true
- next_required_step: phase11e_limited_onboarding_gate_design

## Explicit safety boundary
- phase11_accepted: false
- limited_onboarding_allowed: false
- production_traffic_enabled: false
- no_onboarding_authorized: true
- mutation_performed: false
- firewall_mutation_performed: false
- nat_mutation_performed: false
- conntrack_mutation_performed: false
- docker_mutation_performed: false
- db_mutation_performed: false

The existing canary NAT/firewall artifact is controlled canary state only and does not authorize real customer onboarding.
