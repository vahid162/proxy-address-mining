# Intranet Install Guide

Status: Phase 1 operational guide

This project may be deployed to servers that do not have direct GitHub or internet access. The target server may only have access to internal package mirrors or a controlled intranet.

## Principle

Do not assume the target server can run:

```bash
git clone
pip install from the public internet
docker pull from public registries
```

The safe process is:

```text
1. Prepare repository artifacts on a workstation that has GitHub access.
2. Copy approved artifacts to the intranet server.
3. Run read-only preflight on the server.
4. Review the preflight output.
5. Run a phase-specific bootstrap script only after review.
6. Run smoke verification.
```

## Phase 1 Intranet Path

For Phase 1, the server needs only:

```text
Ubuntu package access through an approved mirror
repository files copied manually or by approved internal transfer
no GitHub access required on the server
no Docker image pulls required
no Python package downloads from PyPI required
```

The Phase 1 bootstrap uses Ubuntu packages only:

```text
python3
python3-venv
python3-pip
python3-yaml
python3-pytest
postgresql
postgresql-client
docker.io
docker-compose-v2
conntrack
tcpdump
ipset
sqlite3
iptables
nftables
iproute2
```

## Required First Step: Preflight

Before any bootstrap command, run the read-only preflight:

```bash
sudo bash scripts/preflight.sh
```

If the repository is not available on the server, copy the contents of `scripts/preflight.sh` and run it manually.

Preflight must confirm:

```text
OS and version
network and DNS state
APT mirror availability
firewall backend
Docker availability
PostgreSQL availability
Python availability
required tools
capacity
reachability constraints
```

## Phase 1 Bootstrap

After preflight review, use:

```bash
sudo bash scripts/bootstrap_phase1_ubuntu2404.sh
```

This script is intentionally scoped to Phase 1.

Allowed:

```text
install base packages
create mpf system user
create standard directories
create local PostgreSQL role/database
write /etc/mpf/mpf.yaml with apply_mode=plan_only
install minimal safe mpf smoke CLI
enable Docker service without containers
run smoke tests
```

Forbidden:

```text
customer firewall rules
NAT redirects
backend exposure
proxy data-plane containers
v2rayA activation
forwarder activation
usage timers
abuse runner automation
block/pause automation
UI service
Telegram bot
production customer import
```

## Artifact Transfer Options

Use one of these controlled approaches:

```text
- download repository ZIP/TAR on a workstation and copy it to the server
- use an internal Git mirror, if available
- use an approved SCP/SFTP transfer
- use a mounted internal share
```

Do not paste or transfer secrets through GitHub.

## Secrets

Secrets must stay outside the repository:

```text
/etc/mpf/secrets.env
/etc/mpf/secrets.d/
```

Recommended permissions:

```text
secret file mode: 0600
secret directory mode: 0750
```

Forbidden in Git:

```text
Telegram tokens
private proxy subscription URLs
pool credentials
production customer secrets
database passwords, if any are introduced later
```

## NTP / Time Sync

Production phases require reliable time.

For intranet servers, public NTP may not work. Before production traffic or abuse automation, configure one of:

```text
internal NTP server
provider-approved NTP endpoint
explicit firewall allowance for UDP/123
```

Do not activate the abuse runner while system time is unsynchronized.

## Verification After Bootstrap

Expected checks:

```bash
mpf --version
mpf phase-status
mpf config validate
mpf doctor
mpf db ping
cd /opt/mpf-py && python -m pytest
systemctl is-active postgresql
systemctl is-active docker
docker ps -a
iptables-save | grep -E 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
```

Expected result:

```text
mpf config validate OK
mpf db ping OK
pytest passed
Docker has no containers
No MPF firewall rules exist
firewall.apply_mode remains plan_only
```

## Transition to Phase 2

Phase 2 may start only after Phase 1 is accepted.

Phase 2 is repository implementation work for:

```text
PostgreSQL schema
Alembic migrations
config/domain models
lane model
customer model
policy model
abuse state representation
event/audit representation
job_runs and scheduler_locks
restore_points and firewall_snapshots
```

Phase 2 still must not apply firewall rules or start production traffic.
