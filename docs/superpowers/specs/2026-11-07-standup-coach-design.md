# StandupCoach Design Document

## 1. Intent and Why
Dự án **StandupCoach** là một trợ lý ảo cá nhân tích hợp trực tiếp trong Antigravity nhằm giúp kỹ sư / người dùng luyện tập và nâng cao chất lượng báo cáo Daily Standup meeting qua giọng nói. Mục tiêu cốt lõi là biến các bài report rườm rà, ngập ngừng, thiếu trọng tâm thành các phần báo cáo súc tích, mạch lạc, chuyên nghiệp và tiết kiệm thời gian cho cả nhóm.

## 2. Goals, Non-Goals, and Anti-Goals
- **Goals:**
  - Nhận diện và tiếp nhận file âm thanh (hoặc voice input) trong Antigravity.
  - Tự động nhận diện câu chốt báo cáo (ví dụ: *"em đã report xong, mời mọi người report tiếp"* hoặc tương tự) để đánh dấu ranh giới kết thúc bài nói.
  - Chấm điểm khắt khe trên thang 100 dựa trên 6 tiêu chí chuẩn mực thực tế:
    1. *Độ ổn định trong từng từ nói & phát âm thuật ngữ IT/Jira* (Pronunciation & Articulation Stability)
    2. *Độ dễ hiểu & tính tinh gọn* (Clarity & Conciseness, bao gồm xử lý Q&A ngắn gọn nếu có)
    3. *Độ liên kết câu & mạch tư duy* (Cohesion & Logical Flow)
    4. *Mức độ ngắt nghỉ & nhịp điệu (Pacing & Pauses)*
    5. *Kiểm soát từ đệm & ngập ngừng* (Filler words: à, ừm, kiểu như...)
    6. *Chuẩn quy trình Daily meeting thực tế* (Chào hỏi - Dẫn dắt Jira task - Đã làm - Sẽ làm - Nêu Blocker/hỗ trợ - Q&A nếu có - Câu chốt chuyển giao)
  - Đưa ra nhận xét cụ thể, khách quan, trích dẫn chính xác lỗi phát âm hoặc câu dài dòng và gợi ý câu viết lại tốt hơn.
  - Lưu trữ lịch sử báo cáo bền vững vào file `data/standup_history.json` trong workspace.
  - Hiển thị kết quả bằng giao diện trực quan (Antigravity Artifact / Generative UI) gồm thẻ điểm, bảng nhận xét và biểu đồ radar + biểu đồ xu hướng 10 lần gần nhất.
- **Non-Goals:**
  - Không trở thành công cụ ghi âm/transcription toàn bộ cuộc họp nhiều người tham gia.
  - Không yêu cầu cài đặt server bên ngoài hay trả phí Gemini API Key riêng biệt.
- **Anti-Goals:**
  - Không đưa ra lời khen xã giao vô thưởng vô phạt. Nhận xét phải thẳng thắn, khắt khe và mang tính xây dựng cao để người dùng tiến bộ thực chất.
  - Không làm mất hoặc ghi đè sai lịch sử báo cáo khi người dùng mở phiên làm việc mới.

## 3. Constraints
- **Môi trường hoạt động:** Antigravity IDE (Gemini multimodal core).
- **Tên dự án:** `StandupCoach` (thư mục vật lý hiện tại là `03_report_checker_tool` được giữ nguyên để bảo toàn trạng thái workspace và lịch sử chat của Antigravity).
- **Ngôn ngữ xử lý chính:** Tiếng Việt (chấp nhận và hỗ trợ chuẩn xác các thuật ngữ kỹ thuật công nghệ thông tin thông dụng bằng tiếng Anh như *PR, deploy, bug, merge, refactor, backend, sprint*...).
- **Không dùng external paid API:** Toàn bộ quá trình phân tích âm thanh tận dụng mô hình Gemini tích hợp sẵn trong Antigravity.

