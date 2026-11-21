"""Tests cho Phase 2 Slice 1: Contract v1.1, inputs/inventory, cá bơi/phản xạ/sinh cá & choke bước chạm 0."""

import json
import math
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer, InputState, LiveInputs, load_frames
from chonoi.inventory import KINDS_P2, validate_items
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim, TICK

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def _make_sim(scenario=None, seed=1):
    tuning = load_contract()["tuning"]
    return GatherSim(tuning, scenario or {}, Streams(seed), IdAllocator()), tuning["gather"]


def _idle_inp(interact=False, catch=False):
    edges = set()
    if interact:
        edges.add("interact")
    if catch:
        edges.add("catch")
    return InputState((0.0, 0.0), {"interact": interact, "catch": catch}, edges)


class ContractAndInputsV11Tests(unittest.TestCase):
    def test_contract_v11_structure_and_tuning(self):
        c = load_contract()
        self.assertEqual(c["contract_version"], "1.1")
        t = c["tuning"]
        g = t["gather"]
        self.assertEqual(len(g["nodes"]), 6)
        nodes_by_id = {n["id"]: n for n in g["nodes"]}
        self.assertEqual(nodes_by_id["N5"], {"id": "N5", "kind": "keo_neo", "pos": [76, 0]})
        self.assertEqual(nodes_by_id["N6"], {"id": "N6", "kind": "keo_neo", "pos": [90, 0]})
        self.assertEqual(g["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})
        self.assertEqual(g["fish_initial"], 8)
        self.assertEqual(g["fish_max"], 12)
        self.assertEqual(g["fish_speed"], 1.5)
        self.assertEqual(g["fish_turn_ticks"], 120)
        self.assertEqual(g["fish_spawn_ticks"], 360)
        self.assertEqual(g["fish_spawn_clearance"], 1.0)
        self.assertEqual(g["fish_x"], [4, 96])
        self.assertEqual(g["fish_depths"], {"ca_linh": [3, 12], "ca_loc": [8, 20], "ca_keo": [22, 28]})
        self.assertEqual(g["fish_weights"], {"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3})
        self.assertEqual(len(t["menu"]), 6)
        self.assertEqual(t["menu"]["lau_mam"]["recipe"],
                         {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1})
        self.assertEqual(len(t["day_plan"]), 5)
        self.assertEqual(t["shop"]["max_ticks"], 600)

    def test_inventory_accepts_6_ingredients_and_rejects_unknown(self):
        items = validate_items({k: 1 for k in KINDS_P2})
        self.assertEqual(set(items), set(KINDS_P2))
        with self.assertRaises(BadInput):
            validate_items({"ca_khong_co": 1})

    def test_inputs_v11_pause_shop_done_and_buy_string(self):
        with Workdir() as w:
            p = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "pause": True},
                    {"tick": 1, "pause": True, "buy": "oxygen"},
                    {"tick": 2, "shop_done": True},
                ),
            )
            pl = InputPlayer(load_frames(p))
            s0 = pl.advance(0)
            self.assertTrue(s0.pressed("pause"))
            self.assertIsNone(s0.buy)

            s1 = pl.advance(1)
            self.assertFalse(s1.pressed("pause"))
            self.assertEqual(s1.buy, "oxygen")

            s2 = pl.advance(2)
            self.assertTrue(s2.pressed("shop_done"))
            self.assertIsNone(s2.buy, "buy chỉ có hiệu lực tại frame khai báo")

            for bad in ({"tick": 0, "buy": True}, {"tick": 0, "buy": ""}, {"tick": 0, "pause": "yes"}):
                bp = write_json(w.path("bad.json"), frames(bad))
                with self.assertRaises(BadInput):
                    load_frames(bp)

        li = LiveInputs()
        li.set(pause=True, buy="hp")
        st = li.advance()
        self.assertTrue(st.pressed("pause"))
        self.assertEqual(st.buy, "hp")
        st2 = li.advance()
        self.assertFalse(st2.pressed("pause"))
        self.assertIsNone(st2.buy)
        with self.assertRaises(BadInput):
            li.set(buy=True)


class GatherFishV11Tests(unittest.TestCase):
    def test_initial_8_schools_distinct_positions_and_random_fish_false(self):
        sim, g = _make_sim(seed=5)
        self.assertEqual(len(sim.fish), g["fish_initial"])
        positions = {tuple(f["pos"]) for f in sim.fish}
        self.assertEqual(len(positions), 8)
        self.assertTrue(all(f["age_ticks"] == 0 for f in sim.fish))

        # random_fish: false -> không tạo cá mặc định và giữ nguyên cá fixture đứng yên
        sim_off, _ = _make_sim({
            "random_fish": False,
            "fish": [{"id": "F1", "kind": "ca_keo", "pos": [30, 24], "heading_deg": 0, "age_ticks": 10}],
        })
        for _ in range(125):
            sim_off.step(_idle_inp())
        self.assertEqual(len(sim_off.fish), 1)
        self.assertEqual(sim_off.fish[0]["pos"], [30.0, 24.0])
        self.assertEqual(sim_off.fish[0]["age_ticks"], 10)

        sim_empty, _ = _make_sim({"random_fish": False})
        self.assertEqual(sim_empty.fish, [])
        for _ in range(365):
            ev = sim_empty.step(_idle_inp())
            self.assertEqual([n for n, _ in ev], [])
        self.assertEqual(sim_empty.fish, [])

    def test_fish_swim_120_tick_turn_before_moving(self):
        sim, g = _make_sim({
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [50, 7], "heading_deg": 0, "age_ticks": 118}]
        }, seed=3)
        step_dist = g["fish_speed"] / TICK
        # Bước 1: age_ticks 118 -> 119, giữ heading 0
        sim.step(_idle_inp())
        self.assertEqual(sim.fish[0]["age_ticks"], 119)
        self.assertAlmostEqual(sim.fish[0]["pos"][0], 50.0 + step_dist)
        self.assertAlmostEqual(sim.fish[0]["pos"][1], 7.0)
        self.assertEqual(sim.fish[0]["heading_deg"], 0.0)

        # Bước 2: age_ticks 119 -> 120 -> đổi hướng theo Streams TRƯỚC khi di chuyển
        prev_pos = list(sim.fish[0]["pos"])
        sim.step(_idle_inp())
        self.assertEqual(sim.fish[0]["age_ticks"], 120)
        new_h = sim.fish[0]["heading_deg"]
        self.assertNotEqual(new_h, 0.0)
        rad = math.radians(new_h)
        self.assertAlmostEqual(sim.fish[0]["pos"][0], prev_pos[0] + math.cos(rad) * step_dist)
        self.assertAlmostEqual(sim.fish[0]["pos"][1], prev_pos[1] + math.sin(rad) * step_dist)

    def test_fish_edge_and_corner_reflection(self):
        # Chạm mép phải x = 96 và mép đáy ca_linh d = 12 trong cùng 1 bước (góc)
        sim, g = _make_sim({
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [95.99, 11.99], "heading_deg": 45}]
        })
        step_dist = g["fish_speed"] / TICK
        delta = step_dist * math.cos(math.radians(45))
        sim.step(_idle_inp())
        f = sim.fish[0]
        self.assertAlmostEqual(f["pos"][0], 2 * 96.0 - (95.99 + delta))
        self.assertAlmostEqual(f["pos"][1], 2 * 12.0 - (11.99 + delta))
        self.assertAlmostEqual(f["heading_deg"], 225.0)

    def test_fish_spawn_schedule_clearance_normalized_weights_and_cap(self):
        # Đặt cá tại tất cả điểm sinh ca_keo (d in {24, 27}, 6 cột x -> 12 điểm; nhưng cap < 12 để sinh được!)
        # Dùng 11 đàn chặn toàn bộ điểm ca_keo: 6 điểm ở d=24, và chọn 5 điểm ở d=27 (chừa [90, 27] và đặt player tại [90, 27])
        # -> 0 điểm ca_keo hợp lệ; chỉ ca_linh & ca_loc hợp lệ!
        fish_list = [
            {"id": f"F{i}", "kind": "ca_keo", "pos": [x, 24], "heading_deg": 0}
            for i, x in enumerate([15, 30, 45, 60, 75, 90], 1)
        ] + [
            {"id": f"F{i}", "kind": "ca_keo", "pos": [x, 27], "heading_deg": 0}
            for i, x in enumerate([15, 30, 45, 60, 75], 7)
        ]
        sim, g = _make_sim({"player": {"pos": [90, 27]}, "fish": fish_list}, seed=2)
        self.assertEqual(len(sim.fish), 11)
        # Chạy tới phase_tick = 360: cá bơi 360 bước (vẫn quanh [x, 24]/[x, 27]), và sinh tại 360
        # Đặt random_fish=True, kiểm tra sự kiện fish_spawned tại phase_tick=360
        spawned_at = []
        for _ in range(360):
            ev = sim.step(_idle_inp())
            for name, data in ev:
                if name == "fish_spawned":
                    spawned_at.append((sim.phase_tick, data))
        self.assertEqual(len(spawned_at), 1)
        self.assertEqual(spawned_at[0][0], 360)
        self.assertEqual(len(sim.fish), 12)
        self.assertIn(spawned_at[0][1]["kind"], ("ca_linh", "ca_loc", "ca_keo"))
        # Đã đạt fish_max=12 -> tick 720 không sinh thêm
        for _ in range(360):
            ev = sim.step(_idle_inp())
            self.assertNotIn("fish_spawned", [n for n, _ in ev])
        self.assertEqual(len(sim.fish), 12)

    def test_fish_spawn_normalized_weights_when_species_blocked(self):
        # Đứng yên ở thời điểm kiểm tra sinh bằng cách test _step_fish_spawn trực tiếp sau khi chặn hết điểm ca_keo
        # (chỉ còn 11 đàn: dùng vị trí [x, 25.5] chặn đồng thời cả d=24 và d=27? Không, dist([x, 25.5], [x, 24]) = 1.5 > 1.0)
        # Đặt 6 đàn tại [x, 24] và 5 đàn tại [x, 27] (x=15..75), player tại [90, 27], phase_tick = 359
        fish_list = [
            {"id": f"F{i}", "kind": "ca_keo", "pos": [x, 24], "heading_deg": 0}
            for i, x in enumerate([15, 30, 45, 60, 75, 90], 1)
        ] + [
            {"id": f"F{i}", "kind": "ca_keo", "pos": [x, 27], "heading_deg": 0}
            for i, x in enumerate([15, 30, 45, 60, 75], 7)
        ]
        sim, _ = _make_sim({"player": {"pos": [90, 27]}, "fish": fish_list}, seed=7)
        sim.phase_tick = 360
        ev = []
        sim._step_fish_spawn(ev)
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0][0], "fish_spawned")
        self.assertIn(ev[0][1]["kind"], ("ca_linh", "ca_loc"))
        self.assertEqual(ev[0][1]["id"], "F12")

    def test_catch_uses_pre_swim_position_and_no_swim_on_time_end(self):
        sim, g = _make_sim({
            "player": {"pos": [20.0, 10.0]},
            "fish": [{"id": "F1", "kind": "ca_keo", "pos": [22.0, 10.0], "heading_deg": 0}],
            "time_left_ticks": 1,
        })
        # Nếu bơi trước thì F1 chạy ra 22.025 (> catch_radius 2.0); theo mục 4.5 catch chạy trước bơi -> bắt được!
        ev = sim.step(_idle_inp(catch=True))
        self.assertEqual([n for n, _ in ev], ["fish_caught", "gather_end"])
        self.assertEqual(sim.hold, ["ca_keo", "ca_keo"])
        self.assertEqual(sim.fish, [])


