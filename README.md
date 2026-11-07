# 🎙️ StandupCoach

> **AI Daily Standup Meeting Reviewer & Voice Coach**  
> Trợ lý ảo tích hợp trực tiếp trong **Google Antigravity**, giúp kỹ sư luyện tập và nâng cao chất lượng báo cáo Daily Meeting qua giọng nói với bộ tiêu chí khắt khe chuẩn Agile/Scrum.

---

## 🌟 Điểm nổi bật (Key Features)

- **🧠 Phân tích âm thanh gốc (Native Multimodal Audio)**: Tận dụng trực tiếp mô hình Gemini cao cấp nhất trong Antigravity để "nghe" file âm thanh gốc mà không bị mất mát dữ liệu qua khâu bóc băng (STT) trung gian — cảm nhận trọn vẹn nhịp thở, độ rung giọng, khoảng lặng ngắt nghỉ và ngữ điệu.
- **🎙️ Thu âm 1 chạm (Zero-dependency Native Audio)**: Script tiện ích `scripts/record.py` cho phép thu âm mic trực tiếp trên Windows (sử dụng native Windows Multimedia `winmm.dll` qua `ctypes`), không bắt buộc cài đặt các thư viện C++ phức tạp.
- **📋 Quy trình chuẩn Daily Meeting 6 bước**:
  1. *Chào hỏi mở đầu* tự tin, đúng tác phong kỹ sư.
  2. *Dẫn dắt màn hình Jira Task* (chia sẻ màn hình, trích dẫn mã ticket cụ thể).
  3. *Báo cáo Việc đã làm* (Yesterday).
  4. *Báo cáo Việc sẽ làm* (Today).
  5. *Nêu Blocker / Khó khăn* (hoặc xác nhận rõ *"hiện tại em không có blocker nào"*).
  6. *Xử lý trao đổi qua lại (Q&A)* nhanh gọn & *Câu chốt chuyển giao* lượt nói (*"Em đã report xong, mời mọi người..."*).
- **🔊 Chẩn đoán Microphone & Tiếng ồn môi trường (Hardware & Noise Diagnostic)**:
  - Cảnh báo âm lượng mic: *Quá bé (Too quiet)*, *Tối ưu (Optimal)*, hoặc *Quá lớn/Rè (Clipping)*.
  - Đo mức tạp âm nền: *Sạch (Clean)*, *Ồn vừa phải (Moderate)*, hoặc *Quá ồn (Too noisy)*.
  - Phân tách độc lập thành badge kỹ thuật, không trừ oan vào điểm kỹ năng nói.
- **🎯 Thang điểm 100 & Nhận xét khắt khe**: Đánh giá chi tiết 6 tiêu chí cốt lõi, trích dẫn chính xác lỗi phát âm, từ đệm ("à, ừm, thì là mà") và viết lại mẫu câu chuẩn ngắn gọn hơn.
- **📊 Báo cáo kép trực quan (Dual Dashboard)**:
  - **Inline trong Antigravity**: Xuất Antigravity Markdown Artifact ngay trong tab Artifacts của IDE với bảng điểm chi tiết và biểu đồ tiến trình Mermaid (`xychart-beta`).
  - **Visual HTML Dashboard**: Tự động sinh file `reports/standup_dashboard.html` với Chart.js (Radar chart 6 tiêu chí & Line chart xu hướng 10 lần gần nhất) và tự động mở trên trình duyệt.
- **🔒 Bảo mật & Riêng tư**: Toàn bộ file ghi âm cá nhân và lịch sử chấm điểm được lưu trữ cục bộ, đã cấu hình `.gitignore` chặn đẩy dữ liệu nhạy cảm lên repository công khai.

---

## 📐 Cấu trúc thư mục (Project Structure)

```text
03_report_checker_tool/
├── .agents/
│   └── skills/
│       ├── push/
│       │   └── SKILL.md            # Git push skill (/push)
│       └── standup-coach/
│           └── SKILL.md            # Antigravity Custom Skill prompt & Persona
├── .gemini/
│   └── skills/
│       └── standup-coach/
│           └── SKILL.md            # Bản đồng bộ Skill cho tương thích đa cấu hình
├── docs/
│   └── superpowers/
│       ├── specs/                  # Tài liệu thiết kế kỹ thuật (Design Doc)
│       └── plans/                  # Kế hoạch triển khai chi tiết (Implementation Plan)
├── data/
│   ├── .gitkeep                    # Giữ cấu trúc thư mục trên Git
│   └── standup_history.json        # File lưu trữ lịch sử các lần báo cáo (git-ignored)
├── records/
│   ├── sample_standup.txt          # 4 kịch bản mẫu tiếng Việt tham khảo (DevOps, Frontend, Backend)
│   └── latest_report.wav           # File ghi âm mới nhất từ mic (git-ignored)
├── reports/
│   ├── .gitkeep
│   └── standup_dashboard.html      # Dashboard đồ thị trực quan Chart.js (git-ignored)
├── scripts/
│   ├── record.py                   # Tiện ích thu âm 1-chạm qua Microphone
│   └── report_manager.py           # CLI quản lý lịch sử, tính trend và sinh Dashboard
├── src/
│   ├── __init__.py
│   ├── models.py                   # Data models (RubricScores, StandupReport, HistoryStore)
│   ├── history_manager.py          # Atomic JSON persistence & 10-session trend calculator
│   └── dashboard_generator.py      # Bộ sinh Markdown Artifact & HTML Visualizer
├── tests/
│   ├── test_models.py              # Test dataclasses, bounds validation & serialization
│   ├── test_history_manager.py     # Test lưu trữ atomic, Windows file locking & trend stats
│   ├── test_dashboard_generator.py # Test Mermaid chart, HTML escaping & Chart.js radar/line
│   ├── test_cli_integration.py     # Test các cờ lệnh CLI (--add, --show-trend, record)
│   └── test_e2e_flow.py            # Test toàn bộ luồng tích hợp End-to-End
├── .gitignore                      # Quy tắc lọc file nhạy cảm và file tạm
└── README.md                       # Tài liệu hướng dẫn sử dụng
```

