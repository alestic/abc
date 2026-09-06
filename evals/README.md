# Model evaluations

Compare models using abc's providers and system prompt:

```bash
# One-time setup (.venv must exist; npm is also required).
.venv/bin/python -m pip install -e . -e ./abc_provider_anthropic -e ./abc_provider_openai

make eval MODELS="claude-sonnet-5@low claude-sonnet-5@medium gpt-6-astra@low" REPEAT=3
make eval-view
make eval-summary
```

Each `model@effort` gets its own column. Plain model IDs omit the effort
parameter and use API defaults. Effort names are provider-specific; unsupported
settings fail rather than silently falling back. Claude Haiku does not support
effort. The pilot supports Claude IDs starting `claude-` and GPT IDs starting
`gpt-`; availability depends on your API account.

Current Anthropic families (checked September 6, 2026):

```bash
make eval MODELS="claude-haiku-4-5 claude-sonnet-5@low claude-opus-5@low claude-fable-5-1@low"
```

GPT examples: `gpt-6-astra@low`, `gpt-5.6-sol@low`, `gpt-5.6-terra@low`,
`gpt-5.6-luna@low`. GPT evaluations use the application's Responses API option;
Claude uses Messages. Effort is forwarded as OpenAI `reasoning.effort` or
Anthropic `output_config.effort`. See the [Anthropic model catalog](https://platform.claude.com/docs/en/models/overview)
and [OpenAI model catalog](https://developers.openai.com/api/docs/models).

## Keys and settings

Environment keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) take priority. Otherwise,
abc's normal config discovery (`ABC_CONFIG`, XDG, or legacy path) is used.
The first section matching the provider, in file order, supplies the key.
Sections without a provider follow abc's default of Anthropic.

- Claude: override section selection with `ABC_SECTION=name`.
- GPT: override section selection with `ABC_OPENAI_SECTION=name`.

The selected section must match the provider. Only requested providers need
keys. Keys are passed through the worker environment, not written into generated
configuration or result metadata. Other personal config settings are not loaded.

`MAX_TOKENS=4096` is the eval default for every model, including reasoning and
response text. Override it explicitly for experiments that need more reasoning
room. Truncation is an error, not a successful command. Temperature is omitted.
The application defaults outside evaluations are unchanged.

Promptfoo 0.122.2 and Node.js 22.22.0 are pinned and downloaded through npx;
the pinned runtime avoids a global Node upgrade. The viewer and run history are
local, with no hosted account required. Each live run makes paid API calls:
10 cases × model/effort combinations × repeats. Response caching is disabled.
Normal `make test` does not run evaluations.

## Results

The runner prints pass counts, error counts, median response time, and p95 after
each completed run. `make eval-summary` prints the saved summary without calls.
Times cover completed provider calls, including responses that fail assertions;
API errors are counted separately. These are full-response times, not time to
first token. Small samples provide only rough latency estimates.

Results live in ignored `evals/.results/`. Live exports overwrite `latest.json`;
smoke exports use `smoke.json`. Promptfoo retains run history in its local state
directory. Metadata records source revision, dirty working tree, and smoke mode.

Automated checks apply abc's Markdown/CDATA cleanup and check the two-line
output contract, expected danger labels, and balanced Bash/zsh quoting. They do
not establish semantic correctness, full shell syntax validity, or whether the
danger label describes the actual command. Commands are never executed.

Review outputs against the case's `review` rubric in `cases.json`, including
filename handling, side effects, and shell/OS compatibility. Examples are only
for offline smoke tests, not exact-match answers, and are not sent to models.
Token usage and cost are not reported because abc's providers return only text.

## Maintenance

Add cases with description, shell, OS, accepted danger levels, review rubric,
and a smoke example. Keep checks in `checks.py` and integration in `provider.py`.

```bash
make eval-smoke MODELS="claude-sonnet-5@low gpt-6-astra@medium"
.venv/bin/python -m pytest evals/
```

Smoke tests use fixed responses without model calls or credentials. They test
the framework integration, not model quality or API account access. Mocked
request tests verify provider selection, credential selection, and effort wiring.

[Created with AI: Codex with GPT-6 Astra]
