from pathlib import Path
TARGET='''current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5
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
def test_phase_status_current_state_target(): assert TARGET in Path('docs/PHASE_STATUS.md').read_text()
def test_remaining_plan_phase11_operational_completion(): assert '## Phase 11 operational completion Active Target Position (0.1.237)' in Path('docs/REMAINING_PHASE_PLAN.md').read_text()
