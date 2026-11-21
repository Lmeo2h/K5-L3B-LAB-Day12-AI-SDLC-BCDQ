# Feature Specification: Quán Ăn Chợ Nổi — Phase 2: Một Ngày Ở Chợ Nổi (TICKET-02)

**Feature Branch**: `002-phase-2-day-loop`

**Created**: 2026-11-21

**Status**: Draft

**Milestone / Contract**: Phase 2 (TICKET-02, Test Contract `v1.1`, cửa sổ 55 phút, tag `phase-2` trước `1:55`)

**Input**: TICKET-02 — "Một ngày ở chợ nổi": nâng cấp Test Contract v1.1, bổ sung sinh thái cá bơi & sinh cá, cơ chế choke ngay bước chạm 0, Cá Sấu Năm Chèo (`ca_sau`), mở rộng quán 2 bếp / 4 bàn / 6 món lọc theo `day_plan`, vòng lặp nhiều ngày (`--mode day --days 1..5`), `ShopSim`, nút `pause`, giao diện Menu/HUD trên `chonoi.live`, 2 team skills và bộ kiểm thử QA Phase 2 — tổ chức thành 4 Vertical Slices độc lập cho 4 thành viên.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Contract v1.1, Số liệu chuẩn `gather`, Cá bơi/Sinh cá & Choke bước chạm 0 (`duyhale95` — Hà Lê Duy, dự phòng `missher03`) (Priority: P1)

Người chơi trải nghiệm bản nâng cấp Test Contract `v1.1`: hệ thống nhận đầy đủ 6 loại nguyên liệu (`ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`), mở rộng `inputs` (`pause`, `shop_done`, `buy`), hỗ trợ CLI `--mode day --days N` (`N ∈ [1, 5]`, mặc định `1`). Trong buổi sáng (`gather`), có thêm 2 nút `keo_neo` (`N5`, `N6`), `8` đàn cá ban đầu biết bơi, đổi hướng định kỳ mỗi `120` bước, phản xạ khi chạm biên/độ sâu loài, và sinh thêm đàn cá mới mỗi `360` bước (tối đa `12` đàn); đồng thời quy tắc ngạt trừ 1 HP mỗi `60` ticks được kích hoạt ngay tại bước `oxygen_ticks` vừa chạm `0` dưới nước.

**Why this priority**: Contract `v1.1` (`game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/inputs.py`) là nền móng dữ liệu và điều khiển dùng chung cho toàn bộ các lát cắt còn lại (US2, US3, US4); đồng thời làm giàu sinh thái `gather` và chuẩn hóa nhịp ngạt theo TICKET-02.

**Independent Test**: Có thể kiểm thử độc lập bằng `chonoi.headless --mode gather` với `game.contract.json` v1.1 và bộ fixture kiểm tra: (1) 6 nguyên liệu, `N5`/`N6`, `8` đàn cá khởi tạo; (2) cá bơi `1.5 m/s`, đổi hướng theo `Streams` tại bước bơi `120, 240...` trước khi di chuyển, phản xạ đúng khi chạm mép/góc; (3) sinh cá tại `phase_tick = 360 * k` với khoảng cách an toàn `> 1 m`, tắt khi `random_fish: false`; (4) `oxygen_ticks` chạm `0` ở `d > surface_depth` phát `oxygen_empty` và trừ 1 HP ngay bước chạm `0`, tiếp tục mỗi `60` ticks sau đó.

**Acceptance Scenarios**:

