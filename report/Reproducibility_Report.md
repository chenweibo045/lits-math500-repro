# Reproducibility Work — Reproducing LiTS (LLM Tree Search) on MATH500 with an OpenAI-Compatible Reasoning Model

**Course:** Agentic AI for Business and FinTech (FTEC5660)
**Project:** LiTS — *A Modular Framework for LLM Tree Search* (Li & Tao, ACL 2026 System Demonstrations; arXiv:2603.00631)
**Code:** https://github.com/xinzhel/lits-llm (Apache-2.0) — instructor list, Tier A, No. 3
**Reproduction repo (this work):** https://github.com/chenweibo045/lits-math500-repro

---

## 1. Project summary and what I tried to reproduce

LiTS is a modular Python framework for LLM reasoning via tree search. It decomposes tree search into three reusable components — **Policy** (generates candidate actions), **Transition** (executes actions, produces states), and **RewardModel** (scores action quality) — that plug into search algorithms such as MCTS and BFS, plus chain agents such as ReAct. The paper is a *system demonstration* paper: its core claims are about **component/algorithm composability**, and it reports small-scale demonstration results on three task types (MATH500 language reasoning, BlocksWorld/Crosswords environment planning, MapEval-SQL tool use).

### Target claim

I targeted the paper's **Table 6** result (MATH500, first 100 examples, Llama3-8B-Instruct, all tree-search methods at n_iters=10, n_actions=3):

| Method (components / algorithm) | Reported accuracy |
|---|---|
| ReST-MCTS* (Concat + Concat + GenerativePRM, **MCTS**) | **37%** |
| ToT (same components, **BFS**) | **39%** |
| RAP (RAP components, MCTS) | 18% |
| CoT chain baseline | 17% |

with the qualitative claim that *"all three tree search methods improve over CoT, confirming that branching exploration helps even with a small model."*

**My scoped reproduction target:** the ReST-MCTS* row — MCTS with the built-in `concat` Policy, `concat` Transition and `generative` PRM on MATH500 — reduced to the **first 20 examples** of the repository's registered MATH500 loader, measuring accuracy, LLM invocations, token usage and time. The paper itself justifies small subsets ("tree search methods are computationally expensive … we use representative subsets"), so a 20-example subset is a faithful, honestly-scoped reproducibility target. A secondary target (context only): the paper's **mode-collapse finding** (Table 4 — on Crosswords, 81.1% duplicate actions even with temperature escalation, and tree search fails *with oracle rewards*), which motivated my modification.

## 2. Setup notes

| Item | Value |
|---|---|
| Hardware | Apple MacBook Pro, M5 Pro, 24 GB RAM (no GPU) |
| OS / Python | macOS 26 (Darwin 25.6.0), Python 3.12.15 |
| LiTS version | v0.4.0 (git clone of `xinzhel/lits-llm` @ `f1791daa` + 2 local patch commits) |
| Dataset | `xinzhel/math500-float` (HF), test split; loader returns **316** rows — see "hidden assumptions" |
| Model (swap, controlled variable) | `kimi-k2-0905-preview` via an OpenAI-compatible gateway (assignment permits DeepSeek "or another accessible model") |
| Endpoint | OpenAI chat-completions API via `OPENAI_API_BASE` |
| Sampling params (endpoint constraint) | temperature **1.0**, top_p **0.95** — the gateway *only* accepts these; paper used 0.7–0.8 |
| Request hardening | per-request timeout 900 s, 2 SDK retries (one run stalled >3 h on a hung connection without it) |
| Keys | supplied via environment variables only; **no secrets committed** |

### Controlled variable statement

> Results are **not directly comparable** to the paper because the underlying LLM differs (Kimi K2 reasoning model vs. self-deployed Llama3-8B-Instruct), and the sampling temperature differs (1.0 vs. 0.7–0.8, endpoint-mandated). I therefore compare all arms **against each other under identical conditions** (same tasks, same metrics, same evaluation script), and use the paper's numbers only as a reference for *expected behavior patterns*, not as a number-matching target.

### Hidden assumptions identified

1. **Dataset version.** The paper says "first 100 MATH500 examples"; the registered loader (`xinzhel/math500-float`) serves 316 rows, so the paper's subset boundary is not literally addressable — subset composition depends on loader version. I used the **first 20 rows** and document this explicitly.
2. **Prompt format** is pulled from the centralized PromptRegistry with task-type fallback — identical across arms by construction.
3. **No run seed** on the OpenAI path. Sampling is endpoint-fixed at temperature 1.0, so runs are stochastic. The plan was 3 trials/arm; due to a time budget only **1 completed trial per arm** is reported (an aborted second trial is documented in the debug diary). Trial-level variance is therefore unavailable — a stated limitation; per-example results are reported instead.
4. **Logits-based scoring paths are unavailable** on chat endpoints (no logprobs); two token-budget fixes were required (§6). Both deviations are logged and identical across arms.

