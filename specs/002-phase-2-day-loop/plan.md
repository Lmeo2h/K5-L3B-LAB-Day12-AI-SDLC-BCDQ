# Implementation Plan: Quán Ăn Chợ Nổi — Phase 2 (Một ngày ở chợ nổi)

**Branch**: `002-phase-2-day-loop` | **Date**: 2026-11-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-phase-2-day-loop/spec.md` (TICKET-02, Test Contract v1.1, 55-minute sprint `1:00–1:55`, target git tag `phase-2`)

## Summary

Implement **Phase 2 — Một ngày ở chợ nổi (TICKET-02)** on top of the Phase 1 core simulation, upgrading the project to **Test Contract v1.1** within a strict **55-minute (`1:00–1:55`)** sprint. Phase 2 adds:
1. **Contract v1.1 + `gather` Fish Swimming/Spawning & Choke-on-Zero** (`duyhale95`): 6 ingredients (`ca_keo`, `keo_neo`), N5/N6 surface nodes, 8 initial fish schools with deterministic swimming/120-tick turns/boundary reflection and 360-tick spawning up to `fish_max: 12`, plus updated underwater choke cadence starting on the step oxygen reaches `0`.
2. **`gather` Crocodile Hazards (`M1`/`M2`)** (`missher03`): `chonoi/sim/monsters.py` state machine (`patrol`, `chase`, `recoil`), collision hit (`-1` HP, `invuln_ticks = 90`, LIFO `floor(len(hold) * 0.5)` drop, `monster_hit`), `faint(cause="monster")`, and `gather.monsters[]` validation.
3. **`quan` v1.1 Scale-Up + 2 Team Skills + QA** (`Limdim1604`): 2 stoves (`B1`, `B2`), 4 tables (`T1`–`T4`), 6 dishes, `day_plan` dish filtering in `day` mode, v1.1 scenario validation in `chonoi/scenario.py`, 2 reusable team skills in `.agents/skills/`, P1 regression checks, and `docs/verification/phase-2.md` / `docs/proof/phase-2/`.
4. **Multi-Day Loop (`--mode day --days 1..5`), `ShopSim`, `pause` & Live Web UI/HUD v1.1** (`Lmeo2h`): `DaySim` (`chonoi/sim/day.py`), `ShopSim` (`chonoi/sim/shop.py`), outer `pause` wrapper across all 3 modes (`gather`, `quan`, `day`), v1.1 snapshot/event envelope in `chonoi/{runner,headless,live}.py`, full browser UI/HUD in `chonoi/web/index.html`, Phase 2 quick retro in `docs/retro.md`, and release tag `phase-2`.

## Technical Context

**Language/Version**: Python 3 (standard library only; CI targets Python 3.12 in `.github/workflows/ci.yml`) + vanilla HTML5 Canvas / ES6 JS in `chonoi/web/index.html`.

**Primary Dependencies**: Python 3 standard library only (`json`, `math`, `random`, `argparse`, `http.server`, `threading`, `tempfile`, `os`, `sys`, `unittest`, `subprocess`, `time`). Zero external third-party packages.

**Storage**: Local JSON/JSONL files — `game.contract.json` (`contract_version: "1.1"`), `--scenario`, `--inputs`, `--inventory` / `--inventory-out` (`{"items": {...}}` via `chonoi/inventory.py`), and `JsonlWriter` output (`chonoi/jsonl.py`).

**Testing**: Python `unittest` (`PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` on Linux/CI; `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v` on Windows PowerShell). Existing P1 tests (`test_smoke_p1.py`, `test_python_starter_units.py`, `test_live.py`, `test_team_check.py`, `test_gather_survival.py`, `test_gather_harvest.py`, `test_quan_customers.py`, `test_quan_service.py`) plus 4 new Phase 2 test suites:
- `tests/test_gather_fish_v11.py` (Slice 1 — `duyhale95`)
- `tests/test_gather_monsters.py` (Slice 2 — `missher03`)
- `tests/test_quan_v11.py` (Slice 3 — `Limdim1604`)
- `tests/test_day_shop_pause.py` (Slice 4 — `Lmeo2h`)

**Target Platform**: Cross-platform CLI (`python3 -m chonoi.headless --mode gather|quan|day`), local browser preview (`python3 -m chonoi.live --mode gather|quan|day` + `chonoi/web/index.html` at `1280x720`), and GitHub Actions (`ubuntu-latest`).

**Project Type**: Single-project deterministic 60 Hz game simulation engine with shared `chonoi.runner.Session` driving both `chonoi.headless` and `chonoi.live`.

**Performance Goals**:
- `60 Hz` deterministic fixed-timestep simulation (`tick_hz: 60`).
- **Headless speed**: Full single day (`22,200` unpaused ticks = `10,800` gather + `10,800` quan + `600` shop) MUST complete in `<= 20 seconds` under `chonoi.headless`.
- **Live UI framerate**: `chonoi/web/index.html` MUST render smoothly at `>= 30 FPS` at `1280x720` with sans-serif HUD/text `>= 18px`.

**Constraints**:
- **Strict Determinism**: Identical `--seed`, `--inputs`, `--scenario`, `--inventory`, and `--days` MUST produce byte-identical JSONL and inventory files. All randomness MUST route through `chonoi.rng.Streams` (never global `random` or system clock).
- **Zero Hard-Coding**: All v1.1 constants (fish weights/bounds/speeds, crocodile patrol/chase/recoil/invuln, 6 dishes, 2 stoves, 4 tables, D1–D5 `day_plan`, shop tiers/prices) MUST be read from `game.contract.json` (`tuning.*`).
- **Deterministic IDs & Ordering**: All entity collections sorted via `chonoi.ids.sort_by_id`; spawned fish IDs (`F7`, `F8`, ... or `F9`, `F10`, ... after `F1`–`F8`) allocated via `chonoi.ids.IdAllocator` after reserving scenario/tuning IDs.
- **Fail-Fast Validation**: Invalid CLI flags, v1.1 inputs, scenarios, or `day_plan` conflicts MUST raise `BadInput` and exit with code `2` before creating any output files.
- **UI/Creative Separation**: All new screens, HUD warnings, and optional creative visual polish MUST live in `chonoi/web/` (and live display helpers) and remain completely disabled in `chonoi.headless`.
- **Deferred Extensions**: Optional extras (`Lao xua`, `Vợt hút cá`, `Rắn Hổ Mây`, `Cháy món`, `Chợ Chú Sáu`, `Sổ tay & Cá Hô`, `Settings`) are strictly out of core scope unless all Phase 2 DoD gates are green with spare time.

**Scale/Scope**: 4 team members (`team_size: 4`), 55-minute timebox (`1:00–1:55`), delivering all 4 vertical slices, 2 team skills in `.agents/skills/`, verification evidence in `docs/verification/phase-2.md` & `docs/proof/phase-2/`, Phase 2 quick retro in `docs/retro.md`, and git tag `phase-2`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1. **Determinism & Seeded RNG**: Fish turn decisions (`fish_turn_ticks: 120`), fish spawning (`fish_spawn_ticks: 360`), and `day_plan`-filtered dish choices use dedicated `Streams` channels so adding/removing features does not perturb unrelated RNG streams; all entities use `ids.sort_by_id` and `IdAllocator`. -> **PASS**.
2. **Single Source of Truth for Tuning**: All v1.1 tuning (`fish_speed`, `fish_max`, `fish_turn_ticks`, `fish_spawn_ticks`, `fish_spawn_weights`, `monsters`, `day_plan`, `shop`, 6 dishes, 2 stoves, 4 tables) resides in `game.contract.json` and is validated by `chonoi/contract.py`. -> **PASS**.
3. **Contract Upgrade Discipline**: Upgrading from Test Contract `1.0` to `1.1` is explicitly mandated by TICKET-02. Slice 1 (`duyhale95`) + Integrator (`Lmeo2h`) coordinate and land `T001`–`T004` first on `main` (within minutes `0–8`) and keep `docs/contracts/` / `AGENTS.md` updated. -> **PASS**.
4. **Vertical Slice Isolation & Small PRs**: Work splits into 4 non-overlapping Vertical Slices with separate test files (`tests/test_gather_fish_v11.py`, `tests/test_gather_monsters.py`, `tests/test_quan_v11.py`, `tests/test_day_shop_pause.py`) and clear module boundaries (`monsters.py`, `day.py`, `shop.py`). -> **PASS**.
5. **Honest Testing & Clarification Discipline**: If choke-on-zero changes P1 timing in `tests/test_gather_survival.py`, the P1 test update MUST record the exact rule change in the commit message rather than silently masking failures. Ambiguities go to `docs/clarify.md` for PO (`missher03`). QA (`Limdim1604`) records honest pass/fail results in `docs/verification/phase-2.md`. -> **PASS**.

## Project Structure

### Documentation & Team Artifacts

```text
.agents/skills/              # 2 team-authored skills created in Phase 2 (Limdim1604)
specs/002-phase-2-day-loop/
├── spec.md                  # Phase 2 functional specification (US1–US4)
├── plan.md                  # This file (architecture, file ownership, 4.5 order, 55m plan)
├── tasks.md                 # T001..T036 task breakdown across US1–US4
└── prompts-phase-2.md       # Copy-paste AI prompts per team member

