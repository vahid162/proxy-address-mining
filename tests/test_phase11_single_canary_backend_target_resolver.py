from mpf.services.phase11_single_canary_backend_target_resolver import Phase11SingleCanaryBackendTargetResolver


def _report():
    return {"request": {"customer_key": "canary-btc-001", "lane": "btc", "port": 20001, "expected_version": "0.1.164"}}


class R:
    def __init__(self, rc, out): self.returncode=rc; self.stdout=out


def test_resolver_resolves_container_ip(monkeypatch):
    def fake_run(argv):
        if argv[:2]==["docker","inspect"] and len(argv)==3:
            return R(0, '[{"Id":"abc","State":{"Running":true},"NetworkSettings":{"Networks":{"mpf-proxy-internal":{"IPAddress":"172.18.0.3"}}}}]')
        return R(0,'[{"Options":{"com.docker.network.bridge.name":"br-x"}}]')
    r=Phase11SingleCanaryBackendTargetResolver()
    monkeypatch.setattr(Phase11SingleCanaryBackendTargetResolver,"_run",lambda self,argv: fake_run(argv))
    monkeypatch.setattr(Phase11SingleCanaryBackendTargetResolver,"_connect_ok",lambda self,h,p: False if h=="0.0.0.0" else True)
    out=r.resolve(_report())
    assert out["status"]=="ok" and out["target_host"]=="172.18.0.3"


def test_resolver_rejects_loopback(monkeypatch):
    r=Phase11SingleCanaryBackendTargetResolver()
    monkeypatch.setattr(Phase11SingleCanaryBackendTargetResolver,"_run",lambda self,argv: R(0,'[{"State":{"Running":true},"NetworkSettings":{"Networks":{"mpf-proxy-internal":{"IPAddress":"127.0.0.1"}}}}]'))
    out=r.resolve(_report())
    assert out["status"]=="blocked"
