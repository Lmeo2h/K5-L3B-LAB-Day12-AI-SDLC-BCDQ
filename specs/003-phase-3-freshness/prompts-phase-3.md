# Prompts Phase 3 — Vertical Slices (Nhóm BCDQ)

> Tài liệu này chứa **4 prompt hoàn chỉnh (copy-paste trực tiếp cho AI coding agent)** tương ứng với 4 Vertical Slice của **Phase 3 — TICKET-03: Change Request "Mùa Nước Nổi"** (**Test Contract v1.2**, cửa sổ sprint **35 phút: `1:55–2:30`**, mốc gắn tag `phase-3` trước **`2:30`**).
>
> **Quy tắc chung trước khi chạy prompt:**
> - Tuân thủ `AGENTS.md` và `TEAM.md`: mỗi thành viên làm trên nhánh riêng, **≥ 3 commit có nội dung** từ tài khoản GitHub cá nhân, mở PR theo `.github/pull_request_template.md`, đọc chéo theo cặp dự phòng (`duyhale95` ↔ `missher03`, `Limdim1604` ↔ `Lmeo2h`), cập nhật `docs/ai-usage-log.md`.
> - **Chiến lược giữ `main` luôn xanh trong lúc đổi schema kho (v1.1 → v1.2):**
>   1. **Phút 0–7:** `duyhale95` (Slice 1) land sớm `chonoi/inventory.py` (`FRESH_SCALE = 240` + hàm đọc/ghi v1.2 `[{"id","kind","fresh"}]`) & `chonoi/contract.py` (`freshness`) lên `main` để 3 bạn còn lại rebase và viết test v1.2 song song ngay.
>   2. **Phút 7–20:** Merge tuần tự **Slice 1 (`gather`) → Slice 2 (`monsters`/`day`) → Slice 3 (`quan`/`scenario` + bật `contract_version: "1.2"`)**. Khi Slice 3 merge, mọi đầu bàn giao đã dùng kho cá thể và từ chối kho đếm cũ bằng mã `2`.
>   3. **Phút 20 (`2:15`):** Chạy **smoke bàn giao 2 tiến trình** (`gather --inventory-out` → `quan --inventory --ticks 0`), lưu `docs/proof/phase-3/integration.md`.
>   4. **Phút 20–35 (trước `2:30`):** Merge Slice 4 (`shop`/`runner`/`web/index.html`/`CHANGELOG.md`), chạy toàn bộ regression P1–P3 + `22,200` ticks `<= 20s` + SHA-256 trùng khớp, hoàn thiện `docs/verification/phase-3.md` & `docs/retro.md`, đẩy tag `phase-3` trước **`2:30`**.

---

## Prompt 1 — Hà Lê Duy (`duyhale95` · MSSV `2A202603851`)
**Slice 1:** Contract v1.2 Foundation (`inventory.py` `240`-scale, `contract.py`) + `gather` Độ tươi / Ngưỡng 30 (`spoiled`) · **Vai:** Scrum / Release · **Nhánh Git:** `feat/p3-s1-contract-fresh-gather`

````markdown
Bạn là AI coding agent hỗ trợ **Hà Lê Duy (`duyhale95` — MSSV `2A202603851`)**, vai **Scrum / Release (Nhóm trưởng)** của nhóm **BCDQ** (dự phòng cho `missher03`).

