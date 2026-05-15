from pathlib import Path


DISALLOWED = [
    "subprocess.run",
    "subprocess.Popen",
    "os.system",
    "iptables-save",
    "iptables-restore",
    "conntrack",
    "docker",
    "systemctl",
    'open(..., "w")',
    "write_text",
    "psycopg.connect",
    "insert into",
    "update",
    "delete from",
    "alembic",
    "migration",
    "sqlalchemy create_engine",
    "session.add",
    "session.commit",
]


def test_service_static_safety_tokens_absent() -> None:
    text = Path("mpf/services/phase7_policy_reject_accounting_contract_service.py").read_text(encoding="utf-8").lower()
    for token in DISALLOWED:
        assert token.lower() not in text
