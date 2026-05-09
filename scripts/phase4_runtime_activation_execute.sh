#!/usr/bin/env bash
set -Eeuo pipefail

ACTION="${1:-status}"
APP_DIR="/opt/mpf-py-src"
COMPOSE_FILE="$APP_DIR/compose/mpf-proxy.compose.yaml"
PROJECT_NAME="mpf-proxy"
BACKUP_BASE="/var/backups/mpf"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="${BACKUP_BASE}/phase4-runtime-activation-${STAMP}"
COMPOSE_CONFIG_OUT="/tmp/mpf-phase4-runtime-compose-config.out"
COMPOSE=(docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" --profile phase4-runtime)

section() {
  printf '\n===== %s =====\n' "$1"
}

fail() {
  echo "CRITICAL: $*"
  exit 1
}

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    fail "run as root"
  fi
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

show_phase_and_config() {
  section "PHASE / CONFIG"
  mpf phase-status
  mpf config validate
  mpf config show
  mpf doctor
}

show_database_readonly() {
  section "DATABASE READONLY"
  mpf db ping
  mpf db status
  mpf lanes list
  mpf customer list
  mpf jobs status
}

assert_phase_gate() {
  section "PHASE GATE"
  mpf phase-status | grep -q 'current_accepted_phase: Phase 4.2' || fail "Phase 4.2 is not the accepted phase"
  mpf phase-status | grep -q 'current_working_phase: Phase 4 Runtime Activation Execution Review' || fail "runtime activation execution review is not the working phase"
  mpf phase-status | grep -q 'runtime activation still not authorized' || fail "phase status does not show guarded runtime state"
  grep -q 'current_accepted_phase: Phase 4.2' "$APP_DIR/docs/PHASE_STATUS.md" || fail "PHASE_STATUS is not Phase 4.2 accepted"
  grep -q 'Phase 4 Runtime Activation Execution Review' "$APP_DIR/docs/PHASE_STATUS.md" || fail "PHASE_STATUS is not in runtime activation execution review"
  grep -q 'Runtime Activation Execution Task' "$APP_DIR/docs/PHASE_4_RUNTIME_ACTIVATION_EXECUTION_TASK.md" || fail "runtime activation execution task doc missing or invalid"
  echo "OK: phase gate allows this limited operator-controlled runtime execution script"
}

assert_config_safety() {
  section "CONFIG SAFETY"
  mpf config validate
  mpf config show | grep -q 'firewall.apply_mode: plan_only' || fail "firewall.apply_mode is not plan_only"
  mpf config show | grep -q 'proxy.runtime_activation_allowed: False' || fail "proxy.runtime_activation_allowed is not false"
  echo "OK: config remains plan_only with general runtime activation disabled"
}

assert_no_customers_or_jobs() {
  section "DB EMPTY RUNTIME TABLE SAFETY"
  local status
  status="$(mpf db status)"
  echo "$status"
  echo "$status" | grep -q 'customers: 0' || fail "customers table is not empty"
  echo "$status" | grep -q 'job_runs: 0' || fail "job_runs table is not empty"
  echo "$status" | grep -q 'firewall_applies: 0' || fail "firewall_applies table is not empty"
  echo "$status" | grep -q 'abuse_states: 0' || fail "abuse_states table is not empty"
  echo "OK: no customers/jobs/firewall applies/abuse states exist"
}

assert_compose_source_local_publish() {
  local port="$1"
  local label="$2"
  if ! grep -Eq "['\"]127\.0\.0\.1:${port}:${port}['\"]" "$COMPOSE_FILE"; then
    fail "$label is not local-only in compose source: expected 127.0.0.1:${port}:${port}"
  fi
}

assert_compose_rendered_port() {
  local port="$1"
  local label="$2"
  if grep -Eq "127\.0\.0\.1:${port}:${port}" "$COMPOSE_CONFIG_OUT"; then
    return 0
  fi
  if grep -q 'host_ip: 127.0.0.1' "$COMPOSE_CONFIG_OUT" \
    && grep -Eq "published: ['\"]?${port}['\"]?" "$COMPOSE_CONFIG_OUT" \
    && grep -Eq "target: ${port}" "$COMPOSE_CONFIG_OUT"; then
    return 0
  fi
  echo "----- docker compose config output -----"
  cat "$COMPOSE_CONFIG_OUT"
  echo "----- end docker compose config output -----"
  fail "$label is not local-only in rendered compose config"
}

assert_compose_template_safety() {
  section "COMPOSE TEMPLATE SAFETY"
  [ -f "$COMPOSE_FILE" ] || fail "compose file missing: $COMPOSE_FILE"
  "${COMPOSE[@]}" config >"$COMPOSE_CONFIG_OUT"
  assert_compose_source_local_publish 2014 "v2rayA UI"
  assert_compose_source_local_publish 60010 "BTC backend"
  assert_compose_rendered_port 2014 "v2rayA UI"
  assert_compose_rendered_port 60010 "BTC backend"
  grep -q 'mpf-forwarder-btc' "$COMPOSE_CONFIG_OUT" || fail "BTC forwarder service missing in compose config"
  grep -q 'mpf-v2raya' "$COMPOSE_CONFIG_OUT" || fail "v2rayA service missing in compose config"
  if grep -Eq '0\.0\.0\.0:(2014|60010)|host_ip: 0\.0\.0\.0|\[::\]:(2014|60010)|host_ip: ::' "$COMPOSE_CONFIG_OUT"; then
    cat "$COMPOSE_CONFIG_OUT"
    fail "compose config contains public backend/UI binding"
  fi
  echo "OK: compose template validates and publishes only local-only ports"
}

assert_no_mpf_firewall_refs() {
  section "FIREWALL SAFETY"
  local v4="" v6=""
  v4="$(iptables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010|2014' || true)"
  v6="$(ip6tables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010|2014' || true)"
  if [ -n "$v4" ]; then
    echo "$v4"
    fail "MPF/backend IPv4 firewall references exist"
  fi
  if [ -n "$v6" ]; then
    echo "$v6"
    fail "MPF/backend IPv6 firewall references exist"
  fi
  echo "OK: no MPF/backend firewall references detected"
}

assert_no_risky_ports_before_start() {
  section "PRE-RUNTIME PORT SAFETY"
  local matches=""
  matches="$(ss -lntup 2>/dev/null | grep -E ':(60010|2014|20170|20171|20172|22070|22071|22072)\b' || true)"
  if [ -n "$matches" ]; then
    echo "$matches"
    fail "risky backend/UI port is already listening before runtime startup"
  fi
  echo "OK: no risky backend/UI ports are listening before startup"
}

backup_state() {
  section "BACKUP STATE"
  mkdir -p "$BACKUP_DIR"
  tar -C /opt --exclude='mpf-py-src/.venv' -czf "$BACKUP_DIR/mpf-py-src-no-venv.tgz" mpf-py-src
  cp -a /etc/mpf/mpf.yaml "$BACKUP_DIR/mpf.yaml"
  iptables-save > "$BACKUP_DIR/iptables-save.v4"
  ip6tables-save > "$BACKUP_DIR/ip6tables-save.v6"
  docker ps -a > "$BACKUP_DIR/docker-ps-a.txt" || true
  ss -lntup > "$BACKUP_DIR/ss-lntup.txt" || true
  echo "BACKUP_DIR=$BACKUP_DIR"
}

show_docker_state() {
  section "DOCKER STATE"
  docker ps -a || true
  "${COMPOSE[@]}" ps -a || true
}

assert_post_start_ports() {
  section "POST-START PORT SAFETY"
  local listen=""
  listen="$(ss -lntup 2>/dev/null | grep -E ':(60010|2014)\b' || true)"
  echo "$listen"
  echo "$listen" | grep -q '127.0.0.1:2014' || fail "v2rayA UI is not listening on 127.0.0.1:2014"
  echo "$listen" | grep -q '127.0.0.1:60010' || fail "BTC backend is not listening on 127.0.0.1:60010"
  if echo "$listen" | grep -Eq '0\.0\.0\.0:(2014|60010)|\[::\]:(2014|60010)|:::2014|:::60010'; then
    fail "backend/UI is publicly bound"
  fi
  echo "OK: backend/UI ports are local-only"
}

assert_backend_reachable() {
  section "BACKEND INTERNAL REACHABILITY"
  nc -zv 127.0.0.1 60010
  echo "OK: BTC backend is internally reachable on 127.0.0.1:60010"
}

run_proxy_doctor() {
  section "PROXY DOCTOR"
  mpf proxy config-check
  mpf proxy status || true
  mpf proxy doctor || true
}

start_runtime() {
  require_root
  require_command docker
  require_command ss
  require_command nc
  require_command iptables-save
  require_command ip6tables-save
  cd "$APP_DIR"
  show_phase_and_config
  show_database_readonly
  assert_phase_gate
  assert_config_safety
  assert_no_customers_or_jobs
  assert_compose_template_safety
  assert_no_mpf_firewall_refs
  assert_no_risky_ports_before_start
  backup_state
  section "START LIMITED PHASE 4 RUNTIME"
  echo "Running Docker Compose with --pull never to avoid internet dependency."
  "${COMPOSE[@]}" up -d --pull never
  show_docker_state
  assert_post_start_ports
  assert_backend_reachable
  assert_no_mpf_firewall_refs
  run_proxy_doctor
  section "FINAL VERDICT"
  echo "OK: limited Phase 4 proxy runtime started."
  echo "OK: v2rayA UI is local-only."
  echo "OK: BTC backend 60010 is local-only and internally reachable."
  echo "OK: no customer NAT redirects or customer firewall rules were created."
  echo "OK: firewall.apply_mode remains plan_only."
  echo "OK: proxy.runtime_activation_allowed remains false for general app/API runtime mutation."
  echo "Backup: $BACKUP_DIR"
}

status_runtime() {
  require_root
  cd "$APP_DIR"
  show_phase_and_config
  show_database_readonly
  show_docker_state
  section "PORTS"
  ss -lntup | grep -E ':(60010|2014|20170|20171|20172|22070|22071|22072)\b' || true
  assert_no_mpf_firewall_refs
  run_proxy_doctor
}

stop_runtime() {
  require_root
  require_command docker
  cd "$APP_DIR"
  section "STOP LIMITED PHASE 4 RUNTIME"
  "${COMPOSE[@]}" down
  show_docker_state
  section "POST-STOP PORTS"
  local matches=""
  matches="$(ss -lntup 2>/dev/null | grep -E ':(60010|2014|20170|20171|20172|22070|22071|22072)\b' || true)"
  if [ -n "$matches" ]; then
    echo "$matches"
    fail "risky backend/UI ports still listening after stop"
  fi
  assert_no_mpf_firewall_refs
  run_proxy_doctor
  section "FINAL VERDICT"
  echo "OK: limited Phase 4 proxy runtime stopped."
}

case "$ACTION" in
  start)
    start_runtime
    ;;
  status)
    status_runtime
    ;;
  stop|rollback)
    stop_runtime
    ;;
  *)
    echo "Usage: $0 {start|status|stop|rollback}"
    exit 2
    ;;
esac
