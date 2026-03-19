"""Multi-round simulation loop with feedback."""

import math
import random
from collections import defaultdict
from copy import deepcopy

from millwright.config import MillwrightConfig
from millwright.decomposer import MockDecomposer
from millwright.embedder import Embedder
from millwright.models import ToolReview
from millwright.toolshed import Toolshed, NONE_SENTINEL

from dataclasses import replace

from .queries import BenchmarkQuery, get_queries
from .metrics import compute_metrics
from .tools import get_tools


def _clone_config(base: MillwrightConfig, **overrides) -> MillwrightConfig:
    """Clone a config with field overrides."""
    return replace(base, **overrides)


def _simulate_feedback(
    ranked_tools: list[str],
    query: BenchmarkQuery,
    tool_categories: dict[str, str],
    noise: float = 0.0,
) -> list[ToolReview]:
    """Simulate agent feedback.

    correct -> perfect, same-category -> related, else -> unrelated.
    With noise > 0, ratings are randomly degraded with that probability.
    """
    reviews = []
    expected_set = set(query.expected_tools)
    for tool_name in ranked_tools:
        if tool_name == NONE_SENTINEL:
            continue
        if tool_name in expected_set:
            rating = "perfect"
        elif tool_categories.get(tool_name) == query.category:
            rating = "related"
        else:
            rating = "unrelated"

        # Noisy feedback: with probability `noise`, degrade the rating one step
        if noise > 0 and random.random() < noise:
            degraded = {"perfect": "related", "related": "unrelated", "unrelated": "unrelated"}
            rating = degraded[rating]

        reviews.append(ToolReview(tool_name=tool_name, rating=rating))
    return reviews


def _run_single(
    n_rounds: int,
    seed: int,
    config: MillwrightConfig,
    embedder: Embedder,
    queries: list[BenchmarkQuery],
    tool_categories: dict[str, str],
    baseline: bool = False,
    feedback_noise: float = 0.0,
) -> list[dict]:
    """Run one simulation pass. If baseline=True, never submit feedback (semantic-only)."""
    random.seed(seed)
    tools = get_tools()
    decomposer = MockDecomposer()

    shed = Toolshed(
        tools=tools,
        decomposer=decomposer,
        config=config,
        embedder=embedder,
    )
    shed.clear_data()

    round_results = []

    for round_num in range(1, n_rounds + 1):
        shuffled = list(queries)
        random.shuffle(shuffled)

        all_metrics: list[dict[str, float]] = []
        tier_metrics: dict[int, list[dict[str, float]]] = defaultdict(list)

        for bq in shuffled:
            session = shed.suggest_tools(bq.query)

            ranked_names = [
                name for name, _ in session.ranked_tools
                if name != NONE_SENTINEL
            ]

            m = compute_metrics(ranked_names, bq.expected_tools)
            all_metrics.append(m)
            tier_metrics[bq.tier].append(m)

            if not baseline:
                feedback = _simulate_feedback(
                    ranked_names, bq, tool_categories, noise=feedback_noise
                )
                shed.review_tools(session, feedback)

        if not baseline:
            shed.compact()

        def avg_metrics(metrics_list: list[dict[str, float]]) -> dict[str, float]:
            if not metrics_list:
                return {}
            keys = metrics_list[0].keys()
            return {k: sum(m[k] for m in metrics_list) / len(metrics_list) for k in keys}

        round_results.append({
            "round": round_num,
            "overall": avg_metrics(all_metrics),
            "tier_1": avg_metrics(tier_metrics[1]),
            "tier_2": avg_metrics(tier_metrics[2]),
            "tier_3": avg_metrics(tier_metrics[3]),
        })

    return round_results


def _avg_across_seeds(all_runs: list[list[dict]]) -> list[dict]:
    """Average metrics across multiple seed runs, also compute stddev."""
    n_rounds = len(all_runs[0])
    n_seeds = len(all_runs)
    averaged = []

    for r_idx in range(n_rounds):
        result = {"round": all_runs[0][r_idx]["round"]}
        for section in ["overall", "tier_1", "tier_2", "tier_3"]:
            keys = all_runs[0][r_idx][section].keys()
            section_avg = {}
            section_std = {}
            for k in keys:
                vals = [run[r_idx][section][k] for run in all_runs]
                mean = sum(vals) / n_seeds
                variance = sum((v - mean) ** 2 for v in vals) / n_seeds
                section_avg[k] = mean
                section_std[k] = math.sqrt(variance)
            result[section] = section_avg
            result[f"{section}_std"] = section_std
        averaged.append(result)

    return averaged