1. **Given** `game.contract.json` mang `contract_version: "1.1"`, **When** hệ thống nạp contract, file kho (`inventory.py`) hoặc file `inputs` (`inputs.py`), **Then** chấp nhận 6 nguyên liệu (`ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`), chấp nhận trường input mới `pause` (boolean), `shop_done` (boolean), `buy` (string), và CLI `chonoi.headless` chấp nhận `--mode day` với `--days` trong `[1, 5]` (mặc định `1`, ngoài `[1, 5]` thoát mã `2`).
2. **Given** `gather` khởi tạo mặc định theo Contract v1.1 (`random_fish: true` và không ghi đè `nodes`/`fish`), **When** kiểm tra snapshot tick `0`, **Then** có `6` nút mặt nước gồm `N1..N4` và `N5 [76, 0]` (`keo_neo`), `N6 [90, 0]` (`keo_neo`); `fish_yield` là `{"ca_linh": 3, "ca_loc": 1, "ca_keo": 2}`; và có đúng `8` đàn cá khởi tạo (`fish_initial: 8`) đặt tại `8` điểm sinh khác nhau trích từ bộ `36` cặp `(loài, vị trí)` chuẩn (`x ∈ {15, 30, 45, 60, 75, 90}` kết hợp `ca_linh d ∈ {5, 10}`, `ca_loc d ∈ {10, 16}`, `ca_keo d ∈ {24, 27}` — ứng với `30` vị trí hình học phân biệt).
3. **Given** một đàn cá đang tồn tại trong `gather` với vận tốc `fish_speed = 1.5` m/s, giới hạn ngang `fish_x = [4, 96]` và giới hạn độ sâu theo loài (`ca_linh [3, 12]`, `ca_loc [8, 20]`, `ca_keo [22, 28]`), **When** mô phỏng bước qua mỗi tick, **Then** đàn cá giữ `age_ticks`; tại bước bơi thứ `120, 240, ...` (`fish_turn_ticks = 120`), đàn đổi hướng theo `Streams` TRƯỚC khi di chuyển; nếu đi qua mép giới hạn thì phản xạ phần quãng đường còn lại trong bước và đảo dấu thành phần vận tốc vuông góc (chạm góc thì đảo cả hai thành phần).
4. **Given** đang ở `gather` với `random_fish: true` và số đàn cá hiện tại `< fish_max` (`12`), **When** `phase_tick = 360 * k` (`k >= 1`) sau khi các đàn cá đã bơi trong bước đó, **Then** hệ thống xét tập các loài có ít nhất 1 điểm sinh hợp lệ (khoảng cách tới mọi đàn hiện tại `> 1 m`), chuẩn hóa trọng số `(ca_linh 40%, ca_loc 30%, ca_keo 30%)` trên tập loài hợp lệ đó, chọn đều điểm sinh hợp lệ và góc hướng ban đầu qua `Streams`, tạo tối đa `1` đàn mới (tham gia bơi từ bước kế tiếp) và phát sự kiện `fish_spawned`. Nếu `random_fish: false` hoặc không còn điểm hợp lệ hoặc đã đạt `12` đàn thì không sinh thêm.
5. **Given** người chơi đang ở dưới nước (`d > surface_depth`) với `oxygen_ticks == 1` và `hp > 1`, **When** kết thúc bước di chuyển ở tick này `oxygen_ticks` giảm về `0`, **Then** hệ thống phát `oxygen_empty` VÀ thực hiện `choke` trừ `1` HP ngay ở bước vừa chạm `0` (phát `choke`), sau đó cứ mỗi `60` ticks tiếp theo ở dưới nước khi `oxygen_ticks == 0` lại trừ `1` HP; `choke` xuyên qua `invuln_ticks`, không tự làm rơi `hold`, và nhịp đếm ngạt (`zero_oxy_ticks`) đặt lại về `0` khi `oxygen_ticks > 0` hoặc khi ở mặt nước (`d <= surface_depth`). *(Ghi chú: cần rà soát và cập nhật `docs/clarify.md` mục Phase 1 về `zero_oxy_ticks` khi `oxygen_empty`, đồng thời cập nhật test Phase 1 bị ảnh hưởng kèm lý do rõ ràng trong commit theo `AGENTS.md`.)*

---

### User Story 2 - Cá Sấu Năm Chèo (`ca_sau`), Máu, Bất tử, Rơi hàng LIFO & Ngất (`missher03` — Nguyễn Văn Quốc, dự phòng `duyhale95`) (Priority: P1)

Khi lặn sâu (`d >= 10`), Út Sen phải dè chừng Cá Sấu Năm Chèo (`ca_sau`) tuần tra ở vùng nước sâu (`d ∈ [10, 30]`). Cá sấu phát hiện và rượt đuổi khi người chơi lại gần dưới sâu, gây sát thương `1` HP khi va chạm (`dist <= 1.5 m`), hất rơi một nửa giỏ hàng theo thứ tự LIFO, kích hoạt bất tử tạm thời `90` ticks cho người chơi và bản thân cá sấu lùi lại (`recoil`) trong `60` bước; nếu HP về `0`, người chơi ngất ngay (`faint` với `cause: "monster"`), mất toàn bộ giỏ và kết thúc buổi sáng.

**Why this priority**: Bổ sung yếu tố nguy hiểm chủ động dưới đáy sông, tạo tương tác trực tiếp với giỏ LIFO, `hp`, `invuln_ticks`, và luồng `faint` -> `quan` với kho rỗng trong vòng lặp ngày.

**Independent Test**: Có thể kiểm thử độc lập bằng `chonoi.headless --mode gather` với scenario đặt `gather.monsters[]`, `player.pos` (`d >= 10` và `d < 10`), `hold` (số lượng chẵn/lẻ), `hp`, `invuln_ticks` để kiểm tra: tuần tra `M1` (và `M2` từ ngày 3 trong `day`), chuyển `patrol <-> chase`, va chạm `dist <= 1.5`, ưu tiên tie-break `id` khi nhiều quái cùng tầm, rơi `floor(len(hold) * 0.5)` LIFO, `invuln_ticks = 90`, `recoil` `60` bước, `monster_hit`, `faint(cause="monster")`, và từ chối scenario `monsters[]` sai hợp đồng với mã thoát `2`.

**Acceptance Scenarios**:

