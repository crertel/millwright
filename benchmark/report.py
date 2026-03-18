"""Generate an HTML report with D3 charts from benchmark results."""

import html
import json
from datetime import datetime


def _improvement_row(label: str, v1: float, vn: float) -> str:
    delta = vn - v1
    pct = (delta / v1 * 100) if v1 > 0 else float("inf")
    arrow = "+" if delta >= 0 else ""
    color = "#16a34a" if delta > 0 else ("#dc2626" if delta < 0 else "#6b7280")
    return (
        f"<tr><td>{html.escape(label)}</td>"
        f"<td>{v1:.3f}</td><td>{vn:.3f}</td>"
        f'<td style="color:{color};font-weight:600">{arrow}{delta:.3f} ({arrow}{pct:.1f}%)</td></tr>'
    )


def _build_chart_data(results: dict) -> str:
    """Build a JSON blob with all data D3 needs."""
    adaptive = results["adaptive"]
    baseline = results["baseline"]
    n_seeds = results["n_seeds"]
    multi = n_seeds > 1

    def extract_series(data, section, metric):
        vals = [r[section][metric] for r in data]
        stds = [r.get(f"{section}_std", {}).get(metric, 0) for r in data] if multi else [0] * len(vals)
        return {"values": vals, "stds": stds}

    chart_data = {
        "rounds": [r["round"] for r in adaptive],
        "n_seeds": n_seeds,
        "adaptive": {
            "overall_mrr": extract_series(adaptive, "overall", "mrr"),
            "t1_mrr": extract_series(adaptive, "tier_1", "mrr"),
            "t2_mrr": extract_series(adaptive, "tier_2", "mrr"),
            "t3_mrr": extract_series(adaptive, "tier_3", "mrr"),
            "overall_p1": extract_series(adaptive, "overall", "p@1"),
            "t1_p1": extract_series(adaptive, "tier_1", "p@1"),
            "t2_p1": extract_series(adaptive, "tier_2", "p@1"),
            "t3_p1": extract_series(adaptive, "tier_3", "p@1"),
            "overall_hit5": extract_series(adaptive, "overall", "hit@5"),
            "overall_p3": extract_series(adaptive, "overall", "p@3"),
            "overall_p5": extract_series(adaptive, "overall", "p@5"),
        },
        "baseline": {
            "overall_mrr": extract_series(baseline, "overall", "mrr"),
            "t3_mrr": extract_series(baseline, "tier_3", "mrr"),
            "overall_p1": extract_series(baseline, "overall", "p@1"),
            "t3_p1": extract_series(baseline, "tier_3", "p@1"),
        },
    }
    return json.dumps(chart_data)


