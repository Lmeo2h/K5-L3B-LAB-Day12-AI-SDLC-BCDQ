# Changelog

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

## Unreleased
- Phase 1 & Phase 2 core (`gather`, `quan`, `day`, `shop`, `pause`).
