"""Đọc game.contract.json và kiểm dải hợp lệ của tuning v1.1 (TICKET-02, Test Contract v1.1)."""

from collections import Counter
import json
import os

from .errors import BadInput
from .inventory import KINDS_P2

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")

FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _between(name, v, lo, hi):
    if not _num(v) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải trong [{lo}, {hi}], đang là {v!r}")


SUPPORTED_VERSIONS = ("1.1", "1.2", "1.3")


def load_contract(path=DEFAULT_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được {path}: {e}")
    ver = c.get("contract_version")
    if ver not in SUPPORTED_VERSIONS:
        raise BadInput(f"contract_version phải là một trong {SUPPORTED_VERSIONS}, đang là {ver!r}")
    if ver == "1.3":
        for key in ("bench_cmd", "soak_cmd"):
            val = c.get(key)
            if not isinstance(val, str) or not val.strip():
                raise BadInput(f"{key} phải là chuỗi khác rỗng cho contract_version 1.3")
    validate_tuning(c.get("tuning"), contract_version=ver)
    return c


def _int_between(name, v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải là số nguyên trong [{lo}, {hi}], đang là {v!r}")


def _pos_in(name, pos, bounds, keys):
    if not isinstance(pos, list) or len(pos) != 2 or not all(_num(c) for c in pos):
        raise BadInput(f"tuning.{name} phải là [số, số]")
    for c, k in zip(pos, keys):
        lo, hi = bounds[k]
        if not (lo <= c <= hi):
            raise BadInput(f"tuning.{name} nằm ngoài vùng {k} ∈ [{lo}, {hi}]")


def _range_pair(name, pair, lo_min, hi_max):
    if not (isinstance(pair, list) and len(pair) == 2 and all(_num(c) for c in pair)):
        raise BadInput(f"tuning.{name} phải là [min, max]")
    if not (lo_min <= pair[0] < pair[1] <= hi_max):
        raise BadInput(f"tuning.{name} phải thỏa {lo_min} <= min < max <= {hi_max}, đang là {pair!r}")


def _bounds(name, b, keys):
    if not isinstance(b, dict) or set(b) != set(keys):
        raise BadInput(f"tuning.{name}.bounds phải có đúng khóa {list(keys)}")
    for k in keys:
        v = b[k]
        if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and v[0] == 0 and v[1] > 0):
            raise BadInput(f"tuning.{name}.bounds.{k} phải là [0, số dương]")


def _validate_gather_fish(g, b, fy):
    _int_between("gather.fish_max", g.get("fish_max"), 1, 100)
    _int_between("gather.fish_initial", g.get("fish_initial"), 1, g["fish_max"])
    _between("gather.fish_speed", g.get("fish_speed"), 0.1, 20)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 10_000)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 10_000)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0, 20)
    _range_pair("gather.fish_x", g.get("fish_x"), b["x"][0], b["x"][1])
    fx_lo, fx_hi = g["fish_x"]

    depths = g.get("fish_depths")
    if not isinstance(depths, dict) or set(depths) != set(FISH_KINDS):
        raise BadInput("tuning.gather.fish_depths phải có đủ 3 loài cá")
    for k in FISH_KINDS:
        _range_pair(f"gather.fish_depths.{k}", depths[k], g["surface_depth"], b["d"][1])
        if depths[k][0] <= g["surface_depth"]:
            raise BadInput(f"tuning.gather.fish_depths.{k} phải dưới mặt nước (> {g['surface_depth']})")

    sx = g.get("fish_spawn_x")
    if not isinstance(sx, list) or not sx or not all(_num(x) and fx_lo <= x <= fx_hi for x in sx):
        raise BadInput("tuning.gather.fish_spawn_x phải là mảng số thuộc fish_x")

    sd = g.get("fish_spawn_depths")
    if not isinstance(sd, dict) or set(sd) != set(FISH_KINDS):
        raise BadInput("tuning.gather.fish_spawn_depths phải có đủ 3 loài cá")
    distinct_pts = set()
    for k in FISH_KINDS:
        d_lo, d_hi = depths[k]
        arr = sd[k]
        if not isinstance(arr, list) or not arr or not all(_num(d) and d_lo <= d <= d_hi for d in arr):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{k} phải là mảng số thuộc fish_depths.{k}")
        for x in sx:
            for d in arr:
                distinct_pts.add((x, d))
    if len(distinct_pts) < g["fish_initial"]:
        raise BadInput("số điểm sinh phân biệt phải >= fish_initial")

    fw = g.get("fish_weights")
    if not isinstance(fw, dict) or set(fw) != set(FISH_KINDS):
        raise BadInput("tuning.gather.fish_weights phải có đủ 3 loài cá")
    if any(not _num(fw[k]) or fw[k] <= 0 for k in FISH_KINDS):
        raise BadInput("tuning.gather.fish_weights các loài phải > 0")


