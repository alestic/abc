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
    print('\nModel/effort                         Passed    Errors    Median     p95')
    for label, rows in sorted(groups.items()):
        # Include completed responses whether their assertions pass or fail.
        timings = sorted(row['latencyMs'] / 1000 for row in rows
                         if isinstance(row.get('response', {}).get('output'), str)
                         and isinstance(row.get('latencyMs'), (int, float)))
        median = '{:.2f}s'.format(statistics.median(timings)) if timings else '-'
        p95 = '{:.2f}s'.format(timings[math.ceil(len(timings) * .95) - 1]) if timings else '-'
        passed = sum(bool(row.get('success')) for row in rows)
        errors = sum(not isinstance(row.get('response', {}).get('output'), str) for row in rows)
        print('{:<36} {:>3}/{:<3} {:>7} {:>10} {:>8}'.format(
            label, passed, len(rows), errors, median, p95))
    print('Times cover completed responses, including assertion failures; scores require manual correctness review.')


if __name__ == '__main__':
    print_summary(Path(__file__).resolve().parent / '.results' / 'latest.json')
