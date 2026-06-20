from __future__ import annotations
from pathlib import Path

from mpf.services.historical_phase_status import read_historical_phase_status
from mpf.config import MPFConfig
from mpf.services.firewall_no_customer_apply_execution_gate_service import build_no_customer_apply_execution_gate_report
from mpf.services.firewall_no_customer_apply_package_service import build_no_customer_apply_package_report

FLAGS=("live_firewall_write_allowed","live_firewall_apply_allowed","live_firewall_verify_allowed","live_firewall_rollback_allowed","iptables_restore_allowed","iptables_restore_executed","subprocess_firewall_calls_allowed","subprocess_firewall_calls_executed","real_adapter_allowed","real_adapter_executed","restore_point_write_allowed","restore_point_written","lock_acquisition_allowed","lock_acquired","db_apply_record_write_allowed","db_apply_record_written","db_mutation","filesystem_write_executed","customer_nat_allowed","customer_nat_changed","customer_firewall_rules_allowed","customer_firewall_rules_changed","production_traffic_changed","usage_automation_allowed","abuse_automation_allowed_runtime","ui_allowed_runtime","telegram_allowed_runtime")

def _parse_current_state_block(text:str)->dict[str,str]|None:
 s=text.find('## Current State');a=text.find('```text',s);b=text.find('```',a+7) if a>=0 else -1
 if s<0 or a<0 or b<0:return None
 out={}
 for line in text[a+7:b].strip().splitlines():
  if ':' in line:k,v=line.split(':',1);out[k.strip()]=v.strip()
 return out or None

def _all_false(r:dict[str,object])->bool:return all(r.get(k) is False for k in FLAGS)

