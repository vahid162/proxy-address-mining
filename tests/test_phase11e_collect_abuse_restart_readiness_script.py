from pathlib import Path

def test_script_real_source_collection_enforced():
 t=Path('scripts/phase11e_collect_abuse_restart_readiness_evidence.sh').read_text()
 banned=["iptables_save_text=''","ip6tables_save_text=''","lanes=[{'name':'btc','enabled':True}]","limited-btc-001','status':'paused'","runtime-observation","exposure-observation","docs+tests"]
 for x in banned:
  assert x not in t
 for x in ['iptables-save','ip6tables-save','mpf doctor','mpf db status','mpf proxy doctor','lane_service.list_lane_status','customer_read_service.list_customer_status','missing_real_lane_source','missing_real_customer_source']:
  assert x in t
