# Feature Specification: Quán Ăn Chợ Nổi — Phase 3: Mùa Nước Nổi — Độ tươi & Kho cá thể (TICKET-03)

**Feature Branch**: `003-phase-3-freshness`

**Created**: 2026-11-21

**Status**: Draft

**Milestone / Contract**: Phase 3 (TICKET-03, Test Contract `v1.2`, cửa sổ 35 phút `1:55–2:30`, tag `phase-3` trước `2:30`)

**Input**: TICKET-03 — Change Request "Mùa Nước Nổi": nâng cấp Test Contract `v1.2`, chuyển schema kho từ đếm theo loại sang **kho cá thể** `{"items":[{"id","kind","fresh"}]}`, cấp ID `I1, I2, ...` tăng liên tục xuyên pha và Ngày, hao tươi chính xác bằng số nguyên (`240` đơn vị/điểm tươi: `gather` `-0.5/s`, `quan` `-0.25/s`), ngưỡng ươn `< 30` và sự kiện `spoiled`, giữ chỗ theo `id` (và thử giữ lại 1 lần khi hàng vừa ươn → `unfulfillable`), chốt `base_price` theo trung bình độ tươi khi nấu, HUD độ tươi/hàng ươn, `CHANGELOG.md` và bộ kiểm chứng `phase-3`.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Contract v1.2, Schema Kho Cá Thể & Độ Tươi `gather` (`duyhale95` — Hà Lê Duy, dự phòng `missher03`) (Priority: P1)

Hệ thống chuyển đổi hợp đồng dữ liệu sang **Test Contract v1.2**: mọi file kho, giỏ hàng (`hold`) và kho quán (`stock`) đều lưu theo **từng cá thể** `{"id", "kind", "fresh"}` với `fresh ∈ [0, 100]`. Khi Út Sen bắt cá hoặc hái nút ở buổi sáng (`gather`), mỗi nguyên liệu thu được là một cá thể mới mang `fresh: 100` và ID `I1, I2, ...` tăng liên tục. Các cá thể đã có trong giỏ hao tươi `0.5/s` ngay đầu mỗi bước mô phỏng (`pause` dừng hao tươi), và phát sự kiện `spoiled` đúng một lần khi vượt ngưỡng từ `>= 30` xuống `< 30` (kiểm tra trước làm tròn). File kho đếm theo kiểu cũ (`{"items": {"ca_loc": 1}}`) bị từ chối với mã thoát `2`.

**Why this priority**: Schema kho cá thể v1.2 và bộ biểu diễn độ tươi chính xác (`240` đơn vị mỗi điểm tươi) là nền móng thay đổi cấu trúc toàn dự án; mọi module (`monsters`, `day`, `quan`, `shop`, `scenario`, `web`) đều phụ thuộc vào hợp đồng dữ liệu này.

**Independent Test**: Có thể kiểm thử độc lập bằng `chonoi.inventory`, `chonoi.contract`, và `chonoi.headless --mode gather`: (1) đọc/ghi file kho v1.2, trả mã `2` cho file kho đếm v1.0/v1.1 hoặc `id` trùng/`fresh` ngoài `[0, 100]`; (2) bắt cá `ca_linh` (`yield = 3`) tạo 3 cá thể `I1, I2, I3` với `fresh = 100` không hao ở bước vừa bắt và bắt đầu hao `0.5/s` từ bước sau; (3) fixture `{"id":"I1","kind":"ca_linh","fresh":30}` phát đúng `spoiled` tại tick `1` ở `location: "hold"`; (4) ghi file `--inventory-out` nguyên tử theo `id` đủ độ chính xác cho ngưỡng 30.

**Acceptance Scenarios**:

