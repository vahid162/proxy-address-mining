from pathlib import Path


def test_runtime_first_pr_template_required_headings_only():
    text = Path('.github/PULL_REQUEST_TEMPLATE/runtime-first.md').read_text(encoding='utf-8')
    for heading in ['Why', 'What', 'How to test', 'Version: X.Y.Z -> A.B.C', 'Risk + Rollback']:
        assert heading in text
    for banned in ['Motivation', 'Description', 'Testing']:
        assert banned not in text


def test_governance_pr_template_has_minimal_required_headings():
    text = Path('.github/PULL_REQUEST_TEMPLATE/governance.md').read_text(encoding='utf-8')
    for heading in ['Why', 'What', 'How to test', 'governance-documentation']:
        assert heading in text
    assert 'Version: X.Y.Z -> A.B.C' not in text
