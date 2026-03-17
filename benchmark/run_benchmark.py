"""Entry point: python -m benchmark.run_benchmark"""

import sys
import time

from .simulation import run_simulation


def format_table(results: list[dict]) -> str:
    """Format results as a readable table."""
    lines = []

    header = (
        f"{'Round':>5} | {'MRR':>6} {'P@1':>6} {'P@3':>6} {'P@5':>6} {'Hit@5':>6} | "
        f"{'T1 MRR':>6} {'T2 MRR':>6} {'T3 MRR':>6}"
    )
    separator = "-" * len(header)

    lines.append("")
    lines.append("Millwright Benchmark Results")
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

    # Summary: round 1 vs round 10
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

    # Tier 3 (ambiguous) improvement
    t3_r1 = results[0]["tier_3"]
    t3_rn = results[-1]["tier_3"]
    lines.append("")
    lines.append("Tier 3 (Ambiguous) Improvement:")
    for metric in ["mrr", "p@1"]:
        v1 = t3_r1[metric]
        vn = t3_rn[metric]
        delta = vn - v1
        pct = (delta / v1 * 100) if v1 > 0 else float("inf")
        lines.append(
            f"  {metric.upper():>5}: {v1:.3f} -> {vn:.3f}  "
            f"(delta: {delta:+.3f}, {pct:+.1f}%)"
        )

    lines.append("")
    return "\n".join(lines)


def main():
    print("Millwright Benchmark")
    print("Loading model and running simulation...")
    print()

    start = time.time()
    results = run_simulation(n_rounds=10, seed=42)
    elapsed = time.time() - start

    print(format_table(results))
    print(f"Completed in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
