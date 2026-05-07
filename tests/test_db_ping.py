from __future__ import annotations

from types import SimpleNamespace

from mpf.db import _local_peer_dbname, ping_database


def test_local_peer_dbname_detects_postgresql_socket_url() -> None:
    assert _local_peer_dbname("postgresql:///mpf") == "mpf"


def test_local_peer_dbname_ignores_remote_urls() -> None:
    assert _local_peer_dbname("postgresql://user@example.invalid/mpf") is None
    assert _local_peer_dbname("postgresql+psycopg:///mpf") is None


def test_root_local_peer_ping_uses_mpf_system_user(monkeypatch) -> None:
    calls: list[list[str]] = []

    class Result:
        returncode = 0
        stdout = "1\n"
        stderr = ""

    def fake_run(cmd: list[str], text: bool, capture_output: bool) -> Result:
        calls.append(cmd)
        assert text is True
        assert capture_output is True
        return Result()

    monkeypatch.setattr("mpf.db.os.geteuid", lambda: 0)
    monkeypatch.setattr("mpf.db.subprocess.run", fake_run)

    config = SimpleNamespace(database=SimpleNamespace(url="postgresql:///mpf"))
    result = ping_database(config)  # type: ignore[arg-type]

    assert result.ok is True
    assert result.message == "OK"
    assert calls == [["sudo", "-u", "mpf", "psql", "-d", "mpf", "-tAc", "select 1"]]
