#!/usr/bin/env bash
set -Eeuo pipefail

# Phase 1 read-only preflight.
# This script must not install packages, change firewall rules, create NAT redirects,
# start proxy data-plane services, or enable automation.

section() {
  printf '\n===== %s =====\n' "$1"
}

run_optional() {
  "$@" 2>/dev/null || true
}

section 'BASIC'
date -Is
hostname
run_optional cat /etc/os-release
run_optional uname -a
run_optional timedatectl
run_optional uptime

section 'NETWORK'
run_optional ip -br addr
printf '\n'
run_optional ip route
printf '\n'
run_optional cat /etc/resolv.conf

section 'FIREWALL STACK'
run_optional iptables --version
run_optional ip6tables --version
run_optional update-alternatives --display iptables
run_optional nft --version
run_optional ufw status verbose

section 'TOOLS'
for tool in python3 pip3 git curl wget jq docker conntrack tcpdump ipset sqlite3 psql ss; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf 'OK   %s -> %s\n' "$tool" "$(command -v "$tool")"
    "$tool" --version 2>/dev/null | head -n 1 || true
  else
    printf 'MISS %s\n' "$tool"
  fi
done

section 'DOCKER'
run_optional systemctl is-active docker
run_optional docker version
run_optional docker compose version

section 'POSTGRESQL'
run_optional systemctl is-active postgresql
run_optional psql --version

section 'CAPACITY'
run_optional df -h /
printf '\n'
run_optional free -h
printf '\n'
run_optional swapon --show

section 'APT / REACHABILITY'
run_optional apt-cache policy docker.io docker-ce docker-compose-plugin postgresql python3 python3-venv
printf '\n'
run_optional getent hosts github.com
run_optional getent hosts download.docker.com
run_optional getent hosts archive.ubuntu.com
printf '\n'
timeout 8 bash -lc 'curl -I -4 -sS https://github.com >/dev/null && echo OK_github || echo FAIL_github' || true
timeout 8 bash -lc 'curl -I -4 -sS https://download.docker.com >/dev/null && echo OK_docker || echo FAIL_docker' || true
timeout 8 bash -lc 'curl -I -4 -sS https://archive.ubuntu.com >/dev/null && echo OK_archive || echo FAIL_archive' || true

section 'PHASE 1 SAFETY CHECKS'
echo 'Expected during Phase 1:'
echo '- no customer firewall rules'
echo '- no NAT redirects'
echo '- no backend public exposure'
echo '- no abuse automation'
echo '- no block automation'
echo '- firewall.apply_mode remains plan_only'

echo 'Preflight complete. Send the full output for review before running bootstrap commands.'
