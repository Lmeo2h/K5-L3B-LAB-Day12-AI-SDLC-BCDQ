# Prompts Phase 2 — Vertical Slices (Nhóm BCDQ)

> Tài liệu này chứa **4 prompt hoàn chỉnh (copy-paste trực tiếp cho AI coding agent)** tương ứng với 4 Vertical Slice của **Phase 2 — TICKET-02: Một ngày ở chợ nổi** (**Test Contract v1.1**, cửa sổ sprint **55 phút: `1:00–1:55`**, mốc gắn tag `phase-2` trước **`1:55`**).
>
> **Quy tắc chung trước khi chạy prompt:**
> - Mở **TICKET-02** trên lab board (`https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg`) để đối chiếu các công thức, payload sự kiện và schema v1.1.
> - Tuân thủ nghiêm ngặt `AGENTS.md` và `TEAM.md`: mỗi thành viên làm trên nhánh riêng, **≥ 3 commit có nội dung** từ tài khoản GitHub cá nhân, PR ≤ ~400 dòng theo `.github/pull_request_template.md`, đọc chéo theo cặp dự phòng (`duyhale95` ↔ `missher03`, `Limdim1604` ↔ `Lmeo2h`), và ghi nhật ký AI vào `docs/ai-usage-log.md`.
> - **Lịch phối hợp 55 phút & Thứ tự land lên `main`:**
>   1. **Phút 0–8:** `duyhale95` (Slice 1) land sớm commit/PR **Contract v1.1** (`game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/inputs.py`) lên `main` để 3 thành viên còn lại rebase sạch. Trong lúc chờ, các thành viên khác viết test-first và helper cục bộ trên nhánh riêng.
>   2. **Phút 20:** Chạy **tích hợp thử lần 1**; QA Lead (`Limdim1604`) chạy hồi quy Phase 1 với số liệu chuẩn v1.1 và lưu bằng chứng vào `docs/proof/phase-2/` & `docs/verification/phase-2.md`.
>   3. **Phút 40–55 (trước `1:55`):** Hoàn tất merge đủ 4 slice vào `main`, kiểm tra hiệu năng headless `<= 20s` cho `22,200` ticks (`--mode day --days 1`), UI `live` (`>= 18px` tại `1280x720`, `>= 30 FPS`), điền `docs/retro.md` (Phase 2 nhanh), và Integrator (`Lmeo2h`) gắn tag `phase-2` trước **`1:55`**.
> - **Phối hợp tránh xung đột file dùng chung:**
>   - `chonoi/sim/gather.py`: Slice 1 (`duyhale95`: cá bơi/sinh cá & choke bước chạm 0) và Slice 2 (`missher03`: hook tới `chonoi/sim/monsters.py` & `invuln_ticks`/`faint(cause="monster")`). `missher03` tách toàn bộ logic cá sấu sang `chonoi/sim/monsters.py`, chỉ đặt hook gọn trong `gather.py` và rebase sau Slice 1.
>   - `chonoi/scenario.py`: Slice 1 (`duyhale95`: trường cá/nguyên liệu v1.1 trong `gather`), Slice 2 (`missher03`: validate `gather.monsters[]`), Slice 3 (`Limdim1604`: kiểm mâu thuẫn v1.1 cho `quan` & `day`). Mỗi người chỉ sửa đúng hàm/khối được phân công và rebase tuần tự lên `main`.

---

## Prompt 1 — Hà Lê Duy (`duyhale95` · MSSV `2A202603851`)
**Slice 1:** Contract v1.1 + `gather` Cá bơi & Sinh cá + Choke bước chạm 0 · **Vai:** Scrum / Release (Nhóm trưởng), dự phòng cho `missher03` · **Nhánh Git:** `feat/p2-s1-contract-fish`

````markdown
Bạn là AI coding agent hỗ trợ **Hà Lê Duy (`duyhale95` — MSSV `2A202603851`)**, vai **Scrum / Release (Nhóm trưởng)** của nhóm **BCDQ** (dự phòng cho `missher03`).