1. **Given** `game.contract.json` mang `contract_version: "1.2"` và khối `freshness: {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}`, **When** chạy `chonoi.headless` hoặc gọi `read_inventory`, **Then** chấp nhận schema `{"items": [{"id": "...", "kind": "...", "fresh": ...}]}` (rỗng là `{"items": []}`), từ chối file kho đếm cũ (`{"items": {"ca_loc": 1}}`), `id` trùng/rỗng, `kind` lạ, `fresh` không hữu hạn hoặc ngoài `[0, 100]` bằng `BadInput` (mã thoát `2` trước khi ghi file đầu ra).
2. **Given** `GatherSim` đang chạy với các cá thể trong `hold`, **When** bắt đầu mỗi tick không tạm dừng, **Then** các cá thể đã tồn tại trong `hold` giảm `0.5 / 60` độ tươi mỗi tick (kẹp đáy `0`); cá thể nào chuyển từ `>= 30` xuống `< 30` (kiểm trước làm tròn) phát đúng một sự kiện `("spoiled", {"item_id": id, "kind": kind, "location": "hold"})` theo thứ tự `id_key`; nguyên liệu mới hái/bắt trong bước đó nhận `fresh = 100`, cấp ID `I1, I2, ...` theo thứ tự vào giỏ và chỉ bắt đầu hao tươi từ bước kế tiếp.
3. **Given** scenario `{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":30}],"random_fish":false,"monsters":[]}}`, **When** chạy `chonoi.headless --mode gather --ticks 1`, **Then** tại tick `1` phát `{"type":"event","tick":1,"phase":"gather","name":"spoiled","data":{"item_id":"I1","kind":"ca_linh","location":"hold"}}`; và khi cập bến (`gather_end`), `gather_end.data.inventory` và `--inventory-out` xuất đúng mảng cá thể sắp theo `id` với độ chính xác giữ nguyên nhánh ngưỡng `30` khi đọc lại.

---

### User Story 2 - Rơi Hàng LIFO Cá Thể (`monsters`) & ID Liên Tục Xuyên Pha/Ngày (`day`) (`missher03` — Nguyễn Văn Quốc, dự phòng `duyhale95`) (Priority: P1)

Khi va chạm Cá Sấu Năm Chèo (`monster_hit`) hoặc ngất (`faint`), các nguyên liệu rơi khỏi giỏ vẫn giữ nguyên thứ tự **LIFO** theo đúng thứ tự vào giỏ, nhưng trường `lost` trong sự kiện nay là mảng **cá thể** `[{"id", "kind", "fresh"}, ...]` mang đúng độ tươi hiện tại ở thời điểm rơi. Trong chế độ nhiều ngày (`--mode day`), bộ cấp phát ID `I1, I2, ...` được duy trì liên tục xuyên suốt các pha và các Ngày (không bao giờ cấp lại ID cũ kể cả khi cá thể đã bị nấu, mất hoặc bỏ sau Shop); tại tick chuyển pha `gather -> quan`, hàng bàn giao giữ nguyên số lượng, ID và độ tươi (kể cả hàng ươn), không hao thêm trong tick chuyển pha.

**Why this priority**: Đảm bảo tính nhất quán của định danh vật lý cá thể qua `monster_hit`/`faint` và qua chu trình `gather -> quan -> shop -> Ngày kế` trong `DaySim`.

**Independent Test**: Có thể kiểm thử độc lập bằng `tests/test_monsters_day_v12.py` và headless `--mode day --days 2`: (1) `monster_hit` rơi `floor(len(hold) * 0.5)` cá thể cuối cùng giữ nguyên `id` và `fresh` đúng tick va chạm, `faint` xuất phần còn lại theo LIFO; (2) sang Ngày 2 trong `--mode day`, cá thể mới bắt trong `gather` tiếp tục nhận ID sau ID lớn nhất đã cấp ở Ngày 1 (không reset về `I1`), và Ngày 1 giữ nguyên ID trong `scenario.gather.hold`.

**Acceptance Scenarios**:

1. **Given** Út Sen đang mang danh sách cá thể trong `hold` và bị cá sấu đánh trúng (`monster_hit`) hoặc ngất (`faint`), **When** xử lý rơi hàng, **Then** pop `floor(len(hold) * 0.5)` phần tử cuối cùng (hoặc toàn bộ nếu `hp == 0`) theo LIFO, trả về trong `lost` dưới dạng mảng dict cá thể `{"id", "kind", "fresh"}` với độ tươi chính xác ở bước hiện tại.
2. **Given** chiến dịch `--mode day --days 2` bắt đầu với `scenario.gather.hold` có `[{"id": "I10", ...}]` hoặc thu thập được `I1..I3` ở Ngày 1, **When** chuyển sang `quan` cùng ngày rồi sang `shop` và sang Ngày 2 `gather`, **Then** `gather -> quan` bàn giao nguyên mảng cá thể (kể cả hàng `< 30`) với không thêm tick hao tươi ở tick chuyển pha; sang Ngày 2 mọi hàng thu mới tiếp tục được cấp `I11, I12...` (hoặc `I4, I5...`) không trùng ID đã dùng; nếu mẫu có `gather.hold` cho Ngày 2+ thì cấp ID mới theo thứ tự mảng với `kind`/`fresh` ban đầu.

