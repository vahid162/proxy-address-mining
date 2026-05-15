from pathlib import Path

def test_phase7_service_has_no_runtime_execution_patterns() -> None:
    t = Path('mpf/services/phase7_usage_policy_readiness_service.py').read_text(encoding='utf-8').lower()
    bad = ['subprocess.run','subprocess.popen','os.system','open(..., "w")','write_text','psycopg.connect','insert into','update ','delete from','alembic','migration']
    for b in bad:
        assert b not in t
