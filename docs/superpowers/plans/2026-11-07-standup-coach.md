# StandupCoach Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng StandupCoach — trợ lý AI tích hợp trực tiếp trong Antigravity giúp luyện tập và đánh giá khắt khe báo cáo Daily Standup thực tế (chào hỏi, chia sẻ màn hình Jira, đã làm, sẽ làm, blocker, Q&A, câu chốt) qua giọng nói, chấm điểm thang 100 và theo dõi tiến trình 10 lần gần nhất.

**Architecture:** Hệ thống gồm 3 tầng: (1) Ingestion & Audio Capture (hỗ trợ file âm thanh có sẵn và script ghi âm nhẹ `record.py`), (2) Data & Dashboard Engine (Python modules xử lý lưu trữ JSON, tính toán thống kê và sinh cả Antigravity Markdown Artifact lẫn HTML Chart.js dashboard), và (3) Antigravity Custom Skill (`.gemini/skills/standup-coach/SKILL.md`) hướng dẫn Gemini multimodal phân tích audio trực tiếp theo rubric 6 tiêu chí chuẩn Agile.

**Tech Stack:** Python 3.10+, Standard Library (`json`, `dataclasses`, `pathlib`), `pytest` cho kiểm thử, Chart.js (CDN cho visual HTML report), Mermaid & Markdown cho native Antigravity Artifacts.

**Spec:** [docs/superpowers/specs/2026-11-07-standup-coach-design.md](file:///e:/2_Antigravity/03_report_checker_tool/docs/superpowers/specs/2026-11-07-standup-coach-design.md)

## Global Constraints
- **Môi trường hoạt động:** Tích hợp trực tiếp Antigravity IDE, không yêu cầu external paid API key.
- **Thư mục workspace:** Giữ nguyên tên thư mục hiện tại `03_report_checker_tool` trên hệ điều hành; toàn bộ tên hiển thị trong mã nguồn, tài liệu và dashboard là `StandupCoach`.
- **Ngôn ngữ hỗ trợ:** Tiếng Việt kết hợp thuật ngữ công nghệ thông tin và Jira bằng tiếng Anh.
- **Dữ liệu bền vững:** Dữ liệu lịch sử lưu tại `data/standup_history.json`.
- **Thang điểm chuẩn:** Thang 100 với 6 tiêu chí khắt khe: Chuẩn quy trình Daily & Jira (20đ), Dễ hiểu & súc tích (20đ), Ổn định phát âm & từ ngữ IT (15đ), Liên kết câu (15đ), Ngắt nghỉ & nhịp điệu (15đ), Kiểm soát từ đệm & chuyên nghiệp (15đ).

## Review Focus
1. **Dữ liệu lịch sử rỗng (First-run scenario):** Khi người dùng chạy lần đầu tiên, file `data/standup_history.json` chưa tồn tại hoặc rỗng, hệ thống phải tự động khởi tạo mà không báo lỗi.
2. **Xử lý số lượng báo cáo biến thiên (< 10 lần và > 10 lần):** Khi có ít hơn 10 lần nộp, biểu đồ xu hướng hiển thị đầy đủ các lần đã có; khi vượt quá 10 lần, biểu đồ lấy chính xác 10 lần gần nhất.
3. **Phát hiện câu chốt chuyển giao:** Nếu bài nói thiếu câu chốt ("em đã report xong..."), hệ thống phải cảnh báo rõ ràng trong phần nhận xét và trừ điểm tương ứng trong rubric.
4. **Xử lý tình huống có hoặc không có Blocker / Q&A:** Nếu ứng viên không có blocker nhưng đã xác nhận rõ "không có blocker", vẫn được trọn điểm; nếu có Q&A trong audio thì đánh giá thêm phản hồi ngắn gọn.
5. **Độ tương thích Dashboard:** Antigravity Markdown Artifact phải render chính xác biểu đồ Mermaid trong chat/artifact panel; file HTML sinh ra phải mở độc lập được trên bất kỳ trình duyệt nào mà không cần web server.

---

### Task 1: Data Models & Storage Schema

**Files:**
- Create: `src/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: Python standard library (`dataclasses`, `typing`, `json`)
- Produces: `RubricScores`, `StandupReport`, `HistoryStore`

- [ ] **Step 1: Write the failing test for data models**

```python
# tests/test_models.py
from datetime import datetime
from src.models import RubricScores, StandupReport

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
        suggested_script="Chào mọi người, trên ticket PROJ-123..."
    )
    data = report.to_dict()
    assert data["total_score"] == 85
    assert data["scores"]["process_and_jira"] == 18
    assert data["closing_confirmed"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'src')

- [ ] **Step 3: Implement `src/models.py`**