---

### User Story 3 - Hao Tươi Quán, Giữ Chỗ Theo `id`, Chốt Giá Theo Tươi & Kiểm Scenario v1.2 (`Limdim1604` — Nguyễn Thiên Bảo, dự phòng `Lmeo2h`) (Priority: P1)

Buổi tối (`quan`), toàn bộ nguyên liệu thô trong `stock` (kể cả đang được giữ chỗ) hao tươi `0.25/s` mỗi tick ở đầu bước (trước khi xử lý nấu/phục vụ). Cá thể nào giảm từ `>= 30` xuống `< 30` phát `spoiled(location="stock")` theo thứ tự `id`. Mỗi đơn khách hàng giữ chỗ bằng mảng **`id` cá thể** (`customers[].reserved = ["I1", ...]`), chọn các cá thể chưa ươn tươi nhất (hòa theo `id`). Nếu một cá thể đang giữ vừa bị ươn trong tick đó, sau khi phát hết `spoiled`, quán nhả toàn bộ phần giữ của đơn đó và thử giữ lại đúng 1 lần theo thứ tự `(order_tick, id_key(table_id))`; nếu thiếu thì chuyển đơn sang `unfulfillable` (khách vẫn chờ tới hết kiên nhẫn). Khi bếp bắt đầu nấu (`cook_started`), quán tiêu đúng các `id` đang giữ và chốt `base_price = floor(giá niêm yết × trung bình fresh / 100)`; tiền boa (nếu có) cũng tính `floor(base_price * 0.2)` trên giá đã chốt.

**Why this priority**: Hiện thực hóa toàn bộ logic kinh tế cốt lõi của TICKET-03 ở buổi tối (độ tươi ảnh hưởng trực tiếp đến khả năng nấu và doanh thu/điểm) cùng bộ validator chặt chẽ trong `chonoi/scenario.py` và bảo chứng QA Phase 3.

**Independent Test**: Có thể kiểm thử độc lập bằng `tests/test_quan_freshness_v12.py` và headless `--mode quan`: (1) hao `0.25/s` trên `stock`, phát `spoiled` đúng tick; (2) 2 đơn bị ươn cùng lúc xử lý lại theo `(order_tick, id_key(table_id))`, đơn giữ lại thành công vs đơn thành `unfulfillable`; (3) chọn tươi nhất hòa `id`; (4) `cook_started.data.items` sắp theo `(kind, id)`, `base_price` và `tip` làm tròn `floor` theo độ tươi; (5) `scenario.py` bắt mọi lỗi trùng `id` giữa nơi chứa, trỏ vào hàng ươn, thiếu công thức, hoặc `base_price` sai bằng mã `2`.

**Acceptance Scenarios**:

1. **Given** quán có các cá thể trong `stock` (gồm hàng đang `reserved` và hàng tự do), **When** mỗi bước chạy (không tạm dừng), **Then** sau bước giảm timer, toàn bộ cá thể trong `stock` giảm `0.25 / 60` độ tươi; cá thể chuyển từ `>= 30` xuống `< 30` phát `("spoiled", {"item_id", "kind", "location": "stock"})` theo thứ tự `id_key`.
2. **Given** trong tick có ít nhất 1 cá thể vừa ươn đang nằm trong `customers[].reserved`, **When** tất cả sự kiện `spoiled` của tick đã được phát xong, **Then** duyệt các đơn `reserved` bị ảnh hưởng theo `(order_tick, id_key(table_id))`: nhả toàn bộ `reserved` của đơn đó rồi thử giữ lại đúng 1 lần từ các cá thể khả dụng (`fresh >= 30`, chưa giữ bởi đơn khác), ưu tiên tươi nhất rồi `id_key` nhỏ nhất; nếu không đủ công thức thì chuyển `order_status = "unfulfillable"` và giữ `reserved = []`.
3. **Given** bếp `idle` bắt đầu nấu cho đơn `reserved` cũ nhất, **When** `cook_started` xảy ra, **Then** tiêu thụ đúng các cá thể trong `reserved`, phát `items` là mảng cá thể sắp theo `(kind, id_key(id))`, và chốt `base_price = floor(menu[dish_id]["price"] * mean_fresh / 100)`; khi giao món đủ kiên nhẫn (`>= 50%`), `tip = floor(base_price * tip_rate)`.
4. **Given** scenario truyền `gather.hold`, `quan.stock`, hoặc `customers[].reserved` sai schema v1.2 (trùng `id` vật lý giữa `stock`/`reserved`/nơi chứa, `reserved` trỏ vào `id` ươn `< 30` hoặc không tồn tại, không khớp công thức, dùng chung 1 `id` cho 2 đơn), **When** nạp scenario, **Then** `chonoi/scenario.py` ném `BadInput` và thoát mã `2` trước khi ghi file đầu ra.