## 3. Metric definitions

- **Accuracy**: per-example correctness from `lits-eval` — terminal answers are extracted ("The answer is X"), semantically grouped via a `group_answers` tool call, majority-voted, then compared against the reference with the repo's `eval_output` checker; aggregated over the subset.
- **LLM invocations / tokens / time**: from LiTS's built-in `InferenceLogger` (per component and phase), reported by `lits-eval` after each run. "LLM time" is the sum of per-call durations.
- **Cost-efficiency**: accuracy per 1,000 output tokens.

## 4. Results: our numbers vs. reported numbers

### Baseline arm (paper config, swapped model): MCTS, n_actions=3, n_iters=10, 20 examples, 1 trial

| Metric | This reproduction |
|---|---|
| Accuracy | **16/20 = 80%** (15/19 from the main run + example 16 from a re-run — see debug diary #7) |
| LLM invocations | **792** (39.6 / example) |
| Input tokens | **335,937** (16.8k / example) |
| Output tokens | **180,895** (9.0k / example) |
| LLM time | **5,489 s** (274 s / example); elapsed wall-clock ≈ 7.3 h end-to-end including one >3 h stalled connection (diary #5) and an in-place resume — LLM time is the comparable unit |

Paper reference (different model, 100 ex.): **ReST-MCTS* 37%**, ToT-BFS 39%, CoT 17%.

The absolute number is far above the paper's 37%, as expected under a much stronger reasoning model — **the literal number does not reproduce and was never expected to** (controlled variable). What reproduces is the *pipeline behavior*: the search terminates productively, the PRM provides discriminating signal (terminal-node fast rewards span 0.6–1.0, mean **0.93** over 16 terminal nodes), answers are found via multi-step decomposition, and per-component cost accounting matches the documentation. The claim that tree search improves on a chain baseline is directionally testable only against our own CoT-scale expectations; our measured 80% is in the range where single-path solving already dominates on this easy subset (see §5).

## 5. Modification: remove policy diversity (n_actions 3 → 1)

**Change.** A single isolated parameter change: `--search-arg n_actions=1` (branching factor 3 → 1). With one candidate action per expansion, the MCTS tree degenerates into a single greedy path — policy diversity is removed while everything else (components, prompts, PRM, iteration budget, decoding) is held constant. This directly operationalizes the paper's mode-collapse claim: *if action diversity is the bottleneck, removing branching should cost little; if reward-guided branching adds value, accuracy and/or cost-efficiency should degrade.*

**Scope.** Paired comparison on the **first 5 examples** of the same subset (time budget), 1 trial per arm, identical protocol.

| Arm | Accuracy (5 ex.) | LLM calls | Input tok | Output tok | LLM time |
|---|---|---|---|---|---|
| baseline (n_actions=3) | 4/5 = 80% | ~198 (39.6/ex) | ~84.0k (16.8k/ex) | ~45.2k (9.0k/ex) | ~1,372 s (274 s/ex) |
| **no_branch (n_actions=1)** | **4/5 = 80%** | **95 (19.0/ex)** | **34.5k (6.9k/ex)** | **16.8k (3.4k/ex)** | **423 s (85 s/ex)** |
| Δ (modified − baseline) | **0** | **−52%** | **−59%** | **−63%** | **−69%** |

(baseline per-example averages scaled from the 20-example run; per-problem accuracy pairing: both arms solved exactly the same 4 problems and both failed on the same example #3 — a genuinely hard problem for this model.)

**Reading.** On this subset, removing branching entirely cost **zero accuracy** while cutting token usage by **~59–63%** and LLM time by **~69%**. This is consistent with the paper's mode-collapse finding: when the policy is strong, the extra branches duplicate effort (token-level sampling rarely yields semantically distinct actions), so the diversity that tree search pays for is not exploited. It also refines the paper's claim: the diversity bottleneck matters most when the policy is *weak* (their Llama3-8B at 37%) — with a strong reasoning model at temperature 1.0, greedy single-path search with PRM bookkeeping is the cost-efficient operating point on easy-to-medium problems. We caution that 5 examples cannot detect small accuracy differences; the result is about cost at parity, not a proof of equal accuracy.

## 6. Debug diary: main blockers and resolutions

| # | Blocker | Symptom | Resolution |
|---|---|---|---|
| 1 | Gateway rejects non-default sampling params | `400 invalid temperature: only 1 is allowed` → `400 invalid top_p: only 0.95` | Env-gated override `LITS_OPENAI_FORCE_TEMPERATURE/ TOP_P` in `openai_chat.py` (logged once); recorded as controlled deviation |
| 2 | Binary yes/no scoring unreadable | `Could not extract answer … Output: ''` ×3 retries → default "no" | Reasoning model burned the hard-coded **10-token** budget inside the reasoning channel. Env-gated `LITS_BINARY_MAX_NEW_TOKENS=512` in `base.py` |
| 3 | PRM sampling unreadable | `Logits unavailable … defaulting score to 0.0` | Same cause at **500 tokens** (PRM sampling); env-gated `LITS_PRM_SAMPLE_MAX_NEW_TOKENS=2048` in `reward/generative.py`. Without this, *all* usefulness scores collapse to 0 and search loses its signal — a silent failure mode |
| 4 | Answer voting fails | `Answer voting requires exactly one group_answers tool call` — eval crashes | Reasoning endpoint answers in free text under `tool_choice="auto"`; pinned `tool_choice="required"` in `eval/answer_voting.py` (verified endpoint supports tool calls) |
| 5 | Run stall | one example stalled **>3 h** on a hung connection (CLOSE_WAIT), past all SDK timeouts | Added explicit client `timeout=900` + `max_retries=2` (env-gated `LITS_OPENAI_TIMEOUT/ MAX_RETRIES`); interrupted run resumed in-place via `lits-resume-clean` + same command |
| 6 | HF hub unreachable mid-study | `Connection to huggingface.co timed out` | `HF_HUB_OFFLINE=1` — dataset served from local cache |
| 7 | Resume skipped example 16 | resumed run processed only examples 17–19; `terminal_nodes_16.json` never written | Ran example 16 as a dedicated one-example run (`--var offset=16 limit=1`) and merged its result (correct); flagged as an upstream resume edge case |
| 8 | `lits-eval` must run from `demos/` | module import error for `lits_benchmark` | documented in README run steps |

All fixes are in **two patch commits** (files `0001-…patch` and `0002-…patch` under `patches/`), are inert unless the env vars are set, and none changes the algorithm, prompts, or evaluation semantics.

## 7. Conclusions: what is reproducible, what is not, and why

**Reproducible.** (i) The full ReST-MCTS* pipeline runs end-to-end on an OpenAI-compatible reasoning endpoint after four small env-gated compatibility fixes; (ii) the framework's observability claims — per-component/per-phase token, call and time accounting — work exactly as documented; (iii) the paper's promise that `config.json` alone suffices to re-execute a run was verified flag-for-flag; (iv) the modification experiment is fully measurable with the framework's own tooling.

**Not reproducible as-is.** (i) The literal 37% — bounded by the model swap, endpoint-mandated sampling params, and dataset-version drift; this was expected and is the nature of a controlled-variable reproduction. (ii) The logit-based reward fallback — chat endpoints expose no logprobs; worse, the failure was *silent* (all-zero rewards) until the token-budget fixes, a failure mode worth reporting upstream. (iii) The "first 100 examples" subset semantics — the loader serves 316 rows. (iv) Trial-level variance — a second baseline trial was started but cancelled to meet the time budget; single-trial results are reported with per-example detail instead.

**Why.** Tree-search papers carry hidden experimental variables (model capability, decoding constraints, subset boundaries, endpoint behavior) that dominate headline numbers at demonstration scale. The assignment's framing is the right one: report *what works, at what cost, under what conditions*.

## Appendix A. Exact reproduction commands

```bash
# environment (see repo README for the meaning of each variable)
export OPENAI_API_KEY=... OPENAI_API_BASE=...
export LITS_OPENAI_FORCE_TEMPERATURE=1 LITS_OPENAI_FORCE_TOP_P=0.95
export LITS_BINARY_MAX_NEW_TOKENS=512 LITS_PRM_SAMPLE_MAX_NEW_TOKENS=2048
export LITS_OPENAI_TIMEOUT=900 LITS_OPENAI_MAX_RETRIES=2
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1

# baseline (20 examples)
bash scripts/run_experiment.sh baseline 1
# modification (first 5 examples)
LIMIT=5 bash scripts/run_experiment.sh no_branch 1
# evaluation (per run, from demos/)
lits-eval --result_dir <run_dir>
```

## Appendix B. Cost accounting

| Arm | Examples | LLM calls | Input tok | Output tok | LLM time | Accuracy |
|---|---|---|---|---|---|---|
| baseline (n_actions=3) | 20 | 792 | 335,937 | 180,895 | 5,489 s | 80% |
| no_branch (n_actions=1) | 5 (paired) | 95 | 34,549 | 16,831 | 423 s | 80% |

Endpoint pricing was not available for the swapped model; token counts are the cost unit. For reference, at OpenAI GPT-4o list prices ($2.50 / 1M input, $10 / 1M output) the baseline run would cost ≈ **$2.65** — tree search at demonstration scale is affordable, but per-example cost is ~40 LLM calls, which is the real deployment consideration.
