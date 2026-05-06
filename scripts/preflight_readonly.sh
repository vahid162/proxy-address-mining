#!/usr/bin/env bash
set -Eeuo pipefail

# Phase 1 read-only preflight.
# This script must not install packages, create users, create directories, start services,
# change firewall rules, create NAT redirects, or activate production traffic.

section() {
  printf '\n===== %s =====\n' "$1"
}

run_readonly() {
  local label="$1"
  shift
  printf '\n--- %s ---\n' "$label"
  "$@" 2>&1 || true
}

section 'BASIC'
run_readonly 'date' date -Is
run_readonly 'hostname' hostname
run_readonly 'os-release' cat /etc/os-release
run_readonly 'kernel' uname -a
run_readonly 'timedatectl' timedatectl
run_readonly 'uptime' uptime

section 'NETWORK'
run_readonly 'interfaces' ip -br addr
run_readonly 'routes' ip route
run_readonly 'dns' cat /etc/resolv.conf
run_readonly 'listeners' ss -lntup

section 'FIREWALL STACK'
run_readonly 'iptables version' iptables --version
run_readonly 'ip6tables version' ip6tables --version
run_readonly 'iptables alternatives' update-alternatives --display iptables
run_readonly 'nft version' nft --version
run_readonly 'ufw status' ufw status verbose
run_readonly 'firewalld status' firewall-cmd --state

section 'TOOLS'
for tool in python3 pip3 git curl wget jq docker conntrack tcpdump ipset sqlite3 psql ss iptables ip6tables nft; do
  if command -v "$tool" >/dev/null 2>&1; then
    echo "OK   $tool -> $(command -v "$tool")"
    "$tool" --version 2>/dev/null | head -n 1 || true
  else
    echo "MISS $tool"
  fi
done

section 'DOCKER'
run_readonly 'docker service active' systemctl is-active docker
run_readonly 'docker version' docker version
run_readonly 'docker compose version' docker compose version

section 'POSTGRESQL'
run_readonly 'postgresql service active' systemctl is-active postgresql
run_readonly 'psql version' psql --version

section 'CAPACITY'
run_readonly 'root disk' df -h /
run_readonly 'memory' free -h
run_readonly 'swap' swapon --show

section 'APT / REACHABILITY'
run_readonly 'apt policy' apt-cache policy docker.io docker-ce docker-compose-plugin postgresql python3 python3-venv
run_readonly 'github dns' getent hosts github.com
run_readonly 'docker dns' getent hosts download.docker.com
run_readonly 'ubuntu archive dns' getent hosts archive.ubuntu.com
run_readonly 'github https' timeout 8 bash -lc 'curl -I -4 -sS https://github.com >/dev/null && echo OK_github || echo FAIL_github'
run_readonly 'docker https' timeout 8 bash -lc 'curl -I -4 -sS https://download.docker.com >/dev/null && echo OK_docker || echo FAIL_docker'
run_readonly 'ubuntu archive https' timeout 8 bash -lc 'curl -I -4 -sS https://archive.ubuntu.com >/dev/null && echo OK_archive || echo FAIL_archive'

section 'PHASE 1 SAFETY SUMMARY'
echo 'script_mode: read_only'
echo 'package_installation: not_performed'
echo 'firewall_mutation: not_performed'
echo 'nat_redirect: not_performed'
echo 'service_activation: not_performed'
echo 'customer_onboarding: not_performed'
echo 'abuse_automation: not_performed'