---

### User Story 4 - HUD Độ Tươi/Hàng Ươn, `ShopSim`/`runner` v1.2, `CHANGELOG.md` & Tag `phase-3` (`Lmeo2h` — Nguyễn Tấn Châu, dự phòng `Limdim1604`) (Priority: P1)

`ShopSim` và `Session`/`runner` truyền và giữ nguyên danh sách cá thể (`stock` ở Shop không bị hao tươi, `item_ids` xuyên pha/Ngày được bảo toàn qua `runner`/`DaySim`). Trên cửa sổ chơi trực tiếp (`chonoi/web/index.html`), HUD hiển thị rõ độ tươi của từng nguyên liệu trong giỏ (`hold`) và trong kho quán (`stock`) bằng số/thanh và đánh dấu rõ hàng ươn (`< 30`) mà vẫn giữ chữ không chân `>= 18px` tại `1280x720` và tốc độ `>= 30 FPS` (tắt hoàn toàn trong `headless`). Đồng thời, hoàn tất `CHANGELOG.md` ghi rõ breaking change v1.2 và hướng dẫn chuyển fixture, cập nhật `AGENTS.md`, `docs/retro.md` và gắn tag `phase-3` trước `2:30`.

**Why this priority**: Hoàn thiện vòng khép kín v1.2 từ mô phỏng → file/day handoff → giao diện người chơi, đồng thời khóa sổ tài liệu bàn giao (`CHANGELOG.md`, `AGENTS.md`, `docs/retro.md`, tag `phase-3`).

**Independent Test**: Có thể kiểm thử độc lập bằng `tests/test_v12_handoff_ui.py` + `tests/test_live.py`: (1) smoke bàn giao 2 tiến trình `gather --inventory-out` -> `quan --inventory --ticks 0` khớp từng cá thể; (2) `ShopSim` giữ nguyên `stock` cá thể và không làm hao tươi qua 600 ticks; (3) `chonoi/web/index.html` dựng HUD độ tươi/hàng ươn không lỗi JS và vẫn `headless`-clean; (4) `CHANGELOG.md` đầy đủ mục v1.2, `22,200` ticks `<= 20s`, `check_team.py` xanh.

**Acceptance Scenarios**:

1. **Given** chạy `gather` với `hold` có `{"id":"I1","kind":"ca_linh","fresh":100}` và `interact:true` ở tick 0 (`--inventory-out`), rồi mở `quan --inventory` tại `--ticks 0`, **When** đối chiếu snapshot tick 0 của quán với file kho ghi ra, **Then** danh sách cá thể `id`, `kind`, `fresh` khớp chính xác; và ở `ShopSim` trong `--mode day`, `snapshot()["stock"]` giữ nguyên mảng cá thể từ cuối `quan` mà không hao tươi trong Shop.
2. **Given** người chơi mở `chonoi.live --mode gather|quan|day`, **When** quan sát HUD trong `gather` và `quan`, **Then** thấy được độ tươi (số `%` hoặc thanh màu) của nguyên liệu trong giỏ/kho và nhận diện rõ cá thể đã ươn (`< 30`) bằng nhãn/màu/biểu tượng; toàn bộ mã UI nằm ngoài `headless`.
3. **Given** kết thúc Phase 3, **When** kiểm tra repo trên `main`, **Then** có `CHANGELOG.md` ghi rõ breaking change v1.2 và cách chuyển fixture, `AGENTS.md` cập nhật lệnh/quy ước v1.2, `docs/retro.md` có mục Phase 3 nhanh, toàn bộ `unittest discover` + `check_team.py` + benchmark `22,200` ticks (`<= 20s`) + byte determinism đều đạt và tag `phase-3` được đẩy trước `2:30`.

---

### Edge Cases

