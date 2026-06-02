from pathlib import Path
EXPECTED = '''current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5
current_working_phase: Phase 11 operational completion
server_state: farm5 controlled CLI-limited BTC production/customer activation is accepted; operational completion is required before Phase 12 implementation
production_traffic: controlled_cli_limited
firewall_apply_allowed: controlled
abuse_automation_allowed: controlled_operator_gated
customer_onboarding_allowed: controlled_cli_limited
proxy_data_plane_allowed: limited_runtime_local_only
worker_enforcement_allowed: no
ui_allowed: no
telegram_allowed: no
phase12_start_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only'''
def test_phase_status_current_state_fenced_block_is_unchanged():
 text=Path('docs/PHASE_STATUS.md').read_text(); section=text.split('## Current State',1)[1].split('\n## ',1)[0]; assert section.split('```text',1)[1].split('```',1)[0].strip()==EXPECTED
