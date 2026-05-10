from pathlib import Path
from typer.testing import CliRunner
from mpf.interfaces.cli import app

RUNNER = CliRunner()
CONFIG_PATH = Path('configs/mpf.example.yaml')


def test_customer_show_requires_exactly_one_target():
    res = RUNNER.invoke(app, ['customer','show','--config',str(CONFIG_PATH)])
    assert res.exit_code == 1


def test_customer_show_uses_read_service(monkeypatch):
    from mpf.interfaces import cli
    class C:
        id=1; customer_key='cust_a'; lane='btc'; name='alice'; port=20001; status='active'; activation_mode='immediate'; service_days=30
        activated_at=None; starts_at=None; expires_at=None; first_connected_at=None; expired_at=None; delete_eligible_at=None; deleted_at=None
        auto_expire_enabled=False; auto_delete_enabled=False; lifecycle_note=None; miners=1; farms=1; maxconn=1; rate_per_min=1; burst=1
        ips_mode='any'; abuse_exempt=False; abuse_exempt_reason=None; abuse_exempt_until=None; abuse_exempt_by=None; enabled_ip_pins=[]
    class R: ok=True; message='OK'; customer=C()
    monkeypatch.setattr(cli.customer_read_service,'show_customer',lambda *a, **k: R())
    res=RUNNER.invoke(app,['customer','show','--config',str(CONFIG_PATH),'--customer-key','cust_a'])
    assert res.exit_code==0
    assert 'firewall_change: no' in res.output


def test_customer_list_filters_status(monkeypatch):
    from mpf.interfaces import cli
    from mpf.repositories.customer_repo import CustomerRecord
    class L: ok=True; message='OK'; customers=[CustomerRecord(1,'btc','a',1,'active',None), CustomerRecord(2,'btc','b',2,'deleted',None)]
    monkeypatch.setattr(cli.customer_read_service,'list_customer_status',lambda config, limit=100: L())
    res=RUNNER.invoke(app,['customer','list','--config',str(CONFIG_PATH),'--status','active'])
    assert res.exit_code==0 and 'status=active' in res.output and 'status=deleted' not in res.output
