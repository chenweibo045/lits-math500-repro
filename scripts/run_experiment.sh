#!/bin/bash
# Reproducibility experiment runner (FTEC5660)
# Usage: bash scripts/run_experiment.sh <baseline|no_branch> <trial_number>
# Must be run from the lits-llm/demos directory (needs lits_benchmark.math_qa).
#
# Required env vars:
#   OPENAI_API_KEY       - API key for the OpenAI-compatible endpoint
#   OPENAI_API_BASE      - base URL of the OpenAI-compatible endpoint
#   LITS_OPENAI_FORCE_TEMPERATURE / LITS_OPENAI_FORCE_TOP_P
#                        - endpoint sampling constraints (see README notes)
#   LITS_BINARY_MAX_NEW_TOKENS / LITS_PRM_SAMPLE_MAX_NEW_TOKENS
#                        - token budgets for reasoning-model backends
set -euo pipefail

ARM=${1:?arm required: baseline|no_branch}
TRIAL=${2:?trial number required}

if [ "$ARM" = "baseline" ]; then
    N_ACTIONS=3            # paper config: branching factor 3
elif [ "$ARM" = "no_branch" ]; then
    N_ACTIONS=1            # modification: remove policy diversity (degenerate tree)
else
    echo "unknown arm: $ARM" >&2; exit 1
fi

MODEL=${MODEL:-"openai/kimi-k2-0905-preview"}
LIMIT=${LIMIT:-20}
N_ITERS=${N_ITERS:-10}

OUT=${OUT_DIR:-"../../exp/results/${ARM}_trial${TRIAL}"}

echo "[runner] arm=$ARM trial=$TRIAL n_actions=$N_ACTIONS n_iters=$N_ITERS limit=$LIMIT out=$OUT"
echo "[runner] model=$MODEL"

lits-search \
    --include lits_benchmark.math_qa \
    --dataset math500 \
    --policy-model "$MODEL" \
    --policy concat --transition concat --reward generative \
    --search-arg n_iters="$N_ITERS" n_actions="$N_ACTIONS" roll_out_steps=2 \
                 max_steps=10 force_terminating_on_depth_limit=false \
    --component-arg n_for_correctness=2 n_for_usefulness=1 \
    --var limit="$LIMIT" \
    -o "$OUT" --override
echo "[runner] done: $OUT"
