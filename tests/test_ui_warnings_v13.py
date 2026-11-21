"""Tests cho Phase 4 Slice 2: 3 cảnh báo chữ + biểu tượng và chế độ tương phản cao trong chonoi/web/index.html."""

import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_PATH = os.path.join(ROOT, "chonoi", "web", "index.html")


class WebWarningsAndContrastTests(unittest.TestCase):
    def setUp(self):
        with open(HTML_PATH, encoding="utf-8") as f:
            self.html = f.read()

    def test_three_icon_text_alerts_present(self):
        """Đủ 3 cảnh báo kèm biểu tượng + chữ và điều kiện kích hoạt chuẩn."""
        # 1. Thủy quái gần (chase hoặc dist <= 10 hoặc invuln_ticks > 60)
        self.assertIn("⚠ Thủy quái!", self.html)
        self.assertIn("<= 10", self.html)

        # 2. Oxy sắp hết / Hết hơi (< 25% hoặc == 0)
        self.assertIn("⚠ Hết hơi!", self.html)
        self.assertIn("⚠ Oxy sắp hết!", self.html)
        self.assertIn("< 0.25", self.html)

        # 3. Khách sắp giận (patience_ticks_left / (patience_s * 60) < 0.25)
        self.assertIn("⚠ Khách sắp giận!", self.html)
        self.assertIn("patience_ticks_left", self.html)
        self.assertIn("patience_s", self.html)

    def test_high_contrast_mode_toggle_and_palette(self):
        """Có chế độ tương phản cao: biến trạng thái, nút UI, phím C/H và bảng màu #000/#fff/#ff0/#f33/#0ff."""
        self.assertIn("highContrast", self.html)
        self.assertIn("toggleHighContrast", self.html)
        self.assertIn("Tương phản cao", self.html)
        for color in ("#000000", "#ffffff", "#ffff00", "#ff3b30", "#00ffff"):
            self.assertIn(color, self.html.lower())

    def test_font_size_and_v12_freshness_preserved(self):
        """Giữ nguyên font sans-serif >= 18px và các phần tử HUD độ tươi v1.2."""
        self.assertIn("18px/1.4 sans-serif", self.html)
        self.assertIn("Math.max(18,", self.html)
        self.assertIn("drawFreshnessBar", self.html)
        self.assertIn("[ƯƠN]", self.html)


if __name__ == "__main__":
    unittest.main()
