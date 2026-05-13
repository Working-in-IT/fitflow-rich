"""Funnel Analyzer (FitFlow variant).

Takes a list of funnel steps + user counts at each step, optionally per segment,
and produces:
- per-step table: step_conversion, overall_conversion, dropoff_n, dropoff_pct
- biggest drop-off by impact score (default: absolute dropoff)
- segment ranking by overall conversion

Adapted from https://github.com/nimrodfisher/data-analytics-skills (funnel-analysis)
with additions for: segments, business-outcome value_per_user, JSON output.
Data source: SQLite events table in data/fitflow.db.

Usage:
    python3 funnel_analyzer.py --demo
    python3 funnel_analyzer.py --steps "Open Editor,Execute,Save,Share" --counts "12000,7200,5500,1200"
    python3 funnel_analyzer.py --csv funnel.csv --steps-col step --counts-col users --segment-col segment
    python3 funnel_analyzer.py --json funnel_data.json --output report.md
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def analyze_funnel(steps: list[str], counts: list[int], value_per_user: float = 1.0) -> list[dict]:
    """Compute per-step funnel metrics. Pure function, no I/O."""
    if len(steps) != len(counts):
        raise ValueError(f"steps ({len(steps)}) and counts ({len(counts)}) must have equal length")
    if not steps:
        raise ValueError("Funnel must have at least one step")
    if counts[0] <= 0:
        raise ValueError("Step 1 count must be > 0 (defines the funnel denominator)")

    top = counts[0]
    results = []
    for i, (step, count) in enumerate(zip(steps, counts)):
        prev = counts[i - 1] if i > 0 else count
        step_conv = count / prev if prev > 0 else 0
        overall = count / top if top > 0 else 0
        dropoff = prev - count if i > 0 else 0
        results.append({
            "step_index": i + 1,
            "step": step,
            "users": count,
            "step_conversion": round(step_conv, 6),
            "step_conversion_pct": round(step_conv * 100, 2),
            "overall_conversion": round(overall, 6),
            "overall_conversion_pct": round(overall * 100, 2),
            "dropoff_n": dropoff,
            "dropoff_pct": round((1 - step_conv) * 100, 2) if i > 0 else 0,
            "impact_score": round(dropoff * value_per_user, 2),
        })
    return results


def biggest_dropoff(rows: list[dict]) -> dict | None:
    """Return the step with the largest impact score (dropoff_n × value_per_user)."""
    if len(rows) < 2:
        return None
    return max(rows[1:], key=lambda r: r["impact_score"])


def analyze_segments(segments: dict[str, tuple[list[str], list[int]]],
                     value_per_user: float = 1.0) -> list[dict]:
    """Run funnel per segment, rank by overall conversion.

    segments: { "FL Marketing": (["s1", "s2", "s3"], [412, 200, 74]), ... }
    """
    out = []
    for name, (steps, counts) in segments.items():
        try:
            funnel = analyze_funnel(steps, counts, value_per_user=value_per_user)
        except ValueError as e:
            out.append({"segment": name, "error": str(e)})
            continue
        out.append({
            "segment": name,
            "step1_users": funnel[0]["users"],
            "final_users": funnel[-1]["users"],
            "overall_conversion_pct": funnel[-1]["overall_conversion_pct"],
            "biggest_dropoff_step": biggest_dropoff(funnel)["step"] if len(funnel) > 1 else None,
            "rows": funnel,
        })
    out.sort(key=lambda s: s.get("overall_conversion_pct", -1), reverse=True)
    return out


def format_funnel_table(rows: list[dict], title: str = "Funnel Analysis") -> str:
    """Markdown table + text summary suitable for findings.md / REPORT.md."""
    lines = [f"## {title}", "", "| # | Step | Users | Step conv | Overall conv | Drop-off |",
             "|---|------|------:|----------:|-------------:|---------:|"]
    for r in rows:
        if r["step_index"] == 1:
            dropoff_str = "—"
            step_conv_str = "—"
        else:
            dropoff_str = f"−{r['dropoff_n']:,} (−{r['dropoff_pct']:.1f}%)"
            step_conv_str = f"{r['step_conversion_pct']:.1f}%"
        lines.append(
            f"| {r['step_index']} | {r['step']} | {r['users']:,} | "
            f"{step_conv_str} | {r['overall_conversion_pct']:.1f}% | {dropoff_str} |"
        )
    top = biggest_dropoff(rows)
    lines += ["", f"**Overall conversion:** {rows[-1]['overall_conversion_pct']:.1f}%"]
    if top:
        lines += [
            "",
            f"**Highest impact drop-off:** {top['step']} (step {top['step_index']})",
            f"- Drop-off: {top['dropoff_n']:,} users ({top['dropoff_pct']:.1f}% of prior step)",
            f"- Impact score: {top['impact_score']:,.2f}",
        ]
    return "\n".join(lines)


def format_segments_table(segments: list[dict], title: str = "Segment Breakdown") -> str:
    lines = [f"## {title}", "",
             "| Segment | Step1 users | Final users | Overall conv | Biggest drop-off step |",
             "|---------|------------:|------------:|-------------:|----------------------|"]
    for s in segments:
        if "error" in s:
            lines.append(f"| {s['segment']} | — | — | — | error: {s['error']} |")
            continue
        lines.append(
            f"| {s['segment']} | {s['step1_users']:,} | {s['final_users']:,} | "
            f"{s['overall_conversion_pct']:.1f}% | {s['biggest_dropoff_step'] or '—'} |"
        )
    return "\n".join(lines)


def load_from_csv(path: str, steps_col: str, counts_col: str,
                  segment_col: str | None = None) -> tuple[list, list] | dict:
    """Returns (steps, counts) if no segment_col; else dict[segment] -> (steps, counts)."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if segment_col:
        by_seg: dict[str, tuple[list, list]] = {}
        for row in rows:
            seg = row[segment_col].strip() or "<unknown>"
            steps, counts = by_seg.setdefault(seg, ([], []))
            steps.append(row[steps_col].strip())
            counts.append(int(row[counts_col]))
        return by_seg
    steps = [row[steps_col].strip() for row in rows]
    counts = [int(row[counts_col]) for row in rows]
    return steps, counts


