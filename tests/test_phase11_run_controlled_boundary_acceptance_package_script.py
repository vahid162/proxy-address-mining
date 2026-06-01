import hashlib, json, os, subprocess
from pathlib import Path
SCRIPT_PATH = Path("scripts/phase11_run_controlled_boundary_acceptance_package.sh"); SCRIPT = SCRIPT_PATH.read_text()
def test_helper_runs_only_package_and_documents_local_peer():
    assert '"$MPF_BIN" production phase11-controlled-boundary-acceptance-package' in SCRIPT and SCRIPT.count('"$MPF_BIN" production ') == 1 and "sudo -u mpf" in SCRIPT
def test_helper_has_no_forbidden_mutation_commands():
    for marker in ("iptables-restore", "conntrack -F", "conntrack -D", "docker restart", "docker compose up", "docker compose down", "docker compose restart", "systemctl restart", "systemctl enable", "mpf customer activate", "mpf abuse hard", "mpf abuse unhard", "INSERT ", "UPDATE ", "DELETE ", "ALTER ", "DROP ", "TRUNCATE ", "psql "): assert marker not in SCRIPT
def _run(tmp_path, decision):
    args=[]
    for name in ("limited-acceptance-decision", "artifact-gate", "source-evidence", "abuse-readiness", "restart-readiness"):
        path=tmp_path/f"{name}.json"; path.write_text("{}\n"); sha=hashlib.sha256(path.read_bytes()).hexdigest(); args += [f"--{name}-json", str(path), f"--{name}-json-sha256", sha]
    fake=tmp_path/"fake-mpf"; fake.write_text(f'''#!/usr/bin/env bash\nset -euo pipefail\nout=\nwhile [ $# -gt 0 ]; do if [ "$1" = --out-json ]; then out=$2; shift 2; else shift; fi; done\nprintf '%s\\n' '{{"final_decision":"{decision}"}}' > "$out"\n'''); fake.chmod(0o755)
    out=tmp_path/"out"; proc=subprocess.run([str(SCRIPT_PATH), "--expected-version", "0.1.232", *args, "--out-dir", str(out), "--operator", "operator", "--reason", "read-only"], env={**os.environ,"MPF_BIN":str(fake)}, check=False)
    return proc, out
def test_helper_writes_manifest_hash_files(tmp_path):
    proc,out=_run(tmp_path,"PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_PACKAGE_READY"); assert proc.returncode == 0; manifest=json.loads((out/"manifest.json").read_text()); assert manifest["mutation_performed"] is False; assert (out/"phase11-controlled-boundary-acceptance-package.sha256").is_file() and (out/"sha256-manifest.txt").is_file()
def test_helper_fails_closed_on_blocked(tmp_path): assert _run(tmp_path,"BLOCKED")[0].returncode != 0
