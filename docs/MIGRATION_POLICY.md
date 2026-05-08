# Migration Policy

Status: active database safety contract

This document defines how future PostgreSQL schema changes must be implemented after the initial Phase 2 bootstrap migration.

## Current Baseline

The accepted production baseline is:

```text
alembic_version = 0001_phase2_initial_schema
public schema table count = 64
```

The initial migration was accepted on `farm5` before production traffic existed.

## Future Migration Rule

Future production migrations must use explicit Alembic operations.

The initial bootstrap migration may remain as historical baseline, but new migrations must be explicit and reviewable. Do not use metadata-wide create or metadata-wide drop patterns in future production migrations.

## Required Before Any Server Migration

Before applying a new migration on `farm5`, create and record:

```text
source backup
PostgreSQL backup or restore point
/etc/mpf snapshot
alembic current output
alembic heads output
pytest output
migration review summary
rollback or restore strategy
```

## Required After Any Server Migration

After applying a migration, collect:

```bash
cd /opt/mpf-py-src
.venv/bin/alembic current
.venv/bin/alembic heads
.venv/bin/python -m pytest -q
mpf db status
mpf config validate
mpf doctor
```

Runtime safety checks must also confirm:

```text
firewall.apply_mode remains plan_only unless the accepted phase allows otherwise
no unexpected Docker runtime activation
no customer NAT redirects unless the accepted phase allows them
no abuse automation unless the accepted phase allows it
```

## Restore Strategy

A downgrade function is useful but not enough by itself.

A risky migration requires a restore strategy that includes:

```text
what data is changed
how to restore if verification fails
which backup artifact is used
which commands verify restore success
which runtime services must remain stopped or disabled during restore
```

## Schema Design Rules

Prefer additive changes:

```text
new nullable columns before required columns
new tables before rewiring existing tables
new indexes with clear query need
JSONB only for flexible metadata/evidence, not core relational identity
explicit status fields for lifecycle objects
created_at/updated_at where useful
```

Avoid breaking changes until the dependent services and tests are ready:

```text
renaming columns
changing primary keys
changing foreign key behavior
removing columns
changing status semantics represented as strings
rewiring buyer/customer/worker relationships
```

## AI Coding Agent Rule

An AI coding agent must not create a new migration unless the task explicitly requires a schema change.

For Phase 4 planning, prefer no schema migration unless a table is clearly needed and reviewed.

If a schema migration is required, the patch must include:

```text
SQLAlchemy model update
explicit Alembic migration
tests
restore strategy documentation
phase gate confirmation
server validation commands
```

## Final Rule

A migration is not accepted because it runs once.

It is accepted only when it is explicit, reviewed, tested, backed up, restorable, and compatible with the current phase gate.
