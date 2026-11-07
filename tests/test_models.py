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


def test_rubric_scores_from_dict_null_safety():
    """Verify RubricScores.from_dict handles None/null values gracefully."""
    null_data = {
        "process_and_jira": None,
        "clarity_and_conciseness": None,
        "pronunciation_and_terms": None,
        "cohesion_and_flow": None,
        "pacing_and_pauses": None,
        "filler_words_control": None,
    }
    scores = RubricScores.from_dict(null_data)
    assert scores.process_and_jira == 0
    assert scores.clarity_and_conciseness == 0
    assert scores.pronunciation_and_terms == 0
    assert scores.cohesion_and_flow == 0
    assert scores.pacing_and_pauses == 0
    assert scores.filler_words_control == 0
    assert scores.total == 0

    # Also test empty dict and None
    assert RubricScores.from_dict({}).total == 0
    assert RubricScores.from_dict(None).total == 0  # type: ignore


def test_standup_report_from_dict_null_safety():
    """Verify StandupReport.from_dict guards against None/null values from LLM payloads."""
    null_payload = {
        "id": None,
        "timestamp": None,
        "audio_file": None,
        "duration_seconds": None,
        "wpm": None,
        "closing_confirmed": None,
        "scores": {
            "process_and_jira": None,
            "clarity_and_conciseness": None,
            "pronunciation_and_terms": None,
            "cohesion_and_flow": None,
            "pacing_and_pauses": None,
            "filler_words_control": None,
        },
        "filler_words_count": None,
        "strengths": None,
        "weaknesses": None,
        "suggested_script": None,
        "audio_quality": None,
    }
    report = StandupReport.from_dict(null_payload)
    assert report.id.startswith("report-")
    assert report.timestamp != ""
    assert report.audio_file == ""
    assert report.duration_seconds == 0
    assert report.wpm == 0
    assert report.closing_confirmed is False
    assert report.total_score == 0
    assert report.filler_words_count == 0
    assert report.strengths == []
    assert report.weaknesses == []
    assert report.suggested_script == ""
    assert report.audio_quality == {}

    # None scores entirely
    report_none_scores = StandupReport.from_dict({"scores": None})
    assert report_none_scores.total_score == 0
    assert isinstance(report_none_scores.scores, RubricScores)

    # Empty and None input
    assert StandupReport.from_dict({}).total_score == 0
    assert StandupReport.from_dict(None).total_score == 0  # type: ignore


def test_rubric_scores_float_normalization():
    """Verify float values in RubricScores are normalized to int consistently across total and to_dict."""
    scores = RubricScores(14.6, 14.6, 10, 10, 10, 10)  # type: ignore
    assert isinstance(scores.process_and_jira, int)
    assert isinstance(scores.clarity_and_conciseness, int)
    assert scores.process_and_jira == 15
    assert scores.clarity_and_conciseness == 15
    assert scores.total == 70
    assert RubricScores.from_dict(scores.to_dict()).total == scores.total

    from_float_str = RubricScores.from_dict({"process_and_jira": "15.6", "clarity_and_conciseness": 14.4})
    assert from_float_str.process_and_jira == 16
    assert from_float_str.clarity_and_conciseness == 14


def test_standup_report_negative_metrics_validation():
    """Verify negative duration_seconds, wpm, or filler_words_count raises ValueError."""
    with pytest.raises(ValueError, match="duration_seconds"):
        StandupReport(duration_seconds=-1)

    with pytest.raises(ValueError, match="wpm"):
        StandupReport(wpm=-10)

    with pytest.raises(ValueError, match="filler_words_count"):
        StandupReport(filler_words_count=-2)

