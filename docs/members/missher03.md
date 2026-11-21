# missher03 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm:**
  - **Phase 1 (Slice 2):** Hái nút mặt nước, bắt cá dưới nước, cooldown và xuất kho (`7e44ed4`, `e964572`, `eab97c9`).
  - **Phase 2 (Slice 2):** `chonoi/sim/monsters.py` (Cá Sấu Năm Chèo `M1`/`M2`, `patrol`/`chase`/`recoil`, rơi LIFO `floor(hold/2)`, `faint(cause="monster")`) và validate `gather.monsters[]` (`c6743fc`, `b1a6040`, `923a425`).
  - **Phase 3 (Slice 2):** Nâng `monsters.py` trả cá thể LIFO sạch, `day.py` giữ `item_ids` liên tục xuyên 5 Ngày (`9a28e61`, `017cc49`, `e99ad3c`).
  - **Phase 4 (Slice 2):** 3 cảnh báo chữ + biểu tượng, chế độ tương phản cao trên `chonoi/web/index.html`, điều phối `docs/retro.md` và giữ `docs/clarify.md` (PO).
- **Tôi đã review:** PR Slice 1 (`duyhale95`) và kiểm chéo tích hợp `gather` + `day` qua các phase.
- **AI sai ở đâu và tôi phát hiện thế nào:** Ở Phase 1 AI gọi sai chữ ký `InputState(interact_edge=True)`; ở Phase 2 đặt tọa độ test `chase` cách `~12.04 m > 10 m`. Cả hai đều bị bắt ngay nhờ viết test trước (`unittest`).
- **Điều tôi học được:** Khóa hợp đồng dữ liệu và `docs/clarify.md` sớm giúp 4 nhánh làm song song ít xung đột, còn Test-First chặn AI bịa giả định hiệu quả.
