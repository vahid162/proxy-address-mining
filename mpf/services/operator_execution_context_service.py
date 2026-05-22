from __future__ import annotations

import getpass
import os
from dataclasses import dataclass, asdict

from mpf.config import MPFConfig


@dataclass(slots=True)
class OperatorExecutionContextReport:
    component: str = "operator_execution_context"
    mode: str = "read"
    os_user: str = ""
    effective_uid: int = 0
    database_url: str = ""
    database_url_is_local_peer: bool = False
    db_write_requires_os_user: str | None = None
    current_user_can_db_write: bool | None = None
    current_user_can_read_status: bool = True
    warnings: list[str] | None = None
    blockers: list[str] | None = None
    recommended_command_prefix: str | None = None
    final_decision: str = "UNKNOWN"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _is_local_peer_dsn(dsn: str) -> bool:
    value = (dsn or "").strip().lower()
    return value.startswith("postgresql:///") and "@" not in value and "host=" not in value


def build_operator_execution_context_report(config: MPFConfig, *, mode: str = "read") -> dict[str, object]:
    os_user = getpass.getuser()
    db_url = config.database.url
    is_local_peer = _is_local_peer_dsn(db_url)
    warnings: list[str] = []
    blockers: list[str] = []
    decision = "OK_FOR_READ"

    can_db_write: bool | None
    requires_user: str | None = "mpf" if is_local_peer else None
    cmd_prefix: str | None = None

    if is_local_peer:
        can_db_write = os_user == "mpf"
        if mode == "db-write":
            if can_db_write:
                decision = "OK_FOR_DB_WRITE"
            else:
                decision = "BLOCKED"
                blockers.append("db_write_requires_mpf_os_user")
                warnings.append("local_peer_postgresql_requires_mpf_os_user_for_db_write")
                cmd_prefix = "sudo -u mpf"
        else:
            decision = "OK_FOR_READ"
    else:
        can_db_write = True
        if mode == "db-write":
            decision = "OK_FOR_DB_WRITE"
            warnings.append("non_local_peer_database_url_db_write_auth_not_enforced_by_os_user_guard")

    return OperatorExecutionContextReport(
        mode=mode,
        os_user=os_user,
        effective_uid=os.geteuid(),
        database_url=db_url,
        database_url_is_local_peer=is_local_peer,
        db_write_requires_os_user=requires_user,
        current_user_can_db_write=can_db_write,
        warnings=sorted(set(warnings)),
        blockers=sorted(set(blockers)),
        recommended_command_prefix=cmd_prefix,
        final_decision=decision,
    ).to_dict()
