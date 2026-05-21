from mpf.services.phase11_single_canary_host_apply_executor import Phase11SingleCanaryHostApplyExecutor
from mpf.services.phase11_single_canary_post_apply_verifier import Phase11SingleCanaryPostApplyVerifier


def test_executor_requires_three_guards(monkeypatch):
    ex = Phase11SingleCanaryHostApplyExecutor()
    monkeypatch.delenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", raising=False)
    out = ex.execute({}, "*nat\n-A MPF_NAT_PRE -p tcp --dport 20001 -j DNAT --to-destination 172.18.0.3:60010\nCOMMIT\n")
    assert out["status"] == "blocked"


def test_verifier_duplicate_hook_rejected(monkeypatch):
    class R:
        def __init__(self, rc, out): self.returncode=rc; self.stdout=out
    calls=[]
    def fake_run(argv, **kwargs):
        calls.append(argv)
        if argv[-1] == "nat":
            return R(0, "*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\n-A PREROUTING -j MPF_NAT_PRE\n-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" -j DNAT --to-destination 172.18.0.3:60010\nCOMMIT\n")
        return R(0, "")
    monkeypatch.setattr("subprocess.run", fake_run)
    out = Phase11SingleCanaryPostApplyVerifier().verify({})
    assert out["status"] == "blocked"
