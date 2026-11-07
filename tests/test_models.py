import pytest
from src.models import RubricScores, StandupReport, HistoryStore


def test_rubric_scores_total():
    scores = RubricScores(
        process_and_jira=18,
        clarity_and_conciseness=16,
        pronunciation_and_terms=14,
        cohesion_and_flow=13,
        pacing_and_pauses=12,
        filler_words_control=12
    )
    assert scores.total == 85


def test_rubric_scores_validation_exceed_max():
    # process_and_jira max is 20
    with pytest.raises(ValueError, match="process_and_jira"):
        RubricScores(21, 15, 10, 10, 10, 10)

    # pronunciation_and_terms max is 15
    with pytest.raises(ValueError, match="pronunciation_and_terms"):
        RubricScores(15, 15, 16, 10, 10, 10)


def test_rubric_scores_validation_negative():
    with pytest.raises(ValueError, match="filler_words_control"):
        RubricScores(15, 15, 10, 10, 10, -1)


def test_rubric_scores_validation_boolean():
    with pytest.raises(ValueError, match="process_and_jira"):
        RubricScores(True, 15, 10, 10, 10, 10)  # type: ignore

    with pytest.raises(ValueError, match="clarity_and_conciseness"):
        RubricScores(15, False, 10, 10, 10, 10)  # type: ignore


def test_rubric_scores_to_dict_and_from_dict():
    scores = RubricScores(18, 16, 14, 13, 12, 12)
    data = scores.to_dict()
    assert data == {
        "process_and_jira": 18,
        "clarity_and_conciseness": 16,
        "pronunciation_and_terms": 14,
        "cohesion_and_flow": 13,
        "pacing_and_pauses": 12,
        "filler_words_control": 12,
    }
    reconstructed = RubricScores.from_dict(data)
    assert reconstructed == scores
    assert reconstructed.total == 85


def test_standup_report_serialization():
    scores = RubricScores(18, 16, 14, 13, 12, 12)
    report = StandupReport(
        id="report-001",
        timestamp="2026-11-07T09:00:00",
        audio_file="records/daily_01.wav",
        duration_seconds=75,
        wpm=135,
        closing_confirmed=True,
        scores=scores,
        filler_words_count=3,
        strengths=["Mở đầu tốt, dẫn dắt Jira rõ ràng"],
        weaknesses=["Hơi ngắc ngứ đoạn giải thích bug"],
        suggested_script="Chào mọi người, trên ticket PROJ-123...",
        audio_quality={"volume": "optimal", "noise": "clean", "note": "Âm thanh rõ, mic tốt"}
    )
    data = report.to_dict()
    assert data["total_score"] == 85
    assert data["scores"]["process_and_jira"] == 18
    assert data["closing_confirmed"] is True
    assert data["audio_quality"]["volume"] == "optimal"


def test_standup_report_deserialization():
    raw_data = {
        "id": "report-002",
        "timestamp": "2026-11-07T10:00:00",
        "audio_file": "records/daily_02.wav",
        "duration_seconds": 60,
        "wpm": 140,
        "closing_confirmed": False,
        "scores": {
            "process_and_jira": 15,
            "clarity_and_conciseness": 15,
            "pronunciation_and_terms": 12,
            "cohesion_and_flow": 12,
            "pacing_and_pauses": 11,
            "filler_words_control": 10
        },
        "filler_words_count": 5,
        "strengths": ["Tự tin"],
        "weaknesses": ["Thiếu câu chốt"],
        "suggested_script": "Em đã report xong...",
        "audio_quality": {
            "volume": "too_quiet",
            "noise": "moderate"
        }
    }
    report = StandupReport.from_dict(raw_data)
    assert report.id == "report-002"
    assert report.total_score == 75
    assert isinstance(report.scores, RubricScores)
    assert report.scores.process_and_jira == 15
    assert report.closing_confirmed is False
    assert report.strengths == ["Tự tin"]
    assert report.audio_quality["volume"] == "too_quiet"


def test_standup_report_defaults():
    scores = RubricScores(10, 10, 10, 10, 10, 10)
    report = StandupReport(
        audio_file="records/temp.wav",
        scores=scores
    )
    assert report.id != ""
    assert report.timestamp != ""
    assert report.duration_seconds == 0
    assert report.closing_confirmed is False
    assert report.strengths == []
    assert report.weaknesses == []
    assert report.audio_quality == {}


def test_history_store_roundtrip():
    scores = RubricScores(18, 16, 14, 13, 12, 12)
    report = StandupReport(
        id="rep-1",
        timestamp="2026-11-07T09:00:00",
        audio_file="rec.wav",
        scores=scores
    )
    store = HistoryStore(reports=[report])
    data = store.to_dict()
    assert len(data["reports"]) == 1
    assert data["reports"][0]["id"] == "rep-1"

    loaded_store = HistoryStore.from_dict(data)
    assert len(loaded_store.reports) == 1
    assert loaded_store.reports[0].id == "rep-1"
    assert loaded_store.reports[0].total_score == 85
