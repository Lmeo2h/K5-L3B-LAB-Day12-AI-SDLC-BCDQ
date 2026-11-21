# Kiểm chứng Bench và Soak Phase 4

Chạy ngày 2026-11-21 trên Windows, Python 3.12.2 và Chrome 158.0.8127.36.

## Nhánh Bench sau khi Slice 1 merge

Lượt chính chạy ở `b2a2cf0`, dựa trên `origin/main` tại `d2cbaf3` (Contract 1.3).

| Phép kiểm | Kết quả |
|---|---|
| `python -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json` | Canvas Chrome headless 1280×720, làm nóng 3 giây. Đo 2.161 frame trong 30,014 giây, **72,00 FPS** trung bình, **67,48 FPS** ở 1% thấp nhất và tải frame đầu trong **851,82 ms**. [JSON gốc](bench.json) |
| `python -m chonoi.soak --seed 7 --days 10 --out docs/proof/phase-4/soak.json` | Hai lượt hoàn tất **10/10 Ngày**, **0 crash**, cùng `results` và số Ngày. Thời gian từng lượt là 2,787 giây và 2,773 giây. [JSON lượt đầu](soak.json) |
| `python -m unittest discover -s tests -v` | **136/136 đạt**, 19,391 giây. [Log đầy đủ](regression.log) |
| `python tools/check_team.py` | Mã 0. Danh sách gồm `duyhale95`, `missher03`, `Limdim1604`, `Lmeo2h`. [Log](regression.log) |

Lượt unittest bao gồm CLI fallback không cần trình duyệt, nhánh tự chọn fallback, công thức FPS và thử lỗi thay file để xác nhận báo cáo cũ còn nguyên. Trên Windows dùng `PYTHONPATH=tests;.`, `PYTHONUTF8=1` và executable Python tạm tên `python3.exe` trên PATH cho các test gọi contract.

## Bản ghép đủ bốn lát

Bản ghép tạm dùng `main` tại `3b290ed`, mã Bench của Slice 3 và các đầu nhánh Slice 1 `c39b1e9`, Slice 2 `ca2c5ce`, Slice 4 `fd521fa`. Chrome đo 72,00 FPS trung bình, 1% low 64,74 FPS và 863,23 ms tải. Hai lượt soak cùng hoàn tất 10 Ngày, 0 crash, kết quả gameplay trùng nhau. Bộ test gồm cả cảnh báo và tương phản cao đạt **139/139**. [Log đầy đủ](regression.log)

Cần đối chiếu lại khi có commit phát hành gắn tag trên `main`.
