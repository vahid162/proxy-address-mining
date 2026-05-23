from mpf.services.phase11_single_canary_host_apply_executor import Phase11SingleCanaryHostApplyExecutor
from mpf.services.phase11_single_canary_post_apply_verifier import Phase11SingleCanaryPostApplyVerifier
from mpf.services.phase11_exact_canary_restore_payload_renderer import Phase11ExactCanaryRestorePayloadRenderer


def _target_report():
    return {
        "single_canary_backend_target": {"target_host": "172.18.0.3", "target_port": 60010},
        "live_nat_prerequisites": {"canary_rule_exists": False},
    }


def _payload_ok():
    return (
        "*nat\n"
        "-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" -j DNAT --to-destination 172.18.0.3:60010\n"
        "COMMIT\n"
        "*filter\n"
        ":MPFC_20001 - [0:0]\n"
        "-A MPFC_20001 -p tcp --dport 20001 -m connlimit --connlimit-above 0 -m comment --comment \"mpf:canary-btc-001:customer_connlimit_reject\" -j REJECT\n"
        "-A MPFC_20001 -p tcp --dport 20001 -m hashlimit --hashlimit-above 1/min --hashlimit-burst 1 --hashlimit-mode srcip --hashlimit-name mpf-canary-btc-001-20001 -m comment --comment \"mpf:canary-btc-001:customer_hashlimit_reject\" -j REJECT\n"
        "COMMIT\n"
    )


def _payload_filter_only():
    return (
        "*filter\n"
        ":MPFC_20001 - [0:0]\n"
        "-A MPFC_20001 -p tcp --dport 20001 -m connlimit --connlimit-above 0 -m comment --comment \"mpf:canary-btc-001:customer_connlimit_reject\" -j REJECT\n"
        "-A MPFC_20001 -p tcp --dport 20001 -m hashlimit --hashlimit-above 1/min --hashlimit-burst 1 --hashlimit-mode srcip --hashlimit-name mpf-canary-btc-001-20001 -m comment --comment \"mpf:canary-btc-001:customer_hashlimit_reject\" -j REJECT\n"
        "COMMIT\n"
    )


def test_executor_accepts_exact_nat_filter_payload(monkeypatch):
    ex = Phase11SingleCanaryHostApplyExecutor()
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY_EXECUTE", "allow")
    monkeypatch.delenv("CI", raising=False)

    calls = []

    class R:
        def __init__(self, rc=0, out=""):
            self.returncode = rc
            self.stdout = out

    def fake_run(argv, **kwargs):
        calls.append(argv)
        if argv == ["iptables-save", "-t", "nat"]:
            return R(0, "*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\nCOMMIT\n")
        return R(0, "*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\nCOMMIT\n")

    monkeypatch.setattr(Phase11SingleCanaryHostApplyExecutor, "_run", lambda self, argv, **kwargs: fake_run(argv, **kwargs))
    out = ex.execute(_target_report(), _payload_ok())
    assert out["status"] == "ok"
    assert ["iptables-restore", "--test", "--noflush"] in calls
    assert ["iptables-restore", "--noflush"] in calls


def test_executor_blocks_extra_dport_20001(monkeypatch):
    ex = Phase11SingleCanaryHostApplyExecutor()
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY_EXECUTE", "allow")
    monkeypatch.delenv("CI", raising=False)
    payload = _payload_ok() + "-A MPFC_20001 -p tcp --dport 20001 -j REJECT\n"
    out = ex.execute(_target_report(), payload)
    assert out["status"] == "blocked"


def test_executor_blocks_wrong_or_broad_reject_sources(monkeypatch):
    ex = Phase11SingleCanaryHostApplyExecutor()
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY_EXECUTE", "allow")
    monkeypatch.delenv("CI", raising=False)
    wrong = _payload_ok().replace("mpf:canary-btc-001:customer_connlimit_reject", "mpf:other:customer_connlimit_reject")
    broad = _payload_ok().replace("mpf:canary-btc-001:customer_hashlimit_reject", "customer_hashlimit_reject")
    assert ex.execute(_target_report(), wrong)["status"] == "blocked"
    assert ex.execute(_target_report(), broad)["status"] == "blocked"


def test_executor_blocks_in_ci_or_missing_guards(monkeypatch):
    ex = Phase11SingleCanaryHostApplyExecutor()
    monkeypatch.setenv("CI", "1")
    out = ex.execute(_target_report(), _payload_ok())
    assert out["error"] == "single_canary_host_apply_not_allowed_in_ci"
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", raising=False)
    out2 = ex.execute(_target_report(), _payload_ok())
    assert out2["status"] == "blocked"


