"""Unit & headless tests cho Phase 2 Slice 2 (`gather`: Cá Sấu Năm Chèo M1/M2, va chạm, bất tử, rơi hàng LIFO, ngất)."""

import os
import subprocess
import sys
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputState
from chonoi.runner import Session
from chonoi.scenario import load_scenario
from helpers import ROOT, Workdir, events, frames, read_jsonl, snapshots, write_json


def _load_tuning():
    return load_contract(os.path.join(ROOT, "game.contract.json"))["tuning"]


def _inp(move=(0.0, 0.0), interact=False, catch=False):
    edges = set()
    if interact:
        edges.add("interact")
    if catch:
        edges.add("catch")
    return InputState(move, set(edges), edges)


class GatherMonstersUnitTests(unittest.TestCase):
    def setUp(self):
        self.tuning = _load_tuning()

    def test_default_monsters_day1_vs_day3(self):
        """Ngày 1 (và gather độc lập) chỉ có M1; từ Ngày 3 có thêm M2."""
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.gather import GatherSim

        sim1 = GatherSim(self.tuning, {}, Streams(1), IdAllocator())
        self.assertEqual([m["id"] for m in sim1.snapshot()["monsters"]], ["M1"])
        self.assertEqual(sim1.snapshot()["monsters"][0]["waypoints"], [[60.0, 24.0], [64.0, 24.0]])

        sim3 = GatherSim(self.tuning, {}, Streams(1), IdAllocator(), day=3)
        self.assertEqual([m["id"] for m in sim3.snapshot()["monsters"]], ["M1", "M2"])
        self.assertEqual(sim3.snapshot()["monsters"][1]["waypoints"], [[85.0, 18.0], [89.0, 18.0]])

    def test_patrol_chase_and_exit_chase(self):
        """Tuần tra 1.0 m/s đảo mốc; d>=10 & dist<=10 -> chase 3.0 m/s; dist>16 hoặc d<10 -> patrol."""
        sc = {
            "player": {"pos": [60.0, 5.0]},  # d < 10 -> không rượt
            "monsters": [
                {
                    "id": "M1",
                    "kind": "ca_sau",
                    "pos": [63.99, 24.0],
                    "waypoints": [[60.0, 24.0], [64.0, 24.0]],
                    "state": "patrol",
                    "target_idx": 1,
                }
            ],
            "random_fish": False,
        }
        sess = Session("gather", self.tuning, sc, seed=1)
        # Bước 1: chạm mốc [64, 24] và đảo target_idx về 0
        sess.step(_inp())
        m = sess.sim.snapshot()["monsters"][0]
        self.assertEqual(m["state"], "patrol")
        self.assertAlmostEqual(m["pos"][0], 64.0, places=4)
        self.assertEqual(m["target_idx"], 0)

        # Bước 2: di chuyển ngược về [60, 24] tốc độ 1/60 m/bước
        sess.step(_inp())
        m = sess.sim.snapshot()["monsters"][0]
        self.assertAlmostEqual(m["pos"][0], 64.0 - 1.0 / 60.0, places=5)

        # Đặt người chơi ở d=18, cách ~8.5m (<= 10m) -> chuyển chase 3.0 m/s
        sess.sim.pos = [58.0, 18.0]
        sess.step(_inp())
        m = sess.sim.snapshot()["monsters"][0]
        self.assertEqual(m["state"], "chase")

        # Người chơi lên d = 9.5 (< 10) -> quay lại patrol
        sess.sim.pos = [58.0, 9.5]
        sess.step(_inp())
        self.assertEqual(sess.sim.snapshot()["monsters"][0]["state"], "patrol")

        # Kiểm tra thoát chase khi dist > 16
        sess.sim.pos = [60.0, 15.0]
        sess.step(_inp())
        self.assertEqual(sess.sim.snapshot()["monsters"][0]["state"], "chase")
        sess.sim.pos = [30.0, 15.0]  # > 16m
        sess.step(_inp())
        self.assertEqual(sess.sim.snapshot()["monsters"][0]["state"], "patrol")

    def test_collision_lifo_drop_invuln_recoil_and_tie_break(self):
        """Va chạm sau di chuyển: max 1 hit/bước, hòa id_key, rơi floor(hold/2) LIFO, invuln=90, recoil 60 bước."""
        sc = {
            "player": {"pos": [60.0, 24.0], "hp": 3},
            "hold": [
                {"id": "I1", "kind": "ca_loc", "fresh": 100},
                {"id": "I2", "kind": "bong_sung", "fresh": 100},
                {"id": "I3", "kind": "ca_linh", "fresh": 100},
                {"id": "I4", "kind": "bong_dien_dien", "fresh": 100},
                {"id": "I5", "kind": "ca_loc", "fresh": 100},
            ],  # 5 -> rơi 2 (LIFO)
            "monsters": [
                {
                    "id": "M10",
                    "kind": "ca_sau",
                    "pos": [60.0, 24.0],
                    "waypoints": [[60.0, 24.0], [64.0, 24.0]],
                    "state": "patrol",
                    "target_idx": 1,
                },
                {
                    "id": "M2",
                    "kind": "ca_sau",
                    "pos": [60.0, 24.0],
                    "waypoints": [[60.0, 24.0], [64.0, 24.0]],
                    "state": "patrol",
                    "target_idx": 1,
                },
            ],
            "random_fish": False,
        }
        sess = Session("gather", self.tuning, sc, seed=1)
        evs = sess.step(_inp())
        hit_evs = [e for e in evs if e["name"] == "monster_hit"]
        self.assertEqual(len(hit_evs), 1)
        data = hit_evs[0]["data"]
        self.assertEqual(data["monster_id"], "M2")
        self.assertEqual(data["hp"], 2)
        self.assertEqual([it["id"] for it in data["lost"]], ["I5", "I4"])
        self.assertEqual([it["kind"] for it in data["lost"]], ["ca_loc", "bong_dien_dien"])
        self.assertEqual([it["id"] for it in sess.sim.hold], ["I1", "I2", "I3"])
        self.assertEqual(sess.sim.invuln_ticks, 90)

        m2 = next(m for m in sess.sim.snapshot()["monsters"] if m["id"] == "M2")
        self.assertEqual(m2["state"], "recoil")
        self.assertEqual(m2["recoil_ticks_left"], 60)

        # Trong lúc M2 recoil (và player đang bất tử): M2 lùi theo +x (vì trùng tọa độ)
        sess.step(_inp())
        m2_after = next(m for m in sess.sim.snapshot()["monsters"] if m["id"] == "M2")
        self.assertAlmostEqual(m2_after["pos"][0], 60.0 + 2.0 / 60.0, places=5)
        self.assertEqual(m2_after["recoil_ticks_left"], 59)

        # Chạy hết 59 bước recoil còn lại -> ở bước thứ 60 chuyển về patrol nhưng chưa đánh trong bước đó
        for _ in range(59):
            evs_r = sess.step(_inp())
            self.assertFalse(any(e["name"] == "monster_hit" for e in evs_r))
        m2_done = next(m for m in sess.sim.snapshot()["monsters"] if m["id"] == "M2")
        self.assertEqual(m2_done["state"], "patrol")
        self.assertEqual(m2_done["recoil_ticks_left"], 0)

    def test_faint_cause_monster_ends_immediately_with_empty_hold(self):
        """HP == 1 trúng cá sấu -> monster_hit, faint(cause='monster'), mất sạch hold, gather_end('fainted')."""
        sc = {
            "player": {"pos": [60.0, 24.0], "hp": 1},
            "hold": [
                {"id": "I1", "kind": "ca_loc", "fresh": 100},
                {"id": "I2", "kind": "bong_sung", "fresh": 100},
                {"id": "I3", "kind": "ca_linh", "fresh": 100},
            ],
            "monsters": [
                {
                    "id": "M1",
                    "kind": "ca_sau",
                    "pos": [60.0, 24.0],
                    "waypoints": [[60.0, 24.0], [64.0, 24.0]],
                    "state": "patrol",
                    "target_idx": 1,
                }
            ],
            "random_fish": False,
        }
        sess = Session("gather", self.tuning, sc, seed=1)
        evs = sess.step(_inp())
        names = [e["name"] for e in evs]
        self.assertEqual(names, ["monster_hit", "faint", "gather_end"])
        faint_data = evs[1]["data"]
        self.assertEqual(faint_data["cause"], "monster")
        self.assertEqual(faint_data["hp"], 0)
        self.assertEqual([it["id"] for it in faint_data["lost"]], ["I2", "I1"])
        self.assertEqual([it["kind"] for it in faint_data["lost"]], ["bong_sung", "ca_loc"])
        self.assertEqual(evs[2]["data"]["reason"], "fainted")
        self.assertEqual(evs[2]["data"]["inventory"], {"items": []})
        self.assertEqual(sess.sim.hold, [])
        self.assertTrue(sess.done)

    def test_scenario_monsters_validation_rejects_invalid(self):
        """scenario.py từ chối gather.monsters[] sai loài, ngoài độ sâu [10,30], trùng id, state lạ."""
        bad_cases = [
            [{"id": "M1", "kind": "ca_map", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}],
            [{"id": "M1", "kind": "ca_sau", "pos": [60, 9.5], "waypoints": [[60, 24], [64, 24]]}],
            [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 8], [64, 24]]}],
            [
                {"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]},
                {"id": "M1", "kind": "ca_sau", "pos": [70, 24], "waypoints": [[70, 24], [74, 24]]},
            ],
            [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]], "state": "sleep"}],
            [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]], "target_idx": 2}],
            [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]], "recoil_ticks_left": 61}],
        ]
        with Workdir() as w:
            for idx, monsters in enumerate(bad_cases):
                p = write_json(w.path(f"bad_{idx}.json"), {"gather": {"monsters": monsters}})
                with self.assertRaises(BadInput, msg=f"case {idx} should fail"):
                    load_scenario(p, "gather", self.tuning)


class GatherMonstersHeadlessTests(unittest.TestCase):
    def test_headless_invalid_monster_exit_2_without_output(self):
        with Workdir() as w:
            sc = write_json(
                w.path("bad.json"),
                {"gather": {"monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 5], "waypoints": [[60, 20], [64, 20]]}]}},
            )
            out = w.path("out.jsonl")
            p = subprocess.run(
                [sys.executable, "-m", "chonoi.headless", "--mode", "gather", "--seed", "1", "--ticks", "10", "--scenario", sc, "--out", out],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(p.returncode, 2)
            self.assertFalse(os.path.exists(out))

    def test_headless_monster_faint_empty_inventory(self):
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [60, 24], "hp": 1},
                        "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
                        "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}],
                    }
                },
            )
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
                    "--ticks",
                    "10",
                    "--scenario",
                    sc,
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
            self.assertEqual(events(rows, "faint")[0]["data"]["cause"], "monster")
            self.assertEqual(snapshots(rows)[-1]["hold_count"], 0)
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(f.read().strip(), '{"items":[]}')


if __name__ == "__main__":
    unittest.main()