docs/
├── plan/phase-2.md          # <= 1-page Phase 2 summary plan
├── verification/phase-2.md  # AC-P2-xx traceability matrix & honest QA results
├── proof/phase-2/           # Headless logs, perf benchmarks & regression proofs
├── clarify.md               # PO decisions on TICKET-02 edge cases
├── retro.md                 # Phase 2 quick retro (Điều tốt / Điều tệ / 1 hành động)
├── standup.md               # Phase 2 sync notes
└── ai-usage-log.md          # Team AI usage log
```

### Source Code (repository root)

```text
game.contract.json           # Upgraded to contract_version: "1.1" (T001, duyhale95)
chonoi/
├── contract.py              # v1.1 tuning & schema validation (T002, duyhale95)
├── inventory.py             # KINDS_P2 (6 ingredients: +ca_keo, +keo_neo) (T003, duyhale95)
├── inputs.py                # +pause, +shop_done, +buy string inputs (T004, duyhale95)
├── scenario.py              # v1.1 gather fish/monsters + quan/day validation (Slices 1, 2, 3)
├── runner.py                # --mode day, outer pause state, v1.1 envelope (Slice 4, Lmeo2h)
├── headless.py              # --mode day --days 1..5 CLI & validation (Slice 4, Lmeo2h)
├── live.py                  # LiveGame/LiveServer day mode, pause/shop controls (Slice 4, Lmeo2h)
├── sim/
│   ├── gather.py            # Fish swim/spawn + choke-on-zero (Slice 1) + monster hook (Slice 2)
│   ├── monsters.py          # Cá Sấu Năm Chèo M1/M2 AI, collision, recoil, LIFO drop (Slice 2)
│   ├── quan.py              # 2 stoves, 4 tables, 6 dishes, day_plan filtering (Slice 3)
│   ├── day.py               # DaySim multi-day loop D1–D5 & transitions (Slice 4)
│   └── shop.py              # ShopSim oxygen/hp L1–L2 upgrades & 600-tick timer (Slice 4)
└── web/
    └── index.html           # Menu, DayIntro, EveningIntro, DayResult, Summary, Pause, Shop, HUD v1.1

