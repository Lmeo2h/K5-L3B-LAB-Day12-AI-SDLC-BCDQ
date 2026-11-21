from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi import inventory
from chonoi.rng import Streams
from chonoi.scenario import load_scenario
from chonoi.sim.quan import QuanSim
from tests.helpers import ROOT, Workdir, write_json


CONTRACT = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))
IDLE = InputState((0, 0), {}, set())
INTERACT = InputState((0, 0), {}, {"interact"})
FISH = "ca_loc_nuong_trui"
SALAD = "goi_bong_sung"


def item(i, kind="ca_loc", fresh=100):
    return {"id": f"I{i}", "kind": kind, "fresh": fresh}


def order(i, table, *, dish=FISH, **fields):
    return {"id": f"C{i}", "table_id": f"T{table}", "dish_id": dish, **fields}


def contract_items(counts):
    """Keep old regression scenarios while changing the wire format at the v1.2 cutover."""
    if CONTRACT["contract_version"] != "1.2":
        return counts
    kinds = [kind for kind in sorted(counts) for _ in range(counts[kind])]
    return [item(index, kind) for index, kind in enumerate(kinds, 1)]


def ingredient_counts(stock):
    if isinstance(stock, list):
        counts = {}
        for item in stock:
            kind = item["kind"]
            counts[kind] = counts.get(kind, 0) + 1
        return counts
    return stock


def reservation_counts(reserved, stock):
    return ingredient_counts([item for item in stock if item["id"] in reserved]) if isinstance(reserved, list) else reserved


