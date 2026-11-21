"""Tests for Phase 3 Slice 4: ShopSim v1.2 individual-item stock preservation, runner handoff, and HUD freshness/spoiled UI."""

import copy
import os
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.sim.shop import ShopSim


def _v12_shop_tuning():
    t = copy.deepcopy(load_contract()["tuning"])
    t.setdefault("shop", {
        "max_ticks": 600,
        "upgrades": {
            "oxygen": [
                {"level": 1, "price": 200, "oxygen_max_s": 45},
                {"level": 2, "price": 400, "oxygen_max_s": 60},
            ],
            "hp": [
                {"level": 1, "price": 250, "hp_max": 4},
                {"level": 2, "price": 500, "hp_max": 5},
            ],
        },
    })
    return t


class ShopV12PreservationTests(unittest.TestCase):
    def test_shop_preserves_individual_stock_without_decay_for_600_ticks(self):
        tuning = _v12_shop_tuning()
        stock = [
            {"id": "I1", "kind": "ca_loc", "fresh": 85.5, "_units": 20520},
            {"id": "I2", "kind": "bong_sung", "fresh": 29.0, "_units": 6960},
        ]
        shop = ShopSim(tuning, money=500, earned=500, stock=stock, day=1)
        expected = [
            {"id": "I1", "kind": "ca_loc", "fresh": 85.5},
            {"id": "I2", "kind": "bong_sung", "fresh": 29.0},
        ]
        self.assertEqual(shop.snapshot()["stock"], expected)

        idle = InputState((0.0, 0.0), {}, set())
        for _ in range(tuning["shop"]["max_ticks"]):
            shop.step(idle)

        self.assertTrue(shop.done)
        self.assertEqual(shop.reason, "time")
        self.assertEqual(shop.snapshot()["stock"], expected)


class WebFreshnessHudTests(unittest.TestCase):
    def test_web_hud_includes_freshness_bar_and_spoiled_badge_with_18px_font(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        html_path = os.path.join(root, "chonoi", "web", "index.html")
        with open(html_path, encoding="utf-8") as f:
            html = f.read()
        self.assertIn("drawFreshnessBar", html)
        self.assertIn("[ƯƠN]", html)
        self.assertIn("fresh < 30", html)
        self.assertIn("18px sans-serif", html)


if __name__ == "__main__":
    unittest.main()
