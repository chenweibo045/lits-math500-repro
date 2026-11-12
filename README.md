# Reproducing LiTS (MCTS Tree Search) on MATH500 — FTEC5660 Reproducibility Work

Reproducibility study of **LiTS: A Modular Framework for LLM Tree Search**
(X. Li & Y. Tao, ACL 2026 System Demonstrations, [arXiv:2603.00631](https://arxiv.org/abs/2603.00631);
code: [xinzhel/lits-llm](https://github.com/xinzhel/lits-llm), Apache-2.0).
Instructor project list, **Tier A, No. 3**.

- Full report: [`report/Reproducibility_Report.md`](report/Reproducibility_Report.md) (PDF generated from the same source with `report/md2pdf.py`).
- Slides + 15-minute speaking script: [`presentation/`](presentation/).

## What is reproduced

- **Target claim (paper Table 6):** ReST-MCTS* (MCTS + ConcatPolicy / ConcatTransition / GenerativePRM)
  on MATH500, n_iters=10, n_actions=3 — tree search improves over the CoT chain baseline
  (paper: ReST-MCTS* 37%, ToT-BFS 39%, RAP 18%, CoT 17% on the first 100 examples with Llama3-8B-Instruct).
- **Scope of this reproduction:** the first 20 MATH500 examples of the repo's registered loader
  (`xinzhel/math500-float`), **1 completed trial per arm** (3 were planned; trials 2–3 were cancelled
  to meet the time budget — a stated limitation, per-example results are reported instead).
- **Controlled variable (permitted model swap):** the paper's Llama3-8B is replaced by
  `kimi-k2-0905-preview` served through an OpenAI-compatible gateway (assignment permits DeepSeek
  "or another accessible model"). All numbers are therefore **not directly comparable** to the paper's;
  we compare arms under identical conditions instead.

## Results (final)

| Arm | Examples | Accuracy | LLM calls | Input tok | Output tok | LLM time |
|---|---|---|---|---|---|---|
| baseline (n_actions=3, paper config) | 20 | **16/20 = 80%** | 792 (39.6/ex) | 335,937 (16.8k/ex) | 180,895 (9.0k/ex) | 5,489 s (274 s/ex) |
| no_branch (n_actions=1, modification) | 5 (paired subset) | 4/5 = 80% | 95 (19.0/ex) | 34,549 (6.9k/ex) | 16,831 (3.4k/ex) | 423 s (85 s/ex) |
| Δ (modified − baseline, per-example) | | **0** | **−52%** | **−59%** | **−63%** | **−69%** |

- The literal paper number (37%) **does not reproduce and was never expected to** — different model,
  endpoint-mandated sampling (temperature 1.0 / top_p 0.95), and a different subset boundary
  (the loader serves 316 rows). What reproduces is the **pipeline behavior**: search terminates
  productively on all 20 problems, the generative PRM gives discriminating signal (terminal-node fast
  rewards span 0.6–1.0, mean 0.93), and per-component cost accounting matches the documentation.
- **Modification reading:** removing branching cost zero accuracy on the paired 5-problem subset
  while cutting LLM calls by 52% and LLM time by 69% — consistent with the paper's mode-collapse
  finding (with a strong policy, extra branches duplicate effort). Baseline arm on the 5-example
  subset is scaled from the 20-example run (marked ~ in the report). Caveat: 5 examples cannot
  detect small accuracy differences; the result is about cost at parity.
- Per-example correctness: both arms solved exactly the same problems and both failed on example #3
  (genuinely hard for this model). Baseline failures: #3, 8, 10, 13.

See `results/summary.md` for the machine-readable summary and `results/` eval-log excerpts.

## One modification (isolated + measured)

- **Arm `no_branch`:** `n_actions` 3 → 1. The MCTS tree degenerates to a single greedy path
  (policy diversity removed); everything else (components, prompts, PRM, iteration budget, decoding)
  is held constant. Motivation: the paper's mode-collapse finding (Crosswords: 81.1% duplicate
  actions) claims action *diversity* is the bottleneck of tree search in open-ended action spaces.
  Measured: accuracy, LLM calls, input/output tokens, LLM time, and reward statistics.

## Repository layout

- `patches/0001-*.patch`, `patches/0002-*.patch` — the **only** source changes to upstream LiTS
  (environment-compatibility fixes for OpenAI-compatible *reasoning-model* endpoints; default behavior
  unchanged, everything gated by env vars). Apply in order with `git apply` inside a clone of
  `xinzhel/lits-llm`. Fixes: (1) env-gated sampling-param override + token budgets for binary/PRM
  scoring + `tool_choice="required"` for answer voting; (2) per-request timeout/SDK retry bounds.
- `scripts/run_experiment.sh` — runner for both arms (deterministic CLI flags; every flag is also
  captured in each run's `config.json` by LiTS itself). `scripts/run_all.sh` — sequential multi-trial driver.
- `results/` — aggregated metrics and raw eval-log excerpts.
- `report/` — the ≤10-page report (Markdown source + PDF renderer).
- `presentation/` — 12-slide deck (PPTD source) + 15-minute speaking script.

## Quick start

```bash
git clone https://github.com/xinzhel/lits-llm.git
cd lits-llm
git apply ../patches/0001-*.patch && git apply ../patches/0002-*.patch   # from this repo
uv venv .venv --python 3.12 && uv pip install --python .venv/bin/python -e .

export OPENAI_API_KEY=...                 # any OpenAI-compatible endpoint
export OPENAI_API_BASE=...                  # e.g. reasoning-model gateway
# Endpoint-constrained sampling params (Kimi gateway only accepts temperature=1, top_p=0.95):
export LITS_OPENAI_FORCE_TEMPERATURE=1 LITS_OPENAI_FORCE_TOP_P=0.95
# Token budgets so reasoning models leave parseable answers:
export LITS_BINARY_MAX_NEW_TOKENS=512 LITS_PRM_SAMPLE_MAX_NEW_TOKENS=2048
# Bound per-request wait / retries (unreliable gateways):
export LITS_OPENAI_TIMEOUT=900 LITS_OPENAI_MAX_RETRIES=2
export PATH="$PWD/.venv/bin:$PATH"

cd demos
bash <path-to-this-repo>/scripts/run_experiment.sh baseline 1    # ~91 min LLM time for 20 problems
LIMIT=5 bash <path-to-this-repo>/scripts/run_experiment.sh no_branch 1
lits-eval --result_dir <run_dir>                     # from demos/
```

## Security note

No API keys are committed anywhere in this repository. All credentials are supplied via
environment variables at runtime.