def _validate_gather_monsters(m, b):
    if not isinstance(m, dict):
        raise BadInput("tuning.gather.monsters phải là object")
    _int_between("gather.monsters.invuln_ticks", m.get("invuln_ticks"), 0, 1000)
    _between("gather.monsters.loss_ratio", m.get("loss_ratio"), 0, 1)
    species = m.get("species")
    if not isinstance(species, dict) or "ca_sau" not in species:
        raise BadInput("tuning.gather.monsters.species phải có ca_sau")
    for sname, sp in species.items():
        if not isinstance(sp, dict):
            raise BadInput(f"tuning.gather.monsters.species.{sname} phải là object")
        _between(f"gather.monsters.species.{sname}.patrol_speed", sp.get("patrol_speed"), 0.1, 20)
        _between(f"gather.monsters.species.{sname}.chase_speed", sp.get("chase_speed"), 0.1, 20)
        _between(f"gather.monsters.species.{sname}.detect_radius", sp.get("detect_radius"), 0.5, 100)
        _between(f"gather.monsters.species.{sname}.exit_radius", sp.get("exit_radius"), sp["detect_radius"], 100)
        _range_pair(f"gather.monsters.species.{sname}.depths", sp.get("depths"), b["d"][0], b["d"][1])
        _between(f"gather.monsters.species.{sname}.hit_radius", sp.get("hit_radius"), 0.1, 10)
        _int_between(f"gather.monsters.species.{sname}.recoil_ticks", sp.get("recoil_ticks"), 1, 1000)
        _between(f"gather.monsters.species.{sname}.recoil_dist", sp.get("recoil_dist"), 0, 20)
    spawns = m.get("spawns")
    if not isinstance(spawns, list) or not spawns:
        raise BadInput("tuning.gather.monsters.spawns phải là mảng không rỗng")
    seen = set()
    for spw in spawns:
        if not isinstance(spw, dict) or not isinstance(spw.get("id"), str) or not spw["id"] or spw["id"] in seen:
            raise BadInput("tuning.gather.monsters.spawns: mỗi phần tử cần id duy nhất")
        seen.add(spw["id"])
        kind = spw.get("kind")
        if kind not in species:
            raise BadInput(f"tuning.gather.monsters.spawns.{spw['id']}: kind lạ {kind!r}")
        d_lo, d_hi = species[kind]["depths"]
        _pos_in(f"gather.monsters.spawns.{spw['id']}.pos", spw.get("pos"), b, ("x", "d"))
        if not (d_lo <= spw["pos"][1] <= d_hi):
            raise BadInput(f"tuning.gather.monsters.spawns.{spw['id']}.pos ngoài depths {kind}")
        wps = spw.get("waypoints")
        if not isinstance(wps, list) or len(wps) != 2:
            raise BadInput(f"tuning.gather.monsters.spawns.{spw['id']}.waypoints phải có đúng 2 điểm")
        for idx, wp in enumerate(wps):
            _pos_in(f"gather.monsters.spawns.{spw['id']}.waypoints[{idx}]", wp, b, ("x", "d"))
            if not (d_lo <= wp[1] <= d_hi):
                raise BadInput(f"tuning.gather.monsters.spawns.{spw['id']}.waypoints[{idx}] ngoài depths {kind}")
        _int_between(f"gather.monsters.spawns.{spw['id']}.from_day", spw.get("from_day"), 1, 10)


