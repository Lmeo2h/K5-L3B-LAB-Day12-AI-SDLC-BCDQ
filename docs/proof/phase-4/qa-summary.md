# Kiểm chứng Bench và Soak Phase 4

Chạy ngày 2026-11-21 trên Windows, Python 3.12.2 và Chrome 158.0.8127.36. Bản ghép tạm dùng `main` tại `3b290ed`, mã Bench của Slice 3 và các đầu nhánh Slice 1 `c39b1e9`, Slice 2 `ca2c5ce`, Slice 4 `fd521fa`. Preset của bản ghép là Contract 1.3. Các phép đo này chưa chạy trên commit phát hành đã gắn tag.

| Phép kiểm | Kết quả |
|---|---|
| `python -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json` | Canvas Chrome headless 1280×720, làm nóng 3 giây. Đo 2.161 frame trong 30,014 giây, **72,00 FPS** trung bình, **64,74 FPS** ở 1% thấp nhất và tải frame đầu trong **863,23 ms**. [JSON gốc](bench.json) |
| `python -m chonoi.soak --seed 7 --days 10 --out docs/proof/phase-4/soak.json` | Hai lượt hoàn tất **10/10 Ngày**, **0 crash**, cùng `results` và số Ngày. Thời gian từng lượt là 2,774 giây và 2,764 giây. [JSON lượt đầu](soak.json) |
| `python -m unittest discover -s tests -v` | **139/139 đạt**, 19,785 giây. [Log đầy đủ](regression.log) |
| `python tools/check_team.py` | Mã 0. Danh sách gồm `duyhale95`, `missher03`, `Limdim1604`, `Lmeo2h`. [Log](regression.log) |

Lượt unittest bao gồm CLI fallback không cần trình duyệt, nhánh tự chọn fallback, công thức FPS và thử lỗi thay file để xác nhận báo cáo cũ còn nguyên. Trên Windows dùng `PYTHONPATH=tests;.`, `PYTHONUTF8=1` và executable Python tạm tên `python3.exe` trên PATH cho các test gọi contract.
