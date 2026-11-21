# Feature Specification: Quán Ăn Chợ Nổi — Phase 1 Core

**Feature Branch**: `001-phase-1-core`

**Created**: 2026-11-21

**Status**: Draft

**Input**: User description: "Phase 1 (PRD-0): Lõi mô phỏng chế độ buổi sáng (`gather`) và buổi tối (`quan`) chia thành 4 Vertical Slices độc lập cho 4 thành viên nhóm."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - `gather` Slice 1: Sinh tồn dưới nước & Giỏ LIFO (`duyhale95` — Hà Lê Duy) (Priority: P1)

Người chơi điều khiển Út Sen lặn xuống sông trong chế độ `gather` (`d > surface_depth`), tiêu hao oxy mỗi tick, ngoi lên mặt nước (`d <= surface_depth`) để hồi oxy, chịu sát thương ngạt khi hết oxy dưới nước và ngất (`faint`) khi `hp` về 0 (mất toàn bộ giỏ `hold`, xuất kho rỗng); đồng thời quản lý giỏ nguyên liệu theo thứ tự nhặt (LIFO) với sức chứa `hold_capacity`.

**Why this priority**: Sinh tồn dưới nước và quản lý giỏ là vòng lặp cốt lõi của buổi sáng (`gather`); nếu thiếu cơ chế oxy/ngạt/ngất và giỏ `hold`, người chơi không bị rủi ro khi lặn sâu và không có ranh giới lưu trữ nguyên liệu.

**Independent Test**: Có thể kiểm thử độc lập bằng `chonoi.headless --mode gather` với `scenario` thiết lập vị trí `player.pos`, `player.oxygen_ticks`, `player.hp`, `player.zero_oxy_ticks`, `hold` và `inputs` điều khiển `move` lên/xuống để xác minh đầy đủ các sự kiện `dive`, `surface`, `oxygen_empty`, `choke`, `faint`, `gather_end` (`reason = "fainted"`), file kho rỗng và cấu trúc giỏ LIFO.

**Acceptance Scenarios**:

1. **Given** người chơi đang ở mặt nước (`pos[1] <= surface_depth`, tức `at_surface == True`) với `oxygen_ticks < oxygen_max_ticks`, **When** người chơi lặn xuống dưới nước (`pos[1]` cuối bước vượt qua `surface_depth`), **Then** hệ thống phát sự kiện `dive` (data chứa `pos` — chi tiết payload `[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]`) và trừ `oxygen_ticks` đi 1 mỗi tick dưới nước.
2. **Given** người chơi đang ở dưới nước (`pos[1] > surface_depth`), **When** di chuyển lên mặt nước (`pos[1] <= surface_depth` cuối bước), **Then** hệ thống phát sự kiện `surface` (data chứa `pos` — `[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]`) và mỗi tick ở mặt nước hồi `oxygen_ticks` thêm `oxygen_refill_per_tick`, kẹp trong `[0, oxygen_max]` (`oxygen_max = round(oxygen_max_s * 60)`).
3. **Given** người chơi đang dưới nước với `oxygen_ticks > 0`, **When** `oxygen_ticks` giảm từ dương xuống `0`, **Then** hệ thống phát sự kiện `oxygen_empty` (`[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]`).
4. **Given** người chơi đang dưới nước với `oxygen_ticks == 0`, **When** tiếp tục ở dưới nước qua mỗi chu kỳ `choke_interval_ticks` (đếm qua `zero_oxy_ticks`), **Then** hệ thống trừ 1 `hp` và phát sự kiện `choke` (`[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]`).
5. **Given** người chơi có `hp == 1` và bị trừ máu do ngạt xuống `0`, **When** bước tick đó xử lý xong kiểm tra ngạt, **Then** hệ thống làm rỗng `hold`, phát sự kiện `faint` (`[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]`), kết thúc lượt với `gather_end` (`reason = "fainted"`, `inventory = {"items": {}}`) và xuất file kho rỗng nếu có `--inventory-out`.
6. **Given** người chơi có các nguyên liệu trong giỏ `hold`, **When** thêm hoặc thao tác nguyên liệu trên giỏ có sức chứa tối đa `hold_capacity`, **Then** `hold` bảo toàn thứ tự nhặt (cuối mảng là mới nhất — LIFO) và không vượt quá `hold_capacity` (quy tắc thao tác LIFO cụ thể như vứt/lấy phần tử cuối nếu có `[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]`).

