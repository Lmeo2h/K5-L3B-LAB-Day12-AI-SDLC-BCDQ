# Prompts Phase 1 — Vertical Slices (Nhóm BCDQ)

> Tài liệu này chứa **4 prompt hoàn chỉnh (copy-paste trực tiếp cho AI coding agent)** tương ứng với 4 Vertical Slice của Phase 1 (**Quán Ăn Chợ Nổi**, mốc gắn tag `phase-1` trước `1:00`).
>
> **Quy tắc chung trước khi chạy prompt:**
> - Mở **PRD-0** trên lab board (`https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg`) để đối chiếu các công thức/sự kiện chi tiết chưa ghi đầy đủ trong khung code.
> - Tuân thủ nghiêm ngặt `AGENTS.md` và `TEAM.md`: mỗi thành viên làm trên nhánh riêng, ≥ 3 commit có nội dung từ tài khoản GitHub cá nhân, PR ≤ ~400 dòng theo `.github/pull_request_template.md`, và ghi nhật ký AI vào `docs/ai-usage-log.md`.
> - **Phối hợp tránh xung đột file dùng chung:**
>   - `chonoi/sim/gather.py`: Slice 1 (`duyhale95`) và Slice 2 (`missher03`) cùng sửa file này -> tách helper method riêng biệt; người merge sau rebase lên `main` và giải quyết xung đột theo phạm vi từng lát.
>   - `chonoi/sim/quan.py`: Slice 3 (`Limdim1604`) và Slice 4 (`Lmeo2h`) cùng sửa file này -> tách helper method riêng biệt; người merge sau rebase lên `main` và kiểm tra tích hợp cùng Integrator.

---

## Prompt 1 — Hà Lê Duy (`duyhale95` · MSSV `2A202603851`)
**Slice 1:** `gather` Sinh tồn dưới nước & Giỏ LIFO · **Vai:** Scrum / Release (Nhóm trưởng), dự phòng cho `missher03` · **Nhánh Git:** `feat/p1-s1-gather-survival`

````markdown
Bạn là AI coding agent hỗ trợ **Hà Lê Duy (`duyhale95` — MSSV `2A202603851`)**, vai **Scrum / Release (Nhóm trưởng)** của nhóm **BCDQ** (dự phòng cho `missher03`).

