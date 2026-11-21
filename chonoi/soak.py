"""Công cụ soak headless nhiều ngày liên tiếp (`soak_cmd`, Contract v1.3).

Chạy:
    python3 -m chonoi.soak --seed <int> --days <N> --out <soak.json>

Mã thoát: 0 bình thường; 2 tham số/đầu vào sai (kiểm TRƯỚC khi ghi đầu ra); 1 lỗi chạy/ghi.
"""

import argparse
from collections import Counter
import json
import math
import os
import sys
import tempfile
import time

from .contract import load_contract
from .errors import BadInput
from .ids import id_key
from .inputs import InputState
from .runner import Session


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def _int(name):
    def conv(s):
        try:
            return int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên")
    return conv


def _move_toward(pos, target) -> tuple[float, float]:
    dx = float(target[0]) - float(pos[0])
    dy = float(target[1]) - float(pos[1])
    dist = math.hypot(dx, dy)
    if dist <= 1e-6:
        return (0.0, 0.0)
    return (dx / dist, dy / dist)


class _SoakBot:
    """Bot tất định điều khiển xuyên pha gather -> quan -> shop không dùng RNG/đồng hồ."""

    def decide(self, sess: Session) -> InputState:
        day_sim = sess.sim
        phase = day_sim.phase
        sub = day_sim.sub
        if phase == "gather":
            return self._decide_gather(sub, day_sim.day_plan)
        if phase == "quan":
            return self._decide_quan(sub)
        if phase == "shop":
            return self._decide_shop(sub)
        return InputState((0.0, 0.0), set(), set())

    def _decide_gather(self, sim, day_plan: dict) -> InputState:
        t = sim.t
        dock_pos = t["dock_pos"]
        free = int(t["hold_capacity"]) - len(sim.hold)
        day_ing = day_plan.get("ingredients", {}) if isinstance(day_plan, dict) else {}
        have = Counter(it["kind"] for it in sim.hold)
        needed = {k: max(0, int(cnt) - have[k]) for k, cnt in day_ing.items()}

        # An toàn oxy / máu / thời gian / giỏ đầy / đủ nguyên liệu
        if not sim._at_surface() and sim.oxygen_ticks < max(240, int(0.3 * sim.oxygen_max)):
            return InputState((0.0, -1.0), set(), set())

        if not sim._at_surface():
            for m in sim.monsters:
                if math.dist(sim.pos, m["pos"]) < 7.0 and sim.pos[1] >= 8.0:
                    return InputState((0.0, -1.0), set(), set())

        need_more = any(v > 0 for v in needed.values())
        should_dock = (
            sim.hp <= 1
            or free <= 0
            or sim.phase_tick >= 4200
            or sim.time_left_ticks <= 2400
            or (bool(day_ing) and not need_more)
        )

        target = None
        if not should_dock:
            target = self._pick_gather_target(sim, needed, free)
            if target is None:
                should_dock = True

        if should_dock:
            if sim._in_dock():
                return InputState((0.0, 0.0), {"interact"}, {"interact"})
            return InputState(_move_toward(sim.pos, dock_pos), set(), set())

        kind_type, obj = target
        dist = math.dist(sim.pos, obj["pos"])
        if kind_type == "node":
            if dist <= float(t["interact_radius"]) * 0.9 and sim._at_surface() and not sim._in_dock():
                return InputState((0.0, 0.0), {"interact"}, {"interact"})
            return InputState(_move_toward(sim.pos, obj["pos"]), set(), set())

        # kind_type == "fish"
        if dist <= float(t["catch_radius"]) * 0.9 and not sim._at_surface() and sim.catch_cd_ticks == 0:
            return InputState(_move_toward(sim.pos, obj["pos"]), {"catch"}, {"catch"})
        return InputState(_move_toward(sim.pos, obj["pos"]), set(), set())

    def _pick_gather_target(self, sim, needed: dict, free: int):
        t = sim.t
        node_yield = int(t["node_yield"])
        fish_yield = t["fish_yield"]
        candidates = []

        if node_yield <= free:
            for n in sim.nodes:
                if n["regrow_ticks"] == 0:
                    prio = 0 if needed.get(n["kind"], 0) > 0 else 1
                    candidates.append((prio, math.dist(sim.pos, n["pos"]), 0, id_key(n["id"]), "node", n))

        for f in sim.fish:
            if int(fish_yield.get(f["kind"], 99)) > free:
                continue
            if any(math.dist(f["pos"], m["pos"]) < 6.0 for m in sim.monsters):
                continue
            prio = 0 if needed.get(f["kind"], 0) > 0 else 1
            candidates.append((prio, math.dist(sim.pos, f["pos"]), 1, id_key(f["id"]), "fish", f))

        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
        _, _, _, _, kind_type, obj = candidates[0]
        return kind_type, obj

    def _decide_quan(self, sim) -> InputState:
        radius = float(sim.t["interact_radius"])
        if isinstance(sim.hand, dict):
            order_id = sim.hand.get("order_id")
            customer = next(
                (c for c in sim.customers if c["id"] == order_id and c["state"] == "waiting"),
                None,
            )
            if customer is not None:
                table = next((tb for tb in sim.tables if tb["id"] == customer["table_id"]), None)
                if table is not None:
                    if math.dist(sim.pos, table["pos"]) <= radius * 0.9:
                        return InputState((0.0, 0.0), {"interact"}, {"interact"})
                    return InputState(_move_toward(sim.pos, table["pos"]), set(), set())

        ready_stoves = [s for s in sim.stoves if s["state"] == "ready"]
        if ready_stoves:
            stove = min(ready_stoves, key=lambda s: (math.dist(sim.pos, s["pos"]), id_key(s["id"])))
            if math.dist(sim.pos, stove["pos"]) <= radius * 0.9:
                return InputState((0.0, 0.0), {"interact"}, {"interact"})
            return InputState(_move_toward(sim.pos, stove["pos"]), set(), set())

        if sim._pick_reserved_order() is not None:
            idle_stoves = [s for s in sim.stoves if s["state"] == "idle"]
            if idle_stoves:
                stove = min(idle_stoves, key=lambda s: (math.dist(sim.pos, s["pos"]), id_key(s["id"])))
                if math.dist(sim.pos, stove["pos"]) <= radius * 0.9:
                    return InputState((0.0, 0.0), {"interact"}, {"interact"})
                return InputState(_move_toward(sim.pos, stove["pos"]), set(), set())

        wait_pos = [3.5, 7.5]
        if math.dist(sim.pos, wait_pos) > 0.5:
            return InputState(_move_toward(sim.pos, wait_pos), set(), set())
        return InputState((0.0, 0.0), set(), set())

    def _decide_shop(self, sim) -> InputState:
        for kind in ("oxygen", "hp"):
            tiers = sim._tiers_for(kind)
            lvl = int(sim.upgrades.get(kind, 0))
            if lvl < len(tiers):
                tier = tiers[lvl]
                price = int(tier.get("price", tier.get("cost", 0)))
                if sim.money >= price:
                    return InputState((0.0, 0.0), set(), set(), buy=kind)
        return InputState((0.0, 0.0), {"shop_done"}, {"shop_done"})


