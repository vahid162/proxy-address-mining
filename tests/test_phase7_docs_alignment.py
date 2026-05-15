from pathlib import Path

def test_readme_phase_alignment() -> None:
    t = Path('README.md').read_text(encoding='utf-8')
    assert 'accepted_phase: Phase 6' in t
    assert 'working_phase: Phase 7' in t
    assert 'production_traffic: none' in t
    assert 'firewall_apply_allowed: no' in t
    assert 'abuse_automation_allowed: no' in t

def test_ai_phase7_and_remaining_plan() -> None:
    ai = Path('docs/AI_PHASE_7_TASK.md').read_text(encoding='utf-8')
    rem = Path('docs/REMAINING_PHASE_PLAN.md').read_text(encoding='utf-8')
    assert 'Usage + Policy/Reject Accounting' in ai
    assert 'normal -> over_tracking -> over_grace -> hard' in ai
    assert 'latest recorded farm5 sync evidence is 0.1.104' in rem


def test_ai_phase7_reports_doctor_section_present() -> None:
    ai = Path('docs/AI_PHASE_7_TASK.md').read_text(encoding='utf-8')
    assert 'Current Phase 7 Step — Read-only Reports/Doctor' in ai
