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
    details = usage.get('output_tokens_details') or usage.get('completion_tokens_details') or {}
    reasoning = details.get('reasoning_tokens')
    result = {'input_tokens': input_tokens, 'output_tokens': output_tokens}
    if type(reasoning) is int and 0 <= reasoning <= output_tokens:
        result['reasoning_tokens'] = reasoning
    return result


def estimate_cost(usage, rates):
    if usage is None or not rates:
        return None
    def rate(kind):
        value = rates.get(kind + '_cost_per_token')
        thresholds = []
        for key, tier in rates.items():
            match = re.fullmatch(kind + r'_cost_per_token_above_(\d+)k_tokens', key)
            if match and usage['input_tokens'] > int(match[1]) * 1000:
                thresholds.append((int(match[1]), tier))
        if thresholds:
            value = max(thresholds)[1]
        return value
    input_rate, output_rate = rate('input'), rate('output')
    if not all(type(n) in (int, float) and math.isfinite(n) and n >= 0
               for n in (input_rate, output_rate)):
        return None
    cost = usage['input_tokens'] * input_rate + usage['output_tokens'] * output_rate
    reasoning_rate = rates.get('output_cost_per_reasoning_token')
    if reasoning_rate is not None and reasoning_rate != output_rate:
        if ('reasoning_tokens' not in usage or type(reasoning_rate) not in (int, float)
                or not math.isfinite(reasoning_rate) or reasoning_rate < 0):
            return None
        cost += usage['reasoning_tokens'] * (reasoning_rate - output_rate)
    return cost
