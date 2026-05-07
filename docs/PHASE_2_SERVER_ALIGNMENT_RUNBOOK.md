# Phase 2 Server Alignment Runbook

Status: draft runbook

This runbook describes how to align `farm5` with the GitHub repository after Phase 2 schema work, without rushing into production migration.

## Current Server State

Known accepted server state:

```text
server: farm5
accepted phase: Phase 1
PostgreSQL: active
Docker: active, no containers
MPF firewall rules: none
firewall.apply_mode: plan_only
production traffic: none
```

Known warning:

```text
time synchronization is not confirmed
```

Time sync must be fixed before production traffic, usage accuracy, or abuse automation.

## Goal

Align server files and validate Phase 2 schema safely.

This runbook is intentionally split into gates:

```text
Gate A — repository artifact transfer only
Gate B — read-only server precheck
Gate C — backup/snapshot before migration
Gate D — install/update Python package dependencies if needed
Gate E — run tests and Alembic inspection only
Gate F — migration execution, only after explicit approval
Gate G — post-migration verification
```

## Hard Rules

Do not run these until the correct gate:

```text
alembic upgrade head
alembic downgrade
customer CRUD
firewall apply
NAT redirect
Docker proxy containers
abuse runner
production import
UI service
Telegram service
```

`firewall.apply_mode` must remain:

```text
plan_only
```

## PostgreSQL Peer-auth Rule

The target server uses a local `mpf` PostgreSQL role with peer authentication.

Therefore, Alembic commands that connect to `postgresql+psycopg:///mpf` must be executed as the system user `mpf`, not as root.

Recommended pattern from root:

```bash
sudo -u mpf env PYTHONPATH=/opt/mpf-py-src /opt/mpf-py-src/.venv/bin/alembic -c /opt/mpf-py-src/alembic.ini <command>
```

Running Alembic directly as root can fail or connect as the wrong database role.

## Gate A — Transfer Repository Artifact

Because the server may not have reliable GitHub access, use an approved transfer method:

```text
repository tar/zip from GitHub
internal Git mirror
SCP/SFTP
internal share
```

Recommended target path:

```text
/opt/mpf-py-src
```

Do not overwrite the current Phase 1 `/opt/mpf-py` until prechecks pass.

Suggested layout:

```text
/opt/mpf-py        # current Phase 1 runtime skeleton
/opt/mpf-py-src    # repository source artifact for Phase 2 review
```

## Gate B — Read-only Server Precheck

Run this before any migration:

```bash
sudo bash <<'BASH'
set -Eeuo pipefail

echo '===== PHASE 2 SERVER ALIGNMENT PRECHECK ====='
date -Is
hostname

echo '===== SERVICES ====='
systemctl is-active postgresql || true
systemctl is-active docker || true
systemctl is-active containerd || true

echo '===== CURRENT MPF ====='
command -v mpf || true
mpf --version || true
mpf phase-status || true
mpf config validate || true
mpf doctor || true
mpf db ping || true

echo '===== CONFIG SAFETY ====='
grep -nE 'apply_mode|backend_port|threshold_sec|grace_sec' /etc/mpf/mpf.yaml || true

echo '===== DATABASE CURRENT STATE ====='
sudo -u mpf psql -d mpf -tAc "select current_database(), current_user;" || true
sudo -u mpf psql -d mpf -tAc "select tablename from pg_tables where schemaname='public' order by tablename;" || true

echo '===== DOCKER MUST HAVE NO CONTAINERS ====='
docker ps -a || true

echo '===== FIREWALL MUST HAVE NO MPF RULES ====='
iptables-save | grep -E 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true

echo '===== TIME SYNC WARNING CHECK ====='
timedatectl || true

BASH
```

Expected before migration:

```text
PostgreSQL active
Docker active
mpf db ping OK
firewall.apply_mode=plan_only
no Docker containers
no MPF firewall rules
public schema either empty or only expected bootstrap metadata
```

If unexpected production tables or MPF firewall rules exist, stop.

## Gate C — Backup/Snapshot Before Migration

Before running any Alembic upgrade, create a backup directory:

