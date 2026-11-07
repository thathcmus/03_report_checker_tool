"""Unit tests for DashboardGenerator (Markdown Artifact and HTML Visualizer)."""

import pytest
from src.history_manager import HistoryManager
from src.models import RubricScores, StandupReport
from src.dashboard_generator import DashboardGenerator


@pytest.fixture
def sample_report() -> StandupReport:
    scores = RubricScores(18, 17, 14, 13, 14, 12)
    return StandupReport(
        id="rep-01",
        timestamp="2026-11-07T09:00:00",
        audio_file="records/sample.wav",
        duration_seconds=70,
        wpm=135,
        closing_confirmed=True,
        scores=scores,
        filler_words_count=2,
        audio_quality={"volume": "Optimal", "noise": "Clean"},
        strengths=["Dẫn dắt Jira tự tin", "Cấu trúc rõ ràng"],
        weaknesses=["Từ đệm 'à' xuất hiện 2 lần"],
        suggested_script="Mẫu câu tối ưu...",
    )


def test_generate_markdown_artifact(sample_report):
    generator = DashboardGenerator()
    md_content = generator.generate_markdown_artifact(sample_report, recent_reports=[sample_report])

    assert "# 🎙️ StandupCoach Evaluation Report" in md_content
    assert "88 / 100" in md_content
    assert "```mermaid" in md_content
    assert "Mẫu câu tối ưu..." in md_content
    assert "Quy trình & Jira" in md_content
    assert "Dễ hiểu" in md_content
    assert "Phát âm" in md_content
    assert "Mạch tư duy" in md_content
    assert "Ngắt nghỉ" in md_content
    assert "Kiểm soát từ đệm" in md_content
    assert "Dẫn dắt Jira tự tin" in md_content
    assert "Từ đệm 'à' xuất hiện 2 lần" in md_content
    assert "Hardware & Noise Diagnostic" in md_content or "Audio Quality" in md_content
    assert "> [!NOTE]" in md_content


def test_generate_html_dashboard(sample_report):
    generator = DashboardGenerator()
    html_content = generator.generate_html_dashboard(sample_report, recent_reports=[sample_report])

    assert "<!DOCTYPE html>" in html_content
    assert "chart.js" in html_content.lower()
    assert "radar" in html_content.lower()
    assert "line" in html_content.lower()
    assert "88" in html_content
    assert "Mẫu câu tối ưu..." in html_content
    assert "Dẫn dắt Jira tự tin" in html_content
    assert "Optimal" in html_content
    assert "Clean" in html_content


def test_dashboard_with_history_manager(tmp_path, sample_report):
    history_file = tmp_path / "history.json"
    manager = HistoryManager(file_path=history_file)
    manager.add_report(sample_report)

    # Add second report
    second_report = StandupReport(
        id="rep-02",
        timestamp="2026-11-08T09:00:00",
        audio_file="records/sample2.wav",
        duration_seconds=65,
        wpm=140,
        closing_confirmed=True,
        scores=RubricScores(19, 18, 15, 14, 14, 14),
        filler_words_count=1,
        audio_quality={"volume": "Optimal", "noise": "Clean"},
        strengths=["Tốc độ rất tốt"],
        weaknesses=[],
        suggested_script="Kịch bản 2...",
    )
    manager.add_report(second_report)

    # Call directly as classmethod without instantiation
    md_content = DashboardGenerator.generate_markdown_artifact(second_report, recent_reports=manager)
    html_content = DashboardGenerator.generate_html_dashboard(second_report, recent_reports=manager)

    assert "94 / 100" in md_content
    assert "```mermaid" in md_content
    assert "<!DOCTYPE html>" in html_content
    assert "rep-02" in html_content or "94" in html_content


def test_dashboard_with_empty_audio_quality_and_defaults():
    scores = RubricScores(10, 10, 8, 8, 8, 8)
    report = StandupReport(
        id="rep-empty",
        scores=scores,
        audio_quality={},
        strengths=[],
        weaknesses=[],
    )
    generator = DashboardGenerator()
    md = generator.generate_markdown_artifact(report)
    html = generator.generate_html_dashboard(report)

    assert "52 / 100" in md
    assert "Cần cải thiện" in md
    assert "<!DOCTYPE html>" in html