def build_no_customer_apply_execution_acceptance_report(cfg: MPFConfig, repo_root: Path | None = None) -> dict[str, object]:
 root=repo_root or Path(__file__).resolve().parents[2]; ps=root/'docs'/'PHASE_STATUS.md'; blockers=[]; errors=[]
 text=ps.read_text(encoding='utf-8') if ps.exists() else ''
 if not ps.exists(): blockers.append('historical phase-status archive is missing')
 cur=_parse_current_state_block(text)
 expected={"current_accepted_phase":"Phase 5 — Customer CRUD in DB Only accepted on farm5","current_working_phase":"Phase 6 — Firewall Planner","server_state":"farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active","production_traffic":"none","firewall_apply_allowed":"no","abuse_automation_allowed":"no","customer_onboarding_allowed":"db_only","proxy_data_plane_allowed":"limited_runtime_local_only","ui_allowed":"no","telegram_allowed":"no","live_snapshot_read_allowed":"iptables_save_read_only","restore_lock_record_execution_allowed":"controlled_boundary_only"}
 current_state_preserved=cur is not None and all(cur.get(k)==v for k,v in expected.items())
 if cur is None:blockers.append('Current State is missing or malformed')
 elif not current_state_preserved:blockers.append('Current State is missing or changed')
 apply_mode_plan_only=cfg.firewall.apply_mode=='plan_only'; runtime_activation_allowed=bool(cfg.proxy.runtime_activation_allowed)
 if not apply_mode_plan_only:blockers.append('firewall.apply_mode is not plan_only')
 if runtime_activation_allowed:blockers.append('proxy.runtime_activation_allowed is true')
 ev={
 'read_only_snapshot_evidence_present':"### Phase 6 Read-Only iptables-save Snapshot — Server Evidence" in text,
 'controlled_restore_lock_record_evidence_present':"### Phase 6 Controlled Restore/Lock/DB Apply Record Execution — Server Evidence" in text,
 'no_customer_apply_acceptance_gate_server_evidence_present':"### Phase 6 No-Customer Apply/Verify/Rollback Acceptance Gate — Server Evidence" in text,
 'no_customer_apply_execution_gate_server_evidence_present':"### Phase 6 No-Customer Apply/Verify/Rollback Execution Gate — Server Evidence" in text,
 }
 for k,v in ev.items():
  if not v:blockers.append(f'any required evidence section is missing: {k}')
 eg=build_no_customer_apply_execution_gate_report(cfg,repo_root=root); pkg=build_no_customer_apply_package_report(cfg,repo_root=root)
 egp=bool(eg); egb=eg.get('final_decision')=='BLOCKED'; eged=eg.get('execution_allowed') is False; egmf=_all_false(eg)
 if not egp:blockers.append('execution gate report is missing')
 if not egb:blockers.append('execution gate report is not BLOCKED')
 if not eged:blockers.append('execution gate execution_allowed is not false')
 if not egmf:blockers.append('any execution gate mutation flag is true')
 pkgp=bool(pkg); pkgb=pkg.get('final_decision')=='BLOCKED'; pkged=pkg.get('execution_allowed') is False; pkgmf=_all_false(pkg)
 safe= not any(pkg.get(k,False) for k in ("payload_contains_customer_nat","payload_contains_customer_firewall_rules","payload_contains_production_traffic","payload_contains_iptables_restore","payload_contains_subprocess_call","payload_contains_db_write","payload_contains_file_write","payload_contains_lock_acquisition","payload_contains_restore_point_write"))
 if not pkgp:blockers.append('package report is missing')
 if not pkgb:blockers.append('package report is not BLOCKED')
 if not pkged:blockers.append('package execution_allowed is not false')
 if not pkgmf:blockers.append('any package mutation flag is true')
 if not safe:blockers.append('package is not customer-safe')

 req={"current_state_preserved":current_state_preserved,"config_apply_mode_plan_only":apply_mode_plan_only,"proxy_runtime_activation_disabled":not runtime_activation_allowed,**ev,
 "no_customer_apply_execution_gate_present":egp,"no_customer_apply_package_present":pkgp,"no_customer_apply_package_customer_safe":safe,"no_customer_apply_execution_gate_blocked":egb,"no_customer_apply_package_blocked":pkgb,
 "no_customer_apply_execution_gate_execution_disallowed":eged,"no_customer_apply_package_execution_disallowed":pkged,"no_customer_apply_execution_gate_mutation_flags_false":egmf,"no_customer_apply_package_mutation_flags_false":pkgmf,
 "no_customer_nat":True,"no_customer_firewall_rules":True,"no_production_traffic":True,"no_usage_automation":True,"no_abuse_automation":True,"separate_operator_runtime_execution_approval_still_required":True,"fresh_farm5_runtime_execution_evidence_still_required":True,"explicit_rollback_evidence_still_required":True,"explicit_verify_evidence_still_required":True}
 checklist=[{"item":k,"status":"PASS" if v else "BLOCKED"} for k,v in req.items()]
 return {"component":"firewall_no_customer_apply_execution_acceptance","phase":"Phase 6 — Firewall Planner","gate_type":"no_customer_apply_verify_rollback_execution_acceptance","final_decision":"BLOCKED","authorization_status":"EXECUTION_ACCEPTANCE_DEFINED_NOT_EXECUTABLE","gate_status":"EXECUTION_ACCEPTANCE_REPORT_ONLY","inspection_only":True,"report_only":True,"preflight_only":True,"dry_run":True,"execution_allowed":False,"apply_decision":"BLOCKED","verify_decision":"BLOCKED","rollback_decision":"BLOCKED",
 "current_state_preserved":current_state_preserved,"apply_mode_plan_only":apply_mode_plan_only,"runtime_activation_allowed":runtime_activation_allowed,
 "no_customer_apply_execution_gate_report_present":egp,"no_customer_apply_execution_gate_blocked":egb,"no_customer_apply_execution_gate_execution_disallowed":eged,"no_customer_apply_execution_gate_mutation_flags_false":egmf,
 "no_customer_apply_package_report_present":pkgp,"no_customer_apply_package_blocked":pkgb,"no_customer_apply_package_execution_disallowed":pkged,"no_customer_apply_package_mutation_flags_false":pkgmf,"no_customer_apply_package_customer_safe":safe,
 **ev,"execution_acceptance_checklist":checklist,**{k:False for k in FLAGS},"blockers":blockers,"errors":errors}
