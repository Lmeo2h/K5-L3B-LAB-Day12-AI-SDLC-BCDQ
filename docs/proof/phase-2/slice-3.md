# Bằng chứng Slice 3 Phase 2

Ngày 2026-11-21 (UTC+7). Windows PowerShell, Python 3.12.2, nhánh `feat/p2-s3-quan-v11-qa` từ `origin/main` tại `f71785e`, Contract 1.0. Dùng `PYTHONPATH=tests;.` và `PYTHONUTF8=1`. Bộ test P1 gọi `python3` từ contract. Lần chạy đặt bản sao tạm của Python thật tên `python3.exe` ở đầu PATH và dọn sau khi chạy.

| Kiểm tra | Kết quả quan sát |
|---|---|
| Test-first Slice 3 | Bốn lỗi mong đợi trước triển khai do thiếu `allowed_dishes`, loader chưa có `day` và từ chối `ca_keo`. |
| `python -m unittest tests.test_quan_v11 -v` | 6 đạt, 2 bỏ qua. Sáu ca dùng fixture từ TICKET-02 trong bộ nhớ. Hai ca CLI chờ Contract 1.1 và Slice 4. |
| Hồi quy 8 module test Phase 1 | 71/71 đạt với preset 1.0. |
| `python -m unittest discover -s tests -v` | 77 đạt, 2 bỏ qua, tổng 79. |
| `python tools/check_team.py` | `OK: 4 thành viên: duyhale95, missher03, Limdim1604, Lmeo2h` |
| Hai lần `python -m chonoi.headless --mode quan --seed 1 --ticks 1200 --out <đường dẫn>` | Hai mã thoát 0. SHA-256 giống nhau `FBB2A4978F85E7EB55A591ECE77D7BB27BB17A15FE8107EE5EF65475B967DF58`. |
| Ví dụ trong skill `chonoi-contract-guard` với kho có cá lóc và bông súng | Hai lần cho cùng SHA-256 `ABB2DCFDD39038C6271AC2B55E9EAF367C9DDE8794227879EB881472A0CD0E72`. Có `customer_arrived` tại tick 120. |
| `python -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out <đường dẫn>` | Mã 2, `unrecognized arguments: --days 1`, không có output. Chưa có mẫu benchmark hợp lệ. |

Test fixture v1.1 kiểm thứ tự bàn theo lịch, hai bếp nấu song song, đủ sáu món, lọc menu trước tồn kho, gọi lại món sau khi đã trả tiền đủ chỉ tiêu và từ chối scenario mâu thuẫn. Smoke chuyển kho có [log riêng](integration.md).

Sau khi Slice 1 merge, chạy lại toàn bộ test trên preset thật v1.1. Sau khi Slice 4 merge, chạy test CLI `day`, kiểm lỗi chuyển sang quán giữ mã 2 và không tạo output, chạy benchmark 22.200 tick và ghi dòng `end`. Kết quả tại tag `phase-2` cần được kiểm chứng trên `main`.
