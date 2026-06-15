#!/usr/bin/env bash
set -Eeuo pipefail

BODY_FILE="${1:-/tmp/pr_body.md}"
if [[ $# -gt 0 ]]; then
  shift
fi

if [[ ! -f "$BODY_FILE" ]]; then
  echo "PR body file is missing: $BODY_FILE" >&2
  exit 1
fi

python scripts/validate_runtime_first_pr_body.py "$BODY_FILE"
gh pr create --body-file "$BODY_FILE" "$@"
