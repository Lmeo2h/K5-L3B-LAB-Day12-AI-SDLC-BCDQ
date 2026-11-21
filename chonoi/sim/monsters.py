"""Cá Sấu Năm Chèo (`ca_sau`) cho chế độ `gather` (Phase 2 — TICKET-02)."""

import math

from ..ids import id_key, sort_by_id

TICK = 60.0

_DEFAULT_CFG = {
    "depth_range": [10.0, 30.0],
    "patrol_speed": 1.0,
    "chase_speed": 3.0,
    "recoil_speed": 2.0,
    "detect_radius": 10.0,
    "lose_radius": 16.0,
    "hit_radius": 1.5,
    "invuln_ticks": 90,
    "recoil_ticks": 60,
    "default": [
        {"id": "M1", "kind": "ca_sau", "pos": [60.0, 24.0], "waypoints": [[60.0, 24.0], [64.0, 24.0]], "min_day": 1},
        {"id": "M2", "kind": "ca_sau", "pos": [85.0, 18.0], "waypoints": [[85.0, 18.0], [89.0, 18.0]], "min_day": 3},
    ],
}


def monster_cfg(gather_tuning: dict) -> dict:
    """Lấy cấu hình quái vật từ `tuning['gather']` (tương thích cả v1.0 và v1.1)."""
    raw = gather_tuning.get("monsters")
    if isinstance(raw, dict):
        return {**_DEFAULT_CFG, **raw}
    return _DEFAULT_CFG


def _clamp_pos(pos: list, bounds: dict, depth_range: list):
    lo_x, hi_x = bounds["x"]
    lo_d = max(bounds["d"][0], depth_range[0])
    hi_d = min(bounds["d"][1], depth_range[1])
    pos[0] = min(max(float(pos[0]), float(lo_x)), float(hi_x))
    pos[1] = min(max(float(pos[1]), float(lo_d)), float(hi_d))


def _move_towards(pos: list, target: list, step_dist: float) -> bool:
    """Di chuyển tối đa `step_dist` tới `target`; trả True nếu đã chạm đích."""
    dx = target[0] - pos[0]
    dd = target[1] - pos[1]
    dist = math.hypot(dx, dd)
    if dist <= step_dist:
        pos[0] = float(target[0])
        pos[1] = float(target[1])
        return True
    pos[0] += (dx / dist) * step_dist
    pos[1] += (dd / dist) * step_dist
    return False


def init_monsters(gather_tuning: dict, scenario: dict, ids, day: int = 1) -> list:
    """Khởi tạo danh sách cá sấu từ `scenario['monsters']` hoặc mặc định theo `day`."""
    cfg = monster_cfg(gather_tuning)
    if "monsters" in scenario:
        src = scenario["monsters"]
    else:
        src = [m for m in cfg["default"] if day >= m.get("min_day", 1)]

    monsters = []
    for m in src:
        pos = [float(c) for c in m["pos"]]
        wps = [[float(c) for c in wp] for wp in m.get("waypoints", [pos, pos])]
        entry = {
            "id": m["id"],
            "kind": m.get("kind", "ca_sau"),
            "pos": pos,
            "waypoints": wps,
            "state": m.get("state", "patrol"),
            "target_idx": int(m.get("target_idx", 1 if wps and pos == wps[0] else 0)),
            "recoil_ticks_left": int(m.get("recoil_ticks_left", 0)),
            "recoil_origin": [float(c) for c in m["recoil_origin"]] if "recoil_origin" in m else list(pos),
        }
        ids.reserve(entry["id"])
        monsters.append(entry)
    return monsters


def monsters_snapshot(monsters: list) -> list:
    """Xuất danh sách `monsters[]` đã sắp theo `id_key` cho snapshot."""
    return [
        {
            "id": m["id"],
            "kind": m["kind"],
            "pos": list(m["pos"]),
            "state": m["state"],
            "waypoints": [list(wp) for wp in m["waypoints"]],
            "target_idx": m["target_idx"],
            "recoil_ticks_left": m["recoil_ticks_left"],
        }
        for m in sort_by_id(monsters)
    ]


