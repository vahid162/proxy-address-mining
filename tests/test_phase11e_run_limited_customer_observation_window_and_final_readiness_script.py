from pathlib import Path
SCRIPT=Path('scripts/phase11e_run_limited_customer_observation_window_and_final_readiness.sh').read_text()
def test_helper_runs_window_before_final_readiness_and_writes_manifests():
 assert SCRIPT.index('"$MPF_BIN" production phase11e-limited-customer-observation-window') < SCRIPT.index('"$MPF_BIN" production phase11-final-acceptance-readiness-planning')
 assert 'manifest.json' in SCRIPT and 'sha256-manifest.txt' in SCRIPT and 'sudo -u mpf' in SCRIPT
def test_helper_has_no_forbidden_mutation_commands():
 for marker in ('iptables-restore','conntrack -F','conntrack -D','docker restart','docker compose up','docker compose down','docker compose restart','systemctl restart','systemctl enable','mpf customer activate','mpf abuse hard','mpf abuse unhard','INSERT ','UPDATE ','DELETE ','ALTER ','DROP ','TRUNCATE ','psql '): assert marker not in SCRIPT
