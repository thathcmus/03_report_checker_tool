"""Integration tests for CLI scripts: report_manager.py and record.py."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import wave

import pytest


@pytest.fixture
def sample_payload() -> dict:
    """Fixture providing a valid StandupReport payload."""
    return {
        "audio_file": "records/test.wav",
        "duration_seconds": 65,
        "wpm": 140,
        "closing_confirmed": True,
        "scores": {
            "process_and_jira": 19,
            "clarity_and_conciseness": 18,
            "pronunciation_and_terms": 14,
            "cohesion_and_flow": 14,
            "pacing_and_pauses": 13,
            "filler_words_control": 14,
        },
        "filler_words_count": 1,
        "strengths": ["Dẫn dắt Jira mượt mà", "Rõ ràng mục tiêu sprint"],
        "weaknesses": ["Nói hơi nhanh ở phần blocker"],
        "suggested_script": "Chào anh em, hôm qua em hoàn thành ticket...",
        "audio_quality": {
            "volume": "Optimal",
            "noise": "Clean",
        },
    }


def test_cli_add_report(tmp_path: Path, sample_payload: dict) -> None:
    """Test CLI --add ingests payload and creates history, html, and markdown artifact."""
    history_file = tmp_path / "standup_history.json"
    html_out = tmp_path / "standup_dashboard.html"
    artifact_out = tmp_path / "latest_artifact.md"

    payload_file = tmp_path / "payload.json"
    payload_file.write_text(json.dumps(sample_payload), encoding="utf-8")

    cmd = [
        sys.executable,
        "scripts/report_manager.py",
        "--add",
        str(payload_file),
        "--history-path",
        str(history_file),
        "--html-path",
        str(html_out),
        "--artifact-path",
        str(artifact_out),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)

    assert res.returncode == 0, f"CLI stderr: {res.stderr}"
    assert "StandupCoach: Evaluation saved successfully" in res.stdout
    assert history_file.exists()
    assert html_out.exists()
    assert artifact_out.exists()

    with open(history_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data.get("reports", [])) == 1

    html_content = html_out.read_text(encoding="utf-8")
    assert "StandupCoach Evaluation Dashboard" in html_content

    artifact_content = artifact_out.read_text(encoding="utf-8")
    assert "StandupCoach Evaluation Report" in artifact_content


def test_cli_show_trend(tmp_path: Path, sample_payload: dict) -> None:
    """Test CLI --show-trend prints trend statistics."""
    history_file = tmp_path / "standup_history.json"
    html_out = tmp_path / "standup_dashboard.html"
    artifact_out = tmp_path / "latest_artifact.md"
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(json.dumps(sample_payload), encoding="utf-8")

    # Ingest one report first
    cmd_add = [
        sys.executable,
        "scripts/report_manager.py",
        "--add",
        str(payload_file),
        "--history-path",
        str(history_file),
        "--html-path",
        str(html_out),
        "--artifact-path",
        str(artifact_out),
    ]
    subprocess.run(cmd_add, capture_output=True, text=True, check=True)

    # Now run --show-trend
    cmd_trend = [
        sys.executable,
        "scripts/report_manager.py",
        "--history-path",
        str(history_file),
        "--show-trend",
    ]
    res = subprocess.run(cmd_trend, capture_output=True, text=True)
    assert res.returncode == 0, f"CLI stderr: {res.stderr}"
    assert "Total Sessions:" in res.stdout
    assert "Average Score:" in res.stdout
    assert "Trend Direction:" in res.stdout


def test_cli_missing_payload_file(tmp_path: Path) -> None:
    """Test CLI returns non-zero error when payload file does not exist."""
    nonexistent = tmp_path / "missing.json"
    cmd = [
        sys.executable,
        "scripts/report_manager.py",
        "--add",
        str(nonexistent),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode != 0
    assert "not found" in res.stderr.lower() or "error" in res.stderr.lower()


def test_cli_invalid_json_payload(tmp_path: Path) -> None:
    """Test CLI returns non-zero error when payload file has invalid JSON syntax."""
    bad_payload = tmp_path / "bad_payload.json"
    bad_payload.write_text("{not valid json", encoding="utf-8")

    cmd = [
        sys.executable,
        "scripts/report_manager.py",
        "--add",
        str(bad_payload),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode != 0
    assert "failed to parse json" in res.stderr.lower() or "error" in res.stderr.lower()


def test_cli_open_browser_flag(tmp_path: Path, sample_payload: dict) -> None:
    """Test ingest_payload calls webbrowser.open when open_browser is True."""
    from scripts.report_manager import ingest_payload

    history_file = tmp_path / "standup_history.json"
    html_out = tmp_path / "standup_dashboard.html"
    artifact_out = tmp_path / "latest_artifact.md"
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(json.dumps(sample_payload), encoding="utf-8")

    with patch("webbrowser.open") as mock_open:
        report, history_mgr = ingest_payload(
            payload_path=payload_file,
            history_path=history_file,
            html_path=html_out,
            artifact_path=artifact_out,
            open_browser=True,
        )
        assert report is not None
        assert history_mgr is not None
        assert mock_open.called
        opened_arg = mock_open.call_args[0][0]
        assert str(html_out.resolve().as_uri()) == opened_arg


def test_record_script_help() -> None:
    """Test record.py CLI help flag and default output message."""
    cmd = [
        sys.executable,
        "scripts/record.py",
        "--help",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "records/latest_report.wav" in res.stdout or "output" in res.stdout.lower()


def test_record_script_non_interactive_duration(tmp_path: Path) -> None:
    """Test record.py records a real WAV file for fixed duration without user input."""
    target_wav = tmp_path / "output_test.wav"
    cmd = [
        sys.executable,
        "scripts/record.py",
        "--output",
        str(target_wav),
        "--non-interactive",
        "--duration",
        "0.2",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Record stderr: {res.stderr}"
    assert target_wav.exists()
    assert target_wav.stat().st_size > 0

    # Verify it is a valid WAV audio file
    with wave.open(str(target_wav), "rb") as wf:
        assert wf.getnchannels() in (1, 2)
        assert wf.getframerate() == 16000
        assert wf.getnframes() > 0


def test_record_script_missing_duration_error() -> None:
    """Test record.py errors if non-interactive mode is set without duration."""
    cmd = [
        sys.executable,
        "scripts/record.py",
        "--non-interactive",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode != 0
    assert "requires specifying --duration" in res.stderr.lower()


def test_cli_combined_add_and_show_trend(tmp_path: Path, sample_payload: dict) -> None:
    """Test CLI handles both --add and --show-trend in one run, reusing history_mgr."""
    history_file = tmp_path / "standup_history.json"
    html_out = tmp_path / "standup_dashboard.html"
    artifact_out = tmp_path / "latest_artifact.md"
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(json.dumps(sample_payload), encoding="utf-8")

    cmd = [
        sys.executable,
        "scripts/report_manager.py",
        "--add",
        str(payload_file),
        "--history-path",
        str(history_file),
        "--html-path",
        str(html_out),
        "--artifact-path",
        str(artifact_out),
        "--show-trend",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"CLI stderr: {res.stderr}"
    # Ingestion message
    assert "StandupCoach: Evaluation saved successfully" in res.stdout
    assert "Session ID:" in res.stdout
    # Trend summary message
    assert "StandupCoach Performance Trend Summary" in res.stdout
    assert "Total Sessions:   1" in res.stdout
    assert "Average Score:" in res.stdout
