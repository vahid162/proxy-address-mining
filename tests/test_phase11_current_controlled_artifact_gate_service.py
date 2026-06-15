from mpf.services.phase11_current_controlled_artifact_gate_service import build_phase11_current_controlled_artifact_gate_report

PHASE='''current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5\ncurrent_working_phase: Phase 11 operational completion — Full CLI Production Operations\nproduction_traffic: controlled_cli_limited\nfirewall_apply_allowed: controlled\nabuse_automation_allowed: controlled_operator_gated\ncustomer_onboarding_allowed: controlled_cli_limited\nworker_enforcement_allowed: no\nui_allowed: no\ntelegram_allowed: no\nphase12_start_allowed: no\n'''
HISTORICAL_PHASE='''current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5\ncurrent_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness\nproduction_traffic: none\nfirewall_apply_allowed: no\nabuse_automation_allowed: no\ncustomer_onboarding_allowed: db_only\n'''

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


def test_historical_pre_acceptance_phase_is_non_authorizing():
    r=build_phase11_current_controlled_artifact_gate_report(iptables_save_text='*filter\nCOMMIT\n',phase_status_text=HISTORICAL_PHASE)
    assert r['final_decision']=='BLOCKED_PHASE_GATE_MISMATCH'
    assert 'phase_gate_mismatch' in r['blockers']

OFFICIAL_FULL = '''*filter
:MPF_INPUT - [0:0]
:MPF_CUSTOMERS - [0:0]
:MPF_GUARD - [0:0]
:MPF_ACCT_IN - [0:0]
:MPF_ACCT_OUT - [0:0]
:MPFL_btc - [0:0]
:MPFC_20001 - [0:0]
:MPFO_20001 - [0:0]
:MPFC_20101 - [0:0]
:MPFO_20101 - [0:0]
-A DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:backend_guard" -j MPF_GUARD
-A DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:accounting" -j MPF_ACCT_IN
-A DOCKER-USER -p tcp --dport 60010 -m comment --comment "mpf:hook:verified_user_forward_post_dnat:customers" -j MPF_CUSTOMERS
-A MPF_CUSTOMERS -p tcp --dport 60010 -m comment --comment "mpf:canary-btc-001:customer_dispatch" -j MPFC_20001
-A MPF_CUSTOMERS -p tcp --dport 60010 -m comment --comment "mpf:limited-btc-001:customer_dispatch" -j MPFC_20101
-A MPFC_20001 -p tcp --dport 60010 -m comment --comment "mpf:canary-btc-001:customer_connlimit_reject" -j REJECT
-A MPFC_20101 -p tcp --dport 60010 -m comment --comment "mpf:limited-btc-001:customer_hashlimit_reject" -j REJECT
-A MPF_ACCT_IN -p tcp --dport 60010 -m comment --comment "mpf:canary-btc-001:customer_accounting_in" -j RETURN
-A MPF_ACCT_OUT -p tcp --dport 60010 -m comment --comment "mpf:limited-btc-001:customer_accounting_out" -j RETURN
COMMIT
*nat
:MPF_NAT_PRE - [0:0]
:MPF_NAT_POST - [0:0]
-A PREROUTING -p tcp -m comment --comment "mpf:hook:nat_prerouting" -j MPF_NAT_PRE
-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment "mpf:canary-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.2:60010
-A MPF_NAT_PRE -p tcp --dport 20101 -m comment --comment "mpf:limited-btc-001:customer_nat_redirect" -j DNAT --to-destination 172.18.0.2:60010
COMMIT
'''

def test_official_taxonomy_chains_and_comments_pass_with_resolved_backend_target():
    r = build_phase11_current_controlled_artifact_gate_report(iptables_save_text=OFFICIAL_FULL, phase_status_text=PHASE, expected_backend_target="172.18.0.2:60010")
    assert r['final_decision'] == 'PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS'
    assert r['unknown_mpf_artifacts'] == []


def test_official_looking_wrong_backend_target_blocked():
    r = build_phase11_current_controlled_artifact_gate_report(iptables_save_text=OFFICIAL_FULL, phase_status_text=PHASE, expected_backend_target="172.18.0.9:60010")
    assert r['final_decision'] == 'BLOCKED_UNKNOWN_MPF_ARTIFACTS'
    assert 'unknown_mpf_artifacts_detected' in r['blockers']


def test_unknown_mpf_like_comment_on_official_chain_blocked():
    text = OFFICIAL_FULL.replace('mpf:canary-btc-001:customer_dispatch', 'mpf:canary-btc-001:customer_surprise')
    r = build_phase11_current_controlled_artifact_gate_report(iptables_save_text=text, phase_status_text=PHASE, expected_backend_target="172.18.0.2:60010")
    assert r['final_decision'] == 'BLOCKED_UNKNOWN_MPF_ARTIFACTS'
