# Kế hoạch Phase 1 — Quán Ăn Chợ Nổi (≤ 1 trang)

- **Mục tiêu:** Hoàn thiện lõi mô phỏng tất định 60 Hz (`tick_hz: 60`) cho hai chế độ `gather` (`chonoi/sim/gather.py`) và `quan` (`chonoi/sim/quan.py`) cùng kiểm mâu thuẫn mức luật (`chonoi/scenario.py`), giữ nguyên khung `chonoi/` và `game.contract.json`; vượt qua toàn bộ smoke/unit/headless tests và gắn tag `phase-1` đúng hạn (trước mốc 1:00).

## Phân chia 4 Vertical Slices (Việc / Người / Phụ thuộc)

| Thành viên (MSSV) | Handle | Vai | Dự phòng | Nhánh & File sở hữu | Phạm vi Vertical Slice & Kiểm thử |
|---|---|---|---|---|---|
| Hà Lê Duy (`2A202603851`) | `duyhale95` | Scrum / Release (Nhóm trưởng) | `missher03` | `feat/p1-s1-gather-survival`<br>`chonoi/sim/gather.py` (lát 1)<br>`tests/test_gather_survival.py` | **Slice 1 (US1):** Oxy (trừ/hồi), `dive`/`surface`/`oxygen_empty`, đếm ngạt `zero_oxy_ticks` -> `choke` (-1 HP), `faint` (rỗng giỏ, `gather_end` `"fainted"`), giỏ LIFO (`hold_capacity`). |
| Nguyễn Văn Quốc (`2A202603864`) | `missher03` | PO (`clarify.md`) | `duyhale95` | `feat/p1-s2-gather-harvest`<br>`chonoi/sim/gather.py` (lát 2)<br>`tests/test_gather_harvest.py` | **Slice 2 (US2):** Hái nút mặt nước (`gather`, `hold_full`, `regrow_s`/`node_regrown`), bắt cá dưới nước bằng `catch` (`fish_caught`, `hold_full`, `catch_cooldown_s`), cập bến ưu tiên trước hái & xuất kho. |
| Nguyễn Thiên Bảo (`2A202603861`) | `Limdim1604` | QA Lead | `Lmeo2h` | `feat/p1-s3-quan-customers`<br>`chonoi/sim/quan.py` (lát 3), `chonoi/scenario.py`, `tests/test_quan_customers.py`, `docs/verification/phase-1.md` | **Slice 3 (US3):** Khách đến theo lịch (`first_customer_tick`, `customer_interval_s`), chọn món nấu được từ kho dư, giữ chỗ `reserved`, `no_dish`, giảm kiên nhẫn -> `customer_left` + `left_reputation_delta`; kiểm mâu thuẫn scenario; ma trận QA Phase 1. |
| Nguyễn Tấn Châu (`2A202603846`) | `Lmeo2h` | Integrator | `Limdim1604` | `feat/p1-s4-quan-service`<br>`chonoi/sim/quan.py` (lát 4)<br>`tests/test_quan_service.py` | **Slice 4 (US4):** `interact` bếp/bàn (ưu tiên khoảng cách -> bếp trước bàn -> `id`), `cook_started`, `dish_ready`, `dish_picked`, `served`, ăn -> `paid` + boa (`tip_min_patience_ratio`, `tip_rate`) + `tip_reputation`, `quan_end`; tích hợp & tag `phase-1`. |

### Phụ thuộc & Thứ tự tích hợp
1. **Khởi động chung (10 phút đầu):** Chốt `TEAM.md` (`check_team.py` xanh), `docs/contracts/`, và ghi điểm chưa rõ của PRD-0 vào `docs/clarify.md` để PO (`missher03`) quyết định.
2. **Song song `gather` & `quan`:** Cặp `gather` (Slice 1 & 2) chạy độc lập với cặp `quan` (Slice 3 & 4); mỗi slice có file test riêng (`tests/test_*.py`).
3. **Tránh xung đột cùng file:**
   - Trong `chonoi/sim/gather.py`: Slice 1 viết helper sinh tồn + giỏ LIFO (bước 2 của `step`) và **merge trước**; Slice 2 viết helper hái/bắt cá (bước 3–4 của `step`), **rebase lên `main`** rồi mở PR.
   - Trong `chonoi/sim/quan.py`: Slice 3 chốt cấu trúc khách/`reserved` + `chonoi/scenario.py` và **merge trước**; Slice 4 **rebase lên `main`** để gắn logic bếp, phục vụ, tính tiền/uy tín.
4. **Cổng trước tag `phase-1`:** `python tools/check_team.py`, `PYTHONPATH=tests:. python -m unittest discover -s tests -v` (mọi test xanh), kiểm tra chuỗi `gather --inventory-out` -> `quan --inventory`, cập nhật `docs/verification/phase-1.md` và `docs/ai-usage-log.md`.

## Rủi ro & Giảm thiểu
- **Xung đột merge ở `gather.py` / `quan.py`:** Chia helper tách biệt theo lát cắt, test tách 4 file riêng, bắt buộc Slice 1 -> Slice 2 và Slice 3 -> Slice 4 theo thứ tự rebase.
- **Mơ hồ công thức PRD-0 (vd: ưu tiên bắt cá, boa/uy tín chi tiết):** Không tự suy đoán; ghi ngay vào `docs/clarify.md`, áp dụng quy tắc 2 phút bất đồng -> Integrator chốt (`TEAM.md`).
- **Mất tính tất định hoặc hard-code số liệu:** Mọi thông số đọc từ `game.contract.json`, mọi RNG qua `chonoi.rng.Streams`, mọi danh sách sắp bằng `ids.sort_by_id`; kiểm chứng bằng chạy lặp cùng seed so sánh byte JSONL.
- **Nghẽn >10 phút / trễ hạn tag `phase-1`:** Người dự phòng vào thay theo bảng trên; trước hạn 1:00 đóng băng tính năng, ưu tiên `main` chạy ổn định để gắn tag `phase-1`.
