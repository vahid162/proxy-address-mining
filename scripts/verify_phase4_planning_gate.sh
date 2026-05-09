#!/usr/bin/env bash
set -Eeuo pipefail

section() {
  printf '\n===== %s =====\n' "$1"
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
  docs/PHASE_4_SERVER_RUNBOOK.md
  docs/PHASE_4_1_SERVER_RESULT.md
  docs/PHASE_4_2_SERVER_SYNC_RESULT.md
  docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md
  docs/PHASE_4_RUNTIME_ACTIVATION_EXECUTION_REVIEW.md
  docs/OFFLINE_SYNC_RUNBOOK.md
  scripts/apply_phase4_1_config_planning.sh
  scripts/sync_main_zip_on_server.sh
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
    echo "CRITICAL: missing $file"
    exit 1
  fi
  echo "OK: $file"
done

section 'PHASE STATUS CONTENT'
if ! grep -q 'current_accepted_phase: Phase 4.2' docs/PHASE_STATUS.md; then
  echo 'CRITICAL: docs/PHASE_STATUS.md does not show Phase 4.2 as accepted'
  exit 1
fi
if ! grep -q 'current_working_phase: Phase 4 Runtime Activation Execution Review' docs/PHASE_STATUS.md; then
  echo 'CRITICAL: docs/PHASE_STATUS.md does not show Phase 4 runtime activation execution review as current working phase'
  exit 1
fi
if ! grep -q 'runtime activation still not authorized' docs/PHASE_STATUS.md; then
  echo 'CRITICAL: docs/PHASE_STATUS.md does not keep runtime activation unauthorized'
  exit 1
fi
if ! grep -q 'proxy_data_plane_allowed: planning_only' docs/PHASE_STATUS.md; then
  echo 'CRITICAL: docs/PHASE_STATUS.md does not keep proxy_data_plane_allowed as planning_only'
  exit 1
fi
if ! grep -q 'proxy.runtime_activation_allowed = false' docs/PHASE_STATUS.md; then
  echo 'CRITICAL: docs/PHASE_STATUS.md does not preserve proxy.runtime_activation_allowed=false'
  exit 1
fi
echo 'OK: phase status is runtime activation review only'

section 'README CONTENT'
if ! grep -q 'accepted_phase: Phase 4.2' README.md; then
  echo 'CRITICAL: README.md does not show Phase 4.2 as accepted'
  exit 1
fi
if ! grep -q 'working_phase: Phase 4 Runtime Activation Execution Review' README.md; then
  echo 'CRITICAL: README.md does not show runtime activation execution review as current working phase'
  exit 1
fi
if ! grep -q 'runtime activation still not authorized' README.md; then
  echo 'CRITICAL: README.md does not keep runtime activation unauthorized'
  exit 1
fi
if ! grep -q 'proxy_data_plane_allowed: planning_only' README.md; then
  echo 'CRITICAL: README.md does not show proxy data-plane as planning_only'
  exit 1
fi
if ! grep -q 'proxy.runtime_activation_allowed = false' README.md; then
  echo 'CRITICAL: README.md does not preserve proxy.runtime_activation_allowed=false'
  exit 1
fi
echo 'OK: README phase summary is aligned'

section 'PHASE 4 REVIEW DOC CONTENT'
for needle in \
  'does not authorize runtime activation by itself' \
  'docker compose up' \
  'Do not run during this review step' \
  'customer NAT redirects' \
  'firewall.apply_mode' \
  'proxy.runtime_activation_allowed' \
  'internal_backend_reachable = OK' \
  'external_backend_exposed = NO' \
  'stop/rollback'; do
  if ! grep -qi "$needle" docs/AI_PHASE_4_2_TASK.md docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md docs/PHASE_4_RUNTIME_ACTIVATION_EXECUTION_REVIEW.md; then
    echo "CRITICAL: missing Phase 4 review safety phrase: $needle"
    exit 1
  fi
done
echo 'OK: Phase 4 review safety phrases are present'

section 'CLI PHASE STATUS'
if command -v mpf >/dev/null 2>&1; then
  mpf phase-status
  if ! mpf phase-status | grep -q 'current_accepted_phase: Phase 4.2'; then
    echo 'CRITICAL: mpf phase-status is not aligned with Phase 4.2 accepted'
    exit 1
  fi
  if ! mpf phase-status | grep -q 'current_working_phase: Phase 4 Runtime Activation Execution Review'; then
    echo 'CRITICAL: mpf phase-status is not aligned with runtime activation execution review'
    exit 1
  fi
  if ! mpf phase-status | grep -q 'runtime activation still not authorized'; then
    echo 'CRITICAL: mpf phase-status does not keep runtime activation unauthorized'
    exit 1
  fi
else
  echo 'WARN: mpf command not found; skipping runtime CLI check'
fi

section 'CONFIG SAFETY'
if [ -f /etc/mpf/mpf.yaml ]; then
  grep -n 'apply_mode\|runtime_activation_allowed' /etc/mpf/mpf.yaml || true
  if ! grep -q 'apply_mode: plan_only' /etc/mpf/mpf.yaml; then
    echo 'CRITICAL: /etc/mpf/mpf.yaml is not in plan_only mode'
    exit 1
  fi
  if ! grep -q 'runtime_activation_allowed: false' /etc/mpf/mpf.yaml; then
    echo 'CRITICAL: /etc/mpf/mpf.yaml does not keep proxy runtime activation disabled'
    exit 1
  fi
  echo 'OK: /etc/mpf/mpf.yaml remains plan_only with runtime disabled'
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

section 'FIREWALL SAFETY'
if command -v iptables-save >/dev/null 2>&1; then
  if iptables-save | grep -Eiq 'MPF|MPFBTC|MPFC_|MPFO_|60010'; then
    echo 'CRITICAL: MPF or backend references found in iptables-save during review gate'
    iptables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
    exit 1
  fi
  echo 'OK: no MPF/backend IPv4 firewall references detected'
else
  echo 'WARN: iptables-save not found; skipping IPv4 firewall inspection'
fi

if command -v ip6tables-save >/dev/null 2>&1; then
  if ip6tables-save | grep -Eiq 'MPF|MPFBTC|MPFC_|MPFO_|60010'; then
    echo 'CRITICAL: MPF or backend references found in ip6tables-save during review gate'
    ip6tables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
    exit 1
  fi
  echo 'OK: no MPF/backend IPv6 firewall references detected'
else
  echo 'WARN: ip6tables-save not found; skipping IPv6 firewall inspection'
fi

section 'LISTENING PORT SAFETY'
if command -v ss >/dev/null 2>&1; then
  port_matches="$(ss -lntup 2>/dev/null | grep -E ':(60010|2014|20170|20171|20172|22070|22071|22072)\b' || true)"
  if [ -n "$port_matches" ]; then
    echo "$port_matches"
    echo 'CRITICAL: risky backend/UI port is listening during review gate'
    exit 1
  fi
  echo 'OK: no risky backend/UI ports listening'
else
  echo 'WARN: ss not found; skipping listening port inspection'
fi

section 'PHASE 4 RUNTIME ACTIVATION REVIEW GATE VERDICT'
echo 'OK: Phase 4 runtime activation execution review gate passed. Runtime activation is still not authorized.'
