#!/usr/bin/env bash
set -euo pipefail
usage(){ cat >&2 <<'EOF'
Usage: scripts/phase11_controlled_duplicate_nat_cleanup.sh MODE [mpf args...]
Modes: --plan --package --execute-preflight --execute --verify --rollback-contract --post-cleanup-readiness
EOF
}
[[ $# -ge 1 ]] || { usage; exit 2; }
MODE="$1"; shift; MPF_BIN="${MPF_BIN:-mpf}"
case "$MODE" in
  --plan) exec "$MPF_BIN" production controlled-duplicate-nat-cleanup --mode plan "$@" ;;
  --package) exec "$MPF_BIN" production controlled-duplicate-nat-cleanup --mode package "$@" ;;
  --execute-preflight) exec "$MPF_BIN" production controlled-duplicate-nat-cleanup --mode execute-preflight "$@" ;;
  --execute) [[ "${MPF_PHASE11_CONTROLLED_DUPLICATE_NAT_CLEANUP:-}" == allow ]] || { echo "MPF_PHASE11_CONTROLLED_DUPLICATE_NAT_CLEANUP=allow is required" >&2; exit 1; }; exec "$MPF_BIN" production controlled-duplicate-nat-cleanup --mode execute "$@" ;;
  --verify) exec "$MPF_BIN" production controlled-duplicate-nat-cleanup --mode verify "$@" ;;
  --rollback-contract) exec "$MPF_BIN" production controlled-duplicate-nat-cleanup --mode rollback-contract "$@" ;;
  --post-cleanup-readiness) exec "$MPF_BIN" production controlled-duplicate-nat-cleanup --mode post-cleanup-readiness "$@" ;;
  -h|--help) usage ;;
  *) echo "unknown mode: $MODE" >&2; usage; exit 2 ;;
esac
