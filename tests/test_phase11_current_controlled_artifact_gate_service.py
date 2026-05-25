from mpf.services.phase11_current_controlled_artifact_gate_service import build_phase11_current_controlled_artifact_gate_report

PHASE='''current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5\ncurrent_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness\nproduction_traffic: none\nfirewall_apply_allowed: no\nabuse_automation_allowed: no\ncustomer_onboarding_allowed: db_only\n'''

def test_no_artifacts_pass():
    r=build_phase11_current_controlled_artifact_gate_report(iptables_save_text='*filter\nCOMMIT\n',phase_status_text=PHASE)
    assert r['final_decision']=='PASS_NO_CUSTOMER_ARTIFACTS'

def test_known_artifacts_pass():
    ipt='''-N MPFC_20001\n-N MPFC_20101\n-N MPF_NAT_PRE\n-A MPF_NAT_PRE -p tcp --dport 20001 -j DNAT --to-destination 172.18.0.3:60010\n-A MPF_NAT_PRE -p tcp --dport 20101 -j DNAT --to-destination 172.18.0.3:60010\n-A MPFC_20001 -m comment --comment "customer_connlimit_reject:canary-btc-001" -j REJECT\n-A MPFC_20101 -m comment --comment "customer_hashlimit_reject:limited-btc-001" -j REJECT\n'''
    r=build_phase11_current_controlled_artifact_gate_report(iptables_save_text=ipt,phase_status_text=PHASE)
    assert r['final_decision']=='PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS'

def test_unknown_blocked():
    r=build_phase11_current_controlled_artifact_gate_report(iptables_save_text='-N MPFC_20202\n',phase_status_text=PHASE)
    assert r['final_decision']=='BLOCKED_UNKNOWN_MPF_ARTIFACTS'

def test_wrong_dnat_blocked():
    r=build_phase11_current_controlled_artifact_gate_report(iptables_save_text='-A MPF_NAT_PRE -p tcp --dport 20101 -j DNAT --to-destination 172.18.0.5:60010',phase_status_text=PHASE)
    assert r['final_decision']=='BLOCKED_UNKNOWN_MPF_ARTIFACTS'

def test_ipv6_blocked():
    r=build_phase11_current_controlled_artifact_gate_report(iptables_save_text='',ip6tables_save_text='-N MPFC_20001',phase_status_text=PHASE)
    assert r['final_decision']=='BLOCKED_UNKNOWN_MPF_ARTIFACTS'
