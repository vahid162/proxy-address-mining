from pathlib import Path


SCRIPT = Path("scripts/phase11e_run_limited_activation_execute_package.sh").read_text(encoding="utf-8")


def test_script_resolves_console_entrypoint_and_writes_manifests() -> None:
    assert "MPF_BIN" in SCRIPT
    assert "PYTHON_BIN" not in SCRIPT
    assert '"$MPF_BIN" production phase11e-limited-activation-execute' in SCRIPT
    assert '"$MPF_BIN" production phase11e-limited-activation-post-evidence-collect' in SCRIPT
    assert "-m mpf" not in SCRIPT
    assert "manifest.json" in SCRIPT
    assert "sha256-manifest.txt" in SCRIPT
    assert "python - <<'PY'" not in SCRIPT


def test_script_requires_execute_and_excludes_forbidden_mutation_commands() -> None:
    assert 'if [ "$EXECUTE" != true ]' in SCRIPT
    for forbidden in (
        "iptables-restore",
        "conntrack -F",
        "conntrack -D",
        "docker restart",
        "docker compose up",
        "docker compose down",
        "docker compose restart",
        "systemctl restart",
        "systemctl enable",
        "mpf customer activate",
        "mpf abuse hard",
        "mpf abuse unhard",
    ):
        assert forbidden not in SCRIPT
