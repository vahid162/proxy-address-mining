from pathlib import Path

def test_script_safety_and_manifest():
 t=Path('scripts/phase11e_collect_abuse_restart_readiness_evidence.sh').read_text()
 for x in ['iptables-restore','conntrack -F','docker compose up','docker compose down','docker compose restart','systemctl restart','systemctl enable','abuse hard','abuse unhard','cp "$VIS" "$OUT_DIR/current-controlled-artifact-gate.json"']:
  assert x not in t
 assert '--collect-source-evidence' in t and '--collect-artifact-gate' in t and 'current-controlled-artifact-gate.json' in t
 assert 'phase11e-source-evidence-bundle.json' in t and 'abuse-1h-evidence.json' in t and 'restart-container-order-evidence.json' in t and 'limited-acceptance-precheck.json' in t
