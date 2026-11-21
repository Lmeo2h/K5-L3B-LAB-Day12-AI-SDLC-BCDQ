"""Unit and headless tests for Phase 1 Slice 4 (quan: stoves, interact priority, serve, payment, tip, reputation, closing, quan_end) per PRD-0."""

import json
import math
import subprocess
import sys
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import LiveInputs
from chonoi.runner import Session

from helpers import Workdir, events, frames, read_jsonl, write_json
from tests.test_quan_freshness_v12 import CONTRACT, contract_items, ingredient_counts


def _cooked_items(counts, stock):
    if isinstance(stock, list):
        return [dict(item, fresh=round(100 - 1 / 240, 6)) for item in stock if item["kind"] in counts]
    return [kind for kind in sorted(counts) for _ in range(counts[kind])]


def _first_tick_price(listed):
    return listed - (CONTRACT["contract_version"] == "1.2")


def _run_headless_py(*args):
    p = subprocess.run([sys.executable, "-m", "chonoi.headless", *args], capture_output=True, text=True)
    return p.returncode, p.stderr


def _step_interact(sess):
    li = LiveInputs()
    li.set(interact=True)
    return sess.step(li.advance())


def _step_idle(sess, n=1):
    li = LiveInputs()
    out = []
    for _ in range(n):
        out.extend(sess.step(li.advance()))
    return out


def _dish_payload(order_id, dish_id, base_price):
    return {"order_id": order_id, "dish_id": dish_id, "base_price": base_price}


