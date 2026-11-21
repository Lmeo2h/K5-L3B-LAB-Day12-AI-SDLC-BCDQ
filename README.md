# Quán Ăn Chợ Nổi — Nhóm BCDQ (`v1.0.0`)

Game 2D mô phỏng tất định 60 Hz (**Út Sen** lặn bắt cá, hái rau trên sông buổi sáng và mở quán phục vụ khách buổi tối, nối liền vòng lặp nhiều ngày + cửa hàng nâng cấp + độ tươi cá thể), tuân thủ **Test Contract v1.3**.

## Chạy nhanh từ clone sạch (≤ 3 lệnh, macOS / Linux)

```bash
git clone https://github.com/Lmeo2h/K5-L3B-LAB-Day12-AI-SDLC-BCDQ.git
cd K5-L3B-LAB-Day12-AI-SDLC-BCDQ
python3 -m chonoi.live --mode day --days 5
```

Mở địa chỉ in ra trên terminal (mặc định `http://127.0.0.1:8000/`) bằng trình duyệt (khuyến nghị `1280×720`).

## Yêu cầu môi trường
- **Python 3.10+** (chỉ dùng **thư viện chuẩn Python**, không cần cài gói bên thứ ba).
- Trình duyệt hiện đại hỗ trợ HTML5 Canvas 2D (`chonoi/web/index.html`).

## Phím điều khiển (`chonoi.live`)
- **Di chuyển:** `WASD` hoặc phím mũi tên (`↑ ↓ ← →`)
- **Tương tác / Hái / Cập bến / Nấu & Phục vụ:** `E`
- **Bắt cá dưới nước:** `Space`
- **Tạm dừng / Tiếp tục:** `Esc` hoặc `P`
- **Chế độ tương phản cao:** `C` hoặc `H` (hoặc nút trên giao diện)
- **Shop cuối ngày:** `1` (Bình Oxy), `2` (Áo phao / Máu), `Enter` (Xong)
- **Chơi lại:** `R`

## Các lệnh kiểm thử, Headless, Benchmark & Soak

```bash
# 1. Toàn bộ unit & integration tests (P1–P4)
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 tools/check_team.py

# 2. Chế độ Headless tất định (gather / quan / day)
python3 -m chonoi.headless --mode day --days 5 --seed 1 --ticks 22200 --out out_day.jsonl

# 3. Benchmark render 1280x720 (làm nóng 3s + đo 30s -> bench.json)
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

# 4. Soak headless 10 Ngày liên tiếp (lặp D1–D5 ở Ngày 6–10 -> soak.json)
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

# 5. Đóng gói bản phát hành (chonoi-v1.0.0.zip)
python3 tools/package_release.py
```

*(Trên Windows PowerShell, thay `PYTHONPATH=tests:.` bằng `$env:PYTHONPATH="tests;."` và `python3` bằng `python`.)*

## Giới hạn đã biết
- Trên Windows nếu bật alias `python3` của Microsoft Store, các test gọi `headless_cmd` (`python3`) qua `subprocess` có thể gặp `WinError 1920` (khắc phục bằng cách tắt App Execution Alias hoặc chạy trên Linux/macOS/CI).
- Các tính năng mở rộng tùy chọn ngoài lõi (`Lao xua`, `Vợt hút cá`, `Rắn Hổ Mây`, `Cháy món`, `Chợ Chú Sáu`, `Sổ tay & Cá Hô`, `Dòng nước lũ`, `Khách đặt trước`) được giữ ngoài phạm vi lõi `v1.0.0` để bảo toàn Test Contract `v1.3` và hiệu năng.

## Tài liệu & Giấy phép
- Giấy phép: [`LICENSE`](LICENSE) (MIT) · Nguồn & Công cụ AI: [`CREDITS.md`](CREDITS.md) · Lịch sử thay đổi: [`CHANGELOG.md`](CHANGELOG.md)
- Thành viên nhóm BCDQ: [`TEAM.md`](TEAM.md) · Hướng dẫn agent: [`AGENTS.md`](AGENTS.md)