def _validate_gather(g):
    """Dải hợp lệ v1.1 theo TICKET-02."""
    _between("gather.duration_s", g.get("duration_s"), 60, 600)
    _bounds("gather", g.get("bounds"), ("x", "d"))
    b = g["bounds"]
    _between("gather.dock_radius", g.get("dock_radius"), 0.5, 5)
    _between("gather.interact_radius", g.get("interact_radius"), 0.5, 5)
    _between("gather.catch_radius", g.get("catch_radius"), 0.5, 5)
    _between("gather.swim_speed", g.get("swim_speed"), 1, 10)
    _between("gather.catch_cooldown_s", g.get("catch_cooldown_s"), 0, 10)
    _between("gather.oxygen_max_s", g.get("oxygen_max_s"), 10, 120)
    _int_between("gather.ramp_max_ticks", g.get("ramp_max_ticks"), 0, 6)
    _int_between("gather.hold_capacity", g.get("hold_capacity"), 4, 30)
    _int_between("gather.hp_max", g.get("hp_max"), 1, 99)
    _int_between("gather.oxygen_refill_per_tick", g.get("oxygen_refill_per_tick"), 1, 10_000)
    _int_between("gather.choke_interval_ticks", g.get("choke_interval_ticks"), 1, 10_000)
    _int_between("gather.node_yield", g.get("node_yield"), 1, 12)
    _between("gather.regrow_s", g.get("regrow_s"), 0.1, 600)
    _between("gather.surface_depth", g.get("surface_depth"), 0, 5)
    _pos_in("gather.dock_pos", g.get("dock_pos"), b, ("x", "d"))
    _pos_in("gather.start_pos", g.get("start_pos"), b, ("x", "d"))
    if not _num(g.get("start_heading_deg")):
        raise BadInput("tuning.gather.start_heading_deg phải là số")
    fy = g.get("fish_yield")
    if not isinstance(fy, dict) or not set(FISH_KINDS) <= set(fy):
        raise BadInput("tuning.gather.fish_yield phải có đủ ca_linh, ca_loc, ca_keo")
    for k, v in fy.items():
        _int_between(f"gather.fish_yield.{k}", v, 1, g["hold_capacity"])
    nodes = g.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise BadInput("tuning.gather.nodes phải là mảng không rỗng")
    seen, kinds = set(), set()
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get("id"), str) or n["id"] in seen:
            raise BadInput("tuning.gather.nodes: mỗi nút cần id duy nhất")
        seen.add(n["id"])
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind phải thuộc {NODE_KINDS}")
        kinds.add(n["kind"])
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    if kinds != set(NODE_KINDS):
        raise BadInput(f"tuning.gather.nodes phải có đủ các loại {NODE_KINDS}")
    _validate_gather_fish(g, b, fy)
    _validate_gather_monsters(g.get("monsters"), b)


def _validate_quan_and_menu(q, menu):
    _between("quan.duration_s", q.get("duration_s"), 60, 600)
    _bounds("quan", q.get("bounds"), ("x", "z"))
    qb = q["bounds"]
    _pos_in("quan.start_pos", q.get("start_pos"), qb, ("x", "z"))
    _between("quan.patience_s", q.get("patience_s"), 20, 180)
    _between("quan.walk_speed", q.get("walk_speed"), 1, 10)
    _between("quan.interact_radius", q.get("interact_radius"), 0.5, 5)
    _int_between("quan.ramp_max_ticks", q.get("ramp_max_ticks", 6), 0, 6)
    _between("quan.eat_s", q.get("eat_s"), 0.1, 600)
    _between("quan.customer_interval_s", q.get("customer_interval_s"), 0.1, 600)
    _int_between("quan.first_customer_tick", q.get("first_customer_tick"), 1, int(q["duration_s"] * 60) - 1)
    _int_between("quan.carry_limit", q.get("carry_limit", 1), 1, 10)
    if not (_num(q.get("tip_rate")) and q["tip_rate"] > 0 and _num(q.get("left_reputation_delta"))
            and q["left_reputation_delta"] < 0):
        raise BadInput("tip_rate phải > 0 và left_reputation_delta phải < 0")
    ratio = q.get("tip_min_patience_ratio")
    if not (_num(ratio) and 0 < ratio <= 1):
        raise BadInput("quan.tip_min_patience_ratio phải thuộc (0, 1]")
    if not (_num(q.get("tip_reputation")) and q["tip_reputation"] > 0):
        raise BadInput("quan.tip_reputation phải > 0")
    if q.get("burn_s") is not None:
        raise BadInput("burn_s phải là null trong lõi v1.1")
    for kind in ("stoves", "tables"):
        arr = q.get(kind)
        if not isinstance(arr, list) or not arr:
            raise BadInput(f"tuning.quan.{kind} phải là mảng không rỗng")
        seen = set()
        for e in arr:
            if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"] or e["id"] in seen:
                raise BadInput(f"tuning.quan.{kind}: mỗi phần tử cần id duy nhất")
            seen.add(e["id"])
            _pos_in(f"quan.{kind}.{e['id']}.pos", e.get("pos"), qb, ("x", "z"))

    if len(menu) < 6:
        raise BadInput("tuning.menu phải có đủ 6 món ở v1.1")
    for dish_id, d in menu.items():
        if not isinstance(d, dict):
            raise BadInput(f"menu.{dish_id} phải là object")
        price, cook, recipe = d.get("price"), d.get("cook_s"), d.get("recipe")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
        if not isinstance(recipe, dict) or not recipe:
            raise BadInput(f"menu.{dish_id}.recipe phải là object không rỗng")
        for ing, cnt in recipe.items():
            if ing not in KINDS_P2 or isinstance(cnt, bool) or not isinstance(cnt, int) or cnt <= 0:
                raise BadInput(f"menu.{dish_id}.recipe.{ing}: nguyên liệu hoặc số lượng sai")