### 1. Nhánh Git & Chiến lược Merge sớm
- Làm việc trên nhánh: `feat/p2-s1-contract-fish` (tạo từ `main` mới nhất đã có tag `phase-1`).
- **Ưu tiên tối đa (trong 5–8 phút đầu):** Hoàn thiện và land sớm commit/PR **Contract v1.1** (`game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/inputs.py`) lên `main` để `missher03`, `Limdim1604`, `Lmeo2h` rebase sạch; sau đó tiếp tục phần Cá bơi, Sinh cá và Ngạt mới trong `chonoi/sim/gather.py` + `tests/test_gather_fish_v11.py`.

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md` và `TEAM.md`
2. `specs/002-phase-2-day-loop/spec.md`, `specs/002-phase-2-day-loop/plan.md`, `specs/002-phase-2-day-loop/tasks.md`
3. `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/inputs.py`, `chonoi/scenario.py`
4. `chonoi/sim/gather.py`, `chonoi/rng.py`, `chonoi/ids.py`
5. `tests/test_gather_survival.py`, `tests/test_smoke_p1.py`, `tests/test_python_starter_units.py`
6. **TICKET-02 trên lab board** (`https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg`) — mục Test Contract v1.1, Số liệu chuẩn Gather, Cá bơi/Sinh cá, Ngạt mới, và **Mục 4.5 (Thứ tự xử lý)**.

### 3. Thông số chuẩn & Quy tắc TICKET-02 bắt buộc cho Slice 1
1. **Contract v1.1 (`game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/inputs.py`):**
   - Nâng `"contract_version": "1.1"`.
   - Mở rộng nguyên liệu từ 4 -> **6 loại**: `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`.
   - Nút input v1.1 trong `chonoi/inputs.py`: giữ `interact`, `catch`, thêm nút `pause` (`bool`, cạnh lên), `shop_done` (`bool`, cạnh lên), và trường `buy` dạng **chuỗi** (`str`, ví dụ `"oxygen"`, `"hp"` — cập nhật `load_frames`, `InputPlayer`, `LiveInputs` để không báo lỗi `bool` với `buy` và kiểm tra hợp lệ trước khi ghi output).
   - Số liệu chuẩn `tuning.gather` v1.1 trong `game.contract.json` & validator trong `chonoi/contract.py`:
     - Nút mặt nước (`nodes`, `d = 0`): giữ `N1`–`N4`, thêm **`N5` tại `[76, 0]` (`keo_neo`)** và **`N6` tại `[90, 0]` (`keo_neo`)**.
     - `fish_yield`: `{"ca_linh": 3, "ca_loc": 1, "ca_keo": 2}`.
     - `fish_initial`: **8 đàn** ở 8 điểm sinh phân biệt (thuộc 6 cột `x ∈ {15, 30, 45, 60, 75, 90}`, độ sâu `ca_linh d ∈ {5, 10}`, `ca_loc d ∈ {10, 16}`, `ca_keo d ∈ {24, 27}` — tổng 36 cặp `(loài, vị trí)`, 30 vị trí hình học phân biệt).
     - Tham số cá bơi & sinh cá: `fish_max = 12`, `fish_speed = 1.5` (m/s), `fish_x = [4, 96]`, dải độ sâu theo loài (`ca_linh: [3, 12]`, `ca_loc: [8, 20]`, `ca_keo: [22, 28]`), `fish_turn_ticks = 120`, `fish_spawn_ticks = 360`, `fish_spawn_clearance = 1.0` (đọc từ `game.contract.json`), trọng số sinh chuẩn hóa `ca_linh: 0.4`, `ca_loc: 0.3`, `ca_keo: 0.3`.
     - Thêm cấu hình chuẩn v1.1 cho các slice khác vào `game.contract.json` & `chonoi/contract.py` (để các thành viên không phải sửa `game.contract.json` nữa):
       - `gather.monsters`: `M1` (`[60, 24] <-> [64, 24]`, từ ngày 1) và `M2` (`[85, 18] <-> [89, 18]`, từ ngày 3), dải độ sâu `ca_sau: [10, 30]`, `patrol_speed: 1.0`, `chase_speed: 3.0`, `detect_radius: 10.0`, `lose_radius: 16.0`, `detect_min_depth: 10.0`, `hit_radius: 1.5`, `invuln_ticks: 90`, `recoil_ticks: 60`, `recoil_dist: 2.0`.
       - `quan`: 2 bếp `B1 [2, 8]`, `B2 [5, 8]`; 4 bàn `T1 [9, 2]`, `T2 [13, 2]`, `T3 [9, 6]`, `T4 [13, 6]`; `first_customer_tick: 120`, `customer_interval_s: 15` (`900` ticks).
       - `menu` đủ **6 món**: giữ 3 món P1, thêm `canh_chua_ca_loc` (`cook_s: 8`, `price: 90`), `ca_keo_nuong` (`cook_s: 6`, `price: 70`), `lau_mam` (`cook_s: 12`, `price: 200`) — đối chiếu đúng công thức từ TICKET-02.
       - `day_plan` (Ngày 1–5) & `shop` (`max_ticks: 600`, nâng cấp `oxygen`: L1 `200` -> `45s`, L2 `400` -> `60s`; `hp`: L1 `250` -> `4`, L2 `500` -> `5`).

2. **Cá bơi & Sinh thêm cá (`chonoi/sim/gather.py`):**
   - Thêm `self.phase_tick = 0` trong `GatherSim.__init__` và tăng `self.phase_tick += 1` mỗi `step`.
   - Hỗ trợ `fish[].age_ticks` (mặc định `0` nếu thiếu) và `random_fish: false` (tắt `fish_initial` mặc định khi scenario không truyền `fish`).
   - **Cá bơi (`_step_fish_swim`):**
     - Duyệt theo `sort_by_id(self.fish)`. Tăng `age_ticks` cho đàn cá hiện có.
     - Tại các bước bơi `age_ticks % fish_turn_ticks == 0` (`120, 240, ...`), đổi `heading_deg` bằng `self.rng.get("fish_swim")` (hoặc tên stream thống nhất trong contract) **TRƯỚC** khi di chuyển trong bước đó.
     - Di chuyển với tốc độ `fish_speed / TICK` (`1.5 / 60` m/bước). Nếu chạm biên `fish_x` (`[4, 96]`) hoặc biên dải độ sâu loài (`[d_min, d_max]`): **phản xạ quãng đường dư còn lại** và đảo thành phần vận tốc vuông góc với cạnh chạm; nếu chạm góc thì đảo cả hai thành phần; cập nhật `heading_deg` khớp hướng phản xạ.
   - **Sinh thêm cá (`_step_fish_spawn`):**
     - Xét tại `self.phase_tick % fish_spawn_ticks == 0` (`360 * k`, `k >= 1`), chạy **SAU** bước cá bơi.
     - Nếu `len(self.fish) < fish_max` (`12`), sinh tối đa **1 đàn**:
       - Lọc các cặp `(loài, điểm sinh)` trong 36 cặp có khoảng cách tới người chơi và mọi đàn cá hiện có **`> 1.0 m`** (`clearance > 1 m`).
       - Chuẩn hóa trọng số `ca_linh: 0.4, ca_loc: 0.3, ca_keo: 0.3` trên các loài **còn điểm hợp lệ** -> chọn loài bằng `self.rng.get("fish_spawn")`, chọn đều 1 điểm hợp lệ của loài đó, chọn đều `heading_deg` bằng `self.rng.get(...)`, cấp ID bằng `self.ids.new("F")`.
       - Đàn mới tham gia bơi từ bước **tiếp theo** (không bơi ngay trong bước vừa sinh), phát sự kiện `("fish_spawned", {...})`.

3. **Ngạt mới — Choke bước chạm 0 (`chonoi/sim/gather.py`):**
   - Khi ở dưới nước (`d > surface_depth`) và `oxygen_ticks == 0`: trừ `1` HP mỗi `choke_interval_ticks` (`60` tick), **bao gồm cả bước vừa giảm từ `> 0` xuống `0`** (bước phát `oxygen_empty`).
   - Giữ đúng nhịp `60` tick cho các lần ngạt tiếp theo (`0, 60, 120...`), reset bộ đếm nhịp khi `oxygen_ticks > 0` hoặc khi ở mặt nước (`d <= surface_depth`).
   - `choke` **xuyên qua `invuln_ticks`** (không bị chặn bởi bất tử) và **không làm rơi hàng** trong `hold`; nếu `hp <= 0` -> đặt `hp = 0`, làm rỗng `hold`, phát `faint` (`cause="oxygen"`), gọi `self._finish("fainted", events)` và trả `events` ngay.
   - **Lưu ý test P1:** Nếu cơ chế choke ngay bước chạm 0 hoặc số liệu v1.1 (`8` đàn cá, `6` nút) làm thay đổi timing/count của test Phase 1 (`tests/test_gather_survival.py`, `tests/test_smoke_p1.py`), được phép cập nhật test bị ảnh hưởng và **phải ghi rõ lý do đổi test trong thông điệp commit** (đúng quy tắc `AGENTS.md`).

4. **Thứ tự xử lý trong `GatherSim.step` (Mục 4.5 TICKET-02):**
   1) Đồng hồ, cooldown (`time_left_ticks`, `invuln_ticks`, `catch_cd_ticks`), hồi nút (`node_regrown`), tăng `phase_tick`.
   2) Người chơi di chuyển (`_move`), oxy & ngạt (`dive`/`surface`, `oxygen_empty`, choke bước chạm 0 -> nếu `hp == 0`: `faint` + `gather_end("fainted")` và bỏ các bước còn lại).
   3) *(Hook Slice 2)* Cập nhật quái theo `id` rồi xét tối đa 1 hit (`monster_hit` -> nếu `hp == 0`: `faint` + `gather_end("fainted")` và bỏ các bước còn lại).
   4) `interact` (bến trước -> hái nút).
   5) `catch` (bắt cá **theo vị trí cá trước khi bơi**).
   6) Xét hết giờ (`time_left_ticks <= 0` -> `gather_end("time")`).
   7) **Nếu còn giờ (`not self.done`):** cá bơi (`_step_fish_swim`, tăng `age_ticks`), rồi sinh thêm cá (`_step_fish_spawn` tại `phase_tick = 360 * k`).

### 4. Phạm vi sở hữu & File KHÔNG ĐƯỢC SỬA
- **File bạn sở hữu (được phép sửa/tạo):**
  - `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/inputs.py`
  - `chonoi/sim/gather.py` (CHỈ phần Slice 1: `phase_tick`, cá bơi/phản xạ/đổi hướng, sinh thêm cá, choke bước chạm 0)
  - `chonoi/scenario.py` (CHỈ phần validate fish/hold/nodes v1.1 cho `gather`: 6 nguyên liệu, 3 loài cá, `fish[].age_ticks`)
  - `tests/test_gather_fish_v11.py` (và cập nhật kèm lý do commit nếu test P1 bị ảnh hưởng trực tiếp bởi choke bước chạm 0 / số liệu chuẩn v1.1)
  - `docs/ai-usage-log.md` (thêm dòng Phase 2 của bạn)
  - `docs/clarify.md` (chỉ thêm câu hỏi cho PO nếu phát hiện chỗ mơ hồ)
- **File KHÔNG ĐƯỢC SỬA:**
  - `chonoi/sim/monsters.py` và phần hook cá sấu của `missher03`.
  - `chonoi/sim/quan.py`, phần `quan`/`day` của `chonoi/scenario.py`.
  - `chonoi/sim/day.py`, `chonoi/sim/shop.py`, `chonoi/{runner,headless,live}.py`, `chonoi/web/`.
  - `.agents/skills/`, `docs/verification/`, `docs/proof/`, `docs/retro.md`.

### 5. Lệnh kiểm tra (Windows PowerShell)
```powershell
$env:PYTHONPATH="tests;."; python -m unittest tests.test_gather_fish_v11 -v
$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v
python -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out_s1_a.jsonl
python -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out_s1_b.jsonl
(Get-FileHash out_s1_a.jsonl).Hash -eq (Get-FileHash out_s1_b.jsonl).Hash
Measure-Command { python -m chonoi.headless --mode gather --seed 1 --ticks 10800 --out out_s1_perf.jsonl }
```
*(Xóa `out_s1_*.jsonl` trước khi commit. Sau khi Slice 4 merge sẽ chạy benchmark toàn ngày `22,200` ticks `<= 20s`.)*

### 6. Quy trình Git, Nhật ký AI & PR
- Tạo **≥ 3 commit có nội dung rõ ràng** bằng tài khoản `duyhale95` (gợi ý: 1. Contract v1.1 + inputs/inventory, 2. cá bơi/phản xạ/sinh cá & `scenario.py`, 3. choke bước chạm 0 + `tests/test_gather_fish_v11.py` + `docs/ai-usage-log.md`).
- Mở PR Contract v1.1 sớm nhất có thể, tag `@missher03` và `@Limdim1604` review.
````

---

## Prompt 2 — Nguyễn Văn Quốc (`missher03` · MSSV `2A202603864`)
**Slice 2:** Cá Sấu Năm Chèo, Máu, Bất tử, Rơi hàng LIFO & Ngất (`gather`) · **Vai:** PO (`docs/clarify.md`), dự phòng cho `duyhale95` · **Nhánh Git:** `feat/p2-s2-crocodiles`

````markdown
Bạn là AI coding agent hỗ trợ **Nguyễn Văn Quốc (`missher03` — MSSV `2A202603864`)**, vai **PO (chủ trì `docs/clarify.md`)** của nhóm **BCDQ** (dự phòng cho `duyhale95`).

### 1. Nhánh Git & Phối hợp Rebase
- Làm việc trên nhánh: `feat/p2-s2-crocodiles` (tạo từ `main`; viết test-first và `chonoi/sim/monsters.py` ngay, sau đó rebase lên `main` ngay khi `duyhale95` merge Contract v1.1).
- Mục tiêu: Hoàn thiện **Slice 2 — Cá Sấu Năm Chèo (`M1`, `M2` từ Ngày 3), Va chạm, Bất tử 90t, Rơi hàng LIFO `floor(hold/2)`, `recoil` 60 bước, `faint(cause="monster")`**, kiểm tra `gather.monsters[]` trong `chonoi/scenario.py`, viết `tests/test_gather_monsters.py`, và cập nhật `docs/clarify.md`.

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md`, `TEAM.md`, `docs/clarify.md`
2. `specs/002-phase-2-day-loop/spec.md`, `specs/002-phase-2-day-loop/plan.md`, `specs/002-phase-2-day-loop/tasks.md`
3. `game.contract.json` (bản v1.1 từ Slice 1), `chonoi/sim/gather.py`, `chonoi/scenario.py`, `chonoi/ids.py`, `chonoi/rng.py`
4. **TICKET-02 trên lab board** (`https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg`) — mục Cá Sấu Năm Chèo, Va chạm/Bất tử/Rơi hàng/Ngất, Snapshot `monsters[]`, và **Mục 4.5 (Thứ tự xử lý)**.

