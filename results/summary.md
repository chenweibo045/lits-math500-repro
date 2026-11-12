# Results summary — LiTS ReST-MCTS* on MATH500 (reproduction)

All numbers extracted from `lits-eval` InferenceLogger totals (BY PHASE TOTAL rows).
Baseline = 19-example main run + dedicated 1-example re-run of example 16 (see report §6, diary #7).

## Baseline arm — paper config (MCTS, n_actions=3, n_iters=10), swapped model, 1 trial

| Metric | Value | Per example |
|---|---|---|
| Accuracy | **16/20 = 80%** (15/19 main + #16 re-run correct) | — |
| LLM invocations | **792** | 39.6 |
| Input tokens | **335,937** | 16,797 |
| Output tokens | **180,895** | 9,045 |
| LLM time | **5,489.4 s** | 274.5 s |
| Terminal nodes / mean fast reward | 16 / **0.925** (span 0.6–1.0) | — |

Main-run eval totals (19 ex): 770 calls, 327,876 in, 176,611 out, 5,389.4 s.
Example-16 re-run eval totals (1 ex): 22 calls, 8,061 in, 4,284 out, 100.0 s.
Per-example correctness (main run idx): wrong on 3, 8, 10, 13; #16 correct on re-run.

Paper reference (Llama3-8B-Instruct, first 100 ex., temperature 0.7–0.8): ReST-MCTS* 37%,
ToT-BFS 39%, RAP 18%, CoT 17%. Not directly comparable (controlled variable; see report §2).

## Modification arm — no_branch (n_actions=1), paired first-5 subset, 1 trial

| Metric | Value | Per example |
|---|---|---|
| Accuracy | **4/5 = 80%** (same 4 problems as baseline; both fail #3) | — |
| LLM invocations | **95** | 19.0 |
| Input tokens | **34,549** | 6,910 |
| Output tokens | **16,831** | 3,366 |
| LLM time | **423.4 s** | 84.7 s |

Baseline arm scaled to 5 examples (marked ~ in the report): ~198 calls, ~84.0k in, ~45.2k out, ~1,372 s.

## Deltas (modified − baseline, per-example rates)

| Metric | Δ |
|---|---|
| Accuracy | 0 (identical per-problem outcomes) |
| LLM calls | −52.0% |
| Input tokens | −58.9% |
| Output tokens | −62.8% |
| LLM time | −69.2% |
| Correct answers per 1k output tokens | 0.089 → 0.238 (≈2.7×) |

## Provenance

- Runs: `exp/results/baseline_trial1/` (main), `exp/results/ex16_fix/` (example 16 re-run),
  `exp/results/no_branch_trial1/` (modification) — full eval JSON + logs in each directory.
- Model: `kimi-k2-0905-preview` via OpenAI-compatible gateway; temperature 1.0 / top_p 0.95
  (endpoint-mandated), per-request timeout 900 s, 2 SDK retries.
- Upstream: `xinzhel/lits-llm` @ f1791daa + patch commits 602189c and eaeccd5 (see `patches/`).
