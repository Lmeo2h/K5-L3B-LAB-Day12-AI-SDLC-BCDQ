"""Tests cho Phase 3 Slice 1 (TICKET-03 v1.2): inventory cá thể, contract freshness, GatherSim độ tươi & spoiled."""

import copy
import json
import os
import unittest

from chonoi.contract import load_contract, validate_tuning
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.inventory import (
    FRESH_SCALE,
    KINDS_P2,
    fresh_to_units,
    is_spoiled_units,
    read_inventory,
    read_inventory_v12,
    units_to_fresh,
    validate_items_v12,
    write_inventory,
)
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.scenario import load_scenario
from chonoi.sim.gather import GatherSim

from helpers import Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json


def _inp(move=(0.0, 0.0), interact=False, catch=False, pause=False):
    edges = set()
    if interact:
        edges.add("interact")
    if catch:
        edges.add("catch")
    if pause:
        edges.add("pause")
    return InputState(tuple(move), set(edges), edges)


class InventoryAndContractV12Tests(unittest.TestCase):
    def test_fresh_scale_240_precision_at_threshold_30(self):
        self.assertEqual(FRESH_SCALE, 240)
        self.assertEqual(fresh_to_units(100), 24000)
        self.assertEqual(fresh_to_units(30), 7200)
        self.assertFalse(is_spoiled_units(7200, 30))
        self.assertTrue(is_spoiled_units(7199, 30))
        self.assertTrue(is_spoiled_units(7198, 30))

        # Round-trip qua JSON vẫn giữ nguyên phân biệt ngưỡng 30
        with Workdir() as w:
            p = w.path("inv.json")
            items = [
                {"id": "I10", "kind": "ca_linh", "fresh": units_to_fresh(7200)},
                {"id": "I2", "kind": "ca_loc", "fresh": units_to_fresh(7198)},
            ]
            write_inventory(p, items)
            loaded = read_inventory_v12(p)
            self.assertEqual([it["id"] for it in loaded], ["I2", "I10"])
            self.assertEqual(fresh_to_units(loaded[0]["fresh"]), 7198)
            self.assertEqual(fresh_to_units(loaded[1]["fresh"]), 7200)
            self.assertTrue(is_spoiled_units(fresh_to_units(loaded[0]["fresh"]), 30))
            self.assertFalse(is_spoiled_units(fresh_to_units(loaded[1]["fresh"]), 30))

    def test_inventory_v12_rejects_count_dict_and_bad_items(self):
        with Workdir() as w:
            old_p = write_json(w.path("old.json"), {"items": {"ca_loc": 1}})
            with self.assertRaises(BadInput):
                read_inventory_v12(old_p)
            with self.assertRaises(BadInput):
                read_inventory(old_p, contract_version="1.2")

            empty_p = write_json(w.path("empty.json"), {"items": []})
            self.assertEqual(read_inventory_v12(empty_p), [])

            for bad in (
                [{"id": "", "kind": "ca_linh", "fresh": 100}],
                [{"id": "I1", "kind": "ca_linh", "fresh": 100}, {"id": "I1", "kind": "ca_loc", "fresh": 90}],
                [{"id": "I1", "kind": "ca_la", "fresh": 100}],
                [{"id": "I1", "kind": "ca_linh", "fresh": -0.1}],
                [{"id": "I1", "kind": "ca_linh", "fresh": 100.1}],
                [{"id": "I1", "kind": "ca_linh", "fresh": float("nan")}],
                [{"id": "I1", "kind": "ca_linh", "fresh": True}],
                [{"id": "I1", "kind": "ca_linh"}],
            ):
                with self.assertRaises(BadInput):
                    validate_items_v12(bad, kinds=KINDS_P2)

    def test_contract_freshness_validation(self):
        c = load_contract()
        f = c["tuning"]["freshness"]
        self.assertEqual(
            f,
            {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30},
        )
        t_v12 = copy.deepcopy(c["tuning"])
        validate_tuning(t_v12, contract_version="1.2")

        t_missing = copy.deepcopy(c["tuning"])
        del t_missing["freshness"]
        with self.assertRaises(BadInput):
            validate_tuning(t_missing, contract_version="1.2")

        for bad_f in (
            {"initial": 90, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30},
            {"initial": 100, "gather_decay_per_s": 0, "quan_decay_per_s": 0.25, "spoiled_below": 30},
            {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": -1, "spoiled_below": 30},
            {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 100},
            {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 0},
        ):
            t_bad = copy.deepcopy(c["tuning"])
            t_bad["freshness"] = bad_f
            with self.assertRaises(BadInput):
                validate_tuning(t_bad, contract_version="1.2")


class GatherFreshnessV12Tests(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_scenario_gather_hold_v12_validation(self):
        sc = load_scenario(None, "gather", self.tuning)
        self.assertEqual(sc, {})
        with Workdir() as w:
            ok_p = write_json(
                w.path("ok.json"),
                {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}]}},
            )
            loaded = load_scenario(ok_p, "gather", self.tuning)
            self.assertEqual(loaded["hold"][0]["id"], "I1")

            for bad_hold in (
                ["ca_loc"],
                [{"id": "I1", "kind": "ca_linh", "fresh": 100}, {"id": "I1", "kind": "ca_loc", "fresh": 90}],
                [{"id": "I1", "kind": "ca_linh", "fresh": 101}],
                [{"id": f"I{i}", "kind": "ca_linh", "fresh": 100} for i in range(1, 14)],
            ):
                bp = write_json(w.path("bad.json"), {"gather": {"hold": bad_hold}})
                with self.assertRaises(BadInput):
                    load_scenario(bp, "gather", self.tuning)

    def test_ticket03_spoiled_threshold_tick1_and_once(self):
        sc = {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}], "random_fish": False, "monsters": []}
        sess = Session("gather", self.tuning, sc, seed=1)
        evs1 = sess.step(_inp())
        self.assertEqual(
            evs1,
            [
                {
                    "type": "event",
                    "tick": 1,
                    "phase": "gather",
                    "name": "spoiled",
                    "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"},
                }
            ],
        )
        # Không phát lại ở tick 2
        evs2 = sess.step(_inp())
        self.assertEqual(evs2, [])
        self.assertLess(sess.sim.hold[0]["fresh"], 30)

    def test_multiple_spoiled_emitted_in_id_key_order_and_clamped_at_zero(self):
        sc = {
            "hold": [
                {"id": "I10", "kind": "ca_loc", "fresh": 30},
                {"id": "I2", "kind": "ca_linh", "fresh": 30},
                {"id": "I1", "kind": "bong_sung", "fresh": 0},
            ],
            "random_fish": False,
            "monsters": [],
        }
        sim = GatherSim(self.tuning, sc, Streams(1), IdAllocator())
        evs = sim.step(_inp())
        spoiled_ids = [d["item_id"] for n, d in evs if n == "spoiled"]
        self.assertEqual(spoiled_ids, ["I2", "I10"])
        by_id = {it["id"]: it["fresh"] for it in sim.hold}
        self.assertEqual(by_id["I1"], 0)

    def test_harvest_and_catch_assign_ids_and_decay_only_from_next_tick(self):
        sc = {
            "player": {"pos": [20.0, 0.0]},
            "hold": [{"id": "I5", "kind": "bong_sung", "fresh": 100}],
            "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [20.5, 0.0]}],
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [20.0, 5.0]}],
            "random_fish": False,
            "monsters": [],
        }
        item_ids = IdAllocator()
        sim = GatherSim(self.tuning, sc, Streams(1), IdAllocator(), item_ids=item_ids)
        # Tick 1: hái N1 -> tạo I6 với fresh=100, không hao trong tick 1; I5 hao còn 23998/240
        sim.step(_inp(interact=True))
        by_id = {it["id"]: it for it in sim.hold}
        self.assertIn("I6", by_id)
        self.assertEqual(by_id["I6"]["fresh"], 100)
        self.assertEqual(by_id["I5"]["fresh"], units_to_fresh(23998))

        # Lặn xuống [20, 5] và bắt F1 (ca_linh yield=3 -> I7, I8, I9 với fresh=100)
        sim.pos = [20.0, 5.0]
        sim.step(_inp(catch=True))
        by_id = {it["id"]: it for it in sim.hold}
        self.assertEqual(by_id["I6"]["fresh"], units_to_fresh(23998))
        for iid in ("I7", "I8", "I9"):
            self.assertEqual(by_id[iid]["kind"], "ca_linh")
            self.assertEqual(by_id[iid]["fresh"], 100)

    def test_pause_freezes_freshness_decay(self):
        sc = {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}], "random_fish": False, "monsters": []}
        sess = Session("gather", self.tuning, sc, seed=1)
        evs_pause = sess.step(_inp(pause=True))
        self.assertEqual([e["name"] for e in evs_pause], ["paused"])
        self.assertEqual(sess.sim.hold[0]["fresh"], 30)

        evs_idle = sess.step(_inp())
        self.assertEqual(evs_idle, [])
        self.assertEqual(sess.sim.hold[0]["fresh"], 30)

        evs_resume = sess.step(_inp(pause=True))
        self.assertEqual([e["name"] for e in evs_resume], ["resumed", "spoiled"])

    def test_headless_spoiled_and_inventory_out_roundtrip(self):
        with Workdir() as w:
            sc_path = write_json(
                w.path("sc.json"),
                {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}], "random_fish": False, "monsters": []}},
            )
            out_path = w.path("out.jsonl")
            rc = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc_path, "--out", out_path)
            self.assertEqual(rc, 0)
            evs = events(read_jsonl(out_path))
            self.assertEqual(
                evs,
                [
                    {
                        "type": "event",
                        "tick": 1,
                        "phase": "gather",
                        "name": "spoiled",
                        "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"},
                    }
                ],
            )

            # Kiểm tra --inventory-out khi docked
            sc_dock = write_json(
                w.path("dock.json"),
                {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}], "random_fish": False, "monsters": []}},
            )
            in_dock = write_json(w.path("in_dock.json"), frames({"tick": 0, "interact": True}))
            inv_out = w.path("inv.json")
            out_dock = w.path("dock.jsonl")
            rc2 = run_headless(
                "--mode",
                "gather",
                "--seed",
                "1",
                "--ticks",
                "10",
                "--scenario",
                sc_dock,
                "--inputs",
                in_dock,
                "--out",
                out_dock,
                "--inventory-out",
                inv_out,
            )
            self.assertEqual(rc2, 0)
            end_ev = [e for e in events(read_jsonl(out_dock)) if e["name"] == "gather_end"][0]
            with open(inv_out, encoding="utf-8") as f:
                written = json.load(f)
            self.assertEqual(end_ev["data"]["inventory"], written)
            self.assertEqual(written["items"][0]["id"], "I1")
            self.assertEqual(fresh_to_units(written["items"][0]["fresh"]), 23998)


if __name__ == "__main__":
    unittest.main()
