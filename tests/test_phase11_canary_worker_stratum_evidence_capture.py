from pathlib import Path
from typer.testing import CliRunner

from mpf.config import load_config
from mpf.interfaces.cli import app
from mpf.services import customer_read_service
from mpf.services.customer_read_service import CustomerRecord
from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence, build_phase11_canary_visibility_bundle_report
from mpf.services import phase11_canary_worker_stratum_evidence_capture_service as svc


def _cfg():
    return load_config(Path("configs/mpf.example.yaml"))


def _fake_socket(payloads: list[bytes]):
    class F:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def settimeout(self, x): pass
        def sendall(self, x): pass
        def recv(self, n):
            if not hasattr(self, 'buf'):
                self.buf = b"".join(payloads)
            if not self.buf:
                return b""
            b = self.buf[:1]
            self.buf = self.buf[1:]
            return b
    return F()


def test_subscribe_failure_keeps_worker_visibility_false(monkeypatch):
    monkeypatch.setattr("socket.create_connection", lambda *a, **k: _fake_socket([b'{"id":1,"result":null,"error":"x"}\n']))
    r = svc.build_phase11_canary_worker_stratum_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.188", farm5_baseline_version="0.1.168", connect_host="85.198.11.110", connect_port=20001, worker_name="canary-btc-001.worker-001", collect_live=False)
    assert r["worker_evidence"]["worker_visibility_ok"] is False


def test_authorize_failure_keeps_worker_visibility_false(monkeypatch):
    monkeypatch.setattr("socket.create_connection", lambda *a, **k: _fake_socket([b'{"id":1,"result":[1],"error":null}\n', b'{"id":2,"result":false,"error":null}\n']))
    r = svc.build_phase11_canary_worker_stratum_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.188", farm5_baseline_version="0.1.168", connect_host="85.198.11.110", connect_port=20001, worker_name="canary-btc-001.worker-001", collect_live=False)
    assert r["worker_evidence"]["worker_visibility_ok"] is False


def test_capture_ready_blocked_when_blockers_exist(monkeypatch):
    monkeypatch.setattr("socket.create_connection", lambda *a, **k: _fake_socket([b'{"id":1,"result":[1],"error":null}\n', b'{"id":2,"result":true,"error":null}\n']))
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[]))
    r = svc.build_phase11_canary_worker_stratum_evidence_capture_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.188", farm5_baseline_version="0.1.168", connect_host="85.198.11.110", connect_port=20001, worker_name="canary-btc-001.worker-001", collect_live=False)
    assert r["worker_evidence"]["worker_visibility_ok"] is True
    assert r["final_decision"] == "BLOCKED"


def test_worker_visibility_true_without_reference_not_lifted():
    ev = Phase11CanaryVisibilityEvidence(customer_key="canary-btc-001", lane="btc", port=20001, evidence_source="live_source_backed_canary_worker_stratum", worker_visibility_ok=True, worker_reference=None)
    r = build_phase11_canary_visibility_bundle_report(_cfg(), customer_key="canary-btc-001", lane="btc", port=20001, expected_version="0.1.188", farm5_baseline_version="0.1.168", evidence=ev)
    assert r["visibility"]["unique_workers_visibility"]["status"] == "MISSING"


def test_cli_collect_visibility_propagates_runtime_evidence(monkeypatch, tmp_path):
    runner = CliRunner()
    c = CustomerRecord(id=1, customer_key="canary-btc-001", name="x", lane="btc", port=20001, status="active", activation_mode=None, expires_at=None, deleted_at=None)
    monkeypatch.setattr("mpf.services.customer_read_service.list_customer_status", lambda *a, **k: customer_read_service.CustomerList(ok=True, message="ok", customers=[c]))
    usage = tmp_path / "usage.json"
    usage.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"usage_visibility_ok":true,"usage_reference":"usage-ref"}', encoding="utf-8")
    sess = tmp_path / "sess.json"
    sess.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"session_visibility_ok":true,"session_reference":"session-ref","unique_ip_visibility_ok":true,"unique_ip_reference":"ip-ref"}', encoding="utf-8")
    reject = tmp_path / "reject.json"
    reject.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"evidence_source":"live_source_backed_canary_reject_counters","reject_visibility_ok":true,"reject_reference":"reject-ref"}', encoding="utf-8")
    worker = tmp_path / "worker.json"
    worker.write_text('{"customer_key":"canary-btc-001","lane":"btc","port":20001,"evidence_source":"live_source_backed_canary_worker_stratum","worker_visibility_ok":true,"worker_reference":"live_canary_worker_stratum:canary-btc-001:btc:20001:abc","stratum_subscribe_ok":true,"stratum_authorize_ok":true}', encoding="utf-8")
    res = runner.invoke(app, ["production","canary-acceptance-review","--expected-version","0.1.188","--farm5-baseline-version","0.1.168","--collect-visibility","--visibility-json",str(usage),"--visibility-json",str(sess),"--visibility-json",str(reject),"--visibility-json",str(worker),"--output","json","--config","configs/mpf.example.yaml"])
    assert res.exit_code == 0
    out = res.stdout
    assert '"missing_visibility:unique_workers_visibility"' not in out
    assert '"missing_evidence:stratum_subscribe_ok"' not in out
    assert '"missing_evidence:stratum_authorize_ok"' not in out
    assert '"missing_evidence:stratum_notify_seen"' in out
    assert '"missing_evidence:stratum_set_difficulty_seen"' in out
    assert '"missing_evidence:forwarder_pool_seen"' in out
    assert '"missing_evidence:bridge_loopback_seen"' in out
    assert '"final_decision": "BLOCKED"' in out