Define dataclasses `RubricScores` (validating range 0-20, 0-15, and calculating `total`), and `StandupReport` with `to_dict()` and `from_dict()` serialization.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/models.py tests/test_models.py
git commit -m "feat: add data models for rubric scores and standup report"
```

---

### Task 2: History Manager & Trend Calculator

**Files:**
- Create: `src/history_manager.py`
- Test: `tests/test_history_manager.py`

**Interfaces:**
- Consumes: `StandupReport`, `RubricScores` from `src/models.py`
- Produces: `HistoryManager` class with `add_report(report)`, `get_recent_reports(limit=10)`, `calculate_trend()`, `load_or_create()`

- [ ] **Step 1: Write the failing test for `HistoryManager`**

```python
# tests/test_history_manager.py
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
            timestamp=f"2026-11-0{i+1:02d}T09:00:00",
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_history_manager.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'src.history_manager')

- [ ] **Step 3: Implement `src/history_manager.py`**

Implement `HistoryManager` with atomic file writes to JSON, loading with fallback to empty list, and statistics calculations (average score, diff from previous session, trend direction).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_history_manager.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/history_manager.py tests/test_history_manager.py
git commit -m "feat: add history manager for persistent session tracking and trend calculation"
```

---

### Task 3: Dashboard Generator (Antigravity Markdown Artifact & HTML Visualizer)

**Files:**
- Create: `src/dashboard_generator.py`
- Test: `tests/test_dashboard_generator.py`

**Interfaces:**
- Consumes: `StandupReport`, `HistoryManager` from `src.history_manager`
- Produces: `DashboardGenerator.generate_markdown_artifact(report, history)` and `DashboardGenerator.generate_html_dashboard(report, history)`

- [ ] **Step 1: Write the failing test for `DashboardGenerator`**

```python
# tests/test_dashboard_generator.py
from src.models import RubricScores, StandupReport
from src.dashboard_generator import DashboardGenerator

def test_generate_markdown_artifact():
    scores = RubricScores(18, 17, 14, 13, 14, 12)
    report = StandupReport(
        id="rep-01",
        timestamp="2026-11-07T09:00:00",
        audio_file="records/sample.wav",
        duration_seconds=70,
        wpm=135,
        closing_confirmed=True,
        scores=scores,
        filler_words_count=2,
        strengths=["Dẫn dắt Jira tự tin", "Cấu trúc rõ ràng"],
        weaknesses=["Từ đệm 'à' xuất hiện 2 lần"],
        suggested_script="Mẫu câu tối ưu..."
    )
    generator = DashboardGenerator()
    md_content = generator.generate_markdown_artifact(report, recent_reports=[report])
    
    assert "# 🎙️ StandupCoach Evaluation Report" in md_content
    assert "88 / 100" in md_content
    assert "mermaid" in md_content
    assert "Mẫu câu tối ưu..." in md_content

def test_generate_html_dashboard():
    scores = RubricScores(18, 17, 14, 13, 14, 12)
    report = StandupReport(
        id="rep-01",
        timestamp="2026-11-07T09:00:00",
        audio_file="records/sample.wav",
        duration_seconds=70,
        wpm=135,
        closing_confirmed=True,
        scores=scores,
        filler_words_count=2,
        strengths=["Dẫn dắt Jira"],
        weaknesses=["Từ đệm"],
        suggested_script="..."
    )
    generator = DashboardGenerator()
    html_content = generator.generate_html_dashboard(report, recent_reports=[report])
    
    assert "<!DOCTYPE html>" in html_content
    assert "chart.js" in html_content.lower()
    assert "radar" in html_content.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_dashboard_generator.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'src.dashboard_generator')

- [ ] **Step 3: Implement `src/dashboard_generator.py`**

- Generate Markdown Artifact with: Scorecard summary, 6-criteria table with status badges (Đạt/Cần cải thiện), Mermaid X-Y chart or graph for 10-run trend, specific quotes and rewrites.
- Generate HTML Dashboard with: Modern responsive dark/light UI, Chart.js Radar Chart (6 criteria) and Line Chart (last 10 sessions), details collapse cards.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_dashboard_generator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dashboard_generator.py tests/test_dashboard_generator.py
git commit -m "feat: implement markdown artifact and html dashboard generators"
```

---

### Task 4: CLI Integration Script & One-Touch Recording Utility

**Files:**
- Create: `scripts/report_manager.py`
- Create: `scripts/record.py`
- Test: `tests/test_cli_integration.py`

**Interfaces:**
- Consumes: `src.history_manager`, `src.dashboard_generator`
- Produces: CLI interface to record, ingest JSON analysis from Agent, update `data/standup_history.json`, and output reports.

- [ ] **Step 1: Write the failing test for `scripts/report_manager.py`**

```python
# tests/test_cli_integration.py
import json
import subprocess
import sys
from pathlib import Path