### 1. Nhánh Git & Mục tiêu Slice 1
- Làm việc trên nhánh: `feat/p1-s1-gather-survival` (tạo từ `main` mới nhất).
- Mục tiêu: Hoàn thiện **Slice 1 (`gather` — Sinh tồn dưới nước & Giỏ LIFO)** trong `chonoi/sim/gather.py` (`TODO(nhóm, lát 1)`) và viết unit/headless tests trong `tests/test_gather_survival.py`.

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md` và `TEAM.md`
2. `specs/001-phase-1-core/spec.md`, `specs/001-phase-1-core/plan.md`, `specs/001-phase-1-core/tasks.md`
3. `game.contract.json` (khối `tuning.gather`: `surface_depth`, `oxygen_max_s`, `oxygen_refill_per_tick`, `choke_interval_ticks`, `hp_max`, `hold_capacity`)
4. `docs/contracts/README.md` và `docs/contracts/inventory.sample.json`
5. `chonoi/sim/gather.py`, `chonoi/inventory.py`, `chonoi/ids.py`, `chonoi/rng.py`
6. **PRD-0 trên lab board** (`https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg`) — mục 13.8 ("Gather") để đối chiếu chính xác tên `event`, payload `data`, và quy tắc `invuln_ticks` / `hold` LIFO / `faint`.

### 3. Phạm vi sở hữu & File KHÔNG ĐƯỢC SỬA
- **File bạn sở hữu (được phép sửa/tạo):**
  - `chonoi/sim/gather.py` — **CHỈ phần Slice 1 (`TODO(nhóm, lát 1)`)**: tách thành helper riêng (ví dụ `_update_survival(...)`) để không đè vào phần `TODO(nhóm, lát 2)` của `missher03`:
    - So sánh phân vùng đầu bước vs cuối bước (`_at_surface()` dùng `self.pos[1] <= self.t["surface_depth"]`) để phát sự kiện `dive` và `surface` (kèm `data` có `pos` đúng theo PRD-0).
    - Cập nhật `oxygen_ticks` theo `d` CUỐI bước: ở dưới nước (`d > surface_depth`) trừ `1` tick/tick; ở mặt nước cộng `oxygen_refill_per_tick`, kẹp trong `[0, self.oxygen_max]`.
    - Khi `oxygen_ticks` giảm từ dương về `0`: phát sự kiện `oxygen_empty`.
    - Khi `oxygen_ticks == 0` và đang dưới nước: tăng `zero_oxy_ticks`; khi đạt `choke_interval_ticks`, trừ `1` `hp`, phát sự kiện `choke`, cập nhật lại bộ đếm ngạt (và kiểm tra PRD-0 về `invuln_ticks` nếu áp dụng).
    - Khi `hp <= 0`: đặt `hp = 0`, làm rỗng giỏ (`self.hold = []`) để `inventory_items()` trả `{}` (kho rỗng), phát sự kiện `faint`, gọi `self._finish("fainted", events)`, và `return events` ngay.
    - Đảm bảo logic giỏ (`self.hold`) giữ đúng thứ tự nhặt LIFO (phần tử cuối mảng là mới nhất) và tôn trọng `hold_capacity` (viết helper đẩy/lấy giỏ nếu cần, không làm vỡ `hold_to_items`).
  - `tests/test_gather_survival.py` — viết test đầy đủ cho oxy trừ/hồi, `dive`/`surface`, `oxygen_empty`, `choke`, `faint` (mất toàn bộ giỏ & kho rỗng, `gather_end` reason `fainted`), giới hạn `hold_capacity` & thứ tự LIFO.
  - `docs/ai-usage-log.md` (ghi bổ sung dòng nhật ký AI của bạn).
  - `docs/clarify.md` (nếu phát hiện điểm chưa rõ trong PRD-0, ghi câu hỏi để PO `missher03` chốt).
- **File KHÔNG ĐƯỢC SỬA:**
  - Phần `TODO(nhóm, lát 2)` (hái nút, bắt cá) trong `chonoi/sim/gather.py` (của `missher03`).
  - `chonoi/sim/quan.py`, `chonoi/scenario.py`.
  - `game.contract.json`, `docs/contracts/`, `chonoi/{headless,inputs,contract,rng,ids,jsonl,inventory,runner,live}.py`, `chonoi/web/`.
  - `tests/test_smoke_p1.py`, `tests/test_python_starter_units.py`, `tests/test_team_check.py`, và các file test của slice khác.

### 4. Quy tắc bắt buộc từ `AGENTS.md`
- **Không hard-code số liệu** trong luật: mọi ngưỡng (`surface_depth`, `oxygen_max_s`, `oxygen_refill_per_tick`, `choke_interval_ticks`, `hp_max`, `hold_capacity`) phải đọc từ `self.t` (`game.contract.json`).
- **Mọi số ngẫu nhiên** (nếu dùng) phải đi qua `self.rng.get("<stream_name>")` (`Streams` trong `chonoi/rng.py`); cấm `random` toàn cục và cấm đồng hồ hệ thống.
- **ID & thứ tự thực thể**: dùng `sort_by_id` (`chonoi/ids.py`) và `IdAllocator` (`self.ids`).
- **Không bịa yêu cầu**: chi tiết nào trong PRD-0 mơ hồ (ví dụ payload chi tiết của `dive`/`surface`/`choke`/`faint`, xử lý `zero_oxy_ticks` khi ngoi lên mặt nước, hoặc thứ tự sự kiện trong cùng tick) -> ghi rõ vào `docs/clarify.md` và hỏi PO (`missher03`).
- Không sửa test có sẵn cho xanh khi luật sai. Nếu có sáng tạo thêm, phải tắt mặc định ở chế độ `headless`.

### 5. Lệnh kiểm tra (PowerShell) trước khi mở PR
Chạy toàn bộ các lệnh sau và đảm bảo pass 100%:
```powershell
$env:PYTHONPATH="tests;."; python -m unittest tests.test_gather_survival -v
$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v
python -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out_p1_s1.jsonl
python -m chonoi.live --mode gather --seed 1
```
*(Xóa file `out_p1_s1.jsonl` tạm trước khi commit nếu không dùng làm bằng chứng.)*

### 6. Quy trình Git, Nhật ký AI & PR
- Tạo **≥ 3 commit có nội dung rõ ràng** bằng tài khoản GitHub của bạn (ví dụ: 1. thêm helper sinh tồn & oxy/ngạt, 2. xử lý `faint`/giỏ LIFO, 3. bổ sung `tests/test_gather_survival.py` + `docs/ai-usage-log.md`).
- Cập nhật `docs/ai-usage-log.md` với công cụ/model, công việc, ước lượng token và lỗi AI (nếu có).
- Mở PR vào `main` theo `.github/pull_request_template.md`, tag người review dự phòng (`@missher03`) và QA Lead (`@Limdim1604`). Giữ diff PR gọn (≤ ~400 dòng).
````

---

## Prompt 2 — Nguyễn Văn Quốc (`missher03` · MSSV `2A202603864`)
**Slice 2:** `gather` Hái nút, Bắt cá & Cập bến/Kho · **Vai:** PO (`docs/clarify.md`), dự phòng cho `duyhale95` · **Nhánh Git:** `feat/p1-s2-gather-harvest`

````markdown
Bạn là AI coding agent hỗ trợ **Nguyễn Văn Quốc (`missher03` — MSSV `2A202603864`)**, vai **PO (đầu mối `docs/clarify.md`)** của nhóm **BCDQ** (dự phòng cho `duyhale95`).

### 1. Nhánh Git & Mục tiêu Slice 2
- Làm việc trên nhánh: `feat/p1-s2-gather-harvest` (tạo từ `main` mới nhất; nếu Slice 1 của `duyhale95` đã merge thì rebase lên `main`).
- Mục tiêu: Hoàn thiện **Slice 2 (`gather` — Hái nút mặt nước, Bắt đàn cá dưới nước & Kiểm chứng cập bến/xuất kho)** trong `chonoi/sim/gather.py` (`TODO(nhóm, lát 2)`) và viết unit/headless tests trong `tests/test_gather_harvest.py`.

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md` và `TEAM.md`
2. `specs/001-phase-1-core/spec.md`, `specs/001-phase-1-core/plan.md`, `specs/001-phase-1-core/tasks.md`
3. `game.contract.json` (khối `tuning.gather`: `dock_pos`, `dock_radius`, `surface_depth`, `hold_capacity`, `interact_radius`, `node_yield`, `regrow_s`, `catch_radius`, `catch_cooldown_s`, `fish_yield`, `nodes`, `fish_initial`)
4. `docs/contracts/README.md` và `docs/contracts/inventory.sample.json`
5. `chonoi/sim/gather.py`, `chonoi/inventory.py`, `chonoi/ids.py`, `chonoi/runner.py`, `chonoi/rng.py`
6. **PRD-0 trên lab board** (`https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg`) — mục 13.8 ("Gather") và mục G (Kho) để đối chiếu payload sự kiện `gather`, `hold_full`, `node_regrown`, `fish_caught`, `gather_end` và cách xử lý khi giỏ gần đầy (`fish_yield` > chỗ trống).

