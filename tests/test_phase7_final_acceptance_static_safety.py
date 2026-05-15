from pathlib import Path


def test_new_phase7_services_have_no_runtime_execution_patterns() -> None:
    banned = [
        "subprocess.run", "subprocess.popen", "os.system", "iptables-save", "iptables-restore", "conntrack", "docker", "systemctl",
        "open(", "write_text", "psycopg.connect", "insert into", "delete from", "alembic", "migration", "create_engine", "session.add", "session.commit",
    ]
    for fp in [
        "mpf/services/phase7_final_acceptance_readiness_service.py",
        "mpf/services/phase7_operator_acceptance_decision_service.py",
    ]:
        text = Path(fp).read_text(encoding="utf-8").lower()
        for b in banned:
            assert b not in text
