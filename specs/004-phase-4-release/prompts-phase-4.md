# Prompts Phase 4 — Phát hành v1.0.0 (Nhóm BCDQ)

> Tài liệu này chứa **4 prompt hoàn chỉnh (copy-paste trực tiếp cho AI coding agent)** cho **Phase 4 — TICKET-04: Phát hành v1.0.0** (**Test Contract v1.3**, cửa sổ **30 phút: `2:30–3:00`**, hạn đẩy tag **`phase-4`** và công bố **GitHub Release `v1.0.0`** trước **`3:00`**).
>
> **Quy tắc phối hợp nhanh:**
> - **Không chồng lấn file:** Mỗi thành viên sở hữu tập file riêng biệt (xem `docs/plan/phase-4.md`), có thể làm **song song 100%** ngay từ phút 0!
> - **Mỗi người ≥ 3 commit có nội dung** bằng tài khoản GitHub cá nhân, viết `docs/members/<handle>.md` (`<= 200` từ, có dẫn chứng commit/bằng chứng thật), và cập nhật `docs/ai-usage-log.md`.
> - Nhóm 4 người **không bắt buộc** làm phần mở rộng (`leaderboard`, `SFX subtitles`); tập trung hoàn thành 100% DoD lõi trước `2:55` để kịp tag `phase-4` & Release `v1.0.0`.

---

## Prompt 1 — Hà Lê Duy (`duyhale95` · MSSV `2A202603851`)
**Slice 1:** Contract v1.3 + `DaySim` lặp D1–D5 (Ngày 6–10) + `soak_cmd` (`chonoi/soak.py`) · **Nhánh Git:** `feat/p4-s1-contract-soak`

````markdown
Bạn là AI coding agent hỗ trợ **Hà Lê Duy (`duyhale95` — MSSV `2A202603851`)**, vai **Scrum / Release (Nhóm trưởng)** của nhóm **BCDQ** (dự phòng cho `missher03`).

