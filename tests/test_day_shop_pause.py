"""Unit and headless tests for Phase 2 Slice 4: DaySim (--mode day --days 1..5), ShopSim, pause across 3 modes, and Envelope v1.1."""

import copy
import json
import subprocess
import sys
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session

from helpers import Workdir, events, read_jsonl


def _v11_tuning():
    t = copy.deepcopy(load_contract()["tuning"])
    t.setdefault("shop", {
        "max_ticks": 600,
        "upgrades": {
            "oxygen": [
                {"level": 1, "cost": 200, "oxygen_max_s": 45},
                {"level": 2, "cost": 400, "oxygen_max_s": 60},
            ],
            "hp": [
                {"level": 1, "cost": 250, "hp_max": 4},
                {"level": 2, "cost": 500, "hp_max": 5},
            ],
        },
    })
    t.setdefault("day_plan", {
        "1": {"day": 1, "dishes": {"ca_loc_nuong_trui": 2, "goi_bong_sung": 2}},
        "2": {"day": 2, "dishes": {"ca_loc_nuong_trui": 2, "lau_ca_linh_dien_dien": 1}},
        "3": {"day": 3, "dishes": {"goi_bong_sung": 3, "lau_ca_linh_dien_dien": 2}},
        "4": {"day": 4, "dishes": {"ca_loc_nuong_trui": 3, "lau_ca_linh_dien_dien": 2}},
        "5": {"day": 5, "dishes": {"ca_loc_nuong_trui": 4, "goi_bong_sung": 3, "lau_ca_linh_dien_dien": 2}},
    })
    return t


def _inp(move=(0.0, 0.0), edges=None, buy=None):
    st = InputState(move, {}, set(edges or ()))
    st.buy = buy
    return st


def _run_headless_py(*args):
    p = subprocess.run([sys.executable, "-m", "chonoi.headless", *args], capture_output=True, text=True)
    return p.returncode, p.stderr


class ShopSimTests(unittest.TestCase):
    def setUp(self):
        self.tuning = _v11_tuning()

    def test_shop_buy_oxygen_and_hp_upgrades_preserves_earned_and_score(self):
        from chonoi.sim.shop import ShopSim

        shop = ShopSim(self.tuning, money=1400, earned=1400, reputation=3.0)
        mult = self.tuning["score"]["reputation_multiplier"]
        base_score = shop.earned + mult * 3

        # Buy oxygen L1 (200) -> money 1200, earned still 1400
        evs = shop.step(_inp(buy="oxygen"))
        self.assertEqual([e[0] for e in evs], ["bought"])
        self.assertEqual(evs[0][1]["kind"], "oxygen")
        self.assertEqual(evs[0][1]["level"], 1)
        self.assertEqual(shop.money, 1200)
        self.assertEqual(shop.earned, 1400)
        self.assertEqual(shop.earned + mult * 3, base_score)

        # Buy oxygen L2 (400) -> money 800
        evs = shop.step(_inp(buy="oxygen"))
        self.assertEqual(evs[0][1]["level"], 2)
        self.assertEqual(shop.money, 800)

        # Max level oxygen -> buy_failed
        evs = shop.step(_inp(buy="oxygen"))
        self.assertEqual([e[0] for e in evs], ["buy_failed"])
        self.assertEqual(evs[0][1]["action"], "oxygen")
        self.assertEqual(evs[0][1]["reason"], "max_level")

        # Buy hp L1 (250) -> money 550
        evs = shop.step(_inp(buy="hp"))
        self.assertEqual(evs[0][1]["level"], 1)
        self.assertEqual(shop.money, 550)

        # Buy hp L2 (500) -> money 50
        evs = shop.step(_inp(buy="hp"))
        self.assertEqual(evs[0][1]["level"], 2)
        self.assertEqual(shop.money, 50)

        # Unknown upgrade -> buy_failed
        evs = shop.step(_inp(buy="speed"))
        self.assertEqual(evs[0], ("buy_failed", {"action": "speed", "reason": "unknown_upgrade"}))

        # Insufficient money -> buy_failed
        shop2 = ShopSim(self.tuning, money=100, earned=100)
        evs = shop2.step(_inp(buy="oxygen"))
        self.assertEqual(evs[0], ("buy_failed", {"action": "oxygen", "reason": "insufficient_money"}))
        self.assertEqual(shop2.money, 100)

    def test_shop_done_and_timeout_600_ticks(self):
        from chonoi.sim.shop import ShopSim

        s1 = ShopSim(self.tuning, money=300, earned=300)
        evs = s1.step(_inp(edges={"shop_done"}))
        self.assertTrue(s1.done)
        self.assertEqual(s1.reason, "done")
        self.assertEqual(evs[-1][0], "shop_end")
        self.assertEqual(evs[-1][1]["reason"], "done")

        s2 = ShopSim(self.tuning, money=300, earned=300)
        max_t = self.tuning["shop"]["max_ticks"]
        self.assertEqual(max_t, 600)
        last = []
        for _ in range(max_t):
            last = s2.step(_inp())
        self.assertTrue(s2.done)
        self.assertEqual(s2.reason, "time")
        self.assertEqual(last[-1][0], "shop_end")
        self.assertEqual(last[-1][1]["reason"], "time")


class DaySimAndEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.tuning = _v11_tuning()

    def test_day_loop_two_days_transitions_upgrades_and_clears_hold_stock(self):
        t = copy.deepcopy(self.tuning)
        t["gather"]["duration_s"] = 1  # 60 ticks for fast unit test
        t["quan"]["duration_s"] = 1    # 60 ticks
        t["shop"]["max_ticks"] = 5
        scenario = {"gather": {"hold": ["ca_loc", "bong_sung"]}}

        sess = Session("day", t, scenario, seed=1, days=2)
        snap0 = sess.snapshot()
        self.assertEqual(snap0["mode"], "day")
        self.assertEqual(snap0["phase"], "gather")
        self.assertEqual(snap0["day"], 1)
        self.assertIn("day_plan", snap0)
        self.assertEqual(snap0["upgrades"], {"oxygen": 0, "hp": 0})
        self.assertEqual(snap0["active_upgrades"], {"oxygen": 0, "hp": 0})

        # Tick 1: day_start, day_plan, phase_start(gather)
        evs1 = sess.step(_inp(edges={"interact"}))  # at dock -> ends gather immediately!
        names1 = [e["name"] for e in evs1]
        self.assertEqual(names1[:3], ["day_start", "day_plan", "phase_start"])
        self.assertEqual(evs1[2]["data"], {"phase": "gather", "day": 1})
        self.assertIn("gather_end", names1)
        self.assertEqual(names1[-1], "phase_start")
        self.assertEqual(evs1[-1]["data"], {"phase": "quan", "day": 1})
        self.assertTrue(all(e["day"] == 1 for e in evs1))

        # Run quan to completion (60 ticks)
        quan_events = []
        for _ in range(60):
            quan_events.extend(sess.step(_inp()))
        q_names = [e["name"] for e in quan_events]
        self.assertIn("quan_end", q_names)
        self.assertEqual(q_names[-1], "phase_start")
        self.assertEqual(quan_events[-1]["data"], {"phase": "shop", "day": 1})

        # Give money so player can buy oxygen L1 in shop
        sess.sim.sub.money = 250
        snap_shop = sess.snapshot()
        self.assertEqual(snap_shop["phase"], "shop")
        self.assertEqual(snap_shop["stock"], {})

        # Buy oxygen L1 and finish shop -> day_end -> advances to Day 2
        evs_buy = sess.step(_inp(buy="oxygen", edges={"shop_done"}))
        b_names = [e["name"] for e in evs_buy]
        self.assertIn("bought", b_names)
        self.assertIn("shop_end", b_names)
        self.assertIn("day_end", b_names)
        self.assertFalse(sess.done)
        self.assertEqual(sess.sim.day, 2)
        self.assertEqual(sess.sim.active_upgrades["oxygen"], 1)
        # Hold cleared on new day, oxygen upgraded to 45s (2700 ticks)
        snap_d2 = sess.snapshot()
        self.assertEqual(snap_d2["day"], 2)
        self.assertEqual(snap_d2["phase"], "gather")
        self.assertEqual(snap_d2["hold"], [])
        self.assertEqual(snap_d2["player"]["oxygen_max_ticks"], 45 * 60)
        self.assertEqual(snap_d2["player"]["oxygen_ticks"], 45 * 60)

        # Finish Day 2 -> days_completed
        sess.step(_inp(edges={"interact"}))  # dock -> quan
        for _ in range(60):
            sess.step(_inp())  # quan -> shop
        final_evs = sess.step(_inp(edges={"shop_done"}))
        self.assertTrue(sess.done)
        self.assertEqual(sess.sim.reason, "days_complete")
        self.assertIn("days_completed", [e["name"] for e in final_evs])
        self.assertEqual(sess.end_row()["reason"], "days_complete")

    def test_gather_faint_in_day_mode_transitions_to_empty_quan(self):
        t = copy.deepcopy(self.tuning)
        scenario = {"gather": {"player": {"pos": [50, 10], "oxygen_ticks": 1, "hp": 1}, "hold": ["ca_loc"]}}
        sess = Session("day", t, scenario, seed=1, days=1)
        # Step 1 tick: underwater oxygen 1 -> 0 -> faint if choke-on-zero, or drive hp to 0 directly
        sess.sim.sub.hp = 1
        sess.sim.sub.oxygen_ticks = 0
        sess.sim.sub.zero_oxy_ticks = t["gather"]["choke_interval_ticks"] - 1
        evs = sess.step(_inp())
        names = [e["name"] for e in evs]
        self.assertIn("gather_end", names)
        self.assertEqual(sess.sim.phase, "quan")
        self.assertEqual(sess.snapshot()["stock"], {})