class QuanFreshnessTest(unittest.TestCase):
    def setUp(self):
        if not hasattr(inventory, "validate_items_v12"):
            self.skipTest("Chờ bộ đọc kho cá thể của Slice 1")
        self.tuning = deepcopy(CONTRACT["tuning"])
        self.tuning.setdefault("freshness", {"initial": 100, "gather_decay_per_s": .5,
                                             "quan_decay_per_s": .25, "spoiled_below": 30})

    def sim(self, stock, customers=(), **scenario):
        return QuanSim(self.tuning, {"stock": stock, "customers": list(customers), **scenario},
                       Streams(1), IdAllocator())

    def test_spoils_by_id_then_reassigns_by_order_tick_and_table(self):
        sim = self.sim([item(10, fresh=30), item(2, fresh=30), item(3, fresh=70)],
                       [order(1, 2, reserved=["I2"]), order(2, 1, reserved=["I10"])])
        self.assertEqual(sim.step(IDLE), [
            ("spoiled", {"item_id": "I2", "kind": "ca_loc", "location": "stock"}),
            ("spoiled", {"item_id": "I10", "kind": "ca_loc", "location": "stock"}),
        ])
        self.assertEqual(sim.customers[0]["order_status"], "unfulfillable")
        self.assertEqual(sim.customers[0]["reserved"], [])
        self.assertEqual(sim.customers[1]["reserved"], ["I3"])
        self.assertEqual(sim.step(IDLE), [])
        stock = sim.snapshot()["stock"]
        self.assertEqual([i["id"] for i in stock], ["I2", "I3", "I10"])
        self.assertAlmostEqual(stock[1]["fresh"], 70 - 2 / 240, places=5)
        self.assertEqual(set(stock[0]), {"id", "kind", "fresh"})

    def test_spawn_filters_spoiled_and_selects_freshest_then_id(self):
        sim = self.sim([item(1, fresh=20), item(10, fresh=90), item(2, fresh=90), item(3, fresh=71)])
        first = self.tuning["quan"]["first_customer_tick"]
        for _ in range(first):
            output = sim.step(IDLE)
        self.assertEqual(output[0][0], "customer_arrived")
        self.assertEqual(sim.customers[0]["reserved"], ["I2"])

    def test_cooks_exact_reserved_items_in_kind_id_order_and_locks_price(self):
        dish = "canh_chua_ca_loc"
        sim = self.sim([item(2, fresh=70), item(3, "bong_dien_dien", 90), item(4, fresh=99)],
                       [order(1, 1, dish=dish, reserved=["I3", "I2"])], player={"pos": [2, 8]},
                       random_customers=False)
        name, payload = sim.step(INTERACT)[0]
        self.assertEqual(name, "cook_started")
        self.assertEqual([i["id"] for i in payload["items"]], ["I3", "I2"])
        self.assertEqual([i["id"] for i in sim.snapshot()["stock"]], ["I4"])
        self.assertEqual(payload["base_price"], 71)
        for _ in range(sim.stoves[0]["cook_ticks_left"]):
            sim.step(IDLE)
        sim.step(INTERACT)
        sim.pos = list(sim.tables[0]["pos"])
        name, payload = sim.step(INTERACT)[0]
        self.assertEqual(name, "served")
        self.assertEqual((payload["base_price"], payload["tip"]), (71, 14))

    def test_inferred_reservation_respects_explicit_ids_and_recipe(self):
        sim = self.sim([item(1), item(2, fresh=90), item(3, fresh=70)],
                       [order(1, 1), order(2, 2, reserved=["I1"])])
        self.assertEqual([c["reserved"] for c in sim.customers], [["I2"], ["I1"]])
        for customers in ([order(1, 1, reserved=["I4"])],
                          [order(1, 1, reserved=["I2", "I2"])],
                          [order(1, 1, reserved=["I2"]), order(2, 2, reserved=["I2"])],
                          [order(1, 1, dish=SALAD, reserved=["I2"])]):
            with self.subTest(customers=customers), self.assertRaises(BadInput):
                self.sim([item(2, fresh=100)], customers)
        with self.assertRaises(BadInput):
            self.sim([item(2, fresh=29.99999)], [order(1, 1, reserved=["I2"])])

    def test_fixture_price_matches_locked_dish_and_stays_within_fresh_range(self):
        with Workdir() as work:
            for price, customer_price in ((17, 17), (61, 61), (41, 40)):
                block = {"customers": [order(1, 1, order_status="assigned", base_price=customer_price)],
                         "hand": {"order_id": "C1", "dish_id": FISH, "base_price": price}}
                path = write_json(work.path("fixture.json"), {"quan": block})
                with self.subTest(price=price), self.assertRaises(BadInput):
                    load_scenario(path, "quan", self.tuning)
            block = {"customers": [order(1, 1, order_status="assigned", base_price=18)],
                     "hand": {"order_id": "C1", "dish_id": FISH, "base_price": 18}}
            path = write_json(work.path("valid.json"), {"quan": block})
            self.assertEqual(load_scenario(path, "quan", self.tuning), block)

    def test_cli_rejects_legacy_count_inventory_and_bad_fixture(self):
        if CONTRACT["contract_version"] != "1.2":
            self.skipTest("Contract v1.2 chưa bật")
        with Workdir() as work:
            invalid = [
                ("--inventory", {"items": {"ca_loc": 1}}),
                ("--scenario", {"quan": {"stock": [item(1), item(1)]}}),
                ("--scenario", {"quan": {"stock": [item(1, fresh=29)],
                                         "customers": [order(1, 1, reserved=["I1"])]}}),
                ("--scenario", {"quan": {"customers": [order(1, 1, order_status="assigned")],
                                         "hand": {"order_id": "C1", "dish_id": FISH, "base_price": 61}}}),
            ]
            for i, (flag, data) in enumerate(invalid):
                with self.subTest(data=data):
                    path = write_json(work.path(f"in{i}.json"), data)
                    out = Path(work.path(f"out{i}.jsonl"))
                    cmd = [sys.executable, "-m", "chonoi.headless", "--mode", "quan", "--seed", "1",
                           "--ticks", "0", "--out", str(out), flag, path]
                    run = subprocess.run(cmd, cwd=ROOT, capture_output=True)
                    self.assertEqual(run.returncode, 2, run.stderr)
                    self.assertFalse(out.exists())
