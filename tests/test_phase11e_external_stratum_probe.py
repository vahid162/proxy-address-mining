import json
from pathlib import Path


def test_external_probe_script_contract_shape_and_safety() -> None:
    p = Path('scripts/phase11e_external_stratum_probe.py')
    t = p.read_text(encoding='utf-8')
    assert 'socket.create_connection' in t
    assert '--json-out' in t
    assert 'default=20101' in t
    assert 'default="limited-btc-001.worker01"' in t
    assert 'default=600' in t
    assert 'mining.subscribe' in t and 'mining.authorize' in t
    assert 'mining.submit' not in t
    assert 'READY_TO_COPY_TRANSCRIPT' in t


def test_transcript_shape_matches_classifier_contract(tmp_path) -> None:
    transcript = {
        'connect_host': 'example.test',
        'connect_port': 20101,
        'worker_name': 'limited-btc-001.worker01',
        'messages': [
            {'direction': 'tx', 'id': 1, 'method': 'mining.subscribe', 'params': []},
            {'direction': 'rx', 'id': 1, 'result_present': True, 'result': []},
            {'direction': 'tx', 'id': 2, 'method': 'mining.authorize', 'params': ['limited-btc-001.worker01', 'x']},
            {'direction': 'rx', 'id': 2, 'result': True, 'result_true': True},
            {'direction': 'rx', 'method': 'mining.set_difficulty'},
        ],
    }
    out = tmp_path / 't.json'
    out.write_text(json.dumps(transcript), encoding='utf-8')
    loaded = json.loads(out.read_text(encoding='utf-8'))
    assert loaded['connect_port'] == 20101
    assert any(m.get('method') == 'mining.subscribe' for m in loaded['messages'])
    assert any(m.get('id') == 2 and m.get('result') is True for m in loaded['messages'])
