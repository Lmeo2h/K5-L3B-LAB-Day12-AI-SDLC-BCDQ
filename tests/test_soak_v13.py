"""Tests cho Phase 4 Slice 1 (Contract v1.3, DaySim lặp D1-D5 ở Ngày 6-10, chonoi.soak)."""

import copy
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator, id_key
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.day import DaySim
from chonoi.soak import run_soak
from helpers import ROOT, Workdir, write_json


def _inp(move=(0.0, 0.0), interact=False, shop_done=False):
    edges = set()
    if interact:
        edges.add("interact")
    if shop_done:
        edges.add("shop_done")
    return InputState(move, set(edges), edges)


class ContractV13Tests(unittest.TestCase):
    def test_contract_v13_manifest_has_bench_and_soak_cmds(self):
        c = load_contract(os.path.join(ROOT, "game.contract.json"))
        self.assertEqual(c["contract_version"], "1.3")
        self.assertIsInstance(c.get("bench_cmd"), str)
        self.assertTrue(c["bench_cmd"].strip())
        self.assertIsInstance(c.get("soak_cmd"), str)
        self.assertTrue(c["soak_cmd"].strip())

    def test_invalid_bench_cmd_and_soak_cmd_rejected_with_bad_input(self):
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            base = json.load(f)
        base["contract_version"] = "1.3"
        base.setdefault("bench_cmd", "python3 -m chonoi.bench")
        base.setdefault("soak_cmd", "python3 -m chonoi.soak")

        bad_cases = [
            {k: v for k, v in base.items() if k != "bench_cmd"},
            {**base, "bench_cmd": "   "},
            {**base, "bench_cmd": 123},
            {k: v for k, v in base.items() if k != "soak_cmd"},
            {**base, "soak_cmd": ""},
            {**base, "soak_cmd": None},
        ]
        with Workdir() as w:
            for idx, payload in enumerate(bad_cases):
                path = write_json(w.path(f"bad_{idx}.json"), payload)
                with self.subTest(case=idx):
                    with self.assertRaises(BadInput):
                        load_contract(path)


class DaySimCyclingV13Tests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            self.tuning = json.load(f)["tuning"]

    def test_days_6_to_10_cycle_day_plan_and_keep_monotonic_item_ids(self):
        day_sim = DaySim(copy.deepcopy(self.tuning), {}, Streams(7), IdAllocator(), days=10)
        d1_to_d5 = [day_sim._get_day_plan(d) for d in range(1, 6)]

        seen_plans = {}
        last_item_num = 0
        while not day_sim.done:
            seen_plans.setdefault(day_sim.day, copy.deepcopy(day_sim.day_plan))
            if day_sim.phase == "gather":
                # Cấp một item mới mỗi ngày để kiểm tra item_ids tăng liên tục xuyên 10 ngày
                day_sim.sub._add_hold_item("ca_loc")
                iid = day_sim.sub.hold[-1]["id"]
                num = id_key(iid)[1]
                self.assertGreater(num, last_item_num)
                last_item_num = num
                day_sim.step(_inp(interact=True))
            elif day_sim.phase == "quan":
                day_sim.sub.time_left_ticks = 1
                day_sim.step(_inp())
            elif day_sim.phase == "shop":
                day_sim.step(_inp(shop_done=True))

        self.assertTrue(day_sim.done)
        self.assertEqual(day_sim.days_completed, 10)
        self.assertEqual(sorted(seen_plans), list(range(1, 11)))
        for day in range(6, 11):
            expected = d1_to_d5[(day - 1) % 5]
            self.assertEqual(seen_plans[day], expected)
            self.assertEqual(day_sim._get_day_plan(day), expected)


class SoakCliV13Tests(unittest.TestCase):
    def test_soak_invalid_days_exits_2_without_writing_output(self):
        with Workdir() as w:
            for bad_days in ("0", "-2"):
                out_path = w.path(f"bad_{bad_days}.json")
                proc = subprocess.run(
                    [sys.executable, "-m", "chonoi.soak", "--seed", "7", "--days", bad_days, "--out", out_path],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(proc.returncode, 2, proc.stderr)
                self.assertFalse(os.path.exists(out_path))

    def test_soak_10_days_seed_7_deterministic_and_records_all_days(self):
        with Workdir() as w:
            out1 = w.path("soak1.json")
            out2 = w.path("soak2.json")
            for out_path in (out1, out2):
                proc = subprocess.run(
                    [sys.executable, "-m", "chonoi.soak", "--seed", "7", "--days", "10", "--out", out_path],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)

            with open(out1, encoding="utf-8") as f:
                d1 = json.load(f)
            with open(out2, encoding="utf-8") as f:
                d2 = json.load(f)

        self.assertEqual(d1["days"], 10)
        self.assertEqual(d1["days_completed"], 10)
        self.assertEqual(d1["crashes"], 0)
        self.assertEqual(len(d1["results"]), 10)
        self.assertGreaterEqual(d1["duration_s"], 0.0)
        self.assertEqual([r["day"] for r in d1["results"]], list(range(1, 11)))
        for row in d1["results"]:
            self.assertTrue({"day", "earned", "reputation", "score"} <= set(row.keys()))
        self.assertGreater(d1["results"][-1]["earned"], 0)
        self.assertGreater(d1["results"][-1]["score"], 0)

        self.assertEqual(d1["days_completed"], d2["days_completed"])
        self.assertEqual(d1["crashes"], d2["crashes"])
        self.assertEqual(d1["results"], d2["results"])

    def test_run_soak_counts_unexpected_crash(self):
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            tuning = json.load(f)["tuning"]
        with patch("chonoi.soak.Session.step", side_effect=RuntimeError("boom")):
            res = run_soak(tuning, seed=7, days=2)
        self.assertEqual(res["days"], 2)
        self.assertEqual(res["days_completed"], 0)
        self.assertEqual(res["crashes"], 1)
        self.assertEqual(res["results"], [])


if __name__ == "__main__":
    unittest.main()
