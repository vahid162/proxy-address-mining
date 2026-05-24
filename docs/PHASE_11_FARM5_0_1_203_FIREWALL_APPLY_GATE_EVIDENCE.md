# Phase 11 farm5 0.1.203 firewall apply-gate evidence

Version: 0.1.203

- pytest: 1266 passed
- mpf doctor: OK
- database: OK
- proxy doctor: OK
- apply_mode: plan_only
- traffic_changes: none
- firewall_mutation: disabled
- abuse_automation: disabled

Current gates remain closed (production_traffic none, firewall_apply_allowed no, abuse_automation_allowed no, customer_onboarding_allowed db_only, ui no, telegram no).

Known live artifact: canary 20001 exists (MPFC_20001 + MPF_NAT_PRE + dport 20001 DNAT -> 172.18.0.3:60010).
No live 20101 rule/reference existed before apply-gate.

Hashes:
- firewall_plan_gate_json_sha256: 0893d1d63b7cb7f60a3473ad9f922c3f65bc9b3e6ff8d5b84aecfa701d45c438
- plan_summary_sha256: 7e971dd7e635f46bde2b568ecf133d6ec9ddd1a211386591a95df97d2ee18a41

Boundary: this evidence authorizes building only the controlled apply-execution PR; it does not authorize unrestricted apply, unrestricted production traffic, miner/customer traffic before post-apply runtime evidence, or Phase 11 acceptance.