1. **Given** chế độ `gather` khởi tạo mặc định (hoặc ngày 1–2 trong `day`), **When** xem snapshot và hành vi tuần tra, **Then** có `M1` loài `ca_sau` (`d ∈ [10, 30]`) tuần tra giữa `[60, 24] <-> [64, 24]` với tốc độ `1.0 m/s` tới mốc rồi đảo mục tiêu cho bước tiếp theo; từ ngày `3` trở đi trong `--mode day`, xuất hiện thêm `M2` tuần tra `[85, 18] <-> [89, 18]`.
2. **Given** cá sấu đang ở trạng thái `patrol`, **When** người chơi có `d >= 10` và `dist(monster, player) <= 10 m`, **Then** cá sấu chuyển sang `chase` di chuyển hướng về phía người chơi với tốc độ `3.0 m/s` (kẹp trong biên vùng nước và độ sâu `[10, 30]`); khi `dist > 16 m` hoặc người chơi lên độ sâu `d < 10`, cá sấu quay lại `patrol`.
3. **Given** cả người chơi và cá sấu đã hoàn tất di chuyển trong bước hiện tại, người chơi ở `d >= 10` với `invuln_ticks == 0` và có ít nhất một cá sấu không ở trạng thái `recoil` nằm trong `dist <= 1.5 m`, **When** kiểm tra va chạm, **Then** hệ thống áp dụng tối đa `1` đòn đánh mỗi bước (chọn cá sấu gần nhất, hòa khoảng cách chọn `id` nhỏ hơn theo `id_key`), trừ `1` HP, bỏ ra `floor(len(hold) * 0.5)` phần tử ở cuối `hold` (LIFO, trả danh sách `lost` theo thứ tự rơi), đặt `invuln_ticks = 90`, phát `monster_hit` với `{"monster_id", "hp", "lost", "pos"}`, và đưa cá sấu vừa đánh trúng vào `recoil` trong `60` bước kể từ bước kế tiếp.
4. **Given** cá sấu đang ở trạng thái `recoil`, **When** các bước tiếp theo chạy đủ `60` ticks, **Then** mỗi bước cá sấu lùi `2/60` m ra xa vị trí người chơi được cố định tại thời điểm va chạm (nếu hai vị trí trùng nhau thì lùi theo hướng `+x`), kẹp trong biên và độ sâu `[10, 30]`, không gây va chạm trong lúc `recoil`, và sau đủ `60` bước thì trở về `patrol` (bắt đầu phát hiện/đánh lại từ bước tiếp theo).
5. **Given** người chơi có `hp == 1` bị cá sấu đánh trúng trong bước, **When** `hp` giảm về `0`, **Then** hệ thống phát `faint` có `cause: "monster"`, `lost` (toàn bộ phần `hold` còn lại), `hp: 0`, làm rỗng `hold`, phát `gather_end(reason: "fainted")` ngay lập tức và bỏ qua các bước còn lại của tick; nếu đang chạy `--mode day`, ngày vẫn chuyển tiếp sang buổi tối `quan` với kho rỗng.
6. **Given** `scenario` truyền `gather.monsters[]` sai cấu trúc/id trùng/loài lạ/ngoài biên hoặc ngoài độ sâu `[10, 30]`, **When** nạp scenario trước khi chạy mô phỏng, **Then** `chonoi/scenario.py` ném `BadInput` và thoát với mã `2` trước khi ghi bất kỳ file đầu ra nào.

---

### User Story 3 - `quan` 2 Bếp / 4 Bàn / 6 Món / Lọc theo `day_plan` + 2 Skills nhóm + QA Phase 2 (`Limdim1604` — Nguyễn Thiên Bảo, dự phòng `Lmeo2h`) (Priority: P1)

Buổi tối (`quan`) mở rộng quy mô quán lên `2` bếp (`B1`, `B2`), `4` bàn (`T1`–`T4`) và `6` món ăn từ `6` loại nguyên liệu. Trong chế độ ngày (`day`), khách chọn món từ tập món cho phép trong `day_plan.dishes` của ngày hiện tại trước khi lọc theo kho còn dư; trong chế độ `quan` độc lập, khách dùng toàn bộ `6` món. Đồng thời, kiểm định scenario v1.1 chặn các cấu hình `day` sai luật, xây dựng `2` skill nhóm trong `.agents/skills/`, chạy hồi quy Phase 1 với số liệu chuẩn mới và hoàn thiện hồ sơ kiểm chứng Phase 2.

**Why this priority**: Đảm bảo quán vận hành đúng quy mô 6 món / 2 bếp / 4 bàn, khớp kế hoạch món theo ngày `day_plan` của vòng ngày US4, giữ chặt Test Contract v1.1 ở `scenario.py`, và đảm bảo chất lượng toàn đội thông qua regression + 2 skills chuẩn theo `AGENTS.md`.

**Independent Test**: Có thể kiểm thử độc lập bằng `chonoi.headless --mode quan` (2 bếp, 4 bàn, 6 món) và unit test cho bộ lọc `day_plan`, lịch khách `120 + 900*k` vào bàn trống `id` nhỏ nhất, validator `scenario.py` cho v1.1 (cấm `quan.stock`/`quan.reputation` trong `day`, lỗi nhất quán `day_plan`, xung đột tồn kho đầu buổi tối -> mã thoát `2`), chạy regression bộ test P1 và kiểm tra sự tồn tại + hoạt động của 2 skill trong `.agents/skills/` và báo cáo `docs/verification/phase-2.md` + `docs/proof/phase-2/`.

**Acceptance Scenarios**:

