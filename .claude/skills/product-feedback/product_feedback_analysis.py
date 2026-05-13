"""
Product Feedback Analysis — batch queries against FitFlow feedback table (SQLite).

Runs all standard NPS/CSAT queries and outputs structured JSON.
Designed to be called from Claude Code skills.

NPS formula (adapted for 5-point scale):
    NPS = 100 * (promoters - detractors) / total
    - Promoters: rating = 5 (only top score)
    - Detractors: rating IN (1, 2)
    - Passives: rating IN (3, 4) — not counted, but included in total

feedback table schema:
    feedback_id, user_id, feedback_date, channel, rating, text, platform

Token-optimized output:
    --output FILE   Write full JSON (with text feedback) to FILE,
                    print only compact stats (no text) to stdout.
    Without --output: print everything to stdout (legacy mode).

Usage:
    python product_feedback_analysis.py --db data/fitflow.db --output /tmp/fb.json
    python product_feedback_analysis.py --db data/fitflow.db --days 90

Requires: Python stdlib only (sqlite3, argparse, json).
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path


def get_connection(db_path: str) -> sqlite3.Connection:
    """Open SQLite connection with row factory for dict-style access."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def run_query(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    """Execute SQL and return list of dicts."""
    cursor = conn.execute(sql, params)
    return [dict(row) for row in cursor.fetchall()]


def overall_summary(conn: sqlite3.Connection, days: int) -> list[dict]:
    """Overall summary stats."""
    return run_query(conn, """
        SELECT
            COUNT(*) AS total_ratings,
            COUNT(DISTINCT user_id) AS unique_users,
            ROUND(AVG(CAST(rating AS REAL)), 2) AS avg_rating,
            ROUND(
                (SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END)
                 - SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END))
                * 100.0 / COUNT(*),
                1
            ) AS nps_score,
            SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END) AS detractors,
            SUM(CASE WHEN rating IN (3, 4) THEN 1 ELSE 0 END) AS passives,
            SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) AS promoters,
            SUM(CASE WHEN text IS NOT NULL AND text != '' THEN 1 ELSE 0 END) AS with_text,
            MIN(feedback_date) AS earliest_survey,
            MAX(feedback_date) AS latest_survey
        FROM feedback
        WHERE rating IS NOT NULL
          AND date(feedback_date) >= date((SELECT MAX(feedback_date) FROM feedback), ? || ' days')
    """, (f"-{days}",))


def weekly_nps_trend(conn: sqlite3.Connection, days: int) -> list[dict]:
    """Weekly NPS trend for the last N days."""
    return run_query(conn, """
        SELECT
            strftime('%Y-%W', feedback_date) AS week,
            COUNT(*) AS total,
            SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) AS promoters,
            SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END) AS detractors,
            ROUND(AVG(CAST(rating AS REAL)), 2) AS avg_rating,
            ROUND(
                (SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END)
                 - SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END))
                * 100.0 / COUNT(*),
                1
            ) AS nps_score
        FROM feedback
        WHERE rating IS NOT NULL
          AND date(feedback_date) >= date((SELECT MAX(feedback_date) FROM feedback), ? || ' days')
        GROUP BY strftime('%Y-%W', feedback_date)
        ORDER BY week DESC
    """, (f"-{days}",))


def rating_distribution(conn: sqlite3.Connection, days: int) -> list[dict]:
    """Distribution of ratings 1-5."""
    return run_query(conn, """
        SELECT
            rating,
            COUNT(*) AS cnt,
            ROUND(
                COUNT(*) * 100.0 / (
                    SELECT COUNT(*) FROM feedback
                    WHERE rating IS NOT NULL
                      AND date(feedback_date) >= date((SELECT MAX(feedback_date) FROM feedback), ? || ' days')
                ),
                1
            ) AS pct
        FROM feedback
        WHERE rating IS NOT NULL
          AND date(feedback_date) >= date((SELECT MAX(feedback_date) FROM feedback), ? || ' days')
        GROUP BY rating
        ORDER BY rating
    """, (f"-{days}", f"-{days}"))


def nps_by_channel(conn: sqlite3.Connection, days: int) -> list[dict]:
    """NPS breakdown by feedback channel."""
    return run_query(conn, """
        SELECT
            channel,
            COUNT(*) AS total,
            ROUND(AVG(CAST(rating AS REAL)), 2) AS avg_rating,
            ROUND(
                (SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END)
                 - SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END))
                * 100.0 / COUNT(*),
                1
            ) AS nps_score,
            SUM(CASE WHEN text IS NOT NULL AND text != '' THEN 1 ELSE 0 END) AS with_text
        FROM feedback
        WHERE rating IS NOT NULL
          AND date(feedback_date) >= date((SELECT MAX(feedback_date) FROM feedback), ? || ' days')
        GROUP BY channel
        ORDER BY total DESC
    """, (f"-{days}",))


def nps_by_platform(conn: sqlite3.Connection, days: int) -> list[dict]:
    """NPS breakdown by platform (min 5 ratings)."""
    return run_query(conn, """
        SELECT
            COALESCE(platform, '<unknown>') AS platform,
            COUNT(*) AS total,
            ROUND(AVG(CAST(rating AS REAL)), 2) AS avg_rating,
            ROUND(
                (SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END)
                 - SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END))
                * 100.0 / COUNT(*),
                1
            ) AS nps_score
        FROM feedback
        WHERE rating IS NOT NULL
          AND date(feedback_date) >= date((SELECT MAX(feedback_date) FROM feedback), ? || ' days')
        GROUP BY platform
        HAVING COUNT(*) >= 5
        ORDER BY nps_score ASC
    """, (f"-{days}",))


def negative_feedback(conn: sqlite3.Connection, days: int) -> list[dict]:
    """Negative feedback (rating 1-2) with text comments."""
    return run_query(conn, """
        SELECT
            feedback_date AS survey_date,
            rating,
            text AS message,
            channel,
            platform
        FROM feedback
        WHERE rating <= 2
          AND text IS NOT NULL
          AND text != ''
          AND date(feedback_date) >= date((SELECT MAX(feedback_date) FROM feedback), ? || ' days')
        ORDER BY feedback_date DESC
    """, (f"-{days}",))


def neutral_feedback(conn: sqlite3.Connection, days: int) -> list[dict]:
    """Neutral feedback (rating 3) with text comments."""
    return run_query(conn, """
        SELECT
            feedback_date AS survey_date,
            rating,
            text AS message,
            channel,
            platform
        FROM feedback
        WHERE rating = 3
          AND text IS NOT NULL
          AND text != ''
          AND date(feedback_date) >= date((SELECT MAX(feedback_date) FROM feedback), ? || ' days')
        ORDER BY feedback_date DESC
    """, (f"-{days}",))


def positive_feedback(conn: sqlite3.Connection, days: int) -> list[dict]:
    """Positive feedback (rating 4-5) with text comments."""
    return run_query(conn, """
        SELECT
            feedback_date AS survey_date,
            rating,
            text AS message,
            channel,
            platform
        FROM feedback
        WHERE rating >= 4
          AND text IS NOT NULL
          AND text != ''
          AND date(feedback_date) >= date((SELECT MAX(feedback_date) FROM feedback), ? || ' days')
        ORDER BY feedback_date DESC
    """, (f"-{days}",))


def nps_survey_stats(conn: sqlite3.Connection, days: int) -> list[dict]:
    """Stats specifically for nps_survey channel (primary NPS source)."""
    return run_query(conn, """
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT user_id) AS unique_users,
            ROUND(AVG(CAST(rating AS REAL)), 2) AS avg_rating,
            ROUND(
                (SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END)
                 - SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END))
                * 100.0 / COUNT(*),
                1
            ) AS nps_score
        FROM feedback
        WHERE channel = 'nps_survey'
          AND rating IS NOT NULL
          AND date(feedback_date) >= date((SELECT MAX(feedback_date) FROM feedback), ? || ' days')
    """, (f"-{days}",))


def run_analysis(db_path: str, days: int) -> dict:
    """Run all queries and return structured results."""
    print(f"Analyzing FitFlow feedback for last {days} days...", file=sys.stderr)
    print(f"Database: {db_path}", file=sys.stderr)

    conn = get_connection(db_path)

    result = {
        "product": "FitFlow",
        "days": days,
        "sections": {},
    }

    queries_to_run = [
        ("summary", "Overall summary", lambda: overall_summary(conn, days)),
        ("nps_survey_stats", "NPS survey stats", lambda: nps_survey_stats(conn, days)),
        ("weekly_trend", "Weekly NPS trend", lambda: weekly_nps_trend(conn, days)),
        ("rating_distribution", "Rating distribution", lambda: rating_distribution(conn, days)),
        ("nps_by_channel", "NPS by channel", lambda: nps_by_channel(conn, days)),
        ("nps_by_platform", "NPS by platform", lambda: nps_by_platform(conn, days)),
        ("negative_feedback", "Negative feedback (rating 1-2)", lambda: negative_feedback(conn, days)),
        ("neutral_feedback", "Neutral feedback (rating 3)", lambda: neutral_feedback(conn, days)),
        ("positive_feedback", "Positive feedback (rating 4-5)", lambda: positive_feedback(conn, days)),
    ]

    for key, label, query_fn in queries_to_run:
        print(f"  → {label}...", file=sys.stderr)
        try:
            rows = query_fn()
            result["sections"][key] = {
                "label": label,
                "row_count": len(rows),
                "data": rows,
            }
        except Exception as e:
            result["sections"][key] = {
                "label": label,
                "error": str(e),
            }

    conn.close()
    return result


FEEDBACK_SECTIONS = {"negative_feedback", "neutral_feedback", "positive_feedback"}


def _compact_result(result: dict) -> dict:
    """Strip text feedback from result — keep only quantitative sections."""
    compact = {
        "product": result["product"],
        "days": result["days"],
        "sections": {},
    }
    for key, section in result["sections"].items():
        if key in FEEDBACK_SECTIONS:
            compact["sections"][key] = {
                "label": section["label"],
                "row_count": section.get("row_count", 0),
            }
        else:
            compact["sections"][key] = section
    return compact


def main():
    parser = argparse.ArgumentParser(
        description="Product Feedback Analysis — batch NPS/CSAT queries for FitFlow SQLite"
    )
    parser.add_argument(
        "--db",
        default="data/fitflow.db",
        help="Path to SQLite database (default: data/fitflow.db)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=60,
        help="Analysis period in days (default: 60)",
    )
    parser.add_argument(
        "--output",
        help="Write full JSON (with text feedback) to this file. "
             "Stdout will contain only compact stats (no text).",
    )

    args = parser.parse_args()

    db_path = args.db
    if not Path(db_path).exists():
        print(f"Error: database not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    result = run_analysis(db_path, args.days)

    if args.output:
        Path(args.output).write_text(
            json.dumps(result, indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Full data written to {args.output}", file=sys.stderr)
        print(json.dumps(_compact_result(result), indent=2, default=str, ensure_ascii=False))
    else:
        print(json.dumps(result, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
