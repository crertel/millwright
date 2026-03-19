# Millwright Fidelity Fixes

Ranked by impact on system behavior. Reference: [original post](https://minor.gripe/posts/2026-03-13-millwright_smarter_tool_selection_with_adaptive_toolsheds/).

## 1. ~~Fusion: interleave with holdout (not weighted sum)~~ DONE

Replaced weighted score sum with interleave fusion. `fuse_rankings` now takes `top_k`, `min_semantic_slots`, `min_historical_slots` — guarantees N slots from each signal, fills rest by interleaving. Config params: `min_semantic_slots=2`, `min_historical_slots=1`. Weight sweep replaced with slot holdout sweep.

## 2. ~~NONE sentinel logs unrelated for all presented tools~~ DONE

`review_tools` now detects NONE in review list. When present, all presented tools not otherwise explicitly reviewed get an implicit `unrelated` entry logged.

## 3. ~~Distance threshold on historical lookup~~ DONE

Added `historical_similarity_threshold=0.3` to config. `historical_rank` skips index entries below threshold. Cuts noise from unrelated query regions.

## 4. ~~Compaction: weight fitness by distance to centroid~~ DONE

`compact_reviews` now computes cosine similarity of each review embedding to its cluster centroid and uses that as the weight when averaging fitness. Reviews near the center of a cluster have more influence.

## 5. Multi-round sessions with rejected-tool filtering — DONE (code only)

Added `excluded` param to `suggest_tools` and `continue_session` method to `Toolshed`. Both `semantic_rank` and `historical_rank` accept an `excluded` set. Not exercised by benchmark (single-shot per query) but the API is there.

## 6. Per-subquery embedding storage — DONE

`review_tools` now stores one `ReviewEntry` per subquery embedding rather than collapsing to the mean. With MockDecomposer this is mostly 1:1, but the mechanism is correct for real decomposition.
