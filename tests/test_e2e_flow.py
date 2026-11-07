"""End-to-End (E2E) Integration Tests for StandupCoach.

Verifies the complete pipeline from JSON evaluation payload ingestion,
through persistent history tracking and trend calculation, to Markdown
artifact and HTML visualizer dashboard generation.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest


def test_full_pipeline_flow(tmp_path: Path) -> None:
    """Test full pipeline execution: CLI ingestion, persistence, and report generation."""
    history_file = tmp_path / "standup_history.json"
    html_out = tmp_path / "standup_dashboard.html"
    artifact_out = tmp_path / "latest_artifact.md"

    # Simulate evaluation payload from Antigravity standup-coach skill
    sample_data = {
        "audio_file": "records/demo.wav",
        "duration_seconds": 60,
        "wpm": 130,
        "closing_confirmed": True,
        "scores": {
            "process_and_jira": 18,
            "clarity_and_conciseness": 17,
            "pronunciation_and_terms": 14,
            "cohesion_and_flow": 13,
            "pacing_and_pauses": 14,
            "filler_words_control": 13,
        },
        "filler_words_count": 2,
        "audio_quality": {
            "volume": "optimal",
            "noise": "clean",
            "note": "Mic tốt, âm lượng to rõ, không tạp âm.",
        },
        "strengths": ["Chào hỏi tự tin, share task Jira rõ ràng, cấu trúc súc tích"],
        "weaknesses": ["Còn dùng từ đệm 'ừm' 2 lần khi chuyển ý giữa yesterday và today"],
        "suggested_script": "Chào mọi người, trên Jira ticket ABC-456 hôm qua em đã merge PR...",
    }

    input_json = tmp_path / "input.json"
    input_json.write_text(json.dumps(sample_data, ensure_ascii=False), encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            "scripts/report_manager.py",
            "--add",
            str(input_json),
            "--history-path",
            str(history_file),
            "--html-path",
            str(html_out),
            "--artifact-path",
            str(artifact_out),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert res.returncode == 0, f"CLI exited with error: {res.stderr}"
    assert "StandupCoach: Evaluation saved successfully" in res.stdout
    assert "Session ID:" in res.stdout
    assert "Total Score:      89 / 100" in res.stdout

    # Verify history JSON file was created and contains valid data
    assert history_file.exists()
    history_data = json.loads(history_file.read_text(encoding="utf-8"))
    assert len(history_data["reports"]) == 1
    report = history_data["reports"][0]
    assert report["total_score"] == 89
    assert report["scores"]["process_and_jira"] == 18
    assert report["closing_confirmed"] is True
    assert report["audio_quality"]["noise"] == "clean"

    # Verify HTML dashboard exists and contains essential elements
    assert html_out.exists()
    html_content = html_out.read_text(encoding="utf-8")
    assert "<title>StandupCoach Evaluation Dashboard" in html_content
    assert "89" in html_content
    assert "radarChart" in html_content
    assert "trendChart" in html_content
    assert "Jira ticket ABC-456" in html_content

    # Verify Markdown artifact exists and contains Mermaid and markdown elements
    assert artifact_out.exists()
    artifact_content = artifact_out.read_text(encoding="utf-8")
    assert "# 🎙️ StandupCoach Evaluation Report" in artifact_content
    assert "```mermaid" in artifact_content
    assert "89 / 100" in artifact_content
    assert "Chào hỏi tự tin, share task Jira rõ ràng" in artifact_content


def test_full_pipeline_multi_session_trend_evolution(tmp_path: Path) -> None:
    """Test multiple sequential report ingestions and verify trend analytics evolution."""
    history_file = tmp_path / "data" / "standup_history.json"
    html_out = tmp_path / "reports" / "dashboard.html"
    artifact_out = tmp_path / "reports" / "artifact.md"

    # First session: Score 75
    session_1 = {
        "audio_file": "records/session_1.wav",
        "duration_seconds": 90,
        "wpm": 115,
        "closing_confirmed": False,
        "scores": {
            "process_and_jira": 14,
            "clarity_and_conciseness": 14,
            "pronunciation_and_terms": 12,
            "cohesion_and_flow": 11,
            "pacing_and_pauses": 12,
            "filler_words_control": 12,
        },
        "filler_words_count": 6,
        "strengths": ["Nêu được việc đã làm"],
        "weaknesses": ["Quên câu chốt chuyển giao", "Nói hơi chậm (115 wpm)"],
        "suggested_script": "Chào anh em, em vừa xong task DEV-101...",
    }

    payload_1 = tmp_path / "session_1.json"
    payload_1.write_text(json.dumps(session_1, ensure_ascii=False), encoding="utf-8")

    res1 = subprocess.run(
        [
            sys.executable,
            "scripts/report_manager.py",
            "--add",
            str(payload_1),
            "--history-path",
            str(history_file),
            "--html-path",
            str(html_out),
            "--artifact-path",
            str(artifact_out),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res1.returncode == 0

    # Second session: Score 85 (improved by +10)
    session_2 = {
        "audio_file": "records/session_2.wav",
        "duration_seconds": 70,
        "wpm": 135,
        "closing_confirmed": True,
        "scores": {
            "process_and_jira": 18,
            "clarity_and_conciseness": 17,
            "pronunciation_and_terms": 14,
            "cohesion_and_flow": 13,
            "pacing_and_pauses": 12,
            "filler_words_control": 11,
        },
        "filler_words_count": 3,
        "strengths": ["Đã bổ sung câu chốt kết thúc", "Tốc độ nói cải thiện tốt"],
        "weaknesses": ["Vẫn còn 3 từ đệm 'à'"],
        "suggested_script": "Chào team, ticket DEV-102 em đã test xong...",
    }

    payload_2 = tmp_path / "session_2.json"
    payload_2.write_text(json.dumps(session_2, ensure_ascii=False), encoding="utf-8")

    res2 = subprocess.run(
        [
            sys.executable,
            "scripts/report_manager.py",
            "--add",
            str(payload_2),
            "--history-path",
            str(history_file),
            "--html-path",
            str(html_out),
            "--artifact-path",
            str(artifact_out),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res2.returncode == 0

    # Verify history now stores 2 reports
    history_data = json.loads(history_file.read_text(encoding="utf-8"))
    assert len(history_data["reports"]) == 2
    assert history_data["reports"][0]["total_score"] == 75
    assert history_data["reports"][1]["total_score"] == 85

    # Check CLI --show-trend output
    res_trend = subprocess.run(
        [
            sys.executable,
            "scripts/report_manager.py",
            "--show-trend",
            "--history-path",
            str(history_file),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res_trend.returncode == 0
    assert "StandupCoach Performance Trend Summary" in res_trend.stdout
    assert "Total Sessions:   2" in res_trend.stdout
    assert "Average Score:    80.0 / 100" in res_trend.stdout
    assert "Recent Average:   80.0 / 100" in res_trend.stdout
    assert "UP (+10 from previous)" in res_trend.stdout
    assert "Recent Scores:    [75, 85]" in res_trend.stdout


def test_full_pipeline_closing_and_audio_quality_alerts(tmp_path: Path) -> None:
    """Test full pipeline when closing statement is missing and audio is noisy."""
    history_file = tmp_path / "standup_history.json"
    html_out = tmp_path / "standup_dashboard.html"
    artifact_out = tmp_path / "latest_artifact.md"

    payload_data = {
        "audio_file": "records/noisy_sample.wav",
        "duration_seconds": 120,
        "wpm": 95,
        "closing_confirmed": False,
        "scores": {
            "process_and_jira": 10,
            "clarity_and_conciseness": 10,
            "pronunciation_and_terms": 9,
            "cohesion_and_flow": 8,
            "pacing_and_pauses": 8,
            "filler_words_control": 7,
        },
        "filler_words_count": 8,
        "audio_quality": {
            "volume": "too_quiet",
            "noise": "too_noisy",
            "note": "Âm thanh quá nhỏ, tiếng ồn quạt gió lớn.",
        },
        "strengths": ["Đã cố gắng báo cáo"],
        "weaknesses": ["Nói quá chậm", "Thiếu câu chốt kết thúc", "Nhiều từ đệm"],
        "suggested_script": "Chào cả nhà, ticket BUG-999...",
    }

    input_json = tmp_path / "noisy_input.json"
    input_json.write_text(json.dumps(payload_data, ensure_ascii=False), encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            "scripts/report_manager.py",
            "--add",
            str(input_json),
            "--history-path",
            str(history_file),
            "--html-path",
            str(html_out),
            "--artifact-path",
            str(artifact_out),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert res.returncode == 0
    assert "Total Score:      52 / 100" in res.stdout

    # Verify Markdown artifact highlights closing warning and audio quality alert
    artifact_text = artifact_out.read_text(encoding="utf-8")
    assert "Chưa có câu chốt chuyển giao rõ ràng" in artifact_text
    assert "> [!WARNING]" in artifact_text
    assert "too_noisy" in artifact_text

    # Verify HTML dashboard contains warning badge
    html_text = html_out.read_text(encoding="utf-8")
    assert "badge-warning" in html_text or "too_noisy" in html_text

