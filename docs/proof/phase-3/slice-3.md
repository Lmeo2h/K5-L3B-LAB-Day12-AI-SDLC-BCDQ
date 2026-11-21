# Bằng chứng Slice 3 Phase 3

Ngày 2026-11-21 (UTC+7), Python 3.12.2 trên Windows. Base `608baaa`, Contract đang là 1.1. Dùng `PYTHONPATH=tests;.`, `PYTHONUTF8=1` và bản sao Python tạm tên `python3.exe` trên PATH để lệnh trong contract chạy được.

| Kiểm tra | Kết quả quan sát |
|---|---|
| Test-first ngày 21/11 | Bốn ca ban đầu báo lỗi khi Quán cố chuyển mảng cá thể sang dict đếm. |
| `python -m unittest discover -s tests -v` | 104 đạt, 6 bỏ qua, tổng 110. Sáu ca mới chờ adapter kho v1.2. |
| `tests.test_quan_freshness_v12` với adapter tạm trong bộ nhớ | 5 đạt, ca CLI bỏ qua. Adapter tạm dùng scale 240 và kiểm list/ID trùng để cô lập luật Quán. Chưa dùng bộ đọc kho thật. |
| `python tools/check_team.py` | Mã 0, đủ 4 thành viên. |
| Hai lượt `--mode quan --seed 1 --ticks 1200` dùng cùng kho và seed | File giống từng byte. SHA-256 `baa6ee70c39099b9a4f4e17f2afd743381007342093c355567e36ea741879b08` trên v1.1. |
| `--mode day --days 1 --seed 1 --ticks 22200` | 0,708 giây trên v1.1, `state=finished`, `reason=days_complete`, `days_completed=1`. |

Các test P1/P2 về khách, bếp, thực đơn và smoke chuyển kho chọn fixture theo phiên bản. Khi bật v1.2, các assertion tiêu thụ kiểm cá thể và giá sau một tick hao tươi, các assertion bàn giao đối chiếu nguyên mảng ở tick 0.

Thứ tự trong brief Slice 3 đặt `dish_ready` cùng bước timer trước sự kiện ươn. Mục thứ tự trên lab board liệt kê xét món chín/cháy sau phần giữ chỗ bị ươn. Bản này theo thứ tự brief của lát. Cần nhóm thống nhất trường hợp hai sự kiện trùng tick trước khi gắn tag.
