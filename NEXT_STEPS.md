# Millwright Next Steps

Reference: [original post](https://minor.gripe/posts/2026-03-13-millwright_smarter_tool_selection_with_adaptive_toolsheds/).

## Open

### Benchmark: fuzzy/overlapping tool categories

The 200 synthetic tools have crisp, non-overlapping categories. Real catalogs have tools with ambiguous or multi-category membership. Adding intentionally misleading or overlapping descriptions would stress-test the feedback loop more realistically.

### Benchmark: distribution shift and catalog changes

Tools and queries are fixed for the entire run. No testing of stale reviews for removed tools, cold-start for newly added tools, or query distribution drift. Could add mid-benchmark tool additions/removals and novel queries in later rounds.

### Benchmark: real query decomposition

The benchmark uses `MockDecomposer` (naive conjunction splitting). Per-subquery storage is mostly 1:1 with mock decomposition, so its value is untested. Options: add a mode using `ClaudeDecomposer` (requires API key), or use a cached/precomputed decomposition set.

### Spec gap: vector store for embedding lookup

The original post calls for a vector store: "vector SQLite or `pg_vector` is enough — larger scenarios would want something like Pinecone or Clickhouse." Currently `semantic_rank()` and `historical_rank()` brute-force loop over all tools/index entries computing dot products, and the review index is a flat JSON file. This is fine at 200 tools but won't scale. Swapping the inner loops for ANN queries against sqlite-vec, pgvector, or FAISS would match the spec without changing the ranking API (functions already return `dict[str, float]`).

### Spec gap: "create custom tool" option

The original post describes the ability for agents to create new tools when none of the suggestions fit. Not implemented.

### Spec gap: shadow testing during compaction

The original post mentions validating the compacted index against the raw log to catch regressions. Not implemented.

## Completed

### Benchmark: train/test holdout split

`--holdout 0.2` splits queries stratified by tier. Training queries get feedback; holdout queries are evaluate-only. Test metrics measure generalization separately from memorization.

### Benchmark: multiple baselines (random, TF-IDF, semantic)

`run_baselines()` evaluates random, TF-IDF cosine similarity, and semantic-only rankers alongside the adaptive system. `--no-baselines` to skip.

### Benchmark: bootstrap CIs and significance tests

Bootstrap confidence intervals (10k resamples) computed when `--seeds >= 3`. Paired Wilcoxon signed-rank test for adaptive vs. baseline. CI bands render on charts.

### Benchmark: multi-turn session testing

`--continuation-prob 0.3` exercises `continue_session()` when P@1 misses. Tracks multi-turn hit rate and rounds needed. Validates the rejected-tool filtering API.

### Benchmark: compaction frequency sweep

Sweeps compaction every 1/2/5/10/20 rounds. Shows that every 1–2 rounds is optimal; every 10+ degrades to no-learning baseline. `--no-compaction-sweep` to skip.

### Benchmark: correlated noise model

`--noise-model correlated` uses confusion pairs (file↔system, http↔cloud, database↔transform, crypto↔auth, messaging↔monitoring) with 3× degradation probability, modeling systematic agent errors.

### Benchmark: report narrative separation

Report no longer hardcodes interpretive text. Renders charts and tables only unless `--descriptions` provides a JSON file mapping section keys to prose.

### Benchmark: JSON export

`--results-json` saves all structured results for external analysis.

### Fidelity: fusion with interleave holdout

Replaced weighted score sum with interleave fusion. `fuse_rankings` guarantees N slots from each signal via `min_semantic_slots` / `min_historical_slots`, fills rest by interleaving.

### Fidelity: NONE sentinel logs unrelated for all presented tools

`review_tools` detects NONE in review list. All presented tools not otherwise reviewed get implicit `unrelated` entries.

### Fidelity: distance threshold on historical lookup

`historical_similarity_threshold=0.3` in config. `historical_rank` skips index entries below threshold.

### Fidelity: compaction weights fitness by distance to centroid

`compact_reviews` uses cosine similarity of each review embedding to its cluster centroid as weight when averaging fitness.

### Fidelity: multi-round sessions with rejected-tool filtering

`excluded` param on `suggest_tools` and `continue_session` method on `Toolshed`. Now exercised by benchmark via `--continuation-prob`.

### Fidelity: per-subquery embedding storage

`review_tools` stores one `ReviewEntry` per subquery embedding rather than collapsing to the mean.
