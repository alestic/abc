"""Model selection, credentials, and API parameter regression tests.

[Created with AI: Codex with GPT-6 Astra]
"""
import json
from unittest.mock import Mock, patch
import pytest
from evals.run import get_api_key, parse_model
from evals.provider import call_api


@pytest.mark.parametrize('value,provider,effort', [
    ('claude-haiku-4-5', 'anthropic', None),
    ('claude-sonnet-5@low', 'anthropic', 'low'),
    ('claude-sonnet-5@medium', 'anthropic', 'medium'),
    ('gpt-6-astra@low', 'openai', 'low'),
])
def test_combinations(value, provider, effort):
    config = parse_model(value)
    assert config['provider'] == provider
    assert config.get('effort') == effort
    assert '@' not in config['model']


@pytest.mark.parametrize('value', ['claude-haiku-4-5@low', 'gpt-6-astra@none',
                                  'claude-sonnet-5@', 'claude-sonnet-5@bogus', 'bogus'])
def test_invalid_combinations(value):
    with pytest.raises(ValueError):
        parse_model(value)


def test_provider_credentials(tmp_path, monkeypatch):
    config = tmp_path / 'config'
    config.write_text('[default]\nprovider=anthropic\napi_key=fake-claude\n'
                      '[gpt]\nprovider=openai\napi_key=fake-gpt\n')
    monkeypatch.setenv('ABC_CONFIG', str(config))
    monkeypatch.setenv('ABC_SECTION', 'default')
    monkeypatch.setenv('ABC_OPENAI_SECTION', 'gpt')
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    assert get_api_key('anthropic') == 'fake-claude'
    assert get_api_key('openai') == 'fake-gpt'
    monkeypatch.setenv('OPENAI_API_KEY', 'override')
    assert get_api_key('openai') == 'override'
    monkeypatch.delenv('OPENAI_API_KEY')
    monkeypatch.setenv('ABC_OPENAI_SECTION', 'default')
    with pytest.raises(ValueError):
        get_api_key('openai')


@pytest.mark.parametrize('value', ['claude-sonnet-5@low', 'gpt-6-astra@medium', 'gpt-5.6-sol'])
def test_adapter_request(value, monkeypatch):
    config = dict(parse_model(value), max_tokens=4096)
    monkeypatch.setenv(config['provider'].upper() + '_API_KEY', 'fake-key')
    case = {'description': 'List files', 'shell': 'bash', 'os_info': 'Ubuntu Linux'}
    target = 'anthropic.Anthropic' if config['provider'] == 'anthropic' else 'openai.OpenAI'
    with patch(target) as client:
        if config['provider'] == 'anthropic':
            create = client.return_value.messages.create
            create.return_value = Mock(stop_reason='end_turn', content=[Mock(type='text', text='ls')])
        else:
            create = client.return_value.responses.create
            create.return_value = Mock(status='completed', output_text='ls')
        result = call_api('ignored', {'config': config}, {'vars': case})
        assert result['output'] == 'ls'
        assert result['latencyMs'] >= 0
        kwargs = create.call_args.kwargs
        assert kwargs['model'] == config['model']
        assert 'temperature' not in kwargs
        if config['provider'] == 'anthropic':
            assert kwargs['output_config'] == {'effort': 'low'}
        elif config.get('effort'):
            assert kwargs['reasoning'] == {'effort': config['effort']}
        else:
            assert 'reasoning' not in kwargs


@pytest.mark.parametrize('status,text', [('incomplete', 'partial'), ('completed', '')])
def test_openai_rejects_unusable_responses(status, text):
    from abc_provider_openai.llm_provider import OpenAIProvider
    with patch('openai.OpenAI') as client:
        client.return_value.responses.create.return_value = Mock(status=status, output_text=text)
        provider = OpenAIProvider({'provider':'openai', 'api_key':'fake', 'api':'responses'})
        with pytest.raises(ValueError):
            provider.generate_command('test', {}, 'system')


def test_first_matching_section(tmp_path, monkeypatch):
    config = tmp_path / 'config'
    config.write_text('[first-gpt]\nprovider=openai\napi_key=gpt-first\n'
                      '[implicit-claude]\napi_key=claude-first\n'
                      '[second-gpt]\nprovider=openai\napi_key=gpt-second\n'
                      '[second-claude]\nprovider=anthropic\napi_key=claude-second\n')
    monkeypatch.setenv('ABC_CONFIG', str(config))
    for key in ('ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'ABC_SECTION', 'ABC_OPENAI_SECTION'):
        monkeypatch.delenv(key, raising=False)
    assert get_api_key('openai') == 'gpt-first'
    assert get_api_key('anthropic') == 'claude-second'
    monkeypatch.setenv('ABC_OPENAI_SECTION', '')
    assert get_api_key('openai') == 'gpt-first'
    monkeypatch.setenv('ABC_OPENAI_SECTION', 'second-gpt')
    assert get_api_key('openai') == 'gpt-second'
