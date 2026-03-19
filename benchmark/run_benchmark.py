"""Entry point: python -m benchmark.run_benchmark"""

import argparse
import time
from pathlib import Path

from .queries import get_queries
from .report import generate_html_report
from .simulation import run_simulation, run_slot_sweep, run_fitness_sweep
from .tools import get_tools

MILESTONES = [1, 5, 10, 25, 50, 100]


def format_table(results: list[dict], label: str = "", milestones: list[int] | None = None) -> str:
    """Format results as a readable table, optionally only showing milestone rounds."""
    lines = []

    header = (
        f"{'Round':>5} | {'MRR':>6} {'P@1':>6} {'P@3':>6} {'P@5':>6} {'Hit@5':>6} | "
        f"{'T1 MRR':>6} {'T2 MRR':>6} {'T3 MRR':>6}"
    )
    separator = "-" * len(header)

    title = "Millwright Benchmark Results"
    if label:
        title += f" ({label})"
    lines.append("")
    lines.append(title)
    lines.append("=" * len(header))
    lines.append(header)
    lines.append(separator)

    milestone_set = set(milestones) if milestones else None
    for r in results:
        if milestone_set and r["round"] not in milestone_set:
            continue
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
    parser.add_argument("--rounds", type=int, default=100, help="Number of rounds (default: 100)")
    parser.add_argument("--seeds", type=int, default=1, help="Number of random seeds")
    parser.add_argument("--noise", type=float, default=0.0, help="Feedback noise (0.0-1.0)")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    parser.add_argument("--sweep-rounds", type=int, default=10,
                        help="Rounds per config in sweeps (default: 10)")
    parser.add_argument("--no-sweep", action="store_true", help="Skip slot sweep")
    parser.add_argument("--no-fitness-sweep", action="store_true", help="Skip fitness sweep")
    parser.add_argument("-o", "--output", type=str, default="benchmark_report.html")
    args = parser.parse_args()

    n_phases = 1 + (0 if args.no_sweep else 1) + (0 if args.no_fitness_sweep else 1)
    phase = 0

    print("Millwright Benchmark")
    print(f"  Learning curve: {args.rounds} rounds, {args.seeds} seed(s)")
    if not args.no_sweep:
        print(f"  Slot sweep: 9 configs x {args.sweep_rounds} rounds")
    if not args.no_fitness_sweep:
        print(f"  Fitness sweep: 8 presets x {args.sweep_rounds} rounds")
    if args.noise > 0:
        print(f"  Feedback noise: {args.noise:.0%}")
    print()

    # Phase 1: Learning curve
    phase += 1
    print(f"Phase {phase}/{n_phases}: Learning curve...", flush=True)
    t0 = time.time()
    sim_data = run_simulation(
        n_rounds=args.rounds,
        seed=args.seed,
        n_seeds=args.seeds,
        feedback_noise=args.noise,
    )
    t_sim = time.time() - t0
    print(f"  Done in {t_sim:.1f}s")

    milestones = [m for m in MILESTONES if m <= args.rounds]
    print(format_table(sim_data["adaptive"], "Adaptive", milestones=milestones))

    # Phase 2: Slot holdout sweep
    sweep_data = None
    t_sweep = 0.0
    if not args.no_sweep:
        phase += 1
        print(f"Phase {phase}/{n_phases}: Slot sweep...", flush=True)
        t0 = time.time()
        sweep_data = run_slot_sweep(
            n_rounds=args.sweep_rounds,
            seed=args.seed,
            feedback_noise=args.noise,
        )
        t_sweep = time.time() - t0
        print(f"  Done in {t_sweep:.1f}s")

        print("\nSlot Sweep (final-round MRR):")
        print("-" * 50)
        for entry in sweep_data:
            final = entry["rounds"][-1]["overall"]
            t3 = entry["rounds"][-1]["tier_3"]
            print(f"  {entry['label']:>7}  MRR={final['mrr']:.3f}  T3 MRR={t3['mrr']:.3f}")
        print()

    # Phase 3: Fitness sweep
    fitness_data = None
    t_fitness = 0.0
    if not args.no_fitness_sweep:
        phase += 1
        print(f"Phase {phase}/{n_phases}: Fitness sweep...", flush=True)
        t0 = time.time()
        fitness_data = run_fitness_sweep(
            n_rounds=args.sweep_rounds,
            seed=args.seed,
            feedback_noise=args.noise,
        )
        t_fitness = time.time() - t0
        print(f"  Done in {t_fitness:.1f}s")

        print("\nFitness Sweep (final-round MRR):")
        print("-" * 65)
        for entry in fitness_data:
            final = entry["rounds"][-1]["overall"]
            t3 = entry["rounds"][-1]["tier_3"]
            p = entry["preset"]
            vals = f"P={p['perfect']:.1f} R={p['related']:.2f} U={p['unrelated']:.2f} B={p['broken']:.2f}"
            print(f"  {entry['label']:<20} {vals}  MRR={final['mrr']:.3f}  T3={t3['mrr']:.3f}")
        print()

    elapsed = t_sim + t_sweep + t_fitness
    print(f"Total: {elapsed:.1f}s")

    tools = get_tools()
    queries = get_queries()
    n_tools = len(tools)
    n_queries = len(queries)
    n_categories = len(set(t.category for t in tools))
    tier_counts = tuple(sum(1 for q in queries if q.tier == t) for t in (1, 2, 3))

    report_path = Path(args.output)
    report_path.write_text(generate_html_report(
        sim_data, sweep_data, fitness_data, elapsed,
        n_tools=n_tools, n_queries=n_queries,
        n_categories=n_categories, tier_counts=tier_counts,
    ))
    print(f"HTML report written to {report_path}")


if __name__ == "__main__":
    main()