---

## 🚀 Hướng dẫn sử dụng nhanh (Quick Start)

### Cách 1: Thu âm trực tiếp bằng Microphone (Khuyên dùng)

1. Mở Terminal (PowerShell hoặc Command Prompt) trong thư mục dự án và chạy:
   ```powershell
   python scripts/record.py
   ```
2. Nhấn **Enter** và bắt đầu nói báo cáo Daily meeting của bạn:
   > *"Chào mọi người, trên Jira ticket ABC-102 hôm qua em đã hoàn thành API đăng nhập, hôm nay em tiếp tục làm module thanh toán. Hiện tại em không có blocker nào. Em đã report xong, mời anh Nam report tiếp ạ."*
3. Nhấn **Enter** lần nữa để kết thúc. File âm thanh sẽ tự động lưu vào `records/latest_report.wav`.
4. Quay lại khung chat Antigravity và nhắn:
   > *"Hãy đánh giá bài report trong file records/latest_report.wav giúp tôi."*
   
   Hệ thống sẽ lập tức phân tích, chấm điểm, xuất Markdown Artifact trong IDE và tự động mở Dashboard đồ thị trên trình duyệt.

### Cách 2: Phân tích file ghi âm có sẵn

1. Kéo file ghi âm (`.wav`, `.mp3`, `.m4a`) vào thư mục `records/` (ví dụ: `records/my_daily.mp3`).
2. Nhắn trong chat Antigravity:
   > *"Review report daily trong file records/my_daily.mp3 giúp mình."*

---

## 📊 Bộ rubric chấm điểm khắt khe (Thang 100)

| STT | Tiêu chí đánh giá | Điểm tối đa | Nội dung trọng tâm |
|:---:|---|:---:|---|
| **1** | **Chuẩn quy trình Daily meeting & Jira context** | **20đ** | Đầy đủ 6 bước: Chào hỏi, dẫn dắt màn hình Jira, đã làm, sẽ làm, blocker, câu chốt chuyển giao. |
| **2** | **Độ dễ hiểu, súc tích & Trọng tâm** | **20đ** | Đi thẳng vào kết quả, không lan man tiểu tiết code; xử lý câu hỏi Q&A ngắn gọn, dứt khoát. |
| **3** | **Độ ổn định từ ngữ & Phát âm thuật ngữ IT** | **15đ** | Tròn vành rõ chữ cả tiếng Việt và thuật ngữ kỹ thuật (Sprint, PR, Deploy, Ticket, Merge, Refactor...). |
| **4** | **Độ liên kết câu & Mạch tư duy** | **15đ** | Mạch lạc giữa việc hôm qua -> việc hôm nay -> blocker. Dùng liên từ tự nhiên, chuyển ý mượt mà. |
| **5** | **Mức độ ngắt nghỉ & Nhịp điệu (Pacing & Pauses)** | **15đ** | Tốc độ lý tưởng 120–150 từ/phút, dừng đúng dấu câu/ý, không nói một hơi gây hụt hơi. |
| **6** | **Kiểm soát từ đệm & Tính chuyên nghiệp** | **15đ** | Hạn chế tối đa các từ đệm: "à", "ừm", "kiểu như", "thì là mà". Cứ mỗi 2 từ đệm trừ 1–2 điểm. |
| 🔍 | **Chẩn đoán Microphone & Môi trường** | *Badge riêng* | Đánh giá độc lập: Âm lượng (Quá bé / Chuẩn / Rè) và Độ ồn nền (Sạch / Ồn vừa / Quá ồn). |

---

## 🛠️ CLI Utilities (Dành cho Developer)

### 1. Quản lý lịch sử và xem xu hướng
```powershell
# Xem tóm tắt xu hướng 10 lần report gần nhất qua terminal
python scripts/report_manager.py --show-trend

# Mở dashboard trực quan trên trình duyệt
python scripts/report_manager.py --open-browser
```

### 2. Chạy kiểm thử tự động (Test Suite)
Dự án được xây dựng theo phương pháp TDD với kiểm thử phủ toàn diện:
```powershell
python -m pytest tests -v
```
*(Kết quả: 46/46 unit & integration tests pass 100% trong ~2.5 giây).*

---

## 📄 License
Phát triển cho mục đích cá nhân và nội bộ trong môi trường **Google Antigravity**.
