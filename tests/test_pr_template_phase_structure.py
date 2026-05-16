from pathlib import Path


def test_pr_template_required_headings_only():
    text = Path('.github/PULL_REQUEST_TEMPLATE.md').read_text(encoding='utf-8')
    for heading in ['Why', 'What', 'How to test', 'Version: X.Y.Z -> A.B.C', 'Risk + Rollback']:
        assert heading in text
    for banned in ['Motivation', 'Description', 'Testing']:
        assert banned not in text
