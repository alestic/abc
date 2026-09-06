"""Promptfoo adapter; uses the application prompt and provider unchanged.

[Created with AI: Codex with GPT-6 Astra]
"""
import os
import re
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'abc_provider_anthropic'))

from abc_cli.prompts import get_system_prompt
from abc_cli.abc_generate import DANGER_LEVEL_PATTERN, normalize_generated_output
sys.path.insert(0, str(ROOT / 'abc_provider_openai'))


def call_api(prompt, options, context):
    config = options['config']
    case = context['vars']
    if config.get('smoke') and not case.get('behavior'):
        return {'output': case['example'], 'metadata': {'offline': True}}
    if config.get('smoke'):
        result = {'output': case['example'], 'metadata': {'offline': True}}
        add_behavior(result, case)
        return result
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
        # Empty reasoning_effort disables the provider's GPT-5 default so plain
        # model IDs use the API default effort.
        settings['reasoning_effort'] = config.get('effort', '')
        provider = OpenAIProvider(settings)
    shell_context = {'shell': case['shell'], 'os_info': case['os_info']}
    started = time.monotonic()
    output = provider.generate_command(case['description'], shell_context,
                                       get_system_prompt(shell_context))
    result = {'output': output, 'latencyMs': (time.monotonic() - started) * 1000,
              'metadata': {}}
    add_behavior(result, case)
    return result


def add_behavior(result, case):
    if case.get('behavior') == 'markdown_word' and 'output' in result:
        from evals.behavior import evaluate
        lines = normalize_generated_output(result['output']).splitlines()
        if len(lines) < 2 or not re.fullmatch(DANGER_LEVEL_PATTERN, lines[-1]):
            result['metadata']['behavior'] = {'error': 'Cannot extract command: missing danger annotation'}
            return
        command = '\n'.join(lines[:-1])
        result['metadata']['behavior'] = evaluate(command)