def run_simulation(
    n_rounds: int = 10,
    seed: int = 42,
    config: MillwrightConfig | None = None,
    n_seeds: int = 1,
    feedback_noise: float = 0.0,
) -> dict:
    """Run full benchmark: adaptive + baseline, optionally over multiple seeds.

    Returns dict with keys:
      - "adaptive": list of per-round metric dicts
      - "baseline": list of per-round metric dicts (semantic-only)
      - "n_seeds": number of seeds used
      - "feedback_noise": noise level used
    """
    config = config or MillwrightConfig()
    tools = get_tools()
    tool_categories = {t.name: t.category for t in tools}
    queries = get_queries()

    # Shared embedder (model loading is expensive)
    embedder = Embedder(config)

    seeds = [seed + i for i in range(n_seeds)]

    # Run adaptive
    adaptive_runs = []
    for s in seeds:
        adaptive_runs.append(_run_single(
            n_rounds, s, config, embedder, queries, tool_categories,
            baseline=False, feedback_noise=feedback_noise,
        ))

    # Run baseline (semantic-only, no feedback)
    baseline_runs = []
    for s in seeds:
        baseline_runs.append(_run_single(
            n_rounds, s, config, embedder, queries, tool_categories,
            baseline=True,
        ))

    adaptive = _avg_across_seeds(adaptive_runs) if n_seeds > 1 else adaptive_runs[0]
    baseline = _avg_across_seeds(baseline_runs) if n_seeds > 1 else baseline_runs[0]

    return {
        "adaptive": adaptive,
        "baseline": baseline,
        "n_seeds": n_seeds,
        "feedback_noise": feedback_noise,
    }


def run_slot_sweep(
    configs: list[tuple[int, int]] | None = None,
    n_rounds: int = 10,
    seed: int = 42,
    config: MillwrightConfig | None = None,
    feedback_noise: float = 0.0,
) -> list[dict]:
    """Sweep min_semantic_slots / min_historical_slots holdout ratios.

    Each config is (min_semantic_slots, min_historical_slots).

    Returns a list of dicts, one per slot config:
      {"min_semantic_slots", "min_historical_slots", "label", "rounds": [...]}
    """
    if configs is None:
        configs = [
            (5, 0),  # semantic only (no historical holdout)
            (4, 1),  # mostly semantic
            (3, 2),  # balanced-ish
            (3, 1),  # 3 semantic + 1 historical + 1 interleave
            (2, 2),  # equal holdout
            (2, 1),  # default
            (1, 3),  # mostly historical
            (1, 2),  # historical-heavy
            (0, 4),  # almost pure historical
        ]

    base_config = config or MillwrightConfig()
    tools = get_tools()
    tool_categories = {t.name: t.category for t in tools}
    queries = get_queries()
    embedder = Embedder(base_config)

    results = []
    for sem_slots, hist_slots in configs:
        cfg = _clone_config(
            base_config,
            min_semantic_slots=sem_slots,
            min_historical_slots=hist_slots,
        )
        rounds = _run_single(
            n_rounds, seed, cfg, embedder, queries, tool_categories,
            baseline=False, feedback_noise=feedback_noise,
        )
        results.append({
            "min_semantic_slots": sem_slots,
            "min_historical_slots": hist_slots,
            "label": f"S{sem_slots}/H{hist_slots}",
            "rounds": rounds,
        })

    return results


def run_fitness_sweep(
    presets: dict[str, dict[str, float]] | None = None,
    n_rounds: int = 10,
    seed: int = 42,
    config: MillwrightConfig | None = None,
    feedback_noise: float = 0.0,
) -> list[dict]:
    """Sweep fitness multiplier presets.

    Each preset is a dict mapping rating names to multipliers:
      {"perfect": float, "related": float, "unrelated": float, "broken": float}

    Returns a list of dicts:
      {"label", "preset", "rounds": [...]}
    """
    if presets is None:
        presets = {
            "Flat (no signal)":  {"perfect": 1.0,  "related": 1.0,  "unrelated": 1.0,  "broken": 1.0},
            "Mild":              {"perfect": 1.2,  "related": 1.0,  "unrelated": 0.9,  "broken": 0.5},
            "Default":           {"perfect": 1.4,  "related": 1.05, "unrelated": 0.75, "broken": 0.35},
            "Wide":              {"perfect": 2.0,  "related": 1.1,  "unrelated": 0.5,  "broken": 0.1},
            "Extreme":           {"perfect": 3.0,  "related": 1.2,  "unrelated": 0.3,  "broken": 0.05},
            "Punitive related":  {"perfect": 1.4,  "related": 0.9,  "unrelated": 0.75, "broken": 0.35},
            "Generous related":  {"perfect": 1.4,  "related": 1.3,  "unrelated": 0.75, "broken": 0.35},
            "Binary":            {"perfect": 2.0,  "related": 1.0,  "unrelated": 0.5,  "broken": 0.5},
        }

    base_config = config or MillwrightConfig()
    tools = get_tools()
    tool_categories = {t.name: t.category for t in tools}
    queries = get_queries()
    embedder = Embedder(base_config)

    results = []
    for label, preset in presets.items():
        cfg = _clone_config(
            base_config,
            fitness_perfect=preset["perfect"],
            fitness_related=preset["related"],
            fitness_unrelated=preset["unrelated"],
            fitness_broken=preset["broken"],
        )
        rounds = _run_single(
            n_rounds, seed, cfg, embedder, queries, tool_categories,
            baseline=False, feedback_noise=feedback_noise,
        )
        results.append({
            "label": label,
            "preset": preset,
            "rounds": rounds,
        })

    return results
