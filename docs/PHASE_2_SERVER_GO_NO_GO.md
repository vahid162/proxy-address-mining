# Phase 2 Server Go / No-Go Checklist

Status: operational checklist

Use this before aligning `farm5` with the Phase 2 repository schema.

## Go Conditions

All must be true before running any Phase 2 server migration:

```text
[ ] Latest GitHub CI is green.
[ ] docs/PHASE_2_SCHEMA_REVIEW.md has been read.
[ ] docs/PHASE_2_SERVER_ALIGNMENT_RUNBOOK.md has been read.
[ ] Server precheck output has been reviewed.
[ ] PostgreSQL is active.
[ ] Docker has no MPF/proxy containers.
[ ] No MPF firewall rules exist.
[ ] firewall.apply_mode is plan_only.
[ ] /etc/mpf has been backed up.
[ ] PostgreSQL mpf database has been dumped.
[ ] iptables-save snapshot has been saved.
[ ] pytest passes from the transferred repository source.
[ ] alembic heads/history work.
[ ] Migration execution has explicit operator approval.
```

## No-Go Conditions

Stop if any are true:

```text
[ ] GitHub CI is red.
[ ] Server time or date is clearly wrong.
[ ] PostgreSQL is not active.
[ ] DB ping fails.
[ ] Unexpected Docker containers exist.
[ ] MPF firewall rules already exist.
[ ] firewall.apply_mode is not plan_only.
[ ] Backup/dump fails.
[ ] pytest fails on server.
[ ] alembic cannot find the migration head.
[ ] Unknown production data exists in the public schema.
[ ] Operator is unsure which command will mutate state.
```

## Commands That Mutate State

These require explicit approval:

```bash
alembic upgrade head
alembic downgrade
createdb / dropdb
systemctl start/stop/enable/disable for production services
docker compose up
iptables-restore
mpf customer ...
mpf firewall apply ...
mpf abuse ...
```

## Commands That Are Read-only / Low-risk

These are allowed before approval:

```bash
mpf phase-status
mpf config validate
mpf doctor
mpf db ping
python -m pytest
alembic heads
alembic history
psql SELECT queries
docker ps -a
iptables-save | grep ...
ss -lntup
timedatectl
```

## Current Recommendation

Do not run `alembic upgrade head` until the repository artifact has been copied to the server, precheck output has been reviewed, and backup artifacts have been created successfully.
