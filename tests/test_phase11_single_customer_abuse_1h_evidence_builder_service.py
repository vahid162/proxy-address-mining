import hashlib, json
from pathlib import Path
from mpf.config import load_config
from mpf.services import phase11_single_customer_abuse_1h_evidence_builder_service as s
from mpf.services import phase11_single_customer_abuse_1h_readiness_service as r
cfg=lambda: load_config(Path('configs/mpf.example.yaml'))
V={"final_decision":"PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY","visibility_bundle_ready":True,"expected_version":"0.1.218","repository_version":"0.1.218","candidate_customer_key":"limited-btc-001","candidate_lane":"btc","candidate_public_port":20101,"candidate_backend_target":"172.18.0.3:60010","production_traffic_enabled":False,"miner_traffic_allowed":False,"phase11_accepted":False,"db_activation_allowed":False,"mutation_performed":False}

def w(p,o): p.write_text(json.dumps(o)); return p

def base(v,**kw):
 h=hashlib.sha256(v.read_bytes()).hexdigest()
 return s.build_phase11_single_customer_abuse_1h_evidence_report(cfg(),expected_version='0.1.220',visibility_bundle_json=v,visibility_bundle_json_sha256=h,operator='o',reason='r',operator_confirmed=True,i_understand_evidence_only=True,i_understand_no_abuse_automation_enable=True,i_understand_no_hard_block=True,i_understand_no_firewall_apply=True,i_understand_no_db_mutation=True,i_understand_no_production_traffic=True,i_understand_no_miner_traffic=True,**kw)

def test_default_blocked(tmp_path):
 v=w(tmp_path/'v.json',V); rep=base(v)
 assert rep['final_decision']=='BLOCKED'
 assert 'missing_active_customer_coverage_source' in rep['blockers']

def test_ready_only_with_explicit_sources(tmp_path):
 v=w(tmp_path/'v.json',V)
 rep=base(v,active_enabled_lane_customers=['canary-btc-001'],paused_candidate_customers=['limited-btc-001'],disabled_lanes=[],skipped_active_customers=[],missing_active_customers=[],state_machine_contract=['normal','over_tracking','over_grace','hard'],transition_coverage=['normal->over_tracking','over_tracking->over_grace','over_grace->normal','over_grace->over_tracking','over_tracking->hard_after_threshold'],hard_threshold_sec=3600,exemption_policy_validated=True,manual_unhard_audited=True,restore_point_required_for_hard=True,policy_backup_required_for_hard=True,farms_over_alone_hardens=False,worker_over_alone_hardens=False,db_failure_hardens=False,firewall_failure_hardens=False,missing_or_stale_evidence_hardens=False,active_customer_coverage_source='mpf customer list',abuse_contract_source='docs/ABUSE.md',exemption_contract_source='docs/ABUSE.md',hard_threshold_source='docs/ABUSE.md',manual_unhard_audit_source='docs/ABUSE.md',restore_policy_backup_source='docs/ABUSE.md')
 assert rep['final_decision'].endswith('READY') and rep['mutation_performed'] is False
 a=tmp_path/'a.json'; a.write_text(json.dumps(rep))
 rr=r.build_phase11_single_customer_abuse_1h_readiness_report(cfg(),expected_version='0.1.220',visibility_bundle_json=v,visibility_bundle_json_sha256=hashlib.sha256(v.read_bytes()).hexdigest(),abuse_evidence_json=a,operator='o',reason='r',operator_confirmed=True,i_understand_abuse_readiness_only=True,i_understand_no_abuse_automation_enable=True,i_understand_no_hard_block_automation=True,i_understand_no_production_traffic_acceptance=True,i_understand_no_miner_traffic_acceptance=True,i_understand_no_db_activation=True)
 assert rr['final_decision'].endswith('READY')