### 3. Phạm vi sở hữu & File KHÔNG ĐƯỢC SỬA
- **File bạn sở hữu (được phép sửa/tạo):**
  - `chonoi/sim/gather.py` — **CHỈ phần Slice 2 (`TODO(nhóm, lát 2)`)**: tách thành các helper riêng (ví dụ `_handle_gather(...)`, `_handle_catch(...)`) để không xung đột với phần oxy/ngạt của `duyhale95`:
    - Trong `inp.pressed("interact")`: giữ nguyên ưu tiên `self._in_dock()` -> `self._finish("docked", events)` xét **TRƯỚC** hái nút.
    - Nếu không ở bến và đang ở mặt nước (`self._at_surface()`): tìm nút `ready` (`regrow_ticks == 0`) gần nhất trong `interact_radius` (khi khoảng cách bằng nhau thì chọn `id` nhỏ hơn theo `id_key` / `sort_by_id`). Kiểm tra sức chứa giỏ `hold_capacity`: nếu không đủ chỗ -> phát `hold_full`; nếu đủ -> thêm `node_yield` bản sao `n["kind"]` vào `self.hold`, đặt `n["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))`, phát `gather`.
    - Trong `inp.pressed("catch")`: chỉ thực hiện khi `self.catch_cd_ticks == 0` và đang dưới nước (`not self._at_surface()`). Tìm đàn cá gần nhất trong `catch_radius` (tie-break theo `id` nhỏ hơn qua `id_key` / `sort_by_id`). Kiểm tra `hold_capacity` với `fish_yield[kind]`: phát `fish_caught` hoặc `hold_full`, đặt `self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))` (đối chiếu PRD-0 xem bắt xong đàn cá có biến mất/xóa khỏi `self.fish` hay không và xử lý khi chỗ trống < `fish_yield`).
    - Kiểm chứng tích hợp `node_regrown` (đã có vòng đếm ngược ở đầu `step`) và xuất kho qua `inventory_items()` -> `runner.Session.write_inventory_if_done`.
  - `tests/test_gather_harvest.py` — viết test đầy đủ cho: ưu tiên cập bến trước hái khi đứng trong cả `dock_radius` và `interact_radius`, hái nút mặt nước & mọc lại `node_regrown`, tie-break theo `id`, bắt cá dưới nước & `catch_cd_ticks`, `hold_full`, và headless `--inventory-out` xuất đúng schema `{"items": ...}`.
  - `docs/clarify.md` — với vai trò PO, cập nhật mọi câu hỏi và quyết định đối chiếu từ PRD-0/giảng viên để cả nhóm dùng chung.
  - `docs/ai-usage-log.md` (ghi bổ sung dòng nhật ký AI của bạn).
