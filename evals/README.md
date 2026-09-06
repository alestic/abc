# Model evaluations

Compare models using abc's providers and system prompt:

```bash
# One-time setup (.venv must exist; npm is also required).
.venv/bin/python -m pip install -e . -e ./abc_provider_anthropic -e ./abc_provider_openai
make eval-image # Requires Docker; builds the command fixture image once.

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
11 cases × model/effort combinations × repeats. Response caching is disabled.
Normal `make test` does not run evaluations. Run offline evaluator regression tests
with `.venv/bin/python -m pytest evals/`; these make no model calls and skip Docker
integration tests unless explicitly enabled.

## Results

The runner prints pass counts, error counts, median response time, p95, and
estimated uncached USD cost per call and total after
each completed run. `make eval-summary` prints the saved summary without calls.
Times cover completed provider calls, including responses that fail assertions;
API errors are counted separately. These are full-response times, not time to
first token. Small samples provide only rough latency estimates.

Results live in ignored `evals/.results/`. Live exports overwrite `latest.json`;
smoke exports use `smoke.json`. Promptfoo retains run history in its local state
directory. Metadata records source revision, dirty working tree, and smoke mode.

Every response gets independent named pass/fail checks for Format, Danger,
and Quoting after abc's Markdown/CDATA cleanup. For Bash, Quoting runs `bash -n`
with startup environment variables removed: it checks shell syntax without
executing the generated command. Zsh retains a limited `shlex` quoting check;
tcsh syntax is not validated. The summary also prints pass counts for each check.
A response passes overall only when all its checks pass.
The runner sets an aggregate threshold of 1 and always supplies a nonempty
failure reason, avoiding a false pass in the pinned Promptfoo version. Summaries
also reject saved rows with failed component assertions even if their aggregate
success flag is true. Existing saved results are not regraded or rewritten.
These checks do not establish semantic correctness or whether the danger label
describes the actual command.

The `markdown-word` case adds nine behavioral checks: repository scope, per-file
counting, closest-to-50% selection, empty input, no qualifying word, empty files,
sparse frequencies (20%), unusual filenames (including newlines and leading
hyphens), and read-only behavior. One model response is reused across all checks;
assertions do not make additional model calls. Its command runs against tiny disposable Git
repositories in a resource-limited Docker container, with no network, credentials,
or working repository mounted. The image uses `strace` to detect filesystem
mutations and write-capable opens, including temporary files removed before the
final snapshot. Failed syscalls and opening `/dev/null` for output are allowed.
This is a conservative write-intent check, not a complete side-effect audit
(for example, shell variable changes are not checked).
Rebuild with `make eval-image` to install the version 2 image.
The grader accepts explanatory text around a single selected fixture word, but
rejects lists of competing fixture words. Reported fractions and percentages
must match the fixture.
Other cases do not execute generated commands.
Fixtures catch specific mistakes; readability and broader correctness still need
manual review. Reported live response times exclude fixture execution.

To run just this case:

```bash
make eval CASES=markdown-word MODELS="gpt-6-astra@low claude-sonnet-5@low" REPEAT=3
```

`CASES` accepts space-separated case names; omit it to run all cases. Docker and
the fixture image are checked before any model calls when this case is selected.

Review outputs against the case's `review` rubric in `cases.json`, including
filename handling, side effects, and shell/OS compatibility. Examples are only
for offline smoke tests, not exact-match answers, and are not sent to models.
Input/output token counts and uncached cost estimates are saved with each
response. Reasoning tokens are included in output usage, not added twice.
All cached input is priced at the normal input rate to represent infrequent
abc usage. Estimates are not actual billed costs; retries and account-specific
discounts are not included. A model's cost summary is unknown if any call lacks
pricing or usage, rather than silently reporting a partial total.

Each live run downloads the [LiteLLM pricing catalog](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json)
once. Selected rates, source URL, retrieval time, and catalog hash are saved in
a timestamped `pricing-*.json` file and embedded in the run metadata. Prices
are standard rates with no caching, batch, or priority adjustment. This
third-party catalog may lag official pricing. Missing prices or a failed
download leave cost unknown while evaluations continue. Smoke tests do not
download pricing. Earlier results without token usage cannot be costed retroactively.

## Maintenance

Add cases with description, shell, OS, accepted danger levels, review rubric,
and a smoke example. Keep checks in `checks.py` and integration in `provider.py`.

```bash
make eval-smoke MODELS="claude-sonnet-5@low gpt-6-astra@medium"
.venv/bin/python -m pytest evals/
ABC_EVAL_DOCKER_TESTS=1 .venv/bin/python -m pytest evals/test_behavior.py
```

Smoke tests use fixed responses without model calls or credentials. They test
the framework integration, including Docker fixtures when selected, not model
quality or API account access. Docker tests are opt-in in pytest. Mocked
request tests verify provider selection, credential selection, and effort wiring.

[Created with AI: Codex with GPT-6 Astra]
