"""Benchmark the default gather scene with the web renderer or a software framebuffer."""

import argparse
import json
import math
import os
from pathlib import Path
from queue import Empty, SimpleQueue
import shutil
import subprocess
import sys
import tempfile
import time

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .live import LiveGame, LiveServer
from .runner import Session


WIDTH, HEIGHT = 1280, 720
WARMUP_S = 3.0


def summarize_frames(intervals, load_ms):
    if not intervals or any(not math.isfinite(dt) or dt <= 0 for dt in intervals):
        raise ValueError("benchmark needs positive, finite frame intervals")
    if not math.isfinite(load_ms) or load_ms < 0:
        raise ValueError("benchmark needs a nonnegative, finite load time")
    frames = len(intervals)
    measured = math.fsum(intervals)
    count = max(1, math.ceil(0.01 * frames))
    slowest = sorted(intervals, reverse=True)[:count]
    return {
        "frames": frames,
        "measured_s": measured,
        "avg_fps": frames / measured,
        "p1_low_fps": count / math.fsum(slowest),
        "load_ms": load_ms,
    }


def write_report(path, report):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix=".bench-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            json.dump(report, output, indent=2, allow_nan=False)
            output.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _browser_paths():
    names = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
             "microsoft-edge", "chrome", "msedge")
    paths = [shutil.which(name) for name in names]
    if sys.platform == "win32":
        for root in (os.getenv("ProgramFiles"), os.getenv("ProgramFiles(x86)"), os.getenv("LOCALAPPDATA")):
            if root:
                paths.extend(Path(root) / name for name in (
                    "Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe"))
    elif sys.platform == "darwin":
        paths.extend(Path("/Applications") / f"{app}.app/Contents/MacOS/{app}"
                     for app in ("Google Chrome", "Chromium", "Microsoft Edge"))
    return list(dict.fromkeys(Path(path).absolute() for path in paths if path and Path(path).is_file()))


# Instrument only the benchmark page, leaving the delivered web client unchanged.
# The draw hook runs inside the normal rAF callback and only after a gather snapshot is available.
_INSTRUMENT = """
<script>
(() => {
  screen = "play";
  fit = () => {
    if (cv.width !== WIDTH || cv.height !== HEIGHT) {
      cv.width = WIDTH;
      cv.height = HEIGHT;
    }
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    return [WIDTH, HEIGHT];
  };
  const draw = drawGather;
  const intervals = [];
  let first = null, start = null, previous = null, finished = false;
  const publish = (data) => fetch("/__bench_result", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  });
  drawGather = (w, h) => {
    draw(w, h);
    if (finished) return;
    if (snap.error || snap.finished || snap.state === "finished") {
      finished = true;
      publish({error: "gather scene stopped before the benchmark ended"});
      return;
    }
    const now = performance.now();
    if (first === null) first = now;
    if (now - first < WARMUP_MS) return;
    if (start === null) {
      start = previous = now;
      return;
    }
    if (now <= previous) return;
    intervals.push((now - previous) / 1000);
    previous = now;
    if (now - start >= DURATION_MS) {
      finished = true;
      const load_ms = Math.max(0, performance.timeOrigin + first - LAUNCH_MS);
      publish({intervals, load_ms});
    }
  };
})();
</script>
"""


def _browser_server(tuning, seed, duration, launch_ms, results):
    page = Path(__file__).with_name("web").joinpath("index.html").read_text(encoding="utf-8")
    script = _INSTRUMENT
    for token, value in (("WIDTH", WIDTH), ("HEIGHT", HEIGHT), ("WARMUP_MS", WARMUP_S * 1000),
                         ("DURATION_MS", duration * 1000), ("LAUNCH_MS", launch_ms)):
        script = script.replace(token, str(value))
    html = page.replace("</body>", script + "</body>", 1).encode("utf-8")
    server = LiveServer(LiveGame("gather", tuning, {}, seed), port=0)

    class BenchHandler(server.httpd.RequestHandlerClass):
        def handle(self):
            try:
                super().handle()
            except (BrokenPipeError, ConnectionResetError):
                # Closing headless Chromium cancels the client's outstanding state poll.
                pass

        def do_GET(self):
            if self.path == "/__bench":
                self._send(200, html, "text/html; charset=utf-8")
            else:
                super().do_GET()

        def do_POST(self):
            if self.path != "/__bench_result":
                return super().do_POST()
            try:
                data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if not isinstance(data, dict):
                    raise ValueError("expected a benchmark result object")
                if data.get("error"):
                    result = RuntimeError(data["error"])
                else:
                    result = summarize_frames(data["intervals"], data["load_ms"])
            except (KeyError, TypeError, ValueError):
                self._send(400, b"{}")
                return
            self._send(200, b"{}")
            results.put(result)

    server.httpd.RequestHandlerClass = BenchHandler
    return server


