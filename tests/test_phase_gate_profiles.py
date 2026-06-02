from pathlib import Path
from mpf.services.phase11e_limited_activation_common import PHASE11_PRE_FINAL_ACCEPTANCE_GATE,PHASE11_POST_FINAL_ACCEPTANCE_GATE,validate_current_phase_gate

def make(tmp_path,values):
 p=tmp_path/'status.md';p.write_text('## Current State\n\n```text\n'+'\n'.join(f'{k}: {v}' for k,v in values.items())+'\n```\n');return p
def test_profiles_are_explicit_and_distinct(): assert PHASE11_PRE_FINAL_ACCEPTANCE_GATE != PHASE11_POST_FINAL_ACCEPTANCE_GATE
def test_historical_pre_fixture_validates_but_live_repo_does_not(tmp_path):
 b=[];validate_current_phase_gate(b,phase_status_path=make(tmp_path,PHASE11_PRE_FINAL_ACCEPTANCE_GATE),requirements=PHASE11_PRE_FINAL_ACCEPTANCE_GATE);assert b==[]
 b=[];validate_current_phase_gate(b,requirements=PHASE11_PRE_FINAL_ACCEPTANCE_GATE);assert b
def test_live_repo_is_post_acceptance(): b=[];validate_current_phase_gate(b,requirements=PHASE11_POST_FINAL_ACCEPTANCE_GATE);assert b==[]