---

### User Story 2 - `gather` Slice 2: Thu hoạch mặt nước & Bắt cá (`missher03` — Nguyễn Văn Quốc) (Priority: P1)

Người chơi hái các nút thực vật (`bong_dien_dien`, `bong_sung`) khi ở mặt nước bằng `interact`, lặn xuống bắt các đàn cá (`ca_linh`, `ca_loc`) bằng `catch` có hồi chiêu `catch_cd_ticks`, và quay về vùng bến (`dock_pos`, `dock_radius`) nhấn `interact` (được ưu tiên trước hái) để kết thúc buổi sáng và xuất kho nguyên liệu.

**Why this priority**: Đây là nguồn tạo ra toàn bộ nguyên liệu (`ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`) để chuyển sang chế độ quán buổi tối qua file kho.

**Independent Test**: Có thể kiểm thử độc lập bằng `chonoi.headless --mode gather` với `scenario` đặt `nodes`, `fish`, `hold`, `player.pos` tại bến/nút/đàn cá và `inputs` nhấn `interact`/`catch` để kiểm tra `gather`, `node_regrown`, `fish_caught`, `hold_full`, ưu tiên cập bến trước hái và nội dung `--inventory-out`.

**Acceptance Scenarios**:

1. **Given** người chơi đang ở trong vùng bến (`dist(pos, dock_pos) <= dock_radius`) VÀ đồng thời trong `interact_radius` của một nút hái `ready`, **When** nhấn `interact` (cạnh lên), **Then** hệ thống ưu tiên cập bến trước hái: kết thúc buổi sáng với `gather_end` (`reason = "docked"`) và xuất toàn bộ `hold` hiện tại ra file kho.
2. **Given** người chơi đang ở mặt nước (`_at_surface() == True`), không ở trong vùng bến, và có ít nhất một nút `ready` (`regrow_ticks == 0`) trong `interact_radius`, **When** nhấn `interact`, **Then** hệ thống chọn nút gần nhất (cùng khoảng cách thì chọn `id` nhỏ hơn theo `id_key`); nếu còn chỗ trong `hold` thì thêm `node_yield` phần tử vào `hold`, đặt `regrow_ticks` cho nút theo `regrow_s * 60` và phát `gather`; nếu đầy thì phát `hold_full` (`[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]` cho trường hợp `len(hold) + node_yield > hold_capacity`).
3. **Given** một nút đã bị hái có `regrow_ticks > 0`, **When** bộ đếm giảm về `0` ở đầu tick, **Then** nút trở lại trạng thái `ready = True` và phát sự kiện `node_regrown` (`{"node_id": n["id"]}`).
4. **Given** người chơi đang ở dưới nước (`not _at_surface()`) với `catch_cd_ticks == 0` và có đàn cá trong `catch_radius`, **When** nhấn `catch` (cạnh lên), **Then** hệ thống xử lý bắt cá với `fish_yield[kind]`: nếu thêm được vào `hold` thì cập nhật `hold`, đặt `catch_cd_ticks = round(catch_cooldown_s * 60)` và phát `fish_caught`; nếu giỏ đầy thì phát `hold_full` (`[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]` cho tiêu chí chọn đàn khi nhiều đàn cùng tầm, xử lý đàn cá sau khi bắt và trường hợp vượt một phần `hold_capacity`).
5. **Given** người chơi đang ở mặt nước nhấn `catch`, HOẶC đang ở dưới nước nhấn `interact` gần nút hái, HOẶC đang trong hồi chiêu `catch_cd_ticks > 0`, **When** gửi lệnh tương ứng, **Then** không hái được nút dưới nước và không bắt được cá khi ở mặt nước hoặc đang hồi chiêu.

---

