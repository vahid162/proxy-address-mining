from mpf.services.phase11_current_controlled_artifact_gate_service import build_phase11_current_controlled_artifact_gate_report

PHASE='''current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5\ncurrent_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness\nproduction_traffic: none\nfirewall_apply_allowed: no\nabuse_automation_allowed: no\ncustomer_onboarding_allowed: db_only\n'''

REAL_BASE='''*filter
:MPFC_20001 - [0:0]
:MPFC_20101 - [0:0]
:MPF_NAT_PRE - [0:0]
-A MPFC_20001 -p tcp -m tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_connlimit_reject" -j REJECT
-A MPFC_20101 -p tcp -m tcp --dport 20101 -m comment --comment "mpf:limited-btc-001:customer_connlimit_reject" -j REJECT
-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.3:60010
-A MPF_NAT_PRE -p tcp --dport 20101 -m comment --comment "mpf:limited-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.3:60010
COMMIT
'''

def test_no_artifacts_pass():
    r=build_phase11_current_controlled_artifact_gate_report(iptables_save_text='*filter\nCOMMIT\n',phase_status_text=PHASE)
    assert r['final_decision']=='PASS_NO_CUSTOMER_ARTIFACTS'

def test_real_farm5_known_artifacts_pass():
    r=build_phase11_current_controlled_artifact_gate_report(iptables_save_text=REAL_BASE,phase_status_text=PHASE,expected_backend_target="172.18.0.3:60010")
    assert r['final_decision']=='PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS'

def test_real_unknown_chain_blocked():
    t=REAL_BASE.replace(':MPF_NAT_PRE - [0:0]',''' :MPF_NAT_PRE - [0:0]\n:MPFC_20202 - [0:0]''')
    r=build_phase11_current_controlled_artifact_gate_report(iptables_save_text=t,phase_status_text=PHASE,expected_backend_target="172.18.0.3:60010")
    assert r['final_decision']=='BLOCKED_UNKNOWN_MPF_ARTIFACTS'

def test_unknown_customer_comment_blocked():
    t=REAL_BASE.replace('mpf:limited-btc-001:customer_connlimit_reject','mpf:bad-customer:customer_connlimit_reject')
    r=build_phase11_current_controlled_artifact_gate_report(iptables_save_text=t,phase_status_text=PHASE,expected_backend_target="172.18.0.3:60010")
    assert r['final_decision']=='BLOCKED_UNKNOWN_MPF_ARTIFACTS'

def test_wrong_dnat_target_blocked():
    t=REAL_BASE.replace('20101 -m comment --comment "mpf:limited-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.3:60010','20101 -m comment --comment "mpf:limited-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.5:60010')
    r=build_phase11_current_controlled_artifact_gate_report(iptables_save_text=t,phase_status_text=PHASE,expected_backend_target="172.18.0.3:60010")
    assert r['final_decision']=='BLOCKED_UNKNOWN_MPF_ARTIFACTS'

def test_nat_pre_non_dnat_blocked():
    t=REAL_BASE + '-A MPF_NAT_PRE -p tcp --dport 20101 -j RETURN\n'
    r=build_phase11_current_controlled_artifact_gate_report(iptables_save_text=t,phase_status_text=PHASE,expected_backend_target="172.18.0.3:60010")
    assert r['final_decision']=='BLOCKED_UNKNOWN_MPF_ARTIFACTS'

def test_ipv6_blocked():
    r=build_phase11_current_controlled_artifact_gate_report(iptables_save_text=REAL_BASE,expected_backend_target="172.18.0.3:60010",ip6tables_save_text=':MPFC_20001 - [0:0]',phase_status_text=PHASE)
    assert r['final_decision']=='BLOCKED_UNKNOWN_MPF_ARTIFACTS'

def test_wrong_expected_version_blocked_phase_mismatch():
    r=build_phase11_current_controlled_artifact_gate_report(iptables_save_text=REAL_BASE,phase_status_text=PHASE,expected_backend_target="172.18.0.3:60010",expected_version='0.1.208')
    assert r['final_decision']=='BLOCKED_PHASE_GATE_MISMATCH'
    assert 'wrong_expected_version' in r['blockers']
