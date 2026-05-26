from pathlib import Path

def test_script_contracts_and_forbidden():
 t=Path('scripts/phase11e_prepare_limited_activation_decision_package.sh').read_text()
 for k in ['--abuse-readiness-json-sha256','--restart-readiness-json-sha256','--limited-acceptance-precheck-json-sha256','PYTHON_BIN','"$PYTHON_BIN" - <<\'PY\'']:
  assert k in t
 assert "python - <<'PY'" not in t
 assert 'mpf customer activate' not in t
 for bad in ['iptables-restore','conntrack -F','conntrack -D','docker restart','docker compose up','docker compose down','docker compose restart','systemctl restart','systemctl enable','mpf abuse hard','mpf abuse unhard']:
  assert bad not in t