### User Story 3 - `quan` Slice 3: Đón khách, Giữ chỗ, Kiên nhẫn & Kiểm mâu thuẫn scenario (`Limdim1604` — Nguyễn Thiên Bảo) (Priority: P1)

Trong chế độ `quan`, khách tự động đến quán theo lịch (`first_customer_tick`, `customer_interval_s`) ngồi vào bàn trống, chọn một món nấu được từ kho còn dư (sau khi trừ nguyên liệu đang giữ chỗ `reserved` của các khách khác) và giữ chỗ nguyên liệu cho món đó; nếu không còn món nào nấu được thì phát `no_dish`. Khi khách chờ quá `patience_s`, khách bỏ đi (`customer_left`) và làm giảm uy tín theo `left_reputation_delta`. Đồng thời, `chonoi/scenario.py` chặn đầy đủ các mâu thuẫn mức luật ở đầu vào với mã thoát `2`.

**Why this priority**: Phải có vòng đời đón khách, giữ chỗ nguyên liệu nhất quán và validator scenario chặt chẽ thì hệ thống bếp/phục vụ ở Slice 4 mới có đơn hàng hợp lệ và vượt qua được các test hộp đen về mã thoát `2`.

**Independent Test**: Có thể kiểm thử độc lập bằng `chonoi.headless --mode quan` với `--inventory` hoặc `scenario` (gồm các test hợp lệ để đo khách vào bàn, `reserved`, `no_dish`, `customer_left`, `reputation`, và các fixture mâu thuẫn để kiểm tra mã thoát `2` không ghi file đầu ra).

**Acceptance Scenarios**:

1. **Given** quán đang vận hành với bàn trống và kho có nguyên liệu chưa giữ chỗ đủ cho ít nhất một món trong `menu`, **When** đến tick `first_customer_tick` và sau đó mỗi `customer_interval_s * 60` ticks (khi `random_customers` cho phép — `[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]`), **Then** khách mới được tạo với ID từ `IdAllocator` (`reserve()` trước với khách từ scenario), ngồi vào bàn trống, chọn một món nấu được từ kho khả dụng (`stock - tổng reserved`), giữ chỗ đúng phần nguyên liệu theo `menu[dish_id]["recipe"]` vào `reserved` của khách (`[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]` cho quy tắc chọn bàn/món và sự kiện khách đến nếu có).
2. **Given** đến lượt khách mới hoặc khi cần chọn món nhưng không có bàn trống hoặc kho còn dư không đủ nấu bất kỳ món nào trong `menu`, **When** hệ thống kiểm tra điều kiện đón/chọn món, **Then** phát sự kiện `no_dish` khi không có món nấu được (`[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]` cho trường hợp đầy bàn và payload `no_dish`).
3. **Given** khách đang ngồi chờ món với `patience_ticks_left > 0`, **When** mỗi tick trôi qua mà khách chưa được phục vụ tới khi `patience_ticks_left` về `0`, **Then** khách rời bàn, giải phóng chỗ ngồi và nguyên liệu `reserved` (`[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]`), phát sự kiện `customer_left`, và cộng `left_reputation_delta` vào `reputation` (kẹp trong `[reputation_min, reputation_max]`).
4. **Given** file `scenario` của chế độ `quan` chứa dữ liệu mâu thuẫn mức luật (ví dụ: tổng `reserved` vượt quá `stock`, khách dựng sẵn ở trạng thái `assigned` nhưng thiếu/nhiều hơn một món, khách ở trạng thái `eating` nhưng thiếu giá hoặc thông số boa, hoặc các lỗi hợp lệ khác của `customers`/`stoves`/`tables`/`hand`/`reputation`), **When** chạy `chonoi.headless --mode quan --scenario ...`, **Then** `load_scenario` / `QuanSim` từ chối đầu vào với `BadInput` (mã thoát `2`) trước khi ghi bất kỳ file đầu ra nào.

---

### User Story 4 - `quan` Slice 4: Bếp, Phục vụ, Thanh toán & Kết ca (`Lmeo2h` — Nguyễn Tấn Châu) (Priority: P1)

