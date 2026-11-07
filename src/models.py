"""Data models and storage schema for StandupCoach.

Defines RubricScores (6-criteria evaluation rubric) and StandupReport
(evaluation report for each daily standup session).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


@dataclass
class RubricScores:
    """Detailed score breakdown across 6 evaluation criteria (100-point scale).

    Criteria:
    1. process_and_jira: Chuẩn quy trình Daily meeting & Jira context (0-20 pts)
    2. clarity_and_conciseness: Dễ hiểu, súc tích & trọng tâm (0-20 pts)
    3. pronunciation_and_terms: Độ ổn định phát âm & thuật ngữ IT (0-15 pts)
    4. cohesion_and_flow: Độ liên kết câu & mạch tư duy (0-15 pts)
    5. pacing_and_pauses: Ngắt nghỉ & nhịp điệu (0-15 pts)
    6. filler_words_control: Kiểm soát từ đệm & chuyên nghiệp (0-15 pts)
    """

    process_and_jira: int = 0
    clarity_and_conciseness: int = 0
    pronunciation_and_terms: int = 0
    cohesion_and_flow: int = 0
    pacing_and_pauses: int = 0
    filler_words_control: int = 0

    def __post_init__(self) -> None:
        limits = {
            "process_and_jira": (0, 20),
            "clarity_and_conciseness": (0, 20),
            "pronunciation_and_terms": (0, 15),
            "cohesion_and_flow": (0, 15),
            "pacing_and_pauses": (0, 15),
            "filler_words_control": (0, 15),
        }
        for field_name, (min_val, max_val) in limits.items():
            val = getattr(self, field_name)
            if isinstance(val, bool) or not isinstance(val, (int, float)) or val < min_val or val > max_val:
                raise ValueError(
                    f"{field_name} must be between {min_val} and {max_val}, got {val}"
                )
            setattr(self, field_name, int(round(val)))

    @property
    def total(self) -> int:
        """Calculate total evaluation score (0-100)."""
        return int(
            self.process_and_jira
            + self.clarity_and_conciseness
            + self.pronunciation_and_terms
            + self.cohesion_and_flow
            + self.pacing_and_pauses
            + self.filler_words_control
        )

    def to_dict(self) -> dict[str, int]:
        """Serialize scores to dictionary."""
        return {
            "process_and_jira": int(self.process_and_jira),
            "clarity_and_conciseness": int(self.clarity_and_conciseness),
            "pronunciation_and_terms": int(self.pronunciation_and_terms),
            "cohesion_and_flow": int(self.cohesion_and_flow),
            "pacing_and_pauses": int(self.pacing_and_pauses),
            "filler_words_control": int(self.filler_words_control),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RubricScores:
        """Construct RubricScores from dictionary."""
        if not data or not isinstance(data, dict):
            return cls()

        def _to_int(val: Any) -> int:
            if val is None or val == "":
                return 0
            return int(round(float(val)))

        return cls(
            process_and_jira=_to_int(data.get("process_and_jira")),
            clarity_and_conciseness=_to_int(data.get("clarity_and_conciseness")),
            pronunciation_and_terms=_to_int(data.get("pronunciation_and_terms")),
            cohesion_and_flow=_to_int(data.get("cohesion_and_flow")),
            pacing_and_pauses=_to_int(data.get("pacing_and_pauses")),
            filler_words_control=_to_int(data.get("filler_words_control")),
        )


@dataclass
class StandupReport:
    """Evaluation report for a single standup session."""

    id: str = ""
    timestamp: str = ""
    audio_file: str = ""
    duration_seconds: int = 0
    wpm: int = 0
    closing_confirmed: bool = False
    scores: RubricScores = field(default_factory=RubricScores)
    filler_words_count: int = 0
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    suggested_script: str = ""
    audio_quality: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"report-{uuid.uuid4().hex[:8]}"
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if isinstance(self.scores, dict):
            self.scores = RubricScores.from_dict(self.scores)
        if not isinstance(self.strengths, list):
            self.strengths = list(self.strengths)
        if not isinstance(self.weaknesses, list):
            self.weaknesses = list(self.weaknesses)
        if not isinstance(self.audio_quality, dict):
            self.audio_quality = dict(self.audio_quality) if self.audio_quality else {}
        for metric_field in ("duration_seconds", "wpm", "filler_words_count"):
            val = getattr(self, metric_field)
            if isinstance(val, bool) or not isinstance(val, (int, float)) or val < 0:
                raise ValueError(f"{metric_field} must be a non-negative number, got {val}")
            setattr(self, metric_field, int(round(val)))

    @property
    def total_score(self) -> int:
        """Overall session score computed from RubricScores."""
        return self.scores.total if self.scores else 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize report to dictionary including computed total_score."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "audio_file": self.audio_file,
            "duration_seconds": self.duration_seconds,
            "wpm": self.wpm,
            "closing_confirmed": self.closing_confirmed,
            "total_score": self.total_score,
            "scores": self.scores.to_dict() if hasattr(self.scores, "to_dict") else self.scores,
            "filler_words_count": self.filler_words_count,
            "strengths": list(self.strengths),
            "weaknesses": list(self.weaknesses),
            "suggested_script": self.suggested_script,
            "audio_quality": dict(self.audio_quality) if self.audio_quality else {},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StandupReport:
        """Construct StandupReport from dictionary."""
        if not data or not isinstance(data, dict):
            return cls()

        scores_raw = data.get("scores")
        if isinstance(scores_raw, dict):
            scores = RubricScores.from_dict(scores_raw)
        elif isinstance(scores_raw, RubricScores):
            scores = scores_raw
        else:
            scores = RubricScores()

        return cls(
            id=str(data.get("id") or ""),
            timestamp=str(data.get("timestamp") or ""),
            audio_file=str(data.get("audio_file") or ""),
            duration_seconds=int(data.get("duration_seconds") or 0),
            wpm=int(data.get("wpm") or 0),
            closing_confirmed=bool(data.get("closing_confirmed") or False),
            scores=scores,
            filler_words_count=int(data.get("filler_words_count") or 0),
            strengths=list(data.get("strengths") or []),
            weaknesses=list(data.get("weaknesses") or []),
            suggested_script=str(data.get("suggested_script") or ""),
            audio_quality=dict(data.get("audio_quality") or {}),
        )


@dataclass
class HistoryStore:
    """In-memory representation of persisted standup session history."""

    reports: list[StandupReport] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize all reports to dictionary."""
        return {
            "reports": [report.to_dict() for report in self.reports]
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | list[dict[str, Any]]) -> HistoryStore:
        """Construct HistoryStore from dictionary or list of report dictionaries."""
        if isinstance(data, list):
            reports_raw = data
        elif isinstance(data, dict):
            reports_raw = data.get("reports") or []
        else:
            reports_raw = []
        return cls(reports=[StandupReport.from_dict(r) for r in reports_raw if isinstance(r, dict)])
