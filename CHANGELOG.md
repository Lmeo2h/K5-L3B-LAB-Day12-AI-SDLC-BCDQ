# Changelog

## [1.3.0 / v1.0.0] - Phase 4 (TICKET-04) — Phát hành v1.0.0
- **Test Contract `v1.3`:** Bổ sung `bench_cmd` và `soak_cmd` ở gốc `game.contract.json`; giữ nguyên gameplay, tuning, kho cá thể và JSONL `v1.2`.
- **Soak headless (`chonoi/soak.py`):** Hỗ trợ chạy bot tất định `N` ngày liên tiếp (`--seed 7 --days 10 --out soak.json`), `DaySim` lặp kế hoạch `D1–D5` cho Ngày `6–10`.
- **Render Benchmark (`chonoi/bench.py`):** Đo hiệu năng render cảnh lặn `1280×720` (làm nóng `3s` + đo `duration`s), xuất `bench.json` (`avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`).
- **HUD & Khả năng tiếp cận (`chonoi/web/index.html`):** Đầy đủ 3 cảnh báo (Thủy quái gần, Oxy thấp/Hết hơi, Khách sắp giận `< 25%`) kèm biểu tượng + chữ và chế độ tương phản cao (`C`/`H`).
- **Đóng gói & Phát hành:** `README.md` (chạy clone sạch ≤ 3 lệnh), `LICENSE` (MIT), `CREDITS.md`, `tools/package_release.py` (`chonoi-v1.0.0.zip`), phản tư `docs/members/*.md`, tag `phase-4` & GitHub Release `v1.0.0`.

## [1.2.0] - Phase 3 (TICKET-03) — Mùa Nước Nổi: Độ tươi & Kho cá thể

### Breaking Changes (Từ v1.1 lên v1.2)
1. **Schema file kho (`--inventory` / `--inventory-out`) & `gather_end.data.inventory`**:
   - **Trước (v1.0/v1.1):** `{"items": {"ca_loc": 1, "bong_sung": 2}}` (map đếm theo loại).
   - **Nay (v1.2):** `{"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}, ...]}` (mảng cá thể sắp theo `id_key`). File kho đếm kiểu cũ bị từ chối với mã thoát `2`.
2. **Giỏ hàng (`gather.hold[]`) & Kho quán (`quan.stock[]`, `shop.stock[]`)**:
   - Đổi từ mảng chuỗi / map đếm sang mảng cá thể `{"id", "kind", "fresh"}` với `fresh ∈ [0, 100]`.
   - ID cá thể `I1, I2, ...` tăng liên tục xuyên pha và xuyên Ngày trong `--mode day`.
3. **Giữ chỗ (`customers[].reserved`) & Sự kiện (`cook_started`, `monster_hit`, `faint`, `spoiled`)**:
   - `customers[].reserved` đổi từ map `{kind: qty}` sang mảng ID cá thể `["I1", ...]`.
   - `cook_started.data.items` đổi sang mảng cá thể sắp theo `(kind, id_key(id))`.
   - `monster_hit.data.lost` và `faint.data.lost` đổi sang mảng cá thể theo thứ tự LIFO.
   - Thêm sự kiện `spoiled` (`{"item_id", "kind", "location": "hold" | "stock"}`) khi độ tươi giảm từ `>= 30` xuống `< 30`.
4. **Quy tắc hao tươi & Chốt giá**:
   - Biểu diễn nội bộ bằng số nguyên `FRESH_SCALE = 240` (`100` = `24000`, ngưỡng `30` = `7200`).
   - `gather`: hao `0.5/s` (`-2` units/tick) ở đầu bước cho hàng đã có trong `hold`; hàng mới bắt/hái mang `fresh = 100` và bắt đầu hao từ bước kế tiếp.
   - `quan`: hao `0.25/s` (`-1` unit/tick) cho toàn bộ `stock` (gồm hàng đang giữ chỗ); `ShopSim` không hao tươi.
   - Nếu hàng đang giữ chỗ bị ươn (`< 30`), sau khi phát hết `spoiled`, đơn bị ảnh hưởng nhả toàn bộ `reserved` và thử giữ lại 1 lần theo `(order_tick, id_key(table_id))` (tươi nhất trước, hòa `id_key`); thiếu hàng → `unfulfillable`.
   - `base_price = floor(list_price * avg_fresh / 100)` chốt lúc `cook_started`; `tip = floor(base_price * tip_rate)` tính trên `base_price` đã chốt.

### Hướng dẫn cập nhật fixture từ v1.1 sang v1.2
- File kho: đổi `{"items": {"ca_loc": 1}}` thành `{"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]}`.
- `scenario.gather.hold`: đổi `["ca_loc"]` thành `[{"id": "I1", "kind": "ca_loc", "fresh": 100}]`.
- `scenario.quan.stock`: đổi `{"ca_loc": 1}` thành `[{"id": "I1", "kind": "ca_loc", "fresh": 100}]`.
- `scenario.quan.customers[].reserved`: đổi `{"ca_loc": 1}` thành `["I1"]`.

## [1.1.0] - Phase 2 (TICKET-02) — Một ngày ở chợ nổi
- **Nâng cấp Test Contract `v1.1`:** Mở rộng 6 nguyên liệu (`+ca_keo`, `+keo_neo`), `N5`/`N6`, 8 đàn cá bơi/đổi hướng mỗi 120 ticks/sinh cá mỗi 360 ticks (`fish_max: 12`), ngạt bước chạm `0` (`choke`).
- **Cá Sấu Năm Chèo (`chonoi/sim/monsters.py`):** `M1` (ngày 1+) và `M2` (ngày 3+), `patrol`/`chase`/`recoil` 60 bước, rơi `floor(len(hold)/2)` LIFO, bất tử `90` ticks, `faint(cause="monster")`.
- **Quán mở rộng (`chonoi/sim/quan.py`):** 2 bếp (`B1`, `B2`), 4 bàn (`T1`–`T4`), 6 món ăn, lọc món theo `day_plan` trong `--mode day`.
- **Vòng Ngày, Shop & Pause (`chonoi/sim/day.py`, `chonoi/sim/shop.py`, `chonoi/runner.py`):** `--mode day --days 1..5`, nâng cấp `oxygen`/`hp` L1–L2, `pause`/`resumed` trên cả 3 mode, giao diện Menu/Intro/Shop/HUD v1.1 (`>= 18px`).

## [1.0.0-p1] - Phase 1 (PRD-0) — Lõi mô phỏng `gather` & `quan`
- **Buổi sáng (`gather`):** Bơi 60 Hz, oxy trừ/hồi, ngạt & ngất, giỏ LIFO (`hold_capacity: 12`), hái nút mặt nước, bắt cá dưới nước, cập bến & xuất file kho nguyên tử.
- **Buổi tối (`quan`):** Đón khách theo lịch, giữ chỗ nguyên liệu, kiên nhẫn (`customer_left`), bếp nấu/bưng/phục vụ ưu tiên `(khoảng cách, bếp < bàn, id_key)`, thanh toán/boa/uy tín & kết ca `quan_end`.
