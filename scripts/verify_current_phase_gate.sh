#!/usr/bin/env bash
set -Eeuo pipefail

# Resolve repository root from this script location so absolute-path invocation
# works from any caller CWD (for example: /root during post-sync checks).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"


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
grep -q 'current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not show accepted Phase 11 gate'
grep -q 'current_working_phase: Phase 12 — Worker Policy Enforcement' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not show Phase 12 as current working phase'
grep -q 'production_traffic: controlled_cli_limited' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep production_traffic=controlled_cli_limited'
grep -q 'firewall_apply_allowed: controlled' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep firewall apply controlled'
grep -q 'abuse_automation_allowed: controlled' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep abuse automation controlled'
grep -q 'customer_onboarding_allowed: controlled_cli_limited' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep customer_onboarding_allowed=controlled_cli_limited'
grep -q 'proxy_data_plane_allowed: limited_runtime_local_only' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep proxy_data_plane_allowed=limited_runtime_local_only'
grep -q 'worker_enforcement_allowed: no' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md enables worker enforcement before Phase 12 acceptance'
grep -q 'ui_allowed: no' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep ui_allowed=no'
grep -q 'telegram_allowed: no' docs/PHASE_STATUS.md || fail 'docs/PHASE_STATUS.md does not keep telegram_allowed=no'

section 'CLI PHASE STATUS + SAFE COMMANDS'
command -v mpf >/dev/null 2>&1 || fail 'mpf command not found'
phase_status_output="$(mpf phase-status)"
printf '%s\n' "$phase_status_output"
[[ "$phase_status_output" == *'current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5'* ]] || fail 'mpf phase-status is not aligned with accepted Phase 11 gate'
[[ "$phase_status_output" == *'current_working_phase: Phase 12 — Worker Policy Enforcement'* ]] || fail 'mpf phase-status is not aligned with Phase 12 working phase'
[[ "$phase_status_output" == *'production_traffic: controlled_cli_limited'* ]] || fail 'mpf phase-status does not keep production_traffic=controlled_cli_limited'
[[ "$phase_status_output" == *'firewall_apply_allowed: controlled'* ]] || fail 'mpf phase-status does not keep firewall apply controlled'
[[ "$phase_status_output" == *'abuse_automation_allowed: controlled'* ]] || fail 'mpf phase-status does not keep abuse automation controlled'
[[ "$phase_status_output" == *'customer_onboarding_allowed: controlled_cli_limited'* ]] || fail 'mpf phase-status does not keep customer onboarding controlled CLI-limited'
[[ "$phase_status_output" == *'proxy_data_plane_allowed: limited_runtime_local_only'* ]] || fail 'mpf phase-status does not keep proxy_data_plane_allowed=limited_runtime_local_only'
[[ "$phase_status_output" == *'worker_enforcement_allowed: no'* ]] || fail 'mpf phase-status enables worker enforcement before Phase 12 acceptance'
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
IPTABLES_SAVE_FILE="$(mktemp)"
IP6TABLES_SAVE_FILE="$(mktemp)"
trap 'rm -f "$IPTABLES_SAVE_FILE" "$IP6TABLES_SAVE_FILE"' EXIT

command -v iptables-save >/dev/null 2>&1 || fail 'iptables-save not found'
iptables-save > "$IPTABLES_SAVE_FILE"
if command -v ip6tables-save >/dev/null 2>&1; then
  ip6tables-save > "$IP6TABLES_SAVE_FILE"
else
  : > "$IP6TABLES_SAVE_FILE"
fi

VERSION_FILE="${REPO_ROOT}/VERSION"
[ -f "$VERSION_FILE" ] || fail "VERSION file missing at ${VERSION_FILE}"
EXPECTED_VERSION="$(tr -d "[:space:]" < "$VERSION_FILE")"
[ -n "$EXPECTED_VERSION" ] || fail "VERSION file is empty at ${VERSION_FILE}"
gate_json="$(mpf production current-controlled-artifact-gate --expected-version "$EXPECTED_VERSION" --iptables-save-file "$IPTABLES_SAVE_FILE" --ip6tables-save-file "$IP6TABLES_SAVE_FILE" --output json)"
printf '%s
' "$gate_json"
gate_decision="$(printf '%s' "$gate_json" | python -c 'import json,sys;print(json.load(sys.stdin).get("final_decision",""))')"
unknown_count="$(printf '%s' "$gate_json" | python -c 'import json,sys;print(len(json.load(sys.stdin).get("unknown_mpf_artifacts",[])))')"
echo "artifact_gate_final_decision: $gate_decision"
echo "artifact_gate_unknown_mpf_artifacts: $unknown_count"
if [[ "$gate_decision" == BLOCKED_* ]]; then
  fail "controlled artifact gate blocked: $gate_decision"
fi
if [[ "$gate_decision" == "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS" ]]; then
  echo 'OK_WITH_CONTROLLED_PHASE11_ARTIFACTS: known controlled canary/limited artifacts are present and require review before runtime evidence collection.'
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
  port_matches="$(ss -lntup 2>/dev/null | grep -E ":(${BTC_BACKEND_PORT}|${V2RAYA_HOST_PORT}|2014|20170|20171|20172|22070|22071|22072)\b" || true)"
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
echo 'OK: current Phase 11 accepted / Phase 12 working safety gate passed. Phase 11 remains controlled CLI-limited only; unrestricted production and worker enforcement remain disabled.'