### 3. Thông số chuẩn & Quy tắc TICKET-02 bắt buộc cho Slice 2
1. **Module riêng `chonoi/sim/monsters.py`:**
   - Loài `ca_sau`, dải độ sâu `[10, 30]`. Đọc toàn bộ hằng số từ `tuning["gather"]` (`game.contract.json`), **không hard-code** trong luật.
   - **Cá thể mặc định:**
     - `M1`: tuần tra qua lại `[60, 24] <-> [64, 24]` — xuất hiện từ **Ngày 1** và khi chạy `--mode gather` độc lập.
     - `M2`: tuần tra qua lại `[85, 18] <-> [89, 18]` — chỉ xuất hiện từ **Ngày 3** trở đi (khi `day >= 3`), hoặc khi `scenario.gather.monsters` khai báo tường minh.
   - **Trạng thái & Di chuyển:**
     - `patrol`: tốc độ `1.0 m/s` (`1.0 / 60` m/bước) hướng về mốc tuần tra hiện tại (`waypoints[target_idx]`); khi chạm mốc thì đảo `target_idx` cho bước **tiếp theo**.
     - `chase`: chuyển từ `patrol` sang `chase` khi người chơi ở độ sâu `d >= 10` và `dist(monster.pos, player.pos) <= 10 m`; bơi về phía người chơi tốc độ `3.0 m/s` (`3.0 / 60` m/bước). Thoát `chase` -> `patrol` khi `dist > 16 m` hoặc người chơi ở `d < 10`.
     - Luôn kẹp vị trí cá sấu trong `bounds` (`x`, `d`) và dải độ sâu loài `[10, 30]`.
   - **Va chạm & Hậu quả (xét SAU khi cả người chơi, cá và cá sấu đã di chuyển trong tick — Mục 4.5):**
     - Điều kiện va chạm: `monster.state != "recoil"`, `dist <= 1.5 m`, người chơi ở `d >= 10`, và `self.invuln_ticks == 0`.
     - Tối đa **1 lần trúng mỗi bước**: nếu nhiều con cùng thỏa điều kiện, chọn con gần nhất (`dist` nhỏ nhất), hòa chọn `id` nhỏ hơn theo `id_key(m["id"])`.
     - Khi trúng đòn:
       1. Trừ `1` HP (`self.hp = max(0, self.hp - 1)`).
       2. Rơi hàng LIFO: tính `drop_n = len(self.hold) // 2` (`floor(len(hold) * 0.5)`), lấy `drop_n` món ở cuối mảng `self.hold` theo thứ tự LIFO vào danh sách `lost`.
       3. Đặt `self.invuln_ticks = 90` (từ `tuning`).
       4. Phát sự kiện `("monster_hit", {"monster_id": m["id"], "hp": self.hp, "lost": lost, "pos": list(self.pos)})`.
       5. Đưa con cá sấu vừa va chạm vào trạng thái `recoil` trong **`60` bước** bắt đầu từ bước **tiếp theo**: cố định vị trí người chơi tại thời điểm va chạm làm tâm lùi; mỗi bước trong `recoil` lùi **`2 / 60` m** ra xa khỏi tâm đó (nếu trùng vị trí tâm -> lùi theo hướng **`+x`**), kẹp trong `bounds` và `[10, 30]`; không phát hiện và không gây va chạm trong 60 bước này. Hết 60 bước chuyển về `patrol` (phát hiện/va chạm lại từ bước **tiếp theo**).
       6. Nếu `self.hp == 0`: làm rỗng phần còn lại của `self.hold` (đưa vào `lost` của `faint` theo LIFO hoặc đúng payload TICKET-02), phát `("faint", {"cause": "monster", "lost": ..., "hp": 0, "pos": list(self.pos)})`, gọi `self._finish("fainted", events)` và **dừng phần còn lại của tick ngay** (trong `--mode day`, buổi tối vẫn mở quán với kho rỗng).

