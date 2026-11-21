"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm viết tiếp (đúng thứ tự một bước trong PRD mục 13.8, "Gather"):
  TODO(nhóm, lát 1): bơi + oxy + biên + giỏ
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity
  TODO(nhóm, lát 2): hái + bắt cá + cập bến + kho
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Các tính năng của phase sau chưa nằm trong khung này.
"""

import math

from ..ids import id_key, sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


def _weighted_choice(rng, kinds, weights):
    """Chọn một loài theo trọng số chuẩn hóa trên tập `kinds` hợp lệ."""
    total = sum(float(weights[k]) for k in kinds)
    r = rng.random() * total
    acc = 0.0
    for k in kinds:
        acc += float(weights[k])
        if r <= acc:
            return k
    return kinds[-1]


def _reflect_axis(old_val, val, vel, lo, hi, map_lo, map_hi):
    """Phản xạ quãng đường dư trên 1 trục khi chạm biên [lo, hi]; giữ kẹp trong vùng hợp lệ."""
    reflected = False
    if lo <= old_val <= hi:
        if val < lo or (val == lo and vel < 0):
            val = 2.0 * lo - val
            vel = -vel
            reflected = True
        elif val > hi or (val == hi and vel > 0):
            val = 2.0 * hi - val
            vel = -vel
            reflected = True
        val = min(max(val, lo), hi)
    else:
        val = min(max(val, map_lo), map_hi)
    return val, vel, reflected


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        self.phase_tick = 0
        self.random_fish = scenario.get("random_fish", True)
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định, bơi & sinh
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        for n in self.nodes:
            ids.reserve(n["id"])
        self.fish = self._init_fish(scenario, t, ids)
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    def _init_fish(self, scenario, t, ids):
        if "fish" in scenario:
            fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                     "heading_deg": float(f.get("heading_deg", 0)),
                     "age_ticks": int(f.get("age_ticks", 0))}
                    for f in scenario["fish"]]
            for f in fish:
                ids.reserve(f["id"])
            return fish
        if not self.random_fish:
            return []
        initial = t["fish_initial"]
        if isinstance(initial, list):
            fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                     "heading_deg": float(f.get("heading_deg", 0)),
                     "age_ticks": int(f.get("age_ticks", 0))}
                    for f in initial]
            for f in fish:
                ids.reserve(f["id"])
            return fish
        return self._spawn_initial_fish(int(initial))

    def _spawn_initial_fish(self, count: int):
        """Sinh `count` đàn ban đầu tại `count` vị trí hình học phân biệt từ bộ 36 cặp chuẩn."""
        spawn_x = self.t["fish_spawn_x"]
        spawn_depths = self.t["fish_spawn_depths"]
        weights = self.t["fish_weights"]
        candidates = {
            kind: [(float(x), float(d)) for x in spawn_x for d in spawn_depths[kind]]
            for kind in sorted(spawn_depths)
        }
        used_positions = set()
        rng = self.rng.get("fish_init")
        fish = []
        for _ in range(count):
            valid_by_kind = {
                k: [pt for pt in pts if pt not in used_positions]
                for k, pts in candidates.items()
            }
            valid_kinds = [k for k in sorted(valid_by_kind) if valid_by_kind[k]]
            if not valid_kinds:
                break
            chosen_kind = _weighted_choice(rng, valid_kinds, weights)
            pt = rng.choice(valid_by_kind[chosen_kind])
            used_positions.add(pt)
            fish.append({
                "id": self.ids.new("F"),
                "kind": chosen_kind,
                "pos": [pt[0], pt[1]],
                "heading_deg": rng.uniform(0.0, 360.0),
                "age_ticks": 0,
            })
        return fish

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"],
                      "heading_deg": f["heading_deg"], "age_ticks": f["age_ticks"]}
                     for f in sort_by_id(self.fish)],
        }

    # --- một bước (Mục 4.5 TICKET-02) ------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ, cooldown, phase_tick, nút mọc lại
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # 2. bơi + chặn mép + oxy & ngạt
        was_surface = self._at_surface()
        self._move(inp)
        if self._update_survival(was_surface, events):
            return events
        # 3. (Slice 2 hook) quái vật & va chạm
        # 4. interact: bến trước, rồi hái nút
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            self._try_gather_node(events)
        # 5. bắt cá (theo vị trí cá trước khi bơi)
        if inp.pressed("catch"):
            self._try_catch_fish(events)
        # 6. xét hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        # 7. còn giờ: cá bơi rồi sinh thêm cá theo lịch
        if not self.done and self.random_fish:
            self._step_fish_swim()
            self._step_fish_spawn(events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _try_gather_node(self, events):
        """Hái nút ready gần nhất (hòa theo id_key) khi đang ở mặt nước."""
        if not self._at_surface():
            return
        radius = self.t["interact_radius"]
        candidates = [
            n for n in self.nodes
            if n["regrow_ticks"] == 0 and math.dist(self.pos, n["pos"]) <= radius
        ]
        if not candidates:
            return
        target = min(candidates, key=lambda n: (math.dist(self.pos, n["pos"]), id_key(n["id"])))
        amount = self.t["node_yield"]
        free = self.t["hold_capacity"] - len(self.hold)
        if free < amount:
            events.append((
                "hold_full",
                {"action": "gather", "node_id": target["id"], "required": amount, "free": free},
            ))
            return
        self.hold.extend([target["kind"]] * amount)
        target["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": target["id"], "kind": target["kind"], "amount": amount}))

    def _try_catch_fish(self, events):
        """Bắt đàn cá gần nhất (hòa theo id_key) khi hết hồi chiêu và đang dưới nước."""
        if self.catch_cd_ticks != 0 or self._at_surface():
            return
        radius = self.t["catch_radius"]
        candidates = [f for f in self.fish if math.dist(self.pos, f["pos"]) <= radius]
        if not candidates:
            return
        target = min(candidates, key=lambda f: (math.dist(self.pos, f["pos"]), id_key(f["id"])))
        amount = self.t["fish_yield"][target["kind"]]
        free = self.t["hold_capacity"] - len(self.hold)
        if free < amount:
            events.append((
                "hold_full",
                {"action": "catch", "fish_id": target["id"], "required": amount, "free": free},
            ))
            return
        self.hold.extend([target["kind"]] * amount)
        self.fish.remove(target)
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        events.append(("fish_caught", {"fish_id": target["id"], "kind": target["kind"], "yield": amount}))

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    # --- cá bơi & sinh cá (v1.1) ------------------------------------------------
    def _step_fish_swim(self):
        """Duyệt đàn cá theo id, đổi hướng tại age_ticks % fish_turn_ticks == 0 trước khi bơi, phản xạ mép."""
        turn_ticks = int(self.t["fish_turn_ticks"])
        step_dist = self.t["fish_speed"] / TICK
        x_lo, x_hi = self.t["fish_x"]
        map_x_lo, map_x_hi = self.t["bounds"]["x"]
        map_d_lo, map_d_hi = self.t["bounds"]["d"]
        depths = self.t["fish_depths"]
        rng = self.rng.get("fish_swim")

        for f in sort_by_id(self.fish):
            f["age_ticks"] += 1
            if f["age_ticks"] % turn_ticks == 0:
                f["heading_deg"] = rng.uniform(0.0, 360.0)

            rad = math.radians(f["heading_deg"])
            vx = math.cos(rad) * step_dist
            vd = math.sin(rad) * step_dist
            old_x, old_d = f["pos"]
            d_lo, d_hi = depths[f["kind"]]

            nx, vx, rx = _reflect_axis(old_x, old_x + vx, vx, x_lo, x_hi, map_x_lo, map_x_hi)
            nd, vd, rd = _reflect_axis(old_d, old_d + vd, vd, d_lo, d_hi, map_d_lo, map_d_hi)
            f["pos"] = [nx, nd]
            if rx or rd:
                f["heading_deg"] = math.degrees(math.atan2(vd, vx)) % 360.0

    def _step_fish_spawn(self, events):
        """Tại phase_tick = 360 * k, sinh tối đa 1 đàn mới nếu < fish_max và có điểm cách > clearance."""
        spawn_ticks = int(self.t["fish_spawn_ticks"])
        if self.phase_tick <= 0 or self.phase_tick % spawn_ticks != 0:
            return
        if len(self.fish) >= int(self.t["fish_max"]):
            return

        clearance = float(self.t["fish_spawn_clearance"])
        spawn_x = self.t["fish_spawn_x"]
        spawn_depths = self.t["fish_spawn_depths"]
        weights = self.t["fish_weights"]

        valid_by_kind = {}
        for kind in sorted(spawn_depths):
            pts = []
            for x in spawn_x:
                for d in spawn_depths[kind]:
                    pt = [float(x), float(d)]
                    if math.dist(pt, self.pos) > clearance and all(
                        math.dist(pt, f["pos"]) > clearance for f in self.fish
                    ):
                        pts.append(pt)
            if pts:
                valid_by_kind[kind] = pts

        if not valid_by_kind:
            return

        rng = self.rng.get("fish_spawn")
        chosen_kind = _weighted_choice(rng, sorted(valid_by_kind), weights)
        pos = list(rng.choice(valid_by_kind[chosen_kind]))
        heading_deg = rng.uniform(0.0, 360.0)
        fid = self.ids.new("F")
        self.fish.append({
            "id": fid,
            "kind": chosen_kind,
            "pos": pos,
            "heading_deg": heading_deg,
            "age_ticks": 0,
        })
        events.append(("fish_spawned", {"id": fid, "kind": chosen_kind, "pos": list(pos)}))

    # --- sinh tồn (lát 1) -------------------------------------------------------
    def _step_region_transition(self, was_surface: bool, events: list):
        """Phát sự kiện `dive` hoặc `surface` khi chuyển phân vùng đầu/cuối bước."""
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_surface and now_surface:
            events.append(("surface", {"pos": list(self.pos)}))

    def _step_oxygen_and_choke(self, events: list) -> bool:
        """Cập nhật oxy theo độ sâu cuối bước, đếm ngạt và xử lý `choke` (v1.1: ngạt ngay bước chạm 0)."""
        if self._at_surface():
            refill = int(self.t["oxygen_refill_per_tick"])
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + refill)
            self.zero_oxy_ticks = 0
            return False

        choke_interval = int(self.t["choke_interval_ticks"])
        should_choke = False
        if self.oxygen_ticks > 0:
            self.oxygen_ticks -= 1
            self.zero_oxy_ticks = 0
            if self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"pos": list(self.pos)}))
                should_choke = True
        else:
            self.zero_oxy_ticks += 1
            if self.zero_oxy_ticks >= choke_interval:
                self.zero_oxy_ticks -= choke_interval
                should_choke = True

        if should_choke:
            self.hp = max(0, self.hp - 1)
            events.append(("choke", {"hp": self.hp}))
            if self.hp <= 0:
                self.hp = 0
                lost = list(reversed(self.hold))
                self._clear_hold()
                events.append(("faint", {"cause": "oxygen", "lost": lost, "hp": 0, "pos": list(self.pos)}))
                self._finish("fainted", events)
                return True
        return False

    def _update_survival(self, was_surface: bool, events: list) -> bool:
        """Chạy bước sinh tồn lát 1; trả True nếu lượt chơi kết thúc ngay."""
        self._step_region_transition(was_surface, events)
        return self._step_oxygen_and_choke(events)

    # --- giỏ LIFO (lát 1) -------------------------------------------------------
    def _hold_capacity(self) -> int:
        return int(self.t["hold_capacity"])

    def _hold_free(self) -> int:
        return max(0, self._hold_capacity() - len(self.hold))

    def _can_hold(self, count: int = 1) -> bool:
        return count >= 0 and len(self.hold) + count <= self._hold_capacity()

    def _push_hold(self, kind: str, count: int = 1) -> bool:
        """Đẩy `count` nguyên liệu vào cuối giỏ (LIFO) nếu đủ sức chứa."""
        if count < 0:
            raise ValueError("count phải >= 0")
        if not self._can_hold(count):
            return False
        self.hold.extend([kind] * count)
        return True

    def _pop_hold(self):
        """Lấy phần tử mới nhất ở cuối giỏ (LIFO); trả None nếu giỏ rỗng."""
        if not self.hold:
            return None
        return self.hold.pop()

    def _clear_hold(self):
        """Làm rỗng giỏ khi ngất."""
        self.hold = []

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