def test_cli_add_report(tmp_path):
    history_file = tmp_path / "standup_history.json"
    html_out = tmp_path / "standup_dashboard.html"
    
    payload = {
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
            "filler_words_control": 14
        },
        "filler_words_count": 1,
        "strengths": ["Dẫn dắt Jira mượt mà"],
        "weaknesses": ["Nói hơi nhanh ở phần blocker"],
        "suggested_script": "Chào anh em..."
    }
    
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(json.dumps(payload), encoding="utf-8")
    
    cmd = [
        sys.executable, "scripts/report_manager.py",
        "--add", str(payload_file),
        "--history-path", str(history_file),
        "--html-path", str(html_out)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert history_file.exists()
    assert html_out.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_integration.py -v`
Expected: FAIL (No such file or directory: 'scripts/report_manager.py')

- [ ] **Step 3: Implement `scripts/report_manager.py` and `scripts/record.py`**

- `scripts/report_manager.py`: Parses CLI args (`--add`, `--history-path`, `--html-path`, `--show-trend`), loads input JSON, updates history, triggers `DashboardGenerator`.
- `scripts/record.py`: One-touch interactive recorder (supports Windows via standard library wave + winsound or optional sounddevice/wave; provides clear prompts: "Press Enter to start recording, Press Enter to stop").

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_integration.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/report_manager.py scripts/record.py tests/test_cli_integration.py
git commit -m "feat: add CLI report manager and one-touch audio recording utility"
```

---

### Task 5: Antigravity Custom Skill Definition & E2E Validation

**Files:**
- Create: `.gemini/skills/standup-coach/SKILL.md`
- Create: `tests/test_e2e_flow.py`
- Create: `records/sample_standup.txt` (reference demo transcript and test fixture)

**Interfaces:**
- Consumes: Antigravity Skill Protocol, `scripts/report_manager.py`
- Produces: Antigravity Skill ready to evaluate user audio directly in chat.

- [ ] **Step 1: Write E2E test verifying end-to-end integration**

```python
# tests/test_e2e_flow.py
import subprocess
import sys
import json
from pathlib import Path

def test_full_pipeline_flow(tmp_path):
    history_file = tmp_path / "standup_history.json"
    html_out = tmp_path / "standup_dashboard.html"
    
    # Simulate first report
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
            "filler_words_control": 13
        },
        "filler_words_count": 2,
        "strengths": ["Chào hỏi tự tin, share task Jira rõ ràng"],
        "weaknesses": ["Còn dùng từ đệm 'ừm' 2 lần khi chuyển ý"],
        "suggested_script": "Chào mọi người, trên Jira ticket ABC-456..."
    }
    input_json = tmp_path / "input.json"
    input_json.write_text(json.dumps(sample_data), encoding="utf-8")
    
    res = subprocess.run([
        sys.executable, "scripts/report_manager.py",
        "--add", str(input_json),
        "--history-path", str(history_file),
        "--html-path", str(html_out)
    ], capture_output=True, text=True)
    
    assert res.returncode == 0
    assert "StandupCoach: Evaluation saved successfully" in res.stdout
    assert history_file.exists()
    assert html_out.exists()
```

- [ ] **Step 2: Run test to verify it fails before skill & full CLI link**

Run: `pytest tests/test_e2e_flow.py -v`
Expected: PASS once Task 4 is in place.

- [ ] **Step 3: Author `.gemini/skills/standup-coach/SKILL.md`**

Write the complete skill specification with:
- Frontmatter (`name: standup-coach`, `description: Huấn luyện viên và giám khảo đánh giá báo cáo Daily Standup chuyên nghiệp...`)
- Role & Persona: Huấn luyện viên Agile khắt khe, thẳng thắn, mang tính xây dựng cao.
- Input triggers: Nhận file audio (`.wav`, `.mp3`, `.m4a`) hoặc audio record trong chat.
- Quy trình 6 bước thực tế: Chào hỏi -> Jira task -> Đã làm -> Sẽ làm -> Blocker -> Q&A & Kết thúc.
- Rubric 6 tiêu chí chấm điểm thang 100 chi tiết.
- Hướng dẫn gọi `scripts/report_manager.py` và xuất Antigravity Artifact ngay lập tức.

- [ ] **Step 4: Run full test suite across the entire project**

Run: `pytest tests -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add .gemini/skills/standup-coach/SKILL.md tests/test_e2e_flow.py records/
git commit -m "feat: add standup-coach antigravity custom skill and verify e2e flow"
```