Người chơi di chuyển trong quán và nhấn `interact` để tương tác với bếp hoặc bàn theo thứ tự ưu tiên `(khoảng cách, bếp trước bàn, id nhỏ hơn)`: khởi động bếp nấu món cho đơn đang chờ (`cook_started`), nhận thông báo món chín (`dish_ready`), nhặt món lên tay (`dish_picked`, giới hạn `carry_limit = 1`), bưng ra phục vụ đúng bàn khách (`served`), thu tiền + tiền boa + tăng uy tín khi khách ăn xong (`paid`), và kết thúc ca khi hết giờ (`quan_end`).

**Why this priority**: Hoàn thiện vòng lặp tương tác của người chơi ở buổi tối, tạo doanh thu (`money`, `earned`, `shift_earned`), uy tín (`reputation`) và điểm số (`score`) cuối cùng cho bài chấm headless.

**Independent Test**: Có thể kiểm thử độc lập bằng `chonoi.headless --mode quan` với `scenario` đặt sẵn `stock`, `customers` (đang chờ hoặc đang `eating`), `stoves` (`idle`/`cooking`/`ready`), `hand` và `inputs` di chuyển + nhấn `interact` để kiểm tra ưu tiên đối tượng, `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid`, tính boa/uy tín và `quan_end`.

**Acceptance Scenarios**:

1. **Given** người chơi đứng trong `interact_radius` của nhiều bếp và/hoặc bàn cùng lúc, **When** nhấn `interact` (cạnh lên), **Then** hệ thống thực hiện tối đa MỘT tương tác trên đối tượng có khóa nhỏ nhất theo `(khoảng cách, loại: bếp trước bàn, id theo id_key)`.
2. **Given** đối tượng được chọn là bếp `idle` và có đơn khách đang chờ cần nấu (và `hand` trống — `[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]` cho quy tắc chọn đơn & thời điểm trừ `stock`), **When** nhấn `interact`, **Then** bếp chuyển sang `state = "cooking"`, gán `dish` và `cook_ticks_left = round(menu[dish]["cook_s"] * 60)`, phát sự kiện `cook_started`.
3. **Given** bếp đang ở `state = "cooking"` với `cook_ticks_left > 0`, **When** `cook_ticks_left` đếm ngược về `0`, **Then** bếp chuyển sang `state = "ready"` (`burn_s` là `null` ở Phase 1 nên không cháy) và phát sự kiện `dish_ready`.
4. **Given** bếp đang ở `state = "ready"` và `hand` đang trống (`carry_limit = 1`), **When** nhấn `interact` vào bếp, **Then** món được chuyển lên `hand`, bếp trở về `idle` (`dish = None`), và phát sự kiện `dish_picked`.
5. **Given** người chơi đang cầm món trên `hand` khớp với `dish_id` của khách đang chờ tại bàn được chọn, **When** nhấn `interact` vào bàn đó, **Then** `hand` trở về rỗng, khách chuyển sang `state = "eating"` trong `round(eat_s * 60)` ticks và phát sự kiện `served` (`[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]` cho cách ghi nhận tỉ lệ kiên nhẫn phục vụ để tính boa và trường hợp cầm nhầm món).
6. **Given** khách đang ở `state = "eating"` đến khi ăn xong, **When** hết thời gian `eat_s`, **Then** phát sự kiện `paid`, cộng `price` của món vào `money`/`earned`/`shift_earned`; nếu tỉ lệ kiên nhẫn lúc được phục vụ đạt `>= tip_min_patience_ratio` (`[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]`), cộng thêm tiền boa tính theo `tip_rate` và cộng `tip_reputation` vào `reputation` (kẹp trong `[reputation_min, reputation_max]`); sau đó giải phóng bàn/khách.
7. **Given** `time_left_ticks` giảm về `0` trong `quan`, **When** kết thúc bước tick đó, **Then** `done = True`, `reason = "time"`, và phát sự kiện `quan_end` với `{"reason": "time", "money": money, "earned": earned, "shift_earned": shift_earned, "reputation": reputation}`.

---

### Edge Cases

