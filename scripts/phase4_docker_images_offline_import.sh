#!/usr/bin/env bash
set -Eeuo pipefail

IMAGE_ARCHIVE="${1:-/tmp/mpf-phase4-runtime-images.tar}"
APP_DIR="/opt/mpf-py-src"
COMPOSE_FILE="$APP_DIR/compose/mpf-proxy.compose.yaml"
PROJECT_NAME="mpf-proxy"
COMPOSE_CONFIG_OUT="/tmp/mpf-phase4-offline-images-compose-config.out"
REQUIRED_IMAGES=(
  "mzz2017/v2raya:latest"
  "gogost/gost:latest"
)

section() {
  printf '\n===== %s =====\n' "$1"
}

fail() {
  echo "CRITICAL: $*"
  exit 1
}

require_root() {
  [ "$(id -u)" -eq 0 ] || fail "run as root"
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

assert_no_runtime_is_running() {
  section "RUNTIME STOPPED CHECK"
  docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" --profile phase4-runtime ps -a || true
  local running
  running="$(docker ps --filter "label=com.docker.compose.project=${PROJECT_NAME}" --format '{{.Names}}' || true)"
  if [ -n "$running" ]; then
    echo "$running"
    fail "proxy runtime containers are running; stop them before image import"
  fi
  echo "OK: no proxy runtime containers are running"
}

validate_compose_images() {
  section "COMPOSE IMAGE CONTRACT"
  [ -f "$COMPOSE_FILE" ] || fail "compose file missing: $COMPOSE_FILE"
  docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" --profile phase4-runtime config >"$COMPOSE_CONFIG_OUT"
  for image in "${REQUIRED_IMAGES[@]}"; do
    grep -q "image: ${image}" "$COMPOSE_CONFIG_OUT" || fail "compose config does not reference required image: ${image}"
    echo "OK: compose references ${image}"
  done
}

show_existing_images() {
  section "EXISTING IMAGES"
  docker image ls mzz2017/v2raya || true
  docker image ls gogost/gost || true
}

load_archive() {
  section "LOAD OFFLINE IMAGE ARCHIVE"
  [ -f "$IMAGE_ARCHIVE" ] || fail "image archive not found: $IMAGE_ARCHIVE"
  docker load -i "$IMAGE_ARCHIVE"
}

verify_images() {
  section "VERIFY REQUIRED IMAGES"
  local image
  for image in "${REQUIRED_IMAGES[@]}"; do
    docker image inspect "$image" >/dev/null 2>&1 || fail "required image is still missing after load: $image"
    docker image inspect --format 'OK: {{.RepoTags}} id={{.Id}} created={{.Created}}' "$image"
  done
}

final_checks() {
  section "FINAL IMAGE IMPORT VERDICT"
  echo "OK: required Phase 4 runtime Docker images are available locally."
  echo "OK: server can now retry the guarded runtime startup with --pull never."
  echo "Next command: sudo bash /opt/mpf-py-src/scripts/phase4_runtime_activation_execute.sh start"
}

require_root
require_command docker
cd "$APP_DIR"
assert_no_runtime_is_running
validate_compose_images
show_existing_images
load_archive
verify_images
final_checks
