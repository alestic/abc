"""Run local Promptfoo comparisons using abc's providers.

[Created with AI: Codex with GPT-6 Astra]
"""
import argparse
import configparser
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from abc_cli.abc_generate import get_config, get_config_file
from evals.pricing import fetch_snapshot
PROMPTFOO = ['npx', '--yes', '--package=node@22.22.0',
             '--package=promptfoo@0.122.2', 'promptfoo']


def parse_model(value):
    model, separator, effort = value.partition('@')
    if model.startswith('claude-'):
        provider = 'anthropic'
        allowed = {'low', 'medium', 'high', 'xhigh', 'max'}
        if 'haiku' in model:
            allowed = set()
    elif model.startswith('gpt-'):
        provider = 'openai'
        allowed = {'none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max'}
        if model.startswith('gpt-6'):
            allowed -= {'none', 'minimal'}
    else:
        raise ValueError('Expected a claude- or gpt- model ID: ' + value)
    if separator and effort not in allowed:
        raise ValueError('Unsupported effort for ' + value)
    config = {'model': model, 'provider': provider}
    if separator:
        config['effort'] = effort
    return config


def get_api_key(provider='anthropic'):
    variable = 'ANTHROPIC_API_KEY' if provider == 'anthropic' else 'OPENAI_API_KEY'
    if os.environ.get(variable):
        return os.environ[variable]
    section = (os.environ.get('ABC_SECTION') if provider == 'anthropic'
               else os.environ.get('ABC_OPENAI_SECTION'))
    path = get_config_file()
    if section:
        config = get_config(path, section)
    else:
        sections = configparser.ConfigParser()
        with open(path) as source:
            sections.read_file(source)
        config = next((dict(sections[name]) for name in sections.sections()
                       if sections[name].get('provider', 'anthropic') == provider), None)
        if config is None:
            raise ValueError('No config section matches ' + provider)
    if config.get('provider', 'anthropic') != provider:
        raise ValueError('Selected config section has the wrong provider')
    if not config.get('api_key', '').strip():
        raise ValueError('Selected config section has no api_key')
    return config['api_key']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['eval', 'view'])
    parser.add_argument('--smoke', action='store_true', help='Use fixed responses without API calls')
    args = parser.parse_args()
    env = dict(os.environ, PROMPTFOO_PYTHON=sys.executable,
               PROMPTFOO_CONFIG_DIR=str(ROOT / '.results' / 'state'),
               PROMPTFOO_DISABLE_TELEMETRY='1')
    if args.action == 'view':
        return subprocess.call(PROMPTFOO + ['view'], cwd=ROOT, env=env)
    models = os.environ.get('MODELS', 'claude-opus-4-5 claude-sonnet-5').split()
    try:
        repeat = int(os.environ.get('REPEAT', '1'))
        max_tokens = int(os.environ.get('MAX_TOKENS', '4096'))
        combinations = [parse_model(model) for model in models]
    except ValueError as error:
        parser.error(str(error))
    if max_tokens < 1:
        parser.error('MAX_TOKENS must be positive')
    if not models or repeat < 1:
        parser.error('MODELS must be nonempty and REPEAT must be positive')
    if len(set(models)) != len(models):
        parser.error('MODELS must not repeat an entry; use REPEAT to measure run-to-run variance')
    cases = json.loads((ROOT / 'cases.json').read_text())
    selected = os.environ.get('CASES', '').split()
    if selected:
        names = {case['description'] for case in cases['tests']}
        if set(selected) - names:
            parser.error('Unknown CASES: ' + ', '.join(sorted(set(selected) - names)))
        cases['tests'] = [case for case in cases['tests'] if case['description'] in selected]
    if any(case['vars'].get('behavior') for case in cases['tests']):
        from evals.behavior import check_available
        try:
            check_available()
        except ValueError as error:
            parser.error(str(error))
    if not args.smoke:
        for provider in sorted({item['provider'] for item in combinations}):
            try:
                env[provider.upper() + '_API_KEY'] = get_api_key(provider)
            except (OSError, configparser.Error, ValueError):
                parser.error('Could not load ' + provider + ' key. Check abc config sections '
                             'or set ' + provider.upper() + '_API_KEY.')
    results = ROOT / '.results'
    results.mkdir(exist_ok=True)
    pricing = {'models': {}, 'basis': 'offline smoke; no cost estimate'}
    if not args.smoke:
        pricing = fetch_snapshot(combinations)
        snapshot_path = results / ('pricing-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
        snapshot_path.write_text(json.dumps(pricing, indent=2) + '\n')
        missing = sorted({item['model'] for item in combinations} - pricing['models'].keys())
        if missing:
            print('Pricing unavailable for: ' + ', '.join(missing), file=sys.stderr)
    for case in cases['tests']:
        if case['vars'].get('behavior'):
            case['assert'] = [{'type': 'python', 'metric': 'Word ' + name,
                              'value': 'file://' + str(ROOT / 'checks.py') + ':behavior_check',
                              'config': {'check': name}}
                             for name in ('scope', 'counting', 'selection', 'empty', 'no_candidate', 'read_only')]
    config = {
        'description': 'abc model comparison: automated checks plus manual correctness review',
        'metadata': {'sourceRevision': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'workingTreeDirty': bool(subprocess.check_output(
                ['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()),
            'offlineSmoke': args.smoke, 'pricing': pricing},
        'prompts': ['{{description}}'],
        'providers': [{'id': 'file://' + str(ROOT / 'provider.py'), 'label': model,
                       'config': dict(combination, smoke=args.smoke, max_tokens=max_tokens,
                                      pricing=pricing['models'].get(combination['model']))}
                      for model, combination in zip(models, combinations)],
        'tests': cases['tests'],
        'defaultTest': {'assert': [{'type': 'python', 'metric': name,
                                   'value': 'file://' + str(ROOT / 'checks.py') + ':' + function}
                                  for name, function in [('Format', 'format_check'),
                                                         ('Danger', 'danger_check'),
                                                         ('Quoting', 'quoting_check')]]},
    }
    results = ROOT / '.results'
    results.mkdir(exist_ok=True)
    config_path = results / 'config.json'
    config_path.write_text(json.dumps(config, indent=2) + '\n')
    print('{} cases × {} models × {} repeats = {} calls{}'.format(
        len(cases['tests']), len(models), repeat, len(cases['tests']) * len(models) * repeat,
        ' (offline smoke)' if args.smoke else ''), flush=True)
    status = subprocess.call(PROMPTFOO + ['eval', '-c', str(config_path), '--no-cache',
                           '--repeat', str(repeat), '--max-concurrency', '2',
                           '--output', str(results / ('smoke.json' if args.smoke else 'latest.json'))], cwd=ROOT, env=env)
    if status in (0, 100):
        from summary import print_summary
        print_summary(results / ('smoke.json' if args.smoke else 'latest.json'))
    return status


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
