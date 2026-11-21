from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from chonoi.inputs import InputState
from chonoi.runner import Session
from tests.helpers import ROOT, Workdir, events, read_jsonl, snapshots, write_json


TUNING = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))["tuning"]
QUAN = TUNING["quan"]
FIRST = QUAN["first_customer_tick"]
NEXT = FIRST + round(QUAN["customer_interval_s"] * TUNING["tick_hz"])
PATIENCE = round(QUAN["patience_s"] * TUNING["tick_hz"])
TABLE = QUAN["tables"][0]["id"]
DISH = "ca_loc_nuong_trui"
OTHER_DISH = "goi_bong_sung"
ORDER = {"id": "C9", "table_id": TABLE, "dish_id": DISH}
PAYLOAD = {"order_id": "C9", "dish_id": DISH, "base_price": TUNING["menu"][DISH]["price"]}


class QuanCustomersTest(unittest.TestCase):
    def run_quan(self, w, scenario, ticks=0, *, inventory=None, name="out", seed=1):
        fixture = write_json(w.path(f"{name}.json"), {"quan": scenario})
        out = Path(w.path(f"{name}.jsonl"))
        cmd = [sys.executable, "-m", "chonoi.headless", "--mode", "quan", "--seed", str(seed),
               "--scenario", fixture, "--out", str(out), "--ticks", str(ticks), "--snapshot-every", "1"]
        if inventory is not None:
            cmd.extend(["--inventory", write_json(w.path("inventory.json"), {"items": inventory})])
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True)
        return result, out

    def read_run(self, w, scenario, ticks=0, **kwargs):
        result, out = self.run_quan(w, scenario, ticks, **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
        return read_jsonl(out), out.read_bytes()

    def test_arrival_schedule_and_rng_are_deterministic(self):
        scenario = {"stock": {"ca_loc": 1, "bong_sung": 2},
                    "customers": [dict(ORDER, patience_ticks_left=FIRST + 1)],
                    "time_left_ticks": NEXT + 1}
        with Workdir() as w:
            rows, raw = self.read_run(w, scenario, NEXT)
            _, repeat = self.read_run(w, scenario, NEXT, name="repeat")
            other_seed, _ = self.read_run(w, scenario, NEXT, name="other-seed", seed=4)
        self.assertEqual(raw, repeat)
        arrivals = events(rows, "customer_arrived")
        self.assertEqual([e["tick"] for e in arrivals], [NEXT])
        self.assertEqual(events(rows, "no_dish"), [])
        customer = snapshots(rows)[-1]["customers"][0]
        self.assertEqual(customer["id"], "C10")
        self.assertEqual(customer["table_id"], TABLE)
        self.assertEqual(customer["order_tick"], NEXT)
        self.assertEqual(customer["order_status"], "reserved")
        self.assertEqual(customer["patience_ticks_left"], PATIENCE)
        self.assertEqual(customer["reserved"], TUNING["menu"][customer["dish_id"]]["recipe"])
        self.assertEqual(arrivals[0]["data"], {"order_id": "C10", "table_id": TABLE,
                                               "dish_id": customer["dish_id"]})
        self.assertNotEqual(events(other_seed, "customer_arrived")[0]["data"]["dish_id"], customer["dish_id"])

    def test_free_table_without_recipe_emits_no_dish(self):
        with Workdir() as w:
            rows, _ = self.read_run(w, {"stock": {"bong_sung": 1}}, FIRST)
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "no_dish")], [(FIRST, {})])
        self.assertEqual(snapshots(rows)[-1]["customers"], [])

    def test_expiry_releases_reservation_before_new_arrival(self):
        scenario = {"customers": [dict(ORDER, patience_ticks_left=FIRST)]}
        with Workdir() as w:
            rows, _ = self.read_run(w, scenario, FIRST, inventory={"ca_loc": 1})
        self.assertEqual(snapshots(rows)[0]["customers"][0]["reserved"], {"ca_loc": 1})
        self.assertEqual(snapshots(rows)[-1]["stock"], {"ca_loc": 1})
        self.assertEqual([e["name"] for e in events(rows)], ["customer_left", "customer_arrived"])
        left = events(rows, "customer_left")[0]
        self.assertEqual(left["tick"], FIRST)
        self.assertEqual(left["data"], {"order_id": "C9", "table_id": TABLE, "reason": "patience",
                                       "reputation": QUAN["reputation_initial"] + QUAN["left_reputation_delta"]})
        self.assertEqual(events(rows, "customer_arrived")[0]["data"]["dish_id"], DISH)

    def test_expiry_clamps_reputation_clears_assigned_dish_and_respects_random_flag(self):
        scenario = {"customers": [dict(ORDER, order_status="assigned", patience_ticks_left=1)],
                    "random_customers": False, "hand": PAYLOAD, "reputation": QUAN["reputation_min"]}
        with Workdir() as w:
            rows, _ = self.read_run(w, scenario, FIRST)
        self.assertEqual([e["name"] for e in events(rows)], ["customer_left"])
        final = snapshots(rows)[-1]
        self.assertEqual(final["reputation"], QUAN["reputation_min"])
        self.assertIsNone(final["hand"])
        self.assertIsNone(final["tables"][0]["customer_id"])

    def test_expiry_discards_stove_dish_without_refunding_stock(self):
        for state, cooking, ready in (("cooking", 2, 0), ("ready", 0, 2)):
            with self.subTest(state=state), Workdir() as w:
                scenario = {"customers": [dict(ORDER, order_status="assigned", patience_ticks_left=1)],
                            "stoves": [{"id": "B1", "state": state, "dish": PAYLOAD,
                                        "cook_ticks_left": cooking, "ready_ticks": ready}]}
                rows, _ = self.read_run(w, scenario, 1)
                final = snapshots(rows)[-1]
                self.assertEqual(final["stock"], {})
                self.assertEqual(final["customers"], [])
                self.assertEqual(final["stoves"][0], dict(snapshots(rows)[0]["stoves"][0], state="idle",
                                                         dish=None, cook_ticks_left=0, ready_ticks=0))

    def test_no_new_arrival_on_closing_tick(self):
        with Workdir() as w:
            rows, _ = self.read_run(w, {"stock": {"ca_loc": 1}, "time_left_ticks": FIRST}, FIRST)
        self.assertEqual([e["name"] for e in events(rows)], ["quan_end"])

    def test_rejects_conflicts_before_touching_output(self):
        fixtures = [
            ({"customers": [ORDER]}, {}),
            ({"customers": [dict(ORDER, reserved={"bong_sung": 2})]}, {"bong_sung": 2}),
            ({"customers": [dict(ORDER, order_status="assigned")]}, {}),
            ({"customers": [dict(ORDER, order_status="assigned", dish_id="unknown")]}, {}),
            ({"customers": [dict(ORDER, state="eating", order_status="served", eat_ticks_left=1)]}, {}),
            ({"customers": [dict(ORDER, state="eating", order_status="served", eat_ticks_left=0,
                                 base_price=1, tip=0)]}, {}),
            ({"customers": [dict(ORDER, order_status="assigned")], "hand": PAYLOAD,
              "stoves": [{"id": "B1", "state": "ready", "dish": PAYLOAD}]}, {}),
            ({"customers": [dict(ORDER, order_status="assigned")],
              "hand": dict(PAYLOAD, dish_id=OTHER_DISH)}, {}),
            ({"stoves": [{"id": "B1", "state": "cooking", "dish": PAYLOAD}]}, {}),
            ({"tables": [{"id": "T999"}]}, {}),
            ({"random_customers": 1}, {}),
        ]
        with Workdir() as w:
            for index, (scenario, inventory) in enumerate(fixtures):
                with self.subTest(scenario=scenario):
                    result, out = self.run_quan(w, scenario, inventory=inventory, name=f"conflict-{index}")
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertFalse(out.exists())

    def test_spawn_filters_stock_reserved_at_other_table(self):
        # Phase 1 ships one table. Exercise the same logic with spare seating in memory.
        tuning = deepcopy(TUNING)
        tuning["quan"]["tables"] += [{"id": "T10", "pos": [0, 0]}, {"id": "T2", "pos": [0, 0]}]
        session = Session("quan", tuning, {"stock": {"ca_loc": 1, "bong_sung": 2}, "customers": [ORDER]}, 1)
        for _ in range(FIRST):
            arrivals = session.step(InputState((0, 0), {}, set()))
        self.assertEqual(arrivals[0]["data"], {"order_id": "C10", "table_id": "T2", "dish_id": OTHER_DISH})
