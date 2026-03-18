"""Entry point: python -m benchmark.run_benchmark"""

import argparse
import time
from pathlib import Path

from .report import generate_html_report
from .simulation import run_simulation


def format_table(results: list[dict], label: str = "") -> str:
    """Format results as a readable table."""
    lines = []

    header = (
        f"{'Round':>5} | {'MRR':>6} {'P@1':>6} {'P@3':>6} {'P@5':>6} {'Hit@5':>6} | "
        f"{'T1 MRR':>6} {'T2 MRR':>6} {'T3 MRR':>6}"
    )
    separator = "-" * len(header)

    lines.append("")
    title = f"Millwright Benchmark Results"
    if label:
        title += f" ({label})"
    lines.append(title)
    lines.append("=" * len(header))
    lines.append(header)
    lines.append(separator)

    for r in results:
        o = r["overall"]
        t1 = r["tier_1"]
        t2 = r["tier_2"]
        t3 = r["tier_3"]
        lines.append(
            f"{r['round']:>5} | "
            f"{o['mrr']:>6.3f} {o['p@1']:>6.3f} {o['p@3']:>6.3f} {o['p@5']:>6.3f} {o['hit@5']:>6.3f} | "
            f"{t1['mrr']:>6.3f} {t2['mrr']:>6.3f} {t3['mrr']:>6.3f}"
        )

    lines.append(separator)

    r1 = results[0]["overall"]
    r_last = results[-1]["overall"]
    lines.append("")
    lines.append("Improvement (Round 1 -> Round {})".format(results[-1]["round"]))
    lines.append(separator)
    for metric in ["mrr", "p@1", "p@3", "p@5", "hit@5"]:
        v1 = r1[metric]
        vn = r_last[metric]
        delta = vn - v1
        pct = (delta / v1 * 100) if v1 > 0 else float("inf")
        lines.append(
            f"  {metric.upper():>5}: {v1:.3f} -> {vn:.3f}  "
            f"(delta: {delta:+.3f}, {pct:+.1f}%)"
        )

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Millwright benchmark")
    parser.add_argument("--rounds", type=int, default=10, help="Number of rounds")
    parser.add_argument("--seeds", type=int, default=3, help="Number of random seeds")
    parser.add_argument("--noise", type=float, default=0.0, help="Feedback noise (0.0-1.0)")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    parser.add_argument("-o", "--output", type=str, default="benchmark_report.html")
    args = parser.parse_args()

    print("Millwright Benchmark")
    print(f"  Rounds: {args.rounds}, Seeds: {args.seeds}, Noise: {args.noise}")
    print("  Loading model and running simulation...")
    print()

    start = time.time()
    data = run_simulation(
        n_rounds=args.rounds,
        seed=args.seed,
        n_seeds=args.seeds,
        feedback_noise=args.noise,
    )
    elapsed = time.time() - start

    print(format_table(data["adaptive"], "Adaptive"))
    print(format_table(data["baseline"], "Baseline (semantic-only)"))
    print(f"Completed in {elapsed:.1f}s")

    report_path = Path(args.output)
    report_path.write_text(generate_html_report(data, elapsed))
    print(f"HTML report written to {report_path}")


if __name__ == "__main__":
    main()