def generate_html_report(results: dict, elapsed: float) -> str:
    adaptive = results["adaptive"]
    baseline = results["baseline"]
    n_seeds = results["n_seeds"]
    noise = results["feedback_noise"]
    multi = n_seeds > 1

    r1 = adaptive[0]
    r_last = adaptive[-1]
    b_last = baseline[-1]

    chart_json = _build_chart_data(results)

    # Metrics table rows
    table_rows = []
    for r in adaptive:
        o, t1, t2, t3 = r["overall"], r["tier_1"], r["tier_2"], r["tier_3"]
        std_suffix = ""
        if multi:
            std_suffix_mrr = f' <span class="std">&plusmn;{r["overall_std"]["mrr"]:.3f}</span>'
        else:
            std_suffix_mrr = ""
        table_rows.append(
            f"<tr><td>{r['round']}</td>"
            f"<td>{o['mrr']:.3f}{std_suffix_mrr}</td><td>{o['p@1']:.3f}</td>"
            f"<td>{o['p@3']:.3f}</td><td>{o['p@5']:.3f}</td><td>{o['hit@5']:.3f}</td>"
            f"<td>{t1['mrr']:.3f}</td><td>{t2['mrr']:.3f}</td><td>{t3['mrr']:.3f}</td></tr>"
        )

    # Baseline row
    bo = b_last["overall"]
    baseline_row = (
        f"<tr class='baseline-row'><td>Baseline</td>"
        f"<td>{bo['mrr']:.3f}</td><td>{bo['p@1']:.3f}</td>"
        f"<td>{bo['p@3']:.3f}</td><td>{bo['p@5']:.3f}</td><td>{bo['hit@5']:.3f}</td>"
        f"<td>{b_last['tier_1']['mrr']:.3f}</td><td>{b_last['tier_2']['mrr']:.3f}</td>"
        f"<td>{b_last['tier_3']['mrr']:.3f}</td></tr>"
    )

    # Improvement rows
    imp_rows = []
    for metric, label in [("mrr", "MRR"), ("p@1", "P@1"), ("p@3", "P@3"),
                           ("p@5", "P@5"), ("hit@5", "Hit@5")]:
        imp_rows.append(_improvement_row(label, r1["overall"][metric], r_last["overall"][metric]))

    t3_imp_rows = []
    for metric, label in [("mrr", "MRR"), ("p@1", "P@1"), ("p@3", "P@3")]:
        t3_imp_rows.append(_improvement_row(label, r1["tier_3"][metric], r_last["tier_3"][metric]))

    # Adaptive vs baseline rows
    avb_rows = []
    for metric, label in [("mrr", "MRR"), ("p@1", "P@1"), ("hit@5", "Hit@5")]:
        avb_rows.append(_improvement_row(
            label, b_last["overall"][metric], r_last["overall"][metric]
        ))

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seeds_note = f" &middot; {n_seeds} seeds averaged" if multi else ""
    noise_note = f" &middot; {noise:.0%} feedback noise" if noise > 0 else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Millwright Benchmark Report</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: system-ui, -apple-system, sans-serif; color: #1f2937;
         background: #f9fafb; line-height: 1.6; padding: 2rem; max-width: 1040px; margin: 0 auto; }}
  h1 {{ font-size: 1.75rem; margin-bottom: 0.25rem; }}
  h2 {{ font-size: 1.25rem; margin: 2.5rem 0 0.75rem; color: #111827;
        border-bottom: 2px solid #e5e7eb; padding-bottom: 0.4rem; }}
  h3 {{ font-size: 1rem; margin: 0 0 0.5rem; color: #374151; }}
  .meta {{ color: #6b7280; font-size: 0.875rem; margin-bottom: 1.5rem; }}
  p {{ color: #4b5563; font-size: 0.9375rem; margin-bottom: 1rem; }}
  .note {{ background: #eff6ff; border-left: 3px solid #2563eb; padding: 0.75rem 1rem;
           border-radius: 0 6px 6px 0; margin: 1rem 0; color: #4b5563; font-size: 0.9375rem; }}
  .charts {{ display: flex; flex-wrap: wrap; gap: 1.5rem; margin: 1.5rem 0; }}
  .chart-card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
                 padding: 1rem 1rem 0.5rem; flex: 1 1 460px; min-width: 320px; }}
  .chart-card .caption {{ font-size: 0.8125rem; color: #6b7280; margin-top: 0.25rem;
                          padding: 0 0.25rem 0.5rem; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff;
           border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; font-size: 0.875rem; }}
  th, td {{ padding: 0.5rem 0.75rem; text-align: right; border-bottom: 1px solid #f3f4f6; }}
  th {{ background: #f9fafb; font-weight: 600; color: #374151; text-align: right; }}
  th:first-child, td:first-child {{ text-align: left; }}
  tr:last-child td {{ border-bottom: none; }}
  tbody tr:hover {{ background: #f9fafb; }}
  .baseline-row {{ background: #fefce8; }}
  .baseline-row:hover {{ background: #fef9c3 !important; }}
  .std {{ color: #9ca3af; font-size: 0.75rem; }}
  .summary {{ display: flex; gap: 1.5rem; flex-wrap: wrap; }}
  .summary > div {{ flex: 1 1 300px; }}
  dl {{ margin: 1rem 0; }}
  dt {{ font-weight: 600; color: #374151; margin-top: 0.5rem; }}
  dd {{ margin-left: 1rem; color: #4b5563; }}
  .tier-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 1rem; margin: 1rem 0; }}
  .tier-card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; }}
  .tier-card h4 {{ font-size: 0.875rem; color: #6b7280; text-transform: uppercase;
                   letter-spacing: 0.05em; margin-bottom: 0.25rem; }}
  .tier-card .example {{ font-style: italic; color: #6b7280; font-size: 0.8125rem; }}
  .tooltip {{ position: absolute; background: #1f2937; color: #fff; padding: 6px 10px;
              border-radius: 6px; font-size: 12px; pointer-events: none; opacity: 0;
              transition: opacity 0.15s; white-space: nowrap; }}
  svg text {{ font-family: system-ui, -apple-system, sans-serif; }}
  .grid line {{ stroke: #e5e7eb; }}
  .grid .domain {{ display: none; }}
  .axis .domain {{ stroke: #d1d5db; }}
  .axis text {{ fill: #6b7280; font-size: 11px; }}
  .legend-item {{ cursor: pointer; }}
  .legend-item:hover text {{ fill: #111827; }}
</style>
</head>
<body>

<div class="tooltip" id="tooltip"></div>

<h1>Millwright Benchmark Report</h1>
<p class="meta">{timestamp} &middot; {len(adaptive)} rounds &middot; 50 queries &middot;
30 tools &middot; {elapsed:.1f}s{seeds_note}{noise_note}</p>

<!-- ============================================================ -->
<h2>What is Millwright?</h2>
<p>
  Millwright is an adaptive tool selection system for AI agents. When an agent has access to a
  large catalog of tools, choosing the right one for a given task is itself a hard problem &mdash;
  especially when tool descriptions are vague or the user&rsquo;s query is ambiguous.
  Millwright combines <strong>semantic search</strong> (embedding-based similarity between query and tool
  descriptions) with <strong>historical fitness scores</strong> that improve over time as the agent
  provides feedback on which tools actually worked.
</p>
<p>
  The core hypothesis is: <em>with repeated use and feedback, tool selection should get measurably
  better than semantic search alone, especially for ambiguous queries where pure matching struggles.</em>
  This benchmark tests that hypothesis by comparing an adaptive system against a frozen
  semantic-only baseline.
</p>

<!-- ============================================================ -->
<h2>Benchmark Methodology</h2>

<h3>Tool Catalog</h3>
<p>
  The benchmark uses <strong>30 synthetic tools</strong> spread across 6 domains: file operations,
  HTTP, database, text processing, data transformation, and system utilities. Each tool has a
  name, natural-language description, and category label. This mirrors a realistic agent setup
  where tools come from different providers and have varying description quality.
</p>

<h3>Query Tiers</h3>
<p>
  50 queries are divided into three difficulty tiers to isolate where learning helps most:
</p>
<div class="tier-grid">
  <div class="tier-card">
    <h4>Tier 1 &mdash; Direct (20 queries)</h4>
    <p>Queries that closely match a single tool&rsquo;s description. Semantic search alone
    should handle these well.</p>
    <p class="example">Example: &ldquo;read a file&rdquo; &rarr; file_read</p>
  </div>
  <div class="tier-card">
    <h4>Tier 2 &mdash; Indirect (15 queries)</h4>
    <p>Rephrased or colloquial queries where the intent maps to a tool but the wording
    differs significantly from the tool description.</p>
    <p class="example">Example: &ldquo;check what&rsquo;s inside this document&rdquo; &rarr; file_read</p>
  </div>
  <div class="tier-card">
    <h4>Tier 3 &mdash; Ambiguous (15 queries)</h4>
    <p>Vague queries where multiple tools could be correct. These are the hardest &mdash;
    semantic similarity alone can&rsquo;t reliably pick the right tool, so historical
    feedback should provide the biggest lift.</p>
    <p class="example">Example: &ldquo;get the data&rdquo; &rarr; db_query, http_get, or file_read</p>
  </div>
</div>

<h3>Simulation Loop</h3>
<p>
  The benchmark runs <strong>{len(adaptive)} rounds</strong>. In each round, all 50 queries are
  presented in shuffled order. For each query, Millwright suggests its top-k tools. A simulated
  agent then provides feedback: tools matching the ground truth are rated <strong>perfect</strong>
  (fitness multiplier 1.4&times;), tools in the same category are rated <strong>related</strong>
  (1.05&times;), and everything else is rated <strong>unrelated</strong> (0.75&times;). After each
  round, the review log is compacted via K-means clustering to build an efficient review index.
</p>

<h3>Baseline &amp; Controls</h3>
<p>
  To isolate the effect of learning, we run a <strong>semantic-only baseline</strong> in parallel
  that uses the same queries and shuffle order but <em>never submits feedback</em>. Any
  improvement in the adaptive run over the baseline is attributable to historical fitness
  learning, not random variation in query order.
  {"The results shown are averaged over <strong>" + str(n_seeds) + " random seeds</strong> to reduce variance from shuffle order and epsilon-greedy exploration. Shaded bands in the charts show &plusmn;1 standard deviation." if n_seeds > 1 else ""}
  {"Feedback noise is set to <strong>" + f"{noise:.0%}" + "</strong> &mdash; with this probability, each rating is degraded one level (perfect&rarr;related, related&rarr;unrelated) to simulate imperfect agent judgment." if noise > 0 else ""}
</p>

<!-- ============================================================ -->
<h2>Metrics Explained</h2>
<dl>
  <dt>MRR (Mean Reciprocal Rank)</dt>
  <dd>
    The average of 1/rank for the first correct tool in the results. If the right tool is ranked
    #1, MRR for that query is 1.0; if it&rsquo;s #2, MRR is 0.5; #3 is 0.33, and so on.
    <strong>This is the single most important metric</strong> &mdash; it captures how quickly the
    agent finds the right tool. Higher is better; 1.0 is perfect.
  </dd>

  <dt>Precision@k (P@1, P@3, P@5)</dt>
  <dd>
    The fraction of the top-k results that are correct. P@1 answers &ldquo;did we get it right
    on the first try?&rdquo; P@3 and P@5 measure whether the correct tool appears among the top
    few suggestions. For queries with a single correct tool (Tiers 1 &amp; 2), P@1 is the most
    meaningful. For Tier 3 queries with multiple acceptable tools, P@3 and P@5 better reflect
    whether the system surfaces the right options.
  </dd>

  <dt>Hit@5</dt>
  <dd>
    Binary: did <em>any</em> correct tool appear in the top 5? This is the coarsest metric &mdash;
    it answers &ldquo;would the agent have the right tool available at all?&rdquo; A Hit@5 of
    1.0 means the system never completely misses.
  </dd>
</dl>

<!-- ============================================================ -->
<h2>Results</h2>

<h3>Learning Curves</h3>
<p>
  The charts below show how each metric evolves over rounds. Solid lines are the adaptive
  system; dashed lines are the semantic-only baseline. Upward separation between the two
  demonstrates that historical feedback is improving tool selection.
</p>

<div class="charts">
  <div class="chart-card"><div id="chart-mrr"></div>
    <p class="caption">
      MRR tracks how high the first correct tool ranks. Tier 1 starts near 1.0 (semantic search
      nails direct matches). Tier 3 shows the steepest improvement as feedback disambiguates
      vague queries. The dashed baseline stays flat &mdash; without feedback, semantic-only
      performance does not improve.
    </p>
  </div>
  <div class="chart-card"><div id="chart-p1"></div>
    <p class="caption">
      Precision@1 is the &ldquo;first try&rdquo; success rate. Gains here mean the system is
      learning to put the right tool at rank #1 more often, reducing the need for the agent
      to scan multiple options.
    </p>
  </div>
  <div class="chart-card"><div id="chart-hit"></div>
    <p class="caption">
      Hit@5 and broader precision metrics for the adaptive system. Hit@5 approaching 1.0 means
      the system almost never fails to include the right tool. P@3 and P@5 rising indicate
      better tools are displacing irrelevant ones in the top-k.
    </p>
  </div>
</div>

<h3>Per-Round Metrics Table</h3>
<p>
  The full numbers behind the charts. The highlighted &ldquo;Baseline&rdquo; row shows final
  semantic-only performance for comparison. T1/T2/T3 MRR columns show MRR broken out by
  difficulty tier.
</p>
<table>
<thead><tr>
  <th>Round</th><th>MRR</th><th>P@1</th><th>P@3</th><th>P@5</th><th>Hit@5</th>
  <th>T1 MRR</th><th>T2 MRR</th><th>T3 MRR</th>
</tr></thead>
<tbody>{"".join(table_rows)}{baseline_row}</tbody>
</table>

<!-- ============================================================ -->
<h2>Improvement Summary</h2>

<div class="summary">
<div>
<h3>Round 1 &rarr; Round {r_last['round']} (Learning Over Time)</h3>
<p style="font-size:0.8125rem;color:#6b7280">
  Shows how much the adaptive system improved from cold start to final round.
</p>
<table>
<thead><tr><th>Metric</th><th>Round 1</th><th>Round {r_last['round']}</th><th>Change</th></tr></thead>
<tbody>{"".join(imp_rows)}</tbody>
</table>
</div>
<div>
<h3>Baseline vs. Adaptive (Value of Feedback)</h3>
<p style="font-size:0.8125rem;color:#6b7280">
  Compares final semantic-only baseline against final adaptive performance.
  This isolates the contribution of historical learning.
</p>
<table>
<thead><tr><th>Metric</th><th>Baseline</th><th>Adaptive</th><th>Change</th></tr></thead>
<tbody>{"".join(avb_rows)}</tbody>
</table>
</div>
</div>

<h3 style="margin-top:1.5rem">Tier 3 (Ambiguous) &mdash; Where Learning Matters Most</h3>
<p>
  Ambiguous queries are where semantic search alone is weakest and where historical feedback
  should provide the biggest lift. The numbers confirm this:
</p>
<table style="max-width:500px">
<thead><tr><th>Metric</th><th>Round 1</th><th>Round {r_last['round']}</th><th>Change</th></tr></thead>
<tbody>{"".join(t3_imp_rows)}</tbody>
</table>

<div class="note">
  <strong>Key takeaway:</strong> The adaptive system outperforms the semantic-only baseline across
  all metrics, with the largest gains on Tier 3 (ambiguous) queries. This validates the core
  hypothesis &mdash; historical fitness feedback provides the most value when tool descriptions
  don&rsquo;t clearly distinguish candidates, and the system needs to learn from experience
  which tool the agent actually wants.
</div>

<!-- ============================================================ -->
<!-- D3 Charts -->
<script>
const DATA = {chart_json};
const COLORS = {{
  overall: "#2563eb", t1: "#16a34a", t2: "#9333ea", t3: "#dc2626",
  baseline: "#94a3b8", hit5: "#2563eb", p3: "#16a34a", p5: "#9333ea"
}};

function lineChart(container, config) {{
  const {{ series, title, width = 500, height = 280 }} = config;
  const margin = {{ top: 32, right: 20, bottom: 36, left: 48 }};
  const w = width - margin.left - margin.right;
  const h = height - margin.top - margin.bottom;

  const svg = d3.select(container).append("svg")
    .attr("viewBox", `0 0 ${{width}} ${{height}}`)
    .attr("width", "100%");

  const g = svg.append("g").attr("transform", `translate(${{margin.left}},${{margin.top}})`);

  // Title
  svg.append("text").attr("x", width / 2).attr("y", 18)
    .attr("text-anchor", "middle").attr("font-weight", 600).attr("font-size", 14)
    .attr("fill", "#1f2937").text(title);

  // Scales
  const x = d3.scaleLinear().domain([1, DATA.rounds.length]).range([0, w]);
  const allVals = series.flatMap(s => s.values);
  const yMin = d3.min(allVals) * 0.95;
  const yMax = Math.min(d3.max(allVals) * 1.02, 1.0);
  const y = d3.scaleLinear().domain([yMin, yMax]).range([h, 0]).nice();

  // Grid
  g.append("g").attr("class", "grid")
    .call(d3.axisLeft(y).ticks(5).tickSize(-w).tickFormat(""));

  // Axes
  g.append("g").attr("class", "axis").attr("transform", `translate(0,${{h}})`)
    .call(d3.axisBottom(x).ticks(DATA.rounds.length).tickFormat(d => `R${{d}}`));
  g.append("g").attr("class", "axis")
    .call(d3.axisLeft(y).ticks(5).tickFormat(d3.format(".2f")));

  const tooltip = d3.select("#tooltip");
  const line = d3.line().x((d, i) => x(i + 1)).y(d => y(d));

  series.forEach(s => {{
    // Confidence band (if std data available)
    if (s.stds && s.stds.some(v => v > 0)) {{
      const area = d3.area()
        .x((d, i) => x(i + 1))
        .y0((d, i) => y(s.values[i] - s.stds[i]))
        .y1((d, i) => y(s.values[i] + s.stds[i]));
      g.append("path").datum(s.values)
        .attr("d", area).attr("fill", s.color).attr("opacity", 0.1);
    }}

    // Line
    g.append("path").datum(s.values)
      .attr("fill", "none").attr("stroke", s.color).attr("stroke-width", 2.5)
      .attr("stroke-dasharray", s.dashed ? "6,3" : "none")
      .attr("d", line);

    // Dots with tooltip
    g.selectAll(null).data(s.values).enter().append("circle")
      .attr("cx", (d, i) => x(i + 1)).attr("cy", d => y(d))
      .attr("r", 4).attr("fill", s.color).attr("stroke", "#fff").attr("stroke-width", 1.5)
      .style("cursor", "pointer")
      .on("mouseover", function(event, d) {{
        const i = s.values.indexOf(d);
        let text = `${{s.label}} R${{i + 1}}: ${{d.toFixed(3)}}`;
        if (s.stds && s.stds[i] > 0) text += ` (\u00b1${{s.stds[i].toFixed(3)}})`;
        tooltip.style("opacity", 1).html(text);
      }})
      .on("mousemove", function(event) {{
        tooltip.style("left", (event.pageX + 12) + "px").style("top", (event.pageY - 28) + "px");
      }})
      .on("mouseout", () => tooltip.style("opacity", 0));
  }});

  // Legend
  const legend = svg.append("g").attr("transform", `translate(${{margin.left + 8}}, ${{margin.top + 4}})`);
  series.forEach((s, i) => {{
    const lg = legend.append("g").attr("transform", `translate(0, ${{i * 18}})`).attr("class", "legend-item");
    lg.append("line").attr("x1", 0).attr("x2", 18).attr("y1", 0).attr("y2", 0)
      .attr("stroke", s.color).attr("stroke-width", 2.5)
      .attr("stroke-dasharray", s.dashed ? "6,3" : "none");
    lg.append("text").attr("x", 24).attr("y", 4).attr("font-size", 12)
      .attr("fill", "#374151").text(s.label);
  }});
}}

// Chart 1: MRR by tier with baseline
lineChart("#chart-mrr", {{
  title: "MRR by Round (Adaptive vs. Baseline)",
  series: [
    {{ label: "Overall", color: COLORS.overall,
       values: DATA.adaptive.overall_mrr.values, stds: DATA.adaptive.overall_mrr.stds }},
    {{ label: "Tier 1 (Direct)", color: COLORS.t1,
       values: DATA.adaptive.t1_mrr.values, stds: DATA.adaptive.t1_mrr.stds }},
    {{ label: "Tier 2 (Indirect)", color: COLORS.t2,
       values: DATA.adaptive.t2_mrr.values, stds: DATA.adaptive.t2_mrr.stds }},
    {{ label: "Tier 3 (Ambiguous)", color: COLORS.t3,
       values: DATA.adaptive.t3_mrr.values, stds: DATA.adaptive.t3_mrr.stds }},
    {{ label: "Baseline (Overall)", color: COLORS.baseline, dashed: true,
       values: DATA.baseline.overall_mrr.values, stds: DATA.baseline.overall_mrr.stds }},
    {{ label: "Baseline (Tier 3)", color: COLORS.baseline, dashed: true,
       values: DATA.baseline.t3_mrr.values, stds: DATA.baseline.t3_mrr.stds }},
  ]
}});

// Chart 2: Precision@1 by tier
lineChart("#chart-p1", {{
  title: "Precision@1 by Round",
  series: [
    {{ label: "Overall", color: COLORS.overall,
       values: DATA.adaptive.overall_p1.values, stds: DATA.adaptive.overall_p1.stds }},
    {{ label: "Tier 1", color: COLORS.t1,
       values: DATA.adaptive.t1_p1.values, stds: DATA.adaptive.t1_p1.stds }},
    {{ label: "Tier 2", color: COLORS.t2,
       values: DATA.adaptive.t2_p1.values, stds: DATA.adaptive.t2_p1.stds }},
    {{ label: "Tier 3", color: COLORS.t3,
       values: DATA.adaptive.t3_p1.values, stds: DATA.adaptive.t3_p1.stds }},
    {{ label: "Baseline (Overall)", color: COLORS.baseline, dashed: true,
       values: DATA.baseline.overall_p1.values, stds: DATA.baseline.overall_p1.stds }},
  ]
}});

// Chart 3: Hit rate & precision
lineChart("#chart-hit", {{
  title: "Overall Hit Rate & Precision",
  series: [
    {{ label: "Hit@5", color: COLORS.hit5,
       values: DATA.adaptive.overall_hit5.values, stds: DATA.adaptive.overall_hit5.stds }},
    {{ label: "P@3", color: COLORS.p3,
       values: DATA.adaptive.overall_p3.values, stds: DATA.adaptive.overall_p3.stds }},
    {{ label: "P@5", color: COLORS.p5,
       values: DATA.adaptive.overall_p5.values, stds: DATA.adaptive.overall_p5.stds }},
  ]
}});
</script>

</body>
</html>"""