- **File KHÔNG ĐƯỢC SỬA:**
  - Phần `TODO(nhóm, lát 1)` (oxy, ngạt, ngất) trong `chonoi/sim/gather.py` (của `duyhale95`).
  - `chonoi/sim/quan.py`, `chonoi/scenario.py`.
  - `game.contract.json`, `docs/contracts/`, `chonoi/{headless,inputs,contract,rng,ids,jsonl,inventory,runner,live}.py`, `chonoi/web/`.
  - `tests/test_smoke_p1.py`, `tests/test_python_starter_units.py`, `tests/test_team_check.py`, và các file test của slice khác.

### 4. Quy tắc bắt buộc từ `AGENTS.md`
- **Không hard-code số liệu** trong luật: đọc `interact_radius`, `node_yield`, `regrow_s`, `catch_radius`, `catch_cooldown_s`, `fish_yield`, `hold_capacity` từ `self.t` (`game.contract.json`).
- **Mọi số ngẫu nhiên** (nếu dùng) phải qua `self.rng.get("<stream_name>")`; cấm `random` toàn cục và cấm đồng hồ hệ thống.
- **Sắp thứ tự & cấp ID**: dùng `sort_by_id` / `id_key` (`chonoi/ids.py`) và `self.ids`.
- **Không bịa yêu cầu**: điểm nào PRD-0 chưa ghi tường minh -> hỏi giảng viên / trợ giảng AI và ghi quyết định vào `docs/clarify.md`.
- Không sửa test có sẵn cho xanh khi luật sai. Sáng tạo thêm (nếu có) phải tắt mặc định ở `headless`.

### 5. Lệnh kiểm tra (PowerShell) trước khi mở PR
Chạy toàn bộ các lệnh sau và đảm bảo pass 100%:
```powershell
$env:PYTHONPATH="tests;."; python -m unittest tests.test_gather_harvest -v
$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v
python -m chonoi.headless --mode gather --seed 1 --ticks 600 --inventory-out kho_test.json --out out_p1_s2.jsonl
python -m chonoi.live --mode gather --seed 1 --inventory-out kho_test.json
```
*(Xóa `out_p1_s2.jsonl` và `kho_test.json` tạm trước khi commit.)*

### 6. Quy trình Git, Nhật ký AI & PR
- Tạo **≥ 3 commit có nội dung rõ ràng** bằng tài khoản GitHub của bạn (ví dụ: 1. hái nút mặt nước & `hold_full`, 2. bắt đàn cá dưới nước & cooldown, 3. `tests/test_gather_harvest.py` + cập nhật `docs/clarify.md` & `docs/ai-usage-log.md`).
- Cập nhật `docs/ai-usage-log.md`.
- Mở PR vào `main` theo `.github/pull_request_template.md`, tag người review dự phòng (`@duyhale95`) và QA Lead (`@Limdim1604`). Giữ diff PR gọn (≤ ~400 dòng).
````

---

## Prompt 3 — Nguyễn Thiên Bảo (`Limdim1604` · MSSV `2A202603861`)
**Slice 3:** `quan` Khách đến, Chọn món, Giữ chỗ, Kiên nhẫn & Kiểm mâu thuẫn `scenario.py` + QA `docs/verification/phase-1.md` · **Vai:** QA Lead, dự phòng cho `Lmeo2h` · **Nhánh Git:** `feat/p1-s3-quan-customers`