### 1. Nhánh Git & Mục tiêu Slice 1
- Tạo nhánh `feat/p3-s1-contract-fresh-gather` từ `main` mới nhất (đã có tag `phase-2`).
- **Ưu tiên 0–7 phút đầu:** Đẩy phần adapter/schema `chonoi/inventory.py` (`FRESH_SCALE = 240`, đọc/ghi `{"items":[{"id","kind","fresh"}]}`) và `chonoi/contract.py` (`tuning.freshness`) lên `main` trước để cả nhóm phát triển song song; sau đó hoàn thiện độ tươi trong `chonoi/sim/gather.py`, `chonoi/scenario.py` (`_validate_gather`), `tests/test_freshness_gather_v12.py`, và thích nghi các test `gather` cũ.

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md`, `TEAM.md`, `docs/plan/phase-3.md`
2. `specs/003-phase-3-freshness/spec.md`, `specs/003-phase-3-freshness/plan.md`, `specs/003-phase-3-freshness/tasks.md`
3. `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/sim/gather.py`, `chonoi/scenario.py`, `chonoi/ids.py`
4. `tests/test_gather_harvest.py`, `tests/test_gather_survival.py`, `tests/test_gather_fish_v11.py`, `tests/test_python_starter_units.py`

### 3. Quy tắc TICKET-03 bắt buộc cho Slice 1
1. **Độ chính xác độ tươi & `chonoi/inventory.py`:**
   - Dùng số nguyên `FRESH_SCALE = 240` đơn vị cho mỗi điểm tươi (`100` = `24000`, `30` = `7200`). Ở `gather` trừ `2` đơn vị/tick (`0.5/s`); ở `quan` trừ `1` đơn vị/tick (`0.25/s`).
   - Schema v1.2: `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}` (rỗng là `{"items": []}`). `id` duy nhất khác rỗng, `kind in KINDS_P2`, `fresh` hữu hạn trong `[0, 100]`.
   - Khi `contract_version == "1.2"` (hoặc gọi `read_inventory_v12` / `validate_items_v12`), từ chối kho đếm cũ `{"items": {"ca_loc": 1}}` và mọi sai schema bằng `BadInput` (mã thoát `2` trước khi ghi file).
   - `write_inventory` ghi nguyên tử qua file tạm, sắp theo `id_key(item["id"])`, xuất `fresh` đủ chính xác (ví dụ `round(units / 240, 6)`) để khi đọc lại không sai lệch nhánh ngưỡng `< 30`.
2. **`chonoi/contract.py` & `game.contract.json`:**
   - Khối `"freshness": {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}` trong `tuning`.
   - Validate `freshness` đúng miền (`initial == 100`, `gather_decay_per_s > 0`, `quan_decay_per_s > 0`, `0 < spoiled_below < initial`).
3. **`GatherSim` (`chonoi/sim/gather.py`):**
   - Nhận thêm `item_ids=None` trong `GatherSim.__init__` (mặc định `IdAllocator()` nếu `None`), reserve mọi `id` từ `scenario.get("hold", [])`.
   - `self.hold` chứa các dict cá thể `{"id", "kind", "fresh", "_units"}` (hoặc lưu `fresh` + `_units` nội bộ, xuất ra snapshot/inventory sạch chỉ gồm `{"id", "kind", "fresh"}`).
   - **Bước 1 trong `GatherSim.step`:** cùng lúc đếm timer/nút mọc lại, giảm tươi toàn bộ cá thể **đang có trong `hold`** theo `gather_decay_per_s` (`2` đơn vị/tick, kẹp đáy `0`). Cá thể nào đi từ `>= spoiled_below` (`>= 7200`) xuống `< spoiled_below` (`< 7200`, so trước khi làm tròn!) thì phát `("spoiled", {"item_id": item["id"], "kind": item["kind"], "location": "hold"})` theo thứ tự `id_key(item["id"])`.
   - Cá thể mới vào `hold` khi hái nút (`_try_gather_node`) hoặc bắt cá (`_try_catch_fish`: cá thể từng con theo `yield`) nhận `id = self.item_ids.new("I")`, `fresh = 100` (`24000` units) và **chỉ bắt đầu hao từ bước sau**.
   - `inventory_items()` trả danh sách cá thể sạch sắp theo `id_key`; `hold_to_items` hoặc helper tương ứng xuất chuẩn v1.2 cho `gather_end.data.inventory` và `--inventory-out`.
   - Kiểm tra ca mẫu TICKET-03: `{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":30}],"random_fish":false,"monsters":[]}}` -> tick 1 phát `spoiled` với `item_id="I1"`, `kind="ca_linh"`, `location="hold"`.
4. **`chonoi/scenario.py` (`_validate_gather`):**
   - `gather.hold` là mảng cá thể `{"id", "kind", "fresh"}` (duy nhất `id`, `kind in KINDS_P2`, `fresh` số hữu hạn trong `[0, 100]`, độ dài `<= hold_capacity`).

### 4. Phạm vi sở hữu & File KHÔNG ĐƯỢC SỬA
- **Được phép sửa/tạo:** `game.contract.json` (khối `freshness`), `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/sim/gather.py`, `chonoi/scenario.py` (CHỈ `_validate_gather`), `tests/test_freshness_gather_v12.py` (mới), thích nghi `tests/test_gather_harvest.py`, `tests/test_gather_survival.py`, `tests/test_gather_fish_v11.py`, `tests/test_python_starter_units.py` (kèm lý do commit), `docs/ai-usage-log.md`.
- **KHÔNG sửa:** `chonoi/sim/monsters.py`, `chonoi/sim/quan.py`, `chonoi/sim/day.py`, `chonoi/sim/shop.py`, `chonoi/web/`, phần `_validate_quan`/`_validate_day` của `scenario.py`.

### 5. Kiểm tra & Quy trình Git
- Tạo **≥ 3 commit rõ ràng** bằng tài khoản `duyhale95`; chạy `$env:PYTHONPATH="tests;."; python -m unittest tests.test_freshness_gather_v12 tests.test_gather_harvest tests.test_gather_survival tests.test_gather_fish_v11 -v` và kiểm tra headless byte-determinism trước khi mở PR.
````

---

## Prompt 2 — Nguyễn Văn Quốc (`missher03` · MSSV `2A202603864`)
**Slice 2:** `monsters` LIFO cá thể & `DaySim` ID liên tục xuyên pha/Ngày · **Vai:** PO (`docs/clarify.md`), dự phòng cho `duyhale95` · **Nhánh Git:** `feat/p3-s2-monsters-day-v12`

````markdown
Bạn là AI coding agent hỗ trợ **Nguyễn Văn Quốc (`missher03` — MSSV `2A202603864`)**, vai **PO (chủ trì `docs/clarify.md`)** của nhóm **BCDQ** (dự phòng cho `duyhale95`).

### 1. Nhánh Git & Mục tiêu Slice 2
- Tạo nhánh `feat/p3-s2-monsters-day-v12` từ `main` (viết test-first ngay; rebase sau khi Slice 1 merge).
- Mục tiêu: Chuyển `monster_hit.lost` và `faint.lost` trong `chonoi/sim/monsters.py` sang **mảng cá thể** LIFO giữ nguyên độ tươi lúc rơi; cập nhật `chonoi/sim/day.py` giữ `item_ids: IdAllocator` liên tục xuyên pha & Ngày (Ngày 1 giữ ID từ `scenario.gather.hold`, Ngày 2+ cấp ID mới nếu mẫu có `hold`), bàn giao `gather -> quan` cùng tick không hao thêm; cập nhật `docs/clarify.md` và `tests/test_monsters_day_v12.py`.

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md`, `TEAM.md`, `docs/clarify.md`, `docs/plan/phase-3.md`
2. `specs/003-phase-3-freshness/spec.md`, `specs/003-phase-3-freshness/plan.md`, `specs/003-phase-3-freshness/tasks.md`
3. `chonoi/sim/monsters.py`, `chonoi/sim/day.py`, `chonoi/sim/gather.py`, `chonoi/inventory.py`
4. `tests/test_gather_monsters.py`, `tests/test_day_shop_pause.py`

### 3. Quy tắc TICKET-03 bắt buộc cho Slice 2
1. **`chonoi/sim/monsters.py`:**
   - Khi `monster_hit` rơi `floor(len(hold) * loss_ratio)` phần tử cuối theo LIFO, mỗi phần tử trong `lost` phải là dict cá thể sạch `{"id": ..., "kind": ..., "fresh": ...}` với đúng độ tươi hiện tại ở tick va chạm (không làm tròn sai, không để lộ key nội bộ `_units`).
   - Khi `hp == 0` (`faint`), các phần tử còn lại trong `hold` pop theo LIFO vào `faint.data.lost` dưới dạng mảng cá thể sạch `[{"id", "kind", "fresh"}, ...]`.
2. **`chonoi/sim/day.py`:**
   - `DaySim.__init__` khởi tạo `self.item_ids = IdAllocator()`, reserve toàn bộ ID trong `scenario.get("gather", {}).get("hold", [])` và `scenario.get("quan", {}).get("stock", [])` (nếu có).
   - Truyền `item_ids=self.item_ids` cho `GatherSim` (qua `inspect.signature` để an toàn) và `QuanSim`.
   - Với `Day >= 2`: nếu kịch bản vẫn lặp lại mẫu `gather.hold`, TICKET-03 quy định: *"Trong day, Ngày đầu giữ nguyên id trong mẫu gather.hold, các Ngày kế cấp id mới theo thứ tự mảng với kind/fresh ban đầu."* Hãy cấp lại `id = self.item_ids.new("I")` cho từng phần tử `hold` ở Ngày 2+ (hoặc rõ ràng theo kịch bản ngày).
   - Khi `gather` kết thúc ở bước `old_phase == "gather"`, truyền `inv = [] if self.sub.reason == "fainted" else self.sub.inventory_items()` sang `_start_quan(inv)` trong cùng tick — **không hao tươi thêm trong tick chuyển pha**; `quan` bắt đầu chạy & hao tươi từ bước tiếp theo.
   - Khi `quan` kết thúc, chuyển `leftover` (mảng cá thể còn lại trong `sub.stock`) sang `ShopSim`, giữ nguyên không hao tươi ở Shop; sang Ngày mới xóa sạch `hold` & `stock` cũ nhưng **tuyệt đối không reset `self.item_ids`** (`I1, I2,...` tiếp tục tăng xuyên suốt 5 Ngày!).
3. **Vai trò PO (`docs/clarify.md`):**
   - Ghi nhận các quyết định v1.2 (biểu diễn `240` đơn vị/điểm tươi, thứ tự `spoiled` trước tái giữ chỗ, giá chốt theo tươi trước tính boa, phạm vi mở rộng hoãn cho nhóm 4 người).

### 4. Phạm vi sở hữu & File KHÔNG ĐƯỢC SỬA
- **Được phép sửa/tạo:** `chonoi/sim/monsters.py`, `chonoi/sim/day.py`, `tests/test_monsters_day_v12.py` (mới), thích nghi `tests/test_gather_monsters.py` (kèm lý do commit), `docs/clarify.md`, `docs/ai-usage-log.md`.
- **KHÔNG sửa:** `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/sim/gather.py`, `chonoi/sim/quan.py`, `chonoi/sim/shop.py`, `chonoi/scenario.py`, `chonoi/web/`.

### 5. Kiểm tra & Quy trình Git
- Tạo **≥ 3 commit rõ ràng** bằng tài khoản `missher03`; chạy `$env:PYTHONPATH="tests;."; python -m unittest tests.test_monsters_day_v12 tests.test_gather_monsters -v` sau khi rebase lên Slice 1 và mở PR #2 vào `main`.
````

---

## Prompt 3 — Nguyễn Thiên Bảo (`Limdim1604` · MSSV `2A202603861`)
**Slice 3:** `quan` Độ tươi / `spoiled` / Giữ chỗ `id` / Giá chốt + `scenario.py` v1.2 + Bật v1.2 & QA · **Vai:** QA Lead · **Nhánh Git:** `feat/p3-s3-quan-freshness-qa`

````markdown
Bạn là AI coding agent hỗ trợ **Nguyễn Thiên Bảo (`Limdim1604` — MSSV `2A202603861`)**, vai **QA Lead** của nhóm **BCDQ** (dự phòng cho `Lmeo2h`).

### 1. Nhánh Git & Mục tiêu Slice 3
- Tạo nhánh `feat/p3-s3-quan-freshness-qa` từ `main` (viết test-first ngay; rebase sau khi Slice 2 merge).
- Mục tiêu:
  1. Nâng cấp `chonoi/sim/quan.py` lên v1.2: kho cá thể, hao `0.25/s`, `spoiled(stock)` theo `id_key`, nhả & thử giữ lại 1 lần khi hàng giữ vừa ươn (`(order_tick, id_key(table_id))` → `unfulfillable`), chọn tươi nhất hòa `id_key`, `cook_started.items` sắp `(kind, id_key)`, chốt `base_price = floor(price * avg_fresh / 100)` và tính `tip` trên `base_price` đã chốt.
  2. Nâng cấp `chonoi/scenario.py` (`_validate_quan`, `prepare_quan_customers`) kiểm `quan.stock[]` cá thể, `customers[].reserved[]` mảng ID duy nhất chưa ươn, đủ công thức, `base_price` hợp lệ (thoát mã `2`).
  3. Khi rebase xong sau Slice 2, bật `"contract_version": "1.2"` trong `game.contract.json` (từ chối kho đếm mã `2`), thích nghi các test `quan`/`smoke_p1` cũ, chạy smoke bàn giao 2 tiến trình phút 20 và hoàn thiện `docs/verification/phase-3.md` + `docs/proof/phase-3/`.

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md`, `TEAM.md`, `docs/plan/phase-3.md`, `docs/clarify.md`
2. `specs/003-phase-3-freshness/spec.md`, `specs/003-phase-3-freshness/plan.md`, `specs/003-phase-3-freshness/tasks.md`
3. `chonoi/sim/quan.py`, `chonoi/scenario.py`, `chonoi/inventory.py`, `chonoi/ids.py`
4. `tests/test_quan_customers.py`, `tests/test_quan_service.py`, `tests/test_quan_v11.py`, `tests/test_smoke_p1.py`

### 3. Quy tắc TICKET-03 bắt buộc cho Slice 3
1. **`QuanSim` (`chonoi/sim/quan.py`):**
   - `self.stock`: danh sách/bảng cá thể (`{"id", "kind", "fresh", "_units"}` dùng chung `FRESH_SCALE = 240` từ `inventory.py`). `snapshot()["stock"]` trả mảng cá thể sạch sắp theo `id_key(item["id"])`.
   - **Thứ tự trong `QuanSim.step`:**
     1. Giảm `time_left_ticks`, tăng `phase_tick`, giảm `patience_ticks_left`, giảm `cook_ticks_left` & `eat_ticks_left` (phát `dish_ready`).
     2. **Hao tươi kho thô (`quan_decay_per_s = 0.25/s`, tức `-1` đơn vị/tick, kẹp `0`)** trên TẤT CẢ cá thể trong `self.stock` (kể cả đang `reserved`; món đang nấu/chín/cầm tay không hao). Cá thể nào đi từ `>= 30` xuống `< 30` (so trước làm tròn, tức `< 7200`) phát `("spoiled", {"item_id", "kind", "location": "stock"})` theo `id_key(item["id"])`.
     3. **Sau khi phát hết mọi `spoiled` của tick:** tìm các khách có `order_status == "reserved"` mà `reserved` chứa ít nhất 1 `id` vừa ươn. Sắp các đơn bị ảnh hưởng theo `(c["order_tick"], id_key(c["table_id"]))`. Với từng đơn: nhả toàn bộ `c["reserved"]`, thử chọn lại 1 lần từ các cá thể khả dụng (`not spoiled` và chưa nằm trong `reserved` của đơn khác), mỗi loại theo thứ tự `(-fresh_units, id_key(id))` (tươi nhất, hòa `id` nhỏ). Đủ -> cập nhật `c["reserved"]` (mảng ID sắp theo `id_key`); thiếu -> `c["reserved"] = []`, `c["order_status"] = "unfulfillable"` (khách vẫn chờ tới hết kiên nhẫn).
     4. `_move` và `_handle_interact`: khi bếp `idle` lấy đơn `reserved` cũ nhất `(order_tick, id_key(table_id))`, **tiêu đúng các ID trong `customer["reserved"]`** khỏi `self.stock`; tính `avg_fresh = sum(it["_units"] / FRESH_SCALE for it in used) / len(used)`, chốt `base_price = math.floor(self.menu[dish_id]["price"] * avg_fresh / 100.0)`; `cook_started.data.items` là mảng cá thể sạch `[{"id", "kind", "fresh"}, ...]` sắp theo `(it["kind"], id_key(it["id"]))`. Khi `served`, `tip = math.floor(base_price * tip_rate)` tính trên `base_price` đã chốt.
     5. Thanh toán (`paid`), khách hết kiên nhẫn (`customer_left`), đón khách mới tại `120 + 900 * k` (lọc `day_plan` trước rồi lọc món có đủ cá thể chưa ươn & chưa giữ chỗ, giữ chỗ bằng mảng ID tươi nhất hòa `id_key`).
2. **`chonoi/scenario.py` (`_validate_quan`, `prepare_quan_customers`):**
   - `quan.stock`: mảng cá thể v1.2 (`validate_items_v12`).
   - `customers[].reserved`: mảng `id` cá thể (khi `order_status == "reserved"`, mỗi `id` phải tồn tại trong `stock`, chưa ươn `< 30`, không trùng giữa các đơn, đếm số lượng theo `kind` khớp đúng `menu[dish]["recipe"]`; khi vắng `"reserved"` ở fixture có `stock`, tự cấp theo `(order_tick, id_key(table_id))` lấy tươi nhất hòa `id_key`, thiếu → `BadInput` mã `2`). Kiểm `id` vật lý duy nhất xuyên nơi chứa.
3. **Bật v1.2 & Bằng chứng QA (`docs/verification/phase-3.md`, `docs/proof/phase-3/`):**
   - Chạy smoke 2 tiến trình (`gather --inventory-out` -> `quan --inventory --ticks 0`) khớp từng byte/cá thể (`docs/proof/phase-3/integration.md`).
   - Kiểm tra file kho đếm v1.0/v1.1 trả mã `2` trước khi ghi file.

### 4. Phạm vi sở hữu & File KHÔNG ĐƯỢC SỬA
- **Được phép sửa/tạo:** `chonoi/sim/quan.py`, `chonoi/scenario.py` (`_validate_quan`, `prepare_quan_customers`), `game.contract.json` (chỉ đổi `"contract_version": "1.2"` khi tích hợp xong Slice 3), `tests/test_quan_freshness_v12.py` (mới), thích nghi `tests/test_quan_customers.py`, `tests/test_quan_service.py`, `tests/test_quan_v11.py`, `tests/test_smoke_p1.py` (kèm lý do commit), `docs/verification/phase-3.md`, `docs/proof/phase-3/*`, `docs/ai-usage-log.md`.
- **KHÔNG sửa:** `chonoi/sim/gather.py`, `chonoi/sim/monsters.py`, `chonoi/sim/day.py`, `chonoi/sim/shop.py`, `chonoi/web/`, `CHANGELOG.md`, `docs/retro.md`.

### 5. Kiểm tra & Quy trình Git
- Tạo **≥ 3 commit rõ ràng** bằng tài khoản `Limdim1604`; chạy `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v` và `python tools/check_team.py`, mở PR #3 vào `main`.
````

---

## Prompt 4 — Nguyễn Tấn Châu (`Lmeo2h` · MSSV `2A202603846`)
**Slice 4:** `ShopSim` / `runner` v1.2 + HUD Độ tươi/Hàng ươn + `CHANGELOG.md` + Retro & Tag `phase-3` · **Vai:** Integrator · **Nhánh Git:** `feat/p3-s4-shop-ui-changelog`

````markdown
Bạn là AI coding agent hỗ trợ **Nguyễn Tấn Châu (`Lmeo2h` — MSSV `2A202603846`)**, vai **Integrator** của nhóm **BCDQ** (dự phòng cho `Limdim1604`).

### 1. Nhánh Git & Mục tiêu Slice 4 + Tích hợp `phase-3`
- Tạo nhánh `feat/p3-s4-shop-ui-changelog` từ `main` (làm phần UI/Shop/CHANGELOG song song ngay; rebase sau khi Slice 3 merge).
- Mục tiêu:
  1. Cập nhật `chonoi/sim/shop.py` (giữ `stock` dạng mảng cá thể v1.2, không hao tươi trong Shop) & `chonoi/runner.py` (truyền `contract_version`/hỗ trợ ghi kho v1.2).
  2. Nâng cấp `chonoi/web/index.html` hiển thị rõ **độ tươi (`%` / thanh màu)** và **nhận diện hàng ươn (`< 30`)** cho giỏ (`hold`) và kho quán (`stock`), đảm bảo `>= 18px sans-serif` tại `1280x720`, `>= 30 FPS`, tắt hoàn toàn trong `headless`.
  3. Viết `tests/test_v12_handoff_ui.py` (và thích nghi `tests/test_day_shop_pause.py` theo v1.2), tạo **`CHANGELOG.md`** (ghi breaking change v1.2, schema kho cá thể và cách cập nhật fixture), cập nhật `AGENTS.md`, `docs/retro.md` (Phase 3 nhanh), chạy cổng cuối và gắn tag **`phase-3`** trước **`2:30`**.

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md`, `TEAM.md`, `docs/plan/phase-3.md`, `docs/retro.md`
2. `specs/003-phase-3-freshness/spec.md`, `specs/003-phase-3-freshness/plan.md`, `specs/003-phase-3-freshness/tasks.md`
3. `chonoi/sim/shop.py`, `chonoi/runner.py`, `chonoi/headless.py`, `chonoi/live.py`, `chonoi/web/index.html`, `chonoi/inventory.py`
4. `tests/test_day_shop_pause.py`, `tests/test_live.py`

### 3. Quy tắc TICKET-03 bắt buộc cho Slice 4
1. **`chonoi/sim/shop.py` & `chonoi/runner.py`:**
   - `ShopSim.__init__` nhận `stock` dạng list cá thể `[{"id", "kind", "fresh"}, ...]` (hoặc copy sạch không kèm `_units`), `snapshot()["stock"]` trả về nguyên danh sách cá thể đó mà **không hao tươi** trong `ShopSim.step`.
   - Kiểm tra `runner.py` và `headless.py` (chỉ sửa nếu cần): đảm bảo `write_inventory_if_done` ghi đúng v1.2 `[{"id", "kind", "fresh"}]` và `read_inventory` từ chối file kho đếm cũ với mã `2`.
2. **HUD Độ tươi & Hàng ươn (`chonoi/web/index.html`):**
   - Trong HUD `gather`: hiển thị giỏ (`hold`) kèm độ tươi từng cá thể (ví dụ `Ca linh 99%`, thanh màu xanh/vàng/đỏ) và đánh dấu rõ hàng ươn `< 30` (ví dụ nhãn `[ƯƠN]` / màu đỏ xám).
   - Trong HUD `quan` & `EveningIntro`/`Shop`: hiển thị `stock` cá thể kèm độ tươi và trạng thái ươn (`< 30`), đếm số cá thể tươi khả dụng.
   - Giữ nguyên chuẩn `sans-serif >= 18px` ở `1280x720`, `>= 30 FPS`, không ảnh hưởng `headless`.
3. **`CHANGELOG.md`, `AGENTS.md` & `docs/retro.md`:**
   - Tạo `CHANGELOG.md` ở gốc repo: mục `## [1.2.0] - Phase 3 (TICKET-03)` ghi rõ Breaking Change (đổi `items` từ map đếm sang mảng cá thể `{id, kind, fresh}`, `customers[].reserved` từ map sang mảng ID, `cook_started.items` và `lost` sang mảng cá thể, quy tắc hao tươi/ngưỡng 30/chốt giá), và hướng dẫn chuyển fixture từ v1.1 sang v1.2.
   - Cập nhật `AGENTS.md` (Test Contract `v1.2`, quy ước `FRESH_SCALE=240` và kiểm `CHANGELOG.md`).
   - Điền mục `## Phase 3 (nhanh)` trong `docs/retro.md` (Điều tốt / Điều tệ / 1 hành động cho Phase 4).

### 4. Phạm vi sở hữu & File KHÔNG ĐƯỢC SỬA
- **Được phép sửa/tạo:** `chonoi/sim/shop.py`, `chonoi/runner.py`, `chonoi/web/index.html`, `tests/test_v12_handoff_ui.py` (mới), thích nghi `tests/test_day_shop_pause.py`, `CHANGELOG.md` (mới), `AGENTS.md`, `docs/retro.md`, `docs/ai-usage-log.md`.
- **KHÔNG sửa:** `chonoi/sim/gather.py`, `chonoi/sim/monsters.py`, `chonoi/sim/quan.py`, `chonoi/sim/day.py`, `chonoi/scenario.py`.

### 5. Lệnh kiểm tra cuối & Gắn tag `phase-3` (trước `2:30`)
```powershell
$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v
python tools/check_team.py
Measure-Command { python -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out out_p3_bench.jsonl }
Remove-Item out_p3_bench.jsonl
git checkout main
git pull origin main
git tag phase-3
git push origin phase-3
```
- Tạo **≥ 3 commit rõ ràng** bằng tài khoản `Lmeo2h`, mở PR #4 vào `main`, hoàn tất merge + `docs/verification/phase-3.md` + gắn tag `phase-3` trước **`2:30`**.
````