def load_from_json(path: str) -> dict:
    """JSON shape: {"steps": [...], "counts": [...], "segments": {name: counts, ...}, "value_per_user": float}"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    p = argparse.ArgumentParser(description="Analyze a conversion funnel with optional segments.")
    p.add_argument("--demo", action="store_true", help="Run a baked-in demo")
    p.add_argument("--steps", help="Comma-separated step names")
    p.add_argument("--counts", help="Comma-separated user counts, same length as --steps")
    p.add_argument("--csv", dest="csv_path", help="CSV with funnel data (one row per step)")
    p.add_argument("--steps-col", default="step")
    p.add_argument("--counts-col", default="users")
    p.add_argument("--segment-col", default=None,
                   help="If CSV has this column, run per-segment funnel")
    p.add_argument("--json", dest="json_path",
                   help="JSON: {steps, counts, segments?, value_per_user?}")
    p.add_argument("--value-per-user", type=float, default=1.0,
                   help="Weight per user (for impact score). Use business-outcome value if known.")
    p.add_argument("--title", default="Funnel Analysis")
    p.add_argument("--output", help="Write markdown report to file")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = p.parse_args()

    if args.demo:
        steps = ["Registration", "Onboarding Step 1", "Onboarding Step 2", "Onboarding Complete", "Subscription Started"]
        counts = [3_000, 3_000, 2_120, 1_785, 1_200]
        segments = {
            "Persona: Weight Loss": (steps, [900, 900, 680, 590, 420]),
            "Persona: Muscle Gain": (steps, [750, 750, 540, 460, 340]),
            "Persona: General Fitness": (steps, [620, 620, 420, 340, 210]),
            "Persona: Unknown": (steps, [730, 730, 480, 395, 230]),
        }
        rows = analyze_funnel(steps, counts, args.value_per_user)
        seg_rows = analyze_segments(segments, args.value_per_user)
        report = "\n\n".join([
            format_funnel_table(rows, "Demo: FitFlow onboarding → subscription funnel"),
            format_segments_table(seg_rows),
        ])
        print(report)
        return

    rows = None
    segments = None
    if args.json_path:
        data = load_from_json(args.json_path)
        rows = analyze_funnel(data["steps"], data["counts"],
                              data.get("value_per_user", args.value_per_user))
        if "segments" in data:
            seg_input = {name: (data["steps"], counts) for name, counts in data["segments"].items()}
            segments = analyze_segments(seg_input, data.get("value_per_user", args.value_per_user))
    elif args.csv_path:
        loaded = load_from_csv(args.csv_path, args.steps_col, args.counts_col, args.segment_col)
        if args.segment_col:
            seg_input = {name: (steps, counts) for name, (steps, counts) in loaded.items()}
            # Use first segment's row order to derive overall rows; or aggregate.
            all_steps = next(iter(seg_input.values()))[0]
            agg_counts = [
                sum(counts[i] for steps, counts in seg_input.values() if i < len(counts))
                for i in range(len(all_steps))
            ]
            rows = analyze_funnel(all_steps, agg_counts, args.value_per_user)
            segments = analyze_segments(seg_input, args.value_per_user)
        else:
            steps, counts = loaded  # type: ignore[misc]
            rows = analyze_funnel(steps, counts, args.value_per_user)
    elif args.steps and args.counts:
        steps = [s.strip() for s in args.steps.split(",")]
        counts = [int(c.strip()) for c in args.counts.split(",")]
        rows = analyze_funnel(steps, counts, args.value_per_user)
    else:
        p.error("Provide --steps + --counts, --csv, --json, or --demo")

    if args.format == "json":
        out = {"funnel": rows, "segments": segments, "biggest_dropoff": biggest_dropoff(rows)}
        text = json.dumps(out, indent=2, ensure_ascii=False)
    else:
        parts = [format_funnel_table(rows, args.title)]
        if segments:
            parts.append(format_segments_table(segments))
        text = "\n\n".join(parts)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(text)


if __name__ == "__main__":
    main()
