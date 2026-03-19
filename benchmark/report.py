"""Generate an HTML report with D3 charts from benchmark results."""

import html
import json
from datetime import datetime

MILESTONES = [1, 5, 10, 25, 50, 100]


def _improvement_row(label: str, v1: float, vn: float, ci: tuple[float, float] | None = None) -> str:
    delta = vn - v1
    pct = (delta / v1 * 100) if v1 > 0 else float("inf")
    arrow = "+" if delta >= 0 else ""
    color = "#16a34a" if delta > 0 else ("#dc2626" if delta < 0 else "#6b7280")
    ci_html = ""
    if ci is not None:
        ci_html = f' <span class="std">[{ci[0]:.3f}, {ci[1]:.3f}]</span>'
    return (
        f"<tr><td>{html.escape(label)}</td>"
        f"<td>{v1:.3f}</td><td>{vn:.3f}{ci_html}</td>"
        f'<td style="color:{color};font-weight:600">{arrow}{delta:.3f} ({arrow}{pct:.1f}%)</td></tr>'
    )


def _desc(descriptions: dict[str, str] | None, key: str) -> str:
    """Look up a description block; return empty string if missing."""
    if descriptions is None:
        return ""
    return descriptions.get(key, "")


def _desc_block(descriptions: dict[str, str] | None, key: str, tag: str = "p") -> str:
    """Wrap a description in an HTML tag if present, else empty string."""
    text = _desc(descriptions, key)
    if not text:
        return ""
    return f"<{tag}>{text}</{tag}>"


def _desc_note(descriptions: dict[str, str] | None, key: str) -> str:
    """Render a description as a styled note block if present."""
    text = _desc(descriptions, key)
    if not text:
        return ""
    return f'<div class="note">{text}</div>'


def _build_chart_data(
    results: dict,
    sweep: list[dict] | None,
    fitness: list[dict] | None,
    baselines: list[dict] | None = None,
    compaction_sweep: list[dict] | None = None,
) -> str:
    """Build a JSON blob with all data D3 needs."""
    adaptive = results["adaptive"]
    baseline = results["baseline"]
    n_seeds = results["n_seeds"]
    multi = n_seeds > 1

    def extract_series(data, section, metric):
        vals = [r[section][metric] for r in data if section in r]
        stds = [r.get(f"{section}_std", {}).get(metric, 0) for r in data] if multi else [0] * len(vals)
        cis = []
        for r in data:
            ci_key = f"{section}_ci"
            if ci_key in r and metric in r[ci_key]:
                cis.append(r[ci_key][metric])
            else:
                cis.append(None)
        return {"values": vals, "stds": stds, "cis": cis}

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

    # Test-set series (holdout evaluation)
    if any("test_overall" in r for r in adaptive):
        chart_data["adaptive_test"] = {
            "overall_mrr": extract_series(adaptive, "test_overall", "mrr"),
            "t1_mrr": extract_series(adaptive, "test_tier_1", "mrr"),
            "t2_mrr": extract_series(adaptive, "test_tier_2", "mrr"),
            "t3_mrr": extract_series(adaptive, "test_tier_3", "mrr"),
            "overall_p1": extract_series(adaptive, "test_overall", "p@1"),
            "overall_hit5": extract_series(adaptive, "test_overall", "hit@5"),
        }
        chart_data["adaptive_train"] = {
            "overall_mrr": extract_series(adaptive, "train_overall", "mrr"),
            "overall_p1": extract_series(adaptive, "train_overall", "p@1"),
            "overall_hit5": extract_series(adaptive, "train_overall", "hit@5"),
        }

    if sweep:
        chart_data["sweep"] = []
        for entry in sweep:
            final = entry["rounds"][-1]
            chart_data["sweep"].append({
                "label": entry["label"],
                "sem_slots": entry.get("min_semantic_slots", 0),
                "hist_slots": entry.get("min_historical_slots", 0),
                "overall_mrr": final["overall"]["mrr"],
                "t1_mrr": final["tier_1"]["mrr"],
                "t2_mrr": final["tier_2"]["mrr"],
                "t3_mrr": final["tier_3"]["mrr"],
                "overall_p1": final["overall"]["p@1"],
                "t3_p1": final["tier_3"]["p@1"],
            })

    if fitness:
        chart_data["fitness"] = []
        for entry in fitness:
            final = entry["rounds"][-1]
            chart_data["fitness"].append({
                "label": entry["label"],
                "preset": entry["preset"],
                "overall_mrr": final["overall"]["mrr"],
                "t1_mrr": final["tier_1"]["mrr"],
                "t2_mrr": final["tier_2"]["mrr"],
                "t3_mrr": final["tier_3"]["mrr"],
                "overall_p1": final["overall"]["p@1"],
                "t3_p1": final["tier_3"]["p@1"],
                "overall_hit5": final["overall"]["hit@5"],
            })

    if baselines:
        chart_data["baselines"] = []
        for entry in baselines:
            chart_data["baselines"].append({
                "label": entry["label"],
                "overall_mrr": entry["metrics"]["overall"]["mrr"],
                "overall_p1": entry["metrics"]["overall"]["p@1"],
                "overall_hit5": entry["metrics"]["overall"]["hit@5"],
                "t1_mrr": entry["metrics"].get("tier_1", {}).get("mrr", 0),
                "t2_mrr": entry["metrics"].get("tier_2", {}).get("mrr", 0),
                "t3_mrr": entry["metrics"].get("tier_3", {}).get("mrr", 0),
            })

    if compaction_sweep:
        chart_data["compaction"] = []
        for entry in compaction_sweep:
            final = entry["rounds"][-1]
            chart_data["compaction"].append({
                "label": entry["label"],
                "compact_every": entry["compact_every"],
                "overall_mrr": final["overall"]["mrr"],
                "t1_mrr": final["tier_1"]["mrr"],
                "t2_mrr": final["tier_2"]["mrr"],
                "t3_mrr": final["tier_3"]["mrr"],
                "overall_p1": final["overall"]["p@1"],
                "t3_p1": final["tier_3"]["p@1"],
            })

    return json.dumps(chart_data)