class QuanInteractPriorityTests(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_nearest_stove_selected_within_interact_radius(self):
        """When two ready stoves are in interact_radius, the closer one is picked."""
        tuning = json.loads(json.dumps(self.tuning))
        tuning["quan"]["stoves"] = [
            {"id": "B1", "pos": [5.0, 5.0]},
            {"id": "B2", "pos": [6.0, 5.0]},
        ]
        tuning["quan"]["tables"] = [
            {"id": "T1", "pos": [9.0, 2.0]},
            {"id": "T2", "pos": [12.0, 2.0]},
        ]
        p1 = _dish_payload("C1", "goi_bong_sung", 40)
        p2 = _dish_payload("C2", "ca_loc_nuong_trui", 60)
        scenario = {
            "player": {"pos": [5.8, 5.0]},
            "random_customers": False,
            "stoves": [
                {"id": "B1", "state": "ready", "dish": p1},
                {"id": "B2", "state": "ready", "dish": p2},
            ],
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned"},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"},
            ],
        }
        sess = Session("quan", tuning, scenario, seed=1)
        evs = _step_interact(sess)
        self.assertEqual([e["name"] for e in evs], ["dish_picked"])
        self.assertEqual(evs[0]["data"], {"stove_id": "B2", "order_id": "C2", "dish_id": "ca_loc_nuong_trui"})
        self.assertEqual(sess.sim.hand, p2)

    def test_tie_break_by_id_key_b2_before_b10(self):
        """Equidistant stoves tie-break using id_key (B2 before B10, not lexicographical B10 < B2)."""
        tuning = json.loads(json.dumps(self.tuning))
        tuning["quan"]["stoves"] = [
            {"id": "B10", "pos": [4.0, 5.0]},
            {"id": "B2", "pos": [6.0, 5.0]},
        ]
        tuning["quan"]["tables"] = [
            {"id": "T1", "pos": [9.0, 2.0]},
            {"id": "T2", "pos": [12.0, 2.0]},
        ]
        scenario = {
            "player": {"pos": [5.0, 5.0]},
            "random_customers": False,
            "stoves": [
                {"id": "B10", "state": "ready", "dish": _dish_payload("C10", "goi_bong_sung", 40)},
                {"id": "B2", "state": "ready", "dish": _dish_payload("C2", "ca_loc_nuong_trui", 60)},
            ],
            "customers": [
                {"id": "C10", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned"},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"},
            ],
        }
        sess = Session("quan", tuning, scenario, seed=1)
        evs = _step_interact(sess)
        self.assertEqual([e["name"] for e in evs], ["dish_picked"])
        self.assertEqual(evs[0]["data"]["stove_id"], "B2")

    def test_stove_prioritized_before_table_and_no_fallthrough(self):
        """At equal distance stove wins over table; if the selected stove cannot act, the interact turn is skipped (PRD-0)."""
        tuning = json.loads(json.dumps(self.tuning))
        tuning["quan"]["stoves"] = [{"id": "B1", "pos": [4.0, 5.0]}]
        tuning["quan"]["tables"] = [
            {"id": "T1", "pos": [6.0, 5.0]},
            {"id": "T2", "pos": [12.0, 2.0]},
        ]
        hand = _dish_payload("C1", "ca_loc_nuong_trui", 60)
        scenario = {
            "player": {"pos": [5.0, 5.0]},
            "random_customers": False,
            "hand": hand,
            "stoves": [{"id": "B1", "state": "ready", "dish": _dish_payload("C2", "goi_bong_sung", 40)}],
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"},
                {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung", "order_status": "assigned"},
            ],
        }
        sess = Session("quan", tuning, scenario, seed=1)
        evs = _step_interact(sess)
        self.assertEqual(evs, [])
        self.assertEqual(sess.sim.hand, hand)
        self.assertEqual(sess.sim.customers[0]["state"], "waiting")

    def test_out_of_interact_radius_does_nothing(self):
        """Interact beyond interact_radius triggers no stove or table event."""
        radius = self.tuning["quan"]["interact_radius"]
        stove_pos = self.tuning["quan"]["stoves"][0]["pos"]
        scenario = {
            "player": {"pos": [stove_pos[0] + radius + 0.5, stove_pos[1]]},
            "random_customers": False,
            "stoves": [{"id": "B1", "state": "ready", "dish": _dish_payload("C1", "ca_loc_nuong_trui", 60)}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}],
        }
        sess = Session("quan", self.tuning, scenario, seed=1)
        evs = _step_interact(sess)
        self.assertEqual(evs, [])
        self.assertIsNone(sess.sim.hand)

    def test_idle_stove_picks_oldest_reserved_order_by_order_tick_then_table_id(self):
        """Idle stove chooses reserved order with smallest (order_tick, id_key(table_id)) and emits sorted items."""
        tuning = json.loads(json.dumps(self.tuning))
        tuning["quan"]["tables"] = [
            {"id": "T10", "pos": [9.0, 2.0]},
            {"id": "T2", "pos": [11.0, 2.0]},
        ]
        scenario = {
            "player": {"pos": list(tuning["quan"]["stoves"][0]["pos"])},
            "random_customers": False,
            "stock": contract_items({"ca_linh": 3, "bong_dien_dien": 1, "ca_loc": 1}),
            "customers": [
                {"id": "C10", "table_id": "T10", "dish_id": "ca_loc_nuong_trui", "order_tick": 120},
                {"id": "C2", "table_id": "T2", "dish_id": "lau_ca_linh_dien_dien", "order_tick": 120},
            ],
        }
        sess = Session("quan", tuning, scenario, seed=1)
        evs = _step_interact(sess)
        self.assertEqual([e["name"] for e in evs], ["cook_started"])
        self.assertEqual(evs[0]["data"], {
            "stove_id": "B1",
            "order_id": "C2",
            "dish_id": "lau_ca_linh_dien_dien",
            "items": _cooked_items({"bong_dien_dien": 1, "ca_linh": 3}, scenario["stock"]),
            "base_price": _first_tick_price(self.tuning["menu"]["lau_ca_linh_dien_dien"]["price"]),
        })
        self.assertEqual(ingredient_counts(sess.snapshot()["stock"]), {"ca_loc": 1})


