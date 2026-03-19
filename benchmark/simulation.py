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
from .baselines import random_rank, tfidf_rank


# Category confusion pairs for the correlated noise model.
# When a tool belongs to one side, feedback for a tool in the other side
# has a higher probability of being degraded.
CONFUSION_PAIRS = [
    ("file", "system"),
    ("http", "cloud"),
    ("database", "transform"),
    ("crypto", "auth"),
    ("messaging", "monitoring"),
]

# Build a lookup: category -> confused partner category
_CONFUSION_MAP: dict[str, str] = {}
for a, b in CONFUSION_PAIRS:
    _CONFUSION_MAP[a] = b
    _CONFUSION_MAP[b] = a


def _clone_config(base: MillwrightConfig, **overrides) -> MillwrightConfig:
    """Clone a config with field overrides."""
    return replace(base, **overrides)


def _simulate_feedback(
    ranked_tools: list[str],
    query: BenchmarkQuery,
    tool_categories: dict[str, str],
    noise: float = 0.0,
    noise_model: str = "uniform",
) -> list[ToolReview]:
    """Simulate agent feedback.

    correct -> perfect, same-category -> related, else -> unrelated.
    With noise > 0, ratings are randomly degraded with that probability.

    noise_model:
      "uniform": degrade one step with flat probability
      "correlated": confused category pairs get higher degradation probability
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

        # Noisy feedback
        if noise > 0:
            effective_noise = noise
            if noise_model == "correlated":
                tool_cat = tool_categories.get(tool_name, "")
                confused_partner = _CONFUSION_MAP.get(query.category)
                if confused_partner and tool_cat == confused_partner:
                    # Higher degradation for confused category pairs
                    effective_noise = min(noise * 3.0, 1.0)

            if random.random() < effective_noise:
                degraded = {"perfect": "related", "related": "unrelated", "unrelated": "unrelated"}
                rating = degraded[rating]

        reviews.append(ToolReview(tool_name=tool_name, rating=rating))
    return reviews


def _stratified_split(
    queries: list[BenchmarkQuery], holdout_fraction: float, seed: int
) -> tuple[list[BenchmarkQuery], list[BenchmarkQuery]]:
    """Split queries into train/test sets, stratified by tier.

    The split is deterministic for a given seed.
    """
    rng = random.Random(seed)
    by_tier: dict[int, list[BenchmarkQuery]] = defaultdict(list)
    for q in queries:
        by_tier[q.tier].append(q)

    train, test = [], []
    for tier in sorted(by_tier):
        tier_qs = list(by_tier[tier])
        rng.shuffle(tier_qs)
        n_holdout = max(1, int(len(tier_qs) * holdout_fraction))
        test.extend(tier_qs[:n_holdout])
        train.extend(tier_qs[n_holdout:])
    return train, test


def _run_single(
    n_rounds: int,
    seed: int,
    config: MillwrightConfig,
    embedder: Embedder,
    queries: list[BenchmarkQuery],
    tool_categories: dict[str, str],
    baseline: bool = False,
    feedback_noise: float = 0.0,
    noise_model: str = "uniform",
    holdout_fraction: float = 0.0,
    continuation_prob: float = 0.0,
    compact_every: int = 1,
) -> list[dict]:
    """Run one simulation pass.

    If baseline=True, never submit feedback (semantic-only).
    If holdout_fraction > 0, split into train/test and track metrics separately.
    If continuation_prob > 0, exercise multi-turn continue_session() API.
    """
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

    # Holdout split (fixed per seed)
    train_queries, test_queries = None, None
    if holdout_fraction > 0:
        train_queries, test_queries = _stratified_split(queries, holdout_fraction, seed)
        train_set = set(id(q) for q in train_queries)
    else:
        train_set = set(id(q) for q in queries)

    round_results = []

    for round_num in range(1, n_rounds + 1):
        shuffled = list(queries)
        random.shuffle(shuffled)

        all_metrics: list[dict[str, float]] = []
        tier_metrics: dict[int, list[dict[str, float]]] = defaultdict(list)
        train_metrics_list: list[dict[str, float]] = []
        test_metrics_list: list[dict[str, float]] = []
        train_tier: dict[int, list[dict[str, float]]] = defaultdict(list)
        test_tier: dict[int, list[dict[str, float]]] = defaultdict(list)
        multi_turn_hits: list[float] = []
        multi_turn_rounds_needed: list[float] = []

        for bq in shuffled:
            session = shed.suggest_tools(bq.query)

            ranked_names = [
                name for name, _ in session.ranked_tools
                if name != NONE_SENTINEL
            ]

            m = compute_metrics(ranked_names, bq.expected_tools)
            all_metrics.append(m)
            tier_metrics[bq.tier].append(m)

            is_train = id(bq) in train_set

            if holdout_fraction > 0:
                if is_train:
                    train_metrics_list.append(m)
                    train_tier[bq.tier].append(m)
                else:
                    test_metrics_list.append(m)
                    test_tier[bq.tier].append(m)

            # Multi-turn: if first suggestion misses and continuation_prob triggers
            mt_hit = m["hit@5"]
            mt_rounds_needed = 1.0
            if continuation_prob > 0 and m["p@1"] == 0 and random.random() < continuation_prob:
                # Reject all — submit NONE feedback
                if not baseline and is_train:
                    none_reviews = [ToolReview(tool_name=NONE_SENTINEL, rating="unrelated")]
                    shed.review_tools(session, none_reviews)

                # Continue session
                session2 = shed.continue_session(session)
                ranked_names2 = [
                    name for name, _ in session2.ranked_tools
                    if name != NONE_SENTINEL
                ]
                m2 = compute_metrics(ranked_names2, bq.expected_tools)
                mt_rounds_needed = 2.0
                if m2["hit@5"] > 0:
                    mt_hit = 1.0

                # Provide feedback on second round too
                if not baseline and is_train:
                    feedback2 = _simulate_feedback(
                        ranked_names2, bq, tool_categories,
                        noise=feedback_noise, noise_model=noise_model,
                    )
                    shed.review_tools(session2, feedback2)
            else:
                # Normal feedback path
                if not baseline and is_train:
                    feedback = _simulate_feedback(
                        ranked_names, bq, tool_categories,
                        noise=feedback_noise, noise_model=noise_model,
                    )
                    shed.review_tools(session, feedback)

            multi_turn_hits.append(mt_hit)
            multi_turn_rounds_needed.append(mt_rounds_needed)

        if not baseline and compact_every > 0 and round_num % compact_every == 0:
            shed.compact()

        def avg_metrics(metrics_list: list[dict[str, float]]) -> dict[str, float]:
            if not metrics_list:
                return {}
            keys = metrics_list[0].keys()
            return {k: sum(m[k] for m in metrics_list) / len(metrics_list) for k in keys}

        result = {
            "round": round_num,
            "overall": avg_metrics(all_metrics),
            "tier_1": avg_metrics(tier_metrics[1]),
            "tier_2": avg_metrics(tier_metrics[2]),
            "tier_3": avg_metrics(tier_metrics[3]),
        }

        # Multi-turn aggregate metrics
        if continuation_prob > 0:
            result["overall"]["multi_turn_hit"] = (
                sum(multi_turn_hits) / len(multi_turn_hits) if multi_turn_hits else 0
            )
            result["overall"]["multi_turn_rounds"] = (
                sum(multi_turn_rounds_needed) / len(multi_turn_rounds_needed)
                if multi_turn_rounds_needed else 0
            )

        # Holdout metrics
        if holdout_fraction > 0:
            result["train_overall"] = avg_metrics(train_metrics_list)
            result["test_overall"] = avg_metrics(test_metrics_list)
            for t in (1, 2, 3):
                result[f"test_tier_{t}"] = avg_metrics(test_tier[t])

        round_results.append(result)

    return round_results


def _bootstrap_ci(
    values: list[float], n_bootstrap: int = 10000, ci: float = 0.95
) -> tuple[float, float]:
    """Compute bootstrap confidence interval for the mean."""
    n = len(values)
    if n < 2:
        mean = values[0] if values else 0.0
        return (mean, mean)
    rng = random.Random(0)  # deterministic bootstrap
    means = []
    for _ in range(n_bootstrap):
        sample = [values[rng.randint(0, n - 1)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    alpha = (1 - ci) / 2
    lo = means[int(alpha * n_bootstrap)]
    hi = means[int((1 - alpha) * n_bootstrap)]
    return (lo, hi)


def _avg_across_seeds(all_runs: list[list[dict]]) -> list[dict]:
    """Average metrics across multiple seed runs, also compute stddev and CIs."""
    n_rounds = len(all_runs[0])
    n_seeds = len(all_runs)
    compute_ci = n_seeds >= 3
    averaged = []

    # Discover all section keys from first run's first round
    sample_round = all_runs[0][0]
    section_keys = [k for k in sample_round if isinstance(sample_round[k], dict)]

    for r_idx in range(n_rounds):
        result = {"round": all_runs[0][r_idx]["round"]}
        for section in section_keys:
            # Skip rounds where this section doesn't exist in all runs
            if not all(section in run[r_idx] for run in all_runs):
                continue
            section_data = [run[r_idx][section] for run in all_runs]
            if not section_data or not section_data[0]:
                continue
            keys = section_data[0].keys()
            section_avg = {}
            section_std = {}
            section_ci = {}
            for k in keys:
                vals = [d[k] for d in section_data]
                mean = sum(vals) / n_seeds
                variance = sum((v - mean) ** 2 for v in vals) / n_seeds
                section_avg[k] = mean
                section_std[k] = math.sqrt(variance)
                if compute_ci:
                    section_ci[k] = _bootstrap_ci(vals)
            result[section] = section_avg
            result[f"{section}_std"] = section_std
            if compute_ci:
                result[f"{section}_ci"] = section_ci
        averaged.append(result)

    return averaged


def _wilcoxon_test(x: list[float], y: list[float]) -> dict:
    """Paired Wilcoxon signed-rank test. Returns {"statistic": float, "p_value": float}.

    Falls back gracefully if scipy not available or sample too small.
    """
    try:
        from scipy.stats import wilcoxon
        if len(x) < 6:
            return {"statistic": 0.0, "p_value": 1.0}
        stat, p = wilcoxon(x, y, alternative="two-sided")
        return {"statistic": float(stat), "p_value": float(p)}
    except (ImportError, ValueError):
        return {"statistic": 0.0, "p_value": 1.0}


def run_simulation(
    n_rounds: int = 10,
    seed: int = 42,
    config: MillwrightConfig | None = None,
    n_seeds: int = 1,
    feedback_noise: float = 0.0,
    noise_model: str = "uniform",
    holdout_fraction: float = 0.0,
    continuation_prob: float = 0.0,
) -> dict:
    """Run full benchmark: adaptive + baseline, optionally over multiple seeds.

    Returns dict with keys:
      - "adaptive": list of per-round metric dicts
      - "baseline": list of per-round metric dicts (semantic-only)
      - "n_seeds": number of seeds used
      - "feedback_noise": noise level used
      - "significance": dict with Wilcoxon tests (if n_seeds >= 3)
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
            noise_model=noise_model,
            holdout_fraction=holdout_fraction,
            continuation_prob=continuation_prob,
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

    result = {
        "adaptive": adaptive,
        "baseline": baseline,
        "n_seeds": n_seeds,
        "feedback_noise": feedback_noise,
    }

    # Statistical significance tests (compare per-query final-round metrics)
    if n_seeds >= 3:
        sig = {"wilcoxon": {}, "adaptive_final_ci": {}}
        for metric in ["mrr", "p@1", "hit@5"]:
            adaptive_vals = [run[-1]["overall"][metric] for run in adaptive_runs]
            baseline_vals = [run[-1]["overall"][metric] for run in baseline_runs]
            sig["wilcoxon"][metric] = _wilcoxon_test(adaptive_vals, baseline_vals)
            sig["adaptive_final_ci"][metric] = _bootstrap_ci(adaptive_vals)
        result["significance"] = sig

    return result


