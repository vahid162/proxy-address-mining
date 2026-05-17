from pathlib import Path

from mpf.config import load_config
from mpf.services.phase8_final_acceptance_service import build_phase8_final_acceptance_report


def _cfg():
    return load_config(Path('configs/mpf.example.yaml'))


def test_final_acceptance_report_accepts_with_closed_gates() -> None:
    r = build_phase8_final_acceptance_report(_cfg())
    assert r['component'] == 'phase8_final_acceptance'
    assert r['execution_allowed'] is False
    assert r['production_activation_allowed'] is False
    assert r['runtime_worker_authorized'] is False
    assert r['firewall_apply_authorized'] is False


def test_final_acceptance_report_fails_closed_when_gate_missing(tmp_path: Path) -> None:
    repo = tmp_path
    (repo / 'docs').mkdir(parents=True, exist_ok=True)
    (repo / 'docs/PHASE_STATUS.md').write_text('current_accepted_phase: Phase 9 — Check / Report / Diagnostics accepted on farm5\n', encoding='utf-8')
    (repo / 'docs/PHASE_8_FINAL_ACCEPTANCE_EVIDENCE.md').write_text('# Phase 8 Final Acceptance Evidence\n', encoding='utf-8')
    r = build_phase8_final_acceptance_report(_cfg(), repo_root=repo)
    assert r['final_decision'] == 'BLOCKED'
    assert isinstance(r['blockers'], list)
    assert 'current_working_phase_phase9_missing' in r['blockers']