### 1. Nhánh Git & Mục tiêu Slice 1
- Tạo nhánh `feat/p4-s1-contract-soak` từ `main` mới nhất (đã có tag `phase-3`).
- Mục tiêu: Land sớm **Contract v1.3** (`game.contract.json`, `chonoi/contract.py`), sửa chu kỳ `day_plan` lặp D1–D5 ở Ngày 6–10 trong `chonoi/sim/day.py`, xây dựng `chonoi/soak.py` (`soak_cmd`), viết `tests/test_soak_v13.py` và `docs/members/duyhale95.md`.

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md`, `TEAM.md`, `docs/plan/phase-4.md`
2. `specs/004-phase-4-release/spec.md`, `specs/004-phase-4-release/plan.md`, `specs/004-phase-4-release/tasks.md`
3. `game.contract.json`, `chonoi/contract.py`, `chonoi/sim/day.py`, `chonoi/runner.py`, `chonoi/inputs.py`

### 3. Yêu cầu TICKET-04 cho Slice 1
1. **Contract v1.3 (`game.contract.json`, `chonoi/contract.py`):**
   - Đặt `"contract_version": "1.3"`, thêm ở gốc manifest:
     - `"bench_cmd": "python3 -m chonoi.bench"`
     - `"soak_cmd": "python3 -m chonoi.soak"`
   - Giữ nguyên toàn bộ gameplay, tuning, schema kho cá thể và JSONL theo v1.2.
   - `chonoi/contract.py`: hỗ trợ `"1.3"` trong `SUPPORTED_VERSIONS`, kiểm tra `"bench_cmd"` và `"soak_cmd"` là chuỗi khác rỗng khi `contract_version == "1.3"`.
2. **Lặp kế hoạch D1–D5 ở Ngày 6–10 (`chonoi/sim/day.py`):**
   - Trong `DaySim._get_day_plan(day)`: khi `plans` là danh sách 5 ngày và `day > len(plans)`, dùng `plans[(day - 1) % len(plans)]` (Ngày 6→D1, 7→D2, ..., 10→D5) thay cho `min(day - 1, len(plans) - 1)`.
3. **`chonoi/soak.py` (`--seed <int> --days <N> --out <soak.json>`):**
   - Chạy `N` Ngày (`N >= 1`, không giới hạn `1..5` như `headless --mode day`) trong **1 tiến trình** qua `Session("day", tuning, {}, seed, days=days)` bằng bot tất định (di chuyển hướng tới nút/cá, `interact`/`catch`, nấu/phục vụ ở `quan`, mua nâng cấp hoặc `shop_done` ở `shop`).
   - Tại mỗi thời điểm Shop đóng (`days_completed` tăng), ghi lại vào `results[]`: `{"day": d, "earned": sim.earned, "reputation": round(sim.reputation, 3), "score": snap["score"]}`.
   - Kết thúc ghi JSON gồm đúng 5 trường gốc: `{"days": N, "days_completed": ..., "crashes": 0, "results": [...], "duration_s": ...}`.
   - Đảm bảo 2 lần chạy cùng `--seed` cho cùng `days_completed == N`, `crashes == 0`, và mảng `results` giống hệt nhau.
4. **Tests & Phản tư:**
   - Viết `tests/test_soak_v13.py` (kiểm `contract_version == "1.3"`, `bench_cmd`/`soak_cmd`, `DaySim` Ngày 6 lặp D1, `soak --seed 7 --days 10` ra `days_completed=10, crashes=0` và lặp lại giữa 2 lần chạy).
   - Viết `docs/members/duyhale95.md` (`<= 200` từ theo `docs/members/TEMPLATE.md`, dẫn commit thật) và thêm dòng Phase 4 vào `docs/ai-usage-log.md`.

### 4. Phạm vi sở hữu & Kiểm tra
- **Được phép sửa/tạo:** `game.contract.json`, `chonoi/contract.py`, `chonoi/sim/day.py`, `chonoi/soak.py`, `tests/test_soak_v13.py`, `docs/members/duyhale95.md`, `docs/ai-usage-log.md`.
- **Chạy kiểm tra:**
  ```powershell
  $env:PYTHONPATH="tests;."; python -m unittest tests.test_soak_v13 -v
  $env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v
  python -m chonoi.soak --seed 7 --days 10 --out tmp_soak.json
  Remove-Item tmp_soak.json
  ```
- Tạo **≥ 3 commit rõ ràng** bằng `duyhale95`, mở PR #1 vào `main` sớm để các bạn rebase.
````

---

## Prompt 2 — Nguyễn Văn Quốc (`missher03` · MSSV `2A202603864`)
**Slice 2:** 3 Cảnh báo chữ/biểu tượng + Chế độ tương phản cao (`chonoi/web/index.html`) + Điều phối Retro cuối · **Nhánh Git:** `feat/p4-s2-warnings-contrast`

````markdown
Bạn là AI coding agent hỗ trợ **Nguyễn Văn Quốc (`missher03` — MSSV `2A202603864`)**, vai **PO & Điều phối Retro** của nhóm **BCDQ** (dự phòng cho `duyhale95`).

### 1. Nhánh Git & Mục tiêu Slice 2
- Tạo nhánh `feat/p4-s2-warnings-contrast` từ `main` (có tag `phase-3`).
- Mục tiêu: Nâng cấp `chonoi/web/index.html` có đủ **3 cảnh báo dễ nhận biết** (chữ + biểu tượng) và **chế độ tương phản cao**, viết `tests/test_ui_warnings_v13.py`, cập nhật `docs/clarify.md`, hoàn thiện mục `## Phase 4 (cuối)` trong `docs/retro.md` và viết `docs/members/missher03.md`.

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md`, `TEAM.md`, `docs/plan/phase-4.md`, `docs/retro.md`, `docs/clarify.md`, `docs/ai-usage-log.md`
2. `specs/004-phase-4-release/spec.md`, `specs/004-phase-4-release/plan.md`
3. `chonoi/web/index.html`, `tests/test_v12_handoff_ui.py`

### 3. Yêu cầu TICKET-04 cho Slice 2
1. **3 Cảnh báo chữ + biểu tượng & Chế độ tương phản cao (`chonoi/web/index.html`):**
   - **Cảnh báo 1 (Thủy quái gần):** khi có cá sấu `chase` hoặc khoảng cách tới người chơi `<= 10 m` (hoặc `invuln_ticks > 60`), hiển thị rõ biểu tượng + chữ `"⚠ Thủy quái!"` kèm viền cảnh báo.
   - **Cảnh báo 2 (Oxy sắp hết):** khi `oxygen_ticks / oxygen_max_ticks < 0.25` hoặc `oxygen_ticks === 0`, hiển thị biểu tượng + chữ `"⚠ Oxy sắp hết!"` / `"⚠ Hết hơi!"` với màu cảnh báo nổi bật.
   - **Cảnh báo 3 (Khách sắp giận — mới ở Phase 4):** trong `drawQuan`, tính tỷ lệ kiên nhẫn từng khách đang chờ (`patience_ticks_left / (patience_s * 60)`), vẽ thanh kiên nhẫn trên bàn (đổi màu đỏ/vàng khi `< 0.25`) và nếu có ít nhất 1 khách chờ `< 25%` kiên nhẫn thì hiển thị biểu tượng + chữ `"⚠ Khách sắp giận!"` trên HUD quán.
   - **Chế độ tương phản cao (`highContrast`):** thêm nút bật/tắt `"Tương phản cao"` trên Menu/Pause/HUD và phím tắt `C` (hoặc `H`); khi bật, đổi bảng màu nền `#000000`, chữ `#ffffff`, viền & nhãn cảnh báo `#ffff00` / `#ff3b30` / `#00ffff` rõ nét cho cả 3 cảnh báo, vẫn giữ font `sans-serif >= 18px`.
   - Giữ nguyên tốc độ render `>= 30 FPS` ở `1280×720` và hoàn toàn không ảnh hưởng `headless`.
