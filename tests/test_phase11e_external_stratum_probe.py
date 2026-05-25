import json
import socket
import subprocess
import sys
import threading
from pathlib import Path

SCRIPT = Path("scripts/phase11e_external_stratum_probe.py")


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def test_external_probe_script_contract_shape_and_safety() -> None:
    t = SCRIPT.read_text(encoding="utf-8")
    assert "socket.create_connection" in t
    assert "--json-out" in t
    assert "default=20101" in t
    assert 'default="limited-btc-001.worker01"' in t
    assert "default=600" in t
    assert "mining.subscribe" in t and "mining.authorize" in t
    assert "mining.submit" not in t
    assert "READY_TO_COPY_TRANSCRIPT" in t
    assert 'makefile("rb")' not in t
    assert ".readline(" not in t
    for forbidden in ("requests", "httpx", "aiohttp", "websockets"):
        assert forbidden not in t


def test_no_response_timeout_is_blocked_and_nonzero(tmp_path) -> None:
    port = _find_free_port()

    def server() -> None:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", port))
        srv.listen(1)
        conn, _ = srv.accept()
        with conn:
            conn.recv(4096)
            conn.recv(4096)
            # no response on purpose
            threading.Event().wait(2)
        srv.close()

    th = threading.Thread(target=server, daemon=True)
    th.start()

    out = tmp_path / "blocked.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--ready-timeout-seconds",
            "1",
            "--read-timeout-seconds",
            "1",
            "--hold-seconds",
            "1",
            "--json-out",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "BLOCKED_NO_STRATUM_RESPONSE" in proc.stderr
    assert "READY_TO_COPY_TRANSCRIPT" not in proc.stdout
    assert "Traceback" not in proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["probe_status"] == "BLOCKED_NO_STRATUM_RESPONSE"
    assert payload["blocker"] == "read_timeout_waiting_for_stratum_response"
    assert payload["connection_attempted"] is True
    assert payload["subscribe_sent"] is True
    assert payload["authorize_sent"] is True
    assert payload["no_submit_performed"] is True


def test_successful_stratum_signal_path_produces_useful_transcript(tmp_path) -> None:
    port = _find_free_port()

    def server() -> None:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", port))
        srv.listen(1)
        conn, _ = srv.accept()
        with conn:
            conn.recv(4096)
            conn.sendall(b'{"id":1,"result":[["mining.notify","1"],"ex1",4],"error":null}\n')
            conn.sendall(b'{"id":2,"result":true,"error":null}\n')
            conn.sendall(b'{"id":null,"method":"mining.set_difficulty","params":[1024]}\n')
            threading.Event().wait(2)
        srv.close()

    threading.Thread(target=server, daemon=True).start()
    out = tmp_path / "ok.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--ready-timeout-seconds",
            "5",
            "--read-timeout-seconds",
            "1",
            "--hold-seconds",
            "1",
            "--json-out",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "CONNECTED" in proc.stdout
    assert "SUBSCRIBE_AUTHORIZE_SENT" in proc.stdout
    assert "READY_TO_COPY_TRANSCRIPT" in proc.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["connect_port"] == port
    assert any(m.get("method") == "mining.subscribe" for m in payload["messages"])
    assert any(m.get("id") == 2 and m.get("result") is True for m in payload["messages"])
    assert any(m.get("method") == "mining.set_difficulty" for m in payload["messages"])

