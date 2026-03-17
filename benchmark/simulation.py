"""Multi-round simulation loop with feedback."""

import random
from collections import defaultdict

from millwright.config import MillwrightConfig
from millwright.decomposer import MockDecomposer
from millwright.embedder import Embedder
from millwright.models import ToolReview
from millwright.toolshed import Toolshed, NONE_SENTINEL

from .queries import BenchmarkQuery
from .metrics import compute_metrics
from .tools import get_tools


def _simulate_feedback(
    ranked_tools: list[str],
    query: BenchmarkQuery,
    tool_categories: dict[str, str],
) -> list[ToolReview]:
    """Simulate agent feedback: correct -> perfect, same-category -> related, else -> unrelated."""
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
        reviews.append(ToolReview(tool_name=tool_name, rating=rating))
    return reviews


def run_simulation(
    n_rounds: int = 10,
    seed: int = 42,
    config: MillwrightConfig | None = None,
) -> list[dict]:
    """Run multi-round simulation, return per-round metrics."""
    random.seed(seed)

    config = config or MillwrightConfig()
    tools = get_tools()
    tool_categories = {t.name: t.category for t in tools}

    # Shared embedder for efficiency
    embedder = Embedder(config)
    decomposer = MockDecomposer()

    shed = Toolshed(
        tools=tools,
        decomposer=decomposer,
        config=config,
        embedder=embedder,
    )
    shed.clear_data()

    queries = []
    from .queries import get_queries
    queries = get_queries()

    round_results = []

    for round_num in range(1, n_rounds + 1):
        # Shuffle queries each round
        shuffled = list(queries)
        random.shuffle(shuffled)

        # Collect metrics by tier and overall
        all_metrics: list[dict[str, float]] = []
        tier_metrics: dict[int, list[dict[str, float]]] = defaultdict(list)

        for bq in shuffled:
            session = shed.suggest_tools(bq.query)

            # Extract tool names (excluding sentinel)
            ranked_names = [
                name for name, _ in session.ranked_tools
                if name != NONE_SENTINEL
            ]

            # Compute metrics
            m = compute_metrics(ranked_names, bq.expected_tools)
            all_metrics.append(m)
            tier_metrics[bq.tier].append(m)

            # Simulate and submit feedback
            feedback = _simulate_feedback(ranked_names, bq, tool_categories)
            shed.review_tools(session, feedback)

        # Compact after each round
        shed.compact()

        # Aggregate metrics
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
        round_results.append(result)

    return round_results
