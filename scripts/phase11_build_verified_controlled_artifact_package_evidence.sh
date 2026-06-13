#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo "usage: $0 <packet-path-evidence-dir> <package-output-root>" >&2
  exit 64
fi
EVIDENCE_DIR=$1
OUTPUT_ROOT=$2
if [[ -L "$EVIDENCE_DIR" || -L "$OUTPUT_ROOT" ]]; then
  echo "symlink paths are forbidden" >&2
  exit 65
fi
if [[ ! -d "$EVIDENCE_DIR" ]]; then
  echo "packet-path evidence dir must exist" >&2
  exit 66
fi
mkdir -p "$OUTPUT_ROOT"
if [[ -L "$OUTPUT_ROOT" ]]; then
  echo "package output root symlink forbidden" >&2
  exit 65
fi
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
PACKAGE_DIR="$OUTPUT_ROOT/verified-controlled-artifact-package-evidence-$STAMP"
mkdir "$PACKAGE_DIR"
BINDING_JSON="$PACKAGE_DIR/binding-cli.json"
PACKAGE_JSON="$PACKAGE_DIR/package-cli.json"
VERIFY_JSON="$PACKAGE_DIR/verify-cli.json"
mpf production verified-filter-hook-binding-plan --packet-path-evidence-dir "$EVIDENCE_DIR" --output json > "$BINDING_JSON"
mpf production controlled-artifact-reapply-package-plan --packet-path-evidence-dir "$EVIDENCE_DIR" --output-dir "$PACKAGE_DIR/package" --output json > "$PACKAGE_JSON"
mpf production controlled-artifact-reapply-package-verify --package-dir "$PACKAGE_DIR/package" --output json > "$VERIFY_JSON"
python - "$BINDING_JSON" "$PACKAGE_JSON" "$VERIFY_JSON" <<'PY'
import json, sys
b=json.load(open(sys.argv[1])); p=json.load(open(sys.argv[2])); v=json.load(open(sys.argv[3]))
print(f"binding_final_decision={b.get('final_decision')}")
print(f"package_final_decision={p.get('final_decision')}")
print(f"verify_final_decision={v.get('final_decision')}")
print(f"package_dir={p.get('package_dir')}")
print(f"manifest_sha256={p.get('manifest_sha256')}")
print(f"package_sha256={p.get('package_sha256')}")
PY