- **Thứ tự hao tươi & pause**: Nếu tick có cạnh lên `pause` chuyển sang trạng thái tạm dừng, mọi bước mô phỏng (bao gồm hao tươi ở cả `gather` và `quan`) bị đóng băng hoàn toàn; khi nhấn `pause` để tiếp tục (`resumed`), tick đó chạy lại bình thường kể cả hao tươi.
- **Hàng mới bắt/hái ở `gather` hoặc mua từ Chợ (nếu có)**: Cá thể mới vào giỏ trong bước 4 (`interact`) hoặc bước 5 (`catch`) có `fresh = 100` và **chỉ bắt đầu hao từ bước sau** (vì bước hao tươi của giỏ nằm ở bước 1 đầu tick).
- **Độ chính xác ngưỡng `30` (`240` units)**: Dùng số nguyên `240` đơn vị cho `1.0` điểm tươi (`100` = `24000`, `30` = `7200`, gather `-2/tick`, quán `-1/tick`); kiểm ươn `< 7200` (trước làm tròn) giúp `30.0` (`7200`) chạm ngưỡng `< 30` ở ngay tick 1 (`7198 < 7200` hoặc `7199 < 7200`), và sau `round(units / 240, 6)` khi ghi `--inventory-out` đọc lại vẫn phân biệt rạch ròi `< 30` với `>= 30`.
- **Nhiều cá thể cùng ươn & nhiều đơn bị ảnh hưởng trong cùng 1 tick ở `quan`**:
  1. Phát toàn bộ sự kiện `spoiled` theo thứ tự `id_key(item["id"])` trước.
  2. Sau đó mới lọc các đơn `order_status == "reserved"` có chứa ít nhất 1 ID vừa ươn, sắp theo `(order_tick, id_key(table_id))`.
  3. Mỗi đơn bị ảnh hưởng nhả toàn bộ danh sách `reserved` hiện tại rồi thử giữ lại 1 lần từ kho khả dụng (`fresh >= 30`, chưa giữ bởi đơn nào) theo `(-fresh, id_key(id))` (tức tươi nhất trước, hòa chọn `id` nhỏ hơn); nếu không đủ nguyên liệu chưa ươn thì chuyển `order_status = "unfulfillable"` (khách vẫn chờ cho đến khi hết `patience_ticks_left`, khi rời mới trừ uy tín như khách thường hết kiên nhẫn).
