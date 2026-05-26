from pathlib import Path

def test_script_exists_and_no_forbidden():
 t=Path('scripts/phase11e_prepare_limited_activation_decision_package.sh').read_text()
 for bad in ['iptables-restore','conntrack -F','conntrack -D','docker restart','docker compose up','docker compose down','docker compose restart','systemctl restart','systemctl enable','mpf abuse hard','mpf abuse unhard']:
  assert bad not in t
