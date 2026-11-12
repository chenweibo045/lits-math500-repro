# 15-Minute Presentation Script — Reproducing LiTS on MATH500

Total ≈ 1,550 words at ~105 wpm. Slide numbers refer to the deck in this folder.

---

**Slide 1 — Cover (0:00–0:45)**

Hi, I'm [name], and this is my reproducibility work for FTEC5660. I picked LiTS — "A Modular Framework for LLM Tree Search", an ACL 2026 system demonstration — reproduced one of its reported results on MATH500, and then made one small, controlled modification to test one of the paper's own claims. Everything is on GitHub: the reproduction repo is linked on this slide.

**Slide 2 — The project (0:45–2:30)**

What is LiTS? It's a Python framework for LLM reasoning via tree search. The key idea is modularity: tree search is decomposed into three components — a Policy that generates candidate actions, a Transition that executes them into new states, and a RewardModel that scores action quality. These plug into search algorithms like MCTS or BFS through a decorator registry, and you can swap domains by registering new components, without touching core code.

Importantly, this is a *system demonstration* paper. Its claims are about composability, not state-of-the-art accuracy. On MATH500 with Llama3-8B and 100 examples, it reports the ReST-MCTS* configuration at 37% accuracy, ToT-BFS at 39%, and a CoT chain baseline at 17%. Two claims mattered for me: first, tree search beats the CoT baseline — branching exploration helps; second, a mode-collapse finding — in open-ended action spaces, policy diversity, not reward quality, is the bottleneck for tree search.

**Slide 3 — Target and scope (2:30–3:45)**

My target claim was the ReST-MCTS* row: MCTS with the built-in concat policy, concat transition, and generative PRM on MATH500, ten iterations, branching factor three. I measure accuracy, LLM invocations, tokens, and wall time — all from LiTS's built-in InferenceLogger.

Following the assignment guidance, I scoped down: one benchmark row, one dataset, the first 20 examples instead of 100, and three independent trials, because the endpoint samples at temperature one, so trials are my unit of variance. Evaluation uses the repo's own lits-eval on saved terminal nodes, so scoring never re-runs search.

**Slide 4 — Setup and the model swap (3:45–5:00)**

Setup: an M5 Pro MacBook, Python 3.12, LiTS v0.4.0 from source. The repo hard-codes older model families, so — as the assignment explicitly allows — I swapped the model to an accessible one: kimi-k2-0905-preview through an OpenAI-compatible gateway, changing only config: model name, base URL, key. Two deviations follow and I document both: the endpoint only accepts temperature 1.0 and top_p 0.95, while the paper used 0.7 to 0.8; and of course the model itself differs from Llama3-8B. So my numbers are not directly comparable to the paper — I compare my arms against each other under identical conditions, and use the paper only as a qualitative reference.

**Slide 5 — Hidden assumptions (5:00–6:00)**

Before running, I surfaced four hidden assumptions. One: the paper says "first 100 MATH500 examples", but the registered dataset loader actually serves 316 rows — the paper's subset boundary is not literally addressable, so I fixed my subset as the first 20 rows and documented it. Two: no user-facing seed for the OpenAI path. Three: endpoint-mandated decoding params. Four: the reward model's logit fallback can't work on a chat endpoint with no logprobs. Each of these bounds the reproducibility of any specific number before we even start.

**Slide 6 — Debug diary (6:00–8:00)**

Getting from clone to first valid run took four fixes, all in one small patch commit, all env-gated so default behavior is unchanged. First, the endpoint rejected the framework's sampling params outright. Second — and more interesting — binary yes/no scoring failed silently: the reasoning model burns the hard-coded 10-token budget inside its reasoning channel, leaving an empty answer, so every score defaulted to "no". Third, same cause at 500 tokens for the PRM sampling: usefulness scores collapsed to zero, which means the search tree loses its signal entirely — a truly silent failure mode. Fourth, answer voting crashed because the endpoint answered in free text instead of making the required tool call; pinning tool_choice to "required" fixed it. After these fixes, the smoke test passed one out of one, and a two-problem timing run passed two out of two at roughly 100 seconds per problem.