tests/
├── test_gather_fish_v11.py  # Slice 1 tests (duyhale95)
├── test_gather_monsters.py  # Slice 2 tests (missher03)
├── test_quan_v11.py         # Slice 3 tests (Limdim1604)
└── test_day_shop_pause.py   # Slice 4 tests (Lmeo2h)
```

**Structure Decision**: Extract crocodile logic into `chonoi/sim/monsters.py`, day orchestration into `chonoi/sim/day.py`, and shop state into `chonoi/sim/shop.py` rather than overloading `gather.py` or `runner.py`. This keeps PR diffs small (`<= ~400` lines per slice) and eliminates merge conflicts between parallel branches.

## File Ownership & Conflict-Avoidance Strategy

| Slice / Owner | Branch | Owned Files (Edit Allowed) | DO NOT TOUCH | Merge Order & Conflict Rule |
|---|---|---|---|---|
| **Foundation + Slice 1**<br>`duyhale95` (Hà Lê Duy) | `feat/p2-s1-contract-fish` | `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/inputs.py`, `chonoi/sim/gather.py` (fish swim/spawn, choke-on-zero), `chonoi/scenario.py` (gather fish fields), `tests/test_gather_fish_v11.py` (and documented choke timing update in `tests/test_gather_survival.py` if needed) | `chonoi/sim/monsters.py`, `chonoi/sim/quan.py`, `chonoi/sim/day.py`, `chonoi/sim/shop.py`, `chonoi/{runner,headless,live}.py`, `chonoi/web/`, `tests/test_gather_monsters.py`, `tests/test_quan_v11.py`, `tests/test_day_shop_pause.py` | **1st to land Contract v1.1 (`T001–T004`) on `main` within min 0–8**, then completes Slice 1 and merges **1st** among slices. |
| **Slice 2**<br>`missher03` (Nguyễn Văn Quốc) | `feat/p2-s2-crocodiles` | `chonoi/sim/monsters.py`, minimal monster hook in `chonoi/sim/gather.py` (step hook + snapshot `monsters[]`/`invuln_ticks`), `chonoi/scenario.py` (`gather.monsters[]`), `tests/test_gather_monsters.py`, `docs/clarify.md` | `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/inputs.py`, `chonoi/sim/quan.py`, `chonoi/sim/day.py`, `chonoi/sim/shop.py`, `chonoi/{runner,headless,live}.py`, `chonoi/web/`, other slices' `tests/test_*.py` | Writes `monsters.py` & `test_gather_monsters.py` in parallel; **rebases onto `main` after Slice 1 merges `gather.py`** before adding the hook & merging **2nd**. |
| **Slice 3**<br>`Limdim1604` (Nguyễn Thiên Bảo) | `feat/p2-s3-quan-v11-qa` | `chonoi/sim/quan.py`, `chonoi/scenario.py` (v1.1 `quan` & `day`/`day_plan` validation), `tests/test_quan_v11.py`, `.agents/skills/` (2 team skills), `docs/verification/phase-2.md`, `docs/proof/phase-2/` | `game.contract.json`, `chonoi/sim/{gather,monsters,day,shop}.py`, `chonoi/{runner,headless,live}.py`, `chonoi/web/`, other slices' `tests/test_*.py` | Runs parallel with Slices 1–2 (`quan.py` is unshared). **Rebases onto `main` after Slice 2** so `scenario.py` combines `gather.monsters[]` + `quan`/`day` rules cleanly; merges **3rd**. |
| **Slice 4**<br>`Lmeo2h` (Nguyễn Tấn Châu) | `feat/p2-s4-day-shop-ui` | `chonoi/sim/day.py`, `chonoi/sim/shop.py`, `chonoi/{runner,headless,live}.py`, `chonoi/web/index.html`, `tests/test_day_shop_pause.py`, `docs/retro.md` (Phase 2 quick), tag `phase-2` | `game.contract.json`, `chonoi/sim/{gather,monsters,quan}.py`, `chonoi/scenario.py`, other slices' `tests/test_*.py` | Develops `day.py`, `shop.py`, `web/index.html`, and `test_day_shop_pause.py` in parallel once `T001–T004` land; **rebases onto `main` after Slices 1–3** and merges **4th** before tagging `phase-2`. |

### Shared Boundary Rules
- **`chonoi/sim/gather.py`**: Slice 1 owns fish swim/spawn methods (`_step_fish_swim`, `_step_fish_spawn`) and `_step_oxygen_and_choke`; Slice 2 ONLY inserts calls to `chonoi.sim.monsters` helpers at the exact Section 4.5 step positions and includes `monsters[]` in `snapshot()`.
- **`chonoi/scenario.py`**: Slice 1 updates fish kinds/bounds/age_ticks in `_validate_gather`; Slice 2 adds `gather.monsters[]` in `_validate_gather`; Slice 3 adds `_validate_day` / v1.1 `_validate_quan` rules. Sequential rebase guarantees zero line overlap.
- **Test Isolation**: Each slice only modifies its own `tests/test_*.py` file (exception: Slice 1 may update `tests/test_gather_survival.py` ONLY if choke-on-zero alters P1 tick timing, with commit rationale).

## Processing Order Alignment (TICKET-02 Section 4.5)

All simulation layers MUST follow this exact deterministic per-tick order:

1. **Outer `Session` / `pause` Wrapper (`chonoi/runner.py`)**:
   - Check `inp.pressed("pause")` **FIRST** on every tick across `gather`, `quan`, and `day`.
   - If currently unpaused and `pause` edge fires -> set `paused = True`, increment outer `tick` only (freeze `sim_tick`, `phase_tick`, and all phase/sim timers), emit `paused`, ignore all other action edges and `buy` this tick, emit snapshot with `state: "paused"`.
   - While `paused == True` -> if `pause` edge fires, set `paused = False`, emit `resumed`, and **immediately execute the rest of this tick**; otherwise increment outer `tick` only and ignore all action edges / `buy`.
2. **Day Loop (`chonoi/sim/day.py`)**:
   - Transitions in exact order: `DayIntro` (auto/skip in headless as defined by contract; 4s/key in live) -> `gather` (`day_start` if new day, `day_plan`, `phase_start(phase="gather")`) -> `EveningIntro` -> `quan` (`phase_start(phase="quan")`, carries `gather` inventory or empty inventory on faint) -> `DayResult` -> `ShopSim` (`phase_start(phase="shop")`, `max_ticks: 600`) -> next day (`active_upgrades` applied, full oxygen/HP refill, hold & leftover stock cleared) or `days_completed` (`reason: "days_complete"`). Max `22,200` unpaused ticks/day.
3. **`gather` Tick Order (`chonoi/sim/gather.py` + `chonoi/sim/monsters.py`, TICKET-02 Section 4.5)**:
   1. Decrement timers (`time_left_ticks`, `invuln_ticks`, `catch_cd_ticks`, node `regrow_ticks` -> `node_regrown`), increment `phase_tick`.
   2. Player move + edge clamp; survival check (`dive`/`surface`, oxygen drain/refill, choke-on-zero every 60 ticks -> if `hp == 0`, `faint` + `gather_end("fainted")`, return).
   3. Crocodiles (`M1` Day 1+, `M2` Day 3+): update in `id` order (`recoil` 60 steps `2/60 m/step`, returning to `patrol` after 60 steps; `patrol` `1.0 m/s`; `chase` `3.0 m/s` when `d >= 10 & dist <= 10 m`, exit `dist > 16 m` or `d < 10`), then resolve at most 1 collision (`dist <= 1.5 m`, `d >= 10`, `invuln_ticks == 0`, nearest/`id_key` tie-break -> `-1` HP, drop `floor(len(hold)*0.5)` LIFO (`lost`), `invuln_ticks = 90`, `monster_hit`, monster enters `recoil`; if `hp == 0`, emit `faint(cause="monster")`, clear hold, `gather_end("fainted")` and skip rest of tick).
   4. `interact` (dock check first -> `docked`; else surface node gather).
   5. `catch` (underwater fish catch using fish positions **before** swimming).
   6. `time_left_ticks <= 0` -> `gather_end("time")`.
   7. **If time remains (`not self.done`)**: fish swim (`fish_turn_ticks: 120` seeded turn BEFORE moving; `fish_speed: 1.5`; increment `age_ticks`; reflect remaining distance on `fish_x` & species depth band; corner flips both), then fish spawn (`phase_tick = 360 * k, k >= 1`: max 1 school if `< fish_max (12)` and clearance `> 1 m`, normalized weights 40/30/30 over valid points, uniform point + seeded heading, emits `fish_spawned`, joins next step).
4. **`quan` Tick Order (`chonoi/sim/quan.py`)**:
   - Unchanged Phase 1 order (`patience`, `stoves` & `eat` timers, player move, `interact` 1 target `(dist, stove<table, id_key)`, finished eating `paid`, expired customers `customer_left`, spawn due at `120 + 900*k` to smallest empty table ID filtering menu by `day_plan.dishes` in `day` mode before checking available ingredients, closing settlement -> `quan_end`).
5. **`shop` Tick Order (`chonoi/sim/shop.py`)**:
   - Increment `phase_tick`, decrement `time_left_ticks` (`600` max).
   - Process `buy` string (`"oxygen"` or `"hp"`, L1->L2 upgrades) -> `bought` or `buy_failed(action, reason)`; deduct `money` only (preserve `earned`/`score`).
   - Process `shop_done` -> `shop_end(reason="done")`; else if `time_left_ticks <= 0` -> `shop_end(reason="time")`.

## 55-Minute Sprint Schedule (TICKET-02 Section 5)

| Window | Elapsed | Focus & Milestones | Owners |
|---|---|---|---|
| `1:00–1:08` | `0–8m` | **Contract v1.1 Foundation**: `duyhale95` lands `T001–T004` (`game.contract.json`, `contract.py`, `inventory.py`, `inputs.py`) on `main`; `missher03`, `Limdim1604`, `Lmeo2h` write Test-First skeletons & update `docs/clarify.md` in parallel. | `duyhale95` (leads), all |
| `1:08–1:20` | `8–20m` | **Core Parallel Build**: `gather` fish swim/spawn + choke-on-zero (Slice 1), `monsters.py` + `test_gather_monsters.py` (Slice 2), `quan.py` v1.1 + `scenario.py` (Slice 3), `day.py` + `shop.py` + `pause` (Slice 4). | All 4 in parallel |
| `1:20` | `20m` | **Integration Smoke Checkpoint (`T024`)**: Quick cross-slice smoke test (`gather + monsters + quan + day`), verify no contract drift, save interim proof in `docs/proof/phase-2/`. | `Limdim1604` + `Lmeo2h` |
| `1:20–1:40` | `20–40m` | **Complete Slices, UI & Skills**: Finish `chonoi/web/index.html` screens/HUD v1.1 (`>=18px`, `>=30 FPS`), 2 team skills in `.agents/skills/`, and all 4 per-slice `unittest` + headless determinism suites. | All 4 |
| `1:40–1:50` | `40–50m` | **Sequential PR Merges & Gates**: Merge `Slice 1 -> Slice 2 -> Slice 3 -> Slice 4`; run P1 regression, 22,200-tick headless performance (`<= 20s`) & byte determinism, live `>= 30 FPS` check; fill `docs/verification/phase-2.md` & `docs/proof/phase-2/`. | `Limdim1604` + `Lmeo2h` + all |
| `1:50–1:55` | `50–55m` | **Freeze, Retro & Tag `phase-2`**: Feature freeze at `1:50`; complete `docs/retro.md` (Phase 2 quick), `AGENTS.md`, `docs/ai-usage-log.md`; run `check_team.py` & `unittest discover`; tag `phase-2` before `1:55`. | `Lmeo2h` + `duyhale95` |

## Complexity Tracking

No Constitution Check violations. Extracting `monsters.py`, `day.py`, and `shop.py` keeps each simulation concern single-purpose and avoids parallel merge conflicts while preserving the unified `Session` loop.
