from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding='utf-8')


def test_phase6_h_acceptance_doc_exists() -> None:
    assert Path('docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md').exists()


def test_phase_status_current_state_unchanged() -> None:
    text = _read('docs/PHASE_STATUS.md')
    expected = """## Current State

```text
current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5
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
restore_lock_record_execution_allowed: controlled_boundary_only
```"""
    assert expected in text


def test_phase_status_has_phase6h_accepted_evidence() -> None:
    text = _read('docs/PHASE_STATUS.md')
    assert '### Phase 6-H — Dedicated Apply Gate Entry Criteria / Authorization Boundary' in text
    assert 'version accepted on farm5: 0.1.79' in text
    assert 'docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md added' in text
    assert 'Future dedicated Phase 6 apply gate remains not accepted and not authorized.' in text


def test_phase_status_does_not_enable_forbidden_state() -> None:
    text = _read('docs/PHASE_STATUS.md')
    assert 'firewall_apply_allowed: yes' not in text
    assert 'production_traffic: enabled' not in text
    assert 'abuse_automation_allowed: yes' not in text


def test_index_includes_phase6h_acceptance_in_required_sections() -> None:
    text = _read('docs/INDEX.md')
    start_here = text[text.index('## Start Here'):text.index('## Core Contracts')]
    current_phase = text[text.index('## Current Phase Contracts'):text.index('## Reading Order by Task')]
    assert 'docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md' in start_here
    assert 'docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md' in current_phase
    assert '### `docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md`' in text


def test_no_doc_authorizes_forbidden_live_behaviors_now() -> None:
    docs = [
        'docs/PHASE_STATUS.md', 'docs/INDEX.md', 'docs/AI_PHASE_6_TASK.md', 'docs/FIREWALL.md',
        'docs/ROADMAP.md', 'docs/REMAINING_PHASE_PLAN.md', 'docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md',
    ]
    combined = '\n'.join(_read(p).lower() for p in docs)
    forbidden = [
        'live apply is authorized now', 'iptables-save is allowed now', 'iptables-restore is allowed now',
        'real iptables adapter is allowed now', 'db apply writes are allowed now', 'locks are allowed now',
        'restore point writes are allowed now', 'customer nat redirects are allowed now',
        'customer firewall rules are allowed now', 'production traffic is allowed now',
        'usage automation is allowed now', 'abuse automation is allowed now', 'ui is allowed now',
        'telegram is allowed now'
    ]
    for token in forbidden:
        assert token not in combined


def test_abuse_invariant_preserved() -> None:
    text = _read('docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md')
    assert 'normal -> over_tracking -> over_grace -> hard' in text
    assert 'sustained miner-abuse hardens after about 3600 seconds' in text
    assert 'farms-over alone must not harden' in text
    assert 'worker-over alone must not harden' in text
    assert 'all active customers in enabled lanes must be covered' in text
    assert 'no silent skip is allowed' in text


def test_phase_status_phase6h_placement_and_no_bottom_duplicate() -> None:
    text = _read('docs/PHASE_STATUS.md')
    g = text.index('### Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review')
    h = text.index('### Phase 6-H — Dedicated Apply Gate Entry Criteria / Authorization Boundary')
    warning = text.index('## Current Server Warning')
    assert g < h < warning
    tail = text[text.index('Phase 6-H reference:'):]
    assert '### Phase 6-H — Dedicated Apply Gate Entry Criteria / Authorization Boundary' not in tail


def test_phase_status_next_step_not_planned_only() -> None:
    text = _read('docs/PHASE_STATUS.md')
    assert 'Next planned documentation/test-only step is Phase 6-H' not in text
    assert 'Phase 6-H is planned only' not in text
    assert 'Future dedicated Phase 6 apply gate remains not accepted and not authorized.' in text


def test_index_phase6h_summaries_inside_documentation_summary_not_stop_conditions() -> None:
    text = _read('docs/INDEX.md')
    doc_summary = text.split('## Documentation Summary', 1)[1].split('## Current Roadmap Snapshot', 1)[0]
    stop_block = text.split('## Stop Conditions', 1)[1]
    assert '### `docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md`' in doc_summary
    assert '### `docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md`' in doc_summary
    assert '### `docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md`' not in stop_block
    assert '### `docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md`' not in stop_block


def test_index_current_phase_step_says_phase6h_accepted() -> None:
    text = _read('docs/INDEX.md')
    assert 'Phase 6-H accepted as dedicated apply gate entry criteria / authorization boundary only, documentation/test-only and non-authorizing.' in text


def test_ai_phase6_task_no_stale_phase6g_h_wording() -> None:
    text = _read('docs/AI_PHASE_6_TASK.md')
    assert 'Current active sub-step is Phase 6-G accepted scope only' not in text
    assert 'Phase 6-H is planned only' not in text
    assert 'current sub-step: Phase 6-H accepted' in text
    assert 'Phase 6-H is accepted as dedicated apply gate entry criteria / authorization boundary only, documentation/test-only and non-authorizing' in text
