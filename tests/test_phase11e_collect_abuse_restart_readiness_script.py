from pathlib import Path

def test_script_safety_and_manifest():
 t=Path('scripts/phase11e_collect_abuse_restart_readiness_evidence.sh').read_text()
 for x in ['iptables-restore','conntrack -F','docker compose up','docker compose down','docker compose restart','systemctl restart','systemctl enable','abuse hard','abuse unhard']:
  assert x not in t
 assert 'manifest.json' in t and 'sha256sum' in t and '--expected-version' in t
