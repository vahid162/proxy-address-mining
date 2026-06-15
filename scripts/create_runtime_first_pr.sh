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

create_output="$(gh pr create --body-file "$BODY_FILE" "$@")"
printf '%s\n' "$create_output"

pr_url="$(printf '%s\n' "$create_output" | awk '/^https?:\/\// {print; exit}')"
if [[ -z "$pr_url" ]]; then
  echo "Unable to determine created PR URL from gh pr create output; cannot verify GitHub PR body." >&2
  exit 1
fi

gh pr view --json body --jq .body "$pr_url" > /tmp/pr_body.github.md
if ! python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.github.md; then
  echo "Created GitHub PR body failed runtime-first validation." >&2
  echo "Fix the GitHub PR body immediately using the canonical template, then rerun validation." >&2
  exit 1
fi