def _step_single_monster(m: dict, player_pos: list, bounds: dict, cfg: dict) -> bool:
    """Cập nhật một cá sấu; trả True nếu con này đang ở trạng thái `recoil` trong bước."""
    depth_range = cfg["depth_range"]
    depth_min = float(depth_range[0])

    if m["state"] == "recoil":
        origin = m.get("recoil_origin", m["pos"])
        dx = m["pos"][0] - origin[0]
        dd = m["pos"][1] - origin[1]
        dist = math.hypot(dx, dd)
        step_dist = float(cfg["recoil_speed"]) / TICK
        if dist == 0.0:
            ux, ud = 1.0, 0.0
        else:
            ux, ud = dx / dist, dd / dist
        m["pos"][0] += ux * step_dist
        m["pos"][1] += ud * step_dist
        _clamp_pos(m["pos"], bounds, depth_range)
        m["recoil_ticks_left"] = max(0, m["recoil_ticks_left"] - 1)
        if m["recoil_ticks_left"] == 0:
            m["state"] = "patrol"
        return True

    dist_player = math.dist(m["pos"], player_pos)
    in_deep = player_pos[1] >= depth_min
    if m["state"] == "patrol":
        if in_deep and dist_player <= float(cfg["detect_radius"]):
            m["state"] = "chase"
    elif m["state"] == "chase":
        if not in_deep or dist_player > float(cfg["lose_radius"]):
            m["state"] = "patrol"

    if m["state"] == "chase":
        _move_towards(m["pos"], player_pos, float(cfg["chase_speed"]) / TICK)
    else:
        wp = m["waypoints"][m["target_idx"]]
        if _move_towards(m["pos"], wp, float(cfg["patrol_speed"]) / TICK):
            m["target_idx"] = 1 - m["target_idx"]

    _clamp_pos(m["pos"], bounds, depth_range)
    return False


def step_monsters(sim, events: list) -> bool:
    """Cập nhật toàn bộ cá sấu theo `id` và xử lý tối đa 1 va chạm. Trả True nếu ngất."""
    cfg = monster_cfg(sim.t)
    bounds = sim.t["bounds"]
    depth_min = float(cfg["depth_range"][0])
    recoiled = set()

    for m in sort_by_id(sim.monsters):
        if _step_single_monster(m, sim.pos, bounds, cfg):
            recoiled.add(m["id"])

    if sim.invuln_ticks != 0 or sim.pos[1] < depth_min:
        return False

    hit_radius = float(cfg["hit_radius"])
    candidates = [
        m for m in sim.monsters
        if m["state"] != "recoil"
        and m["id"] not in recoiled
        and math.dist(m["pos"], sim.pos) <= hit_radius
    ]
    if not candidates:
        return False

    target = min(candidates, key=lambda m: (math.dist(m["pos"], sim.pos), id_key(m["id"])))
    sim.hp = max(0, sim.hp - 1)
    drop_n = len(sim.hold) // 2
    lost = [sim._pop_hold() for _ in range(drop_n)]
    sim.invuln_ticks = int(cfg["invuln_ticks"])
    events.append((
        "monster_hit",
        {"monster_id": target["id"], "hp": sim.hp, "lost": lost, "pos": list(sim.pos)},
    ))

    target["state"] = "recoil"
    target["recoil_ticks_left"] = int(cfg["recoil_ticks"])
    target["recoil_origin"] = list(sim.pos)

    if sim.hp <= 0:
        sim.hp = 0
        faint_lost = []
        while sim.hold:
            faint_lost.append(sim._pop_hold())
        events.append((
            "faint",
            {"cause": "monster", "lost": faint_lost, "hp": 0, "pos": list(sim.pos)},
        ))
        sim._finish("fainted", events)
        return True
    return False