2. **Hook gọn vào `chonoi/sim/gather.py`:**
   - Nhận `day=1` (tham số tùy chọn trên `GatherSim.__init__`, mặc định `1` để tương thích P1) hoặc đọc từ `scenario`/khung; khởi tạo `self.monsters` (reserve ID qua `IdAllocator`), ưu tiên `scenario["monsters"]` nếu có.
   - Đảm bảo `snapshot()` có `"monsters"` (sắp xếp bằng `sort_by_id`) và `"player.invuln_ticks"`.
   - Trong `GatherSim.step`, gọi helper cập nhật quái theo `id` và helper va chạm quái vật ngay sau bước di chuyển/oxy/ngạt của người chơi và **trước** `interact`/`catch`/hết giờ/cá bơi, tuân thủ tuyệt đối thứ tự Mục 4.5.

3. **Kiểm tra `gather.monsters[]` trong `chonoi/scenario.py`:**
   - Thêm `"monsters"` vào `GATHER_KEYS`; dùng `_check_ids` đảm bảo `id` duy nhất.
   - Kiểm tra `kind == "ca_sau"`, `pos` và `waypoints` (2 mốc `[x, d]`) nằm trong `bounds` và dải độ sâu `[10, 30]`, `state ∈ {"patrol", "chase", "recoil"}`, `recoil_ticks_left` nguyên không âm (`<= 60`), `target_idx` hợp lệ (`0` hoặc `1`), cấm trường lạ -> ném `BadInput` (thoát mã `2` trước khi ghi output).

4. **Vai trò PO (`docs/clarify.md`):**
   - Chốt các câu hỏi P1 còn treo trong `docs/clarify.md` (chú thích rõ đã nâng cấp theo TICKET-02 đối với choke bước chạm 0 và `faint.cause`).
   - Ghi nhận mọi làm rõ v1.1 từ TICKET-02 (format `lost` trong `monster_hit`/`faint`, `age_ticks`, `day_plan` lọc món) để `Limdim1604` và `Lmeo2h` dùng thống nhất.

