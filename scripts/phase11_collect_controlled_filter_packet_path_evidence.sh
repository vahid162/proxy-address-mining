#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <explicit-output-root>" >&2
  exit 2
fi

OUTPUT_ROOT="$1"
if [[ -z "${OUTPUT_ROOT}" || -L "${OUTPUT_ROOT}" ]]; then
  echo "output root must be explicit and not a symlink" >&2
  exit 2
fi
mkdir -p "${OUTPUT_ROOT}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
COLLECTION_DIR="${OUTPUT_ROOT%/}/controlled-filter-packet-path-${STAMP}"
if [[ -e "${COLLECTION_DIR}" ]]; then
  echo "collection directory already exists: ${COLLECTION_DIR}" >&2
  exit 2
fi

PLAN_JSON="$(mktemp)"
COLLECT_JSON="$(mktemp)"
VERIFY_JSON="$(mktemp)"
trap 'rm -f "${PLAN_JSON}" "${COLLECT_JSON}" "${VERIFY_JSON}"' EXIT

mpf production controlled-filter-packet-path-plan --output json >"${PLAN_JSON}"
mpf production controlled-filter-packet-path-collect --output-dir "${COLLECTION_DIR}" --output json >"${COLLECT_JSON}"
mpf production controlled-filter-packet-path-verify --evidence-dir "${COLLECTION_DIR}" --output json >"${VERIFY_JSON}"

python - "${PLAN_JSON}" "${COLLECT_JSON}" "${VERIFY_JSON}" "${COLLECTION_DIR}" <<'PY'
import json, pathlib, sys
plan=json.loads(pathlib.Path(sys.argv[1]).read_text())
collect=json.loads(pathlib.Path(sys.argv[2]).read_text())
verify=json.loads(pathlib.Path(sys.argv[3]).read_text())
collection_dir=sys.argv[4]
manifest=pathlib.Path(collection_dir)/"manifest.sha256"
print(f"plan_final_decision={plan.get('final_decision')}")
print(f"collect_final_decision={collect.get('final_decision')}")
print(f"verify_final_decision={verify.get('final_decision')}")
print(f"collection_dir={collection_dir}")
if manifest.exists():
    print(f"manifest_sha256={manifest.read_text().split()[0]}")
PY