````markdown
Bạn là AI coding agent hỗ trợ **Nguyễn Thiên Bảo (`Limdim1604` — MSSV `2A202603861`)**, vai **QA Lead** của nhóm **BCDQ** (dự phòng cho `Lmeo2h`).

### 1. Nhánh Git & Mục tiêu Slice 3
- Làm việc trên nhánh: `feat/p1-s3-quan-customers` (tạo từ `main` mới nhất).
- Mục tiêu:
  1. Hoàn thiện **Slice 3 (`quan` — Khách đến, Chọn món nấu được, Giữ chỗ nguyên liệu, Kiên nhẫn & `customer_left`/`no_dish`)** trong `chonoi/sim/quan.py` (`TODO(nhóm, lát 3)`).
  2. Hoàn thiện **kiểm mâu thuẫn scenario mức luật** trong `chonoi/scenario.py` (`TODO(nhóm)` dòng 4–5).
  3. Viết test `tests/test_quan_customers.py` và hoàn thiện báo cáo QA Phase 1 tại `docs/verification/phase-1.md` (kèm bằng chứng trong `docs/proof/phase-1/`).

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md` và `TEAM.md`
2. `specs/001-phase-1-core/spec.md`, `specs/001-phase-1-core/plan.md`, `specs/001-phase-1-core/tasks.md`
3. `game.contract.json` (khối `tuning.quan`: `tables`, `first_customer_tick`, `customer_interval_s`, `patience_s`, `left_reputation_delta`, `reputation_initial`, `reputation_min`, `reputation_max`; và khối `tuning.menu`)
4. `docs/contracts/README.md`, `docs/contracts/inventory.sample.json`, `docs/verification/phase-1.md`
5. `chonoi/sim/quan.py`, `chonoi/scenario.py`, `chonoi/inventory.py`, `chonoi/ids.py`, `chonoi/rng.py`, `chonoi/errors.py`
6. **PRD-0 trên lab board** (`https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg`) — mục D (Scenario & "Mâu thuẫn -> mã 2"), mục E (Sự kiện), và mục F (Quán) để đối chiếu chính xác cấu trúc object `customer`, trạng thái (`waiting`, `assigned`, `eating`...), giữ chỗ `reserved`, và thứ tự xử lý trong `step`.

### 3. Phạm vi sở hữu & File KHÔNG ĐƯỢC SỬA
- **File bạn sở hữu (được phép sửa/tạo):**
  - `chonoi/sim/quan.py` — **CHỈ phần Slice 3 (`TODO(nhóm, lát 3)`)**: tách thành các helper riêng (ví dụ `_init_customer_reservations(...)`, `_update_customers_patience(...)`, `_maybe_spawn_customer(...)`) để không đè vào phần bếp/phục vụ/thanh toán của `Lmeo2h`:
    - Khởi tạo khách dựng sẵn từ `scenario.get("customers", [])` và suy ra giữ chỗ (`reserved`) nguyên liệu theo công thức `menu` (đối chiếu PRD-0).
    - Theo lịch (`first_customer_tick`, `customer_interval_s` và cờ `random_customers` nếu có trong scenario): kiểm tra bàn trống (theo `sort_by_id`), tính phần kho khả dụng (`stock - tổng reserved`), chọn ngẫu nhiên một món nấu được bằng `self.rng.get("customer_order")` (hoặc tên stream thống nhất theo PRD-0/hợp đồng), cấp ID bằng `self.ids.new(...)`, giữ chỗ nguyên liệu vào `reserved` của khách; nếu không còn món nào nấu được -> phát sự kiện `no_dish`.
    - Giảm kiên nhẫn từng tick; khi hết kiên nhẫn -> phát `customer_left`, giải phóng `reserved`, xóa khách khỏi bàn, cộng `left_reputation_delta` vào `self.reputation` và kẹp trong `[reputation_min, reputation_max]`.
  - `chonoi/scenario.py` — bổ sung kiểm mâu thuẫn mức luật tại `TODO(nhóm)` trong `_validate_quan` (và giữ nguyên mọi rule cú pháp/schema hiện có để `test_smoke_p1.py` không gãy): ném `BadInput` (thoát mã 2) khi khách giữ chỗ vượt quá `stock`, đơn đã gán thiếu hoặc có món không hợp lệ trong `menu`, khách `eating` thiếu thông tin bắt buộc/giá/bộ đếm hợp lệ, hoặc các mâu thuẫn được liệt kê trong PRD-0 mục D ("Mâu thuẫn -> mã 2").
  - `tests/test_quan_customers.py` — viết test đầy đủ cho: khách đến theo `first_customer_tick` & `customer_interval_s`, chọn món nấu được từ kho còn dư sau khi trừ `reserved`, phát `no_dish`, hết kiên nhẫn -> `customer_left` + `left_reputation_delta` + kẹp uy tín, tính tất định cùng `seed`, và các ca `scenario` mâu thuẫn thoát mã `2` trước khi ghi file đầu ra.
  - `docs/verification/phase-1.md` và `docs/proof/phase-1/` — ma trận truy vết AC Phase 1 và log chạy kiểm chứng trung thực.
  - `docs/ai-usage-log.md` (ghi bổ sung dòng nhật ký AI của bạn) và `docs/clarify.md` (nếu cần hỏi PO `missher03`).
- **File KHÔNG ĐƯỢC SỬA:**
  - Phần `TODO(nhóm, lát 4)` (interact bếp/bàn, nấu, bưng, phục vụ, `paid`, boa, `quan_end`) trong `chonoi/sim/quan.py` (của `Lmeo2h`).
  - `chonoi/sim/gather.py`.
  - `game.contract.json`, `docs/contracts/`, `chonoi/{headless,inputs,contract,rng,ids,jsonl,inventory,runner,live}.py`, `chonoi/web/`.
  - `tests/test_smoke_p1.py`, `tests/test_python_starter_units.py`, `tests/test_team_check.py`, và các file test của slice khác.

### 4. Quy tắc bắt buộc từ `AGENTS.md`
- **Không hard-code số liệu** trong luật: đọc toàn bộ tuning (`first_customer_tick`, `customer_interval_s`, `patience_s`, `left_reputation_delta`, `reputation_min`, `reputation_max`, `menu`) từ `self.t` và `self.menu` (`game.contract.json`).
- **Mọi số ngẫu nhiên** chọn món/khách phải đi qua `Streams` (`self.rng.get(...)`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- **Sắp thứ tự & cấp ID**: dùng `sort_by_id` (`chonoi/ids.py`) cho bàn/khách và `self.ids.new(...)` để cấp ID khách mới.
- **Không bịa yêu cầu**: mọi chi tiết chưa rõ trong PRD-0 (ví dụ schema các field của khách trong `scenario.customers`, công thức `patience_ticks`, cách chọn bàn trống khi nhiều bàn trống, hoặc khi không có bàn trống có sinh khách không) -> ghi vào `docs/clarify.md` và hỏi PO (`missher03`).
- Không sửa test có sẵn cho xanh khi luật sai. Sáng tạo thêm (nếu có) phải tắt mặc định ở `headless`.

### 5. Lệnh kiểm tra (PowerShell) trước khi mở PR
Chạy toàn bộ các lệnh sau và đảm bảo pass 100%:
```powershell
$env:PYTHONPATH="tests;."; python -m unittest tests.test_quan_customers -v
$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v
python -m chonoi.headless --mode quan --seed 1 --ticks 1200 --out out_p1_s3.jsonl
python -m chonoi.live --mode quan --seed 1
```
*(Xóa `out_p1_s3.jsonl` tạm trước khi commit nếu không đưa vào `docs/proof/phase-1/`.)*

### 6. Quy trình Git, Nhật ký AI & PR
- Tạo **≥ 3 commit có nội dung rõ ràng** bằng tài khoản GitHub của bạn (ví dụ: 1. kiểm mâu thuẫn `scenario.py`, 2. logic khách đến/giữ chỗ/kiên nhẫn trong `quan.py`, 3. `tests/test_quan_customers.py` + `docs/verification/phase-1.md` & `docs/ai-usage-log.md`).
- Cập nhật `docs/ai-usage-log.md`.
- Mở PR vào `main` theo `.github/pull_request_template.md`, tag người review dự phòng (`@Lmeo2h`) và Nhóm trưởng (`@duyhale95`). Giữ diff PR gọn (≤ ~400 dòng).
````

---

## Prompt 4 — Nguyễn Tấn Châu (`Lmeo2h` · MSSV `2A202603846`)
**Slice 4:** `quan` Bếp, Phục vụ, Thanh toán/Boa/Uy tín & `quan_end` · **Vai:** Integrator (giữ `docs/contracts/`, gắn tag `phase-1`), dự phòng cho `Limdim1604` · **Nhánh Git:** `feat/p1-s4-quan-service`

````markdown
Bạn là AI coding agent hỗ trợ **Nguyễn Tấn Châu (`Lmeo2h` — MSSV `2A202603846`)**, vai **Integrator** của nhóm **BCDQ** (dự phòng cho `Limdim1604`).

### 1. Nhánh Git & Mục tiêu Slice 4
- Làm việc trên nhánh: `feat/p1-s4-quan-service` (tạo từ `main` mới nhất; rebase lên `main` sau khi Slice 3 của `Limdim1604` merge để tích hợp trơn tru).
- Mục tiêu:
  1. Hoàn thiện **Slice 4 (`quan` — Bếp, Bưng món, Phục vụ, Thanh toán/Boa/Uy tín & `quan_end`)** trong `chonoi/sim/quan.py` (`TODO(nhóm, lát 4)`).
  2. Viết unit/headless tests trong `tests/test_quan_service.py`.
  3. Với vai trò **Integrator**: kiểm tra khớp hợp đồng tích hợp `docs/contracts/`, chạy smoke test nối `gather` (`--inventory-out`) -> `quan` (`--inventory`) sau khi 4 slice đã vào `main`, và gắn tag `phase-1` đúng hạn (`< 1:00`).

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md` và `TEAM.md`
2. `specs/001-phase-1-core/spec.md`, `specs/001-phase-1-core/plan.md`, `specs/001-phase-1-core/tasks.md`
3. `game.contract.json` (khối `tuning.quan`: `interact_radius`, `stoves`, `tables`, `eat_s`, `burn_s`, `carry_limit`, `tip_rate`, `tip_min_patience_ratio`, `tip_reputation`, `reputation_min`, `reputation_max`; khối `tuning.menu`; và `tuning.score.reputation_multiplier`)
4. `docs/contracts/README.md` và `docs/contracts/inventory.sample.json`
5. `chonoi/sim/quan.py`, `chonoi/ids.py`, `chonoi/runner.py`, `chonoi/rng.py`, `chonoi/inventory.py`
6. **PRD-0 trên lab board** (`https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg`) — mục E (Sự kiện) và mục F (Quán) để đối chiếu chính xác tên sự kiện, payload `data`, quy tắc làm tròn tiền/boa, điều kiện ưu tiên chọn bếp/bàn khi `interact`, và cách tính `money`, `earned`, `shift_earned`, `reputation`.

