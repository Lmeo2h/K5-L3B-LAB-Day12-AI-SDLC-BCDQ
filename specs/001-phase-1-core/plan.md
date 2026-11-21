# Implementation Plan: Quán Ăn Chợ Nổi — Phase 1 Core

**Branch**: `001-phase-1-core` | **Date**: 2026-11-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-phase-1-core/spec.md`

## Summary

Implement Phase 1 Core gameplay rules for **Quán Ăn Chợ Nổi** on top of the existing Python 3 starter framework (`chonoi/`), covering both 60 Hz deterministic simulation modes — `gather` (`chonoi/sim/gather.py`) and `quan` (`chonoi/sim/quan.py`) — plus rule-level scenario conflict validation (`chonoi/scenario.py`). Work is partitioned into 4 independent vertical slices (one per team member: `duyhale95`, `missher03`, `Limdim1604`, `Lmeo2h`), each verified with test-first `unittest` suites and black-box `chonoi.headless` JSONL/inventory runs, while sharing `chonoi.runner.Session` with `chonoi.live` for browser playtesting.

## Technical Context

**Language/Version**: Python 3 (standard library only; CI targets Python 3.12 in `.github/workflows/ci.yml`).

**Primary Dependencies**: Python 3 standard library only (`json`, `math`, `random`, `argparse`, `http.server`, `threading`, `tempfile`, `os`, `sys`, `unittest`, `subprocess`). Zero external third-party packages.

**Storage**: Local JSON/JSONL files — configuration & tuning in `game.contract.json`, input scenarios (`--scenario`), input traces (`--inputs`), inventory interchange (`--inventory` / `--inventory-out` using `{"items": {...}}` via atomic `chonoi.inventory.write_inventory`), and simulation event/snapshot output (`JsonlWriter` in `chonoi/jsonl.py`).

**Testing**: Python `unittest` (`PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` on Linux/CI; `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v` on Windows PowerShell). Includes existing black-box contract tests (`tests/test_smoke_p1.py`), starter unit tests (`tests/test_python_starter_units.py`), live server smoke tests (`tests/test_live.py`), team check (`tests/test_team_check.py`), and 4 new per-slice test modules (`tests/test_gather_survival.py`, `tests/test_gather_harvest.py`, `tests/test_quan_customers.py`, `tests/test_quan_service.py`).

**Target Platform**: Cross-platform CLI (`python3 -m chonoi.headless`), local HTTP browser preview (`python3 -m chonoi.live` + `chonoi/web/index.html`), and GitHub Actions (`ubuntu-latest`).

**Project Type**: Single-project deterministic 2D game simulation engine with shared `chonoi.runner.Session` loop for headless grading/testing and live browser playtesting.

**Performance Goals**: 60 Hz deterministic fixed-timestep simulation (`tuning.tick_hz = 60` in `game.contract.json`), completing full 180-second shifts (10,800 ticks per mode) cleanly in headless mode without lag or real-time clock coupling.

**Constraints**:
- **Strict Determinism**: Same seed + inputs + scenario MUST produce byte-identical JSONL and inventory output. All randomness MUST use `chonoi.rng.Streams` (never global `random` or wall-clock time).
- **Zero Hard-Coding**: All gameplay constants MUST be read from `tuning` in `game.contract.json` (`gather.*`, `quan.*`, `menu.*`, `score.*`).
- **Deterministic IDs & Ordering**: Entity collections sorted via `chonoi.ids.sort_by_id`; new entity IDs allocated via `chonoi.ids.IdAllocator`.
- **Fail-Fast Validation**: Invalid CLI flags, inputs, inventory, or scenario conflicts MUST raise `BadInput` and exit with code `2` before any output file is written.
- **Framework & Contract Lock**: Do NOT alter `game.contract.json` tuning/schema or `docs/contracts/` without team consensus; avoid editing starter plumbing (`chonoi/{headless,inputs,contract,rng,ids,jsonl,inventory,runner,live}.py`, `chonoi/web/`) unless documented and agreed.
- **Creative Extras**: Optional visual/audio/UX enhancements MUST remain disabled in `chonoi.headless`.

**Scale/Scope**: Phase 1 Core across 4 team members (`team_size: 4`), delivering all 4 vertical slices, verification evidence, and git tag `phase-1` before the 1:00 checkpoint.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1. **Determinism & Seeded RNG**: All stochastic operations routed through `Streams(seed).get(stream_name)`; entity lists ordered by `ids.sort_by_id`; runtime IDs generated via `IdAllocator`. -> **PASS**.
2. **Data-Driven Tuning**: `GatherSim` and `QuanSim` read all numeric parameters strictly from `tuning` (`game.contract.json`) with zero hard-coded gameplay constants. -> **PASS**.
3. **Contract & Starter Frame Integrity**: `docs/contracts/`, `game.contract.json` tuning, and `chonoi` runner/IO modules remain intact; group logic resides in `chonoi/sim/gather.py`, `chonoi/sim/quan.py`, and rule-level checks in `chonoi/scenario.py`. -> **PASS**.
4. **Vertical Slice Isolation & Small PRs**: Phase 1 splits cleanly into 4 vertical slices (`US1`–`US4`), each with its own test file, feature branch, and focused PR. -> **PASS**.
5. **Honest Verification & Escalation**: Any unclear PRD-0 formula/rule is documented in `docs/clarify.md` for PO (`missher03`) instead of guessing; QA Lead (`Limdim1604`) maintains `docs/verification/phase-1.md` and `docs/proof/phase-1/`. -> **PASS**.

## Project Structure

### Documentation (this feature)

```text
specs/001-phase-1-core/
├── spec.md              # Phase 1 functional specification (US1–US4)
├── plan.md              # This file (technical plan & parallel integration strategy)
├── tasks.md             # Executable task list per vertical slice
└── prompts-phase-1.md   # Ready-to-run prompts per team member

