# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 09:58 | Payload sự kiện `gather`, `node_regrown`, `hold_full`, `fish_caught`, `gather_end` trong `gather` là gì? | Theo PRD-0 mục E: `gather` = `{"node_id","kind","amount"}`; `node_regrown` = `{"node_id"}`; `hold_full` = `{"action": "gather"\|"catch", "node_id"\|"fish_id", "required", "free"}`; `fish_caught` = `{"fish_id","kind","yield"}`; `gather_end` = `{"reason","inventory"}`. | PO (`missher03`) đối chiếu PRD-0 |
| 2 | 2026-11-21 09:58 | Khi `fish_yield` (hoặc `node_yield`) > chỗ trống còn lại trong `hold`, có bắt một phần hay từ chối cả lượt? | Theo PRD-0 mục F (Gather): đủ chỗ mới thêm toàn bộ `yield`, xóa đàn, phát `fish_caught` và đặt `catch_cooldown_s × 60`. Thiếu chỗ thì phát `hold_full`, giữ đàn và giữ cooldown (không thử đàn khác). | PO (`missher03`) đối chiếu PRD-0 |
| 3 | 2026-11-21 09:58 | Khi nhấn `catch` dưới nước nhưng không có đàn cá trong `catch_radius` thì có đặt cooldown không? | Theo PRD-0 mục F (Gather): không có đàn trong tầm thì không có sự kiện bắt hay hồi chiêu (`catch_cd_ticks` giữ nguyên). | PO (`missher03`) đối chiếu PRD-0 |
| 4 | 2026-11-21 09:58 | Khi đứng trong cả `dock_radius` và `interact_radius` của nút `ready`, nhấn `interact` ưu tiên gì? | Theo PRD-0 mục F (Gather): xét bến trước theo khoảng cách tâm `[x,d]`; trong bến kết thúc ngay `docked` không hái nút. | PO (`missher03`) đối chiếu PRD-0 |
