from pathlib import Path


def test_phase7_usage_accounting_service_has_no_runtime_execution_patterns() -> None:
    t = Path("mpf/services/phase7_usage_accounting_contract_service.py").read_text(encoding="utf-8").lower()
    bad = [
        "subprocess.run",
        "subprocess.popen",
        "os.system",
        "iptables-save",
        "conntrack",
        "docker",
        "systemctl",
        "open(..., \"w\")",
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
    for b in bad:
        assert b not in t