## 4. Approaches Considered
- **Phương án A: Web App độc lập (Python Streamlit + Gemini API)**
  - *Mô tả:* Chạy local server web bằng Streamlit, dùng Python `google-genai` SDK gọi Gemini API.
  - *Đánh đổi:* Trải nghiệm nút bấm thu âm trên web tốt nhưng bắt buộc người dùng tự đăng ký và trả phí Gemini API key, phải bật server thủ công.
- **Phương án B: Antigravity Custom Skill + Generative UI Artifacts (Được chọn)**
  - *Mô tả:* Tạo một Custom Skill Antigravity chuyên biệt (`standup-coach`), lưu lịch sử vào `data/standup_history.json`, dùng Artifact HTML để hiển thị dashboard trực quan.
  - *Lý do chọn:* Tận dụng 100% năng lực Multimodal Audio của Gemini trên Antigravity mà không tốn chi phí API key, dữ liệu gắn liền với workspace, giao diện artifact phong phú.

## 5. Architectural Design & How It Works

### 5.1. Thành phần hệ thống & Luồng hoạt động
1. **Audio Ingestion (Hai phương thức tiếp nhận âm thanh)**:
   - *Cách 1 (File có sẵn)*: Người dùng kéo/thả file âm thanh (`.mp3`, `.wav`, `.m4a`) vào thư mục `records/` hoặc cung cấp đường dẫn trong chat.
   - *Cách 2 (Thu âm trực tiếp)*: Script tiện ích `scripts/record.py` (sử dụng thư viện ghi âm nhẹ). Người dùng chỉ cần gõ lệnh chạy, nhấn Enter để nói, nhấn Enter để kết thúc; file sẽ tự động lưu vào `records/latest_report.wav` để agent phân tích ngay.
2. **Antigravity Custom Skill (`.gemini/skills/standup-coach/SKILL.md`)**:
   - Đóng vai trò Giám khảo / Huấn luyện viên báo cáo Standup khắt khe.
   - Định nghĩa quy trình chấm điểm 6 tiêu chí (Thang 100).
   - Kiểm tra câu chốt kết thúc báo cáo ("em đã report xong...").
   - Trích xuất chi tiết từng lỗi phát âm, từ đệm, cấu trúc câu chưa gãy gọn và viết lại mẫu câu chuẩn.
   - Kích hoạt `scripts/report_manager.py` để cập nhật dữ liệu và hiển thị báo cáo.
3. **Bộ lưu trữ lịch sử (`data/standup_history.json`)**:
   - Lưu trữ có cấu trúc các phiên báo cáo: `id`, `timestamp`, `audio_file`, `duration_seconds`, `wpm`, `closing_confirmed`, `total_score`, `scores` (chi tiết 6 tiêu chí), `filler_words_count`, `strengths`, `weaknesses`, `suggested_script`.
   - Giữ lại đầy đủ dữ liệu để tính toán xu hướng 10 lần gần nhất.
4. **Trình quản lý & Xuất Dashboard đa nền tảng (`scripts/report_manager.py`)**:
   - *Báo cáo inline trong Antigravity*: Tự động tạo Antigravity Markdown Artifact hiển thị ngay trong tab Artifacts của IDE với bảng điểm chi tiết, các callout nhắc nhở và biểu đồ tiến trình dạng Mermaid chart.
   - *Dashboard trực quan trình duyệt*: Tạo file `reports/standup_dashboard.html` với thư viện Chart.js (Radar chart 6 tiêu chí & Line chart xu hướng 10 lần gần nhất), hỗ trợ mở nhanh trên trình duyệt khi người dùng cần xem đồ thị trực quan.

## 5.2. Quy trình chuẩn Daily Standup & Rubric chấm điểm chi tiết (Thang 100)