def generate_html_report(
    results: dict,
    sweep: list[dict] | None,
    fitness: list[dict] | None,
    elapsed: float,
    n_tools: int = 30,
    n_queries: int = 50,
    n_categories: int = 6,
    tier_counts: tuple[int, int, int] = (20, 15, 15),
    descriptions: dict[str, str] | None = None,
    baselines: list[dict] | None = None,
    compaction_sweep: list[dict] | None = None,
) -> str:
    adaptive = results["adaptive"]
    baseline = results["baseline"]
    n_seeds = results["n_seeds"]
    noise = results["feedback_noise"]
    multi = n_seeds > 1
    n_rounds = len(adaptive)
    t1_count, t2_count, t3_count = tier_counts

    r1 = adaptive[0]
    r_last = adaptive[-1]
    b_last = baseline[-1]

    has_holdout = "test_overall" in r_last
    has_multi_turn = "multi_turn_hit" in r_last.get("overall", {})
    has_significance = "significance" in results

    chart_json = _build_chart_data(results, sweep, fitness, baselines, compaction_sweep)

    # Milestone table rows (subset of rounds)
    milestone_rounds = [m for m in MILESTONES if m <= n_rounds]
    milestone_rows = []
    for r in adaptive:
        if r["round"] not in milestone_rounds:
            continue
        o, t1, t2, t3 = r["overall"], r["tier_1"], r["tier_2"], r["tier_3"]
        std_suffix_mrr = ""
        if multi:
            std_suffix_mrr = f' <span class="std">&plusmn;{r["overall_std"]["mrr"]:.3f}</span>'
        milestone_rows.append(
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
        ci = None
        if has_significance and metric in results.get("significance", {}).get("adaptive_final_ci", {}):
            ci = results["significance"]["adaptive_final_ci"][metric]
        imp_rows.append(_improvement_row(label, r1["overall"][metric], r_last["overall"][metric], ci))

    t3_imp_rows = []
    for metric, label in [("mrr", "MRR"), ("p@1", "P@1"), ("p@3", "P@3")]:
        t3_imp_rows.append(_improvement_row(label, r1["tier_3"][metric], r_last["tier_3"][metric]))

    # Adaptive vs baseline rows
    avb_rows = []
    for metric, label in [("mrr", "MRR"), ("p@1", "P@1"), ("hit@5", "Hit@5")]:
        avb_rows.append(_improvement_row(
            label, b_last["overall"][metric], r_last["overall"][metric]
        ))

    # Significance test results
    sig_html = ""
    if has_significance:
        sig = results["significance"]
        sig_rows = []
        for metric, label in [("mrr", "MRR"), ("p@1", "P@1"), ("hit@5", "Hit@5")]:
            if metric in sig.get("wilcoxon", {}):
                w = sig["wilcoxon"][metric]
                p_val = w["p_value"]
                star = "*" if p_val < 0.05 else ""
                color = "#16a34a" if p_val < 0.05 else "#6b7280"
                sig_rows.append(
                    f'<tr><td>{label}</td>'
                    f'<td style="color:{color};font-weight:600">p={p_val:.4f}{star}</td>'
                    f'<td>{w["statistic"]:.2f}</td></tr>'
                )
        if sig_rows:
            sig_html = f"""
<h3 style="margin-top:1.5rem">Statistical Significance (Wilcoxon Signed-Rank)</h3>
<table style="max-width:400px">
<thead><tr><th>Metric</th><th>p-value</th><th>Statistic</th></tr></thead>
<tbody>{"".join(sig_rows)}</tbody>
</table>
"""

    # Weight sweep table rows
    sweep_table = ""
    if sweep:
        sweep_rows = []
        best_mrr = max(e["rounds"][-1]["overall"]["mrr"] for e in sweep)
        for entry in sweep:
            final = entry["rounds"][-1]
            o = final["overall"]
            t3 = final["tier_3"]
            is_best = o["mrr"] == best_mrr
            cls = ' class="best-row"' if is_best else ""
            sweep_rows.append(
                f"<tr{cls}><td>{entry['label']}</td>"
                f"<td>{o['mrr']:.3f}</td><td>{o['p@1']:.3f}</td>"
                f"<td>{o['p@3']:.3f}</td><td>{o['hit@5']:.3f}</td>"
                f"<td>{t3['mrr']:.3f}</td><td>{t3['p@1']:.3f}</td></tr>"
            )
        sweep_table = f"""
<table>
<thead><tr>
  <th>Slots (S/H)</th><th>MRR</th><th>P@1</th><th>P@3</th><th>Hit@5</th>
  <th>T3 MRR</th><th>T3 P@1</th>
</tr></thead>
<tbody>{"".join(sweep_rows)}</tbody>
</table>"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seeds_note = f" &middot; {n_seeds} seeds averaged" if multi else ""
    noise_note = f" &middot; {noise:.0%} feedback noise" if noise > 0 else ""

    # Holdout section
    holdout_section = ""
    if has_holdout:
        test_last = r_last["test_overall"]
        train_last = r_last["train_overall"]
        holdout_rows = []
        for metric, label in [("mrr", "MRR"), ("p@1", "P@1"), ("hit@5", "Hit@5")]:
            train_v = train_last[metric]
            test_v = test_last[metric]
            delta = test_v - train_v
            color = "#16a34a" if delta >= 0 else "#dc2626"
            holdout_rows.append(
                f"<tr><td>{label}</td><td>{train_v:.3f}</td><td>{test_v:.3f}</td>"
                f'<td style="color:{color}">{delta:+.3f}</td></tr>'
            )
        holdout_section = f"""
<!-- ============================================================ -->
<h2>Holdout Evaluation</h2>
{_desc_block(descriptions, "holdout_eval")}
<div class="charts">
  <div class="chart-card"><div id="chart-holdout-mrr"></div></div>
  <div class="chart-card"><div id="chart-holdout-p1"></div></div>
</div>
<h3>Train vs. Test (Final Round)</h3>
<table style="max-width:500px">
<thead><tr><th>Metric</th><th>Train</th><th>Test (Holdout)</th><th>Gap</th></tr></thead>
<tbody>{"".join(holdout_rows)}</tbody>
</table>
"""

    # Baselines comparison section
    baselines_section = ""
    if baselines:
        bl_rows = []
        # Add adaptive final round as comparison
        all_entries = baselines + [{"label": f"Adaptive (R{r_last['round']})", "metrics": {
            "overall": r_last["overall"],
            "tier_1": r_last["tier_1"],
            "tier_2": r_last["tier_2"],
            "tier_3": r_last["tier_3"],
        }}]
        best_mrr = max(e["metrics"]["overall"]["mrr"] for e in all_entries)
        for entry in all_entries:
            o = entry["metrics"]["overall"]
            t3 = entry["metrics"].get("tier_3", {})
            is_best = o["mrr"] == best_mrr
            cls = ' class="best-row"' if is_best else ""
            bl_rows.append(
                f"<tr{cls}><td>{html.escape(entry['label'])}</td>"
                f"<td>{o['mrr']:.3f}</td><td>{o['p@1']:.3f}</td>"
                f"<td>{o.get('hit@5', 0):.3f}</td>"
                f"<td>{t3.get('mrr', 0):.3f}</td><td>{t3.get('p@1', 0):.3f}</td></tr>"
            )
        baselines_section = f"""
<!-- ============================================================ -->
<h2>Baseline Comparison</h2>
{_desc_block(descriptions, "baselines")}
<div class="charts">
  <div class="chart-card"><div id="chart-baselines-mrr"></div></div>
  <div class="chart-card"><div id="chart-baselines-p1"></div></div>
</div>
<table>
<thead><tr><th>Method</th><th>MRR</th><th>P@1</th><th>Hit@5</th><th>T3 MRR</th><th>T3 P@1</th></tr></thead>
<tbody>{"".join(bl_rows)}</tbody>
</table>
"""

    # Multi-turn section
    multi_turn_section = ""
    if has_multi_turn:
        mt_hit = r_last["overall"].get("multi_turn_hit", 0)
        mt_rounds = r_last["overall"].get("multi_turn_rounds", 0)
        multi_turn_section = f"""
<!-- ============================================================ -->
<h2>Multi-Turn Session Results</h2>
{_desc_block(descriptions, "multi_turn")}
<table style="max-width:400px">
<thead><tr><th>Metric</th><th>Value</th></tr></thead>
<tbody>
<tr><td>Multi-turn Hit Rate</td><td>{mt_hit:.3f}</td></tr>
<tr><td>Avg Rounds to Find Tool</td><td>{mt_rounds:.2f}</td></tr>
</tbody>
</table>
"""

    # Sweep section HTML
    sweep_section = ""
    if sweep:
        sweep_rounds = len(sweep[0]["rounds"])
        sweep_section = f"""
<!-- ============================================================ -->
<h2>Slot Holdout Sweep</h2>
{_desc_block(descriptions, "slot_sweep")}

<div class="charts">
  <div class="chart-card"><div id="chart-sweep-mrr"></div>
    {_desc_block(descriptions, "slot_sweep_mrr_caption", "p class='caption'")}
  </div>
  <div class="chart-card"><div id="chart-sweep-p1"></div>
    {_desc_block(descriptions, "slot_sweep_p1_caption", "p class='caption'")}
  </div>
</div>

<h3>Sweep Results (after {sweep_rounds} rounds)</h3>
{sweep_table}

{_desc_note(descriptions, "slot_sweep_interpretation")}
"""

    # Fitness section HTML
    fitness_section = ""
    if fitness:
        fitness_rounds = len(fitness[0]["rounds"])
        fitness_rows = []
        best_mrr = max(e["rounds"][-1]["overall"]["mrr"] for e in fitness)
        for entry in fitness:
            final = entry["rounds"][-1]
            o = final["overall"]
            t3 = final["tier_3"]
            p = entry["preset"]
            is_best = o["mrr"] == best_mrr
            cls = ' class="best-row"' if is_best else ""
            fitness_rows.append(
                f"<tr{cls}><td>{html.escape(entry['label'])}</td>"
                f"<td>{p['perfect']:.1f}</td><td>{p['related']:.2f}</td>"
                f"<td>{p['unrelated']:.2f}</td><td>{p['broken']:.2f}</td>"
                f"<td>{o['mrr']:.3f}</td><td>{o['p@1']:.3f}</td>"
                f"<td>{o['hit@5']:.3f}</td>"
                f"<td>{t3['mrr']:.3f}</td><td>{t3['p@1']:.3f}</td></tr>"
            )
        fitness_table = f"""
<table>
<thead><tr>
  <th>Preset</th><th>Perfect</th><th>Related</th><th>Unrel.</th><th>Broken</th>
  <th>MRR</th><th>P@1</th><th>Hit@5</th><th>T3 MRR</th><th>T3 P@1</th>
</tr></thead>
<tbody>{"".join(fitness_rows)}</tbody>
</table>"""

        fitness_section = f"""
<!-- ============================================================ -->
<h2>Fitness Multiplier Sweep</h2>
{_desc_block(descriptions, "fitness_sweep")}

<div class="charts">
  <div class="chart-card"><div id="chart-fitness-mrr"></div>
    {_desc_block(descriptions, "fitness_sweep_mrr_caption", "p class='caption'")}
  </div>
  <div class="chart-card"><div id="chart-fitness-p1"></div>
    {_desc_block(descriptions, "fitness_sweep_p1_caption", "p class='caption'")}
  </div>
</div>

<h3>Fitness Sweep Results (after {fitness_rounds} rounds)</h3>
{fitness_table}

{_desc_note(descriptions, "fitness_sweep_interpretation")}
"""

    # Compaction sweep section
    compaction_section = ""
    if compaction_sweep:
        comp_rounds = len(compaction_sweep[0]["rounds"])
        comp_rows = []
        best_mrr = max(e["rounds"][-1]["overall"]["mrr"] for e in compaction_sweep)
        for entry in compaction_sweep:
            final = entry["rounds"][-1]
            o = final["overall"]
            t3 = final["tier_3"]
            is_best = o["mrr"] == best_mrr
            cls = ' class="best-row"' if is_best else ""
            comp_rows.append(
                f"<tr{cls}><td>{entry['label']}</td>"
                f"<td>{o['mrr']:.3f}</td><td>{o['p@1']:.3f}</td>"
                f"<td>{o['hit@5']:.3f}</td>"
                f"<td>{t3['mrr']:.3f}</td><td>{t3['p@1']:.3f}</td></tr>"
            )
        comp_table = f"""
<table>
<thead><tr>
  <th>Frequency</th><th>MRR</th><th>P@1</th><th>Hit@5</th>
  <th>T3 MRR</th><th>T3 P@1</th>
</tr></thead>
<tbody>{"".join(comp_rows)}</tbody>
</table>"""

        compaction_section = f"""
<!-- ============================================================ -->
<h2>Compaction Frequency Sweep</h2>
{_desc_block(descriptions, "compaction_sweep")}
<div class="charts">
  <div class="chart-card"><div id="chart-compaction-mrr"></div></div>
  <div class="chart-card"><div id="chart-compaction-p1"></div></div>
</div>
<h3>Compaction Sweep Results (after {comp_rounds} rounds)</h3>
{comp_table}
{_desc_note(descriptions, "compaction_sweep_interpretation")}
"""

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
  .best-row {{ background: #f0fdf4; }}
  .best-row:hover {{ background: #dcfce7 !important; }}
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
              transition: opacity 0.15s; white-space: nowrap; z-index: 10; }}
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
<p class="meta">{timestamp} &middot; {n_rounds} rounds &middot; {n_queries} queries &middot;
{n_tools} tools &middot; {n_categories} domains &middot; {elapsed:.1f}s{seeds_note}{noise_note}</p>

{_desc_block(descriptions, "intro")}

<!-- ============================================================ -->
<h2>Metrics Explained</h2>
<dl>
  <dt>MRR (Mean Reciprocal Rank)</dt>
  <dd>Average of 1/rank for the first correct tool. 1.0 is perfect.</dd>
  <dt>Precision@k (P@1, P@3, P@5)</dt>
  <dd>Fraction of the top-k results that are correct.</dd>
  <dt>Hit@5</dt>
  <dd>Binary: did any correct tool appear in the top 5?</dd>
</dl>

{_desc_block(descriptions, "methodology")}

<!-- ============================================================ -->
<h2>Results</h2>

<h3>Learning Curves</h3>
{_desc_block(descriptions, "learning_curves")}

<div class="charts">
  <div class="chart-card"><div id="chart-mrr"></div>
    {_desc_block(descriptions, "mrr_caption", "p class='caption'")}
  </div>
  <div class="chart-card"><div id="chart-p1"></div>
    {_desc_block(descriptions, "p1_caption", "p class='caption'")}
  </div>
  <div class="chart-card"><div id="chart-hit"></div>
    {_desc_block(descriptions, "hit_caption", "p class='caption'")}
  </div>
</div>

<h3>Milestone Metrics</h3>
{_desc_block(descriptions, "milestones")}
<table>
<thead><tr>
  <th>Round</th><th>MRR</th><th>P@1</th><th>P@3</th><th>P@5</th><th>Hit@5</th>
  <th>T1 MRR</th><th>T2 MRR</th><th>T3 MRR</th>
</tr></thead>
<tbody>{"".join(milestone_rows)}{baseline_row}</tbody>
</table>

<!-- ============================================================ -->
<h2>Improvement Summary</h2>

<div class="summary">
<div>
<h3>Round 1 &rarr; Round {r_last['round']} (Learning Over Time)</h3>
{_desc_block(descriptions, "improvement")}
<table>
<thead><tr><th>Metric</th><th>Round 1</th><th>Round {r_last['round']}</th><th>Change</th></tr></thead>
<tbody>{"".join(imp_rows)}</tbody>
</table>
</div>
<div>
<h3>Baseline vs. Adaptive (Value of Feedback)</h3>
<table>
<thead><tr><th>Metric</th><th>Baseline</th><th>Adaptive</th><th>Change</th></tr></thead>
<tbody>{"".join(avb_rows)}</tbody>
</table>
</div>
</div>

<h3 style="margin-top:1.5rem">Tier 3 (Ambiguous)</h3>
{_desc_block(descriptions, "improvement_tier3")}
<table style="max-width:500px">
<thead><tr><th>Metric</th><th>Round 1</th><th>Round {r_last['round']}</th><th>Change</th></tr></thead>
<tbody>{"".join(t3_imp_rows)}</tbody>
</table>

{_desc_note(descriptions, "improvement_takeaway")}

{sig_html}

{holdout_section}

{baselines_section}

{multi_turn_section}

{sweep_section}

{fitness_section}

{compaction_section}

<!-- ============================================================ -->
<!-- D3 Charts -->
<script>
const DATA = {chart_json};
const COLORS = {{
  overall: "#2563eb", t1: "#16a34a", t2: "#9333ea", t3: "#dc2626",
  baseline: "#94a3b8", hit5: "#2563eb", p3: "#16a34a", p5: "#9333ea",
  train: "#f59e0b", test: "#ef4444"
}};

const tooltip = d3.select("#tooltip");

function lineChart(container, config) {{
  const {{ series, title, width = 500, height = 280 }} = config;
  const margin = {{ top: 32, right: 20, bottom: 36, left: 48 }};
  const w = width - margin.left - margin.right;
  const h = height - margin.top - margin.bottom;
  const nRounds = DATA.rounds.length;

  const svg = d3.select(container).append("svg")
    .attr("viewBox", `0 0 ${{width}} ${{height}}`)
    .attr("width", "100%");

  const g = svg.append("g").attr("transform", `translate(${{margin.left}},${{margin.top}})`);

  // Title
  svg.append("text").attr("x", width / 2).attr("y", 18)
    .attr("text-anchor", "middle").attr("font-weight", 600).attr("font-size", 14)
    .attr("fill", "#1f2937").text(title);

  // Scales
  const x = d3.scaleLinear().domain([1, nRounds]).range([0, w]);
  const allVals = series.flatMap(s => s.values);
  const yMin = d3.min(allVals) * 0.95;
  const yMax = Math.min(d3.max(allVals) * 1.02, 1.0);
  const y = d3.scaleLinear().domain([yMin, yMax]).range([h, 0]).nice();

  // Grid
  g.append("g").attr("class", "grid")
    .call(d3.axisLeft(y).ticks(5).tickSize(-w).tickFormat(""));

  // Axes
  const xTicks = nRounds <= 15 ? nRounds : Math.min(10, nRounds);
  g.append("g").attr("class", "axis").attr("transform", `translate(0,${{h}})`)
    .call(d3.axisBottom(x).ticks(xTicks).tickFormat(d => d));
  g.append("g").attr("class", "axis")
    .call(d3.axisLeft(y).ticks(5).tickFormat(d3.format(".2f")));

  // X axis label
  g.append("text").attr("x", w / 2).attr("y", h + 32)
    .attr("text-anchor", "middle").attr("fill", "#9ca3af").attr("font-size", 11).text("Round");

  const line = d3.line().x((d, i) => x(i + 1)).y(d => y(d));

  const showDots = nRounds <= 25;

  series.forEach(s => {{
    // CI band (preferred) or stddev band
    const hasCIs = s.cis && s.cis.some(v => v !== null);
    if (hasCIs) {{
      const area = d3.area()
        .x((d, i) => x(i + 1))
        .y0((d, i) => y(s.cis[i] ? s.cis[i][0] : s.values[i]))
        .y1((d, i) => y(s.cis[i] ? s.cis[i][1] : s.values[i]));
      g.append("path").datum(s.values)
        .attr("d", area).attr("fill", s.color).attr("opacity", 0.12);
    }} else if (s.stds && s.stds.some(v => v > 0)) {{
      const area = d3.area()
        .x((d, i) => x(i + 1))
        .y0((d, i) => y(s.values[i] - s.stds[i]))
        .y1((d, i) => y(s.values[i] + s.stds[i]));
      g.append("path").datum(s.values)
        .attr("d", area).attr("fill", s.color).attr("opacity", 0.1);
    }}

    // Line
    g.append("path").datum(s.values)
      .attr("fill", "none").attr("stroke", s.color).attr("stroke-width", 2)
      .attr("stroke-dasharray", s.dashed ? "6,3" : "none")
      .attr("d", line);

    // Dots
    const indices = showDots
      ? s.values.map((_, i) => i)
      : [0, 4, 9, 24, 49, 99].filter(i => i < s.values.length);

    g.selectAll(null).data(indices).enter().append("circle")
      .attr("cx", i => x(i + 1)).attr("cy", i => y(s.values[i]))
      .attr("r", showDots ? 3.5 : 4).attr("fill", s.color)
      .attr("stroke", "#fff").attr("stroke-width", 1.5)
      .style("cursor", "pointer")
      .on("mouseover", function(event, i) {{
        let text = `${{s.label}} R${{i + 1}}: ${{s.values[i].toFixed(3)}}`;
        if (s.stds && s.stds[i] > 0) text += ` (\u00b1${{s.stds[i].toFixed(3)}})`;
        if (s.cis && s.cis[i]) text += ` [${{s.cis[i][0].toFixed(3)}}, ${{s.cis[i][1].toFixed(3)}}]`;
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
       values: DATA.adaptive.overall_mrr.values, stds: DATA.adaptive.overall_mrr.stds,
       cis: DATA.adaptive.overall_mrr.cis }},
    {{ label: "Tier 1 (Direct)", color: COLORS.t1,
       values: DATA.adaptive.t1_mrr.values, stds: DATA.adaptive.t1_mrr.stds,
       cis: DATA.adaptive.t1_mrr.cis }},
    {{ label: "Tier 2 (Indirect)", color: COLORS.t2,
       values: DATA.adaptive.t2_mrr.values, stds: DATA.adaptive.t2_mrr.stds,
       cis: DATA.adaptive.t2_mrr.cis }},
    {{ label: "Tier 3 (Ambiguous)", color: COLORS.t3,
       values: DATA.adaptive.t3_mrr.values, stds: DATA.adaptive.t3_mrr.stds,
       cis: DATA.adaptive.t3_mrr.cis }},
    {{ label: "Baseline (Overall)", color: COLORS.baseline, dashed: true,
       values: DATA.baseline.overall_mrr.values, stds: DATA.baseline.overall_mrr.stds,
       cis: DATA.baseline.overall_mrr.cis }},
    {{ label: "Baseline (Tier 3)", color: COLORS.baseline, dashed: true,
       values: DATA.baseline.t3_mrr.values, stds: DATA.baseline.t3_mrr.stds,
       cis: DATA.baseline.t3_mrr.cis }},
  ]
}});

// Chart 2: Precision@1 by tier
lineChart("#chart-p1", {{
  title: "Precision@1 by Round",
  series: [
    {{ label: "Overall", color: COLORS.overall,
       values: DATA.adaptive.overall_p1.values, stds: DATA.adaptive.overall_p1.stds,
       cis: DATA.adaptive.overall_p1.cis }},
    {{ label: "Tier 1", color: COLORS.t1,
       values: DATA.adaptive.t1_p1.values, stds: DATA.adaptive.t1_p1.stds,
       cis: DATA.adaptive.t1_p1.cis }},
    {{ label: "Tier 2", color: COLORS.t2,
       values: DATA.adaptive.t2_p1.values, stds: DATA.adaptive.t2_p1.stds,
       cis: DATA.adaptive.t2_p1.cis }},
    {{ label: "Tier 3", color: COLORS.t3,
       values: DATA.adaptive.t3_p1.values, stds: DATA.adaptive.t3_p1.stds,
       cis: DATA.adaptive.t3_p1.cis }},
    {{ label: "Baseline (Overall)", color: COLORS.baseline, dashed: true,
       values: DATA.baseline.overall_p1.values, stds: DATA.baseline.overall_p1.stds,
       cis: DATA.baseline.overall_p1.cis }},
  ]
}});

// Chart 3: Hit rate & precision
lineChart("#chart-hit", {{
  title: "Overall Hit Rate & Precision",
  series: [
    {{ label: "Hit@5", color: COLORS.hit5,
       values: DATA.adaptive.overall_hit5.values, stds: DATA.adaptive.overall_hit5.stds,
       cis: DATA.adaptive.overall_hit5.cis }},
    {{ label: "P@3", color: COLORS.p3,
       values: DATA.adaptive.overall_p3.values, stds: DATA.adaptive.overall_p3.stds,
       cis: DATA.adaptive.overall_p3.cis }},
    {{ label: "P@5", color: COLORS.p5,
       values: DATA.adaptive.overall_p5.values, stds: DATA.adaptive.overall_p5.stds,
       cis: DATA.adaptive.overall_p5.cis }},
  ]
}});

// ============================================================
// Holdout charts
if (DATA.adaptive_test) {{
  lineChart("#chart-holdout-mrr", {{
    title: "Train vs. Test MRR",
    series: [
      {{ label: "Train MRR", color: COLORS.train,
         values: DATA.adaptive_train.overall_mrr.values, stds: DATA.adaptive_train.overall_mrr.stds,
         cis: DATA.adaptive_train.overall_mrr.cis }},
      {{ label: "Test MRR", color: COLORS.test,
         values: DATA.adaptive_test.overall_mrr.values, stds: DATA.adaptive_test.overall_mrr.stds,
         cis: DATA.adaptive_test.overall_mrr.cis }},
      {{ label: "Baseline", color: COLORS.baseline, dashed: true,
         values: DATA.baseline.overall_mrr.values, stds: DATA.baseline.overall_mrr.stds,
         cis: DATA.baseline.overall_mrr.cis }},
    ]
  }});
  lineChart("#chart-holdout-p1", {{
    title: "Train vs. Test P@1",
    series: [
      {{ label: "Train P@1", color: COLORS.train,
         values: DATA.adaptive_train.overall_p1.values, stds: DATA.adaptive_train.overall_p1.stds,
         cis: DATA.adaptive_train.overall_p1.cis }},
      {{ label: "Test P@1", color: COLORS.test,
         values: DATA.adaptive_test.overall_p1.values, stds: DATA.adaptive_test.overall_p1.stds,
         cis: DATA.adaptive_test.overall_p1.cis }},
      {{ label: "Baseline", color: COLORS.baseline, dashed: true,
         values: DATA.baseline.overall_p1.values, stds: DATA.baseline.overall_p1.stds,
         cis: DATA.baseline.overall_p1.cis }},
    ]
  }});
}}

// ============================================================
// Baseline comparison charts
if (DATA.baselines) {{
  const allBaselines = DATA.baselines.slice();
  // Add adaptive final round
  const lastRound = DATA.rounds.length - 1;
  allBaselines.push({{
    label: "Adaptive (final)",
    overall_mrr: DATA.adaptive.overall_mrr.values[lastRound],
    overall_p1: DATA.adaptive.overall_p1.values[lastRound],
    overall_hit5: DATA.adaptive.overall_hit5.values[lastRound],
    t1_mrr: DATA.adaptive.t1_mrr.values[lastRound],
    t2_mrr: DATA.adaptive.t2_mrr.values[lastRound],
    t3_mrr: DATA.adaptive.t3_mrr.values[lastRound],
  }});

  const blMrrGroups = allBaselines.map(b => ({{
    label: b.label,
    bars: [
      {{ label: "Overall", value: b.overall_mrr, color: COLORS.overall }},
      {{ label: "Tier 1", value: b.t1_mrr, color: COLORS.t1 }},
      {{ label: "Tier 2", value: b.t2_mrr, color: COLORS.t2 }},
      {{ label: "Tier 3", value: b.t3_mrr, color: COLORS.t3 }},
    ]
  }}));
  groupedBarChart("#chart-baselines-mrr", {{
    title: "MRR by Baseline Method",
    groups: blMrrGroups,
  }});

  const blP1Groups = allBaselines.map(b => ({{
    label: b.label,
    bars: [
      {{ label: "Overall P@1", value: b.overall_p1, color: COLORS.overall }},
      {{ label: "Hit@5", value: b.overall_hit5, color: COLORS.hit5 }},
    ]
  }}));
  groupedBarChart("#chart-baselines-p1", {{
    title: "P@1 & Hit@5 by Baseline Method",
    groups: blP1Groups,
  }});
}}

// ============================================================
// Shared grouped bar chart function
function groupedBarChart(container, config) {{
  const {{ groups, title, xLabel, width = 500, height = 280 }} = config;
  const margin = {{ top: 32, right: 20, bottom: 52, left: 48 }};
  const w = width - margin.left - margin.right;
  const h = height - margin.top - margin.bottom;

  const svg = d3.select(container).append("svg")
    .attr("viewBox", `0 0 ${{width}} ${{height}}`)
    .attr("width", "100%");

  const g = svg.append("g").attr("transform", `translate(${{margin.left}},${{margin.top}})`);

  svg.append("text").attr("x", width / 2).attr("y", 18)
    .attr("text-anchor", "middle").attr("font-weight", 600).attr("font-size", 14)
    .attr("fill", "#1f2937").text(title);

  const x0 = d3.scaleBand().domain(groups.map(g => g.label)).range([0, w]).padding(0.2);
  const barLabels = groups[0].bars.map(b => b.label);
  const x1 = d3.scaleBand().domain(barLabels).range([0, x0.bandwidth()]).padding(0.08);

  const allVals = groups.flatMap(g => g.bars.map(b => b.value));
  const yMin = d3.min(allVals) * 0.9;
  const yMax = Math.min(d3.max(allVals) * 1.05, 1.0);
  const y = d3.scaleLinear().domain([yMin, yMax]).range([h, 0]).nice();

  g.append("g").attr("class", "grid")
    .call(d3.axisLeft(y).ticks(5).tickSize(-w).tickFormat(""));

  g.append("g").attr("class", "axis").attr("transform", `translate(0,${{h}})`)
    .call(d3.axisBottom(x0))
    .selectAll("text").attr("transform", "rotate(-30)").attr("text-anchor", "end");
  g.append("g").attr("class", "axis")
    .call(d3.axisLeft(y).ticks(5).tickFormat(d3.format(".2f")));

  if (xLabel) {{
    g.append("text").attr("x", w / 2).attr("y", h + 48)
      .attr("text-anchor", "middle").attr("fill", "#9ca3af").attr("font-size", 11)
      .text(xLabel);
  }}

  groups.forEach(group => {{
    const gGroup = g.append("g").attr("transform", `translate(${{x0(group.label)}},0)`);
    group.bars.forEach(bar => {{
      gGroup.append("rect")
        .attr("x", x1(bar.label)).attr("y", y(bar.value))
        .attr("width", x1.bandwidth()).attr("height", h - y(bar.value))
        .attr("fill", bar.color).attr("rx", 2)
        .on("mouseover", function(event) {{
          tooltip.style("opacity", 1).html(`${{group.label}} ${{bar.label}}: ${{bar.value.toFixed(3)}}`);
        }})
        .on("mousemove", function(event) {{
          tooltip.style("left", (event.pageX + 12) + "px").style("top", (event.pageY - 28) + "px");
        }})
        .on("mouseout", () => tooltip.style("opacity", 0));
    }});
  }});

  // Legend
  const legend = svg.append("g").attr("transform", `translate(${{margin.left + 8}}, ${{margin.top + 4}})`);
  const uniqueBars = groups[0].bars;
  uniqueBars.forEach((b, i) => {{
    const lg = legend.append("g").attr("transform", `translate(${{i * 100}}, 0)`).attr("class", "legend-item");
    lg.append("rect").attr("width", 12).attr("height", 12).attr("rx", 2).attr("fill", b.color).attr("y", -6);
    lg.append("text").attr("x", 16).attr("y", 4).attr("font-size", 11).attr("fill", "#374151").text(b.label);
  }});
}}

// ============================================================
// Weight sweep charts
if (DATA.sweep) {{
  const sweepGroups = DATA.sweep.map(s => ({{
    label: s.label,
    bars: [
      {{ label: "Overall", value: s.overall_mrr, color: COLORS.overall }},
      {{ label: "Tier 1", value: s.t1_mrr, color: COLORS.t1 }},
      {{ label: "Tier 2", value: s.t2_mrr, color: COLORS.t2 }},
      {{ label: "Tier 3", value: s.t3_mrr, color: COLORS.t3 }},
    ]
  }}));

  groupedBarChart("#chart-sweep-mrr", {{
    title: "Final MRR by Slot Holdout",
    xLabel: "Semantic / Historical slots",
    groups: sweepGroups,
  }});

  const sweepP1Groups = DATA.sweep.map(s => ({{
    label: s.label,
    bars: [
      {{ label: "Overall P@1", value: s.overall_p1, color: COLORS.overall }},
      {{ label: "Tier 3 P@1", value: s.t3_p1, color: COLORS.t3 }},
    ]
  }}));

  groupedBarChart("#chart-sweep-p1", {{
    title: "Final Precision@1 by Slot Holdout",
    xLabel: "Semantic / Historical slots",
    groups: sweepP1Groups,
  }});
}}

// ============================================================
// Fitness sweep charts
if (DATA.fitness) {{
  const fitMrrGroups = DATA.fitness.map(f => ({{
    label: f.label,
    bars: [
      {{ label: "Overall", value: f.overall_mrr, color: COLORS.overall }},
      {{ label: "Tier 1", value: f.t1_mrr, color: COLORS.t1 }},
      {{ label: "Tier 2", value: f.t2_mrr, color: COLORS.t2 }},
      {{ label: "Tier 3", value: f.t3_mrr, color: COLORS.t3 }},
    ]
  }}));

  groupedBarChart("#chart-fitness-mrr", {{
    title: "Final MRR by Fitness Preset",
    groups: fitMrrGroups,
  }});

  const fitP1Groups = DATA.fitness.map(f => ({{
    label: f.label,
    bars: [
      {{ label: "Overall P@1", value: f.overall_p1, color: COLORS.overall }},
      {{ label: "Tier 3 P@1", value: f.t3_p1, color: COLORS.t3 }},
    ]
  }}));

  groupedBarChart("#chart-fitness-p1", {{
    title: "Final Precision@1 by Fitness Preset",
    groups: fitP1Groups,
  }});
}}

// ============================================================
// Compaction sweep charts
if (DATA.compaction) {{
  const compGroups = DATA.compaction.map(c => ({{
    label: c.label,
    bars: [
      {{ label: "Overall", value: c.overall_mrr, color: COLORS.overall }},
      {{ label: "Tier 1", value: c.t1_mrr, color: COLORS.t1 }},
      {{ label: "Tier 2", value: c.t2_mrr, color: COLORS.t2 }},
      {{ label: "Tier 3", value: c.t3_mrr, color: COLORS.t3 }},
    ]
  }}));
  groupedBarChart("#chart-compaction-mrr", {{
    title: "Final MRR by Compaction Frequency",
    groups: compGroups,
  }});

  const compP1Groups = DATA.compaction.map(c => ({{
    label: c.label,
    bars: [
      {{ label: "Overall P@1", value: c.overall_p1, color: COLORS.overall }},
      {{ label: "Tier 3 P@1", value: c.t3_p1, color: COLORS.t3 }},
    ]
  }}));
  groupedBarChart("#chart-compaction-p1", {{
    title: "Final P@1 by Compaction Frequency",
    groups: compP1Groups,
  }});
}}
</script>

</body>
</html>"""
