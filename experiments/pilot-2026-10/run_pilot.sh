#!/bin/sh
# Run the whole pilot, in order: plain-agent, skill-agent, then Task2View. Safe to re-run at any
# time: finished runs are skipped, interrupted ones resume, and usage limits are waited out.
#   run_pilot.sh                     everything still missing
#   run_pilot.sh --only IS-seat-L1   Task2View for one goal only (agents still complete first)
set -e
cd "$(dirname "$0")/../../code"
caffeinate -i .venv/bin/python ../experiments/pilot-2026-10/run_agents.py
caffeinate -i .venv/bin/python scripts/run_goal_set.py --goals ../experiments/pilot-2026-10/goals.yaml \
  --out ../experiments/pilot-2026-10/outputs/task2view --llm claude-code:claude-sonnet-5-5 \
  --notations plantuml --wait "$@"
echo "pilot runs complete"