def run_soak(tuning: dict, seed: int, days: int) -> dict:
    """Chạy mô phỏng `days` Ngày trong một tiến trình với bot tất định; trả payload JSON soak."""
    if isinstance(days, bool) or not isinstance(days, int) or days < 1:
        raise BadInput("--days phải là số nguyên >= 1")

    t0 = time.perf_counter()
    sess = Session("day", tuning, {}, seed, days=days)
    bot = _SoakBot()
    results = []
    crashes = 0

    g_ticks = int(round(tuning["gather"]["duration_s"] * tuning["tick_hz"]))
    q_ticks = int(round(tuning["quan"]["duration_s"] * tuning["tick_hz"]))
    s_ticks = int(tuning["shop"]["max_ticks"])
    max_ticks = days * (g_ticks + q_ticks + s_ticks) + 100

    try:
        while not sess.done and sess.tick < max_ticks:
            inp = bot.decide(sess)
            events = sess.step(inp)
            for ev in events:
                if ev.get("name") == "shop_end":
                    snap = sess.snapshot()
                    results.append({
                        "day": ev["day"],
                        "earned": sess.sim.earned,
                        "reputation": round(sess.sim.reputation, 3),
                        "score": snap["score"],
                    })
    except Exception:
        crashes += 1

    elapsed = time.perf_counter() - t0
    return {
        "days": days,
        "days_completed": sess.sim.days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": round(elapsed, 3),
    }


def _write_atomic_json(out_path: str, payload: dict):
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".soak-", suffix=".tmp", dir=out_dir)
    os.close(fd)
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_path, out_path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.soak")
    p.add_argument("--seed", required=True, type=_int("seed"))
    p.add_argument("--days", required=True, type=_int("days"))
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        if a.days < 1:
            raise BadInput("--days phải >= 1")
        if not isinstance(a.out, str) or not a.out.strip():
            raise BadInput("--out không hợp lệ")
        contract = load_contract()
        tuning = contract["tuning"]
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2

    try:
        payload = run_soak(tuning, a.seed, a.days)
        _write_atomic_json(a.out, payload)
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0 if payload["crashes"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
