#!/usr/bin/env bash
set -Eeuo pipefail

section() {
  printf '\n===== %s =====\n' "$1"
}

section 'BASIC'
date -Is
hostname

section 'OFFICIAL MPF RUNTIME'
command -v mpf || true
ls -l /usr/local/bin/mpf 2>/dev/null || true
mpf --version
mpf phase-status

section 'PHASE 3 READ-ONLY COMMANDS'
mpf config validate
mpf config show
mpf doctor
mpf db ping
mpf db status
mpf lanes list
mpf customer list
mpf jobs status

section 'SOURCE TESTS'
cd /opt/mpf-py-src
if [ ! -x .venv/bin/python ]; then
  echo 'CRITICAL: /opt/mpf-py-src/.venv/bin/python is missing or not executable'
  exit 1
fi
.venv/bin/python -m pytest -q
sudo -u mpf .venv/bin/alembic current
sudo -u mpf .venv/bin/alembic heads

section 'CONFIG SAFETY'
grep -R "apply_mode" /etc/mpf /opt/mpf-py-src/configs 2>/dev/null || true
if ! grep -q "apply_mode: plan_only" /etc/mpf/mpf.yaml; then
  echo 'CRITICAL: /etc/mpf/mpf.yaml is not in plan_only mode'
  exit 1
fi

section 'DATABASE RUNTIME TABLES'
sudo -u mpf psql -d mpf -F $'\t' -P pager=off -c "
select 'lanes' as table_name, count(*) from lanes
union all select 'customers', count(*) from customers
union all select 'customer_policies', count(*) from customer_policies
union all select 'abuse_states', count(*) from abuse_states
union all select 'firewall_applies', count(*) from firewall_applies
union all select 'job_runs', count(*) from job_runs
union all select 'worker_blocks', count(*) from worker_blocks
union all select 'buyer_accounts', count(*) from buyer_accounts
order by table_name;
"

section 'DOCKER SAFETY'
docker ps -a
if [ "$(docker ps -aq | wc -l)" -ne 0 ]; then
  echo 'CRITICAL: Docker containers exist before Phase 4 runtime activation'
  exit 1
fi

section 'FIREWALL SAFETY'
if iptables-save | grep -Eiq 'MPF|MPFBTC|MPFC_|MPFO_|60010'; then
  echo 'CRITICAL: MPF or backend references found in iptables-save'
  iptables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
  exit 1
fi
if ip6tables-save | grep -Eiq 'MPF|MPFBTC|MPFC_|MPFO_|60010'; then
  echo 'CRITICAL: MPF or backend references found in ip6tables-save'
  ip6tables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
  exit 1
fi
echo 'OK: no MPF firewall/NAT rules detected'

section 'SYSTEMD AND CRON SAFETY'
unit_matches="$(systemctl list-unit-files --no-pager --plain 2>/dev/null | awk '{print $1}' | grep -E '^(mpf|v2raya|gost|forwarder)[@._-].*\.(service|timer|socket)$|^(mpf|v2raya|gost|forwarder)\.(service|timer|socket)$' || true)"
if [ -n "$unit_matches" ]; then
  echo "$unit_matches"
  echo 'CRITICAL: MPF/proxy unit files exist before allowed phase'
  exit 1
fi
active_matches="$(systemctl --type=service --type=timer --type=socket --state=active --no-pager --plain 2>/dev/null | awk '{print $1}' | grep -E '^(mpf|v2raya|gost|forwarder)[@._-].*\.(service|timer|socket)$|^(mpf|v2raya|gost|forwarder)\.(service|timer|socket)$' || true)"
if [ -n "$active_matches" ]; then
  echo "$active_matches"
  echo 'CRITICAL: MPF/proxy active units exist before allowed phase'
  exit 1
fi
cron_matches="$(grep -RInE '(^|[^A-Za-z0-9_-])(mpf|v2raya|gost|forwarder)([^A-Za-z0-9_-]|$)' /etc/cron* /var/spool/cron/crontabs 2>/dev/null || true)"
if [ -n "$cron_matches" ]; then
  echo "$cron_matches"
  echo 'CRITICAL: MPF/proxy cron references exist before allowed phase'
  exit 1
fi
echo 'OK: no MPF systemd/cron automation detected'

section 'LISTENING PORT SAFETY'
port_matches="$(ss -lntup 2>/dev/null | grep -E ':(60010|2014|20170|20171|20172|22070|22071|22072)\b' || true)"
if [ -n "$port_matches" ]; then
  echo "$port_matches"
  echo 'CRITICAL: risky backend/UI port is listening before Phase 4 runtime activation'
  exit 1
fi
echo 'OK: no risky backend/UI ports listening'

section 'TIME SYNC STATUS'
timedatectl || true
if timedatectl 2>/dev/null | grep -q 'System clock synchronized: yes'; then
  echo 'OK: system clock synchronized'
else
  echo 'WARN: system clock is not synchronized. This blocks production traffic, usage, abuse, and time-series collection.'
fi

section 'PHASE 3.1 VERDICT'
echo 'OK: Phase 3.1 runtime alignment and safety checks passed, except any WARN items above.'
