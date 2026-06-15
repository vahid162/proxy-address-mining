from mpf.services.phase11_controlled_artifact_reapply_rollback_executor_service import build_exact_inverse_payload, execute_reviewed_rollback

class Runner:
    production_ready = True
    def __init__(self):
        self.calls=[]
    def run(self, argv, input_text=None):
        self.calls.append((argv, input_text))
        from mpf.services.phase11_controlled_artifact_reapply_core import CommandResult
        return CommandResult(0, '', '')

def _pkg():
    return {
        'repository_version': '0.1.267',
        'rollback_plan': {
            'manual_review_required': True,
            'exact_inverse_delta': [
                {'table':'filter','exact_rule_text':'-N MPFC_20001','dependency_order':0},
                {'table':'filter','exact_rule_text':'-A MPFC_20001 -p tcp --dport 60010 -j REJECT','dependency_order':1},
                {'table':'nat','exact_rule_text':'-A MPF_NAT_PRE -p tcp --dport 20001 -j DNAT --to-destination 172.18.0.2:60010','dependency_order':2},
            ]
        }
    }

def test_rollback_executor_builds_exact_inverse_in_dependency_reverse_order():
    payload, blockers = build_exact_inverse_payload(_pkg()['rollback_plan'])
    assert blockers == []
    assert payload.index('-D MPF_NAT_PRE') < payload.index('-D MPFC_20001') < payload.index('-X MPFC_20001')


def test_rollback_executor_test_only_does_not_mutate():
    runner=Runner()
    r=execute_reviewed_rollback(package=_pkg(), operator='op', reason='review', runner=runner)
    assert r['final_decision']=='CONTROLLED_ARTIFACT_REAPPLY_ROLLBACK_TEST_READY'
    assert r['firewall_mutation_performed'] is False
    assert [c[0] for c in runner.calls] == [['iptables-restore','--test','--noflush']]


def test_rollback_executor_apply_requires_env_gate_and_yes():
    runner=Runner()
    r=execute_reviewed_rollback(package=_pkg(), operator='op', reason='review', runner=runner, apply=True, yes=False, env={})
    assert r['final_decision']=='BLOCKED_CONTROLLED_ARTIFACT_REAPPLY_ROLLBACK'
    assert runner.calls == []


def test_rollback_executor_apply_runs_test_then_apply_with_gate():
    runner=Runner()
    r=execute_reviewed_rollback(package=_pkg(), operator='op', reason='review', runner=runner, apply=True, yes=True, env={'MPF_PHASE11_CONTROLLED_ARTIFACT_ROLLBACK':'allow'})
    assert r['final_decision']=='CONTROLLED_ARTIFACT_REAPPLY_ROLLBACK_APPLIED_PENDING_REVIEW'
    assert [c[0] for c in runner.calls] == [['iptables-restore','--test','--noflush'], ['iptables-restore','--noflush']]


def test_rollback_executor_refuses_broad_restore():
    pkg=_pkg(); pkg['rollback_plan']['restore_payload']='*filter\nCOMMIT\n'
    payload, blockers = build_exact_inverse_payload(pkg['rollback_plan'])
    assert 'broad_restore_refused' in blockers
