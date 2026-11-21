"""Unit và headless black-box tests cho Slice 1 (gather: sinh tồn dưới nước & giỏ LIFO)."""

import json
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim

from helpers import Workdir, close, events, frames, read_jsonl, run_headless, snapshots, write_json


def _make_sim(scenario=None, seed=1):
    tuning = load_contract()["tuning"]
    return GatherSim(tuning, scenario or {}, Streams(seed), IdAllocator()), tuning["gather"]


def _step_move(sim, move):
    return sim.step(InputState(tuple(move), {"interact": False, "catch": False}, set()))


class GatherSurvivalUnitTests(unittest.TestCase):
    def test_dive_and_surface_transitions_emit_once_with_pos(self):
        g = load_contract()["tuning"]["gather"]
        sim, _ = _make_sim({"player": {"pos": [20, g["surface_depth"]]}})
        self.assertTrue(sim.snapshot()["player"]["at_surface"])

        ev1 = _step_move(sim, (0.0, 1.0))
        self.assertIn("dive", [name for name, _ in ev1])
        dive_data = dict(ev1)["dive"]
        self.assertEqual(dive_data["pos"], sim.pos)
        self.assertFalse(sim.snapshot()["player"]["at_surface"])

        # Tiếp tục bơi xuống dưới nước: không phát lại `dive`
        ev2 = _step_move(sim, (0.0, 1.0))
        self.assertNotIn("dive", [name for name, _ in ev2])

        # Bơi lên tới khi qua ngưỡng mặt nước
        saw_surface = False
        for _ in range(30):
            ev = _step_move(sim, (0.0, -1.0))
            names = [name for name, _ in ev]
            if "surface" in names:
                self.assertFalse(saw_surface, "chỉ phát `surface` đúng 1 lần khi ngoi lên")
                saw_surface = True
                self.assertEqual(dict(ev)["surface"]["pos"], sim.pos)
                self.assertTrue(sim.snapshot()["player"]["at_surface"])
        self.assertTrue(saw_surface)

    def test_oxygen_drain_refill_clamp_and_zero_oxy_reset(self):
        g = load_contract()["tuning"]["gather"]
        sim, _ = _make_sim({
            "player": {
                "pos": [20, g["surface_depth"] + 0.1],
                "oxygen_ticks": 0,
                "zero_oxy_ticks": 5,
            }
        })
        # Ở dưới nước với oxygen_ticks=0 -> zero_oxy_ticks tăng
        _step_move(sim, (0.0, 0.0))
        self.assertEqual(sim.oxygen_ticks, 0)
        self.assertEqual(sim.zero_oxy_ticks, 6)

        # Ngoi lên mặt nước: hồi oxygen_refill_per_tick và reset zero_oxy_ticks
        sim2, _ = _make_sim({
            "player": {
                "pos": [20, g["surface_depth"]],
                "oxygen_ticks": sim.oxygen_max - 2,
            }
        })
        _step_move(sim2, (0.0, 0.0))
        self.assertEqual(sim2.oxygen_ticks, sim2.oxygen_max)
        self.assertEqual(sim2.zero_oxy_ticks, 0)

        # Kiểm tra hồi theo đúng tuning khi cách trần nhiều hơn refill
        refill = g["oxygen_refill_per_tick"]
        sim3, _ = _make_sim({
            "player": {
                "pos": [20, g["surface_depth"]],
                "oxygen_ticks": 10,
            }
        })
        _step_move(sim3, (0.0, 0.0))
        self.assertEqual(sim3.oxygen_ticks, min(sim3.oxygen_max, 10 + refill))
        self.assertEqual(sim3.zero_oxy_ticks, 0)

    def test_oxygen_empty_and_choke_interval(self):
        g = load_contract()["tuning"]["gather"]
        g_hp = g["hp_max"]
        sim, _ = _make_sim({
            "player": {
                "pos": [20, g["surface_depth"] + 2.0],
                "oxygen_ticks": 2,
                "hp": g_hp,
            }
        })
        # Tick 1: 2 -> 1
        ev1 = _step_move(sim, (0.0, 0.0))
        self.assertEqual(sim.oxygen_ticks, 1)
        self.assertEqual([n for n, _ in ev1], [])

        # Tick 2: 1 -> 0 -> oxygen_empty VÀ choke ngay bước chạm 0 (TICKET-02 v1.1)
        ev2 = _step_move(sim, (0.0, 0.0))
        self.assertEqual(sim.oxygen_ticks, 0)
        self.assertEqual([n for n, _ in ev2], ["oxygen_empty", "choke"])
        self.assertEqual(sim.hp, g_hp - 1)
        self.assertEqual(sim.zero_oxy_ticks, 0)

        # Đếm đủ choke_interval_ticks - 1 tick chưa ngạt thêm
        interval = g["choke_interval_ticks"]
        for _ in range(interval - 1):
            ev = _step_move(sim, (0.0, 0.0))
            self.assertEqual([n for n, _ in ev], [])
        self.assertEqual(sim.hp, g_hp - 1)
        self.assertEqual(sim.zero_oxy_ticks, interval - 1)

        # Tick thứ choke_interval_ticks -> choke tiếp theo, trừ 1 hp
        ev_choke = _step_move(sim, (0.0, 0.0))
        self.assertEqual([n for n, _ in ev_choke], ["choke"])
        self.assertEqual(sim.hp, g_hp - 2)
        self.assertEqual(sim.zero_oxy_ticks, 0)

    def test_hold_lifo_order_and_capacity(self):
        sim, g = _make_sim({
            "hold": [
                {"id": "I1", "kind": "ca_loc", "fresh": 100},
                {"id": "I2", "kind": "bong_sung", "fresh": 100},
            ]
        })
        cap = g["hold_capacity"]
        self.assertEqual([it["kind"] for it in sim.hold], ["ca_loc", "bong_sung"])
        self.assertEqual(sim._hold_free(), cap - 2)

        self.assertTrue(sim._push_hold("ca_linh", 2))
        self.assertEqual([it["kind"] for it in sim.hold], ["ca_loc", "bong_sung", "ca_linh", "ca_linh"])
        # Lấy ra theo LIFO (mới nhất là phần tử cuối)
        popped = sim._pop_hold()
        self.assertEqual((popped["id"], popped["kind"]), ("I4", "ca_linh"))
        self.assertEqual([it["kind"] for it in sim.hold], ["ca_loc", "bong_sung", "ca_linh"])

        # Không cho vượt quá hold_capacity
        free = sim._hold_free()
        self.assertFalse(sim._push_hold("bong_dien_dien", free + 1))
        self.assertEqual(len(sim.hold), cap - free)

        self.assertTrue(sim._push_hold("bong_dien_dien", free))
        self.assertEqual(len(sim.hold), cap)
        self.assertFalse(sim._push_hold("ca_loc", 1))

    def test_surface_depth_boundary_is_at_surface(self):
        g = load_contract()["tuning"]["gather"]
        sim, _ = _make_sim({
            "player": {
                "pos": [20, g["surface_depth"]],
                "oxygen_ticks": 100,
            }
        })
        self.assertTrue(sim.snapshot()["player"]["at_surface"])
        ev = _step_move(sim, (0.0, 0.0))
        self.assertEqual([n for n, _ in ev], [])
        self.assertEqual(sim.oxygen_ticks, min(sim.oxygen_max, 100 + g["oxygen_refill_per_tick"]))

    def test_faint_takes_precedence_over_dock_interact_same_tick(self):
        g = load_contract()["tuning"]["gather"]
        # dock_pos = [2, 0], dock_radius = 3 -> [2, 1] vừa trong vùng bến vừa ở dưới nước (> 0.5)
        dock_x, dock_d = g["dock_pos"]
        underwater_in_dock = [dock_x, min(g["surface_depth"] + 0.5, dock_d + g["dock_radius"] * 0.5)]
        self.assertGreater(underwater_in_dock[1], g["surface_depth"])
        sim, _ = _make_sim({
            "player": {
                "pos": underwater_in_dock,
                "oxygen_ticks": 0,
                "zero_oxy_ticks": g["choke_interval_ticks"] - 1,
                "hp": 1,
            },
            "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
        })
        ev = sim.step(InputState((0.0, 0.0), {"interact": True, "catch": False}, {"interact"}))
        self.assertEqual([n for n, _ in ev], ["choke", "faint", "gather_end"])
        self.assertEqual(dict(ev)["gather_end"]["reason"], "fainted")
        self.assertEqual(sim.inventory_items(), [])