class PauseAcrossAllModesTests(unittest.TestCase):
    def setUp(self):
        self.tuning = _v11_tuning()

    def test_pause_freezes_timers_and_ignores_actions_across_all_modes(self):
        for mode in ("gather", "quan", "day"):
            with self.subTest(mode=mode):
                sess = Session(mode, self.tuning, {}, seed=1, days=1)
                t0 = sess.snapshot()["time_left_ticks"]

                # Pause + simultaneous interact edge: pause wins, interact ignored
                evs = sess.step(_inp(edges={"pause", "interact"}))
                self.assertEqual([e["name"] for e in evs], ["paused"])
                snap_p = sess.snapshot()
                self.assertEqual(snap_p["state"], "paused")
                self.assertEqual(snap_p["tick"], 1)
                self.assertEqual(snap_p["sim_tick"], 0)
                self.assertEqual(snap_p["time_left_ticks"], t0)

                # While paused: outer tick advances, sim_tick and timers stay frozen
                evs2 = sess.step(_inp(move=(1.0, 0.0), edges={"interact", "catch", "shop_done"}, buy="oxygen"))
                self.assertEqual(evs2, [])
                snap_p2 = sess.snapshot()
                self.assertEqual(snap_p2["state"], "paused")
                self.assertEqual(snap_p2["tick"], 2)
                self.assertEqual(snap_p2["sim_tick"], 0)
                self.assertEqual(snap_p2["time_left_ticks"], t0)

                # Resume: emits resumed AND executes gameplay step in the same tick!
                evs3 = sess.step(_inp(edges={"pause"}))
                self.assertEqual(evs3[0]["name"], "resumed")
                snap_r = sess.snapshot()
                self.assertEqual(snap_r["state"], "playing")
                self.assertEqual(snap_r["tick"], 3)
                self.assertEqual(snap_r["sim_tick"], 1)
                self.assertEqual(snap_r["time_left_ticks"], t0 - 1)


class HeadlessDayCliTests(unittest.TestCase):
    def test_cli_validation_errors_exit_2_before_writing_output(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            inv = w.path("inv.json")
            with open(inv, "w", encoding="utf-8") as f:
                json.dump({"items": {}}, f)
            bad_cases = [
                ("--mode", "day", "--days", "0", "--seed", "1", "--ticks", "10", "--out", out),
                ("--mode", "day", "--days", "6", "--seed", "1", "--ticks", "10", "--out", out),
                ("--mode", "gather", "--days", "1", "--seed", "1", "--ticks", "10", "--out", out),
                ("--mode", "quan", "--days", "2", "--seed", "1", "--ticks", "10", "--out", out),
                ("--mode", "day", "--seed", "1", "--ticks", "10", "--inventory", inv, "--out", out),
                ("--mode", "day", "--seed", "1", "--ticks", "10", "--inventory-out", inv, "--out", out),
            ]
            for args in bad_cases:
                code, _ = _run_headless_py(*args)
                self.assertEqual(code, 2, args)
                self.assertFalse(w.path("o.jsonl") in [] or False)
                import os
                self.assertFalse(os.path.exists(out))

    def test_headless_day_deterministic_22200_ticks(self):
        with Workdir() as w:
            o1, o2 = w.path("d1.jsonl"), w.path("d2.jsonl")
            for o in (o1, o2):
                code, err = _run_headless_py("--mode", "day", "--days", "1", "--seed", "1", "--ticks", "22200", "--out", o)
                self.assertEqual(code, 0, err)
            with open(o1, "rb") as f1, open(o2, "rb") as f2:
                self.assertEqual(f1.read(), f2.read())
            rows = read_jsonl(o1)
            self.assertEqual(rows[-1]["type"], "end")
            self.assertEqual(rows[-1]["mode"], "day")
            self.assertEqual(rows[-1]["reason"], "days_complete")
            self.assertEqual(len(events(rows, "day_start")), 1)
            self.assertEqual(len(events(rows, "days_completed")), 1)


if __name__ == "__main__":
    unittest.main()
