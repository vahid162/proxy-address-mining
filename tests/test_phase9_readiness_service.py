from pathlib import Path
from mpf.config import load_config
from mpf.services.phase9_readiness_service import build_phase9_readiness_report


def test_phase9_readiness_report_safe() -> None:
    cfg = load_config(Path('configs/mpf.example.yaml'))
    r = build_phase9_readiness_report(cfg)
    assert r['component'] == 'phase9_readiness'
    assert r['execution_allowed'] is False
    assert r['firewall_apply_authorized'] is False
    assert r['production_traffic_authorized'] is False
