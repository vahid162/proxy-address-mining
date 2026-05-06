# AI Phase 1 Task Contract

Status: active task contract for AI coding agents

This file defines the safe task boundary for the next implementation agent.
Read it together with:

1. `AGENTS.md`
2. `README.md`
3. `docs/INDEX.md`
4. `docs/PHASE_STATUS.md`
5. `docs/PHASE_1.md`
6. `docs/SAFETY.md`

## Current Allowed Scope

Only Phase 1 repository bootstrap and preflight preparation are allowed.

Allowed work:

```text
- maintain minimal Python package skeleton
- maintain safe CLI smoke commands
- maintain config loader and validator
- maintain read-only DB ping helper
- maintain read-only preflight script
- maintain example config with firewall.apply_mode=plan_only
- maintain smoke tests
- improve documentation without relaxing safety gates
```

Forbidden work:

```text
- customer CRUD
- production PostgreSQL migrations
- live firewall planner/apply
- NAT redirects
- Docker proxy data-plane activation
- v2rayA activation
- forwarder activation
- usage timers
- abuse runner automation
- block or pause automation
- local UI service
- Telegram bot
- production customer import
- any command that changes traffic
```

## Required Safety Invariant

During this phase:

```text
firewall.apply_mode = plan_only
```

No code path may change production traffic state.

## Implementation Standard

Keep interfaces thin.

Required architecture direction:

```text
CLI / API / jobs
  -> service layer
  -> repositories / adapters
  -> events/audit later when mutations exist
```

During Phase 1 the CLI may call simple config and DB helpers, but it must not grow business logic for customer, firewall, usage, or abuse decisions.

## Required Commands

The repository should support these Phase 1 smoke commands after installation:

```bash
mpf --help
mpf --version
mpf phase-status
mpf doctor --config configs/mpf.example.yaml
mpf config validate --config configs/mpf.example.yaml
mpf config show --config configs/mpf.example.yaml
mpf db ping --config /etc/mpf/mpf.yaml
python -m pytest
```

`mpf db ping` may fail before PostgreSQL exists. That is acceptable during local development, but after server bootstrap it must pass.

## Preflight Rule

Use:

```bash
sudo bash scripts/preflight.sh
```

or copy the file contents to the target server.

The preflight script must remain read-only. It must not install, enable, start, stop, or mutate anything.

## Acceptance Gate

Phase 1 is accepted only when the target server output confirms:

```text
- OS/kernel/timezone known
- network interfaces/routes/DNS known
- iptables/nft/legacy state known
- Docker availability known
- PostgreSQL availability known
- Python/venv/pip availability known
- conntrack/tcpdump/ipset availability known
- disk/RAM/swap capacity known
- repository/intranet package reachability known
```

And these checks pass on the target server after bootstrap:

```bash
mpf --help
mpf doctor
mpf config validate
mpf config show
mpf db ping
python -m pytest
systemctl status postgresql
docker version
docker compose version
conntrack -V
iptables --version
```

Also confirm:

```text
no customer firewall rule exists
no NAT redirect exists
no backend public exposure exists
no abuse automation is active
no block automation is active
firewall.apply_mode is still plan_only
```

## Patch Review Checklist

Before submitting a patch, verify:

```text
[ ] Phase gates were not relaxed.
[ ] No live traffic mutation was added.
[ ] No firewall apply command was added.
[ ] No NAT redirect command was added.
[ ] No abuse automation was added.
[ ] Config validation still rejects non-plan_only apply mode in Phase 1.
[ ] PostgreSQL remains the only production source of truth.
[ ] BTC lane still uses backend port 60010.
[ ] Tests cover changed config/CLI/preflight behavior.
[ ] No secrets were committed.
```

## Next Human Step

Run the preflight on the target server and paste the full output for review before any bootstrap commands are written or executed.