1. **Given** cấu hình `quan` v1.1 trong `game.contract.json`, **When** khởi tạo quán ở chế độ mặc định, **Then** có 2 bếp `B1 [2, 8]`, `B2 [5, 8]`; 4 bàn `T1 [9, 2]`, `T2 [13, 2]`, `T3 [9, 6]`, `T4 [13, 6]`; và `menu` gồm 6 món: `ca_loc_nuong_trui`, `goi_bong_sung`, `lau_ca_linh_dien_dien`, `canh_chua_ca_loc` (`cook_s: 8`, `price: 90`), `ca_keo_nuong` (`cook_s: 6`, `price: 70`), `lau_mam` (`cook_s: 12`, `price: 200`). *(Công thức nguyên liệu từng món mới lấy chính xác từ `game.contract.json` v1.1 / TICKET-02.)*
2. **Given** quán đang vận hành tại `phase_tick = 120 + 900 * k` (`k >= 0`) và còn bàn trống, **When** đón khách mới, **Then** khách được xếp vào bàn trống có `id` nhỏ nhất (theo `id_key`); ở `--mode day`, hệ thống lọc danh sách món theo các khóa món trong `day_plan.dishes` của ngày hiện tại TRƯỚC khi kiểm tra nguyên liệu khả dụng (`stock - tổng reserved`), rồi chọn đều một món nấu được qua `Streams` (khách vẫn có thể gọi lại món dù định mức `day_plan` của món đó đã đạt); ở `--mode quan` độc lập, xét toàn bộ `6` món.
3. **Given** `scenario` truyền vào cho `--mode day` chứa `quan.stock` hoặc `quan.reputation`, HOẶC `day_plan` chứa món không có trong `menu` / thiếu nguyên liệu tương ứng / mâu thuẫn, HOẶC cấu hình `quan` (khách/bếp/tay) mâu thuẫn với kho thực tế mang sang lúc mở quán buổi tối, **When** nạp scenario hoặc chuyển pha sang `quan`, **Then** hệ thống báo `BadInput` (mã thoát `2`) trước khi ghi kết quả không hợp lệ.
4. **Given** yêu cầu quy trình của nhóm trong `AGENTS.md`, **When** kiểm tra `.agents/skills/`, `docs/verification/phase-2.md` và `docs/proof/phase-2/`, **Then** có tối thiểu `2` skill tự viết dùng được trong `.agents/skills/`, bộ test hồi quy Phase 1 chạy lại với số liệu chuẩn v1.1 đều xanh (ghi rõ lý do nếu có test P1 cần cập nhật theo v1.1), và có đầy đủ log chạy headless/test tích hợp Phase 2 tại `docs/proof/phase-2/`.

---

### User Story 4 - Vòng Ngày (`--mode day`), `ShopSim`, `pause`, & Giao diện Menu/HUD trên `live` (`Lmeo2h` — Nguyễn Tấn Châu, dự phòng `Limdim1604`) (Priority: P1)

Người chơi có thể chơi trọn vẹn chiến dịch 1 đến 5 ngày (`--mode day --days N`) theo chu trình `DayIntro -> gather -> EveningIntro -> quan -> DayResult -> Shop -> DayIntro`. Giữa các ngày, người chơi vào `ShopSim` (tối đa `600` ticks) để mua nâng cấp bình oxy (`oxygen` L1/L2) và máu (`hp` L1/L2) bằng `money` (không trừ `earned`/`score`) áp dụng cho ngày tiếp theo. Ở cả 3 mode (`gather`, `quan`, `day`), nút `pause` tạm dừng/tiếp tục mô phỏng tức thì. Trên trình duyệt (`chonoi.live` + `chonoi/web/index.html`), người chơi có đầy đủ Main Menu, các màn chuyển pha, Pause overlay, Shop UI và HUD đầy đủ cảnh báo.

**Why this priority**: Kết nối `gather` và `quan` thành trải nghiệm "Một ngày ở chợ nổi" hoàn chỉnh, hiện thực hóa tiến trình nâng cấp qua nhiều ngày, hỗ trợ tạm dừng chuẩn xác trên cả headless lẫn live, và hoàn tất giao diện chơi trực quan `>= 30 FPS` để bàn giao tag `phase-2`.

**Independent Test**: Có thể kiểm thử độc lập bằng: (1) `chonoi.headless --mode day --days 1..5` kiểm tra chuỗi chuyển pha `day_start -> day_plan -> phase_start(gather) -> gather_end -> phase_start(quan) -> quan_end -> day_end -> shop -> ... -> day_complete`, tối đa `22,200` unpaused ticks/ngày; (2) test `ShopSim` (`buy` `"oxygen"`/`"hp"`, `bought`, `buy_failed`, `shop_done`, timeout `600` ticks, sao chép `active_upgrades` sang ngày mới, hồi đầy oxy/HP và xóa `hold`/kho thừa); (3) test `pause` trên cả 3 mode (đóng băng `sim_tick`/`phase_tick`/timers, `state: "paused"`, `paused`/`resumed`); (4) kiểm tra UI `chonoi.live` + `chonoi/web/index.html` ở `1280x720` và xác minh headless không khởi tạo bất kỳ UI/render nào.

**Acceptance Scenarios**:

1. **Given** chạy `chonoi.headless --mode day --days N` (`N ∈ [1, 5]`, mặc định `1`), **When** bắt đầu ngày mới và chuyển qua các pha của ngày, **Then** mỗi ngày đi qua chu trình `gather -> quan -> shop` (với tổng thời lượng hoạt động không tạm dừng tối đa `22,200` ticks/ngày: `10,800` ticks `gather` + `10,800` ticks `quan` + `600` ticks `shop`), phát đúng thứ tự các sự kiện khởi đầu ngày `day_start`, `day_plan`, `phase_start` (mục 4.5); khi hoàn tất ngày thứ `N` thì tăng `days_completed` và kết thúc lượt với `reason: "days_complete"`.
2. **Given** người chơi đang ở pha `shop` (`ShopSim`, `max_ticks: 600`) với số dư `money`, **When** gửi input `buy` là `"oxygen"` hoặc `"hp"` (cạnh mới hoặc hành động mua hợp lệ theo hợp đồng input `buy` string), **Then** nâng cấp tuần tự L1 -> L2 (`oxygen`: L1 giá `200` thành `45s / 2700` ticks, L2 giá `400` thành `60s / 3600` ticks; `hp`: L1 giá `250` thành `4` HP, L2 giá `500` thành `5` HP):
   - Nếu đủ tiền và chưa tối đa cấp: trừ `money` (giữ nguyên `earned` và `score`), cập nhật `upgrades`, phát `bought`.
   - Nếu không đủ tiền, đã đạt cấp tối đa, hoặc `buy` không hợp lệ: giữ nguyên `money`/`upgrades` và phát `buy_failed(action, reason)`.
   - Khi nhấn `shop_done` hoặc hết `600` ticks: phát `shop_end(reason: "done" | "time")`; sang ngày mới sao chép `upgrades` vào `active_upgrades`, hồi đầy oxy & HP theo `active_upgrades`, xóa sạch `hold` và kho thừa của ngày cũ.
