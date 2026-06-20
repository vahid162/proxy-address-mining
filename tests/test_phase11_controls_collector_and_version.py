from pathlib import Path
import mpf

def test_collector_controls_readiness_safe():
    text=Path('scripts/phase11_collect_operational_surfaces_evidence.sh').read_text()
    assert 'production-controls-pause-block-expire-readiness' in text
    assert 'production-controls-pause-block-expire-readiness.json' in text
    forbidden=['--yes','iptables-restore','conntrack -F','conntrack -D','docker restart','docker compose restart','systemctl restart','systemctl enable','customer update --yes','customer disable --yes','customer delete --yes']
    for f in forbidden:
        assert f not in text

def test_version_01383():
    assert Path('VERSION').read_text().strip() == '0.1.304'
    assert mpf.__version__ == '0.1.304'
    assert 'version = "0.1.304"' in Path('pyproject.toml').read_text()
    assert '## 0.1.304' in Path('CHANGELOG.md').read_text()
