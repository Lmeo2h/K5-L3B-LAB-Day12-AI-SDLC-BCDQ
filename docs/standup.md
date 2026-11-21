# Standup giữa phase (mỗi người một dòng, 2–3 phút)

Các dòng Phase 4 được tổng hợp sau tích hợp từ PR, ma trận QA và retro.

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 4 | `duyhale95` | Contract v1.3, vòng kế hoạch D1–D5 và soak 10 ngày đã merge. [PR #14](https://github.com/Lmeo2h/K5-L3B-LAB-Day12-AI-SDLC-BCDQ/pull/14) | Đối chiếu kết quả soak trong hồ sơ bàn giao. | Hai lượt soak hoàn tất 10 ngày, 0 crash, kết quả gameplay trùng nhau. [Log QA](proof/phase-4/qa-summary.md) |
| 4 | `missher03` | Ba cảnh báo, chế độ tương phản cao và test UI đã merge. [PR #17](https://github.com/Lmeo2h/K5-L3B-LAB-Day12-AI-SDLC-BCDQ/pull/17) | Chơi thử từng cảnh báo. | Ma trận ghi còn thiếu kiểm tra trực tiếp đủ ba cảnh báo. [Ma trận QA](verification/phase-4.md) |
| 4 | `Limdim1604` | Benchmark Chrome, fallback phần mềm, bằng chứng soak và hồi quy đã merge. [PR #16](https://github.com/Lmeo2h/K5-L3B-LAB-Day12-AI-SDLC-BCDQ/pull/16) | Đối chiếu bằng chứng với bản phát hành. | Test gọi `python3` trên Windows cần đặt Python thật vào PATH. [Log QA](proof/phase-4/qa-summary.md) |
| 4 | `Lmeo2h` | Tài liệu và công cụ đóng gói đã merge. Có tag `phase-4`. [PR #15](https://github.com/Lmeo2h/K5-L3B-LAB-Day12-AI-SDLC-BCDQ/pull/15) | Công bố Release `v1.0.0` kèm zip và kiểm clone sạch trên macOS/Linux. | Hồ sơ hiện có kết quả đóng gói và chạy trên Windows. [Ma trận QA](verification/phase-4.md) |
