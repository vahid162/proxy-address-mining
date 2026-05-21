# Phase 11 farm5 0.1.162 Sync/Test Evidence

- farm5 synced 0.1.162 successfully
- pytest: 859 passed
- mpf doctor/db/proxy/phase gate: OK
- production_traffic: none
- firewall_apply_allowed: no
- customer_onboarding_allowed: db_only
- abuse_automation_allowed: no
- ui_allowed: no
- telegram_allowed: no
- safe-check execution remained blocked on `single_canary_restore_payload_not_apply_safe` / `accepted_apply_safe_single_canary_payload`
- no MPF/customer IPv4/IPv6 refs, no customer NAT redirects
- only Docker local publish DNAT for 127.0.0.1:60010
- accepted listeners: 127.0.0.1:2015 and 127.0.0.1:60010
