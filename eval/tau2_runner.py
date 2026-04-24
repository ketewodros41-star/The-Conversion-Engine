"""
Tenacious Conversion Engine - Tau2-Bench Runner CLI
Usage: python tau2_runner.py --model claude-sonnet-4-6 --mechanism scap_v2 --slice held_out --trials 5
"""

import argparse
import json
import sys
from pathlib import Path

# Load .env before anything else so OPENROUTER_API_KEY is available
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# Dev-slice task IDs (30 tasks)
DEV_SLICE = [f"RETAIL-{str(i).zfill(3)}" for i in range(1, 31)]

# Held-out slice (20 tasks — provided by program staff; not exposed before Act IV scoring)
HELD_OUT_SLICE = [f"HELD-{str(i).zfill(3)}" for i in range(1, 21)]

VALID_MECHANISMS = ["none", "scap_v2", "binary_gate", "continuous", "gepa"]
VALID_SLICES = ["dev", "held_out"]


def main():
    parser = argparse.ArgumentParser(description="Run Tau2-Bench evaluation")
    parser.add_argument("--model", default="gemini-2.0-flash-free",
                        help="LLM model alias: gemini-2.0-flash-free (free), gemini-2.0-flash, deepseek-v3, qwen3-8b, or full litellm name")
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="Model temperature (pin at 0.0 for scored runs)")
    parser.add_argument("--mechanism", default="none",
                        choices=VALID_MECHANISMS,
                        help="Mechanism to apply (none=baseline)")
    parser.add_argument("--slice", default="dev",
                        choices=VALID_SLICES,
                        help="Evaluation slice")
    parser.add_argument("--trials", type=int, default=5,
                        help="Number of trials per task")
    parser.add_argument("--output", default=None,
                        help="Output JSONL path (default: eval/trace_log.jsonl)")
    parser.add_argument("--tasks", nargs="*",
                        help="Specific task IDs to run (default: full slice)")
    args = parser.parse_args()

    # Select task IDs
    if args.tasks:
        task_ids = args.tasks
    elif args.slice == "dev":
        task_ids = DEV_SLICE
    else:
        task_ids = HELD_OUT_SLICE

    print(f"Tau2-Bench Evaluation")
    print(f"Model: {args.model} | Temperature: {args.temperature}")
    print(f"Mechanism: {args.mechanism} | Slice: {args.slice}")
    print(f"Tasks: {len(task_ids)} | Trials: {args.trials}")
    print(f"Total evaluations: {len(task_ids) * args.trials}")
    print("-" * 50)

    # Import and run harness
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from eval.harness import Tau2BenchHarness

    harness = Tau2BenchHarness(
        model=args.model,
        temperature=args.temperature,
        mechanism=None if args.mechanism == "none" else args.mechanism,
        slice_name=args.slice,
        trials=args.trials,
        output_path=args.output,
    )

    results = harness.run(task_ids)

    print(f"\nResults:")
    print(f"  pass@1: {results['pass_at_1_mean']:.1%}")
    print(f"  95% CI: [{results['pass_at_1_95ci_lower']:.1%}, {results['pass_at_1_95ci_upper']:.1%}]")
    print(f"  p50 latency: {results['latency_p50_ms']}ms")
    print(f"  p95 latency: {results['latency_p95_ms']}ms")
    print(f"  cost/run: ${results['cost_per_run_usd']:.3f}")
    print(f"  total cost: ${results['total_cost_usd']:.3f}")
    print(f"\nTrace log: {results['trace_log_ref']}")
    print(f"Score log: eval/score_log.json (updated)")


if __name__ == "__main__":
    main()
