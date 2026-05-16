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

section 'PHASE STATUS CONTENT'
[ -f docs/PHASE_STATUS.md ] || fail 'docs/PHASE_STATUS.md is missing'
grep -q 'current_accepted_phase: Phase 8 — Abuse 1h Core accepted on farm5' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not show accepted Phase 7 gate'
grep -q 'current_working_phase: Phase 9 — Check / Report / Diagnostics planning/readiness' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not show Phase 8 planning/readiness as current working phase'
grep -q 'production_traffic: none' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep production_traffic=none'
grep -q 'firewall_apply_allowed: no' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep firewall apply disabled'
grep -q 'abuse_automation_allowed: no' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep abuse automation disabled'
grep -q 'customer_onboarding_allowed: db_only' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep customer_onboarding_allowed=db_only'
grep -q 'proxy_data_plane_allowed: limited_runtime_local_only' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep proxy_data_plane_allowed=limited_runtime_local_only'
grep -q 'ui_allowed: no' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep ui_allowed=no'
grep -q 'telegram_allowed: no' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep telegram_allowed=no'

section 'CLI PHASE STATUS + SAFE COMMANDS'
command -v mpf >/dev/null 2>&1 || fail 'mpf command not found'
phase_status_output="$(mpf phase-status)"
printf '%s\n' "$phase_status_output"
[[ "$phase_status_output" == *'current_accepted_phase: Phase 8 — Abuse 1h Core accepted on farm5'* ]] || fail 'mpf phase-status is not aligned with accepted Phase 7 gate'
[[ "$phase_status_output" == *'current_working_phase: Phase 9 — Check / Report / Diagnostics planning/readiness'* ]] || fail 'mpf phase-status is not aligned with Phase 8 planning/readiness'
[[ "$phase_status_output" == *'production_traffic: none'* ]] || fail 'mpf phase-status does not keep production_traffic=none'
[[ "$phase_status_output" == *'firewall_apply_allowed: no'* ]] || fail 'mpf phase-status does not keep firewall apply disabled'
[[ "$phase_status_output" == *'abuse_automation_allowed: no'* ]] || fail 'mpf phase-status does not keep abuse automation disabled'
[[ "$phase_status_output" == *'customer_onboarding_allowed: db_only'* ]] || fail 'mpf phase-status does not keep customer onboarding DB-only'
[[ "$phase_status_output" == *'proxy_data_plane_allowed: limited_runtime_local_only'* ]] || fail 'mpf phase-status does not keep proxy_data_plane_allowed=limited_runtime_local_only'
[[ "$phase_status_output" == *'ui_allowed: no'* ]] || fail 'mpf phase-status does not keep UI disabled'
[[ "$phase_status_output" == *'telegram_allowed: no'* ]] || fail 'mpf phase-status does not keep Telegram disabled'
mpf config validate
mpf doctor
mpf db status
mpf proxy doctor

section 'CONFIG SAFETY'
if [ -f /etc/mpf/mpf.yaml ]; then
  grep -q 'apply_mode: plan_only' /etc/mpf/mpf.yaml || fail '/etc/mpf/mpf.yaml is not in plan_only mode'
  grep -q 'runtime_activation_allowed: false' /etc/mpf/mpf.yaml || fail '/etc/mpf/mpf.yaml does not keep runtime activation disabled'
  echo 'OK: /etc/mpf/mpf.yaml remains plan_only with runtime activation disabled'
else
  echo 'WARN: /etc/mpf/mpf.yaml not found; skipping server config check'
fi

section 'MPF CUSTOMER FIREWALL SAFETY'
if command -v iptables-save >/dev/null 2>&1; then
  if iptables-save | grep -Eiq 'MPF|MPFBTC|MPFC_|MPFO_'; then
    echo 'CRITICAL: MPF/customer references found in iptables-save during current gate verification'
    iptables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_' || true
    exit 1
  fi
  echo 'OK: no MPF/customer IPv4 firewall references detected'
fi

if command -v ip6tables-save >/dev/null 2>&1; then
  if ip6tables-save | grep -Eiq 'MPF|MPFBTC|MPFC_|MPFO_'; then
    echo 'CRITICAL: MPF/customer references found in ip6tables-save during current gate verification'
    ip6tables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_' || true
    exit 1
  fi
  echo 'OK: no MPF/customer IPv6 firewall references detected'
fi

section 'DOCKER LOCAL PUBLISH NAT REFERENCES'
if runtime_running && command -v iptables-save >/dev/null 2>&1; then
  iptables-save | grep -Ei "${BTC_BACKEND_PORT}|${V2RAYA_HOST_PORT}" | grep -Ei '(-j DNAT|--to-destination)' || true
  echo 'OK: Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational in accepted limited runtime.'
  echo 'OK: MPF/customer NAT redirect paths remain forbidden by MPF/customer reference checks and local-only listener checks.'
else
  echo 'WARN: Docker local publish NAT reference inspection skipped'
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
fi

section 'CURRENT GATE VERDICT'
echo 'OK: current Phase 8 accepted / Phase 9 planning safety gate passed. Production customer traffic remains disabled.'
