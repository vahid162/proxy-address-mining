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
  docs/INDEX.md
  docs/PHASE_STATUS.md
  docs/AI_CODING_RULES.md
  docs/AI_PHASE_4_TASK.md
  docs/PHASE_4_SERVER_RUNBOOK.md
  docs/OFFLINE_SYNC_RUNBOOK.md
  scripts/sync_main_zip_on_server.sh
  mpf/domain/health.py
  mpf/services/proxy_doctor_service.py
  mpf/adapters/docker_compose.py
  mpf/adapters/socket_inspector.py
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
if ! grep -q 'current_accepted_phase: Phase 3.1' docs/PHASE_STATUS.md; then
  echo 'CRITICAL: docs/PHASE_STATUS.md does not show Phase 3.1 as accepted'
  exit 1
fi
if ! grep -q 'current_working_phase: Phase 4' docs/PHASE_STATUS.md; then
  echo 'CRITICAL: docs/PHASE_STATUS.md does not show Phase 4 as current working phase'
  exit 1
fi
if ! grep -q 'proxy_data_plane_allowed: planning_only' docs/PHASE_STATUS.md; then
  echo 'CRITICAL: docs/PHASE_STATUS.md does not keep proxy_data_plane_allowed as planning_only'
  exit 1
fi
echo 'OK: phase status is Phase 4 planning only'

section 'README CONTENT'
if ! grep -q 'accepted_phase: Phase 3.1' README.md; then
  echo 'CRITICAL: README.md does not show Phase 3.1 as accepted'
  exit 1
fi
if ! grep -q 'working_phase: Phase 4' README.md; then
  echo 'CRITICAL: README.md does not show Phase 4 as current working phase'
  exit 1
fi
if ! grep -q 'proxy_data_plane_allowed: planning_only' README.md; then
  echo 'CRITICAL: README.md does not show Phase 4 as planning_only'
  exit 1
fi
echo 'OK: README phase summary is aligned'

section 'PHASE 4 DOC CONTENT'
for needle in \
  'does not authorize server runtime activation' \
  'customer NAT redirects' \
  'firewall.apply_mode' \
  'internal_backend_reachable = OK' \
  'external_backend_exposed = NO' \
  'mpf proxy doctor'; do
  if ! grep -q "$needle" docs/AI_PHASE_4_TASK.md docs/PHASE_4_SERVER_RUNBOOK.md; then
    echo "CRITICAL: missing Phase 4 safety phrase: $needle"
    exit 1
  fi
done
echo 'OK: Phase 4 safety phrases are present'

section 'CLI PHASE STATUS'
if command -v mpf >/dev/null 2>&1; then
  mpf phase-status
  if ! mpf phase-status | grep -q 'current_accepted_phase: Phase 3.1'; then
    echo 'CRITICAL: mpf phase-status is not aligned with Phase 3.1 accepted'
    exit 1
  fi
  if ! mpf phase-status | grep -q 'current_working_phase: Phase 4'; then
    echo 'CRITICAL: mpf phase-status is not aligned with Phase 4 planning'
    exit 1
  fi
else
  echo 'WARN: mpf command not found; skipping runtime CLI check'
fi

section 'CONFIG SAFETY'
if [ -f /etc/mpf/mpf.yaml ]; then
  grep -n 'apply_mode' /etc/mpf/mpf.yaml || true
  if ! grep -q 'apply_mode: plan_only' /etc/mpf/mpf.yaml; then
    echo 'CRITICAL: /etc/mpf/mpf.yaml is not in plan_only mode'
    exit 1
  fi
  echo 'OK: /etc/mpf/mpf.yaml remains plan_only'
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
    echo 'CRITICAL: MPF or backend references found in iptables-save during planning gate'
    iptables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
    exit 1
  fi
  echo 'OK: no MPF/backend IPv4 firewall references detected'
else
  echo 'WARN: iptables-save not found; skipping IPv4 firewall inspection'
fi

if command -v ip6tables-save >/dev/null 2>&1; then
  if ip6tables-save | grep -Eiq 'MPF|MPFBTC|MPFC_|MPFO_|60010'; then
    echo 'CRITICAL: MPF or backend references found in ip6tables-save during planning gate'
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
    echo 'CRITICAL: risky backend/UI port is listening during planning gate'
    exit 1
  fi
  echo 'OK: no risky backend/UI ports listening'
else
  echo 'WARN: ss not found; skipping listening port inspection'
fi

section 'PHASE 4 PLANNING GATE VERDICT'
echo 'OK: Phase 4 planning gate passed. Runtime activation is still not authorized.'
