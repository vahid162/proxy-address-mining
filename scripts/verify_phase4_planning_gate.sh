#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_NAME="mpf-proxy"
V2RAYA_HOST_PORT="2015"
BTC_BACKEND_PORT="60010"

section() {
  printf '\n===== %s =====\n' "$1"
}

fail() {
  echo "CRITICAL: $*"
  exit 1
}

runtime_running() {
  command -v docker >/dev/null 2>&1 || return 1
  [ -n "$(docker ps --filter "label=com.docker.compose.project=${PROJECT_NAME}" --format '{{.Names}}' 2>/dev/null || true)" ]
}

section 'BASIC'
date -Is
hostname

section 'REQUIRED REPOSITORY FILES'
required_files=(
  AGENTS.md
  README.md
  compose/mpf-proxy.compose.yaml
  docs/INDEX.md
  docs/PHASE_STATUS.md
  docs/AI_CODING_RULES.md
  docs/AI_PHASE_4_TASK.md
  docs/AI_PHASE_4_2_TASK.md
  docs/AI_PHASE_5_TASK.md
  docs/PHASE_4_SERVER_RUNBOOK.md
  docs/PHASE_4_1_SERVER_RESULT.md
  docs/PHASE_4_2_SERVER_SYNC_RESULT.md
  docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md
  docs/PHASE_4_RUNTIME_ACTIVATION_EXECUTION_REVIEW.md
  docs/PHASE_4_RUNTIME_ACTIVATION_EXECUTION_TASK.md
  docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md
  docs/OFFLINE_SYNC_RUNBOOK.md
  scripts/apply_phase4_1_config_planning.sh
  scripts/sync_main_zip_on_server.sh
  scripts/phase4_runtime_activation_execute.sh
  mpf/domain/health.py
  mpf/services/proxy_doctor_service.py
  mpf/adapters/docker_compose.py
  mpf/adapters/socket_inspector.py
  tests/test_cli_phase_status.py
  tests/test_smoke.py
  tests/test_phase4_proxy.py
)
for file in "${required_files[@]}"; do
  if [ ! -f "$file" ]; then
    fail "missing $file"
  fi
  echo "OK: $file"
done

section 'PHASE STATUS CONTENT'
grep -q 'current_accepted_phase: Phase 4 Runtime Activation' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not show accepted Phase 4 runtime activation'
grep -q 'current_working_phase: Phase 5' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not show Phase 5 as current working phase'
grep -q 'proxy_data_plane_allowed: limited_runtime_local_only' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep proxy_data_plane_allowed as limited_runtime_local_only'
grep -q 'customer_onboarding_allowed: db_only_after_phase5_gate' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep customer onboarding DB-only'
grep -q 'firewall_apply_allowed: no' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep firewall apply disabled'
grep -q 'abuse_automation_allowed: no' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep abuse automation disabled'
grep -q 'proxy.runtime_activation_allowed = false' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not preserve proxy.runtime_activation_allowed=false'
echo 'OK: phase status is accepted Phase 4 runtime with Phase 5 DB-only work'

section 'README CONTENT'
grep -q 'accepted_phase: Phase 4 Runtime Activation' README.md || fail 'README.md does not show accepted Phase 4 runtime activation'
grep -q 'working_phase: Phase 5' README.md || fail 'README.md does not show Phase 5 as current working phase'
grep -q 'proxy_data_plane_allowed: limited_runtime_local_only' README.md || fail 'README.md does not show proxy data-plane as limited_runtime_local_only'
grep -q 'customer_onboarding_allowed: db_only_after_phase5_gate' README.md || fail 'README.md does not preserve Phase 5 DB-only customer boundary'
grep -q 'proxy.runtime_activation_allowed = false' README.md || fail 'README.md does not preserve proxy.runtime_activation_allowed=false'
echo 'OK: README phase summary is aligned'

section 'PHASE 4 RUNTIME RESULT CONTENT'
grep -q 'mpf-v2raya container started and healthy' docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md || fail 'Phase 4 runtime server result does not record healthy v2rayA'
grep -q 'mpf-forwarder-btc container started and healthy' docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md || fail 'Phase 4 runtime server result does not record healthy forwarder'
grep -q '127.0.0.1:2015' docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md || fail 'Phase 4 runtime server result does not record local-only v2rayA UI port'
grep -q '127.0.0.1:60010' docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md || fail 'Phase 4 runtime server result does not record local-only BTC backend port'
echo 'OK: Phase 4 runtime result evidence is present'

section 'PHASE 5 DOC CONTENT'
for needle in \
  'Customer CRUD in DB Only' \
  'customer CRUD remains DB-only' \
  'no firewall apply is introduced' \
  'no NAT redirect is introduced' \
  'firewall.apply_mode = plan_only' \
  'proxy.runtime_activation_allowed = false' \
  'reject reserved backend/UI ports' \
  'verify no firewall apply code path is called'; do
  if ! grep -qi "$needle" docs/AI_PHASE_5_TASK.md docs/PHASE_STATUS.md README.md; then
    fail "missing Phase 5 safety phrase: $needle"
  fi
done
echo 'OK: Phase 5 DB-only safety phrases are present'

