# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| US3.1 — Khách đến đúng lịch, nhận bàn trống và giữ đúng công thức | Headless và `Session`: kiểm tick đến, bàn theo ID, kho khả dụng, ID nối tiếp và JSONL giống từng byte cùng seed | [Test Slice 3 và JSONL](../proof/phase-1/slice-3.md) | Đạt |
| US3.2 — Bàn trống nhưng thiếu món thì báo `no_dish` | Headless: kiểm payload `{}`, bỏ lượt khi kín bàn hoặc hết ca | [Test Slice 3 và JSONL](../proof/phase-1/slice-3.md) | Đạt |
| US3.3 — Khách hết kiên nhẫn nhả bàn, nhả giữ chỗ và giảm uy tín | Headless: kiểm tick rời, kẹp uy tín, dọn món trên bếp/tay và không hoàn nguyên liệu đã dùng | [Test Slice 3](../proof/phase-1/slice-3.md) | Đạt |
| US3.4 — Fixture mâu thuẫn bị từ chối trước khi ghi output | Headless: 11 fixture gồm quá tồn kho, món/đơn không khớp, khách đang ăn thiếu dữ liệu và trạng thái bếp sai | [Test Slice 3](../proof/phase-1/slice-3.md) | Đạt |
| PRD-0 mục G — Hai tiến trình chuyển kho | `test_inv_01_gather_writes_inventory_quan_reads_it` trong suite | [Suite hiện có](../proof/phase-1/slice-3.md) | Đạt với fixture smoke |

## Đánh giá ngắn

- Các kết quả trên chạy ở nhánh Slice 3. Cần bổ sung bằng chứng các lát còn lại trên commit `main` được gắn tag `phase-1`.
- Sau khi tích hợp Slice 4, kiểm tra phục vụ đúng tick kiên nhẫn về 0 và xử lý khách khi đóng ca bằng luồng chơi hoàn chỉnh.