class GatherSurvivalHeadlessTests(unittest.TestCase):
    def test_headless_dive_surface_and_oxygen_drain_refill(self):
        g = load_contract()["tuning"]["gather"]
        omax = int(round(g["oxygen_max_s"] * 60))
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [20, g["surface_depth"]]}}})
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "move": [0, 1]},
                    {"tick": 40, "move": [0, -1]},
                ),
            )
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "100",
                                     "--scenario", sc, "--inputs", inp, "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            dives = events(rows, "dive")
            surfaces = events(rows, "surface")
            self.assertEqual(len(dives), 1)
            self.assertEqual(len(surfaces), 1)
            self.assertGreater(dives[0]["data"]["pos"][1], g["surface_depth"])
            self.assertLessEqual(surfaces[0]["data"]["pos"][1], g["surface_depth"])
            snaps = {r["tick"]: r for r in snapshots(rows)}
            # Có thời điểm oxy giảm dưới max rồi hồi lên max
            min_oxy = min(r["player"]["oxygen_ticks"] for r in snaps.values())
            self.assertLess(min_oxy, omax)
            self.assertEqual(snaps[100]["player"]["oxygen_ticks"], omax)

    def test_headless_faint_clears_hold_writes_empty_inventory_before_time_end(self):
        g = load_contract()["tuning"]["gather"]
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {
                        "pos": [20, g["surface_depth"] + 5.0],
                        "oxygen_ticks": 0,
                        "zero_oxy_ticks": g["choke_interval_ticks"] - 1,
                        "hp": 1,
                    },
                    "hold": [
                        {"id": "I1", "kind": "ca_loc", "fresh": 100},
                        {"id": "I2", "kind": "bong_sung", "fresh": 100},
                        {"id": "I3", "kind": "ca_linh", "fresh": 100},
                    ],
                    "time_left_ticks": 1,
                }
            })
            out = w.path("o.jsonl")
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "3", "--ticks", "10",
                                     "--scenario", sc, "--inventory-out", inv, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            ev_names = [r["name"] for r in events(rows)]
            self.assertEqual(ev_names, ["choke", "faint", "gather_end"])
            end_ev = events(rows, "gather_end")[0]
            self.assertEqual(end_ev["data"]["reason"], "fainted")
            self.assertEqual(end_ev["data"]["inventory"], {"items": []})
            self.assertEqual(rows[-1]["reason"], "fainted")
            final_snap = snapshots(rows)[-1]
            self.assertEqual(final_snap["player"]["hp"], 0)
            self.assertEqual(final_snap["hold"], [])
            self.assertEqual(final_snap["hold_count"], 0)
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})

    def test_headless_survival_deterministic_bytes(self):
        g = load_contract()["tuning"]["gather"]
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {
                        "pos": [20, g["surface_depth"] + 5.0],
                        "oxygen_ticks": 2,
                        "hp": 1,
                    },
                    "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
                }
            })
            ticks = g["choke_interval_ticks"] + 5
            for i in (1, 2):
                code, err = run_headless("--mode", "gather", "--seed", "9", "--ticks", str(ticks),
                                         "--scenario", sc, "--inventory-out", w.path(f"inv{i}.json"),
                                         "--out", w.path(f"o{i}.jsonl"))
                self.assertEqual(code, 0, err)
            with open(w.path("o1.jsonl"), "rb") as a, open(w.path("o2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())
            with open(w.path("inv1.json"), "rb") as a, open(w.path("inv2.json"), "rb") as b:
                self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