def run_baselines(
    seed: int = 42,
    config: MillwrightConfig | None = None,
    n_seeds: int = 1,
) -> list[dict]:
    """Run all baseline rankers (random, TF-IDF, semantic-only) and collect metrics.

    Each baseline gets the same query order per seed. No feedback loop.

    Returns:
      [{"label": str, "metrics": {"overall": {...}, "tier_1": {...}, ...}}, ...]
    """
    config = config or MillwrightConfig()
    tools = get_tools()
    queries = get_queries()
    embedder = Embedder(config)

    seeds = [seed + i for i in range(n_seeds)]

    baseline_configs = [
        ("Random", "random"),
        ("TF-IDF", "tfidf"),
        ("Semantic", "semantic"),
    ]

    results = []
    for label, method in baseline_configs:
        all_seed_metrics = []
        for s in seeds:
            random.seed(s)
            shuffled = list(queries)
            random.shuffle(shuffled)

            all_metrics: list[dict[str, float]] = []
            tier_metrics: dict[int, list[dict[str, float]]] = defaultdict(list)

            if method == "semantic":
                # Use Toolshed with no feedback (single round)
                decomposer = MockDecomposer()
                shed = Toolshed(
                    tools=tools, decomposer=decomposer,
                    config=config, embedder=embedder,
                )
                shed.clear_data()

                for bq in shuffled:
                    session = shed.suggest_tools(bq.query)
                    ranked_names = [
                        name for name, _ in session.ranked_tools
                        if name != NONE_SENTINEL
                    ]
                    m = compute_metrics(ranked_names, bq.expected_tools)
                    all_metrics.append(m)
                    tier_metrics[bq.tier].append(m)
            else:
                for bq in shuffled:
                    if method == "random":
                        scores = random_rank(tools)
                    else:  # tfidf
                        scores = tfidf_rank(bq.query, tools)

                    ranked_names = sorted(scores, key=scores.get, reverse=True)[:config.top_k]
                    m = compute_metrics(ranked_names, bq.expected_tools)
                    all_metrics.append(m)
                    tier_metrics[bq.tier].append(m)

            def avg_metrics(metrics_list):
                if not metrics_list:
                    return {}
                keys = metrics_list[0].keys()
                return {k: sum(m[k] for m in metrics_list) / len(metrics_list) for k in keys}

            all_seed_metrics.append({
                "overall": avg_metrics(all_metrics),
                "tier_1": avg_metrics(tier_metrics[1]),
                "tier_2": avg_metrics(tier_metrics[2]),
                "tier_3": avg_metrics(tier_metrics[3]),
            })

        # Average across seeds
        if n_seeds > 1:
            avg = {}
            for section in ["overall", "tier_1", "tier_2", "tier_3"]:
                keys = all_seed_metrics[0][section].keys()
                avg[section] = {
                    k: sum(d[section][k] for d in all_seed_metrics) / n_seeds
                    for k in keys
                }
        else:
            avg = all_seed_metrics[0]

        results.append({"label": label, "metrics": avg})

    return results