```bash
sudo bash <<'BASH'
set -Eeuo pipefail
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/var/backups/mpf/phase2-align-${STAMP}"
install -d -m 0750 -o mpf -g mpf "$BACKUP_DIR"

echo "backup_dir=$BACKUP_DIR"

sudo -u mpf pg_dump -d mpf --format=custom --file="$BACKUP_DIR/mpf-before-phase2.dump"
cp -a /etc/mpf "$BACKUP_DIR/etc-mpf"
iptables-save > "$BACKUP_DIR/iptables-save.before"
ss -lntup > "$BACKUP_DIR/ss-lntup.before" || true
docker ps -a > "$BACKUP_DIR/docker-ps-a.before" || true
timedatectl > "$BACKUP_DIR/timedatectl.before" || true

sha256sum "$BACKUP_DIR"/* 2>/dev/null | tee "$BACKUP_DIR/SHA256SUMS" || true

echo "Created backup: $BACKUP_DIR"
BASH
```

Do not continue if backup creation fails.

## Gate D — Prepare Repository Environment

From the transferred repository directory, create a venv and install the repository there.

Recommended:

```bash
cd /opt/mpf-py-src
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -e '.[dev]'
```

If the server has no PyPI access, do not improvise. Prepare an offline wheelhouse in a later documented step.

Do not remove the existing `/usr/local/bin/mpf` symlink during this gate.

## Gate E — Tests and Alembic Inspection Only

Allowed commands:

```bash
cd /opt/mpf-py-src
.venv/bin/python -m pytest
.venv/bin/alembic heads
.venv/bin/alembic history
sudo -u mpf env PYTHONPATH=/opt/mpf-py-src /opt/mpf-py-src/.venv/bin/alembic -c /opt/mpf-py-src/alembic.ini current
```

Expected:

```text
pytest passed
alembic sees 0001_phase2_initial_schema as head
alembic current connects as database user mpf and shows no current revision before migration
```

Still forbidden in Gate E:

```text
alembic upgrade head
```

## Gate F — Migration Execution Only After Explicit Approval

Only after Gate A-E pass and the operator confirms, run:

```bash
sudo -u mpf env PYTHONPATH=/opt/mpf-py-src /opt/mpf-py-src/.venv/bin/alembic -c /opt/mpf-py-src/alembic.ini upgrade head
```

This creates schema tables in the local `mpf` PostgreSQL database.

Important current migration caveat:

```text
The initial migration currently uses Base.metadata.create_all().
This is acceptable for controlled Phase 2 validation on an empty/new DB,
but it is not a mature production migration style.
```

Do not run downgrade casually, because the current downgrade drops modeled tables.

## Gate G — Post-migration Verification

After migration:

```bash
sudo bash <<'BASH'
set -Eeuo pipefail

echo '===== ALEMBIC VERSION ====='
sudo -u mpf psql -d mpf -x -c 'select * from alembic_version;'

echo '===== TABLE COUNT ====='
sudo -u mpf psql -d mpf -tAc "select count(*) from pg_tables where schemaname='public';"

echo '===== KEY TABLES ====='
sudo -u mpf psql -d mpf -tAc "select tablename from pg_tables where schemaname='public' and tablename in ('lanes','customers','customer_policies','abuse_states','firewall_applies','restore_points','job_runs','scheduler_locks','buyer_accounts','worker_blocks','feature_flags','server_profiles','import_batches') order by tablename;"

echo '===== NO TRAFFIC STATE ====='
docker ps -a || true
iptables-save | grep -E 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
ss -lntup || true

echo '===== CONFIG SAFETY ====='
grep -nE 'apply_mode|backend_port|threshold_sec|grace_sec' /etc/mpf/mpf.yaml

BASH
```

Expected:

```text
alembic_version = 0001_phase2_initial_schema
expected key tables exist
no Docker containers
no MPF firewall rules
firewall.apply_mode remains plan_only
no proxy/backend data-plane was started
```

## Rollback / Restore Path

Preferred rollback for Phase 2 validation failure:

```text
restore DB from pg_dump taken in Gate C
restore /etc/mpf snapshot if changed
verify no firewall/docker side effects
```

Do not rely on `alembic downgrade` as the primary rollback path for this first migration because the current downgrade drops modeled tables.

Example DB restore command, only if needed and after explicit decision:

```bash
sudo -u mpf dropdb mpf
sudo -u postgres createdb -O mpf mpf
sudo -u mpf pg_restore -d mpf /path/to/mpf-before-phase2.dump
```

## Phase Status Update

Do not update `docs/PHASE_STATUS.md` to Phase 2 accepted until:

```text
migration ran successfully on server
post-migration verification passed
backup path is recorded
no traffic side effects exist
```

## Operator Reminder

After any patch, script, migration, or major operational change, collect the command output and review it before moving to the next gate.
