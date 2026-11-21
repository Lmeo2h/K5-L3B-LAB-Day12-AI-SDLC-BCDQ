"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

Kiểm cú pháp, miền dữ liệu và mâu thuẫn giữa các thực thể trong fixture.
"""

import json

from collections import Counter

from .errors import BadInput
from .ids import id_key, sort_by_id
from .inventory import KINDS_P2, _current_contract_version, fresh_to_units, validate_items, validate_items_v12

GATHER_KEYS = {"player", "hold", "nodes", "fish", "monsters", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "state", "target_idx",
                "recoil_ticks_left", "recoil_origin", "state_ticks_left", "recoil_dir"}
MONSTER_STATES = {"patrol", "chase", "recoil"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
NODE_KEYS = {"id", "kind", "pos", "regrow_ticks"}
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
FISH_KEYS = {"id", "kind", "pos", "heading_deg", "age_ticks"}
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                 "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}
DISH_KEYS = {"order_id", "dish_id", "base_price"}
DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        data = {}
    else:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            raise BadInput(f"không đọc được scenario {path}: {e}") from e
    if not isinstance(data, dict):
        raise BadInput("scenario phải là object")
    if mode == "day":
        return _validate_day(data, tuning)
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    return _validate_mode_block(mode, data.get(mode, {}), tuning)


def _validate_mode_block(mode, block, tuning):
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = round(tuning[mode]["duration_s"] * tuning["tick_hz"])
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
    return block


def _validate_day(data, tuning):
    if data.keys() - {"gather", "quan", "day"}:
        raise BadInput("scenario day chỉ nhận các khối gather, quan và day")
    quan = data.get("quan", {})
    if isinstance(quan, dict) and quan.keys() & {"stock", "reputation"}:
        raise BadInput("day không nhận quan.stock hoặc quan.reputation")
    for mode in ("gather", "quan"):
        if mode in data:
            _validate_mode_block(mode, data[mode], tuning)

    day = data.get("day", {})
    if not isinstance(day, dict) or day.keys() - DAY_KEYS:
        raise BadInput("khối day phải là object và chỉ chứa các trường được hỗ trợ")
    money, earned = day.get("money", 0), day.get("earned", 0)
    _nonneg_int("day.money", money)
    _nonneg_int("day.earned", earned)
    if money > earned or ((money or earned) and not {"money", "earned"} <= day.keys()):
        raise BadInput("day cần cả money và earned khi có số dư đầu kỳ, với money <= earned")
    if "reputation" in day:
        _validate_quan_reputation(day["reputation"], tuning["quan"], "day.reputation")
    if not isinstance(day.get("upgrades", {}), dict):
        raise BadInput("day.upgrades phải là object")
    preset = tuning.get("day_plan")
    if not isinstance(preset, list) or len(preset) != 5:
        raise BadInput("tuning.day_plan phải có đúng năm kế hoạch")
    menu = tuning["menu"]
    expected_days = set()
    for plan in preset:
        if not isinstance(plan, dict) or plan.keys() != {"day", "dishes", "ingredients"}:
            raise BadInput("tuning.day_plan cần day, dishes và ingredients")
        number = plan["day"]
        _nonneg_int("tuning.day_plan.day", number)
        if str(number) in expected_days or not 1 <= number <= len(preset):
            raise BadInput("tuning.day_plan có số Ngày trùng hoặc ngoài preset")
        _day_plan_ingredients(plan, menu)
        expected_days.add(str(number))
    if "day_plan" in day:
        overrides = day["day_plan"]
        if not isinstance(overrides, dict) or overrides.keys() - expected_days:
            raise BadInput("day.day_plan phải là map theo số Ngày trong preset")
        for number, plan in overrides.items():
            if not isinstance(plan, dict) or plan.keys() - {"dishes", "ingredients"}:
                raise BadInput(f"day.day_plan.{number}: chỉ nhận dishes và ingredients")
            plan["ingredients"] = _day_plan_ingredients(plan, menu)
    return data


def _day_plan_ingredients(plan, menu):
    dishes = plan.get("dishes")
    if not isinstance(dishes, dict) or not dishes:
        raise BadInput("day_plan.dishes phải là map món có ít nhất một món")
    required = Counter()
    for dish, servings in dishes.items():
        _nonneg_int(f"day_plan.dishes.{dish}", servings)
        if dish not in menu or servings == 0:
            raise BadInput("day_plan: món không có trong menu hoặc số suất không dương")
        required.update({kind: qty * servings for kind, qty in menu[dish]["recipe"].items()})
    if "ingredients" in plan:
        ingredients = plan["ingredients"]
        if validate_items(ingredients, kinds=required) != required:
            raise BadInput("day_plan.ingredients không khớp tổng công thức và số suất")
    return dict(sorted(required.items()))


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish", "monsters"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = validate_items_v12(b["hold"], kinds=KINDS_P2)
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        extra_n = set(n) - NODE_KEYS
        if extra_n:
            raise BadInput(f"nodes.{n['id']}: trường lạ {sorted(extra_n)}")
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        extra_f = set(f) - FISH_KEYS
        if extra_f:
            raise BadInput(f"fish.{f['id']}: trường lạ {sorted(extra_f)}")
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    _validate_monsters(b.get("monsters", []), bounds, g)


def _validate_monsters(monsters, bounds, gather_tuning):
    cfg = gather_tuning.get("monsters") if isinstance(gather_tuning.get("monsters"), dict) else {}
    sp = cfg.get("species", {}).get("ca_sau", {}) if isinstance(cfg.get("species"), dict) else {}
    depth_lo, depth_hi = sp.get("depths", cfg.get("depth_range", [10.0, 30.0]))
    recoil_max = int(sp.get("recoil_ticks", cfg.get("recoil_ticks", 60)))
    for m in monsters:
        mid = m["id"]
        extra = set(m) - MONSTER_KEYS
        if extra:
            raise BadInput(f"monsters.{mid}: trường lạ {sorted(extra)}")
        if m.get("kind") != "ca_sau":
            raise BadInput(f"monsters.{mid}: kind phải là 'ca_sau'")
        _pos(f"monsters.{mid}.pos", m.get("pos"), bounds)
        if not (depth_lo <= m["pos"][1] <= depth_hi):
            raise BadInput(f"monsters.{mid}.pos: độ sâu phải trong [{depth_lo}, {depth_hi}]")
        if "waypoints" in m:
            wps = m["waypoints"]
            if not isinstance(wps, list) or len(wps) != 2:
                raise BadInput(f"monsters.{mid}.waypoints phải gồm đúng 2 mốc [x, d]")
            for idx, wp in enumerate(wps):
                _pos(f"monsters.{mid}.waypoints[{idx}]", wp, bounds)
                if not (depth_lo <= wp[1] <= depth_hi):
                    raise BadInput(f"monsters.{mid}.waypoints[{idx}]: độ sâu phải trong [{depth_lo}, {depth_hi}]")
        state = m.get("state", "patrol")
        if "state" in m and state not in MONSTER_STATES:
            raise BadInput(f"monsters.{mid}.state phải thuộc {sorted(MONSTER_STATES)}")
        if "target_idx" in m:
            ti = m["target_idx"]
            if isinstance(ti, bool) or not isinstance(ti, int) or ti not in (0, 1):
                raise BadInput(f"monsters.{mid}.target_idx phải là 0 hoặc 1")
        for timer_key in ("recoil_ticks_left", "state_ticks_left"):
            if timer_key in m:
                rtl = m[timer_key]
                _nonneg_int(f"monsters.{mid}.{timer_key}", rtl)
                if rtl > recoil_max:
                    raise BadInput(f"monsters.{mid}.{timer_key} vượt quá {recoil_max}")
                if state == "recoil" and rtl <= 0:
                    raise BadInput(f"monsters.{mid}.{timer_key} phải dương khi state='recoil'")
        if "recoil_origin" in m:
            _pos(f"monsters.{mid}.recoil_origin", m["recoil_origin"], bounds)
        if "recoil_dir" in m:
            rd = m["recoil_dir"]
            if rd is not None:
                if not (isinstance(rd, list) and len(rd) == 2 and all(_num(c) for c in rd)):
                    raise BadInput(f"monsters.{mid}.recoil_dir phải là vector [x, d] hoặc null")
                if abs((rd[0] ** 2 + rd[1] ** 2) ** 0.5 - 1.0) > 1e-2:
                    raise BadInput(f"monsters.{mid}.recoil_dir phải là vector đơn vị")
                if state != "recoil":
                    raise BadInput(f"monsters.{mid}.recoil_dir phải là null khi không ở recoil")
            elif state == "recoil":
                raise BadInput(f"monsters.{mid}.recoil_dir cần vector đơn vị khi state='recoil'")


def _validate_quan(b, tuning):
    t = tuning["quan"]
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        stock = prepare_quan_stock(b["stock"], tuning)
    else:
        stock = None
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = t["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {table["id"] for table in t["tables"]}
    for c in b.get("customers", []):
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
    if not isinstance(b.get("random_customers", True), bool):
        raise BadInput("random_customers phải là boolean")
    _validate_quan_reputation(b.get("reputation", t["reputation_initial"]), t, "quan.reputation")

    customers = prepare_quan_customers(b, tuning, stock)
    dishes = [b["hand"]] if b.get("hand") is not None else []
    stove_keys = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
    for kind, keys in (("tables", {"id", "pos"}), ("stoves", stove_keys)):
        known_ids = {entity["id"] for entity in t[kind]}
        for entity in b.get(kind, []):
            if entity["id"] not in known_ids or entity.keys() - keys:
                raise BadInput(f"{kind}.{entity['id']}: id hoặc trường không hợp lệ")
            if "pos" in entity:
                _pos(f"{kind}.{entity['id']}.pos", entity["pos"], qb, axes=("x", "z"))
    for stove in b.get("stoves", []):
        dish = _stove_fixture_dish(stove)
        if dish is not None:
            dishes.append(dish)
    freshness = tuning.get("freshness") if quan_uses_items(tuning, stock) else None
    _validate_quan_dishes(customers, dishes, tuning["menu"], freshness)


def _validate_quan_reputation(value, t, field):
    if not _num(value) or not t["reputation_min"] <= value <= t["reputation_max"]:
        raise BadInput(f"{field} nằm ngoài miền uy tín")


def _quan_ingredient_kinds(menu):
    return set(KINDS_P2).union(*(dish["recipe"] for dish in menu.values()))


def quan_uses_items(tuning, stock=None):
    if "freshness" not in tuning:
        return False
    if isinstance(stock, list):
        return True
    version = tuning.get("contract_version") or _current_contract_version()
    return version == "1.2"


def prepare_quan_stock(stock, tuning):
    if not quan_uses_items(tuning, stock):
        return validate_items(stock, kinds=_quan_ingredient_kinds(tuning["menu"]))
    items = validate_items_v12(stock)
    threshold = tuning["freshness"]["spoiled_below"]
    threshold_units = fresh_to_units(threshold)
    result = []
    for item in items:
        units = fresh_to_units(item["fresh"])
        if item["fresh"] < threshold:
            units = min(units, threshold_units - 1)
        result.append(dict(item, _units=units))
    return sort_by_id(result)


def select_quan_items(stock, held, recipe, spoiled_below):
    """Return a full reservation, or None without claiming any item."""
    remaining = dict(recipe)
    chosen = []
    candidates = sorted(stock, key=lambda item: (-item["_units"], id_key(item["id"])))
    for item in candidates:
        kind = item["kind"]
        if item["_units"] >= spoiled_below and item["id"] not in held and remaining.get(kind, 0):
            chosen.append(item)
            remaining[kind] -= 1
    if any(remaining.values()):
        return None
    return [item["id"] for item in sort_by_id(chosen)]


def prepare_quan_customers(scenario, tuning, stock, *, menu=None):
    """Dựng khách theo mục D. Kho file chỉ có sau khi CLI đã đọc scenario."""
    patience = round(tuning["quan"]["patience_s"] * tuning["tick_hz"])
    full_menu = tuning["menu"]
    menu = full_menu if menu is None else menu
    kinds = _quan_ingredient_kinds(full_menu)
    fresh = quan_uses_items(tuning, stock)
    customers = []
    claimed = set()
    for fixture in scenario.get("customers", []):
        label = f"customers.{fixture['id']}"
        if fixture.keys() - CUSTOMER_KEYS:
            raise BadInput(f"{label}: trường không hỗ trợ")
        customer = dict({"dish_id": None, "order_tick": 0, "state": "waiting",
                         "patience_ticks_left": patience, "eat_ticks_left": 0,
                         "order_status": "reserved", "base_price": 0, "tip": 0}, **fixture)
        for key in ("order_tick", "patience_ticks_left", "eat_ticks_left", "base_price", "tip"):
            _nonneg_int(f"{label}.{key}", customer[key])
        state, status, dish = customer["state"], customer["order_status"], customer["dish_id"]
        if state not in ("waiting", "eating") or status not in ("reserved", "assigned", "unfulfillable", "served"):
            raise BadInput(f"{label}: trạng thái khách hoặc đơn không hợp lệ")
        if not (isinstance(dish, str) and dish in menu) and not (dish is None and status == "unfulfillable"):
            raise BadInput(f"{label}: món không hợp lệ")
        if state == "eating":
            if (status != "served" or customer["eat_ticks_left"] == 0
                    or not {"base_price", "tip"} <= fixture.keys()
                    or (not fresh and not customer["base_price"])):
                raise BadInput(f"{label}: khách đang ăn cần đơn served, timer, base_price và tip")
        elif status == "served" or customer["eat_ticks_left"]:
            raise BadInput(f"{label}: khách đang chờ không thể có đơn served hoặc timer ăn")
        if fresh and status in ("assigned", "served") and "base_price" in fixture:
            _validate_fresh_price(customer["base_price"], menu[dish]["price"], tuning["freshness"])

        expected = menu[dish]["recipe"] if status == "reserved" else {}
        if fresh:
            if "reserved" in fixture:
                reserved = fixture["reserved"]
                if (not isinstance(reserved, list) or any(not isinstance(i, str) or not i for i in reserved)
                        or len(set(reserved)) != len(reserved) or (status != "reserved" and reserved)
                        or not claimed.isdisjoint(reserved)):
                    raise BadInput(f"{label}: reserved phải là mảng ID duy nhất khớp trạng thái đơn")
                customer["reserved"] = sorted(reserved, key=id_key)
                claimed.update(reserved)
            else:
                customer["reserved"] = None if status == "reserved" else []
        else:
            if "reserved" in fixture and validate_items(fixture["reserved"], kinds=kinds) != expected:
                raise BadInput(f"{label}: giữ chỗ không khớp công thức hoặc trạng thái đơn")
            customer["reserved"] = dict(expected)
        customers.append(customer)

    if stock is not None and fresh:
        _reserve_quan_fixture_items(customers, stock, menu, tuning["freshness"])
    elif stock is not None:
        held = Counter()
        for customer in sorted(customers, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            held.update(customer["reserved"])
            if any(amount > stock.get(kind, 0) for kind, amount in held.items()):
                raise BadInput(f"customers.{customer['id']}: nguyên liệu giữ chỗ vượt tồn kho")
    return customers


def _reserve_quan_fixture_items(customers, stock, menu, freshness):
    threshold = fresh_to_units(freshness["spoiled_below"])
    by_id = {item["id"]: item for item in stock}
    held = set()
    orders = [c for c in customers if c["order_status"] == "reserved"]
    for customer in orders:
        reserved = customer["reserved"]
        if reserved is None:
            continue
        recipe = menu[customer["dish_id"]]["recipe"]
        if (any(i in held or i not in by_id or by_id[i]["_units"] < threshold for i in reserved)
                or Counter(by_id[i]["kind"] for i in reserved) != recipe):
            raise BadInput(f"customers.{customer['id']}: ID giữ chỗ vắng, ươn, trùng hoặc sai công thức")
        held.update(reserved)
    for customer in sorted(orders, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
        if customer["reserved"] is not None:
            continue
        reserved = select_quan_items(stock, held, menu[customer["dish_id"]]["recipe"], threshold)
        if reserved is None:
            raise BadInput(f"customers.{customer['id']}: nguyên liệu giữ chỗ vượt tồn kho khả dụng")
        customer["reserved"] = reserved
        held.update(reserved)


def _stove_fixture_dish(stove):
    state, dish = stove.get("state", "idle"), stove.get("dish")
    cook, ready = stove.get("cook_ticks_left", 0), stove.get("ready_ticks", 0)
    _nonneg_int("stove.cook_ticks_left", cook)
    _nonneg_int("stove.ready_ticks", ready)
    if state not in ("idle", "cooking", "ready") or (state == "idle") != (dish is None):
        raise BadInput("bếp có trạng thái hoặc món không hợp lệ")
    if (state == "cooking") != (cook > 0) or (state != "ready" and ready):
        raise BadInput("bếp có bộ đếm mâu thuẫn với trạng thái")
    return dish


def _validate_fresh_price(price, listed, freshness):
    minimum = int(listed * freshness["spoiled_below"] / freshness["initial"])
    if not minimum <= price <= listed:
        raise BadInput("base_price ngoài miền giá theo độ tươi")


def _validate_quan_dishes(customers, dishes, menu, freshness):
    assigned = {c["id"]: c for c in customers if c["order_status"] == "assigned"}
    for dish in dishes:
        if not isinstance(dish, dict) or dish.keys() != DISH_KEYS or not isinstance(dish["order_id"], str):
            raise BadInput("payload món phải có order_id, dish_id và base_price")
        customer = assigned.pop(dish["order_id"], None)
        if customer is None or dish["dish_id"] != customer["dish_id"]:
            raise BadInput("món trùng hoặc không khớp đơn assigned")
        _nonneg_int("dish.base_price", dish["base_price"])
        if freshness is not None:
            _validate_fresh_price(dish["base_price"], menu[dish["dish_id"]]["price"], freshness)
            if customer["base_price"] not in (0, dish["base_price"]):
                raise BadInput("dish.base_price không khớp giá đã chốt của khách")
        elif dish["base_price"] == 0:
            raise BadInput("dish.base_price phải dương")
    if assigned:
        raise BadInput("đơn assigned phải có đúng một món trên bếp hoặc tay")
