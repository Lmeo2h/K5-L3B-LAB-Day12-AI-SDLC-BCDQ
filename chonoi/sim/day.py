"""Vòng lặp nhiều ngày (`--mode day --days 1..5`): gather -> quan -> shop (TICKET-02, Contract v1.1)."""

import copy
import inspect

from ..ids import IdAllocator
from .gather import GatherSim
from .quan import QuanSim
from .shop import ShopSim


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning = tuning
        self.scenario = scenario or {}
        self.rng = streams
        self.ids = ids
        self.days = days
        self.day = 1
        self.days_completed = 0
        self.phase = "gather"
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.upgrades = {"oxygen": 0, "hp": 0}
        self.active_upgrades = {"oxygen": 0, "hp": 0}
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

    def _get_day_plan(self, day: int) -> dict:
        plans = self.tuning.get("day_plan", {})
        if isinstance(plans, list):
            idx = min(max(0, day - 1), len(plans) - 1) if plans else 0
            return copy.deepcopy(plans[idx]) if plans else {"day": day, "dishes": {}}
        key = str(day)
        if key in plans:
            return copy.deepcopy(plans[key])
        if day in plans:
            return copy.deepcopy(plans[day])
        if plans:
            first_key = sorted(plans.keys())[0]
            return copy.deepcopy(plans[first_key])
        return {"day": day, "dishes": {d: 1 for d in self.tuning.get("menu", {})}}

    def _make_day_start_events(self) -> list:
        return [
            ("day_start", {"day": self.day}),
            ("day_plan", copy.deepcopy(self.day_plan)),
            ("phase_start", {"phase": "gather", "day": self.day}),
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
                elif "oxygen_max_ticks" in tier:
                    t["gather"]["oxygen_max_s"] = tier["oxygen_max_ticks"] / float(t.get("tick_hz", 60))
                elif "value" in tier:
                    t["gather"]["oxygen_max_s"] = tier["value"]
        hp_lvl = int(self.active_upgrades.get("hp", 0))
        if hp_lvl > 0:
            tiers = src.get("hp")
            if isinstance(tiers, list) and hp_lvl <= len(tiers):
                tier = tiers[hp_lvl - 1]
                if "hp_max" in tier:
                    t["gather"]["hp_max"] = tier["hp_max"]
                elif "value" in tier:
                    t["gather"]["hp_max"] = tier["value"]
        return t

    def _start_gather(self):
        self.phase = "gather"
        t = self._upgraded_gather_tuning()
        sc = copy.deepcopy(self.scenario.get("gather", {}))
        sc["hold"] = []  # Xóa giỏ thừa khi sang ngày mới
        kwargs = {}
        if "day" in inspect.signature(GatherSim.__init__).parameters:
            kwargs["day"] = self.day
        sim = GatherSim(t, sc, self.rng, IdAllocator(), **kwargs)
        sim.money = self.money
        sim.earned = self.earned
        sim.reputation = self.reputation
        return sim

    def _start_quan(self, inventory: dict):
        self.phase = "quan"
        sc = copy.deepcopy(self.scenario.get("quan", {}))
        sc.pop("stock", None)
        sc.pop("reputation", None)
        kwargs = {"inventory": inventory}
        if "allowed_dishes" in inspect.signature(QuanSim.__init__).parameters:
            dishes = self.day_plan.get("dishes", {})
            kwargs["allowed_dishes"] = list(dishes.keys()) if isinstance(dishes, dict) else list(dishes)
        sim = QuanSim(self.tuning, sc, self.rng, IdAllocator(), **kwargs)
        sim.money = self.money
        sim.earned = self.earned
        sim.reputation = self.reputation
        return sim

    def _start_shop(self):
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
            day=self.day,
        )

    def snapshot(self) -> dict:
        snap = self.sub.snapshot()
        snap["day"] = self.day
        snap["days"] = self.days
        snap["days_completed"] = self.days_completed
        snap["day_plan"] = copy.deepcopy(self.day_plan)
        snap["upgrades"] = dict(self.upgrades)
        snap["active_upgrades"] = dict(self.active_upgrades)
        return snap

    def step(self, inp):
        events = []
        if self._pending_events:
            events.extend(self._pending_events)
            self._pending_events = []

        sub_events = self.sub.step(inp)
        events.extend(sub_events)
        self.money = self.sub.money
        self.earned = self.sub.earned
        self.reputation = self.sub.reputation

        if not self.sub.done:
            return events

        if self.phase == "gather":
            inv = {} if self.sub.reason == "fainted" else self.sub.inventory_items()
            self.sub = self._start_quan(inv)
            events.append(("phase_start", {"phase": "quan", "day": self.day}))
        elif self.phase == "quan":
            self.sub = self._start_shop()
            events.append(("phase_start", {"phase": "shop", "day": self.day}))
        elif self.phase == "shop":
            self.upgrades = dict(self.sub.upgrades)
            events.append(("day_end", {
                "day": self.day,
                "money": self.money,
                "earned": self.earned,
                "reputation": self.reputation,
                "upgrades": dict(self.upgrades),
            }))
            self.days_completed += 1
            if self.days_completed >= self.days:
                self.done = True
                self.reason = "days_complete"
                events.append(("days_completed", {
                    "days": self.days,
                    "days_completed": self.days_completed,
                    "reason": "days_complete",
                    "money": self.money,
                    "earned": self.earned,
                    "reputation": self.reputation,
                }))
            else:
                self.day += 1
                self.active_upgrades = dict(self.upgrades)
                self.day_plan = self._get_day_plan(self.day)
                self.sub = self._start_gather()
                self._pending_events = self._make_day_start_events()
        return events
