"""Unit & headless tests cho Slice 2 (`gather`: hái nút mặt nước, bắt cá dưới nước, cập bến & xuất kho)."""

import json
import os
import subprocess
import sys
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session
from helpers import ROOT, Workdir, events, frames, read_jsonl, snapshots, write_json


def _load_tuning():
    return load_contract(os.path.join(ROOT, "game.contract.json"))["tuning"]


def _inp(interact=False, catch=False, move=(0.0, 0.0)):
    edges = set()
    if interact:
        edges.add("interact")
    if catch:
        edges.add("catch")
    return InputState(move, set(edges), edges)


class GatherHarvestUnitTests(unittest.TestCase):
    def setUp(self):
        self.tuning = _load_tuning()
        self.g = self.tuning["gather"]

    def test_dock_priority_over_nearby_ready_node(self):
        """Đứng trong cả dock_radius và interact_radius của nút ready: interact ưu tiên cập bến."""
        dock = self.g["dock_pos"]
        sc = {
            "player": {"pos": list(dock)},
            "hold": ["ca_loc"],
            "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": list(dock)}],
            "random_fish": False,
        }
        sess = Session("gather", self.tuning, sc, seed=1)
        evs = sess.step(_inp(interact=True))
        names = [e["name"] for e in evs]
        self.assertEqual(names, ["gather_end"])
        self.assertEqual(evs[0]["data"]["reason"], "docked")
        self.assertEqual(evs[0]["data"]["inventory"], {"items": {"ca_loc": 1}})
        self.assertTrue(sess.done)
        self.assertEqual(sess.sim.nodes[0]["regrow_ticks"], 0)

    def test_surface_node_harvest_and_regrow(self):
        """Hái nút ở mặt nước đúng mép bán kính, đặt regrow_ticks, và node_regrown cho phép hái lại ngay."""
        r = self.g["interact_radius"]
        regrow_ticks = int(round(self.g["regrow_s"] * self.tuning["tick_hz"]))
        sc = {
            "player": {"pos": [20.0, self.g["surface_depth"]]},
            "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [20.0 + r, 0.0]}],
            "random_fish": False,
        }
        # Khoảng cách từ [20, 0.5] tới [20 + r, 0] > r nên đặt pos tại [20 + r, 0] với d=0 để đúng mép r.
        sc["player"]["pos"] = [20.0, 0.0]
        sess = Session("gather", self.tuning, sc, seed=1)

        evs = sess.step(_inp(interact=True))
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["name"], "gather")
        self.assertEqual(
            evs[0]["data"],
            {"node_id": "N1", "kind": "bong_dien_dien", "amount": self.g["node_yield"]},
        )
        self.assertEqual(sess.sim.hold, ["bong_dien_dien"] * self.g["node_yield"])
        self.assertEqual(sess.sim.nodes[0]["regrow_ticks"], regrow_ticks)

        # Đang mọc lại -> không hái được
        evs_cd = sess.step(_inp(interact=True))
        self.assertEqual(evs_cd, [])

        # Chạy tới tick ngay trước khi mọc lại xong, rồi tick cuối cùng vừa mọc lại vừa hái ngay
        for _ in range(regrow_ticks - 2):
            self.assertEqual(sess.step(_inp()), [])
        evs_regrow_and_gather = sess.step(_inp(interact=True))
        self.assertEqual([e["name"] for e in evs_regrow_and_gather], ["node_regrown", "gather"])
        self.assertEqual(evs_regrow_and_gather[0]["data"], {"node_id": "N1"})

    def test_node_tie_break_by_id_key_and_underwater_ignored(self):
        """Hai nút cách đều -> chọn id nhỏ theo id_key (N2 trước N10); dưới nước không hái được."""
        sc = {
            "player": {"pos": [20.0, 0.0]},
            "nodes": [
                {"id": "N10", "kind": "bong_sung", "pos": [21.0, 0.0]},
                {"id": "N2", "kind": "bong_dien_dien", "pos": [19.0, 0.0]},
            ],
            "random_fish": False,
        }
        sess = Session("gather", self.tuning, sc, seed=1)
        evs = sess.step(_inp(interact=True))
        self.assertEqual(evs[0]["name"], "gather")
        self.assertEqual(evs[0]["data"]["node_id"], "N2")

        # Dưới nước -> interact không hái nút
        sc_under = {
            "player": {"pos": [20.0, self.g["surface_depth"] + 0.5]},
            "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20.0, 0.0]}],
            "random_fish": False,
        }
        sess_under = Session("gather", self.tuning, sc_under, seed=1)
        self.assertEqual(sess_under.step(_inp(interact=True)), [])

    def test_gather_hold_full(self):
        """Giỏ đầy không đủ node_yield -> phát hold_full và nút giữ nguyên ready."""
        cap = self.g["hold_capacity"]
        sc = {
            "player": {"pos": [20.0, 0.0]},
            "hold": ["ca_loc"] * cap,
            "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20.5, 0.0]}],
            "random_fish": False,
        }
        sess = Session("gather", self.tuning, sc, seed=1)
        evs = sess.step(_inp(interact=True))
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["name"], "hold_full")
        self.assertEqual(
            evs[0]["data"],
            {"action": "gather", "node_id": "N1", "required": self.g["node_yield"], "free": 0},
        )
        self.assertEqual(sess.sim.nodes[0]["regrow_ticks"], 0)
        self.assertEqual(len(sess.sim.hold), cap)

    def test_catch_fish_underwater_cooldown_and_tie_break(self):
        """Bắt cá dưới nước: chọn gần nhất (hòa theo id_key F2 < F10), xóa đàn, đặt cooldown."""
        cd_ticks = int(round(self.g["catch_cooldown_s"] * self.tuning["tick_hz"]))
        sc = {
            "player": {"pos": [30.0, 10.0]},
            "fish": [
                {"id": "F10", "kind": "ca_loc", "pos": [31.0, 10.0]},
                {"id": "F2", "kind": "ca_linh", "pos": [29.0, 10.0]},
            ],
        }
        sess = Session("gather", self.tuning, sc, seed=1)
        evs = sess.step(_inp(catch=True))
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["name"], "fish_caught")
        self.assertEqual(
            evs[0]["data"],
            {"fish_id": "F2", "kind": "ca_linh", "yield": self.g["fish_yield"]["ca_linh"]},
        )
        self.assertEqual(sess.sim.hold, ["ca_linh"] * self.g["fish_yield"]["ca_linh"])
        self.assertEqual([f["id"] for f in sess.sim.fish], ["F10"])
        self.assertEqual(sess.sim.catch_cd_ticks, cd_ticks)

        # Trong cooldown -> không bắt được F10
        self.assertEqual(sess.step(_inp(catch=True)), [])
        for _ in range(cd_ticks - 1):
            sess.step(_inp())
        self.assertEqual(sess.sim.catch_cd_ticks, 0)
        evs2 = sess.step(_inp(catch=True))
        self.assertEqual(evs2[0]["name"], "fish_caught")
        self.assertEqual(evs2[0]["data"]["fish_id"], "F10")
        self.assertEqual(sess.sim.fish, [])

    def test_catch_surface_miss_and_partial_hold_full(self):
        """Ở mặt nước không bắt được; miss không kích hoạt cooldown; chỗ trống < yield -> hold_full, giữ đàn & cooldown."""
        # 1. Ở mặt nước -> không bắt
        sc_surf = {
            "player": {"pos": [15.0, self.g["surface_depth"]]},
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15.0, self.g["surface_depth"] + 0.5]}],
        }
        sess_surf = Session("gather", self.tuning, sc_surf, seed=1)
        self.assertEqual(sess_surf.step(_inp(catch=True)), [])
        self.assertEqual(sess_surf.sim.catch_cd_ticks, 0)

        # 2. Dưới nước nhưng không có cá trong tầm -> không sự kiện, không cooldown
        sc_miss = {"player": {"pos": [15.0, 5.0]}, "fish": []}
        sess_miss = Session("gather", self.tuning, sc_miss, seed=1)
        self.assertEqual(sess_miss.step(_inp(catch=True)), [])
        self.assertEqual(sess_miss.sim.catch_cd_ticks, 0)

        # 3. Chỗ trống = 2, cá linh cần 3 -> hold_full, giữ đàn, giữ cooldown = 0, không thử đàn khác
        cap = self.g["hold_capacity"]
        sc_full = {
            "player": {"pos": [15.0, 5.0]},
            "hold": ["bong_sung"] * (cap - 2),
            "fish": [
                {"id": "F1", "kind": "ca_linh", "pos": [15.5, 5.0]},
                {"id": "F2", "kind": "ca_loc", "pos": [16.0, 5.0]},
            ],
        }
        sess_full = Session("gather", self.tuning, sc_full, seed=1)
        evs = sess_full.step(_inp(catch=True))
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["name"], "hold_full")
        self.assertEqual(
            evs[0]["data"],
            {"action": "catch", "fish_id": "F1", "required": 3, "free": 2},
        )
        self.assertEqual(len(sess_full.sim.fish), 2)
        self.assertEqual(sess_full.sim.catch_cd_ticks, 0)
        self.assertEqual(len(sess_full.sim.hold), cap - 2)