- **Cập bến vs. Hái nút cùng tầm**: Khi người chơi ở trong `dock_radius` lẫn `interact_radius` của nút hái `ready` và nhấn `interact`, cập bến phải thắng tuyệt đối (`gather_end` `reason="docked"`).
- **Hết giờ vs. Ngất trong cùng một tick (gather)**: Thứ tự xử lý trong `GatherSim.step`: nếu ngạt làm `hp` về `0` ở bước oxy thì `faint` và `gather_end("fainted")` kết thúc ngay (`return events`) trước khi kiểm tra hết giờ hoặc `interact` (`gather.py` dòng 114).
- **Biên vùng chơi**: `gather` chặn `pos` trong `[0, 100] x [0, 30]` (`d >= 0` không bay lên trời), `quan` chặn `pos` trong `[0, 16] x [0, 10]`, triệt tiêu thành phần `vel` hướng ra ngoài mép (đã có trong khung).
- **Không ghi kho khi dừng do `--ticks` (`tick_limit`)**: Nếu hết số `--ticks` CLI trước khi có `gather_end`, `write_inventory_if_done` không ghi `--inventory-out` (đã có trong `runner.py`).
- **Xung đột đầu vào CLI / Scenario**: Vừa có `--inventory` vừa có `quan.stock`, hoặc id trùng, hoặc `table_id` không tồn tại, hoặc scenario sai mode (`gather` vs `quan`) phải thoát mã `2` trước khi ghi bất kỳ file đầu ra nào.
- **Kẹp giá trị uy tín (`reputation`)**: Sau mọi lần cộng `tip_reputation` hoặc `left_reputation_delta`, `reputation` luôn nằm trong `[reputation_min, reputation_max]` (`[0, 5]`).
- **Tương tác nhiều đối tượng trong `quan`**: Một lần nhấn `interact` chỉ kích hoạt tối đa 1 bếp hoặc 1 bàn (không vừa nhặt bếp vừa phục vụ bàn trong cùng 1 tick).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (Tuning & Determinism)**: Toàn bộ tham số thời gian, tọa độ, bán kính, tốc độ, sức chứa, công thức món và thưởng/phạt phải đọc từ `game.contract.json` (`tuning.*`) tại `tick_hz = 60`; mọi yếu tố ngẫu nhiên phải dùng `Streams` (`chonoi/rng.py`), và sắp xếp thực thể qua `ids.sort_by_id` (`chonoi/ids.py`).
- **FR-002 (Oxy & Sinh tồn dưới nước — US1)**: `GatherSim` phải trừ `oxygen_ticks` (1 tick/tick) khi `pos[1] > surface_depth`, hồi `oxygen_refill_per_tick` (kẹp `[0, oxygen_max]`) khi `pos[1] <= surface_depth`; phát `dive` / `surface` khi chuyển vùng đầu-cuối bước; phát `oxygen_empty` khi oxy từ dương về `0`; đếm `zero_oxy_ticks` khi oxy bằng `0` dưới nước và mỗi `choke_interval_ticks` trừ 1 `hp` (phát `choke`); khi `hp` về `0` thì làm rỗng `hold`, phát `faint` và `gather_end` (`reason = "fainted"`).
- **FR-003 (Giỏ LIFO — US1)**: `GatherSim` phải lưu `hold` theo thứ tự nhặt (cuối mảng là mới nhất) với giới hạn `hold_capacity`, phản ánh chính xác qua `hold_count` và `inventory_items()`. *(Chi tiết thao tác bỏ/lấy LIFO ngoài sức chứa, nếu có: `[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]`.)*
- **FR-004 (Thu hoạch mặt nước & Mọc lại — US2)**: Khi nhấn `interact` ngoài vùng bến và đang ở mặt nước (`_at_surface()`), `GatherSim` phải tìm nút `ready` gần nhất trong `interact_radius` (ưu tiên `id` nhỏ hơn khi bằng nhau); hái thêm `node_yield` vào `hold` (phát `gather`, đặt `regrow_ticks = round(regrow_s * 60)`) hoặc phát `hold_full` nếu không đủ chỗ. Khi `regrow_ticks` giảm về `0` phát `node_regrown`.
- **FR-005 (Bắt cá dưới nước & Cập bến — US2)**: Khi nhấn `catch` dưới nước và `catch_cd_ticks == 0`, `GatherSim` phải kiểm tra đàn cá trong `catch_radius` để bắt theo `fish_yield[kind]` (đặt `catch_cd_ticks = round(catch_cooldown_s * 60)`, phát `fish_caught`, hoặc `hold_full` nếu đầy). Khi nhấn `interact` trong vùng bến (`_in_dock()`), luôn ưu tiên kết thúc với `gather_end` (`reason = "docked"`).
- **FR-006 (Đón khách, Giữ chỗ & Kiên nhẫn — US3)**: `QuanSim` phải quản lý khách dựng sẵn và khách đến theo lịch (`first_customer_tick`, `customer_interval_s`), phân bổ bàn trống, chọn món nấu được từ kho chưa bị giữ chỗ (`stock` trừ tổng `reserved`), ghi nhận `reserved` trên khách, phát `no_dish` khi không có món nấu được, giảm `patience_ticks_left` mỗi tick và khi về `0` thì phát `customer_left`, giải phóng bàn/giữ chỗ và cập nhật `reputation` theo `left_reputation_delta`.
- **FR-007 (Kiểm mâu thuẫn scenario — US3)**: `chonoi/scenario.py` (và/hoặc kiểm tra khi dựng sim) phải phát hiện và từ chối bằng `BadInput` (mã thoát `2`, trước khi ghi file đầu ra) các mâu thuẫn mức luật trong `scenario` của `quan` (khách giữ chỗ vượt quá `stock`, đơn trạng thái `assigned` không có đúng một món, khách trạng thái `eating` thiếu giá/thông số boa, cùng các kiểm tra hợp lệ trường `quan` chưa có).
- **FR-008 (Bếp, Phục vụ, Thanh toán & Kết ca — US4)**: Trong `QuanSim`, mỗi lần nhấn `interact` thực hiện tối đa 1 tương tác trong `interact_radius` theo thứ tự `(khoảng cách, bếp trước bàn, id)`. Hỗ trợ đầy đủ luồng `cook_started` -> đếm ngược `cook_ticks_left` -> `dish_ready` -> `dish_picked` (`carry_limit = 1`) -> `served` (`state = "eating"`, đếm `eat_s`) -> `paid` (cộng `price`, xét boa theo `tip_min_patience_ratio` & `tip_rate`, cộng `tip_reputation` kẹp `[reputation_min, reputation_max]`) -> `quan_end` (`reason = "time"`).
- **FR-009 (Các điểm cần đối chiếu PRD-0 trước khi khóa chi tiết)**: Nhóm cần đối chiếu PRD-0 / ghi vào `docs/clarify.md` cho các công thức và payload chưa có trong starter code:
  1. `[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]` Cấu trúc `data` chính xác của các sự kiện chưa cài đặt trong khung: `dive`, `surface`, `oxygen_empty`, `choke`, `faint`, `gather`, `hold_full`, `fish_caught`, `no_dish`, `customer_left`, `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid` (và sự kiện khách mới đến nếu có).
  2. `[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]` Quy tắc `hold` khi sắp vượt `hold_capacity` (`node_yield` hoặc `fish_yield` > chỗ trống còn lại: hái/bắt một phần vừa khít hay từ chối cả lượt + phát `hold_full`?), thao tác LIFO trên `hold` nếu có, và cách reset `zero_oxy_ticks` khi hồi oxy/lên mặt nước.
  3. `[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]` Tiêu chí chọn đàn cá khi nhiều đàn nằm trong `catch_radius`, và đàn cá bị bắt xong có bị xóa khỏi `self.fish` hay có cơ chế khác trong Phase 1.
  4. `[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]` Thứ tự xử lý trong `QuanSim.step`, thuật toán chọn món nấu được từ `menu` + `stock` còn dư (dùng `Streams` hay thứ tự cố định), điều kiện `random_customers`, cấu trúc đầy đủ các trường của từng phần tử trong `customers[]` (`state`, `dish_id`, `patience_ticks_left`, `eat_ticks_left`, `reserved`, v.v.) và `hand` trong `snapshot` cũng như trong `scenario`.
  5. `[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]` Quy tắc bếp khi có nhiều khách chờ (chọn đơn nào để nấu tại bếp `idle`), thời điểm trừ nguyên liệu khỏi `stock`, công thức làm tròn tiền boa (`round`/`int`/`float`) theo `tip_rate`, và quy tắc khi nhấn `interact` vào bàn mà `hand` không khớp món của khách.

