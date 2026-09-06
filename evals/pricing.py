"""Uncached standard-rate cost estimates from a run-specific price snapshot.

[Created with AI: Codex with GPT-6 Astra, Claude Code with Fable 5.1]
"""
from datetime import datetime, timezone
import hashlib
import http.client
import json
import math
import re
import urllib.request

SOURCE = 'https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json'


def fetch_snapshot(combinations):
    snapshot = {'source': SOURCE, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'basis': 'uncached standard-rate USD estimate', 'models': {}}
    try:
        with urllib.request.urlopen(SOURCE, timeout=15) as response:
            raw = response.read()
        catalog = json.loads(raw)
        if not isinstance(catalog, dict):
            raise ValueError('Pricing catalog must be an object')
        snapshot['sha256'] = hashlib.sha256(raw).hexdigest()
        for item in combinations:
            model, provider = item['model'], item['provider']
            for key in (model, provider + '/' + model):
                entry = catalog.get(key, {})
                if not isinstance(entry, dict) or entry.get('litellm_provider') != provider:
                    continue
                snapshot['models'][model] = {k: v for k, v in entry.items()
                    if k in ('input_cost_per_token', 'output_cost_per_token',
                             'output_cost_per_reasoning_token') or re.fullmatch(
                                 r'(input|output)_cost_per_token_above_\d+k_tokens', k)}
                break
    except (OSError, ValueError, http.client.HTTPException):
        snapshot['error'] = 'Pricing download failed; costs unavailable for this run'
    return snapshot


def normalize_usage(provider, usage):
    if usage is None:
        return None
    if not isinstance(usage, dict):
        usage = usage.model_dump()
    if not isinstance(usage, dict):
        return None
    if provider == 'anthropic':
        counts = [usage.get('input_tokens'), usage.get('output_tokens'),
                  usage.get('cache_read_input_tokens') or 0,
                  usage.get('cache_creation_input_tokens') or 0]
        if not all(type(n) is int and n >= 0 for n in counts):
            return None
        input_tokens, output_tokens, cached, written = counts
        return {'input_tokens': input_tokens + cached + written, 'output_tokens': output_tokens}
    input_tokens = usage.get('input_tokens', usage.get('prompt_tokens'))
    output_tokens = usage.get('output_tokens', usage.get('completion_tokens'))
    if not all(type(n) is int and n >= 0 for n in (input_tokens, output_tokens)):
        return None
    # OpenAI output_tokens already includes reasoning; do not add it again.
    return {'input_tokens': input_tokens, 'output_tokens': output_tokens}


def estimate_cost(usage, rates):
    if usage is None or not rates:
        return None
    input_rate = rates.get('input_cost_per_token')
    output_rate = rates.get('output_cost_per_token')
    if not all(type(n) in (int, float) and math.isfinite(n) and n >= 0
               for n in (input_rate, output_rate)):
        return None
    # Only standard rates are supported; do not underprice special-rate calls.
    for key in rates:
        match = re.fullmatch(r'(input|output)_cost_per_token_above_(\d+)k_tokens', key)
        if match and usage['input_tokens'] > int(match[2]) * 1000:
            return None
    if rates.get('output_cost_per_reasoning_token', output_rate) != output_rate:
        return None
    return usage['input_tokens'] * input_rate + usage['output_tokens'] * output_rate
