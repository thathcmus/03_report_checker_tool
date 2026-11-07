"""CLI Report Manager for StandupCoach.

Ingests evaluation JSON payloads, persists session reports to history,
generates Markdown artifacts and HTML visualizer dashboards, and prints
trend analytics.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Any
import webbrowser

# Ensure UTF-8 output encoding on Windows consoles/pipes
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.dashboard_generator import DashboardGenerator
from src.history_manager import HistoryManager
from src.models import StandupReport

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("report_manager")


def print_trend_summary(trend: dict[str, Any]) -> None:
    """Format and print performance trend summary to stdout."""
    print("=" * 60)
    print("📈 StandupCoach Performance Trend Summary")
    print("=" * 60)
    print(f"Total Sessions:   {trend.get('total_reports', 0)}")
    print(f"Average Score:    {trend.get('average_score', 0.0)} / 100")
    print(f"Recent Average:   {trend.get('recent_average', 0.0)} / 100")

    diff = trend.get("diff_from_previous", 0)
    diff_str = f"+{diff}" if diff > 0 else str(diff)
    print(f"Trend Direction:  {trend.get('trend_direction', 'stable').upper()} ({diff_str} from previous)")

    scores = trend.get("last_10_scores", [])
    if scores:
        print(f"Recent Scores:    {scores}")

    category_avgs = trend.get("category_averages", {})
    if category_avgs:
        print("\nRubric Category Averages:")
        for cat, avg in category_avgs.items():
            cat_display = cat.replace("_", " ").title()
            print(f"  - {cat_display:25s}: {avg:.1f}")
    print("=" * 60)


def ingest_payload(
    payload_path: Path,
    history_path: Path,
    html_path: Path,
    artifact_path: Path,
    open_browser: bool = False,
) -> StandupReport:
    """Ingest evaluation payload, update history store, and generate reports."""
    if not payload_path.exists():
        sys.stderr.write(f"Error: Payload file not found: {payload_path}\n")
        sys.exit(1)

    try:
        with open(payload_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as err:
        sys.stderr.write(f"Error: Failed to parse JSON payload {payload_path}: {err}\n")
        sys.exit(1)

    # Instantiate StandupReport from payload data
    try:
        report = StandupReport.from_dict(data)
    except Exception as err:
        sys.stderr.write(f"Error: Invalid StandupReport data schema: {err}\n")
        sys.exit(1)

    # Update history store
    history_mgr = HistoryManager(file_path=history_path)
    history_mgr.add_report(report)

    # Generate HTML Dashboard
    html_content = DashboardGenerator.generate_html_dashboard(report, history_mgr)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Generate Markdown Artifact
    artifact_content = DashboardGenerator.generate_markdown_artifact(report, history_mgr)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    with open(artifact_path, "w", encoding="utf-8") as f:
        f.write(artifact_content)

    # Print success message required by spec
    print("StandupCoach: Evaluation saved successfully")
    print(f"Session ID:       {report.id}")
    print(f"Total Score:      {report.total_score} / 100")
    print(f"History updated:  {history_path}")
    print(f"HTML Dashboard:   {html_path}")
    print(f"Markdown Report:  {artifact_path}")

    if open_browser:
        target_uri = html_path.resolve().as_uri()
        print(f"Opening dashboard in browser: {target_uri}")
        webbrowser.open(target_uri)

    return report


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="StandupCoach CLI Report Manager: Ingest evaluation payloads and manage reports.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--add",
        type=Path,
        metavar="PAYLOAD_JSON",
        help="Path to evaluation payload JSON file to ingest",
    )
    parser.add_argument(
        "--history-path",
        type=Path,
        default=Path("data/standup_history.json"),
        help="Path to persistent standup history JSON file",
    )
    parser.add_argument(
        "--html-path",
        type=Path,
        default=Path("reports/standup_dashboard.html"),
        help="Path to write standalone HTML visualizer dashboard",
    )
    parser.add_argument(
        "--artifact-path",
        type=Path,
        default=Path("reports/latest_artifact.md"),
        help="Path to write Markdown artifact report",
    )
    parser.add_argument(
        "--show-trend",
        action="store_true",
        help="Display performance trend statistics to stdout",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open generated HTML dashboard in default browser",
    )
    return parser


def main() -> None:
    """Main CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.add and not args.show_trend:
        parser.print_help()
        sys.exit(0)

    if args.add:
        ingest_payload(
            payload_path=args.add,
            history_path=args.history_path,
            html_path=args.html_path,
            artifact_path=args.artifact_path,
            open_browser=args.open_browser,
        )

    if args.show_trend:
        history_mgr = HistoryManager(file_path=args.history_path)
        trend = history_mgr.calculate_trend()
        print_trend_summary(trend)


if __name__ == "__main__":
    main()
