from __future__ import annotations
from mpf.config import MPFConfig
from mpf.services.phase11e_limited_activation_common import PHASE11_POST_FINAL_ACCEPTANCE_GATE, SAFE_ARTIFACT_DECISIONS, load_hashed_json, validate_confirmations, validate_current_phase_gate, validate_expected_version, validate_operator
CONFIRMATIONS=("operator_confirmed","i_understand_post_acceptance_verification_only","i_understand_no_db_mutation","i_understand_no_firewall_apply","i_understand_no_runtime_change","i_understand_ui_telegram_remain_disabled","i_understand_worker_enforcement_remains_disabled")
def build_phase11_post_acceptance_verification_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
 del config
 blockers=[]; expected_version=validate_expected_version(kwargs, blockers); validate_operator(kwargs, blockers); validate_confirmations(kwargs, CONFIRMATIONS, blockers)
 acceptance=load_hashed_json(kwargs,"final_acceptance_json","final_acceptance_json_sha256",blockers); artifact=load_hashed_json(kwargs,"artifact_gate_json","artifact_gate_json_sha256",blockers)
 validate_current_phase_gate(blockers, requirements=PHASE11_POST_FINAL_ACCEPTANCE_GATE)
 if not acceptance or acceptance.get("final_decision")!="PHASE11_FINAL_ACCEPTANCE_ACCEPTED" or acceptance.get("phase11_accepted") is not True: blockers.append("final_acceptance_not_accepted")
 if not artifact or artifact.get("final_decision") not in SAFE_ARTIFACT_DECISIONS: blockers.append("artifact_gate_not_passed")
 unknown=[] if not artifact else artifact.get("unknown_mpf_artifacts")
 exposed=None if not artifact else artifact.get("forbidden_public_runtime_exposure")
 if unknown != []: blockers.append("unknown_mpf_artifacts")
 if exposed is not False: blockers.append("forbidden_public_runtime_exposure")
 ready=not blockers
 return {"component":"phase11_post_acceptance_verification","expected_version":expected_version,"repository_version":__import__('mpf').__version__,"phase11_accepted":True,"phase11_operational_completion_required":True,"phase12_start_allowed":"no","production_traffic":"controlled_cli_limited","firewall_apply_allowed":"controlled","abuse_automation_allowed":"controlled_operator_gated","customer_onboarding_allowed":"controlled_cli_limited","worker_enforcement_allowed":"no","ui_allowed":"no","telegram_allowed":"no","artifact_gate_passed":ready and artifact is not None,"unknown_mpf_artifacts":unknown,"forbidden_public_runtime_exposure":exposed,"mutation_performed":False,"db_mutation_performed":False,"firewall_apply_performed":False,"conntrack_flush_performed":False,"docker_restart_performed":False,"systemd_restart_performed":False,"blockers":sorted(set(blockers)),"warnings":[],"next_required_step":"implement_controlled_abuse_operational_core" if ready else "fix_blockers_and_rerun_phase11_post_acceptance_verification","final_decision":"PHASE11_POST_ACCEPTANCE_VERIFICATION_READY" if ready else "BLOCKED"}
