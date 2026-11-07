---
name: push
description: Use when the user types /push or asks to push changes to git, synchronize local branch with remote repository, or publish commits.
---

# Git Push Skill (/push)

Use this skill whenever the user triggers `/push` or requests to push local code/commits to the remote git repository.

## Workflow

### 1. Kiểm tra trạng thái Git (Inspect Status)
Chạy lệnh kiểm tra trạng thái working tree:
```powershell
git status
```

- **Trường hợp A: Còn file chưa commit (Uncommitted changes)**
  - Nếu có file mới hoặc thay đổi chưa commit:
    1. Kiểm tra xem có file nào nhạy cảm/không nên commit không (dựa trên `.gitignore`).
    2. Nếu các thay đổi hợp lệ, tự động tạo commit với Conventional Commits message súc tích:
       ```powershell
       git add -A
       git commit -m "<type>: <mô tả ngắn gọn công việc đã làm>"
       ```
- **Trường hợp B: Working tree sạch sẽ (Clean), đã có commit mới**
  - Chuyển tiếp ngay sang Bước 2.

### 2. Xác định nhánh và Remote (Detect Branch & Remote)
Lấy tên nhánh hiện tại và kiểm tra remote:
```powershell
git branch --show-current
git remote -v
```

### 3. Thực hiện Push (Execute Push)
- Nếu nhánh hiện tại đã có upstream tracking:
  ```powershell
  git push
  ```
- Nếu nhánh mới chưa có upstream:
  ```powershell
  git push -u origin <tên-nhánh-hiện-tại>
  ```

### 4. Báo cáo kết quả (Report)
Báo cáo ngắn gọn cho người dùng:
- Tên nhánh đã push (`branch`)
- Đường dẫn repository remote
- Mã commit SHA mới nhất
- Trạng thái xác nhận: Đồng bộ thành công 100%.