### 4. Phạm vi sở hữu & File KHÔNG ĐƯỢC SỬA
- **File bạn sở hữu (được phép sửa/tạo):**
  - `chonoi/sim/monsters.py` (mới)
  - `chonoi/sim/gather.py` (CHỈ phần hook `monsters`, `day` param, `snapshot()["monsters"]`, `faint(cause="monster")`)
  - `chonoi/scenario.py` (CHỈ phần validate `gather.monsters[]`)
  - `tests/test_gather_monsters.py` (mới)
  - `docs/clarify.md` và `docs/ai-usage-log.md`
- **File KHÔNG ĐƯỢC SỬA:**
  - `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/inputs.py`.
  - Logic cá bơi / sinh cá / choke bước chạm 0 của `duyhale95` trong `chonoi/sim/gather.py`.
  - `chonoi/sim/quan.py`, phần `quan`/`day` của `chonoi/scenario.py`.
  - `chonoi/sim/day.py`, `chonoi/sim/shop.py`, `chonoi/{runner,headless,live}.py`, `chonoi/web/`.
  - `.agents/skills/`, `docs/verification/`, `docs/proof/`, `docs/retro.md`.

### 5. Lệnh kiểm tra (Windows PowerShell)
```powershell
$env:PYTHONPATH="tests;."; python -m unittest tests.test_gather_monsters -v
$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v
python -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out_s2_a.jsonl
python -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out_s2_b.jsonl
(Get-FileHash out_s2_a.jsonl).Hash -eq (Get-FileHash out_s2_b.jsonl).Hash
```
*(Xóa `out_s2_*.jsonl` tạm trước khi commit. Sau khi Slice 4 merge, xác minh thêm hiệu năng `--mode day --days 1 --ticks 22200` `<= 20s`.)*

### 6. Quy trình Git, Nhật ký AI & PR
- Tạo **≥ 3 commit có nội dung rõ ràng** bằng tài khoản `missher03` (1. `chonoi/sim/monsters.py` patrol/chase/recoil/LIFO, 2. hook `gather.py` + validate `gather.monsters[]` trong `scenario.py`, 3. `tests/test_gather_monsters.py` + `docs/clarify.md` + `docs/ai-usage-log.md`).
- Mở PR vào `main` theo `.github/pull_request_template.md`, tag `@duyhale95` và `@Limdim1604` review.
````

---

## Prompt 3 — Nguyễn Thiên Bảo (`Limdim1604` · MSSV `2A202603861`)
**Slice 3:** `quan` 2 Bếp / 4 Bàn / 6 Món / Lọc theo `day_plan` + Kiểm mâu thuẫn v1.1 + 2 Skills nhóm + QA Phase 2 · **Vai:** QA Lead, dự phòng cho `Lmeo2h` · **Nhánh Git:** `feat/p2-s3-quan-v11-qa`

````markdown
Bạn là AI coding agent hỗ trợ **Nguyễn Thiên Bảo (`Limdim1604` — MSSV `2A202603861`)**, vai **QA Lead** của nhóm **BCDQ** (dự phòng cho `Lmeo2h`).

