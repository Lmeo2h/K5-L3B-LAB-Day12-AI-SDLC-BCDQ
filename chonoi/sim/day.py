"""Vòng lặp nhiều ngày (`--mode day --days 1..5`): gather -> quan -> shop (TICKET-02, Contract v1.1)."""

import copy
import inspect

from ..ids import IdAllocator
from .gather import GatherSim
from .quan import QuanSim
from .shop import ShopSim


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1, item_ids=None):
        self.tuning = tuning
        self.scenario = scenario or {}
        day_cfg = self.scenario.get("day", {})
        self.rng = streams
        self.ids = ids
        self.item_ids = item_ids if item_ids is not None else IdAllocator()
        for item in self.scenario.get("gather", {}).get("hold", []):
            if isinstance(item, dict) and "id" in item:
                self.item_ids.reserve(item["id"])
        for item in self.scenario.get("quan", {}).get("stock", []):
            if isinstance(item, dict) and "id" in item:
                self.item_ids.reserve(item["id"])
        self.days = days
        self.day = 1
        self.days_completed = 0
        self.phase = "gather"
        self.money = day_cfg.get("money", 0)
        self.earned = day_cfg.get("earned", 0)
        self.reputation = day_cfg.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict(day_cfg.get("upgrades", {}))
        self.active_upgrades = dict(self.upgrades)
        self._day_plan_overrides = self._parse_day_plan_overrides(day_cfg.get("day_plan"))
        self.day_plan = self._get_day_plan(self.day)
        self.done = False
        self.reason = None
        self.sub = self._start_gather()
        self._pending_events = self._make_day_start_events()

    @property
    def time_left_ticks(self) -> int:
        return self.sub.time_left_ticks

    @property
    def phase_tick(self) -> int:
        return getattr(self.sub, "phase_tick", 0)

    def _parse_day_plan_overrides(self, raw) -> dict:
        if not raw:
            return {}
        if isinstance(raw, list):
            return {int(item["day"]): item for item in raw if isinstance(item, dict) and "day" in item}
        if isinstance(raw, dict):
            return {int(k): v for k, v in raw.items()}
        return {}

    def _compute_ingredients(self, dishes: dict) -> dict:
        menu = self.tuning.get("menu", {})
        ing = {}
        for dish_id, count in dishes.items():
            recipe = menu.get(dish_id, {}).get("recipe", {})
            for kind, qty in recipe.items():
                ing[kind] = ing.get(kind, 0) + qty * count
        return {k: ing[k] for k in sorted(ing)}

    def _get_day_plan(self, day: int) -> dict:
        if day in self._day_plan_overrides:
            ov = copy.deepcopy(self._day_plan_overrides[day])
            dishes = ov.get("dishes", {})
            ingredients = ov.get("ingredients") or self._compute_ingredients(dishes)
            return {"dishes": dishes, "ingredients": ingredients}

        plans = self.tuning.get("day_plan", [])
        entry = None
        if isinstance(plans, list):
            for item in plans:
                if item.get("day") == day:
                    entry = item
                    break
            if entry is None and plans:
                entry = plans[min(day - 1, len(plans) - 1)]
        elif isinstance(plans, dict):
            entry = plans.get(str(day)) or plans.get(day)
        if entry:
            dishes = copy.deepcopy(entry.get("dishes", {}))
            ingredients = copy.deepcopy(entry.get("ingredients")) or self._compute_ingredients(dishes)
            return {"dishes": dishes, "ingredients": ingredients}
        dishes = {d: 1 for d in self.tuning.get("menu", {})}
        return {"dishes": dishes, "ingredients": self._compute_ingredients(dishes)}

    def _make_day_start_events(self) -> list:
        return [
            ("day_start", {}),
            ("day_plan", copy.deepcopy(self.day_plan)),
            ("phase_start", {}),
        ]

    def _upgraded_gather_tuning(self) -> dict:
        t = copy.deepcopy(self.tuning)
        shop_t = t.get("shop", {})
        src = shop_t.get("upgrades", shop_t)
        oxy_lvl = int(self.active_upgrades.get("oxygen", 0))
        if oxy_lvl > 0:
            tiers = src.get("oxygen")
            if isinstance(tiers, list) and oxy_lvl <= len(tiers):
                tier = tiers[oxy_lvl - 1]
                if "oxygen_max_s" in tier:
                    t["gather"]["oxygen_max_s"] = tier["oxygen_max_s"]
        hp_lvl = int(self.active_upgrades.get("hp", 0))
        if hp_lvl > 0:
            tiers = src.get("hp")
            if isinstance(tiers, list) and hp_lvl <= len(tiers):
                tier = tiers[hp_lvl - 1]
                if "hp_max" in tier:
                    t["gather"]["hp_max"] = tier["hp_max"]
        return t

    def _reassign_hold_ids(self, hold: list) -> list:
        """Cấp ID mới tuần tự cho mẫu `hold` ở Ngày 2+ mà vẫn giữ kind/fresh ban đầu."""
        out = []
        for item in hold:
            if isinstance(item, dict):
                cloned = {"id": self.item_ids.new("I"), "kind": item["kind"], "fresh": item["fresh"]}
                out.append(cloned)
            else:
                out.append(item)
        return out

    def _start_gather(self):
        self.phase = "gather"
        t = self._upgraded_gather_tuning()
        sc = copy.deepcopy(self.scenario.get("gather", {})) if self.day == 1 else {}
        if self.day > 1 and sc.get("hold"):
            sc["hold"] = self._reassign_hold_ids(sc["hold"])
        kwargs = {}
        params = inspect.signature(GatherSim.__init__).parameters
        if "day" in params:
            kwargs["day"] = self.day
        if "item_ids" in params:
            kwargs["item_ids"] = self.item_ids
        sim = GatherSim(t, sc, self.rng, IdAllocator(), **kwargs)
        sim.money = self.money
        sim.earned = self.earned
        sim.reputation = self.reputation
        return sim

    def _start_quan(self, inventory):
        self.phase = "quan"
        sc = copy.deepcopy(self.scenario.get("quan", {})) if self.day == 1 else {}
        sc.pop("stock", None)
        sc.pop("reputation", None)
        kwargs = {"inventory": inventory}
        params = inspect.signature(QuanSim.__init__).parameters
        if "allowed_dishes" in params:
            dishes = self.day_plan.get("dishes", {})
            kwargs["allowed_dishes"] = list(dishes.keys()) if isinstance(dishes, dict) else list(dishes)
        if "item_ids" in params:
            kwargs["item_ids"] = self.item_ids
        sim = QuanSim(self.tuning, sc, self.rng, IdAllocator(), **kwargs)
        sim.money = self.money
        sim.earned = self.earned
        sim.reputation = self.reputation
        return sim

    def _start_shop(self, leftover_stock: dict):
        self.phase = "shop"
        return ShopSim(
            self.tuning,
            self.scenario.get("shop", {}),
            self.rng,
            IdAllocator(),
            money=self.money,
            earned=self.earned,
            reputation=self.reputation,
            upgrades=self.upgrades,
            stock=leftover_stock,
            day=self.day,
        )

    def snapshot(self) -> dict:
        snap = self.sub.snapshot()
        snap["day"] = self.day
        snap["day_plan"] = copy.deepcopy(self.day_plan)
        snap["upgrades"] = dict(self.upgrades)
        snap["active_upgrades"] = dict(self.active_upgrades)
        return snap

    def step(self, inp):
        """Trả về list (day, phase, name, data) để runner giữ đúng pha cũ/mới trên từng event."""
        events = []
        if self._pending_events:
            for name, data in self._pending_events:
                events.append((self.day, self.phase, name, data))
            self._pending_events = []

        old_phase = self.phase
        old_day = self.day
        sub_events = self.sub.step(inp)
        for name, data in sub_events:
            events.append((old_day, old_phase, name, data))
        self.money = self.sub.money
        self.earned = self.sub.earned
        self.reputation = self.sub.reputation

        if not self.sub.done:
            return events

        if old_phase == "gather":
            if self.sub.reason == "fainted":
                inv = [] if (self.tuning.get("contract_version") == "1.2" or isinstance(self.sub.inventory_items(), list)) else {}
            else:
                inv = self.sub.inventory_items()
            self.sub = self._start_quan(inv)
            events.append((self.day, "quan", "phase_start", {}))
        elif old_phase == "quan":
            if isinstance(self.sub.stock, list):
                leftover = [
                    {"id": it["id"], "kind": it["kind"], "fresh": it["fresh"]}
                    for it in self.sub.stock
                ]
            else:
                leftover = {k: v for k, v in self.sub.stock.items() if v > 0}
            self.sub = self._start_shop(leftover)
            events.append((self.day, "shop", "phase_start", {}))
        elif old_phase == "shop":
            self.upgrades = dict(self.sub.upgrades)
            self.days_completed += 1
            if self.days_completed >= self.days:
                self.done = True
                self.reason = "days_complete"
            else:
                self.day += 1
                self.active_upgrades = dict(self.upgrades)
                self.day_plan = self._get_day_plan(self.day)
                self.sub = self._start_gather()
                for name, data in self._make_day_start_events():
                    events.append((self.day, "gather", name, data))
        return events
