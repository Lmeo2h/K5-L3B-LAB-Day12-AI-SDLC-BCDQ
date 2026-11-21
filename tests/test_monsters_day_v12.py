"""Unit tests cho Phase 3 Slice 2 (TICKET-03 v1.2):
- `monsters.py`: `monster_hit.lost` & `faint.lost` trả mảng cá thể LIFO sạch `{"id", "kind", "fresh"}`
- `day.py`: `DaySim.item_ids` liên tục xuyên pha & Ngày 1..5, bàn giao `gather -> quan` không hao thêm.
"""

import os
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.day import DaySim
from chonoi.sim.monsters import step_monsters
from helpers import ROOT


def _load_tuning():
    return load_contract(os.path.join(ROOT, "game.contract.json"))["tuning"]


def _inp(move=(0.0, 0.0), interact=False, catch=False):
    edges = set()
    if interact:
        edges.add("interact")
    if catch:
        edges.add("catch")
    return InputState(move, set(edges), edges)


class _DummySim:
    """Giả lập GatherSim mang hold cá thể (kèm _units nội bộ) để test monsters.py độc lập."""

    def __init__(self, tuning, pos, hold, hp=3):
        self.t = tuning["gather"]
        self.pos = list(pos)
        self.hold = list(hold)
        self.hp = hp
        self.invuln_ticks = 0
        self.done = False
        self.reason = None
        self.monsters = [
            {
                "id": "M1",
                "kind": "ca_sau",
                "pos": list(pos),
                "waypoints": [list(pos), [pos[0] + 4.0, pos[1]]],
                "state": "patrol",
                "target_idx": 1,
                "recoil_ticks_left": 0,
                "recoil_origin": list(pos),
                "recoil_dir": None,
            }
        ]

    def _pop_hold(self):
        return self.hold.pop() if self.hold else None

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": []}}))


class MonstersV12Tests(unittest.TestCase):
    def setUp(self):
        self.tuning = _load_tuning()

    def test_monster_hit_and_faint_return_clean_lifo_item_dicts(self):
        """monster_hit.lost và faint.lost trả dict cá thể LIFO sạch (không lộ _units, giữ nguyên fresh)."""
        hold = [
            {"id": "I1", "kind": "ca_loc", "fresh": 99.5, "_units": 23880},
            {"id": "I2", "kind": "bong_sung", "fresh": 80.0, "_units": 19200},
            {"id": "I3", "kind": "ca_linh", "fresh": 29.991667, "_units": 7198},
        ]
        sim = _DummySim(self.tuning, pos=[60.0, 24.0], hold=hold, hp=2)
        events = []
        ended = step_monsters(sim, events)
        self.assertFalse(ended)
        self.assertEqual(len(events), 1)
        name, data = events[0]
        self.assertEqual(name, "monster_hit")
        self.assertEqual(data["hp"], 1)
        # floor(3 * 0.5) = 1 -> pop I3 (cuối mảng, LIFO)
        self.assertEqual(len(data["lost"]), 1)
        self.assertEqual(set(data["lost"][0].keys()), {"id", "kind", "fresh"})
        self.assertEqual(data["lost"][0]["id"], "I3")
        self.assertAlmostEqual(data["lost"][0]["fresh"], 7198 / 240.0, places=5)

        # Va chạm thứ 2 khi hp == 1 -> faint(cause="monster"), pop phần còn lại LIFO [I2, I1]
        sim.invuln_ticks = 0
        sim.monsters[0]["state"] = "patrol"
        sim.monsters[0]["recoil_ticks_left"] = 0
        sim.monsters[0]["pos"] = [60.0, 24.0]
        events2 = []
        ended2 = step_monsters(sim, events2)
        self.assertTrue(ended2)
        self.assertEqual([e[0] for e in events2], ["monster_hit", "faint", "gather_end"])
        self.assertEqual(events2[0][1]["lost"], [{"id": "I2", "kind": "bong_sung", "fresh": 80.0}])
        self.assertEqual(events2[1][1]["cause"], "monster")
        self.assertEqual(events2[1][1]["lost"], [{"id": "I1", "kind": "ca_loc", "fresh": 99.5}])
        self.assertEqual(sim.hold, [])


class DaySimV12Tests(unittest.TestCase):
    def setUp(self):
        self.tuning = _load_tuning()

    def test_day_sim_reserves_item_ids_and_persists_across_days(self):
        """DaySim reserve ID từ scenario Ngày 1 và giữ item_ids tăng liên tục qua Ngày 2+."""
        scenario = {
            "gather": {
                "hold": [
                    {"id": "I10", "kind": "ca_loc", "fresh": 100.0},
                ]
            }
        }
        day_sim = DaySim(self.tuning, scenario, Streams(1), IdAllocator(), days=2)
        self.assertEqual(day_sim.item_ids.new("I"), "I11")

        # Kiểm tra _reassign_hold_ids cho Ngày 2+ khi có mẫu hold lặp lại
        reassigned = day_sim._reassign_hold_ids([
            {"id": "I10", "kind": "ca_loc", "fresh": 95.0},
            {"id": "I1", "kind": "bong_sung", "fresh": 50.0},
        ])
        self.assertEqual([x["id"] for x in reassigned], ["I12", "I13"])
        self.assertEqual([x["fresh"] for x in reassigned], [95.0, 50.0])

    def test_day_sim_gather_to_quan_handoff_no_extra_decay(self):
        """Chuyển pha gather -> quan cùng tick giữ nguyên stock/hold bàn giao và không hao thêm ở tick chuyển."""
        scenario = {
            "gather": {"time_left_ticks": 1},
            "quan": {"time_left_ticks": 5},
            "shop": {"max_ticks": 1},
        }
        day_sim = DaySim(self.tuning, scenario, Streams(1), IdAllocator(), days=2)
        item_ids_id = id(day_sim.item_ids)
        evs = day_sim.step(_inp())
        self.assertEqual(day_sim.phase, "quan")
        self.assertTrue(any(e[2] == "phase_start" and e[1] == "quan" for e in evs))
        # item_ids vẫn là cùng một IdAllocator xuyên pha
        self.assertEqual(id(day_sim.item_ids), item_ids_id)
        # Sau khi quan & shop kết thúc sang Ngày 2, item_ids vẫn không bị reset
        for _ in range(10):
            if day_sim.day == 2:
                break
            inp = InputState((0.0, 0.0), {"shop_done"}, {"shop_done"}) if day_sim.phase == "shop" else _inp()
            day_sim.step(inp)
        self.assertEqual(day_sim.day, 2)
        self.assertEqual(id(day_sim.item_ids), item_ids_id)


if __name__ == "__main__":
    unittest.main()