def test_verifier_exact_nat_and_filter_ok(monkeypatch):
    class R:
        def __init__(self, rc, out): self.returncode=rc; self.stdout=out
    def fake_run(argv, **kwargs):
        if argv[-1] == "nat":
            return R(0, "*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\n-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" -j DNAT --to-destination 172.18.0.3:60010\nCOMMIT\n")
        return R(0, "*filter\n:MPFC_20001 - [0:0]\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_connlimit_reject\" -j REJECT\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_hashlimit_reject\" -j REJECT\nCOMMIT\n")
    monkeypatch.setattr("subprocess.run", fake_run)
    out = Phase11SingleCanaryPostApplyVerifier().verify(_target_report())
    assert out["status"] == "ok"
    assert out["filter_reject_counter_source_verified"] is True


def test_verifier_filter_source_failures(monkeypatch):
    class R:
        def __init__(self, rc, out): self.returncode=rc; self.stdout=out
    nat_ok = "*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\n-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" -j DNAT --to-destination 172.18.0.3:60010\nCOMMIT\n"
    def run_missing_chain(argv, **kwargs):
        return R(0, nat_ok if argv[-1]=="nat" else "*filter\nCOMMIT\n")
    monkeypatch.setattr("subprocess.run", run_missing_chain)
    assert Phase11SingleCanaryPostApplyVerifier().verify(_target_report())["status"] == "blocked"

    def run_wrong(argv, **kwargs):
        filt = "*filter\n:MPFC_20001 - [0:0]\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:other:customer_connlimit_reject\" -j REJECT\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_hashlimit_reject\" -j REJECT\nCOMMIT\n"
        return R(0, nat_ok if argv[-1]=="nat" else filt)
    monkeypatch.setattr("subprocess.run", run_wrong)
    assert Phase11SingleCanaryPostApplyVerifier().verify(_target_report())["status"] == "blocked"

    def run_broad(argv, **kwargs):
        filt = "*filter\n:MPFC_20001 - [0:0]\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"customer_connlimit_reject\" -j REJECT\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_hashlimit_reject\" -j REJECT\nCOMMIT\n"
        return R(0, nat_ok if argv[-1]=="nat" else filt)
    monkeypatch.setattr("subprocess.run", run_broad)
    assert Phase11SingleCanaryPostApplyVerifier().verify(_target_report())["status"] == "blocked"


def test_verifier_backend_exposure_blocks(monkeypatch):
    class R:
        def __init__(self, rc, out): self.returncode=rc; self.stdout=out
    def fake_run(argv, **kwargs):
        if argv[-1] == "nat":
            return R(0, "*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\n-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" -j DNAT --to-destination 172.18.0.3:60010\nCOMMIT\n")
        return R(0, "*filter\n:MPFC_20001 - [0:0]\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_connlimit_reject\" -j REJECT\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_hashlimit_reject\" -j REJECT\n-A INPUT -p tcp --dport 60010 -j ACCEPT\nCOMMIT\n")
    monkeypatch.setattr("subprocess.run", fake_run)
    out = Phase11SingleCanaryPostApplyVerifier().verify(_target_report())
    assert out["status"] == "blocked"
    assert out["error"] == "single_canary_backend_public_exposure_detected"


def test_executor_accepts_real_renderer_payload(monkeypatch):
    report = {
        "scope": {"single_canary_only": True},
        "request": {
            "requested_action": "execute",
            "expected_version": "0.1.192",
            "customer_key": "canary-btc-001",
            "lane": "btc",
            "port": 20001,
        },
        "live_nat_prerequisites": {"mpf_nat_pre_chain_exists": True, "prerouting_hook_to_mpf_nat_pre_count": 1},
        "single_canary_backend_target": {"target_host": "172.18.0.3", "target_port": 60010, "target_kind": "docker_container_ipv4"},
    }
    rendered = Phase11ExactCanaryRestorePayloadRenderer().render(report)
    assert rendered["status"] == "ok"

    ex = Phase11SingleCanaryHostApplyExecutor()
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY_EXECUTE", "allow")
    monkeypatch.delenv("CI", raising=False)

    calls = []

    class R:
        def __init__(self, rc=0, out=""):
            self.returncode = rc
            self.stdout = out

    def fake_run(argv, **kwargs):
        calls.append(argv)
        if argv == ["iptables-save", "-t", "nat"]:
            return R(0, "*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\nCOMMIT\n")
        return R(0, "*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\nCOMMIT\n")

    monkeypatch.setattr(Phase11SingleCanaryHostApplyExecutor, "_run", lambda self, argv, **kwargs: fake_run(argv, **kwargs))
    out = ex.execute(_target_report(), rendered["restore_payload"])
    assert out["status"] == "ok"
    assert ["iptables-restore", "--test", "--noflush"] in calls
    assert ["iptables-restore", "--noflush"] in calls


def test_executor_accepts_filter_only_when_report_proves_existing_nat(monkeypatch):
    ex = Phase11SingleCanaryHostApplyExecutor()
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY_EXECUTE", "allow")
    monkeypatch.delenv("CI", raising=False)
    report = _target_report()
    report["live_nat_prerequisites"]["canary_rule_exists"] = True

    class R:
        def __init__(self, rc=0, out=""): self.returncode = rc; self.stdout = out

    def fake_run(argv, **kwargs):
        if argv == ["iptables-save", "-t", "nat"]:
            return R(0, "*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\n-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" -j DNAT --to-destination 172.18.0.3:60010\nCOMMIT\n")
        return R(0, "")
    monkeypatch.setattr(Phase11SingleCanaryHostApplyExecutor, "_run", lambda self, argv, **kwargs: fake_run(argv, **kwargs))
    assert ex.execute(report, _payload_filter_only())["status"] == "ok"


def test_executor_blocks_filter_only_without_existing_nat_proof(monkeypatch):
    ex = Phase11SingleCanaryHostApplyExecutor()
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY_EXECUTE", "allow")
    monkeypatch.delenv("CI", raising=False)
    assert ex.execute(_target_report(), _payload_filter_only())["status"] == "blocked"


def test_executor_blocks_payload_with_nat_when_existing_nat_proven(monkeypatch):
    ex = Phase11SingleCanaryHostApplyExecutor()
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY", "allow")
    monkeypatch.setenv("MPF_PHASE11_SINGLE_CANARY_HOST_APPLY_EXECUTE", "allow")
    monkeypatch.delenv("CI", raising=False)
    report = _target_report()
    report["live_nat_prerequisites"]["canary_rule_exists"] = True
    assert ex.execute(report, _payload_ok())["status"] == "blocked"


def test_verifier_blocks_unrelated_customer_nat_reference(monkeypatch):
    class R:
        def __init__(self, rc, out): self.returncode=rc; self.stdout=out
    def fake_run(argv, **kwargs):
        if argv[-1] == "nat":
            return R(0, "*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\n-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" -j DNAT --to-destination 172.18.0.3:60010\n-A MPF_NAT_PRE -p tcp --dport 20002 -m comment --comment \"mpf:other:customer_nat_redirect\" -j DNAT --to-destination 172.18.0.4:60010\nCOMMIT\n")
        return R(0, "*filter\n:MPFC_20001 - [0:0]\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_connlimit_reject\" -j REJECT\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_hashlimit_reject\" -j REJECT\nCOMMIT\n")
    monkeypatch.setattr("subprocess.run", fake_run)
    out = Phase11SingleCanaryPostApplyVerifier().verify(_target_report())
    assert out["status"] == "blocked"
    assert out["error"] == "single_canary_unrelated_customer_rule_detected"


def test_verifier_blocks_duplicate_canary_with_loopback_target(monkeypatch):
    class R:
        def __init__(self, rc, out): self.returncode=rc; self.stdout=out
    def fake_run(argv, **kwargs):
        if argv[-1] == "nat":
            return R(0, "*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\n-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" -j DNAT --to-destination 172.18.0.3:60010\n-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" -j DNAT --to-destination 127.0.0.1:60010\nCOMMIT\n")
        return R(0, "*filter\n:MPFC_20001 - [0:0]\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_connlimit_reject\" -j REJECT\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_hashlimit_reject\" -j REJECT\nCOMMIT\n")
    monkeypatch.setattr("subprocess.run", fake_run)
    out = Phase11SingleCanaryPostApplyVerifier().verify(_target_report())
    assert out["status"] == "blocked"
    assert out["error"] == "single_canary_loopback_target_forbidden"


def test_verifier_blocks_duplicate_canary_with_wrong_target(monkeypatch):
    class R:
        def __init__(self, rc, out): self.returncode=rc; self.stdout=out
    def fake_run(argv, **kwargs):
        if argv[-1] == "nat":
            return R(0, "*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\n-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" -j DNAT --to-destination 172.18.0.3:60010\n-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" -j DNAT --to-destination 172.18.0.99:60010\nCOMMIT\n")
        return R(0, "*filter\n:MPFC_20001 - [0:0]\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_connlimit_reject\" -j REJECT\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_hashlimit_reject\" -j REJECT\nCOMMIT\n")
    monkeypatch.setattr("subprocess.run", fake_run)
    out = Phase11SingleCanaryPostApplyVerifier().verify(_target_report())
    assert out["status"] == "blocked"
    assert out["error"] == "single_canary_duplicate_rule_detected"


def test_verifier_blocks_single_canary_rule_with_wrong_destination(monkeypatch):
    class R:
        def __init__(self, rc, out): self.returncode=rc; self.stdout=out
    def fake_run(argv, **kwargs):
        if argv[-1] == "nat":
            return R(0, "*nat\n:MPF_NAT_PRE - [0:0]\n-A PREROUTING -j MPF_NAT_PRE\n-A MPF_NAT_PRE -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_nat_redirect\" -j DNAT --to-destination 172.18.0.99:60010\nCOMMIT\n")
        return R(0, "*filter\n:MPFC_20001 - [0:0]\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_connlimit_reject\" -j REJECT\n-A MPFC_20001 -p tcp --dport 20001 -m comment --comment \"mpf:canary-btc-001:customer_hashlimit_reject\" -j REJECT\nCOMMIT\n")
    monkeypatch.setattr("subprocess.run", fake_run)
    out = Phase11SingleCanaryPostApplyVerifier().verify(_target_report())
    assert out["status"] == "blocked"
    assert out["error"] == "single_canary_wrong_nat_target_detected"