def _measure_browser(executable, tuning, seed, duration):
    results = SimpleQueue()
    server = _browser_server(tuning, seed, duration, time.time() * 1000, results)
    server.start()
    try:
        with tempfile.TemporaryDirectory(prefix="chonoi-browser-", ignore_cleanup_errors=True) as profile:
            command = [str(executable), "--headless=new", "--no-first-run", "--no-default-browser-check",
                       f"--user-data-dir={profile}", f"--window-size={WIDTH},{HEIGHT}",
                       "--force-device-scale-factor=1", "--hide-scrollbars", server.url + "__bench"]
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                deadline = time.perf_counter() + WARMUP_S + duration + 12
                while process.poll() is None and time.perf_counter() < deadline:
                    try:
                        result = results.get(timeout=0.1)
                        if isinstance(result, RuntimeError):
                            raise result
                        return result
                    except Empty:
                        continue
                raise RuntimeError("browser exited or did not report frames")
            finally:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    finally:
        server.stop()


class _GatherRaster:
    """Draw the live snapshot to an RGB framebuffer without a display or third-party libraries."""

    def __init__(self, bounds):
        self.bounds = bounds
        self.surface = HEIGHT // 5
        self.background = (bytes((143, 202, 216)) * WIDTH * self.surface
                           + bytes((30, 97, 111)) * WIDTH * (HEIGHT - self.surface))
        self.pixels = bytearray(self.background)

    def _block(self, x, y, width, height, color):
        left, right = max(0, x), min(WIDTH, x + width)
        if left >= right:
            return
        row = color * (right - left)
        for line in range(max(0, y), min(HEIGHT, y + height)):
            start = (line * WIDTH + left) * 3
            self.pixels[start:start + len(row)] = row

    def draw(self, snapshot):
        self.pixels[:] = self.background
        left, right = self.bounds["x"]
        shallow, deep = self.bounds["d"]
        for entities, color, size in (
            (snapshot["nodes"], b"\xaf\xd9\x54", 7),
            (snapshot["fish"], b"\xff\xc0\x6e", 10),
            (snapshot["monsters"], b"\x73\x41\xac", 19),
            ((snapshot["player"],), b"\xff\xec\xca", 12),
        ):
            for entity in entities:
                x, depth = entity["pos"]
                px = int((x - left) / (right - left) * (WIDTH - 1))
                py = self.surface + int((depth - shallow) / (deep - shallow) * (HEIGHT - self.surface - 1))
                self._block(px - size, py - size // 2, size * 2, size, color)
        player = snapshot["player"]
        oxygen = int(220 * player["oxygen_ticks"] / player["oxygen_max_ticks"])
        self._block(20, 20, 220, 16, b"\x30\x39\x40")
        self._block(20, 20, oxygen, 16, b"\x35\xda\xee")
        for index, item in enumerate(snapshot["hold"]):
            self._block(20 + index * 12, 48, 10, int(item["fresh"] / 10), b"\xe3\xcf\x85")


def _measure_software(tuning, seed, duration):
    launch = time.perf_counter()
    session = Session("gather", tuning, {}, seed)
    raster = _GatherRaster(tuning["gather"]["bounds"])
    tick_hz = tuning["tick_hz"]
    idle = InputState((0, 0), {}, set())
    raster.draw(session.snapshot())
    first = previous = time.perf_counter()
    warm_until = first + WARMUP_S
    deadline = first
    start = None
    intervals = []
    while start is None or previous - start < duration:
        deadline = max(deadline + 1 / tick_hz, previous)
        time.sleep(max(0, deadline - time.perf_counter()))
        target_tick = int((time.perf_counter() - first) * tick_hz)
        while session.tick < target_tick and not session.done:
            session.step(idle)
        if session.done:
            raise RuntimeError("gather scene stopped before the benchmark ended")
        raster.draw(session.snapshot())
        now = time.perf_counter()
        if start is not None:
            intervals.append(now - previous)
        elif now >= warm_until:
            start = now
        previous = now
    return summarize_frames(intervals, (first - launch) * 1000)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="chonoi.bench", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--renderer", choices=("auto", "browser", "software"), default="auto")
    args = parser.parse_args(argv)
    if not math.isfinite(args.duration) or args.duration <= 0:
        parser.error("--duration must be positive and finite")
    try:
        tuning = load_contract()["tuning"]
        if args.duration + WARMUP_S >= tuning["gather"]["duration_s"]:
            parser.error("--duration and warmup must fit within the default gather shift")
        report = None
        if args.renderer != "software":
            for executable in _browser_paths():
                try:
                    report = _measure_browser(executable, tuning, args.seed, args.duration)
                except (OSError, RuntimeError) as error:
                    print(f"{executable.name}: {error}", file=sys.stderr)
                    continue
                print(f"renderer: {executable.name} (headless Chromium canvas)", file=sys.stderr)
                break
        if report is None:
            if args.renderer == "browser":
                raise RuntimeError("no working Chromium browser")
            report = _measure_software(tuning, args.seed, args.duration)
            print("renderer: software RGB framebuffer", file=sys.stderr)
        write_report(args.out, report)
    except (BadInput, OSError, RuntimeError, ValueError) as error:
        print(f"benchmark: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
