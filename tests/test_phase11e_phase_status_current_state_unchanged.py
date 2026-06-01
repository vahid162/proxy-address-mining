from pathlib import Path
EXPECTED = '''current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5
current_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only'''
def test_phase_status_current_state_fenced_block_is_unchanged():
 text=Path('docs/PHASE_STATUS.md').read_text(); section=text.split('## Current State',1)[1].split('\n## ',1)[0]; assert section.split('```text',1)[1].split('```',1)[0].strip()==EXPECTED
