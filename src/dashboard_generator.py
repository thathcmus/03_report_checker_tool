"""Dashboard Generator for StandupCoach.

Generates:
1. Native Antigravity Markdown Artifact for chat/artifacts pane with GitHub-style alerts,
   6-criteria evaluation table, audio quality diagnostics, and Mermaid trend chart.
2. Standalone HTML Visualizer with Chart.js Radar Chart (6 criteria) and Line Chart
   (10-session trend), viewable directly in browsers via file:// protocol.
"""

from __future__ import annotations

import html
import json
from typing import Any

from src.models import StandupReport


CRITERIA_DEFINITIONS: list[dict[str, Any]] = [
    {
        "key": "process_and_jira",
        "name": "Quy trình & Jira",
        "full_name": "Chuẩn quy trình Daily meeting & Jira context",
        "max": 20,
        "description": "Chào hỏi, mở Jira task, Yesterday, Today, Blocker, chuyển giao",
    },
    {
        "key": "clarity_and_conciseness",
        "name": "Dễ hiểu & Trọng tâm",
        "full_name": "Độ dễ hiểu, súc tích & Trọng tâm",
        "max": 20,
        "description": "Trọng tâm mục tiêu/kết quả, không lan man tiểu tiết",
    },
    {
        "key": "pronunciation_and_terms",
        "name": "Phát âm & Thuật ngữ",
        "full_name": "Độ ổn định phát âm & Thuật ngữ IT",
        "max": 15,
        "description": "Rõ ràng tiếng Việt & thuật ngữ Sprint, PR, Deploy, Ticket...",
    },
    {
        "key": "cohesion_and_flow",
        "name": "Mạch tư duy & Flow",
        "full_name": "Độ liên kết câu & Mạch tư duy",
        "max": 15,
        "description": "Mạch lạc giữa việc hôm qua -> hôm nay -> blocker, liên từ tự nhiên",
    },
    {
        "key": "pacing_and_pauses",
        "name": "Ngắt nghỉ & Nhịp điệu",
        "full_name": "Mức độ ngắt nghỉ & Nhịp điệu (Pacing)",
        "max": 15,
        "description": "Tốc độ 120-150 từ/phút, ngắt nghỉ đúng chỗ, không hụt hơi",
    },
    {
        "key": "filler_words_control",
        "name": "Kiểm soát từ đệm",
        "full_name": "Kiểm soát từ đệm & Tính chuyên nghiệp",
        "max": 15,
        "description": "Hạn chế 'à', 'ừm', 'kiểu như', ngập ngừng ngắt quãng",
    },
]


def _extract_recent_reports(
    report: StandupReport,
    recent_reports: Any = None,
    limit: int = 10,
) -> list[StandupReport]:
    """Module-level compatibility helper for extracting recent reports."""
    return DashboardGenerator._extract_recent_reports(report, recent_reports, limit=limit)


def _format_audio_quality(audio_quality: dict[str, Any]) -> tuple[str, str]:
    """Extract and normalize volume and noise diagnostic labels."""
    vol = (
        audio_quality.get("volume")
        or audio_quality.get("volume_level")
        or audio_quality.get("microphone")
        or "Optimal"
    )
    noise = (
        audio_quality.get("noise")
        or audio_quality.get("noise_level")
        or audio_quality.get("background_noise")
        or "Clean"
    )
    return str(vol), str(noise)


