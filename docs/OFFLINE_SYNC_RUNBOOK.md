# Offline Sync Runbook

Status: active server alignment runbook

`farm5` does not have reliable GitHub or internet access. Repository changes must be synced by uploading a GitHub main ZIP archive from an operator machine and then running the local sync script on the server.

This runbook is the required path for aligning `/opt/mpf-py-src` with GitHub `main` while preserving the server virtual environment.

## Source of Truth

GitHub `main` is the repository source of truth.

The server source path is:

```text
/opt/mpf-py-src
```

The server runtime command is:

```text
/usr/local/bin/mpf
```

The sync process must preserve:

```text
/opt/mpf-py-src/.venv
/etc/mpf/mpf.yaml
/var/backups/mpf
```

## Operator Machine Step

Download the latest GitHub `main` ZIP archive on a machine that can access GitHub.

Then upload it to the server:

```bash
scp proxy-address-mining-main.zip root@85.198.11.110:/tmp/proxy-address-mining-main.zip
```

If the sync script itself changed, also upload the script or copy it from the synced repository after extraction.

## Server Sync Step

Do not run `/opt/mpf-py-src/scripts/sync_main_zip_on_server.sh` directly for future ZIP syncs.
Use the bootstrap wrapper so the sync script is executed from inside the extracted ZIP source:

```bash
sudo bash /opt/mpf-py-src/scripts/mpf_sync_main_zip_bootstrap.sh /tmp/proxy-address-mining-main.zip
```

Optional one-time install:

```bash
sudo install -m 0755 /opt/mpf-py-src/scripts/mpf_sync_main_zip_bootstrap.sh /usr/local/sbin/mpf-sync-main-zip
sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
```

If `/opt/mpf-py-src` is not yet aligned enough to contain the script, paste the script from GitHub or upload it to `/tmp` and run:

```bash
sudo bash /tmp/sync_main_zip_on_server.sh /tmp/proxy-address-mining-main.zip
```

## What The Sync Script Must Do

The script must:

```text
verify the ZIP exists
verify /opt/mpf-py-src exists
verify /opt/mpf-py-src/.venv exists
create a timestamped backup under /var/backups/mpf
extract the ZIP to a temporary directory
validate required repository files
replace source files while preserving .venv
install/update /usr/local/bin/mpf wrapper
run pytest through the preserved venv
run safe MPF smoke commands
run the current phase safety gate script (`scripts/verify_current_phase_gate.sh`)
```

The script must not:

```text
install packages from the internet
run git pull
start Docker containers
run docker compose up
change firewall rules
create NAT redirects
create or mutate customers
start usage timers
start abuse automation
start UI or Telegram
```

## Required Post-Sync Evidence

After sync, collect and send back:

```bash
cd /opt/mpf-py-src
/opt/mpf-py-src/.venv/bin/python -m pytest -q
mpf phase-status
mpf config validate
mpf doctor
mpf db ping
mpf db status
mpf lanes list
mpf customer list
mpf jobs status
bash scripts/verify_current_phase_gate.sh
```


`verify_phase4_planning_gate.sh` remains in-repo for historical Phase 4/5 verification only and is no longer the active sync gate.

For Phase 4 planning hardening, also run:

```bash
mpf proxy config-check
mpf proxy status
mpf proxy doctor
```

## Rollback

Every sync creates a backup under:

```text
/var/backups/mpf/source-before-zip-sync-<timestamp>
```

Rollback must be manual and reviewed. Do not overwrite the current source from backup unless the failed sync output has been reviewed.

## Final Rule

A server is considered aligned only when:

```text
GitHub main ZIP was synced
pytest passed
mpf phase-status matches docs/PHASE_STATUS.md
safe smoke checks passed
current phase gate passed
runtime activation remains unauthorized unless a later accepted runtime task explicitly allows it
```
