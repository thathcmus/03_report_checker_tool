import pytest
from pathlib import Path
from src.models import RubricScores, StandupReport
from src.history_manager import HistoryManager


def test_history_manager_initialization_empty(tmp_path):
    history_file = tmp_path / "data" / "standup_history.json"
    manager = HistoryManager(file_path=history_file)
    assert manager.get_recent_reports() == []
    assert history_file.exists()


def test_add_report_and_get_recent_10(tmp_path):
    history_file = tmp_path / "data" / "standup_history.json"
    manager = HistoryManager(file_path=history_file)

    # Add 12 dummy reports
    for i in range(12):
        scores = RubricScores(15, 15, 10, 10, 10, 10)
        report = StandupReport(
            id=f"rep-{i}",
            timestamp=f"2026-11-{i+1:02d}T09:00:00",
            audio_file=f"rec_{i}.wav",
            duration_seconds=60,
            wpm=130,
            closing_confirmed=True,
            scores=scores,
            filler_words_count=2,
            strengths=["OK"],
            weaknesses=["Cần cải thiện"],
            suggested_script="..."
        )
        manager.add_report(report)

    recent = manager.get_recent_reports(limit=10)
    assert len(recent) == 10
    assert recent[-1].id == "rep-11"

    trend = manager.calculate_trend()
    assert "average_score" in trend
    assert trend["total_reports"] == 12
    assert len(trend["last_10_scores"]) == 10


def test_persistence_across_instances(tmp_path):
    history_file = tmp_path / "data" / "standup_history.json"
    manager1 = HistoryManager(file_path=history_file)

    report = StandupReport(
        id="rep-persist-1",
        scores=RubricScores(10, 10, 5, 5, 5, 5),
    )
    manager1.add_report(report)

    # Re-instantiate from the same file
    manager2 = HistoryManager(file_path=history_file)
    reports = manager2.get_recent_reports()
    assert len(reports) == 1
    assert reports[0].id == "rep-persist-1"
    assert reports[0].total_score == 40


def test_calculate_trend_empty(tmp_path):
    history_file = tmp_path / "data" / "standup_history.json"
    manager = HistoryManager(file_path=history_file)
    trend = manager.calculate_trend()

    assert trend["total_reports"] == 0
    assert trend["average_score"] == 0.0
    assert trend["last_10_scores"] == []
    assert trend["score_diff"] == 0
    assert trend["trend_direction"] in ("neutral", "stable", "insufficient_data")


def test_calculate_trend_single_report(tmp_path):
    history_file = tmp_path / "data" / "standup_history.json"
    manager = HistoryManager(file_path=history_file)
    report = StandupReport(
        id="rep-1",
        scores=RubricScores(15, 15, 10, 10, 10, 10),  # total 70
    )
    manager.add_report(report)

    trend = manager.calculate_trend()
    assert trend["total_reports"] == 1
    assert trend["average_score"] == 70.0
    assert trend["last_10_scores"] == [70]
    assert trend["score_diff"] == 0


def test_calculate_trend_diff_and_direction(tmp_path):
    history_file = tmp_path / "data" / "standup_history.json"
    manager = HistoryManager(file_path=history_file)

    # First report: total = 50
    manager.add_report(StandupReport(id="rep-1", scores=RubricScores(10, 10, 5, 10, 10, 5)))
    # Second report: total = 70 (improving)
    manager.add_report(StandupReport(id="rep-2", scores=RubricScores(15, 15, 10, 10, 10, 10)))

    trend1 = manager.calculate_trend()
    assert trend1["total_reports"] == 2
    assert trend1["score_diff"] == 20
    assert trend1["trend_direction"] == "improving"
    assert trend1["average_score"] == 60.0

    # Third report: total = 60 (declining)
    manager.add_report(StandupReport(id="rep-3", scores=RubricScores(10, 15, 10, 10, 10, 5)))
    trend2 = manager.calculate_trend()
    assert trend2["total_reports"] == 3
    assert trend2["score_diff"] == -10
    assert trend2["trend_direction"] == "declining"

    # Fourth report: total = 60 (stable)
    manager.add_report(StandupReport(id="rep-4", scores=RubricScores(10, 15, 10, 10, 10, 5)))
    trend3 = manager.calculate_trend()
    assert trend3["total_reports"] == 4
    assert trend3["score_diff"] == 0
    assert trend3["trend_direction"] == "stable"


def test_history_manager_corrupted_file(tmp_path):
    history_file = tmp_path / "data" / "standup_history.json"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text("invalid json content {{{", encoding="utf-8")

    manager = HistoryManager(file_path=history_file)
    assert manager.get_recent_reports() == []