class DashboardGenerator:
    """Generates markdown artifacts and standalone HTML visualizers for standup evaluations."""

    @classmethod
    def _extract_recent_reports(
        cls,
        report: StandupReport,
        recent_reports: Any = None,
        limit: int = 10,
    ) -> list[StandupReport]:
        """Extract a list of recent reports from list, HistoryManager, or default.

        If recent_reports does not already contain a report with r.id == report.id,
        appends report so the active report is always reflected as the latest point
        in the trend chart, then returns reports[-limit:].
        """
        reports: list[StandupReport] = []
        if recent_reports is None:
            reports = []
        elif hasattr(recent_reports, "get_recent_reports") and callable(recent_reports.get_recent_reports):
            items = recent_reports.get_recent_reports(limit=limit)
            reports = list(items) if items else []
        elif hasattr(recent_reports, "reports") and isinstance(recent_reports.reports, list):
            reports = list(recent_reports.reports)
        elif isinstance(recent_reports, list):
            reports = list(recent_reports)
        else:
            reports = []

        if not any(getattr(r, "id", None) == report.id for r in reports):
            reports.append(report)

        return reports[-limit:] if limit > 0 else []

    @classmethod
    def generate_markdown_artifact(
        cls,
        report: StandupReport,
        recent_reports: Any = None,
        history: Any = None,
        **kwargs: Any,
    ) -> str:
        """Generate Antigravity-native Markdown Artifact.

        Includes:
        - Scorecard summary & status badge
        - GitHub-style diagnostic alerts (> [!NOTE], > [!TIP], > [!WARNING])
        - 6-criteria score breakdown table with status tags
        - Mermaid xychart-beta progression graph
        - Audio Quality diagnostics
        - Strengths, Weaknesses, and Suggested Script Rewrite
        """
        if recent_reports is None and history is not None:
            recent_reports = history

        history_list = cls._extract_recent_reports(report, recent_reports, limit=10)
        vol_label, noise_label = _format_audio_quality(report.audio_quality)

        total_score = report.total_score
        status_tag = "✅ Đạt chuẩn" if total_score >= 80 else "⚠️ Cần cải thiện"

        # Audio quality diagnosis alert
        audio_alert_type = (
            "WARNING"
            if (vol_label.lower().replace("_", " ") in ("too quiet", "clipping", "noisy", "too noisy")
                or noise_label.lower().replace("_", " ") in ("noisy", "too noisy"))
            else "NOTE"
        )

        # Mermaid xychart-beta generation
        session_labels: list[str] = []
        score_values: list[int] = []
        for idx, r in enumerate(history_list, start=1):
            session_labels.append(f'"S{idx}"')
            score_values.append(r.total_score)

        labels_str = ", ".join(session_labels)
        scores_str = ", ".join(str(s) for s in score_values)

        mermaid_chart = (
            "```mermaid\n"
            "xychart-beta\n"
            '    title "Tiến độ điểm số các phiên gần nhất (Score Progression)"\n'
            f"    x-axis [{labels_str}]\n"
            '    y-axis "Điểm (0-100)" 0 --> 100\n'
            f"    line [{scores_str}]\n"
            "```"
        )

        # 6 criteria rows
        table_rows: list[str] = []
        scores_obj = report.scores
        for item in CRITERIA_DEFINITIONS:
            key = item["key"]
            val = getattr(scores_obj, key, 0) if scores_obj else 0
            max_val = item["max"]
            pct = int((val / max_val) * 100) if max_val > 0 else 0
            badge = "✅ Đạt" if pct >= 80 else "⚠️ Cần cải thiện"
            table_rows.append(
                f"| **{item['name']}** <br><sub>*{item['full_name']}*</sub> | "
                f"**{val}** / {max_val} | {pct}% | {badge} |"
            )
        table_body = "\n".join(table_rows)

        # Strengths list
        if report.strengths:
            strengths_md = "\n".join(f"- ✅ {s}" for s in report.strengths)
        else:
            strengths_md = "- *(Chưa có ghi nhận điểm mạnh đặc biệt)*"

        # Weaknesses list
        if report.weaknesses:
            weaknesses_md = "\n".join(f"- ⚠️ {w}" for w in report.weaknesses)
        else:
            weaknesses_md = "- *(Không có điểm yếu nghiêm trọng)*"

        # Suggested script
        script_raw = report.suggested_script.strip() if report.suggested_script else "*(Không có kịch bản gợi ý)*"
        script_md = "\n> ".join(script_raw.splitlines())

        # Closing confirmation message
        closing_msg = (
            "✅ Có câu chốt chuyển giao rõ ràng"
            if report.closing_confirmed
            else "⚠️ Chưa có câu chốt chuyển giao rõ ràng"
        )

        md = f"""# 🎙️ StandupCoach Evaluation Report

> **Session ID:** `{report.id}` | **Thời gian:** `{report.timestamp}` | **File:** `{report.audio_file}`

---

## 🏆 Điểm tổng quan: **{total_score} / 100** ({status_tag})

| Thời lượng | Tốc độ nói | Từ đệm | Kết thúc chuyển giao |
|:---:|:---:|:---:|:---:|
| **{report.duration_seconds}s** | **{report.wpm} WPM** *(Chuẩn: 120-150)* | **{report.filler_words_count}** từ | {closing_msg} |

> [!{audio_alert_type}]
> **Hardware & Noise Diagnostic (Chất lượng Mic & Môi trường):**
> - **Âm lượng Micro (Volume):** `{vol_label}` *(Chuẩn: Optimal)*
> - **Tạp âm nền (Background Noise):** `{noise_label}` *(Chuẩn: Clean)*
> *(Lưu ý: Chỉ số phần cứng nhằm hỗ trợ điều chỉnh mic, không trừ điểm kỹ năng nói).*

---

### 📊 Bảng đánh giá chi tiết 6 tiêu chí (Rubric Breakdown)

| Tiêu chí đánh giá | Điểm số | Tỷ lệ | Trạng thái |
|---|:---:|:---:|:---:|
{table_body}
| **TỔNG KẾT** | **{total_score}** / 100 | **{total_score}%** | **{status_tag}** |

---

### 📈 Lịch sử tiến độ điểm số (10 phiên gần nhất)

{mermaid_chart}

---

### 💡 Phân tích chi tiết & Góp ý cải thiện

#### 🌟 Điểm làm tốt:
{strengths_md}

#### 🎯 Điểm cần khắc phục:
{weaknesses_md}

> [!TIP]
> **Coaching Tip:** Để bài standup trôi chảy và chuyên nghiệp hơn, hãy mở sẵn Jira ticket trên màn hình trước khi bắt đầu nói. Luôn sử dụng câu chốt chuyển giao (VD: *"Em đã report xong, mời anh Nam tiếp theo ạ"*) để đồng nghiệp nắm được nhịp và tiếp nối mượt mà.

---

### 📝 Mẫu kịch bản đề xuất (Suggested Script Rewrite)

> {script_md}
"""
        return md

    @classmethod
    def generate_html_dashboard(
        cls,
        report: StandupReport,
        recent_reports: Any = None,
        history: Any = None,
        **kwargs: Any,
    ) -> str:
        """Generate Standalone HTML Visualizer with Chart.js Radar and Line charts.

        Features:
        - Modern responsive dashboard UI with clean styling
        - Chart.js Radar chart for the 6 rubric criteria
        - Chart.js Line chart for 10-session trend
        - Audio quality hardware diagnostic badges
        - Detailed breakdown table and expandable script card
        - Works completely offline / via file:// protocol
        """
        if recent_reports is None and history is not None:
            recent_reports = history

        history_list = cls._extract_recent_reports(report, recent_reports, limit=10)
        vol_label, noise_label = _format_audio_quality(report.audio_quality)

        total_score = report.total_score
        scores_obj = report.scores

        # Prepare Radar Chart data
        radar_labels = [item["name"] for item in CRITERIA_DEFINITIONS]
        radar_values = [
            getattr(scores_obj, item["key"], 0) if scores_obj else 0
            for item in CRITERIA_DEFINITIONS
        ]
        radar_max_values = [item["max"] for item in CRITERIA_DEFINITIONS]

        # Prepare Line Chart data
        trend_labels = [f"Session {i}" for i in range(1, len(history_list) + 1)]
        trend_scores = [r.total_score for r in history_list]

        # Criteria table HTML rows
        table_rows_html = []
        for item in CRITERIA_DEFINITIONS:
            key = item["key"]
            val = getattr(scores_obj, key, 0) if scores_obj else 0
            max_val = item["max"]
            pct = int((val / max_val) * 100) if max_val > 0 else 0
            badge_class = "badge-success" if pct >= 80 else "badge-warning"
            badge_text = "Đạt" if pct >= 80 else "Cần cải thiện"
            table_rows_html.append(
                f"""<tr>
                    <td>
                        <div class="criteria-title">{html.escape(item['name'])}</div>
                        <div class="criteria-desc">{html.escape(item['description'])}</div>
                    </td>
                    <td class="text-center font-bold">{val} / {max_val}</td>
                    <td>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: {pct}%;"></div>
                        </div>
                    </td>
                    <td class="text-center"><span class="badge {badge_class}">{badge_text}</span></td>
                </tr>"""
            )
        criteria_tbody = "\n".join(table_rows_html)

        # Strengths HTML
        if report.strengths:
            strengths_items = "".join(f"<li>{html.escape(s)}</li>" for s in report.strengths)
        else:
            strengths_items = "<li>Chưa có điểm nổi bật</li>"

        # Weaknesses HTML
        if report.weaknesses:
            weaknesses_items = "".join(f"<li>{html.escape(w)}</li>" for w in report.weaknesses)
        else:
            weaknesses_items = "<li>Không có điểm yếu nghiêm trọng</li>"

        # Status badge
        overall_badge_class = "badge-success" if total_score >= 80 else "badge-warning"
        overall_badge_text = "Đạt chuẩn" if total_score >= 80 else "Cần cải thiện"

        # Audio Quality badge styling
        vol_class = "badge-success" if vol_label.lower() == "optimal" else "badge-warning"
        noise_class = "badge-success" if noise_label.lower() == "clean" else "badge-warning"

        closing_text = "✅ Đã xác nhận" if report.closing_confirmed else "⚠️ Chưa có"

        html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StandupCoach Evaluation Dashboard - {html.escape(report.id)}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-page: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #24344d;
            --border-color: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #3b82f6;
            --primary-light: #60a5fa;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-page);
            color: var(--text-main);
            padding: 24px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
        }}
        .header-title h1 {{
            font-size: 1.75rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .header-title p {{
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-top: 4px;
        }}
        .diagnostic-pill-box {{
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(30, 41, 59, 0.8);
            padding: 8px 16px;
            border-radius: 9999px;
            border: 1px solid var(--border-color);
        }}
        .diagnostic-label {{
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        .badge-success {{
            background: rgba(16, 185, 129, 0.2);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.4);
        }}
        .badge-warning {{
            background: rgba(245, 158, 11, 0.2);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.4);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .stat-card .label {{
            font-size: 0.85rem;
            color: var(--text-muted);
        }}
        .stat-card .value {{
            font-size: 1.8rem;
            font-weight: 700;
            margin: 6px 0;
            color: var(--text-main);
        }}
        .stat-card .subtext {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}
        .chart-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            min-height: 380px;
            display: flex;
            flex-direction: column;
        }}
        .chart-header {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .chart-wrapper {{
            position: relative;
            flex: 1;
            width: 100%;
            height: 300px;
        }}
        .table-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            font-size: 0.85rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .criteria-title {{
            font-weight: 600;
            color: var(--text-main);
        }}
        .criteria-desc {{
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 2px;
        }}
        .text-center {{ text-align: center; }}
        .font-bold {{ font-weight: 700; }}
        .progress-bar-bg {{
            background: #334155;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            width: 100%;
            min-width: 100px;
        }}
        .progress-bar-fill {{
            background: linear-gradient(90deg, #3b82f6, #10b981);
            height: 100%;
            border-radius: 4px;
        }}
        .insights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}
        .insight-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
        }}
        .insight-card h3 {{
            font-size: 1.05rem;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .insight-card ul {{
            list-style: none;
            padding-left: 0;
        }}
        .insight-card li {{
            padding: 6px 0;
            font-size: 0.9rem;
            border-bottom: 1px dashed rgba(51, 65, 85, 0.6);
        }}
        .script-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
        }}
        .script-header {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .script-box {{
            background: #0f172a;
            border: 1px solid var(--border-color);
            border-left: 4px solid var(--primary);
            border-radius: 8px;
            padding: 16px;
            font-family: inherit;
            font-size: 0.92rem;
            color: #e2e8f0;
            line-height: 1.6;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title">
                <h1>🎙️ StandupCoach Evaluation Dashboard</h1>
                <p>Mã phiên: {html.escape(report.id)} | Thời gian: {html.escape(report.timestamp)}</p>
            </div>
            <div class="diagnostic-pill-box">
                <span class="diagnostic-label">Micro & Noise:</span>
                <span class="badge {vol_class}">Mic: {html.escape(vol_label)}</span>
                <span class="badge {noise_class}">Noise: {html.escape(noise_label)}</span>
            </div>
        </header>

        <section class="stats-grid">
            <div class="stat-card">
                <span class="label">Điểm tổng kết</span>
                <span class="value">{total_score} <span style="font-size: 1rem; color: var(--text-muted);">/ 100</span></span>
                <span class="subtext"><span class="badge {overall_badge_class}">{overall_badge_text}</span></span>
            </div>
            <div class="stat-card">
                <span class="label">Tốc độ nói (WPM)</span>
                <span class="value">{report.wpm}</span>
                <span class="subtext">Chuẩn khuyến nghị: 120-150 WPM</span>
            </div>
            <div class="stat-card">
                <span class="label">Thời lượng</span>
                <span class="value">{report.duration_seconds}s</span>
                <span class="subtext">Thời gian báo cáo</span>
            </div>
            <div class="stat-card">
                <span class="label">Từ đệm phát hiện</span>
                <span class="value">{report.filler_words_count}</span>
                <span class="subtext">"à", "ừm", "kiểu như"...</span>
            </div>
            <div class="stat-card">
                <span class="label">Kết thúc chuyển giao</span>
                <span class="value" style="font-size: 1.25rem; margin: 12px 0;">{closing_text}</span>
                <span class="subtext">Chuyển giao quyền phát biểu</span>
            </div>
        </section>

        <section class="charts-grid">
            <div class="chart-card">
                <div class="chart-header">
                    <span>🎯 Đánh giá 6 Tiêu chí Rubric</span>
                    <span class="badge badge-success">Radar View</span>
                </div>
                <div class="chart-wrapper">
                    <canvas id="radarChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <div class="chart-header">
                    <span>📈 Xu hướng điểm số (10 phiên gần nhất)</span>
                    <span class="badge badge-success">Line Trend</span>
                </div>
                <div class="chart-wrapper">
                    <canvas id="trendChart"></canvas>
                </div>
            </div>
        </section>

        <section class="table-card">
            <div class="chart-header">
                <span>📋 Bảng điểm chi tiết từng tiêu chí</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 45%;">Tiêu chí</th>
                        <th class="text-center" style="width: 15%;">Điểm số</th>
                        <th style="width: 25%;">Tỷ lệ hoàn thành</th>
                        <th class="text-center" style="width: 15%;">Trạng thái</th>
                    </tr>
                </thead>
                <tbody>
                    {criteria_tbody}
                </tbody>
            </table>
        </section>

        <section class="insights-grid">
            <div class="insight-card">
                <h3>🌟 Điểm mạnh nổi bật</h3>
                <ul>
                    {strengths_items}
                </ul>
            </div>
            <div class="insight-card">
                <h3>🎯 Điểm cần tối ưu</h3>
                <ul>
                    {weaknesses_items}
                </ul>
            </div>
        </section>

        <section class="script-card">
            <div class="script-header">
                <span>📝 Mẫu kịch bản đề xuất (Suggested Script Rewrite)</span>
            </div>
            <div class="script-box">{html.escape(report.suggested_script or "Chưa có kịch bản mẫu.")}</div>
        </section>
    </div>

    <script>
        const radarLabels = {json.dumps(radar_labels, ensure_ascii=False)};
        const radarData = {json.dumps(radar_values)};
        const radarMaxData = {json.dumps(radar_max_values)};

        const ctxRadar = document.getElementById('radarChart').getContext('2d');
        new Chart(ctxRadar, {{
            type: 'radar',
            data: {{
                labels: radarLabels,
                datasets: [{{
                    label: 'Điểm thực tế',
                    data: radarData,
                    backgroundColor: 'rgba(59, 130, 246, 0.25)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 2
                }}, {{
                    label: 'Điểm tối đa',
                    data: radarMaxData,
                    borderColor: 'rgba(148, 163, 184, 0.35)',
                    borderDash: [4, 4],
                    pointRadius: 0,
                    fill: false
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    r: {{
                        angleLines: {{ color: 'rgba(255, 255, 255, 0.1)' }},
                        grid: {{ color: 'rgba(255, 255, 255, 0.1)' }},
                        pointLabels: {{
                            color: '#cbd5e1',
                            font: {{ size: 11 }}
                        }},
                        ticks: {{
                            backdropColor: 'transparent',
                            color: '#94a3b8',
                            stepSize: 5
                        }},
                        suggestedMin: 0,
                        suggestedMax: 20
                    }}
                }},
                plugins: {{
                    legend: {{
                        labels: {{ color: '#cbd5e1' }}
                    }}
                }}
            }}
        }});

        const trendLabels = {json.dumps(trend_labels, ensure_ascii=False)};
        const trendData = {json.dumps(trend_scores)};

        const ctxTrend = document.getElementById('trendChart').getContext('2d');
        new Chart(ctxTrend, {{
            type: 'line',
            data: {{
                labels: trendLabels,
                datasets: [{{
                    label: 'Tổng điểm (Thang 100)',
                    data: trendData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: '#10b981',
                    pointBorderColor: '#fff',
                    pointRadius: 5,
                    pointHoverRadius: 7
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                        ticks: {{ color: '#94a3b8' }}
                    }},
                    y: {{
                        min: 0,
                        max: 100,
                        grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                        ticks: {{ color: '#94a3b8' }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        labels: {{ color: '#cbd5e1' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        return html_content
