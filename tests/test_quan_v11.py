from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.scenario import load_scenario
from chonoi.sim.quan import QuanSim
from tests.helpers import ROOT, Workdir, events, read_jsonl, write_json
from tests.test_quan_freshness_v12 import contract_items, reservation_counts


CONTRACT = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))
STOVES = {"B1": [2, 8], "B2": [5, 8]}
TABLES = {"T1": [9, 2], "T2": [13, 2], "T3": [9, 6], "T4": [13, 6]}
NEW_DISHES = {
    "canh_chua_ca_loc": {"recipe": {"ca_loc": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 90},
    "ca_keo_nuong": {"recipe": {"ca_keo": 2}, "cook_s": 6, "price": 70},
    "lau_mam": {"recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1},
                "cook_s": 12, "price": 200},
}
CA_LOC = "ca_loc_nuong_trui"
GOI = "goi_bong_sung"
MENU_IDS = {CA_LOC, GOI, "lau_ca_linh_dien_dien", *NEW_DISHES}
NO_INPUT = InputState((0, 0), {}, set())
INTERACT = InputState((0, 0), {}, {"interact"})


def quan_tuning():
    tuning = deepcopy(CONTRACT["tuning"])
    if CONTRACT["contract_version"] == "1.0":
        # Test against the ticket while Slice 1 owns the preset migration.
        tuning["quan"]["stoves"] = [{"id": key, "pos": pos} for key, pos in STOVES.items()]
        tuning["quan"]["tables"] = [{"id": key, "pos": pos} for key, pos in TABLES.items()]
        tuning["menu"].update(NEW_DISHES)
        tuning["day_plan"] = [{"day": day, "dishes": {CA_LOC: 1}, "ingredients": {"ca_loc": 1}}
                              for day in range(1, 6)]
    return tuning


class QuanV11Test(unittest.TestCase):
    def setUp(self):
        self.tuning = quan_tuning()

    def sim(self, scenario, **kwargs):
        if "stock" in scenario:
            scenario = dict(scenario, stock=contract_items(scenario["stock"]))
        if "inventory" in kwargs:
            kwargs["inventory"] = contract_items(kwargs["inventory"])
        return QuanSim(self.tuning, scenario, Streams(1), IdAllocator(), **kwargs)

    def step_for(self, sim, count):
        return [event for _ in range(count) for event in sim.step(NO_INPUT)]

    def read_scenario(self, mode, data):
        with Workdir() as work:
            path = write_json(work.path("fixture.json"), data)
            return load_scenario(path, mode, self.tuning)

    def test_full_menu_and_four_tables_use_preset_schedule(self):
        stock = Counter()
        for dish in self.tuning["menu"].values():
            stock.update({kind: qty * len(TABLES) for kind, qty in dish["recipe"].items()})
        sim = self.sim({"stock": stock})
        self.assertEqual(set(sim.menu), MENU_IDS)
        self.assertEqual({s["id"]: s["pos"] for s in sim.stoves}, STOVES)
        self.assertEqual({t["id"]: t["pos"] for t in sim.tables}, TABLES)
        first = self.tuning["quan"]["first_customer_tick"]
        interval = round(self.tuning["quan"]["customer_interval_s"] * self.tuning["tick_hz"])
        self.assertEqual((first, interval), (120, 900))
        self.assertEqual(self.step_for(sim, first - 1), [])
        self.assertEqual(sim.step(NO_INPUT)[0][1]["table_id"], "T1")
        for table_id in ("T2", "T3", "T4"):
            self.assertEqual(self.step_for(sim, interval - 1), [])
            self.assertEqual(sim.step(NO_INPUT)[0][1]["table_id"], table_id)
        self.assertEqual(self.step_for(sim, interval - 1), [])
        departure, arrival = sim.step(NO_INPUT)
        self.assertEqual((departure[0], departure[1]["table_id"]), ("customer_left", "T1"))
        self.assertEqual((arrival[0], arrival[1]["table_id"]), ("customer_arrived", "T1"))

    def test_two_stoves_cook_independently(self):
        dishes = ("ca_keo_nuong", "lau_mam")
        stock = Counter()
        customers = []
        for index, dish in enumerate(dishes, 1):
            stock.update(self.tuning["menu"][dish]["recipe"])
            customers.append({"id": f"C{index}", "table_id": f"T{index}", "dish_id": dish})
        sim = self.sim({"stock": stock, "customers": customers, "random_customers": False})
        for index, stove in enumerate(sim.stoves):
            sim.pos = list(stove["pos"])
            name, payload = sim.step(INTERACT)[0]
            self.assertEqual((name, payload["stove_id"], payload["dish_id"]),
                             ("cook_started", stove["id"], dishes[index]))
            listed = self.tuning["menu"][dishes[index]]["price"]
            self.assertEqual(payload["base_price"], listed - (CONTRACT["contract_version"] in ("1.2", "1.3")))
        self.assertEqual([s["state"] for s in sim.stoves], ["cooking", "cooking"])
        self.assertEqual(sim.snapshot()["stock"], contract_items({}))
        for stove_id, dish in zip(("B1", "B2"), dishes):
            stove = next(s for s in sim.stoves if s["id"] == stove_id)
            self.assertEqual(self.step_for(sim, stove["cook_ticks_left"]), [
                ("dish_ready", {"stove_id": stove_id, "order_id": stove["dish"]["order_id"], "dish_id": dish})
            ])

    def test_day_menu_filters_before_stock_and_accepts_repeat_orders(self):
        first = self.tuning["quan"]["first_customer_tick"]
        interval = round(self.tuning["quan"]["customer_interval_s"] * self.tuning["tick_hz"])
        allowed = {CA_LOC: 1}
        blocked = self.sim({}, inventory={"ca_keo": 2}, allowed_dishes=allowed)
        self.assertEqual(self.step_for(blocked, first), [("no_dish", {})])
        paid_customer = {"id": "C9", "table_id": "T1", "dish_id": CA_LOC, "state": "eating",
                         "order_status": "served", "eat_ticks_left": 1,
                         "base_price": self.tuning["menu"][CA_LOC]["price"], "tip": 0}
        sim = self.sim({"customers": [paid_customer]}, inventory={"ca_loc": 2, "ca_keo": 6},
                       allowed_dishes=allowed)
        self.assertEqual(sim.step(NO_INPUT)[0][0], "paid")
        orders = self.step_for(sim, first + interval - 1)
        self.assertEqual([(name, payload["dish_id"]) for name, payload in orders],
                         [("customer_arrived", CA_LOC), ("customer_arrived", CA_LOC)])
        self.assertEqual(self.step_for(sim, interval), [("no_dish", {})])

    def test_standalone_can_order_new_dish_and_accept_new_ingredients(self):
        scenario = {"stock": {"ca_keo": 2}, "customers": []}
        loaded = dict(scenario, stock=contract_items(scenario["stock"]))
        self.assertEqual(self.read_scenario("quan", {"quan": loaded}), loaded)
        sim = self.sim(scenario)
        name, data = self.step_for(sim, self.tuning["quan"]["first_customer_tick"])[0]
        self.assertEqual((name, data["dish_id"]), ("customer_arrived", "ca_keo_nuong"))

    def test_evening_checks_stock_and_rejects_fixture_dishes_outside_plan(self):
        fixture = {"customers": [{"id": "C1", "table_id": "T1", "dish_id": CA_LOC}]}
        with self.assertRaises(BadInput):
            self.sim(fixture, inventory={}, allowed_dishes={CA_LOC: 1})
        with self.assertRaises(BadInput):
            self.sim(fixture, inventory={"ca_loc": 1}, allowed_dishes={GOI: 1})
        sim = self.sim(fixture, inventory={"ca_loc": 1}, allowed_dishes={CA_LOC: 1})
        self.assertEqual(reservation_counts(sim.customers[0]["reserved"], sim.snapshot()["stock"]), {"ca_loc": 1})

    def test_day_plan_validation_and_forbidden_quan_fields(self):
        override = {"day": {"day_plan": {"1": {"dishes": {"ca_keo_nuong": 2}}}}}
        block = self.read_scenario("day", override)
        self.assertEqual(block["day"]["day_plan"]["1"]["ingredients"], {"ca_keo": 4})
        for plan in ({"dishes": {"unknown": 1}}, {"dishes": {CA_LOC: True}},
                     {"dishes": {CA_LOC: 1}, "ingredients": {"keo_neo": 0}},
                     {"dishes": {CA_LOC: 1}, "ingredients": {"ca_loc": 2}},
                     {"dishes": {CA_LOC: 1}, "ingredients": {"unknown": 1}}):
            with self.subTest(plan=plan), self.assertRaises(BadInput):
                self.read_scenario("day", {"day": {"day_plan": {"1": plan}}})
        for field, value in (("stock", {}), ("reputation", 3)):
            with self.subTest(field=field), self.assertRaises(BadInput):
                self.read_scenario("day", {"quan": {field: value}})
        for day in ({"money": 5}, {"money": 5, "earned": 4}, {"reputation": "3"}, {"upgrades": True}):
            with self.subTest(day=day), self.assertRaises(BadInput):
                self.read_scenario("day", {"day": day})
        with self.assertRaises(BadInput):
            self.read_scenario("day", {"day": {"day_plan": {"6": override["day"]["day_plan"]["1"]}}})
        self.tuning["day_plan"] = self.tuning["day_plan"][:-1]
        with self.assertRaises(BadInput):
            self.read_scenario("day", {})

    def test_quan_cli_uses_v11_preset(self):
        if CONTRACT["contract_version"] == "1.0":
            self.skipTest("Contract v1.1 chưa vào main")
        cli = [sys.executable, "-m", "chonoi.headless"]
        with Workdir() as work:
            out = work.path("out.jsonl")
            stock = write_json(work.path("stock.json"), {"items": contract_items({"ca_keo": 2})})
            args = ["--seed", "1", "--ticks", "120", "--out", out]
            run = subprocess.run([*cli, "--mode", "quan", "--inventory", stock, *args],
                                 cwd=ROOT, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            rows = read_jsonl(out)
            self.assertEqual(len(rows[0]["stoves"]), 2)
            self.assertEqual(len(rows[0]["tables"]), 4)
            self.assertEqual(events(rows, "customer_arrived")[0]["data"]["dish_id"], "ca_keo_nuong")

    def test_day_cli_rejects_conflicts_without_output(self):
        cli = [sys.executable, "-m", "chonoi.headless"]
        probe = subprocess.run([*cli, "--help"], cwd=ROOT, capture_output=True)
        if b"--days" not in probe.stdout:
            self.skipTest("Slice 4 chưa hỗ trợ --mode day")
        with Workdir() as work:
            args = [*cli, "--mode", "day", "--days", "1", "--seed", "1", "--ticks", "120"]
            smoke = work.path("day.jsonl")
            run = subprocess.run([*args, "--out", smoke], cwd=ROOT, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(read_jsonl(smoke)[-1]["mode"], "day")
            for index, data in enumerate((
                {"quan": {"stock": {}}}, {"quan": {"reputation": 3}},
                {"day": {"day_plan": {"1": {"dishes": {"unknown": 1}}}}},
                {"gather": {"time_left_ticks": 1},
                 "quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": CA_LOC}]}},
            )):
                with self.subTest(data=data):
                    fixture = write_json(work.path("invalid.json"), data)
                    invalid_out = Path(work.path(f"invalid-{index}.jsonl"))
                    cmd = [*args, "--scenario", fixture, "--out", str(invalid_out)]
                    run = subprocess.run(cmd, cwd=ROOT, capture_output=True)
                    self.assertEqual(run.returncode, 2, run.stderr)
                    self.assertFalse(invalid_out.exists())
