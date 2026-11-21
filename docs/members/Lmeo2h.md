# `Lmeo2h` — phản tư cá nhân

- **Tôi đã làm:**
  - Phase 1: Bếp, bưng món, phục vụ, thanh toán/boa/uy tín & đóng ca (`chonoi/sim/quan.py`, `tests/test_quan_service.py` — PR #4 `ef2c1a9`), gắn tag `phase-1`.
  - Phase 2: `ShopSim` (`chonoi/sim/shop.py`), `DaySim` (`chonoi/sim/day.py`), `pause` 3 chế độ & Envelope v1.1 (`runner.py`, `headless.py`, `live.py`), HUD/Menu v1.1 (`chonoi/web/index.html`, `tests/test_day_shop_pause.py` — PR #8 `25fde94`), gắn tag `phase-2`.
  - Phase 3: `ShopSim`/`runner` v1.2, HUD độ tươi & nhãn `[ƯƠN]` (`< 30`), `CHANGELOG.md`, `AGENTS.md`, `tests/test_v12_handoff_ui.py` (PR #10 `f975e16`), gắn tag `phase-3`.
  - Phase 4: `README.md` (clone sạch ≤ 3 lệnh), `LICENSE`, `CREDITS.md`, `CHANGELOG.md` tổng hợp, `tools/package_release.py`, đóng gói & phát hành `v1.0.0`.
- **Tôi đã review:** Đọc chéo PR của `Limdim1604` (Slice 3 các phase) và đối chiếu hợp đồng tích hợp giữa `gather` → `quan` → `shop`.
- **AI sai ở đâu và tôi phát hiện thế nào:** Ở Phase 1 bản nháp đầu dùng chuỗi `dish_id` cho `hand` và cho phép fallthrough khi `interact`; đối chiếu trực tiếp PRD-0 đã sửa sang `{order_id, dish_id, base_price}` và bỏ lượt đúng quy tắc.
- **Điều tôi học được:** Khóa hợp đồng dữ liệu (`game.contract.json`, `CHANGELOG.md`) và chạy smoke liên pha sớm giúp 4 nhánh tích hợp mượt mà đúng hạn tag.