def _validate_day_plan(dp, menu):
    if not isinstance(dp, list) or len(dp) != 5:
        raise BadInput("tuning.day_plan phải là mảng đúng 5 ngày")
    for idx, entry in enumerate(dp, 1):
        if not isinstance(entry, dict) or entry.get("day") != idx:
            raise BadInput(f"tuning.day_plan[{idx - 1}].day phải là {idx}")
        dishes = entry.get("dishes")
        ings = entry.get("ingredients")
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"tuning.day_plan[{idx - 1}].dishes phải là object không rỗng")
        expected = Counter()
        for dish_id, count in dishes.items():
            if dish_id not in menu:
                raise BadInput(f"tuning.day_plan[{idx - 1}]: món lạ {dish_id!r}")
            if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
                raise BadInput(f"tuning.day_plan[{idx - 1}].dishes.{dish_id} phải là số nguyên dương")
            for ing, req in menu[dish_id]["recipe"].items():
                expected[ing] += req * count
        if not isinstance(ings, dict) or Counter(ings) != expected:
            raise BadInput(f"tuning.day_plan[{idx - 1}].ingredients không khớp tổng công thức")


def _validate_shop(shop):
    if not isinstance(shop, dict):
        raise BadInput("tuning.shop phải là object")
    _int_between("shop.max_ticks", shop.get("max_ticks"), 1, 10_000)
    upgrades = shop.get("upgrades")
    if not isinstance(upgrades, dict) or not {"oxygen", "hp"} <= set(upgrades):
        raise BadInput("tuning.shop.upgrades phải có oxygen và hp")
    for key, stat_key in (("oxygen", "oxygen_max_s"), ("hp", "hp_max")):
        tiers = upgrades[key]
        if not isinstance(tiers, list) or not tiers:
            raise BadInput(f"tuning.shop.upgrades.{key} phải là mảng không rỗng")
        prev_stat = 0
        for idx, tier in enumerate(tiers, 1):
            if not isinstance(tier, dict) or tier.get("level") != idx:
                raise BadInput(f"tuning.shop.upgrades.{key}[{idx - 1}].level phải là {idx}")
            price = tier.get("price")
            stat = tier.get(stat_key)
            if isinstance(price, bool) or not isinstance(price, int) or price <= 0:
                raise BadInput(f"tuning.shop.upgrades.{key}[{idx - 1}].price phải > 0")
            if not _num(stat) or stat <= prev_stat:
                raise BadInput(f"tuning.shop.upgrades.{key}[{idx - 1}].{stat_key} phải tăng dần")
            prev_stat = stat


def _validate_freshness(f):
    if not isinstance(f, dict):
        raise BadInput("tuning.freshness phải là object")
    initial = f.get("initial")
    if isinstance(initial, bool) or not _num(initial) or initial != 100:
        raise BadInput(f"tuning.freshness.initial phải là 100, đang là {initial!r}")
    for key in ("gather_decay_per_s", "quan_decay_per_s"):
        v = f.get(key)
        if not _num(v) or v <= 0:
            raise BadInput(f"tuning.freshness.{key} phải > 0, đang là {v!r}")
    spoiled_below = f.get("spoiled_below")
    if not _num(spoiled_below) or not (0 < spoiled_below < initial):
        raise BadInput(f"tuning.freshness.spoiled_below phải trong (0, {initial}), đang là {spoiled_below!r}")


def validate_tuning(t, contract_version="1.1"):
    if not isinstance(t, dict):
        raise BadInput("thiếu khối tuning")
    g, q, menu = t.get("gather"), t.get("quan"), t.get("menu")
    if not isinstance(g, dict) or not isinstance(q, dict) or not isinstance(menu, dict):
        raise BadInput("tuning phải có gather, quan, menu")
    if contract_version in ("1.2", "1.3") or "freshness" in t:
        _validate_freshness(t.get("freshness"))
    _validate_gather(g)
    _validate_quan_and_menu(q, menu)
    _validate_day_plan(t.get("day_plan"), menu)
    _validate_shop(t.get("shop"))
