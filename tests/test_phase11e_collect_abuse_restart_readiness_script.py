from pathlib import Path

def test_script_real_source_collection_enforced():
 t=Path('scripts/phase11e_collect_abuse_restart_readiness_evidence.sh').read_text()
 banned=[
  "iptables_save_text=''",
  "ip6tables_save_text=''",
  "required_containers_running':True",
  "v2raya_running_before_forwarder_check':True",
  "socks_bridge_ready_before_forwarder_check':True",
  "forwarder_ready':True",
  "bridge_ready':True",
  "backend_60010_local_or_internal_reachable':True",
  "public_v2raya_ui_exposed':False",
  "backend_60010_publicly_exposed':False",
 ]
 for x in banned:
  assert x not in t
 for x in ['docker-ps.txt','ss-listen.txt','required_names','backend_public','public_v2raya_ui','controlled_order_test_performed','iptables-save','ip6tables-save']:
  assert x in t