section 'CLI PHASE STATUS'
if command -v mpf >/dev/null 2>&1; then
  mpf phase-status
  mpf phase-status | grep -q 'current_accepted_phase: Phase 4 Runtime Activation' || fail 'mpf phase-status is not aligned with accepted Phase 4 runtime'
  mpf phase-status | grep -q 'current_working_phase: Phase 5' || fail 'mpf phase-status is not aligned with Phase 5'
  mpf phase-status | grep -q 'proxy_data_plane_allowed: limited_runtime_local_only' || fail 'mpf phase-status does not show limited_runtime_local_only'
  mpf phase-status | grep -q 'customer_onboarding_allowed: db_only_after_phase5_gate' || fail 'mpf phase-status does not keep customer onboarding DB-only'
else
  echo 'WARN: mpf command not found; skipping runtime CLI check'
fi

section 'CONFIG SAFETY'
if [ -f /etc/mpf/mpf.yaml ]; then
  grep -n 'apply_mode\|runtime_activation_allowed' /etc/mpf/mpf.yaml || true
  grep -q 'apply_mode: plan_only' /etc/mpf/mpf.yaml || fail '/etc/mpf/mpf.yaml is not in plan_only mode'
  grep -q 'runtime_activation_allowed: false' /etc/mpf/mpf.yaml || fail '/etc/mpf/mpf.yaml does not keep proxy runtime activation disabled'
  echo 'OK: /etc/mpf/mpf.yaml remains plan_only with runtime disabled for general app/API mutation'
else
  echo 'WARN: /etc/mpf/mpf.yaml not found; skipping server config check'
fi

section 'PROXY CLI SAFETY'
if command -v mpf >/dev/null 2>&1; then
  mpf proxy config-check
  mpf proxy status
  mpf proxy doctor
else
  echo 'WARN: mpf command not found; skipping proxy CLI checks'
fi

section 'DOCKER SAFETY'
if command -v docker >/dev/null 2>&1; then
  docker ps -a || true
else
  echo 'WARN: docker not found; skipping Docker inspection'
fi

section 'MPF CUSTOMER FIREWALL SAFETY'
if command -v iptables-save >/dev/null 2>&1; then
  if iptables-save | grep -Eiq 'MPF|MPFBTC|MPFC_|MPFO_'; then
    echo 'CRITICAL: MPF/customer references found in iptables-save during Phase 5 gate'
    iptables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_' || true
    exit 1
  fi
  echo 'OK: no MPF/customer IPv4 firewall references detected'
else
  echo 'WARN: iptables-save not found; skipping IPv4 firewall inspection'
fi

if command -v ip6tables-save >/dev/null 2>&1; then
  if ip6tables-save | grep -Eiq 'MPF|MPFBTC|MPFC_|MPFO_'; then
    echo 'CRITICAL: MPF/customer references found in ip6tables-save during Phase 5 gate'
    ip6tables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_' || true
    exit 1
  fi
  echo 'OK: no MPF/customer IPv6 firewall references detected'
else
  echo 'WARN: ip6tables-save not found; skipping IPv6 firewall inspection'
fi

section 'LISTENING PORT SAFETY'
if command -v ss >/dev/null 2>&1; then
  port_matches="$(ss -lntup 2>/dev/null | grep -E ":(${BTC_BACKEND_PORT}|${V2RAYA_HOST_PORT}|2014|20170|20171|20172|22070|22071|22072)\\b" || true)"
  if [ -n "$port_matches" ]; then
    echo "$port_matches"
    if runtime_running; then
      echo "$port_matches" | grep -q "127.0.0.1:${V2RAYA_HOST_PORT}" || fail "v2rayA UI runtime listener is not local-only on 127.0.0.1:${V2RAYA_HOST_PORT}"
      echo "$port_matches" | grep -q "127.0.0.1:${BTC_BACKEND_PORT}" || fail "BTC backend runtime listener is not local-only on 127.0.0.1:${BTC_BACKEND_PORT}"
      if echo "$port_matches" | grep -Eq "0\.0\.0\.0:(${V2RAYA_HOST_PORT}|${BTC_BACKEND_PORT})|\[::\]:(${V2RAYA_HOST_PORT}|${BTC_BACKEND_PORT})|:::${V2RAYA_HOST_PORT}|:::${BTC_BACKEND_PORT}"; then
        fail 'runtime backend/UI listener is publicly bound'
      fi
      echo 'OK: accepted limited runtime listeners are local-only'
    else
      fail 'accepted limited runtime ports are listening without Compose runtime containers'
    fi
  else
    fail 'accepted limited runtime listeners are missing'
  fi
else
  echo 'WARN: ss not found; skipping listening port inspection'
fi

section 'DOCKER LOCAL PUBLISH FIREWALL REFERENCES'
if runtime_running && command -v iptables-save >/dev/null 2>&1; then
  iptables-save | grep -Ei "${BTC_BACKEND_PORT}|${V2RAYA_HOST_PORT}" || true
  echo 'OK: Docker-managed local publish rules are informational during accepted limited runtime.'
  echo 'OK: external exposure is enforced by listener binding checks.'
else
  echo 'WARN: limited runtime Docker publish inspection skipped'
fi

section 'PHASE 5 DB-ONLY GATE VERDICT'
echo 'OK: accepted Phase 4 runtime / Phase 5 DB-only gate passed. Production customer traffic remains disabled.'
