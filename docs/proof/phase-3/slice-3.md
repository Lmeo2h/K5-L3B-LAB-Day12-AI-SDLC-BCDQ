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

## Sau khi Slice 1 merge (`7c31363`)

- Test Slice 3 dùng adapter thật có 6 ca đạt, 1 ca CLI chờ bật nghiêm ngặt v1.2. Đã kiểm chứng CLI đọc kho cá thể và giữ đúng ID khi nhận fixture từ hai file.
- Trong bản sao tạm bật Contract 1.2, chạy `test_quan_freshness_v12`, `test_quan_customers`, `test_quan_service`, `test_quan_v11` và `test_smoke_p1`: **57/57 đạt**. Kho đếm cũ thoát mã 2 trước khi tạo output. Nhánh chính của lát vẫn dùng phiên bản chuyển tiếp để chờ Slice 2.
- Lần chạy toàn suite sau khi rebase Slice 1 có 119 ca. Có 6 lỗi từ `test_day_shop_pause` và `test_gather_monsters`: fixture giỏ dạng chuỗi hoặc `DaySim` cũ gọi `.items()` trên mảng cá thể. `check_team.py` đạt. Cần chạy lại toàn suite sau khi các lát liên quan merge.
- [Smoke bàn giao hai tiến trình](integration.md) xác nhận ID, loại và đơn vị độ tươi của từng cá thể ở tick 0. Test P1/P2 giữ các assertion về luật và dùng fixture kho cá thể khi bật v1.2.

## Ghép thử các lát trong bản sao tạm

Ghép Slice 2 tại `9e25f87` và runtime/kiểm thử Slice 4 tại `bedb846` vào mã Slice 3, bật 1.2 trong bản sao. Lệnh headless `--mode day --days 1 --seed 1 --ticks 22200` hoàn tất **0,857 giây**, dòng `end` có `state=finished`, `reason=days_complete`, `days_completed=1` và `sim_tick=22200`.

Toàn suite của bản ghép tạm có **119 đạt, 6 lỗi, tổng 125**. Các lỗi nằm ở fixture `hold` dạng chuỗi của `test_gather_monsters` và `test_day_shop_pause`, cùng assertion còn yêu cầu phiên bản 1.1 trong `test_gather_fish_v11`. Kết quả này dùng để phối hợp sửa ở các lát sở hữu test trước khi chạy lại trên commit bàn giao.

Thứ tự trong brief Slice 3 đặt `dish_ready` cùng bước timer trước sự kiện ươn. Mục thứ tự trên lab board liệt kê xét món chín/cháy sau phần giữ chỗ bị ươn. Bản này theo thứ tự brief của lát. Cần nhóm thống nhất trường hợp hai sự kiện trùng tick trước khi gắn tag.
