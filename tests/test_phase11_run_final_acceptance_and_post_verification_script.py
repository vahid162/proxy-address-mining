from pathlib import Path
S=Path('scripts/phase11_run_final_acceptance_and_post_verification.sh').read_text()
def test_order_and_local_peer_note(): assert S.index('production phase11-final-acceptance') < S.index('production phase11-post-acceptance-verification') and 'sudo -u mpf' in S
def test_no_forbidden_commands():
 for x in ('iptables-restore','conntrack -F','conntrack -D','docker restart','docker compose up','docker compose down','docker compose restart','systemctl restart','systemctl enable','mpf customer activate','mpf abuse hard','mpf abuse unhard','INSERT ','UPDATE ','DELETE ','ALTER ','DROP ','TRUNCATE ','psql '): assert x not in S
