from __future__ import annotations

import ipaddress
import json
import socket
import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class Phase11SingleCanaryBackendTargetResolver:
    expected_version: str = "0.1.187"
    container_name: str = "mpf-forwarder-btc"
    docker_network: str = "mpf-proxy-internal"
    customer_key: str = "canary-btc-001"
    lane: str = "btc"
    customer_port: int = 20001
    backend_port: int = 60010

    def _run(self, argv: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(argv, shell=False, check=False, capture_output=True, text=True)

    def _connect_ok(self, host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=1.5):
                return True
        except OSError:
            return False

    def _is_public(self, ip: ipaddress.IPv4Address) -> bool:
        return not (ip.is_private or ip.is_loopback or ip.is_link_local)

    def _listener_public_exposure(self) -> bool:
        ss = self._run(["ss", "-ltn", "sport", "=", f":{self.backend_port}"])
        if ss.returncode != 0:
            return True
        lines = [l.strip() for l in ss.stdout.splitlines() if l.strip()]
        for line in lines:
            if line.startswith("State"):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            local = parts[3]
            host = local.rsplit(":", 1)[0].strip("[]")
            if host in {"127.0.0.1", "::1", "localhost"}:
                continue
            if host.startswith("127."):
                continue
            return True
        return False

    def resolve(self, report: dict[str, object]) -> dict[str, object]:
        req = report.get("request", {}) if isinstance(report.get("request"), dict) else {}
        if req.get("customer_key") != self.customer_key or req.get("lane") != self.lane or req.get("port") != self.customer_port:
            return {"status": "blocked", "error": "single_canary_scope_mismatch"}
        if req.get("expected_version") != self.expected_version:
            return {"status": "blocked", "error": "wrong_expected_version"}

        inspect = self._run(["docker", "inspect", self.container_name])
        if inspect.returncode != 0:
            return {"status": "blocked", "error": "single_canary_backend_target_inspect_failed"}
        try:
            data = json.loads(inspect.stdout)
        except json.JSONDecodeError:
            return {"status": "blocked", "error": "single_canary_backend_target_inspect_invalid_json"}
        if not isinstance(data, list) or not data:
            return {"status": "blocked", "error": "single_canary_backend_target_container_missing"}
        c = data[0]
        state = c.get("State", {}) if isinstance(c.get("State"), dict) else {}
        if state.get("Running") is not True:
            return {"status": "blocked", "error": "single_canary_backend_target_container_not_running"}
        nets = c.get("NetworkSettings", {}).get("Networks", {}) if isinstance(c.get("NetworkSettings"), dict) else {}
        if not isinstance(nets, dict) or self.docker_network not in nets:
            return {"status": "blocked", "error": "single_canary_backend_target_network_missing"}
        n = nets[self.docker_network] if isinstance(nets[self.docker_network], dict) else {}
        ip_raw = str(n.get("IPAddress", "")).strip()
        if not ip_raw:
            return {"status": "blocked", "error": "single_canary_backend_target_ip_missing"}
        try:
            ip = ipaddress.ip_address(ip_raw)
        except ValueError:
            return {"status": "blocked", "error": "single_canary_backend_target_ip_invalid"}
        if not isinstance(ip, ipaddress.IPv4Address):
            return {"status": "blocked", "error": "single_canary_backend_target_not_ipv4"}
        if ip.is_loopback:
            return {"status": "blocked", "error": "single_canary_backend_target_loopback_forbidden"}
        if self._is_public(ip):
            return {"status": "blocked", "error": "single_canary_backend_target_public_ip_forbidden"}

        host_backend_reachability = self._connect_ok(ip_raw, self.backend_port)
        if not host_backend_reachability:
            return {"status": "blocked", "error": "single_canary_backend_target_unreachable"}

        if self._listener_public_exposure():
            return {"status": "blocked", "error": "single_canary_backend_public_exposure_detected"}

        net_inspect = self._run(["docker", "inspect", "network", self.docker_network])
        bridge_name = None
        if net_inspect.returncode == 0:
            try:
                nw = json.loads(net_inspect.stdout)
                if isinstance(nw, list) and nw and isinstance(nw[0], dict):
                    opts = nw[0].get("Options", {}) if isinstance(nw[0].get("Options"), dict) else {}
                    bridge_name = opts.get("com.docker.network.bridge.name")
            except json.JSONDecodeError:
                bridge_name = None

        return {
            "status": "ok",
            "target_host": ip_raw,
            "target_port": self.backend_port,
            "container_name": self.container_name,
            "container_id": c.get("Id"),
            "docker_network": self.docker_network,
            "docker_bridge_name": bridge_name,
            "target_kind": "docker_container_ipv4",
            "host_backend_reachability": True,
            "backend_public_exposure": False,
            "mutation_performed": False,
            "production_traffic_enabled": False,
        }
