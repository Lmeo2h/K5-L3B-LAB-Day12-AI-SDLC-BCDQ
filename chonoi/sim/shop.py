"""Cửa hàng cuối ngày (ShopSim) — nâng cấp oxygen / hp L1->L2 bằng money (TICKET-02, Contract v1.1)."""


class ShopSim:
    mode = "shop"
    phase = "shop"

    def __init__(self, tuning, scenario=None, streams=None, ids=None, money=0, earned=0,
                 reputation=None, upgrades=None, day=1):
        t = tuning.get("shop", {})
        self.t = t
        self.tick_hz = float(tuning.get("tick_hz", 60))
        self.max_ticks = int(t.get("max_ticks", 600))
        self.time_left_ticks = self.max_ticks
        self.phase_tick = 0
        self.day = day
        self.money = money
        self.earned = earned
        self.reputation = tuning["quan"]["reputation_initial"] if reputation is None else reputation
        self.upgrades = {"oxygen": 0, "hp": 0}
        if upgrades:
            self.upgrades.update(upgrades)
        self.done = False
        self.reason = None

    def _tiers_for(self, kind: str) -> list:
        src = self.t.get("upgrades", self.t)
        tiers = src.get(kind)
        if isinstance(tiers, list):
            return tiers
        if isinstance(tiers, dict):
            return [tiers[k] for k in sorted(tiers, key=lambda x: int(x) if str(x).isdigit() else str(x))]
        return []

    def snapshot(self) -> dict:
        return {
            "stock": {},
            "upgrades": dict(self.upgrades),
            "shop": {
                "time_left_ticks": self.time_left_ticks,
                "max_ticks": self.max_ticks,
                "upgrades": dict(self.upgrades),
            },
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        buy = getattr(inp, "buy", None)
        if buy is not None:
            self._handle_buy(buy, events)

        if inp.pressed("shop_done"):
            self.done = True
            self.reason = "done"
            events.append(("shop_end", {
                "reason": "done",
                "money": self.money,
                "earned": self.earned,
                "reputation": self.reputation,
                "upgrades": dict(self.upgrades),
            }))
            return events

        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("shop_end", {
                "reason": "time",
                "money": self.money,
                "earned": self.earned,
                "reputation": self.reputation,
                "upgrades": dict(self.upgrades),
            }))
        return events

    def _handle_buy(self, buy, events):
        if not isinstance(buy, str) or buy not in ("oxygen", "hp"):
            events.append(("buy_failed", {"action": buy, "reason": "unknown_upgrade"}))
            return
        tiers = self._tiers_for(buy)
        cur_lvl = int(self.upgrades.get(buy, 0))
        if cur_lvl >= len(tiers):
            events.append(("buy_failed", {"action": buy, "reason": "max_level"}))
            return
        tier = tiers[cur_lvl]
        cost = int(tier.get("cost", tier.get("price", 0)))
        if self.money < cost:
            events.append(("buy_failed", {"action": buy, "reason": "insufficient_money"}))
            return
        self.money -= cost
        new_lvl = cur_lvl + 1
        self.upgrades[buy] = new_lvl
        events.append(("bought", {
            "kind": buy,
            "level": new_lvl,
            "cost": cost,
            "money": self.money,
            "upgrades": dict(self.upgrades),
        }))