docs/
├── plan/phase-1.md          # <= 1-page Phase 1 summary plan
├── verification/phase-1.md  # Traceability matrix & honest QA results
├── proof/phase-1/           # Headless/test logs & verification artifacts
├── clarify.md               # Open PRD-0 questions & PO decisions
├── standup.md               # Short phase sync notes
└── ai-usage-log.md          # Team AI usage log
```

### Source Code (repository root)

```text
chonoi/
├── __init__.py
├── contract.py              # Loads game.contract.json (starter frame)
├── errors.py                # BadInput -> exit code 2 (starter frame)
├── headless.py              # CLI entrypoint for automated grading (starter frame)
├── ids.py                   # id_key, sort_by_id, IdAllocator (starter frame)
├── inputs.py                # InputPlayer, LiveInputs, load_frames (starter frame)
├── inventory.py             # read_inventory, write_inventory, hold_to_items (starter frame)
├── jsonl.py                 # Deterministic JsonlWriter (starter frame)
├── live.py                  # Browser playtest server sharing Session (starter frame)
├── rng.py                   # Seeded Streams RNG (starter frame)
├── runner.py                # Shared 60 Hz Session & run() loop (starter frame)
├── scenario.py              # Scenario loader + Slice 3 rule-level validation
├── sim/
│   ├── __init__.py
│   ├── ramp.py              # Velocity ramping helper (starter frame)
│   ├── gather.py            # Slice 1 (survival/LIFO) + Slice 2 (harvest/catch)
│   └── quan.py              # Slice 3 (customers/reserve/patience) + Slice 4 (cook/serve/pay)
└── web/
    └── index.html           # Starter canvas preview client

tests/
├── helpers.py               # Black-box headless test helpers
├── test_smoke_p1.py         # Public black-box contract smoke tests
├── test_python_starter_units.py
├── test_live.py
├── test_team_check.py
├── test_gather_survival.py  # Slice 1 unit + headless tests (duyhale95)
├── test_gather_harvest.py   # Slice 2 unit + headless tests (missher03)
├── test_quan_customers.py   # Slice 3 unit + headless tests (Limdim1604)
└── test_quan_service.py     # Slice 4 unit + headless tests (Lmeo2h)

