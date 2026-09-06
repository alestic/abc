"""Summarize saved Promptfoo results without model calls.

[Created with AI: Codex with GPT-6 Astra]
"""
from collections import defaultdict
import json
import math
from pathlib import Path
import statistics


def print_summary(path):
    data = json.loads(Path(path).read_text())
    groups = defaultdict(list)
    for row in data['results']['results']:
        groups[row['provider']['label']].append(row)
    print('\nModel/effort                         Passed    Errors    Median     p95    Uncached $/call    Est. total $')
    for label, rows in sorted(groups.items()):
        # Include completed responses whether their assertions pass or fail.
        timings = sorted(row['latencyMs'] / 1000 for row in rows
                         if isinstance(row.get('response', {}).get('output'), str)
                         and isinstance(row.get('latencyMs'), (int, float)))
        median = '{:.2f}s'.format(statistics.median(timings)) if timings else '-'
        p95 = '{:.2f}s'.format(timings[math.ceil(len(timings) * .95) - 1]) if timings else '-'
        passed = sum(bool(row.get('success')) for row in rows)
        errors = sum(not isinstance(row.get('response', {}).get('output'), str) for row in rows)
        costs = [row.get('response', {}).get('metadata', {}).get('uncachedCostUsd') for row in rows]
        complete = all(type(cost) in (int, float) for cost in costs)
        average = '{:.6f}'.format(statistics.mean(costs)) if complete else 'unknown'
        total = '{:.6f}'.format(sum(costs)) if complete else 'unknown'
        print('{:<36} {:>3}/{:<3} {:>7} {:>10} {:>8} {:>18} {:>15}'.format(
            label, passed, len(rows), errors, median, p95, average, total))
    print('Times cover completed responses, including assertion failures; scores require manual correctness review.')
    print('Cost estimates use full input/output rates without cache discounts, including reasoning tokens.')
    print('Unknown means pricing or usage is missing for at least one call; not an actual bill or retry total.')
    for label, rows in sorted(groups.items()):
        checks = defaultdict(list)
        for row in rows:
            for check in (row.get('gradingResult') or {}).get('componentResults', []):
                name = (check.get('assertion') or {}).get('metric')
                if name:
                    checks[name].append(bool(check['pass']))
        if checks:
            print(label + ': ' + ', '.join('{} {}/{}'.format(name, sum(values), len(values))
                                           for name, values in sorted(checks.items())))


if __name__ == '__main__':
    print_summary(Path(__file__).resolve().parent / '.results' / 'latest.json')