3. **Given** người chơi đang ở bất kỳ mode nào (`gather`, `quan`, `day` — gồm mọi pha kể cả `shop`), **When** gửi cạnh lên nút `pause`, **Then** `pause` được kiểm tra ĐẦU TIÊN trong bước tick:
   - Khi chuyển sang tạm dừng: chỉ tăng biến đếm `tick` bên ngoài, đóng băng `sim_tick`, `phase_tick`, mọi bộ đếm thời gian/hồi chiêu/nhịp sinh/khách/nấu/ăn/ngạt, bỏ qua mọi cạnh nút hành động khác và `buy`, đặt `snapshot.state = "paused"` và phát `paused`.
   - Khi nhấn `pause` lần nữa lúc đang tạm dừng: phát `resumed`, khôi phục `state = "playing"` và chạy bước gameplay bình thường ngay trong tick đó.
4. **Given** snapshot và dòng sự kiện JSONL trong v1.1, **When** kiểm tra cấu trúc dữ liệu ở mọi mode/pha, **Then** envelope sự kiện có trường `day`; snapshot bổ sung các trường `day`, `day_plan`, `upgrades`, `active_upgrades`, `phase`, `stock` (trong pha `shop`), và `state` (`"playing"` | `"paused"` | `"finished"`).
5. **Given** người chơi mở `chonoi.live` trên trình duyệt ở độ phân giải `1280x720`, **When** chơi từ đầu đến hết ngày/chiến dịch, **Then** giao diện hiển thị đầy đủ Main Menu (`Chơi` / `Thoát`), `DayIntro` (`4s` hoặc nhấn phím bỏ qua), `EveningIntro`, `DayResult`, `Summary`, Pause overlay (`Esc` / `P`), Shop UI và HUD trong `gather`/`quan` (cảnh báo `< 25%` oxy/máu, đổi màu thời gian `<= 30s`, viền tím `"Thủy quái!"` khi bị cá sấu rượt/đánh, `"Hết hơi!"` khi cạn oxy, bảng kiểm nguyên liệu theo `day_plan`), dùng font sans-serif cỡ chữ `>= 18px`, đạt `>= 30 FPS`; đồng thời hoàn toàn không kích hoạt code UI/render khi chạy `chonoi.headless`.

---

### Edge Cases

