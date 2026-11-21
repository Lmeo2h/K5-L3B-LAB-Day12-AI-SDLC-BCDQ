# Kế hoạch Phase 2 — Một ngày ở chợ nổi (≤ 1 trang)

- **Mục tiêu:** Nâng cấp hệ thống lên **Test Contract v1.1** theo **TICKET-02** trong **55 phút (`1:00–1:55`)**: hoàn thiện `gather` (cá bơi/sinh cá, choke bước chạm 0, Cá Sấu Năm Chèo `M1`/`M2`), `quan` (2 bếp, 4 bàn, 6 món, lọc `day_plan`), vòng lặp nhiều ngày `--mode day --days 1..5`, `ShopSim`, `pause` cả 3 chế độ, giao diện/HUD v1.1 (`>= 18px` tại `1280x720`, `>= 30 FPS`), **2 skills nhóm**, P1 regression, retro nhanh và gắn tag `phase-2` trước `1:55`.

## Phân chia 4 Vertical Slices (Việc / Người / Phụ thuộc)

| Thành viên (MSSV) | Handle | Vai / Dự phòng | Nhánh & File sở hữu | Phạm vi Vertical Slice |
|---|---|---|---|---|
| Hà Lê Duy (`2A202603851`) | `duyhale95` | Scrum/Release · Dự phòng `missher03` | `feat/p2-s1-contract-fish`<br>`game.contract.json`, `chonoi/{contract,inventory,inputs}.py`, `chonoi/sim/gather.py`, `chonoi/scenario.py` (fish), `tests/test_gather_fish_v11.py` | **Slice 1 (US1):** Đẩy **Contract v1.1 (`T001–T004`)** lên `main` trong 5–8 phút đầu (+ `ca_keo`, `keo_neo`, N5/N6, `pause`/`shop_done`/`buy`); cá bơi/đổi hướng 120t/phản xạ biên, sinh cá 360t (`fish_max: 12`, 40/30/30), choke bước chạm 0. |
| Nguyễn Văn Quốc (`2A202603864`) | `missher03` | PO (`clarify.md`) · Dự phòng `duyhale95` | `feat/p2-s2-crocodiles`<br>`chonoi/sim/monsters.py`, hook trong `gather.py`, `scenario.py` (`monsters[]`), `tests/test_gather_monsters.py`, `docs/clarify.md` | **Slice 2 (US2):** Cá Sấu `M1` (ngày 1+) & `M2` (ngày 3+), `patrol`/`chase`/`recoil` 60 bước, va chạm (`-1` HP, bất tử 90t, rơi `floor(hold/2)` LIFO, `monster_hit`), `faint(cause="monster")`, kiểm `gather.monsters[]`. |
| Nguyễn Thiên Bảo (`2A202603861`) | `Limdim1604` | QA Lead · Dự phòng `Lmeo2h` | `feat/p2-s3-quan-v11-qa`<br>`chonoi/sim/quan.py`, `chonoi/scenario.py` (v1.1), `tests/test_quan_v11.py`, `.agents/skills/` (2 skills), `docs/{verification/phase-2.md,proof/phase-2/}` | **Slice 3 (US3):** 2 bếp (`B1`,`B2`), 4 bàn (`T1`–`T4`), 6 món, lọc thực đơn theo `day_plan` trong `day`, kiểm mâu thuẫn v1.1 (mã thoát `2`), 2 skill nhóm, P1 regression & cổng QA Phase 2. |
| Nguyễn Tấn Châu (`2A202603846`) | `Lmeo2h` | Integrator · Dự phòng `Limdim1604` | `feat/p2-s4-day-shop-ui`<br>`chonoi/sim/{day,shop}.py`, `chonoi/{runner,headless,live}.py`, `chonoi/web/index.html`, `tests/test_day_shop_pause.py`, `docs/retro.md` | **Slice 4 (US4):** `--mode day --days 1..5`, `ShopSim` (`oxygen`/`hp` L1–L2, 600t), `pause` cả 3 chế độ, envelope v1.1, toàn bộ màn hình & HUD v1.1, retro nhanh Phase 2 & gắn tag `phase-2`. |

## Phụ thuộc & Lịch trình 55 phút (`1:00–1:55`)

1. **`1:00–1:08` (Phút 0–8) — Khóa nền Contract v1.1:** `duyhale95` hoàn thành & merge `T001–T004` lên `main`; 3 thành viên còn lại viết skeleton Test-First và chốt điểm mở ở `docs/clarify.md` song song.
2. **`1:08–1:20` (Phút 8–20) — Phát triển song song 4 lát:** Mọi nhánh rebase lên Contract v1.1 và cài đặt theo đúng thứ tự xử lý mục 4.5 (TICKET-02).
3. **`1:20` (Phút 20) — Mốc Smoke Tích hợp:** `Limdim1604` & `Lmeo2h` chạy kiểm tra ghép sớm (`gather + monsters + quan + day`), đối chiếu P1 regression và lưu proof tạm vào `docs/proof/phase-2/`.
4. **`1:20–1:40` (Phút 20–40) — Hoàn thiện lõi, UI/HUD & Skills:** Đủ 4 bộ `tests/test_*.py`, `chonoi/web/index.html` (`>= 18px` tại `1280x720`, `>= 30 FPS`), và 2 skill nhóm tại `.agents/skills/`.
5. **`1:40–1:50` (Phút 40–50) — Merge tuần tự & Đo cổng:** Merge lần lượt **Slice 1 -> Slice 2 -> Slice 3 -> Slice 4** (mỗi PR rebase sạch); đo hiệu năng headless (`22,200` ticks/ngày `<= 20s`), kiểm tất định cùng seed và điền `docs/verification/phase-2.md`.
6. **`1:50–1:55` (Phút 50–55) — Đóng băng, Retro & Tag `phase-2`:** Đóng băng code từ `1:50`, ghi `docs/retro.md` (Phase 2 nhanh), cập nhật `AGENTS.md`/`docs/ai-usage-log.md`, chạy `check_team.py` + `unittest discover`, gắn tag `phase-2` trước `1:55`.

## Rủi ro & Giảm thiểu

- **Xung đột `gather.py` / `scenario.py`:** Tách cá sấu sang `chonoi/sim/monsters.py` (chỉ chèn hook gọn vào `gather.py`), tách vùng validate trong `scenario.py` và giữ đúng thứ tự merge `1 -> 2 -> 3 -> 4`.
- **Choke bước chạm 0 làm lệch timing test P1:** Nếu `tests/test_gather_survival.py` đổi tick ngạt, ghi rõ lý do đổi theo luật TICKET-02 vào commit (không sửa bừa cho xanh).
- **Trễ hiệu năng `<= 20s` cho 22,200 ticks hoặc phình phạm vi UI:** Giữ đồ họa mở rộng tắt hoàn toàn ở `headless`; các tính năng mở rộng ngoài lõi (`Lao xua`, `Vợt hút cá`, `Rắn Hổ Mây`, `Cháy món`, `Chợ Chú Sáu`, `Sổ tay & Cá Hô`, `Settings`) hoãn lại nếu chưa xong DoD lõi. Nghẽn `> 10 phút` -> kích hoạt cặp dự phòng ngay.