tools/
└── check_team.py            # TEAM.md & team_size validator
```

**Structure Decision**: Keep the existing single-project Python 3 structure (`chonoi/` + `tests/` + `docs/` + `specs/001-phase-1-core/`). Both `chonoi.headless` and `chonoi.live` execute the exact same `GatherSim` and `QuanSim` classes through `chonoi.runner.Session`, eliminating duplicate simulation code.

## Parallel Integration Strategy

Because two pairs share simulation files (`gather.py` for Slices 1 & 2; `quan.py` for Slices 3 & 4), merge conflicts are prevented via **distinct helper methods**, **isolated test files**, and **sequential PR rebase/merge order**:

### 1. `chonoi/sim/gather.py` — Slices 1 & 2 Partitioning
- **Shared Invariant**: `self.hold` is a Python `list` ordered from oldest to newest (`self.hold[-1]` is newest for LIFO removal), bounded by `self.t["hold_capacity"]`.
- **Slice 1 (`duyhale95` — `feat/p1-s1-gather-survival`)**:
  - Owns `tests/test_gather_survival.py`.
  - Adds private helpers in `GatherSim`: `_step_region_transition(was_surface, events)` (emits `dive` / `surface` with `pos`), `_step_oxygen_and_choke(events)` (refills `oxygen_refill_per_tick` at surface, drains 1/tick underwater, emits `oxygen_empty` on `>0 -> 0`, counts `zero_oxy_ticks` up to `choke_interval_ticks` to subtract 1 HP and emit `choke`, handles HP `<= 0` -> clears `self.hold`, emits `faint`, calls `self._finish("fainted", events)`), and LIFO helper `_push_hold(kind)` / `_clear_hold()`.
  - Only modifies step block `2` in `GatherSim.step()` (capturing `was_surface = self._at_surface()` before `self._move(inp)`).
- **Slice 2 (`missher03` — `feat/p1-s2-gather-harvest`)**:
  - Owns `tests/test_gather_harvest.py`.
  - Adds private helpers in `GatherSim`: `_try_gather_node(events)` (only when `self._at_surface()`; selects nearest `ready` node within `interact_radius`, tie-breaking by `id_key`; checks `hold_capacity` -> appends `node_yield` items / `hold_full`, sets `regrow_ticks = int(round(self.t["regrow_s"] * TICK))`, emits `gather`) and `_try_catch_fish(events)` (only when `not self._at_surface()` and `self.catch_cd_ticks == 0`; selects target fish within `catch_radius` per PRD-0 tie-break, checks `hold_capacity` -> appends `fish_yield[kind]` / `hold_full`, sets `catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))`, emits `fish_caught`).
  - Only modifies step blocks `3` (after existing `if self._in_dock():`) and `4` in `GatherSim.step()`.
- **Merge Order**: Merge Slice 1 PR first into `main`; Slice 2 rebases onto `main` (reusing `_push_hold` or `len(self.hold) >= self.t["hold_capacity"]`) and opens PR cleanly with zero overlapping helper edits.

### 2. `chonoi/sim/quan.py` & `chonoi/scenario.py` — Slices 3 & 4 Partitioning
- **Shared Customer State Contract**: Both slices agree on the customer dictionary fields in `self.customers` (e.g., `id`, `table_id`, `reserved` from starter `chonoi/sim/quan.py`, plus `state`, `dish_id`, `patience_ticks_left`, `eat_ticks_left`, price/tip fields confirmed against PRD-0 in `docs/clarify.md`) and stove dictionary fields (`id`, `pos`, `state`, `dish`, `cook_ticks_left`, `ready_ticks`). Any field names or payloads not present in starter `quan.py` / `scenario.py` are verified against PRD-0 and recorded in `docs/clarify.md` before coding.
- **Slice 3 (`Limdim1604` — `feat/p1-s3-quan-customers`)**:
  - Owns `chonoi/scenario.py` (rule-level validation in `_validate_quan`: ingredient reservations vs `stock`, `assigned`/waiting customer dish validity, `eating` customer fields, table/stove/customer consistency) and `tests/test_quan_customers.py`.
  - Adds private helpers in `QuanSim`: `_init_customer_reservations()`, `_available_stock()`, `_pick_cookable_dish()`, `_step_customer_patience(events)` (decrements patience, handles `customer_left`, applies `left_reputation_delta` clamped to `[reputation_min, reputation_max]`, releases `reserved`), and `_spawn_customer_if_due(events)` (`first_customer_tick`, `customer_interval_s`, selects free table & cookable dish or emits `no_dish`).
- **Slice 4 (`Lmeo2h` — `feat/p1-s4-quan-service`)**:
  - Owns `tests/test_quan_service.py` and `phase-1` integration/tagging.
  - Adds private helpers in `QuanSim`: `_step_stoves(events)` (decrements `cook_ticks_left`, transitions to `ready`, emits `dish_ready`), `_step_eating_customers(events)` (decrements `eat_ticks_left`, computes `paid` + tip via `tip_min_patience_ratio`/`tip_rate` + `tip_reputation`, updates `money`/`earned`/`shift_earned`/`reputation`, removes customer), and `_handle_interact(events)` (at most one interact per tick within `interact_radius`, ranked by `(distance, 0 if stove else 1, id_key(id))`, emitting `cook_started`, `dish_picked`, `served`).
- **Merge Order**: Merge Slice 3 PR first so `QuanSim` customer initialization, `reserved` stock accounting, and `scenario.py` validation are on `main`; Slice 4 rebases onto `main` and wires stove/service/payment into `QuanSim.step()`.

### 3. Shared Guardrails
- Never edit another slice's test file (`tests/test_*.py`).
- Before opening any PR, run `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v` and `python -m chonoi.headless` verification.
- Integrator (`Lmeo2h`) runs full cross-mode test (`gather --inventory-out` -> `quan --inventory`) and deterministic byte-comparison on `main` before Release (`duyhale95`) / Integrator tags `phase-1`.

## Complexity Tracking

No Constitution Check violations. No extra abstractions, external dependencies, or multi-project splits are required for Phase 1.