class QuanCookingAndServiceTests(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.tick_hz = self.tuning["tick_hz"]

    def test_full_cook_ready_pick_serve_pay_with_tip(self):
        """Full loop: cook_started -> dish_ready -> dish_picked -> served -> paid (with tip & tip_reputation)."""
        q = self.tuning["quan"]
        dish = "ca_loc_nuong_trui"
        dish_cfg = self.tuning["menu"][dish]
        cook_ticks = int(round(dish_cfg["cook_s"] * self.tick_hz))
        eat_ticks = int(round(q["eat_s"] * self.tick_hz))
        patience_max = int(round(q["patience_s"] * self.tick_hz))

        stove_pos = q["stoves"][0]["pos"]
        table_pos = q["tables"][0]["pos"]
        scenario = {
            "player": {"pos": list(stove_pos)},
            "random_customers": False,
            "stock": contract_items({"ca_loc": 1}),
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": dish, "order_tick": 0, "patience_ticks_left": patience_max}
            ],
        }
        sess = Session("quan", self.tuning, scenario, seed=1)

        # 1. Start cooking at idle stove
        expected_price = _first_tick_price(dish_cfg["price"])
        evs = _step_interact(sess)
        self.assertEqual([e["name"] for e in evs], ["cook_started"])
        self.assertEqual(evs[0]["data"], {
            "stove_id": "B1",
            "order_id": "C1",
            "dish_id": dish,
            "items": _cooked_items({"ca_loc": 1}, scenario["stock"]),
            "base_price": expected_price,
        })
        self.assertEqual(sess.sim.stoves[0]["state"], "cooking")
        self.assertEqual(sess.sim.stoves[0]["cook_ticks_left"], cook_ticks)
        self.assertEqual(sess.sim.customers[0]["order_status"], "assigned")
        self.assertEqual(sess.sim.customers[0]["reserved"], contract_items({}))
        self.assertEqual(sess.snapshot()["stock"], contract_items({}))

        # 2. Wait cook_ticks - 1 ticks -> still cooking
        evs = _step_idle(sess, cook_ticks - 1)
        self.assertEqual(evs, [])
        self.assertEqual(sess.sim.stoves[0]["state"], "cooking")

        # 3. Final cooking tick -> dish_ready with ready_ticks == 0
        evs = _step_idle(sess, 1)
        self.assertEqual([e["name"] for e in evs], ["dish_ready"])
        self.assertEqual(evs[0]["data"], {"stove_id": "B1", "order_id": "C1", "dish_id": dish})
        self.assertEqual(sess.sim.stoves[0]["state"], "ready")
        self.assertEqual(sess.sim.stoves[0]["ready_ticks"], 0)

        # 4. Pick dish -> dish_picked, stove idle, hand filled with dish payload
        evs = _step_interact(sess)
        self.assertEqual([e["name"] for e in evs], ["dish_picked"])
        self.assertEqual(evs[0]["data"], {"stove_id": "B1", "order_id": "C1", "dish_id": dish})
        self.assertEqual(sess.sim.hand, _dish_payload("C1", dish, expected_price))
        self.assertEqual(sess.sim.stoves[0]["state"], "idle")
        self.assertIsNone(sess.sim.stoves[0]["dish"])

        # 5. Move to table and serve -> served
        sess.sim.pos = list(table_pos)
        evs = _step_interact(sess)
        expected_tip = math.floor(expected_price * q["tip_rate"])
        expected_patience_left = patience_max - (cook_ticks + 3)
        self.assertEqual([e["name"] for e in evs], ["served"])
        self.assertEqual(evs[0]["data"], {
            "order_id": "C1",
            "table_id": "T1",
            "dish_id": dish,
            "patience_ticks_left": expected_patience_left,
            "base_price": expected_price,
            "tip": expected_tip,
        })
        self.assertIsNone(sess.sim.hand)
        self.assertEqual(sess.sim.customers[0]["state"], "eating")
        self.assertEqual(sess.sim.customers[0]["order_status"], "served")
        self.assertEqual(sess.sim.customers[0]["eat_ticks_left"], eat_ticks)

        # 6. Wait eat_ticks - 1 ticks -> still eating
        evs = _step_idle(sess, eat_ticks - 1)
        self.assertEqual(evs, [])
        self.assertEqual(len(sess.sim.customers), 1)

        # 7. Final eating tick -> paid with tip & tip_reputation, table freed
        evs = _step_idle(sess, 1)
        self.assertEqual([e["name"] for e in evs], ["paid"])
        expected_amount = expected_price + expected_tip
        expected_rep = min(q["reputation_max"], q["reputation_initial"] + q["tip_reputation"])
        self.assertEqual(evs[0]["data"], {
            "order_id": "C1",
            "table_id": "T1",
            "base_price": expected_price,
            "tip": expected_tip,
            "amount": expected_amount,
            "reason": "finished_eating",
        })
        self.assertEqual(sess.sim.money, expected_amount)
        self.assertEqual(sess.sim.earned, expected_amount)
        self.assertEqual(sess.sim.shift_earned, expected_amount)
        self.assertAlmostEqual(sess.sim.reputation, expected_rep)
        self.assertEqual(sess.sim.customers, [])
        self.assertIsNone(sess.snapshot()["tables"][0]["customer_id"])

    def test_no_tip_when_patience_below_threshold(self):
        """Customer served with patience_ratio < tip_min_patience_ratio pays base_price only and no reputation gain."""
        q = self.tuning["quan"]
        dish = "goi_bong_sung"
        dish_cfg = self.tuning["menu"][dish]
        patience_max = int(round(q["patience_s"] * self.tick_hz))
        # After 1 tick decrement in step 1, patience_ticks_left drops below 0.5 * patience_max
        threshold_patience = int(patience_max * q["tip_min_patience_ratio"])
        eat_ticks = int(round(q["eat_s"] * self.tick_hz))

        scenario = {
            "player": {"pos": list(q["tables"][0]["pos"])},
            "random_customers": False,
            "hand": _dish_payload("C1", dish, dish_cfg["price"]),
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": dish, "order_status": "assigned", "patience_ticks_left": threshold_patience}
            ],
        }
        sess = Session("quan", self.tuning, scenario, seed=1)
        evs = _step_interact(sess)
        self.assertEqual([e["name"] for e in evs], ["served"])
        self.assertEqual(evs[0]["data"]["tip"], 0)

        evs = _step_idle(sess, eat_ticks)
        paid = [e for e in evs if e["name"] == "paid"]
        self.assertEqual(len(paid), 1)
        self.assertEqual(paid[0]["data"], {
            "order_id": "C1",
            "table_id": "T1",
            "base_price": dish_cfg["price"],
            "tip": 0,
            "amount": dish_cfg["price"],
            "reason": "finished_eating",
        })
        self.assertEqual(sess.sim.money, dish_cfg["price"])
        self.assertAlmostEqual(sess.sim.reputation, q["reputation_initial"])

    def test_serve_on_patience_zero_tick_is_valid(self):
        """Serving on the exact tick patience hits 0 succeeds without triggering customer_left (PRD-0)."""
        q = self.tuning["quan"]
        dish = "ca_loc_nuong_trui"
        price = self.tuning["menu"][dish]["price"]
        scenario = {
            "player": {"pos": list(q["tables"][0]["pos"])},
            "random_customers": False,
            "hand": _dish_payload("C1", dish, price),
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": dish, "order_status": "assigned", "patience_ticks_left": 1}
            ],
        }
        sess = Session("quan", self.tuning, scenario, seed=1)
        evs = _step_interact(sess)
        self.assertEqual([e["name"] for e in evs], ["served"])
        self.assertEqual(evs[0]["data"]["patience_ticks_left"], 0)
        self.assertEqual(evs[0]["data"]["tip"], 0)
        self.assertEqual(sess.sim.customers[0]["state"], "eating")

    def test_reputation_clamped_to_reputation_max(self):
        """Tip reputation gain is clamped to reputation_max."""
        q = self.tuning["quan"]
        dish = "ca_loc_nuong_trui"
        dish_cfg = self.tuning["menu"][dish]
        eat_ticks = int(round(q["eat_s"] * self.tick_hz))
        patience_max = int(round(q["patience_s"] * self.tick_hz))

        scenario = {
            "player": {"pos": list(q["tables"][0]["pos"])},
            "random_customers": False,
            "hand": _dish_payload("C1", dish, dish_cfg["price"]),
            "reputation": q["reputation_max"] - 0.05,
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": dish, "order_status": "assigned", "patience_ticks_left": patience_max}
            ],
        }
        sess = Session("quan", self.tuning, scenario, seed=1)
        _step_interact(sess)
        _step_idle(sess, eat_ticks)
        self.assertEqual(sess.sim.reputation, q["reputation_max"])

    def test_carry_limit_prevents_picking_second_dish(self):
        """With carry_limit = 1 and hand occupied, interacting with a ready stove does not pick up."""
        tuning = json.loads(json.dumps(self.tuning))
        tuning["quan"]["tables"] = [
            {"id": "T1", "pos": [9.0, 2.0]},
            {"id": "T2", "pos": [12.0, 2.0]},
        ]
        held = _dish_payload("C1", "goi_bong_sung", 40)
        scenario = {
            "player": {"pos": list(tuning["quan"]["stoves"][0]["pos"])},
            "random_customers": False,
            "hand": held,
            "stoves": [{"id": "B1", "state": "ready", "dish": _dish_payload("C2", "ca_loc_nuong_trui", 60)}],
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned"},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"},
            ],
        }
        sess = Session("quan", tuning, scenario, seed=1)
        evs = _step_interact(sess)
        self.assertEqual(evs, [])
        self.assertEqual(sess.sim.hand, held)
        self.assertEqual(sess.sim.stoves[0]["state"], "ready")

    def test_wrong_order_id_on_hand_does_not_serve(self):
        """Table only accepts the dish matching its customer's order_id (PRD-0)."""
        tuning = json.loads(json.dumps(self.tuning))
        tuning["quan"]["tables"] = [
            {"id": "T1", "pos": [9.0, 2.0]},
            {"id": "T2", "pos": [12.0, 2.0]},
        ]
        held = _dish_payload("C2", "ca_loc_nuong_trui", 60)
        scenario = {
            "player": {"pos": [9.0, 2.0]},
            "random_customers": False,
            "hand": held,
            "stock": contract_items({"ca_loc": 1}),
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "reserved"},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"},
            ],
        }
        sess = Session("quan", tuning, scenario, seed=1)
        evs = _step_interact(sess)
        self.assertEqual(evs, [])
        self.assertEqual(sess.sim.hand, held)
        self.assertEqual(sess.sim.customers[0]["state"], "waiting")

    def test_burn_s_null_does_not_burn_ready_dish(self):
        """In Phase 1 burn_s is null, so a ready dish stays ready indefinitely and increments ready_ticks."""
        q = self.tuning["quan"]
        self.assertIsNone(q["burn_s"])
        scenario = {
            "random_customers": False,
            "stoves": [{"id": "B1", "state": "ready", "dish": _dish_payload("C1", "ca_loc_nuong_trui", 60)}],
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}],
        }
        sess = Session("quan", self.tuning, scenario, seed=1)
        evs = _step_idle(sess, 600)
        self.assertEqual(evs, [])
        self.assertEqual(sess.sim.stoves[0]["state"], "ready")
        self.assertEqual(sess.sim.stoves[0]["ready_ticks"], 600)

    def test_closing_pays_eating_and_leaves_waiting_without_rep_penalty(self):
        """On final tick, serving succeeds -> paid(closing); waiting customer leaves(closing) with no rep penalty -> quan_end."""
        tuning = json.loads(json.dumps(self.tuning))
        tuning["quan"]["tables"] = [
            {"id": "T1", "pos": [9.0, 2.0]},
            {"id": "T2", "pos": [12.0, 2.0]},
        ]
        q = tuning["quan"]
        dish1 = "ca_loc_nuong_trui"
        p1 = tuning["menu"][dish1]["price"]
        patience_max = int(round(q["patience_s"] * self.tick_hz))
        scenario = {
            "player": {"pos": [9.0, 2.0]},
            "random_customers": False,
            "hand": _dish_payload("C1", dish1, p1),
            "time_left_ticks": 1,
            "stoves": [{"id": "B1", "state": "cooking", "dish": _dish_payload("C2", "goi_bong_sung", 40), "cook_ticks_left": 100}],
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": dish1, "order_status": "assigned", "patience_ticks_left": patience_max},
                {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung", "order_status": "assigned", "patience_ticks_left": patience_max},
            ],
        }
        sess = Session("quan", tuning, scenario, seed=1)
        evs = _step_interact(sess)
        self.assertEqual([e["name"] for e in evs], ["served", "paid", "customer_left", "quan_end"])
        self.assertEqual(evs[1]["data"]["reason"], "closing")
        self.assertEqual(evs[2]["data"]["reason"], "closing")
        self.assertAlmostEqual(evs[2]["data"]["reputation"], q["reputation_initial"] + q["tip_reputation"])
        self.assertEqual(sess.sim.stoves[0]["state"], "idle")
        self.assertIsNone(sess.sim.stoves[0]["dish"])
        self.assertTrue(sess.done)

    def test_headless_quan_end_score_and_determinism(self):
        """Headless quan emits paid and quan_end with accurate totals, score formula, and byte-identical determinism."""
        q = self.tuning["quan"]
        mult = self.tuning["score"]["reputation_multiplier"]
        dish = "lau_ca_linh_dien_dien"
        dish_cfg = self.tuning["menu"][dish]
        eat_ticks = int(round(q["eat_s"] * self.tick_hz))
        patience_max = int(round(q["patience_s"] * self.tick_hz))
        total_ticks = eat_ticks + 5

        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "player": {"pos": list(q["tables"][0]["pos"])},
                    "random_customers": False,
                    "hand": _dish_payload("C1", dish, dish_cfg["price"]),
                    "reputation": 3.9,
                    "time_left_ticks": total_ticks,
                    "customers": [
                        {
                            "id": "C1",
                            "table_id": "T1",
                            "dish_id": dish,
                            "order_status": "assigned",
                            "patience_ticks_left": patience_max,
                        }
                    ],
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            out1, out2 = w.path("o1.jsonl"), w.path("o2.jsonl")
            for out in (out1, out2):
                code, err = _run_headless_py("--mode", "quan", "--seed", "1", "--ticks", str(total_ticks + 10),
                                             "--scenario", sc, "--inputs", inp, "--out", out)
                self.assertEqual(code, 0, err)

            with open(out1, "rb") as f1, open(out2, "rb") as f2:
                self.assertEqual(f1.read(), f2.read())

            rows = read_jsonl(out1)
            served_ev = events(rows, "served")
            paid_ev = events(rows, "paid")
            end_ev = events(rows, "quan_end")
            self.assertEqual(len(served_ev), 1)
            self.assertEqual(len(paid_ev), 1)
            self.assertEqual(len(end_ev), 1)

            expected_tip = math.floor(dish_cfg["price"] * q["tip_rate"])
            expected_earned = dish_cfg["price"] + expected_tip
            expected_rep = min(q["reputation_max"], 3.9 + q["tip_reputation"])
            expected_score = expected_earned + mult * math.floor(expected_rep)

            qd = end_ev[0]["data"]
            self.assertEqual(qd["reason"], "time")
            self.assertEqual(qd["money"], expected_earned)
            self.assertEqual(qd["earned"], expected_earned)
            self.assertEqual(qd["shift_earned"], expected_earned)
            self.assertAlmostEqual(qd["reputation"], expected_rep, places=3)

            end_row = rows[-1]
            self.assertEqual(end_row["type"], "end")
            self.assertEqual(end_row["reason"], "time")
            self.assertEqual(end_row["earned"], expected_earned)
            self.assertEqual(end_row["score"], expected_score)


if __name__ == "__main__":
    unittest.main()
