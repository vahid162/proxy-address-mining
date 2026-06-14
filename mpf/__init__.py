"""MPF Python control plane package.

Current repository state: Phase 11 — Production / Customer Activation Gate accepted on farm5; Phase 11 operational completion is the current working phase; Phase 12 — Worker Policy Enforcement remains blocked until operational completion acceptance.
The accepted production/customer boundary is controlled_cli_limited for the limited BTC scope only.
UI, Telegram, worker enforcement, unrestricted production expansion, and unrestricted miner expansion remain closed.
Importing this package performs no DB, firewall, conntrack, Docker, or systemd mutation.
"""

__version__ = "0.1.257"