### 1. Nhánh Git & Mục tiêu Slice 3
- Làm việc trên nhánh: `feat/p2-s3-quan-v11-qa` (viết test-first và 2 skill nhóm ngay; rebase lên `main` sau khi `duyhale95` land Contract v1.1).
- Mục tiêu:
  1. Nâng cấp `chonoi/sim/quan.py` lên v1.1: **2 Bếp (`B1`, `B2`), 4 Bàn (`T1`–`T4`), 6 Món**, lọc thực đơn theo `day_plan` trong `--mode day`.
  2. Hoàn thiện **kiểm mâu thuẫn scenario v1.1** trong `chonoi/scenario.py` (cấm `quan.stock`/`quan.reputation` trong `day`, kiểm `day_plan`, kiểm xung đột tồn kho lúc vào ca tối).
  3. Viết `tests/test_quan_v11.py`.
  4. Tạo **2 skill nhóm** bắt buộc theo `AGENTS.md` trong `.agents/skills/`.
  5. Chạy **hồi quy P1** với số liệu chuẩn v1.1, **tích hợp phút 20**, và hoàn thiện `docs/verification/phase-2.md` + `docs/proof/phase-2/` (kèm benchmark `22,200` ticks `<= 20s` khi Slice 4 merge).

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md` và `TEAM.md`
2. `specs/002-phase-2-day-loop/spec.md`, `specs/002-phase-2-day-loop/plan.md`, `specs/002-phase-2-day-loop/tasks.md`
3. `game.contract.json` (bản v1.1 từ Slice 1), `chonoi/sim/quan.py`, `chonoi/scenario.py`, `chonoi/ids.py`, `chonoi/rng.py`
4. `docs/verification/phase-1.md`, `docs/verification/phase-2.md`
5. **TICKET-02 trên lab board** (`https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg`) — mục Quán v1.1, `day_plan` Ngày 1–5, Kiểm mâu thuẫn scenario v1.1, Mục 4.5 (Thứ tự xử lý), và yêu cầu Harness/Skills.

### 3. Yêu cầu chi tiết Slice 3 & QA Phase 2
1. **Nâng cấp `chonoi/sim/quan.py` lên v1.1:**
   - Đọc 2 bếp (`B1 [2, 8]`, `B2 [5, 8]`) và 4 bàn (`T1 [9, 2]`, `T2 [13, 2]`, `T3 [9, 6]`, `T4 [13, 6]`) từ `self.t["stoves"]` và `self.t["tables"]` (không hard-code).
   - Hỗ trợ đầy đủ **6 món** từ `tuning["menu"]`: `ca_loc_nuong_trui`, `goi_bong_sung`, `lau_ca_linh_dien_dien`, `canh_chua_ca_loc` (`8s`, `90`), `ca_keo_nuong` (`6s`, `70`), `lau_mam` (`12s`, `200`).
   - Lịch khách đến `120 + 900 * k` (`k >= 0`) vào bàn trống có `id` nhỏ nhất theo `sort_by_id`.
   - **Lọc món theo `day_plan`:** nhận danh sách món cho phép của ngày (ví dụ tham số `allowed_dishes=None` trong `QuanSim.__init__`):
     - Nếu đang trong `--mode day` (`allowed_dishes` được truyền từ `day_plan` của ngày hiện tại): lọc `menu` theo các khóa món trong `day_plan.dishes` **TRƯỚC** khi kiểm tra nguyên liệu khả dụng (`stock - reserved`), sau đó chọn đều món nấu được bằng `self.rng.get("customer_order")`. Khách **vẫn có thể gọi lại** một món ngay cả khi đã bán đủ chỉ tiêu trong ngày.
     - Nếu chạy `--mode quan` độc lập (`allowed_dishes is None`): dùng toàn bộ **6 món**.
   - Giữ đúng thứ tự xử lý Mục 4.5 trong `QuanSim.step`: giảm timer kiên nhẫn/nấu/ăn -> di chuyển -> `interact` (tối đa 1 lần, ưu tiên `(khoảng cách, bếp < bàn, id_key)`) -> thanh toán ăn xong -> khách rời vì hết kiên nhẫn -> sinh khách mới nếu tới lịch -> đóng ca khi `time_left_ticks <= 0`.

2. **Kiểm mâu thuẫn scenario v1.1 trong `chonoi/scenario.py`:**
   - Mở rộng validator cho cấu trúc scenario của `--mode day` (nếu hỗ trợ block `day` hoặc `gather`/`quan` trong `day`):
     - Khi chạy `--mode day`: **cấm** `quan.stock` và `quan.reputation` (`BadInput` -> mã thoát `2` trước khi ghi file đầu ra).
     - Kiểm tra `day_plan` (nếu có trong tuning/scenario): tên món thuộc `menu`, nguyên liệu thuộc 6 loại v1.1, số lượng dương.
   - Ở `--mode quan` và lúc khởi tạo `QuanSim` trong ca tối của `--mode day`: đảm bảo `prepare_quan_customers` kiểm tra tồn kho thực tế mang sang (hoặc `quan.stock`), nếu khách dựng sẵn giữ chỗ vượt quá tồn kho hoặc gọi món ngoài `allowed_dishes` của ngày -> ném `BadInput` (mã `2`).

3. **Viết 2 skill nhóm trong `.agents/skills/` (bắt buộc theo `AGENTS.md`):**
   - Tạo 2 thư mục skill chuẩn `SKILL.md` (có YAML frontmatter `name` và `description` rõ ràng, ngắn gọn, dùng được ngay), ví dụ:
     1. `.agents/skills/chonoi-contract-guard/SKILL.md`: checklist tự động kiểm tra không hard-code số ngoài `game.contract.json`, mọi RNG đi qua `Streams`, dùng `sort_by_id`/`IdAllocator`, và đối chiếu byte-identical JSONL headless.
     2. `.agents/skills/chonoi-slice-qa/SKILL.md`: quy trình test-first theo TICKET, chạy hồi quy phase trước + benchmark hiệu năng PowerShell, và xuất bằng chứng trung thực vào `docs/proof/` & `docs/verification/`.

4. **Kiểm chứng & Bằng chứng (`docs/verification/phase-2.md`, `docs/proof/phase-2/`):**
   - Viết `tests/test_quan_v11.py` kiểm tra đủ: 2 bếp chạy song song, 4 bàn, 6 món, lọc theo `day_plan` trước khi kiểm kho (và gọi lại món sau khi đủ chỉ tiêu), `--mode quan` đủ 6 món, và các ca scenario mâu thuẫn thoát mã `2`.
   - Chạy **hồi quy P1** trên bộ số liệu chuẩn v1.1, chạy **tích hợp phút 20**, lưu log chạy thật vào `docs/proof/phase-2/`, và điền trung thực ma trận `docs/verification/phase-2.md` (kể cả phần còn thiếu nếu slice khác chưa merge tại phút 20, rồi cập nhật lại sau khi đủ 4 slice).

### 4. Phạm vi sở hữu & File KHÔNG ĐƯỢC SỬA
- **File bạn sở hữu (được phép sửa/tạo):**
  - `chonoi/sim/quan.py`
  - `chonoi/scenario.py` (CHỈ phần kiểm mâu thuẫn v1.1 cho `quan` và `day`)
  - `tests/test_quan_v11.py` (mới)
  - `.agents/skills/<skill-1>/SKILL.md` và `.agents/skills/<skill-2>/SKILL.md` (2 skill nhóm mới)
  - `docs/verification/phase-2.md` và `docs/proof/phase-2/*`
  - `docs/ai-usage-log.md`
- **File KHÔNG ĐƯỢC SỬA:**
  - `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/inputs.py`.
  - `chonoi/sim/gather.py`, `chonoi/sim/monsters.py`.
  - `chonoi/sim/day.py`, `chonoi/sim/shop.py`, `chonoi/{runner,headless,live}.py`, `chonoi/web/`.
  - `docs/retro.md` (của `Lmeo2h`), `docs/clarify.md` (của `missher03`).

### 5. Lệnh kiểm tra (Windows PowerShell)
```powershell
$env:PYTHONPATH="tests;."; python -m unittest tests.test_quan_v11 -v
$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v
python tools/check_team.py
python -m chonoi.headless --mode quan --seed 1 --ticks 1200 --out out_s3_a.jsonl
python -m chonoi.headless --mode quan --seed 1 --ticks 1200 --out out_s3_b.jsonl
(Get-FileHash out_s3_a.jsonl).Hash -eq (Get-FileHash out_s3_b.jsonl).Hash
# Sau khi Slice 4 merge, chạy kiểm chứng benchmark 1 ngày (<= 20s):
Measure-Command { python -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out out_p2_bench.jsonl }
```
*(Xóa file `.jsonl` tạm ngoài `docs/proof/phase-2/` trước khi commit.)*

### 6. Quy trình Git, Nhật ký AI & PR
- Tạo **≥ 3 commit có nội dung rõ ràng** bằng tài khoản `Limdim1604` (1. `quan.py` 2 bếp/4 bàn/6 món/`day_plan` + `scenario.py` v1.1, 2. `tests/test_quan_v11.py` + 2 skills trong `.agents/skills/`, 3. bằng chứng P1 regression & QA trong `docs/proof/phase-2/` + `docs/verification/phase-2.md` + `docs/ai-usage-log.md`).
- Mở PR vào `main` theo `.github/pull_request_template.md`, tag `@Lmeo2h` và `@duyhale95` review.
````

---

## Prompt 4 — Nguyễn Tấn Châu (`Lmeo2h` · MSSV `2A202603846`)
**Slice 4:** `--mode day --days 1..5`, `ShopSim`, `pause` cả 3 chế độ, Envelope v1.1, UI/HUD `live` (`>= 18px`, `>= 30 FPS`), Retro & Tag `phase-2` · **Vai:** Integrator (giữ `docs/contracts/`, gắn tag), dự phòng cho `Limdim1604` · **Nhánh Git:** `feat/p2-s4-day-shop-ui`

````markdown
Bạn là AI coding agent hỗ trợ **Nguyễn Tấn Châu (`Lmeo2h` — MSSV `2A202603846`)**, vai **Integrator** của nhóm **BCDQ** (dự phòng cho `Limdim1604`).

### 1. Nhánh Git & Mục tiêu Slice 4 + Tích hợp `phase-2`
- Làm việc trên nhánh: `feat/p2-s4-day-shop-ui` (viết `chonoi/sim/shop.py`, `chonoi/sim/day.py`, UI `chonoi/web/index.html`, và `tests/test_day_shop_pause.py` song song ngay; rebase lên `main` sau khi Slice 1–3 merge).
- Mục tiêu:
  1. Cài đặt **`ShopSim`** (`chonoi/sim/shop.py`) & **`DaySim`** (`chonoi/sim/day.py`) cho `--mode day --days 1..5`.
  2. Cài đặt **`pause` trên cả 3 chế độ** (`gather`, `quan`, `day`) và **Snapshot/Event Envelope v1.1** trong `chonoi/{runner,headless,live}.py`.
  3. Nâng cấp **`chonoi/web/index.html`** (Menu, DayIntro, EveningIntro, DayResult, Summary, Pause, Shop, HUD v1.1 với chữ `>= 18px` tại `1280x720`, `>= 30 FPS`, tắt hoàn toàn trong `headless`).
  4. Viết `tests/test_day_shop_pause.py`, điền `docs/retro.md` (mục **Phase 2 (nhanh)**), merge đủ 4 slice và **gắn tag `phase-2` trước `1:55`**.

### 2. Đọc các file sau TRƯỚC KHI viết code
1. `AGENTS.md`, `TEAM.md`, `docs/contracts/README.md`, `docs/retro.md`
2. `specs/002-phase-2-day-loop/spec.md`, `specs/002-phase-2-day-loop/plan.md`, `specs/002-phase-2-day-loop/tasks.md`
3. `game.contract.json` (bản v1.1 từ Slice 1), `chonoi/runner.py`, `chonoi/headless.py`, `chonoi/live.py`, `chonoi/web/index.html`
4. `chonoi/sim/gather.py`, `chonoi/sim/quan.py`, `chonoi/inputs.py`
5. **TICKET-02 trên lab board** (`https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg`) — mục Vòng Ngày, Shop & Nâng cấp, `pause`, Snapshot/Event Envelope v1.1, **Mục 4.5 (Thứ tự xử lý)**, và yêu cầu Menu/HUD.

### 3. Yêu cầu chi tiết Slice 4 (TICKET-02)
1. **`ShopSim` (`chonoi/sim/shop.py`):**
   - `max_ticks = 600` (10s @ 60 Hz; đọc từ `tuning["shop"]`).
   - Hai loại nâng cấp đọc từ `tuning`:
     - `"oxygen"`: Cấp 1 giá `200` -> `45s` (`2700` ticks); Cấp 2 giá `400` -> `60s` (`3600` ticks).
     - `"hp"`: Cấp 1 giá `250` -> `4` HP; Cấp 2 giá `500` -> `5` HP.
   - Xử lý input mỗi bước:
     - Nếu có `buy` (chuỗi): mua hợp lệ -> trừ `money` (**KHÔNG trừ `earned` và `score`**), tăng cấp `upgrades`, phát `("bought", {...})`; mua thất bại (thiếu tiền, tối đa cấp, tên lạ) -> phát `("buy_failed", {"action": ..., "reason": ...})`.
     - Nếu `inp.pressed("shop_done")`: kết thúc shop với `("shop_end", {"reason": "done", ...})`.
     - Hết `600` tick: kết thúc shop với `("shop_end", {"reason": "time", ...})`.
   - Áp dụng nâng cấp cho ngày tiếp theo: khi sang ngày mới, copy `upgrades` sang `active_upgrades`, hồi đầy oxy & HP theo mức `active_upgrades`, và xóa sạch `hold` & `stock` thừa của ngày cũ.

2. **`DaySim` (`chonoi/sim/day.py`) & Thứ tự xử lý Mục 4.5:**
   - Hỗ trợ `--mode day --days N` (`N ∈ [1, 5]`, mặc định `1`; kiểm lỗi `BadInput` mã `2` nếu sai phạm vi hoặc dùng `--days` cho `gather`/`quan`).
   - Vòng ngày: `DayIntro -> gather -> EveningIntro -> quan -> DayResult -> Shop -> DayIntro` (tối đa `22,200` unpaused ticks/ngày). Trong `headless` không có độ trễ thời gian thực cho các màn Intro/Result.
   - Chuỗi sự kiện chuyển pha:
     - Đầu ngày mới: phát `day_start`, `day_plan` (kế hoạch món của ngày hiện tại từ `tuning["day_plan"]`), `phase_start` (`phase="gather"`).
     - Kết thúc `gather` (`docked`/`fainted`/`time`): chuyển `inventory_items()` (rỗng `{}` nếu `fainted`) sang `QuanSim(allowed_dishes=day_plan_dishes)`, phát `phase_start` (`phase="quan"`).
     - Kết thúc `quan` (`quan_end`): chuyển `money`, `earned`, `reputation`, `upgrades` sang `ShopSim`, phát `phase_start` (`phase="shop"`). (Hoặc nếu là ngày cuối / theo đúng quy tắc TICKET-02: kiểm tra xem ngày cuối có qua Shop hay kết thúc ngay `days_complete` — đối chiếu chính xác TICKET-02).
     - Khi hoàn thành đủ `--days N`: kết thúc với `days_completed`, `reason: "days_complete"`.

3. **`pause` trên cả 3 chế độ & Envelope v1.1 (`chonoi/runner.py`, `chonoi/headless.py`, `chonoi/live.py`):**
   - **Quy tắc `pause` (Mục 4.5 — kiểm tra ĐẦU TIÊN mỗi tick trong `Session.step`):**
     - Khi đang chơi mà nhận cạnh lên `pause`: chuyển sang tạm dừng; **chỉ tăng `tick` ngoài**, đóng băng `sim_tick`, `phase_tick`, mọi bộ đếm/lịch; **bỏ qua mọi cạnh action** (`interact`, `catch`, `shop_done`) và `buy`; phát `("paused", ...)`.
     - Trong lúc đang tạm dừng: `snapshot()` trả `"state": "paused"`.
     - Khi đang tạm dừng mà nhận cạnh lên `pause` tiếp theo: thoát tạm dừng, phát `("resumed", ...)`, và **chạy bước gameplay ngay trong tick đó** (tăng `sim_tick`, `phase_tick`, xử lý input).
   - **Snapshot & Event Envelope v1.1:**
     - `snapshot()` bổ sung: `day`, `day_plan`, `upgrades`, `active_upgrades`, `phase`, `stock` (khi ở `shop`), `state` (`"playing"` / `"paused"` / `"finished"`). Giữ tương thích với test P1 ở `--mode gather|quan`.
     - Mỗi dòng `event` bổ sung trường `"day"` theo Contract v1.1.
   - **`chonoi/headless.py`:** mở khóa `--mode day`, thêm `--days` (default `1`, validate `1..5`), cấm `--inventory`/`--inventory-out` khi `--mode day` (thoát mã `2` trước khi ghi file).
   - **`chonoi/live.py`:** hỗ trợ `--mode day --days N`, nhận input `pause`, `shop_done`, `buy` qua `POST /input`, cấp `meta` đúng cho pha hiện tại (`gather`/`quan`/`shop`) trong `GET /state`.

4. **UI / HUD v1.1 (`chonoi/web/index.html`):**
   - Bổ sung màn hình & lớp phủ: **Main Menu** (`Chơi` / `Thoát`), **`DayIntro`** (4s hoặc bấm phím qua), **`EveningIntro`**, **`DayResult`**, **`Summary`**, **Pause overlay** (`Esc` / `P` gửi `pause`), **Shop UI** (mua nâng cấp `oxygen`/`hp`, nút qua lượt `shop_done`), và **HUD v1.1**:
     - Cảnh báo oxy `< 25%`; đổi màu đồng hồ khi `<= 30s`;
     - Viền tím + thông báo `"Thủy quái!"` khi cá sấu rượt/tấn công, `"Hết hơi!"` khi hết oxy;
     - Checklist nguyên liệu cần thu/còn trong ngày theo `day_plan`;
     - Vẽ rõ cá sấu (`monsters[]`: phân biệt `patrol` / `chase` / `recoil`), nút `N5`/`N6`, 6 loài/món, 2 bếp, 4 bàn.
     - **Bắt buộc:** font `sans-serif`, cỡ chữ **`>= 18px`** tại độ phân giải `1280x720`, đảm bảo **`>= 30 FPS`** mượt mà. Toàn bộ UI/hiệu ứng chỉ nằm ở client web & `live`, **tắt hoàn toàn ở `headless`**.
   - *(Ghi chú: các phần mở rộng tùy chọn ngoài lõi như `Lao xua`, `Vợt hút cá`, `Rắn Hổ Mây`, `Cháy món`, `Chợ Chú Sáu`, `Sổ tay & Cá Hô`, `Settings` để ngoài lõi, chỉ cân nhắc sau khi DoD Phase 2 đã xanh 100%.)*

### 4. Phạm vi sở hữu & File KHÔNG ĐƯỢC SỬA
- **File bạn sở hữu (được phép sửa/tạo):**
  - `chonoi/sim/shop.py` (mới), `chonoi/sim/day.py` (mới)
  - `chonoi/runner.py`, `chonoi/headless.py`, `chonoi/live.py`, `chonoi/web/index.html`
  - `tests/test_day_shop_pause.py` (mới)
  - `docs/retro.md` (điền mục `## Phase 2 (nhanh)`), `docs/ai-usage-log.md`
  - `docs/contracts/` (chỉ cập nhật ghi chú envelope v1.1 nếu cần sau khi báo cả nhóm)
- **File KHÔNG ĐƯỢC SỬA:**
  - `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/inputs.py`.
  - `chonoi/sim/gather.py`, `chonoi/sim/monsters.py`, `chonoi/sim/quan.py`, `chonoi/scenario.py`.
  - `.agents/skills/`, `docs/verification/phase-2.md`, `docs/proof/phase-2/`, `docs/clarify.md`.

### 5. Lệnh kiểm tra (Windows PowerShell) & Gắn tag `phase-2` (trước `1:55`)
```powershell
$env:PYTHONPATH="tests;."; python -m unittest tests.test_day_shop_pause -v
$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v
python tools/check_team.py
python -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out out_day_a.jsonl
python -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out out_day_b.jsonl
(Get-FileHash out_day_a.jsonl).Hash -eq (Get-FileHash out_day_b.jsonl).Hash
Measure-Command { python -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out out_day_perf.jsonl }
python -m chonoi.live --mode day --days 2 --seed 1
```
- Yêu cầu bắt buộc: `Measure-Command` cho `22,200` ticks phải **`<= 20` giây**, 2 lần chạy cùng seed phải giống nhau từng byte (`Hash` bằng nhau), và trên trình duyệt `1280x720` đạt `>= 30 FPS`, chữ HUD `>= 18px`.
- Xóa các file `out_day_*.jsonl` tạm trước khi commit.
- Sau khi toàn bộ 4 PR đã merge vào `main` và `discover -s tests -v` + `check_team.py` + `22,200 ticks <= 20s` xanh 100%, gắn tag trước **`1:55`**:
```powershell
git checkout main
git pull origin main
git tag phase-2
git push origin phase-2
```

### 6. Quy trình Git, Nhật ký AI & PR
- Tạo **≥ 3 commit có nội dung rõ ràng** bằng tài khoản `Lmeo2h` (1. `shop.py` & `day.py`, 2. `pause` + envelope v1.1 trên `runner`/`headless`/`live` & `tests/test_day_shop_pause.py`, 3. UI/HUD `chonoi/web/index.html` + `docs/retro.md` + `docs/ai-usage-log.md`).
- Mở PR vào `main` theo `.github/pull_request_template.md`, tag `@Limdim1604` và `@duyhale95` review.
````
