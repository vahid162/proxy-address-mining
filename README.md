# Proxy Address Mining

`proxy-address-mining` is a Python-first, API-first, PostgreSQL-backed control plane for a mining customer gateway.

It replaces a legacy shell-script operational setup with a clean, testable service-layer architecture. The project preserves required operational capability, but it must not become a direct migration, patch series, or extension of the old scripts.

## Start Here

- **GPT/Codex and other coding agents:** read [`AGENTS.md`](AGENTS.md) first.
- **Project documentation:** start at [`docs/INDEX.md`](docs/INDEX.md).
- **Current phase, gate, and next required step:** read [`docs/PHASE_STATUS.md`](docs/PHASE_STATUS.md). This is the only authoritative dynamic project-state document.
- **Runtime safety:** read [`docs/SAFETY.md`](docs/SAFETY.md) before proposing or performing runtime-affecting work.

## Scope and Design

The initial control plane is designed around:

- Python-first, API-first service architecture
- PostgreSQL as the production source of truth
- lane-based customer and policy modeling
- planner-driven firewall plan, apply, verify, and rollback contracts
- fail-closed, operator-gated runtime operations
- future local UI, Telegram, worker intelligence, and observability interfaces that use the same service layer

The current product roadmap and non-goals are documented in [`docs/ROADMAP.md`](docs/ROADMAP.md). The architecture contract is in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Development

Install the package with development dependencies:

```bash
python -m pip install -e '.[dev]'
```

Run the test suite:

```bash
python -m pytest -q
```

For pull-request body validation:

```bash
python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md
```

## Documentation

| Topic | Document |
|---|---|
| Current state and gates | [`docs/PHASE_STATUS.md`](docs/PHASE_STATUS.md) |
| Documentation map | [`docs/INDEX.md`](docs/INDEX.md) |
| Architecture | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Runtime safety | [`docs/SAFETY.md`](docs/SAFETY.md) |
| Data model | [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) |
| Firewall | [`docs/FIREWALL.md`](docs/FIREWALL.md) |
| Abuse lifecycle | [`docs/ABUSE.md`](docs/ABUSE.md) |
| Customer lifecycle | [`docs/CUSTOMER_LIFECYCLE.md`](docs/CUSTOMER_LIFECYCLE.md) |
| Control rules | [`docs/CONTROL_RULES.md`](docs/CONTROL_RULES.md) |
| Backend-port policy | [`docs/BACKEND_PORT_POLICY.md`](docs/BACKEND_PORT_POLICY.md) |
| Artifact taxonomy | [`docs/TAXONOMY.md`](docs/TAXONOMY.md) |

## Version History

The current version is maintained in [`VERSION`](VERSION). Release history belongs in [`CHANGELOG.md`](CHANGELOG.md); operational evidence and historical phase documents do not define the current gate.