### 3. Phạm vi sở hữu & File KHÔNG ĐƯỢC SỬA
- **File bạn sở hữu (được phép sửa/tạo):**
  - `chonoi/sim/quan.py` — **CHỈ phần Slice 4 (`TODO(nhóm, lát 4)`)**: tách thành các helper riêng (ví dụ `_update_stoves_and_eating(...)`, `_handle_interact(...)`, `_complete_payment(...)`) để không đè vào phần khách/giữ chỗ của `Limdim1604`:
    - Cập nhật bếp (`stoves`) và khách đang ăn (`eating`): giảm `cook_ticks_left`; khi về `0` chuyển bếp sang trạng thái `ready` và phát `dish_ready` (lưu ý `burn_s` hiện là `null` trong `game.contract.json` cho Phase 1). Khách ăn hết `eat_s` -> thanh toán (`paid`), kiểm tra điều kiện boa (`tip_min_patience_ratio`, `tip_rate`), cộng `money`, `earned`, `shift_earned`, cộng `tip_reputation` vào `self.reputation` (kẹp `[reputation_min, reputation_max]`), giải phóng bàn.
    - Xử lý `inp.pressed("interact")`: mỗi tick tối đa **MỘT** `interact`; xét tất cả bếp và bàn trong `interact_radius`, chọn đối tượng theo khóa ưu tiên `(khoảng cách, bếp trước bàn, id_key(id))`:
      - Tại bếp `idle` khi tay rỗng (`self.hand is None`): chọn món cần nấu (theo khách đang chờ) có đủ nguyên liệu, bắt đầu nấu (`cook_started`, đặt `cook_ticks_left` theo `menu[dish]["cook_s"]`, trừ kho/chuyển giữ chỗ đúng quy tắc PRD-0).
      - Tại bếp `ready` khi tay còn chỗ (`carry_limit`): bưng món lên `self.hand` (`dish_picked`), đưa bếp về `idle`.
      - Tại bàn có khách khớp món trên `self.hand`: phục vụ khách (`served`), xóa món khỏi `self.hand`, khách chuyển sang ăn trong `eat_s`.
    - Kiểm chứng `quan_end` khi hết ca (`time_left_ticks <= 0`, đã có khung: `reason`, `money`, `earned`, `shift_earned`, `reputation`).
  - `tests/test_quan_service.py` — viết test đầy đủ cho: chọn đối tượng `interact` theo `(khoảng cách, bếp trước bàn, id)`, `cook_started` -> `dish_ready` -> `dish_picked` -> `served` -> `paid`, có boa và không boa theo `tip_min_patience_ratio`, cập nhật `tip_reputation` (kẹp trần `reputation_max`), và `quan_end` cùng `score` (`earned + reputation_multiplier * floor(reputation)`).
  - `docs/ai-usage-log.md` (ghi bổ sung dòng nhật ký AI của bạn).
  - `docs/clarify.md` (nếu cần ghi câu hỏi/làm rõ cho PO `missher03`).
