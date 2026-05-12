from pathlib import Path


def test_phase_status_and_next_step_e1() -> None:
    t = Path('docs/PHASE_STATUS.md').read_text(encoding='utf-8')
    assert 'current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5' in t
    assert 'current_working_phase: Phase 6 — Firewall Planner' in t
    assert 'Phase 6-E2 — Isolated Harness Evidence Package / Boundary Planning, isolated/non-production only' in t


def test_no_cli_live_apply_commands_added() -> None:
    t = Path('mpf/interfaces/cli.py').read_text(encoding='utf-8')
    assert 'def firewall_apply(' not in t
    assert 'def firewall_rollback(' not in t
    assert 'live verify' not in t


def test_docs_do_not_authorize_live_apply_or_host_mutation() -> None:
    docs = [
        'docs/PHASE_6_E1_ISOLATED_HARNESS_HARDENING.md',
        'docs/AI_PHASE_6_TASK.md',
        'docs/FIREWALL.md',
        'docs/REMAINING_PHASE_PLAN.md',
    ]
    text = '\n'.join(Path(d).read_text(encoding='utf-8') for d in docs)
    assert 'does not authorize host production firewall mutation' in text
    assert 'no live read/write' in text or 'live firewall read/write' in text
    assert 'real iptables adapter' in text or 'real iptables adapters' in text