### Quy trình chuẩn thực tế (6 bước):
1. **Chào hỏi mở đầu**: Chào team/Scrum Master một cách tự tin, chuyên nghiệp (ví dụ: *"Chào anh em/mọi người, em xin phép report..."*).
2. **Dẫn dắt màn hình Jira Task**: Đề cập việc chia sẻ màn hình và tham chiếu mã ticket Jira cụ thể (ví dụ: *"Mọi người thấy màn hình Jira em rồi đúng không ạ, trên ticket ABC-123..."*).
3. **Báo cáo Việc đã làm (Yesterday)**: Tóm tắt ngắn gọn kết quả đạt được, không kể lể quá trình dài dòng.
4. **Báo cáo Việc sẽ làm (Today)**: Nêu rõ mục tiêu công việc trong ngày và dự kiến hoàn thành.
5. **Nêu Blocker / Khó khăn (nếu có)**: Nêu chính xác điểm nghẽn, ai/bộ phận nào cần phối hợp hỗ trợ; nếu trơn tru thì xác nhận rõ *"hiện tại em không có blocker nào"*.
6. **Xử lý trao đổi qua lại & Kết thúc chuyển giao**: Trả lời nhanh, đúng trọng tâm nếu có đồng nghiệp hỏi; kết thúc bằng câu chốt chuyển giao rõ ràng (ví dụ: *"Em đã report xong, mời anh Nam / mời bạn tiếp theo report ạ"*).

### Phân bổ điểm chi tiết (Thang 100):
- **1. Chuẩn quy trình Daily meeting & Jira context (20 điểm):**
  - Đầy đủ chào hỏi, dẫn dắt Jira task, đã làm, sẽ làm, blocker và câu chốt chuyển giao. Thiếu bước nào trừ điểm tương ứng.
- **2. Độ dễ hiểu, súc tích & Trọng tâm (20 điểm):**
  - Trọng tâm vào kết quả/mục tiêu; không lan man tiểu tiết kỹ thuật ngoài lề; nếu có Q&A qua lại thì trả lời ngắn gọn, thẳng thắn, không biện hộ vòng vo.
- **3. Độ ổn định từ ngữ & Phát âm (15 điểm):**
  - Phát âm rõ ràng, không nuốt chữ, tròn vành rõ chữ cả tiếng Việt và các thuật ngữ Jira/Tech (Sprint, Backlog, Deploy, Ticket, PR, Merge...).
- **4. Độ liên kết câu & Mạch tư duy (15 điểm):**
  - Mạch lạc giữa việc hôm qua -> việc hôm nay -> lý do blocker. Dùng liên từ tự nhiên, chuyển ý dứt khoát.
- **5. Mức độ ngắt nghỉ & Nhịp điệu (15 điểm):**
  - Tốc độ nói vừa phải (120-150 từ/phút), dừng đúng lúc chuyển ý (ví dụ sau khi kết thúc việc hôm qua chuyển sang việc hôm nay), không bị hụt hơi.
- **6. Kiểm soát từ đệm & Tính chuyên nghiệp (15 điểm):**
  - Hạn chế tối đa các từ đệm: "à", "ừm", "kiểu như", "thì là mà", các âm kéo dài khi đang suy nghĩ. Cứ mỗi 2 từ đệm trừ 1-2 điểm.

### 5.3. Nhận diện kết thúc
- Skill kiểm tra xem bài report có kết thúc bằng câu chuyển giao / đóng phiên hay không (ví dụ: *"em đã report xong, mời anh/chị... tiếp theo"*). Nếu thiếu, nhắc nhở và trừ nhẹ điểm chuyên nghiệp (1-2 điểm).

## 6. What's Left to the Builder
- Triển khai cấu trúc file của Skill `.gemini/skills/standup-coach/` và cấu hình metadata.
- Triển khai script `scripts/report_manager.py` xử lý JSON I/O và tạo giao diện HTML trực quan với Chart.js (tương thích Antigravity Artifact).
- Viết test suite giả lập dữ liệu lịch sử để đảm bảo tính toán thống kê và render biểu đồ 10 lần gần nhất chạy ổn định.