- **Thứ tự xử lý `pause` đầu tick**: Nếu cùng một frame input vừa có cạnh lên `pause` vừa có cạnh lên `interact`/`catch`/`shop_done`/`buy`, hệ thống phải xử lý `pause` trước tiên; khi bước đó chuyển sang tạm dừng, toàn bộ hành động khác và `buy` trong tick đó bị bỏ qua hoàn toàn.
- **Choke bước chạm 0 khi `hp == 1` hoặc trùng tick với cá sấu**: Trong cùng tick ở `gather`, thứ tự xử lý phải tuân theo Mục 4.5 của TICKET-02 (đồng hồ/cooldown/hồi nút -> người chơi bơi, oxy, ngạt -> cập nhật quái theo `id` và xét tối đa 1 hit -> `interact` -> `catch` theo vị trí cá trước khi bơi -> hết giờ -> nếu còn giờ thì cá bơi, sinh thêm theo lịch): nếu ngạt hoặc va chạm làm `hp` về `0`, phải phát `faint` (đúng `cause`), làm rỗng `hold` và trả về `gather_end(reason="fainted")` ngay lập tức, bỏ qua các bước còn lại trong tick.
- **Choke xuyên `invuln_ticks`**: Khi người chơi vừa bị cá sấu đánh trúng (`invuln_ticks = 90`) nhưng hết oxy ở `d > surface_depth`, sát thương ngạt `choke` vẫn trừ `1` HP mỗi `60` ticks (không bị `invuln_ticks` chặn) và không làm rơi từng phần `hold`.
- **Rơi hàng LIFO khi `len(hold)` lẻ hoặc bằng 0–1**: `floor(len(hold) * 0.5)` bằng `0` khi `len(hold) <= 1` (`lost = []`); khi `len(hold) = 5` thì rơi `2` phần tử cuối cùng của `hold` (tính theo thứ tự nhặt, phần tử mới nhất rơi trước).
- **Cá sấu `recoil` khi trùng tọa độ người chơi**: Nếu `monster.pos == player.pos` tại thời điểm va chạm, vector lùi đặt cố định theo hướng `+x` (`[1, 0]`), di chuyển `2/60 m/bước` và kẹp trong biên `bounds` và độ sâu `ca_sau` `[10, 30]`.
- **Phản xạ cá ở góc vùng giới hạn**: Nếu đàn cá trong một bước vượt qua đồng thời cả biên `fish_x` (`4` hoặc `96`) lẫn biên độ sâu loài, phải phản xạ phần quãng đường dư trên cả hai trục và đảo dấu cả hai thành phần vận tốc.
- **Không còn loài/điểm sinh cá hợp lệ ở tick `360 * k`**: Nếu một loài không còn điểm sinh nào cách mọi đàn hiện tại `> 1 m`, bỏ loài đó khỏi phân bố chuẩn hóa trọng số (`40/30/30`); nếu tất cả loài đều không có điểm hợp lệ (hoặc đang có `12` đàn), không sinh đàn mới trong kỳ đó (không phát `fish_spawned`).
- **Xung đột `day_plan` và món khách gọi ở `quan`**: Nếu `day_plan.dishes` quy định tập món cho ngày hôm đó nhưng kho thực tế mang từ buổi sáng sang không đủ nấu món nào trong `day_plan.dishes` (kể cả khi kho có nguyên liệu cho món khác nằm ngoài `day_plan`), khách đến vẫn phát `no_dish`.
- **Ngất ở `gather` trong `--mode day`**: Kết thúc `gather` với `reason: "fainted"`, kho chuyển sang `quan` là rỗng `{}` nhưng ngày chơi không kết thúc — vẫn mở buổi tối `quan` và sau đó sang `ShopSim` bình thường.
- **Thoát lỗi mã `2` trước khi ghi file**: Mọi lỗi CLI (`--days` ngoài `[1, 5]`, `--inventory` dùng sai mode), lỗi `scenario` (dùng `quan.stock`/`quan.reputation` trong `--mode day`, sai `monsters[]`, sai `fish[].age_ticks`, sai `day_plan`), hoặc xung đột `quan` lúc mở quán phải thoát mã `2` trước khi ghi file đầu ra.
- **Ngoài phạm vi lõi (Out-of-Core / Deferred)**: Các tính năng mở rộng tùy chọn trong TICKET-02 (`Lao xua`, `Vợt hút cá`, `Rắn Hổ Mây`, `Cháy món`, `Chợ Chú Sáu`, `Sổ tay & Cá Hô`, `Settings`) **không thuộc phạm vi lõi** của Phase 2 và chỉ xem xét bổ sung nếu còn thời gian sau khi hoàn thành toàn bộ Definition of Done (DoD) lõi và được Integrator phê duyệt không phá vỡ Test Contract v1.1.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (Test Contract v1.1 & CLI — US1, US4)**: Hệ thống phải nâng cấp `game.contract.json` lên `contract_version: "1.1"`, cập nhật `chonoi/contract.py`, `chonoi/inventory.py` (hỗ trợ đủ 6 nguyên liệu `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`), `chonoi/inputs.py` (hỗ trợ `interact`, `catch`, `pause`, `shop_done`, và `buy` kiểu string), và `chonoi/headless.py` (hỗ trợ `--mode day --days N` với `N ∈ [1, 5]`, mặc định `1`). Mọi số liệu cân bằng đọc từ `game.contract.json`, mọi ngẫu nhiên đi qua `Streams`, mọi danh sách thực thể sắp xếp theo `ids.sort_by_id` và cấp id bằng `IdAllocator`.
- **FR-002 (Số liệu chuẩn & Cá bơi/Sinh cá — US1)**: `GatherSim` phải hỗ trợ `N1..N6` (thêm `N5 [76, 0]`, `N6 [90, 0]` loại `keo_neo`), `fish_yield` (`ca_linh: 3`, `ca_loc: 1`, `ca_keo: 2`), `fish_initial: 8` tại `8` điểm sinh khác nhau, `fish_max: 12`, `fish_speed: 1.5`, biên `fish_x: [4, 96]`, khoảng độ sâu từng loài (`ca_linh [3, 12]`, `ca_loc [8, 20]`, `ca_keo [22, 28]`), đổi hướng định kỳ mỗi `fish_turn_ticks = 120` trước khi di chuyển, phản xạ biên/góc, sinh cá mỗi `fish_spawn_ticks = 360` (`phase_tick = 360 * k, k >= 1`) sau bước cá bơi với khoảng cách an toàn `> 1 m` và trọng số chuẩn hóa `40/30/30` -> phát `fish_spawned`, cùng hỗ trợ `fish[].age_ticks` và `random_fish: false`.
- **FR-003 (Choke bước chạm 0 — US1)**: Trong `GatherSim`, khi `d > surface_depth` và `oxygen_ticks == 0`, người chơi mất `1` HP mỗi `choke_interval_ticks` (`60` ticks) **tính cả bước mà `oxygen_ticks` vừa giảm từ `1 -> 0`**; nhịp đếm đặt lại khi `oxygen_ticks > 0` hoặc `d <= surface_depth`; sát thương ngạt xuyên qua `invuln_ticks` và không làm rơi `hold` từng phần.
- **FR-004 (Cá Sấu Năm Chèo — US2)**: `GatherSim` (qua module `chonoi/sim/monsters.py` và hook trong `gather.py`) phải quản lý loài `ca_sau` (`d ∈ [10, 30]`): `M1` `[60, 24] <-> [64, 24]` từ ngày 1 (và trong `gather` độc lập), `M2` `[85, 18] <-> [89, 18]` từ ngày 3 (`day`); chuyển trạng thái `patrol` (`1.0 m/s`) <-> `chase` (`3.0 m/s`, vào khi `d >= 10` & `dist <= 10 m`, thoát khi `dist > 16 m` hoặc `d < 10`); va chạm sau di chuyển (`dist <= 1.5 m`, `d >= 10`, `invuln_ticks == 0`, tối đa 1 hit/bước, tie-break `id`) gây `-1` HP, rơi `floor(len(hold) * 0.5)` LIFO, `invuln_ticks = 90`, phát `monster_hit{monster_id, hp, lost, pos}`, đưa quái vào `recoil` `60` bước (`2/60 m/bước` xa điểm người chơi lúc va chạm, `+x` nếu trùng); `hp == 0` phát `faint(cause="monster", lost, hp=0)` và kết thúc ngay `gather_end(reason="fainted")`. Snapshot xuất `monsters[]` và `player.invuln_ticks`.
- **FR-005 (Quán 2 Bếp / 4 Bàn / 6 Món / Lọc `day_plan` — US3)**: `QuanSim` phải hỗ trợ `B1 [2, 8]`, `B2 [5, 8]`; `T1 [9, 2]`, `T2 [13, 2]`, `T3 [9, 6]`, `T4 [13, 6]`; `6` món (`ca_loc_nuong_trui`, `goi_bong_sung`, `lau_ca_linh_dien_dien`, `canh_chua_ca_loc` `8s/90`, `ca_keo_nuong` `6s/70`, `lau_mam` `12s/200`); lịch đón khách `120 + 900 * k` vào bàn trống `id` nhỏ nhất; trong `--mode day`, lọc món theo `day_plan.dishes` trước khi kiểm tra nguyên liệu khả dụng và chọn đều qua `Streams` (cho phép gọi lại sau khi đạt định mức); chế độ `quan` độc lập dùng cả `6` món.
- **FR-006 (Kiểm định Scenario v1.1 — US1, US2, US3)**: `chonoi/scenario.py` phải kiểm tra hợp lệ các trường mở rộng v1.1: `gather.fish[].age_ticks`, `gather.monsters[]`, cấu hình `day` (cấm `quan.stock` và `quan.reputation` trong `day`, kiểm tra tính nhất quán nguyên liệu của `day_plan`, và kiểm tra xung đột đầu vào `quan` với kho thực tế lúc mở quán -> `BadInput`, mã thoát `2`).
- **FR-007 (Vòng Ngày & `ShopSim` — US4)**: Hệ thống phải triển khai `DaySim` (`chonoi/sim/day.py`) và `ShopSim` (`chonoi/sim/shop.py`) tích hợp vào `Session`/`runner.py` cho `--mode day --days N` (`1..5`): luân chuyển `gather -> quan -> shop` mỗi ngày (tối đa `22,200` unpaused ticks/ngày), phát đúng thứ tự `day_start`, `day_plan`, `phase_start` (mục 4.5), kết thúc sau ngày `N` với `days_completed` và `reason: "days_complete"`. `ShopSim` chạy tối đa `600` ticks, xử lý `shop_done` và `buy` (`"oxygen"` L1 `200`->`45s/2700t`, L2 `400`->`60s/3600t`; `"hp"` L1 `250`->`4`, L2 `500`->`5`), trừ `money` giữ nguyên `earned`/`score`, phát `bought`/`buy_failed(action, reason)`/`shop_end(reason: done|time)`, áp dụng `active_upgrades` vào ngày kế tiếp cùng hồi đầy oxy/HP và xóa `hold`/kho thừa.
- **FR-008 (Tạm dừng `pause` & Envelope/Snapshot v1.1 — US4)**: Cả 3 mode (`gather`, `quan`, `day`) phải kiểm tra cạnh lên `pause` ĐẦU TIÊN mỗi tick: đóng băng `sim_tick`, `phase_tick`, mọi bộ đếm/lịch và bỏ qua nút hành động/`buy` khi tạm dừng (`paused`, `state: "paused"`); nhấn lại `pause` phát `resumed` và thực thi bước gameplay ngay trong tick đó. Toàn bộ snapshot và event envelope cập nhật đầy đủ các trường v1.1 (`day`, `day_plan`, `upgrades`, `active_upgrades`, `phase`, `stock` ở shop, `day` trên event envelope).
- **FR-009 (Web Live UI & Headless Isolation — US4)**: `chonoi/web/index.html` và `chonoi/live.py` phải cung cấp Main Menu (`Chơi`/`Thoát`), `DayIntro` (`4s`/nhấn phím), `EveningIntro`, `DayResult`, `Summary`, Pause overlay (`Esc`/`P`), Shop UI, và HUD `gather`/`quan` (cảnh báo `<25%`, màu thời gian `<=30s`, viền tím `"Thủy quái!"`, `"Hết hơi!"`, checklist nguyên liệu, sans-serif `>= 18px` ở `1280x720`, `>= 30 FPS`). Code UI/render không được chạy hay phụ thuộc trong `chonoi.headless`.
- **FR-010 (Team Skills & Bằng chứng QA — US3)**: Nhóm phải tạo tối thiểu `2` skill trong `.agents/skills/` (tuân thủ `AGENTS.md`), chạy lại kiểm thử hồi quy Phase 1 trên nền Contract v1.1, lập báo cáo kiểm chứng `docs/verification/phase-2.md` và lưu bằng chứng chạy tại `docs/proof/phase-2/`.
- **FR-011 (Hạng mục cần đối chiếu TICKET-02 trước khi khóa số liệu v1.1)**: Công thức chi tiết của 3 món mới (`canh_chua_ca_loc`, `ca_keo_nuong`, `lau_mam`), bảng chỉ tiêu `day_plan` cho từng ngày D1–D5, thứ tự chính xác từng bước trong mục 4.5 (cộng dồn giữa `gather.step` và `day.step`), và tương tác `zero_oxy_ticks` khi `oxygen_empty` phải được đối chiếu trực tiếp từ TICKET-02 và ghi rõ vào `game.contract.json` v1.1 / `docs/clarify.md` khi US1 & US2 triển khai.

