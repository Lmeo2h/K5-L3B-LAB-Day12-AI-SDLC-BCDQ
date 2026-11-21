import json
import math
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from chonoi import bench
from tests.helpers import ROOT, Workdir


FIELDS = {"frames", "measured_s", "avg_fps", "p1_low_fps", "load_ms"}


class BenchTests(unittest.TestCase):
    def test_uses_ceiling_and_mean_of_slowest_intervals(self):
        intervals = [0.01] * 99 + [0.05, 0.04]
        result = bench.summarize_frames(intervals, 144)
        self.assertEqual(set(result), FIELDS)
        self.assertEqual(result["frames"], 101)
        self.assertAlmostEqual(result["measured_s"], 1.08)
        self.assertAlmostEqual(result["avg_fps"], 101 / 1.08)
        self.assertAlmostEqual(result["p1_low_fps"], 1 / 0.045)
        self.assertEqual(result["load_ms"], 144)
        self.assertEqual(bench.summarize_frames([0.02], 0)["p1_low_fps"], 50)

    def test_atomic_output_preserves_previous_report_on_replace_failure(self):
        with Workdir() as work:
            target = Path(work.path("bench.json"))
            target.write_text("old report", encoding="utf-8")
            report = bench.summarize_frames([0.02], 0)
            with patch.object(bench.os, "replace", side_effect=OSError("replace failed")):
                with self.assertRaises(OSError):
                    bench.write_report(target, report)
            self.assertEqual(target.read_text(encoding="utf-8"), "old report")
            self.assertEqual(list(target.parent.iterdir()), [target])
            bench.write_report(target, report)
            self.assertEqual(json.loads(target.read_bytes()), report)

    def test_cli_creates_valid_report_without_browser(self):
        with Workdir() as work:
            target = Path(work.path("bench.json"))
            target.write_text("previous report", encoding="utf-8")
            cmd = [sys.executable, "-m", "chonoi.bench", "--seed", "42", "--duration", "1",
                   "--out", str(target), "--renderer", "software"]
            result = subprocess.run(cmd, cwd=ROOT, capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(target.read_bytes())
            self.assertEqual(set(report), FIELDS)
            self.assertIs(type(report["frames"]), int)
            self.assertGreater(report["frames"], 0)
            self.assertGreaterEqual(report["measured_s"], 1)
            self.assertLess(report["measured_s"], 3)
            self.assertTrue(all(math.isfinite(value) for value in report.values()))
            self.assertAlmostEqual(report["avg_fps"], report["frames"] / report["measured_s"])
            self.assertGreater(report["p1_low_fps"], 0)
            self.assertLessEqual(report["p1_low_fps"], report["avg_fps"] + 1e-9)
            self.assertGreaterEqual(report["load_ms"], 0)
            self.assertEqual(list(target.parent.iterdir()), [target])

    def test_cli_rejects_non_finite_duration_without_replacing_file(self):
        with Workdir() as work:
            target = Path(work.path("bench.json"))
            target.write_text("old report", encoding="utf-8")
            result = subprocess.run([sys.executable, "-m", "chonoi.bench", "--duration", "nan",
                                     "--out", str(target)], cwd=ROOT, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), "old report")

    def test_auto_uses_software_when_no_browser_is_installed(self):
        with Workdir() as work:
            target = Path(work.path("bench.json"))
            expected = bench.summarize_frames([0.02], 1)
            with patch.object(bench, "_browser_paths", return_value=[]), patch.object(
                bench, "_measure_software", return_value=expected
            ) as render:
                self.assertEqual(bench.main(["--out", str(target)]), 0)
            self.assertEqual(render.call_args.args[1:], (42, 30.0))
            self.assertEqual(json.loads(target.read_bytes()), expected)