def test_dashboard_noisy_audio_triggers_warning_alert():
    report = StandupReport(
        id="rep-noisy",
        scores=RubricScores(15, 15, 12, 12, 12, 12),
        audio_quality={"volume": "Too quiet", "noise": "Too noisy"},
    )
    md = DashboardGenerator.generate_markdown_artifact(report)
    assert "> [!WARNING]" in md
    assert "Too quiet" in md
    assert "Too noisy" in md


def test_html_dashboard_escaping_xss():
    malicious_report = StandupReport(
        id="<script>alert('xss')</script>",
        timestamp="<svg onload=alert(1)>",
        scores=RubricScores(15, 15, 10, 10, 10, 10),
        strengths=["<script>bad()</script>"],
        weaknesses=["<b>unescaped</b>"],
        suggested_script="<script>malicious()</script>",
    )
    html_out = DashboardGenerator.generate_html_dashboard(malicious_report)

    assert "<script>alert('xss')</script>" not in html_out
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in html_out or "&lt;script&gt;" in html_out
    assert "<script>malicious()</script>" not in html_out


def test_recent_reports_truncates_to_last_10():
    reports = [
        StandupReport(id=f"rep-{i}", scores=RubricScores(10, 10, 10, 10, 10, 10))
        for i in range(15)
    ]
    md = DashboardGenerator.generate_markdown_artifact(reports[-1], recent_reports=reports)
    html = DashboardGenerator.generate_html_dashboard(reports[-1], recent_reports=reports)

    # Should only have S1 to S10 in mermaid
    assert '"S10"' in md
    assert '"S11"' not in md
    # Should only have Session 1 to Session 10 in html
    assert '"Session 10"' in html
    assert '"Session 11"' not in html


def test_active_report_appended_when_not_in_recent_reports():
    """Verify active report is appended as the latest point if not already present."""
    r1 = StandupReport(id="old-1", scores=RubricScores(10, 10, 10, 10, 10, 10))
    r2 = StandupReport(id="old-2", scores=RubricScores(12, 12, 12, 12, 12, 12))
    active = StandupReport(id="active-new", scores=RubricScores(15, 15, 15, 15, 15, 15))

    md = DashboardGenerator.generate_markdown_artifact(active, recent_reports=[r1, r2])
    html = DashboardGenerator.generate_html_dashboard(active, recent_reports=[r1, r2])

    # 3 sessions: S1, S2, S3
    assert '"S3"' in md
    assert '"Session 3"' in html
    # Active report score 90 should be the last value
    assert "line [60, 72, 90]" in md
    assert "[60, 72, 90]" in html


def test_history_keyword_alias(sample_report):
    """Verify 'history' keyword alias works identically to 'recent_reports'."""
    md = DashboardGenerator.generate_markdown_artifact(sample_report, history=[sample_report])
    html = DashboardGenerator.generate_html_dashboard(sample_report, history=[sample_report])

    assert "# 🎙️ StandupCoach Evaluation Report" in md
    assert "<!DOCTYPE html>" in html
    assert "88 / 100" in md


def test_suggested_script_multiparagraph_blockquote():
    """Verify multi-paragraph suggested scripts stay cleanly within markdown blockquotes."""
    report = StandupReport(
        id="rep-multi",
        scores=RubricScores(15, 15, 12, 12, 12, 12),
        suggested_script="Đoạn 1: Mở đầu Jira.\n\nĐoạn 2: Hôm qua và hôm nay.\nĐoạn 3: Kết thúc chuyển giao.",
    )
    md = DashboardGenerator.generate_markdown_artifact(report)

    assert "> Đoạn 1: Mở đầu Jira." in md
    assert "> \n> Đoạn 2: Hôm qua và hôm nay." in md
    assert "> Đoạn 3: Kết thúc chuyển giao." in md


def test_dashboard_renders_audio_quality_note():
    """Verify audio_quality['note'] is rendered in both Markdown Artifact and HTML Dashboard."""
    report = StandupReport(
        id="rep-note",
        scores=RubricScores(18, 17, 14, 13, 14, 12),
        audio_quality={
            "volume": "Optimal",
            "noise": "Clean",
            "note": "Mic thu rõ, không bị vang phòng.",
        },
    )
    md = DashboardGenerator.generate_markdown_artifact(report)
    html = DashboardGenerator.generate_html_dashboard(report)

    assert "Mic thu rõ, không bị vang phòng." in md
    assert "Mic thu rõ, không bị vang phòng." in html

