#!/bin/bash
# Runs the full experiment matrix sequentially:
#   baseline (n_actions=3) trials 1..3, then no_branch (n_actions=1) trials 1..3.
# Run from lits-llm/demos with the environment described in README.md.
set -euo pipefail
TRIALS=${TRIALS:-3}
for t in $(seq 1 "$TRIALS"); do
    echo "===== baseline trial $t ====="
    bash ../scripts/run_experiment.sh baseline "$t"
done
for t in $(seq 1 "$TRIALS"); do
    echo "===== no_branch trial $t ====="
    bash ../scripts/run_experiment.sh no_branch "$t"
done
