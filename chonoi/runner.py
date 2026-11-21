"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt
hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import inspect
import math
import os
import tempfile

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        kwargs = {}
        if "item_ids" in inspect.signature(GatherSim.__init__).parameters:
            kwargs["item_ids"] = ids
        return GatherSim(tuning, scenario, streams, ids, **kwargs)
    if mode == "day":
        return DaySim(tuning, scenario, streams, ids, days=days)
    kwargs = {"inventory": inventory}
    if "item_ids" in inspect.signature(QuanSim.__init__).parameters:
        kwargs["item_ids"] = ids
    return QuanSim(tuning, scenario, streams, ids, **kwargs)


def _common(sim, tick, sim_tick, phase_tick, tuning, state):
    mult = tuning["score"]["reputation_multiplier"]
    row = {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }
    if sim.mode == "day":
        row["day"] = sim.day
        row["day_plan"] = sim.day_plan
        row["upgrades"] = dict(sim.upgrades)
        row["active_upgrades"] = dict(sim.active_upgrades)
    return row


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days=days)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def _state(self) -> str:
        if self.sim.done:
            return "finished"
        return "paused" if self.paused else "playing"

    def snapshot(self) -> dict:
        phase_tick = getattr(self.sim, "phase_tick", self.sim_tick)
        s = _common(self.sim, self.tick, self.sim_tick, phase_tick, self.tuning, self._state())
        s.update(self.sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        pre = []
        day_before = getattr(self.sim, "day", None)
        phase_before = self.sim.phase
        if inp.pressed("pause"):
            if not self.paused:
                self.paused = True
                self.tick += 1
                row = {"type": "event", "tick": self.tick, "phase": phase_before, "name": "paused", "data": {}}
                if self.mode == "day":
                    row["day"] = day_before
                return [row]
            self.paused = False
            pre.append((day_before, phase_before, "resumed", {}))
        elif self.paused:
            self.tick += 1
            return []

        raw_events = self.sim.step(inp)
        self.sim_tick += 1
        self.tick += 1
        out = []
        for ev_day, ev_phase, name, data in pre:
            row = {"type": "event", "tick": self.tick, "phase": ev_phase, "name": name, "data": data}
            if self.mode == "day":
                row["day"] = ev_day
            out.append(row)
        for item in raw_events:
            if self.mode == "day":
                ev_day, ev_phase, name, data = item
                out.append({"type": "event", "tick": self.tick, "phase": ev_phase, "day": ev_day, "name": name, "data": data})
            else:
                name, data = item
                out.append({"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": name, "data": data})
        return out

    def end_row(self) -> dict:
        sim = self.sim
        score = _common(sim, self.tick, self.sim_tick, getattr(sim, "phase_tick", self.sim_tick), self.tuning, "")["score"]
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
               "state": "finished" if sim.done else ("paused" if self.paused else "playing"),
               "reason": sim.reason if sim.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}
        if self.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None, days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days=days)
    player = InputPlayer(frames)
    out_dir = os.path.dirname(os.path.abspath(out_path))
    fd, tmp_path = tempfile.mkstemp(prefix=".out-", suffix=".tmp", dir=out_dir)
    os.close(fd)
    w = JsonlWriter(tmp_path)
    try:
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
        w.close()
        os.replace(tmp_path, out_path)
    except BaseException:
        w.close()
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
