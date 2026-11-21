"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

import math

from ..ids import id_key, sort_by_id
from ..scenario import prepare_quan_customers
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.tick_hz = tuning["tick_hz"]
        self.phase_tick = 0
        self.patience_ticks = round(t["patience_s"] * self.tick_hz)
        self.customer_interval_ticks = round(t["customer_interval_s"] * self.tick_hz)
        self.random_customers = scenario.get("random_customers", True)
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = prepare_quan_customers(scenario, tuning, self.stock)
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._tick_customer_patience()
        self._step_stoves(events)
        self._move(inp)
        if inp.pressed("interact"):
            self._handle_interact(events)
        if self.time_left_ticks > 0:
            self._remove_expired_customers(events)
            self._spawn_customer_if_due(events)
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    # --- Slice 4: bếp, bưng món, phục vụ & ưu tiên interact --------------------
    def _step_stoves(self, events):
        for stove in sort_by_id(self.stoves):
            if stove["state"] == "ready":
                stove["ready_ticks"] = stove.get("ready_ticks", 0) + 1
            elif stove["state"] == "cooking":
                stove["cook_ticks_left"] = max(0, stove["cook_ticks_left"] - 1)
                if stove["cook_ticks_left"] == 0:
                    stove["state"] = "ready"
                    stove["ready_ticks"] = 0
                    dish = stove["dish"]
                    events.append(("dish_ready", {
                        "stove_id": stove["id"],
                        "order_id": dish["order_id"],
                        "dish_id": dish["dish_id"],
                    }))

    def _handle_interact(self, events):
        radius = self.t["interact_radius"]
        candidates = []
        for stove in self.stoves:
            d = math.dist(self.pos, stove["pos"])
            if d <= radius:
                candidates.append((d, 0, id_key(stove["id"]), "stove", stove))
        for table in self.tables:
            d = math.dist(self.pos, table["pos"])
            if d <= radius:
                candidates.append((d, 1, id_key(table["id"]), "table", table))
        if not candidates:
            return
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        _, _, _, kind, obj = candidates[0]
        if kind == "stove":
            self._try_interact_stove(obj, events)
        else:
            self._try_interact_table(obj, events)

    def _pick_reserved_order(self):
        eligible = [
            c for c in self.customers
            if c.get("state") == "waiting"
            and c.get("order_status") == "reserved"
            and c.get("dish_id") in self.menu
        ]
        eligible.sort(key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))
        return eligible[0] if eligible else None

    def _try_interact_stove(self, stove, events) -> bool:
        if stove["state"] == "ready":
            if self.hand is not None or not isinstance(stove.get("dish"), dict):
                return False
            payload = dict(stove["dish"])
            self.hand = payload
            stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
            events.append(("dish_picked", {
                "stove_id": stove["id"],
                "order_id": payload["order_id"],
                "dish_id": payload["dish_id"],
            }))
            return True
        if stove["state"] == "idle":
            customer = self._pick_reserved_order()
            if customer is None:
                return False
            dish_id = customer["dish_id"]
            recipe = customer["reserved"]
            for ing, qty in recipe.items():
                if self.stock.get(ing, 0) < qty:
                    return False
            for ing, qty in recipe.items():
                self.stock[ing] = self.stock.get(ing, 0) - qty
                if self.stock[ing] <= 0:
                    self.stock.pop(ing, None)
            items = [ing for ing in sorted(recipe) for _ in range(recipe[ing])]
            base_price = self.menu[dish_id]["price"]
            customer["reserved"] = {}
            customer["order_status"] = "assigned"
            customer["base_price"] = base_price
            stove.update(
                state="cooking",
                dish={"order_id": customer["id"], "dish_id": dish_id, "base_price": base_price},
                cook_ticks_left=int(round(self.menu[dish_id]["cook_s"] * self.tick_hz)),
                ready_ticks=0,
            )
            events.append(("cook_started", {
                "stove_id": stove["id"],
                "order_id": customer["id"],
                "dish_id": dish_id,
                "items": items,
                "base_price": base_price,
            }))
            return True
        return False

    def _try_interact_table(self, table, events) -> bool:
        if not isinstance(self.hand, dict):
            return False
        customer = next((c for c in self.customers if c["table_id"] == table["id"]), None)
        if customer is None or customer["state"] != "waiting":
            return False
        if self.hand.get("order_id") != customer["id"]:
            return False
        payload = self.hand
        self.hand = None
        dish_id = payload["dish_id"]
        base_price = payload["base_price"]
        patience_left = customer["patience_ticks_left"]
        patience_ratio = (patience_left / self.patience_ticks) if self.patience_ticks > 0 else 0.0
        tip = math.floor(base_price * self.t["tip_rate"]) if patience_ratio >= self.t["tip_min_patience_ratio"] else 0
        customer.update(
            state="eating",
            order_status="served",
            eat_ticks_left=int(round(self.t["eat_s"] * self.tick_hz)),
            base_price=base_price,
            tip=tip,
            reserved={},
        )
        events.append(("served", {
            "order_id": customer["id"],
            "table_id": table["id"],
            "dish_id": dish_id,
            "patience_ticks_left": patience_left,
            "base_price": base_price,
            "tip": tip,
        }))
        return True

    def _tick_customer_patience(self):
        for customer in self.customers:
            if customer["state"] == "waiting":
                customer["patience_ticks_left"] = max(0, customer["patience_ticks_left"] - 1)

    def _remove_expired_customers(self, events):
        for customer in sort_by_id(self.customers, key=lambda c: c["table_id"]):
            if customer["state"] != "waiting" or customer["patience_ticks_left"] > 0:
                continue
            order_id = customer["id"]
            self.customers.remove(customer)
            self._discard_order_dish(order_id)
            reputation = self.reputation + self.t["left_reputation_delta"]
            self.reputation = max(self.t["reputation_min"], min(self.t["reputation_max"], reputation))
            events.append(("customer_left", {"order_id": order_id, "table_id": customer["table_id"],
                                             "reason": "patience", "reputation": self.reputation}))

    def _discard_order_dish(self, order_id):
        if self.hand is not None and self.hand["order_id"] == order_id:
            self.hand = None
        for stove in self.stoves:
            dish = stove["dish"]
            if dish is not None and dish["order_id"] == order_id:
                stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)

    def _spawn_customer_if_due(self, events):
        since_first = self.phase_tick - self.t["first_customer_tick"]
        if not self.random_customers or since_first < 0 or since_first % self.customer_interval_ticks:
            return
        occupied = {customer["table_id"] for customer in self.customers}
        # _merge keeps tables sorted by id.
        table = next((table for table in self.tables if table["id"] not in occupied), None)
        if table is None:
            return

        available = self.stock.copy()
        for customer in self.customers:
            for kind, amount in customer["reserved"].items():
                available[kind] -= amount
        cookable = [dish for dish in sorted(self.menu)
                    if all(available.get(kind, 0) >= amount for kind, amount in self.menu[dish]["recipe"].items())]
        if not cookable:
            events.append(("no_dish", {}))
            return

        dish = self.rng.get("customer_order").choice(cookable)
        order_id = self.ids.new("C")
        self.customers.append({"id": order_id, "table_id": table["id"], "dish_id": dish,
                               "order_tick": self.phase_tick, "state": "waiting", "order_status": "reserved",
                               "patience_ticks_left": self.patience_ticks, "eat_ticks_left": 0,
                               "reserved": dict(self.menu[dish]["recipe"]), "base_price": 0, "tip": 0})
        events.append(("customer_arrived", {"order_id": order_id, "table_id": table["id"], "dish_id": dish}))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
