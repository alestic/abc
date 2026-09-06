"""Cost calculations must not discount cached input or double-count reasoning.

[Created with AI: Codex with GPT-6 Astra, Claude Code with Fable 5.1]
"""
import http.client
import io
import json
from unittest.mock import patch
import pytest
from evals.pricing import normalize_usage, estimate_cost, fetch_snapshot

RATES = {'input_cost_per_token': 2e-6, 'output_cost_per_token': 10e-6}


def test_anthropic_cache_tokens_at_full_price():
    usage = normalize_usage('anthropic', {'input_tokens': 100, 'output_tokens': 50,
                            'cache_read_input_tokens': 200, 'cache_creation_input_tokens': 300})
    assert usage['input_tokens'] == 600
    assert estimate_cost(usage, RATES) == pytest.approx(.0017)


def test_openai_reasoning_included_once():
    usage = normalize_usage('openai', {'input_tokens': 1000, 'output_tokens': 100,
        'input_tokens_details': {'cached_tokens': 900},
        'output_tokens_details': {'reasoning_tokens': 80}})
    assert estimate_cost(usage, RATES) == pytest.approx(.003)


def test_missing_usage_and_prices_unknown():
    assert normalize_usage('openai', None) is None
    assert estimate_cost(None, RATES) is None
    assert estimate_cost({'input_tokens': 20, 'output_tokens': 10}, {}) is None


def test_long_context_tier():
    rates = dict(RATES, input_cost_per_token_above_272k_tokens=4e-6,
                 output_cost_per_token_above_272k_tokens=15e-6)
    assert estimate_cost({'input_tokens': 300000, 'output_tokens': 100}, rates) == pytest.approx(1.2015)


def test_snapshot_provider_match_and_failure():
    catalog = {'claude-test': dict(RATES, litellm_provider='anthropic'),
               'gpt-test': dict(RATES, litellm_provider='some-other-provider')}
    models = [{'model':'claude-test', 'provider':'anthropic'}, {'model':'gpt-test', 'provider':'openai'}]
    with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(catalog).encode())):
        snapshot = fetch_snapshot(models)
    assert snapshot['models'] == {'claude-test': RATES}
    assert snapshot['sha256'] and snapshot['retrieved_at']
    for failure in (OSError(), http.client.IncompleteRead(b'')):
        with patch('urllib.request.urlopen', side_effect=failure):
            failed = fetch_snapshot(models)
        assert failed['models'] == {} and failed['error']


@pytest.mark.parametrize('provider,failed', [('anthropic', False), ('openai', False), ('openai', True)])
def test_adapter_keeps_usage_and_cost_on_responses(provider, failed, monkeypatch):
    from unittest.mock import Mock
    from evals.provider import call_api
    monkeypatch.setenv(provider.upper() + '_API_KEY', 'fake')
    target = 'anthropic.Anthropic' if provider == 'anthropic' else 'openai.OpenAI'
    usage = {'input_tokens': 100, 'output_tokens': 50}
    with patch(target) as client:
        if provider == 'anthropic':
            client.return_value.messages.create.return_value = Mock(
                usage=usage, stop_reason='end_turn', content=[Mock(type='text', text='ls')])
        else:
            client.return_value.responses.create.return_value = Mock(
                usage=usage, status='incomplete' if failed else 'completed', output_text='ls')
        result = call_api('', {'config': {'provider':provider, 'model':'test', 'max_tokens':4096,
                                          'pricing':RATES}},
                          {'vars': {'description':'List files', 'shell':'bash', 'os_info':'Linux'}})
    assert result['metadata']['uncachedCostUsd'] == pytest.approx(.0007)
    assert result['tokenUsage']['total'] == 150
    assert ('error' in result) == failed
