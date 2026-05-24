# Phase 11E single customer staging

Purpose: controlled DB-only staging for limited-btc-001 after 0.1.199 execution-gate evidence.

Allowed modes: `plan`, `execute-db-only`.

Safety boundary: DB-only staging at most; no firewall apply, NAT apply, production traffic, live customer traffic, abuse automation, UI, Telegram, scheduler, worker enforcement.

Candidate: limited-btc-001 / btc / 20101 / 172.18.0.3:60010

Rollback note: DB-created limited customer must be removable/markable through accepted customer lifecycle path later.
