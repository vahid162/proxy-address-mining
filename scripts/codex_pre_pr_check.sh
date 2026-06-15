#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ! -f /tmp/pr_body.md ]]; then
  echo "Missing /tmp/pr_body.md. Generate it with: python scripts/validate_runtime_first_pr_body.py --print-template > /tmp/pr_body.md" >&2
  exit 1
fi

python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md
python -m pytest tests/test_ai_runtime_first_project_governance.py -q
python -m pytest tests/test_ai_pr_validation_recovery.py -q
python -m pytest tests/test_version_consistency.py -q
python -m pytest -q
git diff --check

echo "OK_TO_CREATE_RUNTIME_FIRST_PR"