2. **Kiểm thử & Retro cuối:**
   - Viết `tests/test_ui_warnings_v13.py` kiểm tra sự hiện diện và logic tính toán của cả 3 cảnh báo + chế độ tương phản cao trong `chonoi/web/index.html`.
   - Cập nhật `docs/retro.md` mục `## Phase 4 (cuối)`:
     - **Rà lại hành động Phase 2:** nhóm đã làm gì (tóm tắt TICKET/clarify & SpecKit), còn vướng gì và vì sao.
     - **Điều tốt / Điều tệ / Hành động tiếp theo.**
     - **Số liệu đóng góp:** tổng hợp số commit theo người, cách đọc code của nhau, ước tính token từ `docs/ai-usage-log.md`.
     - **Một lần AI sai và cách nhóm phát hiện/xác minh** (dẫn chứng cụ thể từ nhật ký AI của nhóm).
   - Cập nhật `docs/clarify.md`, `docs/ai-usage-log.md`, và viết `docs/members/missher03.md` (`<= 200` từ).

### 4. Phạm vi sở hữu & Kiểm tra
- **Được phép sửa/tạo:** `chonoi/web/index.html`, `tests/test_ui_warnings_v13.py`, `docs/clarify.md`, `docs/retro.md`, `docs/members/missher03.md`, `docs/ai-usage-log.md`.
- Chạy `$env:PYTHONPATH="tests;."; python -m unittest tests.test_ui_warnings_v13 tests.test_live -v`, tạo **≥ 3 commit rõ ràng** bằng `missher03` và mở PR #2 vào `main`.
````

---

## Prompt 3 — Nguyễn Thiên Bảo (`Limdim1604` · MSSV `2A202603861`)
**Slice 3:** `bench_cmd` (`chonoi/bench.py`) + Hồ sơ QA Phase 4 (`bench.json`, `soak.json`, `docs/verification/phase-4.md`) · **Nhánh Git:** `feat/p4-s3-bench-qa`

````markdown
Bạn là AI coding agent hỗ trợ **Nguyễn Thiên Bảo (`Limdim1604` — MSSV `2A202603861`)**, vai **Bench / QA Lead** của nhóm **BCDQ** (dự phòng cho `Lmeo2h`).

