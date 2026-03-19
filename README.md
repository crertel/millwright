# Millwright

Adaptive tool selection for AI agents. Millwright learns from feedback to recommend better tools over time, combining semantic search with historical fitness scores.

Based on the design described in [Millwright: Smarter Tool Selection with Adaptive Toolsheds](https://minor.gripe/posts/2026-03-13-millwright_smarter_tool_selection_with_adaptive_toolsheds/).

## How it works

An agent calls `suggest_tools(query)` and gets back a ranked list of candidate tools. After using a tool, the agent calls `review_tools(session, reviews)` with a fitness rating (`perfect`, `related`, `unrelated`, or `broken`). Over time, this feedback loop improves which tools get surfaced for similar queries.

The pipeline:

1. **Decompose** the query into atomic subqueries
2. **Embed** subqueries and tool descriptions with `all-MiniLM-L6-v2`
3. **Semantic rank** — cosine similarity between subquery and tool embeddings (max across subqueries)
4. **Historical rank** — look up similar past queries in the review index, weight by fitness and similarity
5. **Fuse** — interleave both rankings with holdout guarantees (at least N slots from each signal), then rerank by combined score
6. **Explore** — epsilon-greedy random injection (10%) to discover underused tools
7. Return top-k candidates plus a `__none__` sentinel

Feedback flows back through an append-only review log. Periodically, K-means compaction clusters the log into a compact review index for fast lookup.

## Project structure

```
millwright/              # Core library
  toolshed.py            # Main orchestrator — suggest_tools() and review_tools()
  ranking.py             # Semantic ranking, historical ranking, holdout fusion
  compaction.py          # K-means clustering of review log into review index
  config.py              # All hyperparameters in one dataclass
  models.py              # Data structures (ToolDefinition, ReviewEntry, etc.)
  embedder.py            # SentenceTransformer wrapper with caching
  decomposer.py          # Query decomposition (mock + Claude API)
  storage.py             # JSONL review log + JSON review index

benchmark/               # Evaluation framework
  run_benchmark.py       # Entry point — learning curve, sweeps, baselines
  simulation.py          # Multi-round simulation with simulated agent feedback
  baselines.py           # Random and TF-IDF baseline rankers
  tools.py               # 200 synthetic tools across 12 domains
  queries.py             # 120 benchmark queries in 3 difficulty tiers
  metrics.py             # MRR, Precision@k, Hit@k
  report.py              # D3.js HTML report generation
```

## Getting started

### With Nix (recommended)

```sh
nix develop          # Sets up Python 3.12 venv + installs deps
```

### Without Nix

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Run the benchmark

```sh
# Full benchmark (100 rounds, all sweeps, baselines, holdout, multi-turn)
python -m benchmark.run_benchmark --rounds 100 --seeds 3 --holdout 0.2 --continuation-prob 0.3

# Quick check (10 rounds, no sweeps or baselines)
python -m benchmark.run_benchmark --rounds 10 --no-sweep --no-fitness-sweep --no-baselines --no-compaction-sweep

# Multi-seed averaging with noisy feedback (correlated noise model)
python -m benchmark.run_benchmark --rounds 100 --seeds 5 --noise 0.1 --noise-model correlated

# Export structured results for external analysis
python -m benchmark.run_benchmark --results-json results.json

# Load narrative descriptions from a JSON file
python -m benchmark.run_benchmark --descriptions descriptions.json

# Custom output path
python -m benchmark.run_benchmark -o my_report.html
```

The benchmark produces a `benchmark_report.html` with interactive D3 charts. Without `--descriptions`, the report renders charts and tables only (no interpretive text). Pass a JSON file mapping section keys to prose to populate narrative blocks.

## Benchmark results

200 tools across 12 domains, 120 queries in 3 tiers:

| Tier | Count | Description | Example |
|------|-------|-------------|---------|
| 1 — Direct | 45 | Query closely matches tool description | "read a file" |
| 2 — Indirect | 40 | Rephrased/colloquial query | "check what's inside this document" |
| 3 — Ambiguous | 35 | Vague, multiple correct tools | "get the data" |

Results from a 100-round, 3-seed run with 20% holdout and multi-turn testing:

**Baselines (single-pass, no feedback):**

| Method | MRR | P@1 | Hit@5 | T3 MRR |
|--------|-----|-----|-------|--------|
| Random | 0.018 | 0.006 | 0.050 | 0.023 |
| TF-IDF | 0.617 | 0.550 | 0.708 | 0.549 |
| Semantic-only | 0.796 | 0.700 | 0.928 | 0.743 |
| **Adaptive (R100)** | **0.879** | **0.825** | **0.956** | **0.890** |

**Learning curve (adaptive, 3-seed average):**

| Round | MRR | P@1 | Hit@5 | T3 MRR |
|-------|-----|-----|-------|--------|
| 1 | 0.797 | 0.700 | 0.933 | 0.743 |
| 5 | 0.863 | 0.811 | 0.942 | 0.845 |
| 10 | 0.863 | 0.806 | 0.950 | 0.820 |
| 50 | 0.870 | 0.817 | 0.950 | 0.871 |
| 100 | 0.879 | 0.825 | 0.956 | 0.890 |

**Sweep highlights:**
- Slot holdout: S4/H1 (mostly semantic + 1 historical slot) best at MRR=0.936
- Fitness multipliers: "Mild" and "Wide" tied at MRR=0.908; "Flat" (no learning signal) drops to 0.660
- Compaction frequency: every 1–2 rounds optimal; every 10+ rounds degrades to no-learning baseline

**Train/test holdout (20% held out, no feedback):** Train MRR reaches 0.943 while test MRR settles at 0.626 — a large gap. This is expected: the toolshed is designed to memorize which tools work for queries the agent actually asks. The improvement is concentrated on seen queries, which is the intended use case. Test set performance stays well above Random (0.018) and TF-IDF (0.617), showing some generalization through embedding similarity in the review index.

Open `benchmark_report.html` for full interactive charts including holdout evaluation, baseline comparison, multi-turn results, and all sweep visualizations.

## Algorithm deep dives

Where to look if you want to understand or modify specific parts:

| Topic | File | What to read |
|-------|------|--------------|
| Core loop | `millwright/toolshed.py` | `suggest_tools()` and `review_tools()` are the two API entry points |
| Ranking signals | `millwright/ranking.py` | `semantic_rank()`, `historical_rank()`, and `fuse_rankings()` |
| Fusion strategy | `millwright/ranking.py:93` | Holdout + interleave + rerank — the key design choice |
| Review compaction | `millwright/compaction.py` | K-means clustering with centroid-weighted fitness aggregation |
| Hyperparameters | `millwright/config.py` | Every tunable knob in one place |
| NONE sentinel | `millwright/toolshed.py:117` | Implicit negative feedback when agent rejects all suggestions |
| Feedback simulation | `benchmark/simulation.py:57` | How the benchmark generates perfect/related/unrelated ratings |
| Query difficulty tiers | `benchmark/queries.py` | The 120 test queries with ground truth |

## Hacking on things

### Tune hyperparameters

Everything is in `millwright/config.py`. The most impactful knobs:

- `min_semantic_slots` / `min_historical_slots` — how many top-k slots are guaranteed from each ranking signal. The slot sweep in the benchmark explores this space.
- `fitness_perfect` / `fitness_related` / `fitness_unrelated` / `fitness_broken` — how aggressively feedback shifts future rankings. The fitness sweep explores this.
- `historical_similarity_threshold` (default 0.3) — minimum cosine similarity to consider a historical review relevant. Lower = more recall, more noise.
- `epsilon` (default 0.1) — probability of replacing the last suggestion with a random unexplored tool.

### Change the fusion strategy

The fusion logic lives in `ranking.py:fuse_rankings()`. The current approach is holdout + interleave + score-based rerank. If you want to try weighted sums, reciprocal rank fusion, or something else, this is the function to replace.

### Add tools or queries

- Tools: `benchmark/tools.py` — add entries to the tool list with a name, description, and category.
- Queries: `benchmark/queries.py` — add `BenchmarkQuery(query, expected_tools, category, tier)` entries.

### Swap the embedding model

Change `embedding_model` in `config.py`. The `Embedder` class in `embedder.py` wraps `sentence-transformers`, so any model it supports will work. Update `embedding_dim` to match.

### Use real query decomposition

The benchmark uses `MockDecomposer` (splits on conjunctions). For production use, `ClaudeDecomposer` in `decomposer.py` calls the Claude API to semantically decompose compound queries. Pass it to the `Toolshed` constructor instead.

### Add new ranking signals

The fusion function takes two score dicts (semantic + historical). To add a third signal (e.g., recency, popularity, cost), produce a `dict[str, float]` and modify `fuse_rankings()` to accept and interleave it.

## Benchmark limitations

### Addressed

The following issues from earlier versions have been fixed:

- **Train/test split** — `--holdout 0.2` splits queries stratified by tier. Training queries get feedback; holdout queries are evaluate-only. Test metrics measure generalization.
- **Multiple baselines** — Random, TF-IDF, and semantic-only baselines run alongside the adaptive system.
- **Statistical rigor** — Bootstrap CIs (10k resamples) when `--seeds >= 3`. Paired Wilcoxon signed-rank test for adaptive vs. baseline significance.
- **Multi-turn sessions** — `--continuation-prob 0.3` exercises `continue_session()` when P@1 misses. Tracks multi-turn hit rate and rounds needed.
- **Compaction timing** — Compaction frequency sweep tests every 1/2/5/10/20 rounds.
- **Correlated noise** — `--noise-model correlated` defines confusion pairs (file↔system, http↔cloud, database↔transform, crypto↔auth, messaging↔monitoring) with 3× degradation probability, modeling systematic agent errors rather than uniform noise.
- **Report narrative** — Interpretive text is no longer hardcoded. The report renders data only unless `--descriptions` provides a JSON file with narrative blocks.

### Still open

- **Synthetic tools with clean categories** — The 200 tools have crisp, non-overlapping categories. Real tool catalogs have fuzzy boundaries, overlapping functionality, and misleading descriptions.
- **MockDecomposer sidesteps a core feature** — The benchmark uses naive conjunction splitting, not the Claude-based decomposer. Per-subquery storage is mostly 1:1 with mock decomposition, so its value is untested.
- **No distribution shift or catalog changes** — Tools and queries are fixed for the entire run. No testing of stale reviews for removed tools, cold-start for newly added tools, or query distribution drift.
- **Metric interpretation is use-case dependent** — If agents scan all 5 suggestions, Hit@5 matters most. If they only use #1, P@1 is all that matters. The report presents all metrics without asserting which matters most.

## Fidelity notes

See `NEXT_STEPS.md` for a list of spec-alignment fixes applied against the original blog post. The core algorithm — decompose, embed, dual-rank, holdout-fuse, feedback loop, K-means compaction — matches the post. Minor gaps: the "create custom tool" option and shadow testing during compaction are not implemented.
