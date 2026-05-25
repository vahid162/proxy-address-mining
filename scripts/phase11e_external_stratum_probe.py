#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import tempfile
import time
from pathlib import Path
from typing import Any


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with open(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        Path(tmp_name).replace(path)
    finally:
        if Path(tmp_name).exists():
            Path(tmp_name).unlink(missing_ok=True)


def _record_tx(messages: list[dict[str, Any]], payload: dict[str, Any]) -> None:
    messages.append({"direction": "tx", **payload})


def _record_rx(messages: list[dict[str, Any]], payload: dict[str, Any]) -> None:
    msg: dict[str, Any] = {"direction": "rx"}
    for key in ("id", "method", "result", "params", "error"):
        if key in payload:
            msg[key] = payload[key]
    if "result" in payload:
        msg["result_present"] = True
        if payload.get("result") is True:
            msg["result_true"] = True
    messages.append(msg)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Phase11E external Stratum probe (run outside farm5)")
    p.add_argument("--host", required=True)
    p.add_argument("--port", type=int, default=20101)
    p.add_argument("--worker", default="limited-btc-001.worker01")
    p.add_argument("--password", default="x")
    p.add_argument("--hold-seconds", type=int, default=600)
    p.add_argument("--ready-timeout-seconds", type=int, default=30)
    p.add_argument("--read-timeout-seconds", type=int, default=2)
    p.add_argument("--json-out", required=True)
    p.add_argument("--operator-mapped-worker", default="")
    return p


def main() -> int:
    args = build_parser().parse_args()
    out_path = Path(args.json_out)
    started = time.monotonic()
    messages: list[dict[str, Any]] = []
    transcript: dict[str, Any] = {
        "connect_host": args.host,
        "connect_port": args.port,
        "worker_name": args.worker,
        "messages": messages,
    }
    if args.operator_mapped_worker:
        transcript["operator_mapped_worker"] = args.operator_mapped_worker
    _atomic_write_json(out_path, transcript)

    subscribe = {"id": 1, "method": "mining.subscribe", "params": []}
    authorize = {"id": 2, "method": "mining.authorize", "params": [args.worker, args.password]}

    with socket.create_connection((args.host, args.port), timeout=max(1, args.ready_timeout_seconds)) as sock:
        sock.settimeout(float(args.read_timeout_seconds))
        for request in (subscribe, authorize):
            payload = (json.dumps(request, separators=(",", ":")) + "\n").encode("utf-8")
            sock.sendall(payload)
            _record_tx(messages, request)
            _atomic_write_json(out_path, transcript)

        deadline = started + max(1, args.ready_timeout_seconds)
        got_signal = False
        fobj = sock.makefile("rb")
        while time.monotonic() < deadline:
            try:
                line = fobj.readline()
            except socket.timeout:
                continue
            if not line:
                break
            raw = line.decode("utf-8", errors="replace").strip()
            if not raw:
                continue
            try:
                rx = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(rx, dict):
                _record_rx(messages, rx)
                _atomic_write_json(out_path, transcript)
                method = rx.get("method")
                if method in {"mining.set_difficulty", "mining.notify"}:
                    got_signal = True
                    break

        hold_until = started + max(1, args.hold_seconds)
        print("READY_TO_COPY_TRANSCRIPT while connection remains open", flush=True)
        while time.monotonic() < hold_until:
            time.sleep(1)
            if got_signal:
                # keep open intentionally; no extra tx/rx needed.
                pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