### Key Entities *(include if feature involves data)*

- **Player (`gather`)**: `pos` (`[x, d]`), `vel`, `heading_deg`, `oxygen_ticks`, `oxygen_max_ticks`, `hp`, `hp_max`, `zero_oxy_ticks`, `invuln_ticks`, `catch_cd_ticks`, `at_surface`.
- **Hold (`gather`)**: Mảng nguyên liệu theo thứ tự nhặt (`ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`), sức chứa `hold_capacity` (`12`), xuất thành `{"items": {...}}` qua `hold_to_items`.
- **Node (`gather`)**: `id` (`N1`..`N4`), `kind` (`bong_dien_dien`, `bong_sung`), `pos` (`d = 0`), `regrow_ticks`, `ready` (`regrow_ticks == 0`).
- **Fish (`gather`)**: `id` (`F1`..`F6`), `kind` (`ca_linh`, `ca_loc`), `pos` (`d > surface_depth`), `heading_deg`.
- **Player & Hand (`quan`)**: `pos` (`[x, z]`), `vel`, `hand` (tối đa `carry_limit = 1`).
- **Stock & Reserved (`quan`)**: `stock` (nạp từ `--inventory` hoặc `scenario.stock`), `reserved` trên từng khách để giữ chỗ nguyên liệu.
- **Stove (`quan`)**: `id` (`B1`), `pos`, `state` (`idle`, `cooking`, `ready`), `dish`, `cook_ticks_left`, `ready_ticks`.
- **Table & Customer (`quan`)**: Bàn `id` (`T1`), `pos`, `customer_id`; Khách `id`, `table_id`, `dish_id`, `state` (như `eating`, ...), `patience_ticks_left`, `reserved`.
- **Economy & Reputation (`quan`)**: `money`, `earned`, `shift_earned`, `reputation` (trong `[reputation_min, reputation_max]`), `score` (`earned + reputation_multiplier * math.floor(reputation)`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tất cả smoke test hiện có (`tests/test_smoke_p1.py`, `tests/test_python_starter_units.py`) và unit/integration test mới cho cả 4 Vertical Slices chạy xanh 100% qua `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`.
- **SC-002**: Chạy `python3 -m chonoi.headless --mode gather` và `--mode quan` với cùng `--seed`, `--inputs`, `--scenario` 2 lần liên tiếp tạo ra file JSONL và file `--inventory-out` giống hệt nhau từng byte.
- **SC-003**: Toàn bộ các trường hợp scenario mâu thuẫn hoặc sai schema trả về mã thoát `2` trước khi tạo/ghi file đầu ra.
- **SC-004**: Có thể chơi thử liên hoàn `gather --inventory-out kho.json` rồi `quan --inventory kho.json` bằng `chonoi.live` hoặc `chonoi.headless` từ lúc lặn hái/bắt cá, cập bến xuất kho, tới phục vụ khách thu tiền, tính boa, cập nhật uy tín và kết ca `quan_end`.

## Assumptions

- Nhóm giữ nguyên starter Python 3 (`chonoi/`) làm nền tảng triển khai Phase 1 như cấu hình mặc định trong `game.contract.json`.
- Mọi thành viên đều có tài khoản GitHub khai báo trong `TEAM.md` khớp `team_size = 4` trong `game.contract.json` và làm việc trên các lát cắt độc lập được phân công (US1–US4).
- Mọi chi tiết công thức/payload được gắn nhãn `[CẦN ĐỐI CHIẾU PRD-0 / docs/clarify.md]` sẽ được PO/nhóm đối chiếu trực tiếp với tài liệu PRD-0 trên Lab Board và chốt vào `docs/clarify.md` cùng `docs/contracts/` trước khi chốt code cuối Phase 1.