class ChokeOnZeroV11Tests(unittest.TestCase):
    def test_choke_on_zero_pierces_invuln_preserves_hold_and_faints_with_cause(self):
        g = load_contract()["tuning"]["gather"]
        sim, g = _make_sim({
            "player": {
                "pos": [20, g["surface_depth"] + 2.0],
                "oxygen_ticks": 1,
                "hp": 2,
                "invuln_ticks": 90,
            },
            "hold": ["ca_loc", "keo_neo"],
        })
        # Bước vừa chạm 0: phát oxygen_empty VÀ choke (xuyên invuln_ticks, không rơi hold)
        ev1 = sim.step(_idle_inp())
        self.assertEqual([n for n, _ in ev1], ["oxygen_empty", "choke"])
        self.assertEqual(sim.hp, 1)
        self.assertEqual(sim.hold, ["ca_loc", "keo_neo"])
        self.assertEqual(sim.zero_oxy_ticks, 0)

        # Chạy 59 bước -> chưa choke
        for _ in range(59):
            self.assertEqual(sim.step(_idle_inp()), [])
        self.assertEqual(sim.hp, 1)

        # Bước 60 -> choke -> hp=0 -> faint(cause="oxygen", lost LIFO) + gather_end("fainted")
        ev60 = sim.step(_idle_inp())
        self.assertEqual([n for n, _ in ev60], ["choke", "faint", "gather_end"])
        faint_data = dict(ev60)["faint"]
        self.assertEqual(faint_data["cause"], "oxygen")
        self.assertEqual(faint_data["hp"], 0)
        self.assertEqual(faint_data["lost"], ["keo_neo", "ca_loc"])
        self.assertEqual(sim.hold, [])
        self.assertEqual(dict(ev60)["gather_end"]["reason"], "fainted")


