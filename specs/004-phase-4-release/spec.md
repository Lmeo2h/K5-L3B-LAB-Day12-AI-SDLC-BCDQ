# Feature Specification: Quán Ăn Chợ Nổi — Phase 4: Phát hành v1.0.0 (TICKET-04)

**Feature Branch**: `004-phase-4-release`

**Created**: 2026-11-21

**Status**: Draft

**Milestone / Contract**: Phase 4 (TICKET-04, Test Contract `v1.3`, cửa sổ 30 phút `2:30–3:00`, tag `phase-4` & GitHub Release `v1.0.0` trước `3:00`)

**Input**: TICKET-04 — "Phát hành v1.0.0": nâng cấp `contract_version: "1.3"` với `bench_cmd` và `soak_cmd` (giữ nguyên gameplay/tuning/kho/JSONL v1.2), công cụ benchmark cảnh lặn có render `1280×720` (`3s` warmup + `30s` measure → `bench.json`), công cụ soak headless 10 Ngày lặp kế hoạch D1–D5 ở Ngày 6–10 (`soak.json`), 3 cảnh báo chữ/biểu tượng kèm chế độ tương phản cao, đóng gói chạy được từ clone sạch trong `<= 3` lệnh, `README.md`/`LICENSE`/`CREDITS.md`/`CHANGELOG.md`, retro cuối + 4 phản tư cá nhân `docs/members/<handle>.md`, tag `phase-4` và GitHub Release `v1.0.0`.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Contract v1.3, Chu kỳ D1–D5 cho Ngày 6–10 & Soak Headless (`duyhale95` — Hà Lê Duy, dự phòng `missher03`) (Priority: P1)

Hệ thống nâng cấp `game.contract.json` lên `contract_version: "1.3"`, khai báo `bench_cmd` và `soak_cmd` ở gốc manifest, đồng thời cung cấp lệnh soak headless `<soak_cmd> --seed <int> --days <N> --out <soak.json>` chạy liên tục `N` Ngày (ví dụ `10` Ngày với `--seed 7`) trong một tiến trình bằng bot tất định. Kế hoạch ngày D1–D5 được lặp lại ở Ngày 6–10; tiền, tổng thu (`earned`), uy tín, cấp nâng cấp, số Ngày và ID cá thể (`I1, I2, ...`) tiếp tục xuyên suốt không reset hay crash.

**Independent Test**: `python -m chonoi.soak --seed 7 --days 10 --out soak.json` chạy 2 lần liên tiếp cho cùng `days_completed == 10`, `crashes == 0`, và mảng `results[]` (`day`, `earned`, `reputation`, `score` tại lúc đóng Shop mỗi ngày) giống hệt nhau giữa 2 lần chạy.

---

### User Story 2 - 3 Cảnh báo Trực quan, Chế độ Tương phản Cao & Retro Tổng kết (`missher03` — Nguyễn Văn Quốc, dự phòng `duyhale95`) (Priority: P1)

Trên giao diện chơi trực tiếp (`chonoi/web/index.html`), người chơi nhận biết tức thì bằng chữ và biểu tượng cho cả 3 cảnh báo quan trọng: (1) **Thủy quái gần**, (2) **Oxy sắp hết / Hết hơi**, và (3) **Khách sắp giận** (kiên nhẫn `< 25%` ở buổi tối). Đồng thời có **chế độ tương phản cao** bật/tắt được ngay trên giao diện/bàn phím để kiểm thử rõ cả 3 cảnh báo. Kết hợp điều phối tổng kết nhóm (`docs/retro.md` rà lại hành động P2, `docs/clarify.md`, `docs/members/missher03.md`).

**Independent Test**: Kiểm tra DOM/Canvas trong `chonoi/web/index.html` có đủ 3 cảnh báo (chữ + biểu tượng) và nút/phím chuyển chế độ tương phản cao; chạy test `tests/test_ui_warnings_v13.py` + kiểm thử trực tiếp trên `chonoi.live`.

---

### User Story 3 - Benchmark Render 1280×720 (`bench_cmd`) & Hồ sơ QA Phase 4 (`Limdim1604` — Nguyễn Thiên Bảo, dự phòng `Lmeo2h`) (Priority: P1)

