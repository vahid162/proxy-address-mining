#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: scripts/phase11_controlled_artifact_refresh.sh MODE [mpf args...]

Modes (explicit, replacement/refresh naming only):
  --plan               Build/read a controlled stale-artifact refresh plan (read-only).
  --package            Build/read a controlled stale-artifact refresh package (read-only).
  --execute-preflight  Run operator review preflight before any execute.
  --execute            Execute only after reviewed READY preflight and explicit mpf gates.
  --verify             Verify corrected post-DNAT graph after controlled refresh.
  --rollback-test      Test reviewed rollback package/payload only.

This wrapper never starts Docker/systemd, never flushes conntrack, and never
performs DB/customer/policy/abuse mutation by itself. Pass any required source
JSON/snapshot/package arguments after the mode; the underlying mpf command must
remain the authority for safety gates.
EOF
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

MODE="$1"
shift
MPF_BIN="${MPF_BIN:-mpf}"

case "${MODE}" in
  --plan)
    exec "${MPF_BIN}" production controlled-artifact-refresh-package "$@"
    ;;
  --package)
    exec "${MPF_BIN}" production controlled-artifact-refresh-package "$@"
    ;;
  --execute-preflight)
    exec "${MPF_BIN}" production controlled-artifact-refresh-package "$@"
    ;;
  --execute)
    if [[ "${MPF_PHASE11_CONTROLLED_ARTIFACT_REFRESH_EXECUTE:-}" != "allow" ]]; then
      echo "MPF_PHASE11_CONTROLLED_ARTIFACT_REFRESH_EXECUTE=allow is required for controlled refresh execute" >&2
      exit 1
    fi
    exec "${MPF_BIN}" production controlled-artifact-refresh-package "$@"
    ;;
  --verify)
    exec "${MPF_BIN}" production controlled-artifact-refresh-package "$@"
    ;;
  --rollback-test)
    exec "${MPF_BIN}" production controlled-artifact-refresh-package "$@"
    ;;
  -h|--help)
    usage
    ;;
  *)
    echo "unknown mode: ${MODE}" >&2
    usage
    exit 2
    ;;
esac
