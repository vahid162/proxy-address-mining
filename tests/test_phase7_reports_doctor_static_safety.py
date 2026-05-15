from pathlib import Path


def test_phase7_reports_doctor_service_has_no_runtime_execution_patterns() -> None:
    t = Path("mpf/services/phase7_reports_doctor_service.py").read_text(encoding="utf-8").lower()
    forbidden = [
        "subprocess.run", "subprocess.popen", "os.system", "open(..., \"w\")", "write_text", "psycopg.connect",
        "insert into", "update", "delete from", "alembic", "migration", "sqlalchemy create_engine", "session.add", "session.commit",
    ]
    for pattern in forbidden:
        assert pattern not in t