### 1. Nhánh Git & Mục tiêu Slice 3
- Tạo nhánh `feat/p4-s3-bench-qa` từ `main` (có tag `phase-3`).
- Mục tiêu: Xây dựng `chonoi/bench.py` (`bench_cmd`), viết `tests/test_bench_v13.py`, chạy đo benchmark thật (`--seed 42 --duration 30`), chạy soak (`--seed 7 --days 10` sau khi Slice 1 merge), chạy regression P1–P4, lưu artifact tại `docs/proof/phase-4/`, điền `docs/verification/phase-4.md` và viết `docs/members/Limdim1604.md`.

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md`, `TEAM.md`, `docs/plan/phase-4.md`, `docs/verification/phase-4.md`
2. `specs/004-phase-4-release/spec.md`, `specs/004-phase-4-release/plan.md`
3. `chonoi/live.py`, `chonoi/web/index.html`, `chonoi/runner.py`, `chonoi/sim/gather.py`, `game.contract.json`

### 3. Yêu cầu TICKET-04 cho Slice 3
1. **`chonoi/bench.py` (`--seed <int> --duration <float> --out <bench.json>`):**
   - Khởi chạy cảnh lặn buổi sáng mặc định (độ tươi, cá bơi, Cá Sấu Năm Chèo, Út Sen đứng yên tại bến `[2, 0]`, `--seed 42`, cửa sổ `1280×720`).
   - Làm nóng `3 s` (`warmup = 3.0`), sau đó đo `duration` giây (mặc định `30.0`).
   - Hỗ trợ render thật bằng headless Chromium/Chrome/Edge mở `LiveServer` (`chonoi/web/index.html` ở `1280×720`) đo `requestAnimationFrame` nếu máy có trình duyệt, **VÀ** có fallback render Python (`tkinter` 1280×720 hoặc software frame loop vẽ trạng thái `GatherSim`) khi chạy trong môi trường không có trình duyệt/màn hình để lệnh `<bench_cmd>` luôn chạy thành công 100% từ repo sạch.
   - Tính chính xác 5 trường JSON:
     - `frames`: tổng số khung hình đo được sau làm nóng.
     - `measured_s`: thời gian đo thực tế (giây).
     - `avg_fps`: `frames / measured_s`.
     - `p1_low_fps`: chọn `k = max(1, math.ceil(0.01 * frames))` khoảng thời gian khung hình chậm nhất, lấy `1.0 / (sum(slowest_k) / k)`.
     - `load_ms`: mili giây từ lúc khởi chạy tới khung hình đầu tiên của cảnh đo.
2. **Tests & Bằng chứng QA (`docs/proof/phase-4/`, `docs/verification/phase-4.md`):**
   - Viết `tests/test_bench_v13.py` kiểm tra công thức tính `p1_low_fps`/`avg_fps`, CLI `python -m chonoi.bench --seed 42 --duration 1 --out ...` xuất đủ 5 khóa hợp lệ và tạo file nguyên tử.
   - Sau khi các slice hợp nhất, chạy và lưu kết quả thật:
     - `python -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json`
     - `python -m chonoi.soak --seed 7 --days 10 --out docs/proof/phase-4/soak.json`
     - Log regression `unittest discover -s tests -v` và `check_team.py` vào `docs/proof/phase-4/qa-summary.md`, cập nhật `docs/verification/phase-4.md`.
   - Viết `docs/members/Limdim1604.md` (`<= 200` từ) và cập nhật `docs/ai-usage-log.md`.

### 4. Phạm vi sở hữu & Kiểm tra
- **Được phép sửa/tạo:** `chonoi/bench.py`, `tests/test_bench_v13.py`, `docs/proof/phase-4/*`, `docs/verification/phase-4.md`, `docs/members/Limdim1604.md`, `docs/ai-usage-log.md`.
- Tạo **≥ 3 commit rõ ràng** bằng `Limdim1604` và mở PR #3 vào `main`.
````

---

## Prompt 4 — Nguyễn Tấn Châu (`Lmeo2h` · MSSV `2A202603846`)
**Slice 4:** Đóng gói clone sạch ≤ 3 lệnh, `README.md`, `LICENSE`, `CREDITS.md`, `CHANGELOG.md`, Tag `phase-4` & GitHub Release `v1.0.0` · **Nhánh Git:** `feat/p4-s4-package-release`

````markdown
Bạn là AI coding agent hỗ trợ **Nguyễn Tấn Châu (`Lmeo2h` — MSSV `2A202603846`)**, vai **Đóng gói & Release / Integrator** của nhóm **BCDQ** (dự phòng cho `Limdim1604`).

### 1. Nhánh Git & Mục tiêu Slice 4
- Tạo nhánh `feat/p4-s4-package-release` từ `main` (có tag `phase-3`).
- Mục tiêu: Hoàn thiện toàn bộ hồ sơ phát hành (`README.md` chạy clone sạch `<= 3` lệnh, `LICENSE`, `CREDITS.md`, `CHANGELOG.md` đủ 4 phase, `AGENTS.md`), viết `tools/package_release.py` tạo gói chạy được, kiểm thử clone sạch, ghi `docs/members/Lmeo2h.md`, gắn tag **`phase-4`** và công bố **GitHub Release `v1.0.0`** từ cùng commit trên `main` trước **`3:00`**.

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md`, `TEAM.md`, `README.md`, `CHANGELOG.md`, `CREDITS.md`, `docs/plan/phase-4.md`
2. `specs/004-phase-4-release/spec.md`, `specs/004-phase-4-release/plan.md`
3. `game.contract.json` (bản v1.3), `docs/verification/phase-4.md`

### 3. Yêu cầu TICKET-04 cho Slice 4
1. **`README.md` (chạy bản có giao diện từ clone sạch ≤ 3 lệnh trên macOS/Linux):**
   - Mở đầu bằng hướng dẫn chạy nhanh 3 lệnh từ clone sạch:
     ```bash
     git clone https://github.com/Lmeo2h/K5-L3B-LAB-Day12-AI-SDLC-BCDQ.git
     cd K5-L3B-LAB-Day12-AI-SDLC-BCDQ
     python3 -m chonoi.live --mode day --days 5
     ```
   - Ghi rõ yêu cầu môi trường (Python 3.10+, chỉ thư viện chuẩn), phím điều khiển (`WASD`/mũi tên, `E`, `Space`, `Esc`/`P`, `C`/`H` tương phản cao, `R`), lệnh `test`, lệnh `headless`, lệnh `bench_cmd`, lệnh `soak_cmd`, và giới hạn đã biết.
2. **`LICENSE`, `CREDITS.md`, `CHANGELOG.md` & `AGENTS.md`:**
   - Thêm file `LICENSE` (MIT License).
   - Rà và cập nhật `CREDITS.md` (ghi rõ đồ họa Canvas 2D thuần tự vẽ 100%, không dùng asset bên thứ 3 dính bản quyền, cùng công cụ AI sử dụng).
   - Cập nhật `CHANGELOG.md` có đầy đủ mục theo từng phase: `[1.3.0 / v1.0.0] - Phase 4`, `[1.2.0] - Phase 3`, `[1.1.0] - Phase 2`, `[1.0.0-p1] - Phase 1`.
   - Cập nhật `AGENTS.md` với Test Contract `v1.3`, lệnh `bench` và `soak`.
3. **Đóng gói, Kiểm tra Clone sạch, Tag `phase-4` & Release `v1.0.0`:**
   - Tạo `tools/package_release.py` (dùng `zipfile` / `tarfile` chuẩn Python, đóng gói sạch mã nguồn + `game.contract.json` + `README.md` + `LICENSE` + `CHANGELOG.md` thành `chonoi-v1.0.0.zip` — không commit file `.zip` nặng vào git nếu không cần, chỉ đính kèm vào GitHub Release `v1.0.0`).
   - Viết `docs/members/Lmeo2h.md` (`<= 200` từ) và cập nhật `docs/ai-usage-log.md`.
   - Sau khi cả 4 PR merge vào `main` và `unittest discover` + `check_team.py` + `bench` + `soak` + `docs/verification/phase-4.md` hoàn tất:
     - Tạo tag `phase-4` và `v1.0.0` (hoặc tạo GitHub Release `v1.0.0` từ tag `v1.0.0` trỏ cùng commit `phase-4` trên `main`!).
     - Đính kèm gói `chonoi-v1.0.0.zip` vào `gh release create v1.0.0 ...` kèm release notes đầy đủ (điểm mới, cách chạy, giới hạn đã biết).

### 4. Phạm vi sở hữu & Kiểm tra
- **Được phép sửa/tạo:** `README.md`, `LICENSE`, `CREDITS.md`, `CHANGELOG.md`, `AGENTS.md`, `tools/package_release.py`, `docs/members/Lmeo2h.md`, `docs/ai-usage-log.md`.
- Tạo **≥ 3 commit rõ ràng** bằng `Lmeo2h`, mở PR #4 vào `main`, hoàn tất tag `phase-4` và GitHub Release `v1.0.0` trước **`3:00`**.
````
