from pathlib import Path
SCRIPT=Path('scripts/phase11e_run_limited_activation_execute_package.sh').read_text()
def test_script_has_safe_python_and_manifests():
 assert 'PYTHON_BIN' in SCRIPT;assert 'manifest.json' in SCRIPT;assert 'sha256-manifest.txt' in SCRIPT;assert "python - <<'PY'" not in SCRIPT
def test_script_requires_execute_and_uses_scoped_commands():
 assert 'if [ "$EXECUTE" != true ]' in SCRIPT;assert 'phase11e-limited-activation-execute' in SCRIPT;assert 'phase11e-limited-activation-post-evidence-collect' in SCRIPT