### Key Entities

- **Ingredient (v1.1)**: `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`.
- **Node (`gather`)**: `N1..N6` ở mặt nước (`d = 0`), gồm `bong_dien_dien` (`N1`, `N2`), `bong_sung` (`N3`, `N4`), `keo_neo` (`N5 [76, 0]`, `N6 [90, 0]`).
- **Fish (`gather`)**: `id`, `kind` (`ca_linh`, `ca_loc`, `ca_keo`), `pos`, `heading_deg`, `age_ticks` (v1.1); tối đa `12` đàn, tốc độ `1.5 m/s`, đổi hướng mỗi `120` bước bơi, sinh mỗi `360` ticks.
- **Monster (`gather`)**: `id` (`M1` từ ngày 1, `M2` từ ngày 3), `kind: "ca_sau"`, `pos`, `state` (`patrol` | `chase` | `recoil`), `waypoints`, `target_idx`, `recoil_ticks_left`, `recoil_origin` (điểm người chơi lúc va chạm).
- **Menu & Dish (`quan`, 6 món)**: `ca_loc_nuong_trui`, `goi_bong_sung`, `lau_ca_linh_dien_dien`, `canh_chua_ca_loc` (`8s / 90`), `ca_keo_nuong` (`6s / 70`), `lau_mam` (`12s / 200`).
- **DayPlan (`day`)**: Kế hoạch món và chỉ tiêu theo từng ngày (`day_plan.dishes` và định mức nguyên liệu/món cho D1–D5).
- **Upgrades & Shop (`day`/`shop`)**: `upgrades` (đã mua, dạng cấp bậc `oxygen: 0..2`, `hp: 0..2`), `active_upgrades` (đang hiệu lực trong ngày hiện tại); `ShopSim` (`max_ticks: 600`, `buy`, `shop_done`).
- **Pause & Snapshot/Event Envelope v1.1**: `tick` ngoài, `sim_tick`, `phase_tick`, `mode`, `phase` (`gather` | `quan` | `shop`), `day`, `days_completed`, `state` (`playing` | `paused` | `finished`), `day_plan`, `upgrades`, `active_upgrades`, `stock` (trong `shop`).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Toàn bộ test Phase 1 (regression sau khi thích nghi số liệu chuẩn v1.1 nếu có) và test mới của cả 4 Vertical Slices Phase 2 (`test_gather_fish_v11.py`, `test_gather_monsters.py`, `test_quan_v11.py`, `test_day_shop_pause.py`) chạy xanh 100% qua `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v`.
- **SC-002**: Chạy `python -m chonoi.headless` trên cả 3 mode (`gather`, `quan`, `day`) với cùng `--seed`, `--days`, `--inputs`, `--scenario` 2 lần liên tiếp cho đầu ra JSONL và `--inventory-out` (với `gather`) giống hệt nhau từng byte (100% tất định).
- **SC-003 (Hiệu năng Headless)**: Chạy `python -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out ...` hoàn thành trong thời gian `<= 20 giây`.
- **SC-004 (Trải nghiệm Live UI)**: Chạy `python -m chonoi.live --mode day --days 5` ở độ phân giải `1280x720` đạt tốc độ khung hình `>= 30 FPS`, chữ trên Menu/Shop/HUD dùng font sans-serif cỡ `>= 18px`, hiển thị đầy đủ các màn chuyển pha, Pause overlay và cảnh báo trạng thái.
- **SC-005 (Kiểm đầu vào & Quy trình)**: 100% các tình huống sai schema/mâu thuẫn v1.1 (`--days` ngoài `[1, 5]`, `day` chứa `quan.stock`/`quan.reputation`, sai `monsters[]`, sai `day_plan`, xung đột kho lúc vào `quan`) trả mã thoát `2` trước khi ghi file đầu ra; `.agents/skills/` có tối thiểu `2` skill nhóm hợp lệ; `docs/verification/phase-2.md` và `docs/proof/phase-2/` được hoàn tất trước khi Integrator gắn tag `phase-2` đúng hạn `1:55`.

---

## Assumptions

- Nhóm tiếp tục phát triển trên nền starter Python 3 (`chonoi/`) và bộ test `unittest` có sẵn từ Phase 1.
- Cả 4 thành viên (`duyhale95`, `missher03`, `Limdim1604`, `Lmeo2h`) làm việc song song theo ranh giới sở hữu file rõ ràng; `duyhale95` (US1) chốt và merge phần Contract `v1.1` sớm để 3 thành viên còn lại rebase sạch trước mốc tích hợp phút 20.
- Các tính năng mở rộng tùy chọn ngoài lõi (`Lao xua`, `Vợt hút cá`, `Rắn Hổ Mây`, `Cháy món`, `Chợ Chú Sáu`, `Sổ tay & Cá Hô`, `Settings`) được tách khỏi phạm vi bắt buộc Phase 2 để bảo toàn tiến độ cửa sổ 55 phút và tag `phase-2`.
