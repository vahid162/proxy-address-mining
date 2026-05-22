from mpf.services.phase11_single_canary_backend_target_resolver import Phase11SingleCanaryBackendTargetResolver


def _report():
    return {"request": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001, "expected_version": "0.1.170"}}


class R:
    def __init__(self, rc, out):
        self.returncode = rc
        self.stdout = out


def _container_json(ip: str) -> str:
    return '[{"Id":"abc","State":{"Running":true},"NetworkSettings":{"Networks":{"mpf-proxy-internal":{"IPAddress":"'+ip+'"}}}}]'


def test_resolver_resolves_container_ip_with_local_only_listener(monkeypatch):
    def fake_run(argv):
        if argv[:3] == ["docker", "inspect", "mpf-forwarder-btc"]:
            return R(0, _container_json("172.18.0.3"))
        if argv[:3] == ["docker", "inspect", "network"]:
            return R(0, '[{"Options":{"com.docker.network.bridge.name":"br-x"}}]')
        return R(0, "State Recv-Q Send-Q Local Address:Port Peer Address:Port\nLISTEN 0 4096 127.0.0.1:60010 0.0.0.0:*")

    r = Phase11SingleCanaryBackendTargetResolver()
    monkeypatch.setattr(Phase11SingleCanaryBackendTargetResolver, "_run", lambda self, argv: fake_run(argv))
    monkeypatch.setattr(Phase11SingleCanaryBackendTargetResolver, "_connect_ok", lambda self, h, p: True)
    out = r.resolve(_report())
    assert out["status"] == "ok"
    assert out["backend_public_exposure"] is False


def test_resolver_rejects_loopback(monkeypatch):
    r = Phase11SingleCanaryBackendTargetResolver()
    monkeypatch.setattr(Phase11SingleCanaryBackendTargetResolver, "_run", lambda self, argv: R(0, _container_json("127.0.0.1")))
    out = r.resolve(_report())
    assert out["status"] == "blocked"


def test_resolver_rejects_public_ip(monkeypatch):
    r = Phase11SingleCanaryBackendTargetResolver()
    monkeypatch.setattr(Phase11SingleCanaryBackendTargetResolver, "_run", lambda self, argv: R(0, _container_json("8.8.8.8")))
    out = r.resolve(_report())
    assert out["error"] == "single_canary_backend_target_public_ip_forbidden"


def test_resolver_blocks_public_listener_on_60010(monkeypatch):
    def fake_run(argv):
        if argv[:3] == ["docker", "inspect", "mpf-forwarder-btc"]:
            return R(0, _container_json("172.18.0.3"))
        if argv[:3] == ["docker", "inspect", "network"]:
            return R(0, '[{}]')
        return R(0, "State Recv-Q Send-Q Local Address:Port Peer Address:Port\nLISTEN 0 4096 0.0.0.0:60010 0.0.0.0:*")

    r = Phase11SingleCanaryBackendTargetResolver()
    monkeypatch.setattr(Phase11SingleCanaryBackendTargetResolver, "_run", lambda self, argv: fake_run(argv))
    monkeypatch.setattr(Phase11SingleCanaryBackendTargetResolver, "_connect_ok", lambda self, h, p: True)
    out = r.resolve(_report())
    assert out["error"] == "single_canary_backend_public_exposure_detected"