Lệnh `<bench_cmd> --seed 42 --duration 30 --out bench.json` khởi chạy cảnh lặn buổi sáng lõi ở độ phân giải `1280×720` (độ tươi, cá bơi, Cá Sấu Năm Chèo, hiệu ứng mặc định, Út Sen đứng yên ở bến), làm nóng `3s` rồi đo `30s`, xuất file `bench.json` gồm 5 trường (`avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`) đúng công thức. Lưu bằng chứng `bench.json`, `soak.json` và ma trận `docs/verification/phase-4.md` khớp commit bàn giao.

**Independent Test**: Chạy `python -m chonoi.bench --seed 42 --duration 3 --out tmp_bench.json` (và `duration=30` cho artifact chính thức) kiểm tra JSON đầu ra hợp lệ đủ 5 trường, `p1_low_fps <= avg_fps`, `load_ms >= 0`, `frames > 0`.

---

### User Story 4 - Clone Sạch ≤ 3 Lệnh, Đóng gói, Tag `phase-4` & GitHub Release `v1.0.0` (`Lmeo2h` — Nguyễn Tấn Châu, dự phòng `Limdim1604`) (Priority: P1)

Từ một bản clone sạch của repository, người dùng/giảng viên có thể chạy được bản có giao diện theo `README.md` trong tối đa 3 lệnh trên macOS hoặc Linux. `README.md`, `LICENSE`, `CREDITS.md`, `CHANGELOG.md`, `AGENTS.md`, đủ 4 file `docs/members/*.md` được hoàn tất; bản đóng gói chạy được được đính kèm vào **GitHub Release `v1.0.0`** cùng release notes tại tag **`phase-4`** trên `main` trước `3:00`.

**Independent Test**: Clone sạch vào thư mục tạm, chạy đúng các lệnh trong `README.md` (`<= 3` lệnh), kiểm tra bản đóng gói + kiểm tra `gh release view v1.0.0` và `git tag`.

---

## Requirements & Success Criteria

- **FR-001 (Contract v1.3)**: `game.contract.json` mang `"contract_version": "1.3"`, khai `"bench_cmd"` và `"soak_cmd"` ở gốc; `chonoi/contract.py` kiểm định hai lệnh này khi `contract_version == "1.3"`. Gameplay, tuning, kho cá thể và JSONL giữ nguyên chuẩn v1.2.
- **FR-002 (`bench_cmd`)**: `chonoi/bench.py` nhận `--seed`, `--duration`, `--out`; chạy cảnh lặn mặc định `1280×720`, làm nóng `3s`, đo `duration`s, xuất đúng 5 khóa `{avg_fps, p1_low_fps, frames, measured_s, load_ms}` với `p1_low_fps = 1 / mean(slowest max(1, ceil(0.01 * frames)) frames)`.
- **FR-003 (`soak_cmd` & D1–D5 Loop)**: `DaySim` lặp kế hoạch `day_plan[(day - 1) % len(plans)]` cho Ngày `>= 6`; `chonoi/soak.py` nhận `--seed`, `--days`, `--out`, chạy bot tất định `N` ngày liên tiếp và xuất `{days, days_completed, crashes, results, duration_s}`.
- **FR-004 (Warnings & High Contrast)**: `chonoi/web/index.html` có đủ 3 cảnh báo (Thủy quái gần, Oxy thấp/Hết hơi, Khách sắp giận `< 25%`) kèm biểu tượng + chữ và chế độ tương phản cao bật/tắt được.
- **FR-005 (Packaging & Release)**: `README.md` (≤ 3 lệnh chạy từ clone sạch), `LICENSE`, `CREDITS.md`, `CHANGELOG.md` (từng phase), `docs/retro.md` (rà hành động P2), `docs/members/<handle>.md` (đủ 4 thành viên ≤ 200 từ/người), `docs/verification/phase-4.md`, `docs/proof/phase-4/`, tag `phase-4` và GitHub Release `v1.0.0` trước `3:00`.
- **SC-001**: Toàn bộ `unittest discover -s tests -v` + `python tools/check_team.py` xanh 100%; `soak --seed 7 --days 10` cho `days_completed == 10, crashes == 0` và lặp lại giữa 2 lần chạy; `bench --seed 42 --duration 30` xuất `bench.json` đúng schema.