class GatherHarvestHeadlessTests(unittest.TestCase):
    def test_headless_harvest_catch_dock_inventory_out(self):
        """Chạy headless từ hái nút -> bắt cá -> cập bến xuất kho đúng schema {"items": ...}."""
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [12, 0]},
                        "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}],
                        "fish": [{"id": "F1", "kind": "ca_linh", "pos": [12, 2]}],
                    }
                },
            )
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "interact": True},
                    {"tick": 1, "interact": False, "move": [0, 1]},
                    {"tick": 35, "move": [0, 0], "catch": True},
                    {"tick": 36, "catch": False, "move": [-1, -1]},
                    {"tick": 250, "move": [0, 0], "interact": True},
                ),
            )
            # Thay bằng kịch bản chắc chắn tới bến: đặt player ở [12,0] hái N1, lặn xuống [12,2] bắt F1,
            # rồi dùng scenario riêng cho dock hoặc chạy đủ tick về [2,0].
            # Từ [12, 2] về [2, 0] khoảng ~10.2m với speed=4m/s cần ~155 ticks.
            out = w.path("out.jsonl")
            inv = w.path("inv.json")
            p = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chonoi.headless",
                    "--mode",
                    "gather",
                    "--seed",
                    "1",
                    "--scenario",
                    sc,
                    "--inputs",
                    inp,
                    "--ticks",
                    "300",
                    "--out",
                    out,
                    "--inventory-out",
                    inv,
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(p.returncode, 0, p.stderr)
            rows = read_jsonl(out)
            self.assertEqual(len(events(rows, "gather")), 1)
            self.assertEqual(len(events(rows, "fish_caught")), 1)
            end_evs = events(rows, "gather_end")
            self.assertEqual(len(end_evs), 1)
            self.assertEqual(end_evs[0]["data"]["reason"], "docked")
            with open(inv, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved, {"items": {"bong_dien_dien": 1, "ca_linh": 3}})
            self.assertEqual(end_evs[0]["data"]["inventory"], saved)
            snap = snapshots(rows)[-1]
            self.assertEqual(snap["hold_count"], 4)


if __name__ == "__main__":
    unittest.main()
