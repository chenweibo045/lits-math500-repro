# Reproducing LiTS (MCTS Tree Search) on MATH500 — FTEC5660 Reproducibility Work

Reproducibility study of **LiTS: A Modular Framework for LLM Tree Search**
(X. Li & Y. Tao, ACL 2026 System Demonstrations, [arXiv:2603.00631](https://arxiv.org/abs/2603.00631);
code: [xinzhel/lits-llm](https://github.com/xinzhel/lits-llm), Apache-2.0).

> Full report: see `report/` (added with final numbers).
> Slides + 15-minute speaking script: see `presentation/`.

## What is reproduced

- **Target claim (paper Table 6):** ReST-MCTS* (MCTS + ConcatPolicy/ConcatTransition/GenerativePRM)
  on MATH500, n_iters=10, n_actions=3 — tree search improves over the CoT chain baseline
  (paper: ReST 37%, ToT-BFS 39%, RAP 18%, CoT 17% on the first 100 examples with Llama3-8B-Instruct).
- **Scope of this reproduction:** the first 20 MATH500 examples of the repo's registered loader
  (`xinzhel/math500-float`), 3 independent trials per arm.
- **Controlled variable (permitted model swap):** the paper's Llama3-8B is replaced by
  `kimi-k2-0905-preview` served through an OpenAI-compatible gateway. All numbers are therefore
  **not directly comparable** to the paper's; we compare arms under identical conditions instead.

## One modification (isolated + measured)

- **Arm `no_branch`:** `n_actions` 3 → 1. The MCTS tree degenerates to a single greedy path
  (policy diversity removed). Motivation: the paper's mode-collapse finding claims action
  *diversity* (not reward quality) is the bottleneck of tree search in open-ended action spaces.
  Measured: accuracy, LLM calls, input/output tokens, wall time, and reward statistics.

## Repository layout

- `patches/0001-compat-reasoning-endpoints.patch` — the only source changes to upstream LiTS
  (environment-compatibility fixes for OpenAI-compatible *reasoning-model* endpoints;
  default behavior unchanged, everything gated by env vars).
- `scripts/run_experiment.sh` — runner for both arms (deterministic CLI flags; every flag is
  also captured in each run's `config.json` by LiTS itself).
- `scripts/run_all.sh` — runs all trials sequentially (baseline ×3, then no_branch ×3).
- `results/` — aggregated per-trial metrics and raw eval logs (added after the runs).

## Quick start

```bash
git clone https://github.com/xinzhel/lits-llm.git
cd lits-llm
git apply ../patches/0001-compat-reasoning-endpoints.patch   # from this repo
uv venv .venv --python 3.12 && uv pip install --python .venv/bin/python -e .

export OPENAI_API_KEY=...                 # any OpenAI-compatible endpoint
export OPENAI_API_BASE=...                  # e.g. reasoning-model gateway
# Endpoint-constrained sampling params (Kimi gateway only accepts temperature=1, top_p=0.95):
export LITS_OPENAI_FORCE_TEMPERATURE=1 LITS_OPENAI_FORCE_TOP_P=0.95
# Token budgets so reasoning models leave parseable answers:
export LITS_BINARY_MAX_NEW_TOKENS=512 LITS_PRM_SAMPLE_MAX_NEW_TOKENS=2048
export PATH="$PWD/.venv/bin:$PATH"

cd demos
bash ../../scripts/run_experiment.sh baseline 1    # ~45-55 min for 20 problems
bash ../../scripts/run_experiment.sh no_branch 1
lits-eval --result_dir <run_dir>                     # from demos/
```

## Security note

No API keys are committed anywhere in this repository. All credentials are supplied via
environment variables at runtime.
