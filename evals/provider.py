"""Promptfoo adapter; uses the application prompt and provider unchanged.

[Created with AI: Codex with GPT-6 Astra]
"""
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'abc_provider_anthropic'))

from abc_cli.prompts import get_system_prompt
sys.path.insert(0, str(ROOT / 'abc_provider_openai'))


def call_api(prompt, options, context):
    config = options['config']
    case = context['vars']
    if config.get('smoke'):
        return {'output': case['example'], 'metadata': {'offline': True}}
    name = config['provider']
    settings = {'provider': name, 'api_key': os.environ[name.upper() + '_API_KEY'],
                'model': config['model'], 'max_tokens': str(config['max_tokens'])}
    if name == 'anthropic':
        from abc_provider_anthropic.llm_provider import AnthropicProvider
        if config.get('effort'):
            settings['effort'] = config['effort']
        provider = AnthropicProvider(settings)
    else:
        from abc_provider_openai.llm_provider import OpenAIProvider
        settings['api'] = 'responses'
        if config.get('effort'):
            settings['reasoning_effort'] = config['effort']
        provider = OpenAIProvider(settings)
    shell_context = {'shell': case['shell'], 'os_info': case['os_info']}
    started = time.monotonic()
    output = provider.generate_command(case['description'], shell_context,
                                       get_system_prompt(shell_context))
    return {'output': output, 'latencyMs': (time.monotonic() - started) * 1000}