- **File KHÔNG ĐƯỢC SỬA:**
  - Phần `TODO(nhóm, lát 3)` (khách đến, chọn món, giữ chỗ, kiên nhẫn, `customer_left`, `no_dish`) trong `chonoi/sim/quan.py` (của `Limdim1604`).
  - `chonoi/sim/gather.py`, `chonoi/scenario.py`.
  - `game.contract.json`, `chonoi/{headless,inputs,contract,rng,ids,jsonl,inventory,runner,live}.py`, `chonoi/web/`.
  - `tests/test_smoke_p1.py`, `tests/test_python_starter_units.py`, `tests/test_team_check.py`, và các file test của slice khác.

### 4. Quy tắc bắt buộc từ `AGENTS.md`
- **Không hard-code số liệu** trong luật: đọc toàn bộ tuning (`interact_radius`, `eat_s`, `carry_limit`, `tip_rate`, `tip_min_patience_ratio`, `tip_reputation`, `reputation_min`, `reputation_max`, `menu[dish]["cook_s"]`, `menu[dish]["price"]`) từ `self.t` và `self.menu`.
- **Mọi số ngẫu nhiên** (nếu dùng) phải qua `Streams` (`self.rng.get(...)`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- **Sắp thứ tự & tie-break ID**: dùng `id_key` / `sort_by_id` (`chonoi/ids.py`).
- **Không bịa yêu cầu**: chi tiết nào trong PRD-0 chưa rõ (ví dụ cách trừ `stock`/`reserved` tại thời điểm `cook_started`, cách chọn khách khi nhiều khách cùng chờ món tại một bếp, làm tròn tiền boa) -> ghi vào `docs/clarify.md` và hỏi PO (`missher03`).
- Không sửa test có sẵn cho xanh khi luật sai. Sáng tạo thêm (nếu có) phải tắt mặc định ở `headless`.

### 5. Lệnh kiểm tra (PowerShell) trước khi mở PR & gắn tag `phase-1`
Chạy toàn bộ các lệnh sau và đảm bảo pass 100%:
```powershell
$env:PYTHONPATH="tests;."; python -m unittest tests.test_quan_service -v
$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v
python tools/check_team.py
python -m chonoi.headless --mode gather --seed 1 --ticks 600 --inventory-out kho_p1.json --out out_gather.jsonl
python -m chonoi.headless --mode quan --seed 1 --ticks 1200 --inventory kho_p1.json --out out_quan.jsonl
python -m chonoi.live --mode quan --seed 1
```
*(Xóa các file `kho_p1.json`, `out_gather.jsonl`, `out_quan.jsonl` tạm trước khi commit/gắn tag.)*

Sau khi toàn bộ 4 PR đã merge vào `main` và `discover -s tests -v` + `tools/check_team.py` xanh 100%, thực hiện gắn tag (Integrator):
```powershell
git checkout main
git pull origin main
git tag phase-1
git push origin phase-1
```

### 6. Quy trình Git, Nhật ký AI & PR
- Tạo **≥ 3 commit có nội dung rõ ràng** bằng tài khoản GitHub của bạn (ví dụ: 1. bếp nấu/bưng/phục vụ & ưu tiên `interact`, 2. thanh toán/boa/uy tín & kết ca, 3. `tests/test_quan_service.py` + `docs/ai-usage-log.md`).
- Cập nhật `docs/ai-usage-log.md`.
- Mở PR vào `main` theo `.github/pull_request_template.md`, tag người review dự phòng (`@Limdim1604`) và Nhóm trưởng (`@duyhale95`). Giữ diff PR gọn (≤ ~400 dòng).
````