**Slide 7 — Baseline results (8:00–9:30)**

Here are the baseline numbers — MCTS with branching factor three on 20 problems, one completed trial (two more were cancelled for the time budget, so no trial spread — a stated limitation; per-example detail is in the report instead). Accuracy 16 of 20, 80%. Cost: 792 LLM calls, about 40 per problem; 336k input and 181k output tokens; 91.5 minutes of LLM time. The patterns to note: the search terminates productively on every problem, the PRM signal is alive — terminal-node rewards span 0.6 to 1.0 with mean 0.93, so the reward model discriminates — and the per-component cost accounting matches the documentation exactly. Recall the paper reference is 37% for this configuration — different model, different subset size, so I treat direction and pipeline behavior, not the literal number, as the reproduction target.

**Slide 8 — The modification (9:30–10:45)**

For the modification I made exactly one change: branching factor from three to one. With one candidate action per expansion, the MCTS tree degenerates into a single greedy path — a sequential chain with PRM bookkeeping. Everything else is held constant. I chose this because it directly operationalizes the paper's mode-collapse claim on a language-grounded task: if action diversity really is the bottleneck, removing branching should cost little; if reward-guided branching adds value, we should see measurable degradation in accuracy or cost-efficiency.

**Slide 9 — Modification results (10:45–12:00)**

Comparing the arms: accuracy is identical — both solve 4 of 5, both fail only on problem number 3, which is genuinely hard for this model. The deltas are all in cost: LLM calls down 52%, input tokens down 59%, output tokens down 63%, LLM time down 69%. On the efficiency view — correct answers per thousand output tokens — that is 0.089 for the baseline versus 0.238 for the single-path arm, about two-point-seven times more accuracy per token. The interpretation relative to the paper's claim: this is exactly the mode-collapse pattern they report — when the policy is strong, the extra branches duplicate effort instead of exploring, so the diversity that tree search pays for goes unused. It also refines their claim: the diversity bottleneck bites when the policy is weak — their Llama3-8B at 37% — but with a strong reasoning model, greedy single-path search with PRM bookkeeping is the cost-efficient operating point on easy-to-medium problems. The caveat: five problems cannot detect small accuracy differences — this result is about cost at parity, not proof of equal accuracy.

**Slide 10 — What is reproducible (12:00–13:00)**

What reproduced: the full pipeline runs end-to-end; the observability claims — per-component token and time accounting — work exactly as documented; and a run can be re-executed from config.json alone, which I verified flag-for-flag. What did not reproduce as-is: the literal 37% — bounded by the model swap, sampling params, and the dataset-version drift; the logit-based reward path; and the "first 100 examples" subset semantics.

**Slide 11 — Lessons (13:00–14:00)**

Four lessons. Reasoning models break silent contracts — size every token budget for reasoning overhead, or you get empty answers with no errors. Endpoint constraints are undocumented experimental variables — record decoding params as first-class metadata. Tool-calling discipline varies by endpoint — verify conformance explicitly. And evaluating from saved artifacts, which LiTS does well, is what made iterating cheap: we caught and fixed the voting bug without re-running any search.

**Slide 12 — Summary (14:00–15:00)**

To summarize: I reproduced LiTS's ReST-MCTS* configuration on MATH500 with a permitted model swap, verified its framework-level claims, and quantified the value of policy diversity with one isolated modification — removing branching cost zero accuracy on a paired five-problem subset while cutting LLM calls by 52% and LLM time by 69%. The framework's claims hold up; the paper's literal numbers are bounded by model, sampling, and dataset assumptions — which is exactly what reproducibility work is for. Thank you.

---

*Recording note: this script is written for a ~15-minute Zoom recording; all numbers are final — rehearse once against the slides for timing.*