- **Tiêu thụ ở bếp & `base_price`**: Bếp lấy đúng các ID trong `customer["reserved"]` (không tự đổi sang ID khác lúc bắt đầu nấu); `base_price = math.floor(list_price * (sum(fresh) / len(items)) / 100)` — chú ý tính trên giá trị `fresh` chính xác (`units / 240`), sau đó mới `math.floor`. Nếu làm tròn `tip`, tính `math.floor(base_price * tip_rate)` trên `base_price` đã chốt.
- **Độ dài `hold` khi có hàng ươn**: Hàng ươn (`fresh < 30`) trong `hold` vẫn chiếm `1` ô trong `hold_capacity` (`12`) và vẫn tham gia rơi LIFO khi trúng cá sấu hoặc ngất.
- **Ngoài phạm vi lõi (Deferred cho nhóm 4 người)**: Hai mục mở rộng trong TICKET-03 (`Dòng nước lũ current` và `Khách đặt trước reservations`) không bắt buộc với nhóm 4 người và chỉ cân nhắc nếu 100% DoD lõi v1.2 đã xong sớm trước `2:25`.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (Contract v1.2 & Kho Cá Thể — US1)**: Nâng `game.contract.json` lên `contract_version: "1.2"`, bổ sung `tuning.freshness` (`initial: 100`, `gather_decay_per_s: 0.5`, `quan_decay_per_s: 0.25`, `spoiled_below: 30`); `chonoi/inventory.py` hỗ trợ schema `{"items": [{"id", "kind", "fresh"}]}` với độ chính xác `240` đơn vị/điểm tươi (`FRESH_SCALE = 240`), từ chối kho đếm v1.0/v1.1 và dữ liệu sai bằng mã thoát `2` trước khi ghi file đầu ra.
- **FR-002 (Độ tươi & Ngưỡng ươn trong `GatherSim` — US1)**: `GatherSim` quản lý `hold` dưới dạng mảng cá thể; cấp ID `I1, I2, ...` từ `IdAllocator` chia sẻ xuyên pha/Ngày; đầu mỗi bước (không tạm dừng) giảm `0.5/s` cho hàng đang có trong `hold`, kẹp `0`, phát `spoiled(item_id, kind, location="hold")` theo `id_key` đúng 1 lần khi đi từ `>= 30` xuống `< 30`; hàng mới bắt/hái mang `fresh = 100` và bắt đầu hao từ bước sau; `gather_end.data.inventory` và `--inventory-out` xuất theo schema v1.2 (sắp theo `id_key`).
- **FR-003 (LIFO cá thể & ID liên tục trong `DaySim` — US2)**: `chonoi/sim/monsters.py` phát `monster_hit.lost` và `faint.lost` là mảng cá thể theo thứ tự LIFO giữ nguyên độ tươi lúc rơi; `chonoi/sim/day.py` duy trì bộ cấp ID `I1, I2, ...` liên tục xuyên pha và các Ngày (Ngày 1 giữ nguyên ID trong `scenario.gather.hold`, Ngày 2+ cấp ID mới theo thứ tự mảng nếu có `hold`), bàn giao `gather -> quan` cùng tick không hao thêm, không hao tươi ở `ShopSim`.
- **FR-004 (`QuanSim` Độ tươi, Giữ chỗ theo `id` & Giá theo tươi — US3)**: `QuanSim` quản lý `stock` theo cá thể, hao `0.25/s` toàn bộ kho thô (gồm hàng đang giữ chỗ) sau giảm timer; phát hết `spoiled(item_id, kind, location="stock")` theo `id_key` trước khi xét giữ chỗ lại; với các đơn `reserved` có hàng vừa ươn, xử lý theo `(order_tick, id_key(table_id))` nhả và thử giữ lại đúng 1 lần theo tươi nhất (`-fresh`, `id_key`), thiếu → `unfulfillable`; khi `cook_started` tiêu đúng các `id` giữ, phát `items` sắp theo `(kind, id_key(id))` và chốt `base_price = floor(price * avg_fresh / 100)`; `tip` tính trên `base_price` đã chốt.
- **FR-005 (Scenario & JSONL v1.2 — US1, US3)**: `chonoi/scenario.py` xác thực `gather.hold[]`, `quan.stock[]` dạng cá thể và `customers[].reserved` dạng mảng `id` cá thể; đảm bảo `id` vật lý duy nhất giữa các nơi chứa, trỏ đúng cá thể chưa ươn, đủ công thức, không dùng chung, `base_price` hợp lệ; mọi sai lệch thoát mã `2` trước khi ghi output.
- **FR-006 (HUD Độ tươi & Tài liệu chuyển đổi — US4)**: `chonoi/web/index.html` hiển thị độ tươi/nhãn ươn trên `hold` và `stock` (`>= 18px sans-serif` ở `1280x720`, `>= 30 FPS`, tắt ở `headless`); `CHANGELOG.md` ghi rõ breaking change v1.2 và hướng dẫn chuyển fixture; `AGENTS.md`, `docs/clarify.md`, `docs/retro.md`, `docs/verification/phase-3.md` và `docs/proof/phase-3/` đầy đủ trước tag `phase-3`.

### Key Entities

- **Item (`v1.2`)**: `{"id": "I1", "kind": <ingredient>, "fresh": <float in [0, 100]>}` (biểu diễn nội bộ `fresh_units = int(round(fresh * 240))` để tránh sai số dấu phẩy động).
- **Freshness Tuning**: `{"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}`.
- **Reservation (`quan`)**: `customers[].reserved = ["I1", "I2", ...]` (mảng ID cá thể duy nhất đang giữ cho đơn đó).
- **Spoiled Event**: `("spoiled", {"item_id": "I1", "kind": "ca_linh", "location": "hold" | "stock"})`.

---

## Success Criteria *(mandatory)*

- **SC-001**: Toàn bộ bộ test (test mới v1.2 + bộ test P1–P2 đã thích nghi có lý do commit) pass 100% qua `unittest discover -s tests -v`.
- **SC-002**: Smoke 2 tiến trình (`gather --inventory-out` → `quan --inventory --ticks 0`) và chạy `--mode day --days 2..5` khớp chính xác `id`, `kind`, `fresh` qua bàn giao; file kho đếm v1.0/v1.1 bị từ chối với mã thoát `2`.
- **SC-003**: Hai lần chạy `chonoi.headless` cùng `--seed` trên cả 3 mode cho JSONL và file kho giống hệt nhau từng byte; `22,200` ticks/ngày chạy `<= 20s`.
- **SC-004**: `CHANGELOG.md`, `docs/plan/phase-3.md`, `docs/verification/phase-3.md`, `docs/proof/phase-3/`, `docs/retro.md`, `docs/ai-usage-log.md`, `AGENTS.md`, `python tools/check_team.py` và tag `phase-3` hoàn tất đúng hạn `2:30`.