class HeadlessV11IntegrationTests(unittest.TestCase):
    def test_headless_n5_keo_neo_and_ca_keo_plus_determinism_and_bad_age_ticks(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [76, 0]},
                    "fish": [{"id": "F1", "kind": "ca_keo", "pos": [76, 2], "heading_deg": 0, "age_ticks": 0}],
                }
            })
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False, "move": [0, 1]},
                {"tick": 35, "move": [0, 0], "catch": True},
            ))
            out1, out2 = w.path("o1.jsonl"), w.path("o2.jsonl")
            for out in (out1, out2):
                code, err = run_headless("--mode", "gather", "--seed", "11", "--ticks", "60",
                                         "--scenario", sc, "--inputs", inp, "--out", out)
                self.assertEqual(code, 0, err)
            with open(out1, "rb") as a, open(out2, "rb") as b:
                self.assertEqual(a.read(), b.read())
            rows = read_jsonl(out1)
            self.assertEqual(events(rows, "gather")[0]["data"]["kind"], "keo_neo")
            self.assertEqual(events(rows, "fish_caught")[0]["data"]["kind"], "ca_keo")

            bad_sc = write_json(w.path("bad_sc.json"), {
                "gather": {"fish": [{"id": "F1", "kind": "ca_keo", "pos": [30, 24], "age_ticks": -1}]}
            })
            code_bad, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                       "--scenario", bad_sc, "--out", w.path("never.jsonl"))
            self.assertEqual(code_bad, 2)


if __name__ == "__main__":
    unittest.main()
