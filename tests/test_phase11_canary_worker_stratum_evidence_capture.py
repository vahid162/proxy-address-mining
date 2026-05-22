from pathlib import Path
from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence, build_phase11_canary_visibility_bundle_report
from mpf.services.phase11_canary_acceptance_review_service import build_phase11_canary_acceptance_review_report, Phase11CanaryAcceptanceEvidence
from mpf.services import phase11_canary_worker_stratum_evidence_capture_service as svc


def _cfg():
    return load_config(Path("configs/mpf.example.yaml"))


def test_worker_stratum_capture_success(monkeypatch):
    class F:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def settimeout(self, x): pass
        def sendall(self, x): pass
        def recv(self, n):
            if not hasattr(self, 'buf'):
                self.buf=(b'{"id":1,"result":[1],"error":null}\n'+b'{"id":2,"result":true,"error":null}\n'+b'{"method":"mining.set_difficulty"}\n'+b'{"method":"mining.notify"}\n')
            if not self.buf: return b''
            b=self.buf[:1]; self.buf=self.buf[1:]; return b
    monkeypatch.setattr("socket.create_connection", lambda *a, **k: F())
    monkeypatch.setattr(svc, "_read_only_docker_logs", lambda c, lines=200: "canary-btc-001.worker-001 bitcoin.viabtc.io:3333 127.0.0.1:20170")
    r = svc.build_phase11_canary_worker_stratum_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.185", farm5_baseline_version="0.1.168", connect_host="85.198.11.110", connect_port=20001, worker_name="canary-btc-001.worker-001", collect_live=False)
    assert r["worker_evidence"]["worker_visibility_ok"] is True
    assert r["worker_evidence"]["unique_worker_count"] == 1


def test_scope_mismatch_does_not_lift_worker_visibility():
    ev = Phase11CanaryVisibilityEvidence(customer_key="other", lane="btc", port=20001, evidence_source="live_source_backed_canary_worker_stratum", worker_visibility_ok=True, worker_reference="x")
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.185", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["unique_workers_visibility"]["status"] == "MISSING"


def test_cli_requires_connect_host():
    out = CliRunner().invoke(app, ["production", "canary-worker-stratum-evidence-capture", "--config", "configs/mpf.example.yaml"])
    assert out.exit_code != 0


def test_acceptance_review_clears_subscribe_authorize_when_proven():
    ev = Phase11CanaryAcceptanceEvidence(canary_customer_db_visible=True, usage_visibility_ok=True, reject_visibility_ok=True, session_visibility_ok=True, unique_ip_visibility_ok=True, worker_visibility_ok=True, mpf_nat_pre_exists=True, prerouting_hook_present=True, canary_nat_rule_present=True, canary_nat_rule_count=1, no_extra_customer_nat_rules=True, no_unexpected_mpf_firewall_references=True, canary_nat_target="172.18.0.3:60010", proxy_doctor_ok=True, bridge_healthy=True, bridge_reachable_from_forwarder=True, v2raya_ui_local_only=True, btc_backend_local_only=True, bridge_no_host_publish=True, forwarder_uses_bridge_upstream=True, direct_v2raya_20170_blocked=True, nat_counter_packets=1, conntrack_assured=True, stratum_subscribe_ok=True, stratum_authorize_ok=True)
    r = build_phase11_canary_acceptance_review_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.185", farm5_baseline_version="0.1.168", evidence=ev)
    assert "stratum_subscribe_ok" not in r["missing_evidence_primitives"]
    assert "stratum_authorize_ok" not in r["missing_evidence_primitives"]
