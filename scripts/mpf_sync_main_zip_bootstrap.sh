#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "ERROR: must run as root" >&2
  exit 1
fi

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /path/to/proxy-address-mining-main.zip" >&2
  exit 1
fi

ZIP="$1"
if [[ ! -f "$ZIP" ]]; then
  echo "ERROR: ZIP not found: $ZIP" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d /tmp/mpf-sync-main-zip.XXXXXX)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

unzip -q "$ZIP" -d "$TMP_DIR"

NEW_SRC="$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1 || true)"
if [[ -z "$NEW_SRC" || ! -d "$NEW_SRC" ]]; then
  echo "ERROR: extracted source directory not found in ZIP" >&2
  exit 1
fi

if [[ ! -f "$NEW_SRC/scripts/sync_main_zip_on_server.sh" ]]; then
  echo "ERROR: extracted source missing scripts/sync_main_zip_on_server.sh" >&2
  exit 1
fi

bash "$NEW_SRC/scripts/sync_main_zip_on_server.sh" "$ZIP"