def run_slot_sweep(
    configs: list[tuple[int, int]] | None = None,
    n_rounds: int = 10,
    seed: int = 42,
    config: MillwrightConfig | None = None,
    feedback_noise: float = 0.0,
    noise_model: str = "uniform",
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
            noise_model=noise_model,
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
    noise_model: str = "uniform",
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
            noise_model=noise_model,
        )
        results.append({
            "label": label,
            "preset": preset,
            "rounds": rounds,
        })

    return results


def run_compaction_sweep(
    frequencies: list[int] | None = None,
    n_rounds: int = 10,
    seed: int = 42,
    config: MillwrightConfig | None = None,
    feedback_noise: float = 0.0,
    noise_model: str = "uniform",
) -> list[dict]:
    """Sweep compaction frequency: how often to run compact().

    Returns a list of dicts:
      {"label", "compact_every", "rounds": [...]}
    """
    if frequencies is None:
        frequencies = [1, 2, 5, 10, 20]

    base_config = config or MillwrightConfig()
    tools = get_tools()
    tool_categories = {t.name: t.category for t in tools}
    queries = get_queries()
    embedder = Embedder(base_config)

    results = []
    for freq in frequencies:
        rounds = _run_single(
            n_rounds, seed, base_config, embedder, queries, tool_categories,
            baseline=False, feedback_noise=feedback_noise,
            noise_model=noise_model,
            compact_every=freq,
        )
        results.append({
            "label": f"Every {freq}" if freq > 1 else "Every round",
            "compact_every": freq,
            "rounds": rounds,
        })

    return results
