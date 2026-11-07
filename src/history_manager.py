"""History manager and trend calculator for daily standup evaluation sessions.

Persists evaluation reports to JSON and calculates performance trends across sessions.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import tempfile
from typing import Any

from src.models import HistoryStore, StandupReport

logger = logging.getLogger(__name__)


class HistoryManager:
    """Manages persistence and trend statistics of standup session evaluation history."""

    def __init__(self, file_path: str | Path = "data/standup_history.json") -> None:
        self.file_path = Path(file_path)
        self._store: HistoryStore = HistoryStore()
        self.load_or_create()

    def load_or_create(self) -> HistoryStore:
        """Load history from file or create an empty store and file if missing."""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._store = HistoryStore(reports=[])
            self._save()
            return self._store

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._store = HistoryStore.from_dict(data)
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as err:
            logger.warning(
                "Failed to parse history from %s (%s). Falling back to empty store.",
                self.file_path,
                err,
            )
            self._store = HistoryStore(reports=[])

        return self._store

    def _save(self) -> None:
        """Atomically persist current history store to disk."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = tempfile.NamedTemporaryFile(
            dir=self.file_path.parent,
            delete=False,
            mode="w",
            encoding="utf-8",
        )
        try:
            json.dump(self._store.to_dict(), temp_file, indent=2, ensure_ascii=False)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_file.close()
            os.replace(temp_file.name, self.file_path)
        except Exception:
            if os.path.exists(temp_file.name):
                try:
                    os.remove(temp_file.name)
                except OSError:
                    pass
            raise

    def add_report(self, report: StandupReport) -> None:
        """Add a new evaluation report and persist to storage."""
        self._store.reports.append(report)
        self._save()

    def get_recent_reports(self, limit: int = 10) -> list[StandupReport]:
        """Return up to `limit` most recent reports in chronological order."""
        if limit <= 0:
            return []
        if len(self._store.reports) <= limit:
            return list(self._store.reports)
        return list(self._store.reports[-limit:])

    def calculate_trend(self) -> dict[str, Any]:
        """Calculate performance trends across historical standup sessions.

        Returns statistics including average score, recent 10 scores,
        diff from previous session, and trend direction.
        """
        total_reports = len(self._store.reports)
        if total_reports == 0:
            return {
                "total_reports": 0,
                "average_score": 0.0,
                "recent_average": 0.0,
                "last_10_scores": [],
                "score_diff": 0,
                "trend_direction": "insufficient_data",
                "category_averages": {},
            }

        all_scores = [r.total_score for r in self._store.reports]
        average_score = round(sum(all_scores) / total_reports, 2)

        recent_10_reports = self._store.reports[-10:]
        last_10_scores = [r.total_score for r in recent_10_reports]
        recent_average = round(sum(last_10_scores) / len(last_10_scores), 2)

        if total_reports >= 2:
            score_diff = (
                self._store.reports[-1].total_score - self._store.reports[-2].total_score
            )
            if score_diff > 0:
                trend_direction = "improving"
            elif score_diff < 0:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
        else:
            score_diff = 0
            trend_direction = "neutral"

        # Rubric category averages across all sessions
        category_averages: dict[str, float] = {}
        for cat in (
            "process_and_jira",
            "clarity_and_conciseness",
            "pronunciation_and_terms",
            "cohesion_and_flow",
            "pacing_and_pauses",
            "filler_words_control",
        ):
            cat_vals = [getattr(r.scores, cat, 0) for r in self._store.reports if r.scores]
            if cat_vals:
                category_averages[cat] = round(sum(cat_vals) / len(cat_vals), 2)

        return {
            "total_reports": total_reports,
            "average_score": average_score,
            "recent_average": recent_average,
            "last_10_scores": last_10_scores,
            "score_diff": score_diff,
            "trend_direction": trend_direction,
            "category_averages": category_averages,
        }
