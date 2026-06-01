import subprocess
from pathlib import Path
SCRIPT=Path('scripts/phase11e_collect_limited_activation_observation_and_review.sh')
def test_script_is_read_only_and_ordered():
 s=SCRIPT.read_text(); assert '"$MPF_BIN" production' in s; assert 'python -m mpf' not in s; assert s.index('phase11e-limited-activation-observation-collect') < s.index('phase11e-limited-activation-acceptance-review'); assert 'manifest.json' in s and 'sha256-manifest.txt' in s
 for forbidden in ('iptables-restore','conntrack -F','conntrack -D','docker restart','docker compose up','docker compose down','docker compose restart','systemctl restart','systemctl enable','mpf customer activate','mpf abuse hard','mpf abuse unhard'): assert forbidden not in s
def test_script_fails_closed_on_hash_mismatch(tmp_path):
 f=tmp_path/'x.json'; f.write_text('{}'); args=[]
 for name in ('activation-execution','post-activation-evidence','source-evidence','rollback-package','artifact-gate'): args += [f'--{name}-json',str(f),f'--{name}-json-sha256','bad']
 r=subprocess.run(['bash',str(SCRIPT),'--expected-version','x',*args,'--out-dir',str(tmp_path/'out'),'--operator','o','--reason','r'],capture_output=True,text=True); assert r.returncode != 0
