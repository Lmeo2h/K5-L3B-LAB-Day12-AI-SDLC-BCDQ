---
description: "Phase 2 (TICKET-02, Test Contract v1.1) 55-minute task breakdown across 4 vertical slices"
---

# Tasks: Quán Ăn Chợ Nổi — Phase 2 (Một ngày ở chợ nổi)

**Input**: Design documents from `specs/002-phase-2-day-loop/` (`spec.md`, `plan.md`)
**Prerequisites**: `specs/002-phase-2-day-loop/plan.md`, `specs/002-phase-2-day-loop/spec.md`, `.specify/memory/constitution.md`, `TEAM.md`, `AGENTS.md`

**Tests**: Test-First is REQUIRED for every vertical slice (`tests/test_gather_fish_v11.py`, `tests/test_gather_monsters.py`, `tests/test_quan_v11.py`, `tests/test_day_shop_pause.py`).

**Timebox**: `55 phút` (`1:00–1:55`), target git tag `phase-2` before `1:55`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no blocking dependency)
- **[Story]**: User story / vertical slice mapping (`US1`..`US4`)
- Exact file paths are included in every task.

---

## Phase 1: Foundational — Contract v1.1 & Shared Baseline (Minutes 0–8)

**Purpose**: Land Test Contract v1.1 schema, tuning, ingredient list, and input buttons on `main` within the first 5–8 minutes so all 4 branches rebase cleanly while others draft Test-First suites and clarifications in parallel.

- [ ] T001 [US1] Upgrade `game.contract.json` to `contract_version: "1.1"` with all TICKET-02 tuning constants (`ca_keo`, `keo_neo`, `N5`/`N6`, 8 `fish_initial`, `fish_max: 12`, `fish_speed: 1.5`, `fish_x: [4, 96]`, species depth ranges, `fish_turn_ticks: 120`, `fish_spawn_ticks: 360`, `fish_spawn_weights`, crocodile `M1`/`M2` & recoil/invuln params, 2 stoves `B1`/`B2`, 4 tables `T1`–`T4`, 6 menu dishes, D1–D5 `day_plan` & `max_days: 5`, and `shop` oxygen/hp L1–L2 tiers & `max_ticks: 600`) (`duyhale95`)
- [ ] T002 [US1] Update `chonoi/contract.py` to validate Contract v1.1 tuning schema and ranges (`fish_initial` 8 schools, `fish_spawn_weights`, `monsters`, 6 menu dishes, `day_plan`, `shop` tiers) (`duyhale95`, depends on T001)
- [ ] T003 [P] [US1] Update `chonoi/inventory.py` to support the 6 v1.1 ingredients (`ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`) while keeping `{"items": {...}}` schema intact (`duyhale95`)
- [ ] T004 [P] [US1] Update `chonoi/inputs.py` to accept v1.1 inputs (`pause` boolean, `shop_done` boolean, `buy` string validation in `load_frames`, `InputPlayer`, and `LiveInputs`) and merge `T001`–`T004` to `main` by minute 8 (`duyhale95`)
- [ ] T005 [P] Verify P1 baseline on `main` (`python tools/check_team.py`, `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v`) and initialize `docs/proof/phase-2/` (`Limdim1604`)
- [ ] T006 [P] Document TICKET-02 edge-case clarifications (choke-on-zero step vs `oxygen_empty`/`zero_oxy_ticks` interaction, crocodile tie-breaks, `day` vs standalone `quan` `day_plan` behavior) in `docs/clarify.md` (`missher03`)

**Checkpoint**: Contract v1.1 (`T001`–`T004`) merged on `main` — all 4 members rebase and run full parallel vertical slice development.

---

## Phase 2: User Story 1 — `gather` Fish Swimming/Spawning & Choke-on-Zero (Priority: P1)

**Owner**: `duyhale95` (Hà Lê Duy — Scrum/Release, backup `missher03`) | **Branch**: `feat/p2-s1-contract-fish`
**Goal**: Implement deterministic fish swimming (`fish_turn_ticks: 120`, boundary reflection, `age_ticks`, `random_fish: false`), fish spawning (`fish_spawn_ticks: 360`, `fish_max: 12`, clearance `> 1 m`, normalized 40/30/30 weights, `fish_spawned`), and choke-on-zero underwater cadence in `chonoi/sim/gather.py`.
**Independent Test**: Run `tests/test_gather_fish_v11.py` and headless `--mode gather` runs verifying deterministic fish trajectories, spawning caps/weights, and exact tick of choke damage when oxygen hits `0`.

### Tests for User Story 1 (Write FIRST — ensure FAIL before implementation)

- [ ] T007 [P] [US1] Write unit & headless tests in `tests/test_gather_fish_v11.py` for fish swimming (`fish_speed: 1.5`), 120-tick seeded heading turns before moving, remaining-distance reflection on `fish_x` (`[4, 96]`) & species depth bounds (including corner double-flip), `fish[].age_ticks`, and `random_fish: false`
- [ ] T008 [P] [US1] Write unit & headless tests in `tests/test_gather_fish_v11.py` for 360-tick fish spawning (`fish_max: 12`, max 1 school/step, clearance `> 1 m`, normalized 40/30/30 weights over valid points, `fish_spawned`) and choke-on-zero (loses 1 HP every 60 ticks starting on the step oxygen reaches `0`, resets when `oxygen_ticks > 0` or at surface, pierces `invuln_ticks`, preserves `hold`)

### Implementation & Verification for User Story 1

- [ ] T009 [US1] Update `_validate_gather` in `chonoi/scenario.py` to accept `ca_keo`, `keo_neo`, `fish[].age_ticks`, and v1.1 species depth bounds while rejecting invalid fish/node fixtures with `BadInput` (exit code 2)
- [ ] T010 [US1] Implement `_step_fish_swim` and `_step_fish_spawn` in `chonoi/sim/gather.py` using dedicated `Streams` channels, `ids.sort_by_id`, and `IdAllocator` (after reserving scenario/tuning IDs)
- [ ] T011 [US1] Update `_step_oxygen_and_choke` in `chonoi/sim/gather.py` for choke-on-zero 60-tick cadence (pierces invuln, preserves hold); update any P1 test in `tests/test_gather_survival.py` affected by the v1.1 rule change with an explicit commit reason
- [ ] T012 [US1] Run `tests/test_gather_fish_v11.py`, full `unittest` suite, and headless determinism check; log AI usage in `docs/ai-usage-log.md` and merge `feat/p2-s1-contract-fish` to `main` (PR #1)

**Checkpoint**: US1 merged on `main` — Contract v1.1, swimming/spawning fish, and choke-on-zero are green.

---

## Phase 3: User Story 2 — `gather` Cá Sấu Năm Chèo, Bất tử, Rơi hàng LIFO & Ngất (Priority: P1)

**Owner**: `missher03` (Nguyễn Văn Quốc — PO, backup `duyhale95`) | **Branch**: `feat/p2-s2-crocodiles`
**Goal**: Implement `M1` (Day 1+) and `M2` (Day 3+) crocodiles (`patrol`, `chase`, `recoil`), collision hit (`-1` HP, `invuln_ticks = 90`, LIFO `floor(len(hold)*0.5)` drop, `monster_hit`), `faint(cause="monster")`, and `gather.monsters[]` validation.
**Independent Test**: Run `tests/test_gather_monsters.py` and headless `--mode gather` runs confirming patrol/chase/recoil transitions, LIFO drop math, `invuln_ticks` protection, `faint(cause="monster")`, and exit code `2` on invalid `gather.monsters[]`.

### Tests for User Story 2 (Write FIRST — ensure FAIL before implementation)

- [ ] T013 [P] [US2] Write unit & headless tests in `tests/test_gather_monsters.py` for `M1` (`[60,24]<->[64,24]`, Day 1+) & `M2` (`[85,18]<->[89,18]`, Day 3+) `patrol` (1.0 m/s), `chase` (3.0 m/s at `d >= 10` & `dist <= 10 m`), exit chase (`dist > 16 m` or `d < 10`), `ca_sau` depth `[10, 30]`, and `gather.monsters[]` validation (exit code 2)
- [ ] T014 [P] [US2] Write unit & headless tests in `tests/test_gather_monsters.py` for collision after both move (`dist <= 1.5 m`, `d >= 10`, `invuln_ticks == 0`, nearest/`id_key` max 1 hit/step), `-1` HP, `floor(len(hold)*0.5)` LIFO drop (`lost`), `invuln_ticks = 90`, `monster_hit`, 60-step `recoil` (`2/60 m/step`, `+x` on coincident pos, clamped), and `hp == 0` -> `faint(cause="monster")` + `gather_end("fainted")`

### Implementation & Verification for User Story 2

- [ ] T015 [US2] Create `chonoi/sim/monsters.py` implementing crocodile state setup (`M1`/`M2` day gating), `_step_monsters` (`patrol`/`chase`/`recoil`), and `_resolve_monster_collision` (LIFO `floor(len(hold)*0.5)` drop, `recoil` vector, `monster_hit`, `faint(cause="monster")`)
- [ ] T016 [US2] Extend `_validate_gather` in `chonoi/scenario.py` to validate `gather.monsters[]` IDs, `kind == "ca_sau"`, state/target/recoil fields, bounds, and depth `[10, 30]`
- [ ] T017 [US2] Rebase onto `main` (after T012), hook `chonoi/sim/monsters.py` into `GatherSim.step()` (Section 4.5 steps 5–6), and add `monsters[]` and `player.invuln_ticks` to `GatherSim.snapshot()` in `chonoi/sim/gather.py`
- [ ] T018 [US2] Run `tests/test_gather_monsters.py`, full `unittest` suite, and headless determinism check; log AI usage in `docs/ai-usage-log.md` and merge `feat/p2-s2-crocodiles` to `main` (PR #2)

**Checkpoint**: US1 + US2 integrated on `main` — full Phase 2 `gather` gameplay (fish, choke, crocodiles) passes all tests.

---

## Phase 4: User Story 3 — `quan` 2 Bếp / 4 Bàn / 6 Món / `day_plan`, 2 Team Skills & QA (Priority: P1)

**Owner**: `Limdim1604` (Nguyễn Thiên Bảo — QA Lead, backup `Lmeo2h`) | **Branch**: `feat/p2-s3-quan-v11-qa`
**Goal**: Upgrade `QuanSim` (`B1`/`B2`, `T1`–`T4`, 6 dishes, `day_plan` filtering) and `chonoi/scenario.py` v1.1 rules, create 2 team skills in `.agents/skills/`, execute the 20-min integration smoke & P1 regression, and maintain `docs/verification/phase-2.md` & `docs/proof/phase-2/`.
**Independent Test**: Run `tests/test_quan_v11.py` verifying 2-stove/4-table parallel service, 6-dish recipes, `day_plan` dish filtering in `day` vs standalone `quan`, and exit code `2` on v1.1 scenario conflicts.

### Tests for User Story 3 (Write FIRST — ensure FAIL before implementation)

- [ ] T019 [P] [US3] Write unit & headless tests in `tests/test_quan_v11.py` for 2 stoves (`B1`, `B2`), 4 tables (`T1`–`T4`), 6 dishes (`canh_chua_ca_loc` 8s/90, `ca_keo_nuong` 6s/70, `lau_mam` 12s/200), arrival `120 + 900*k` to smallest empty table ID, and `day_plan` menu filtering in `day` mode (allowing reorders past quota) vs all 6 dishes in standalone `quan`
- [ ] T020 [P] [US3] Write unit & headless tests in `tests/test_quan_v11.py` for v1.1 scenario validation (`day` rejecting `quan.stock`/`quan.reputation`, invalid `day_plan` dishes/ingredients, and evening `quan` conflict against carried stock returning exit code 2)

### Implementation, Skills & Mid-Sprint Smoke for User Story 3

- [ ] T021 [US3] Update `chonoi/sim/quan.py` for 2 stoves, 4 tables, 6 dishes, and `day_plan` menu filtering prior to available-ingredient check with uniform `Streams` selection
- [ ] T022 [US3] Rebase onto `main` (after T018) and update `chonoi/scenario.py` (`_validate_quan`, `_validate_day`) for v1.1 `day_plan` and fail-fast `BadInput` checks against carried evening stock
- [ ] T023 [P] [US3] Author 2 reusable team skills in `.agents/skills/` (per `AGENTS.md`: e.g., `chonoi-contract-verify` for Contract v1.1 / headless determinism checks and `chonoi-slice-qa` for vertical slice PR & AC verification)
- [ ] T024 [US3] **20-Minute Integration Smoke Checkpoint**: Run mid-sprint integration smoke across `gather` + `monsters` + `quan` v1.1 and P1 regression (`test_smoke_p1.py`, `test_gather_*`, `test_quan_*`) with v1.1 standard numbers; save interim logs in `docs/proof/phase-2/`
- [ ] T025 [US3] Run `tests/test_quan_v11.py` and full `unittest` suite, update `docs/verification/phase-2.md` & `docs/proof/phase-2/`, log AI usage in `docs/ai-usage-log.md`, and merge `feat/p2-s3-quan-v11-qa` to `main` (PR #3)

**Checkpoint**: US1–US3 merged on `main` — `gather` v1.1, `monsters`, `quan` v1.1, v1.1 scenario checks, and 2 team skills ready.

---

## Phase 5: User Story 4 — Day Loop (`--mode day`), `ShopSim`, `pause` & Live Web UI/HUD v1.1 (Priority: P1)

**Owner**: `Lmeo2h` (Nguyễn Tấn Châu — Integrator, backup `Limdim1604`) | **Branch**: `feat/p2-s4-day-shop-ui`
**Goal**: Implement `--mode day --days 1..5`, `ShopSim` (`oxygen`/`hp` L1–L2 upgrades, 600 ticks), outer `pause` wrapper across all 3 modes, v1.1 snapshot/event envelope, and full browser UI/HUD v1.1 (`>= 18px` at `1280x720`, `>= 30 FPS`, disabled in headless).
**Independent Test**: Run `tests/test_day_shop_pause.py` verifying 5-day loop transitions, shop purchase/rollover math, `pause`/`resumed` freezing across all 3 modes, and `chonoi.live` browser playtesting.

### Tests for User Story 4 (Write FIRST — ensure FAIL before implementation)

- [ ] T026 [P] [US4] Write unit & headless tests in `tests/test_day_shop_pause.py` for `--mode day --days 1..5` (default 1, max 5, invalid `--days` -> exit 2), phase order (`DayIntro -> gather -> EveningIntro -> quan -> DayResult -> Shop -> DayIntro`), `day_start`/`day_plan`/`phase_start`/`days_completed`, max `22,200` unpaused ticks/day, gather faint -> empty-stock `quan`, and v1.1 snapshot/event fields
- [ ] T027 [P] [US4] Write unit & headless tests in `tests/test_day_shop_pause.py` for `ShopSim` (`oxygen` L1 `200->45s`/L2 `400->60s`, `hp` L1 `250->4`/L2 `500->5`, `buy`, `shop_done`, `max_ticks: 600`, `bought`/`buy_failed`/`shop_end`, `money` vs `earned`/`score`, `active_upgrades` next-day activation) and `pause` across `gather`, `quan`, `day` (`paused`/`resumed`, `state: "paused"`, frozen timers/sim_tick)

### Implementation & Verification for User Story 4

- [ ] T028 [P] [US4] Implement `chonoi/sim/shop.py` (`ShopSim` with `oxygen`/`hp` L1–L2 tiers, `buy` validation, `shop_done`, `max_ticks: 600`, `bought`/`buy_failed(action, reason)`/`shop_end(reason)`)
- [ ] T029 [US4] Implement `chonoi/sim/day.py` (`DaySim` orchestrating D1–D5 loop, `day_start`/`day_plan`/`phase_start`/`days_completed`, `active_upgrades` rollover, oxygen/HP refill, hold & leftover stock clear on new day)
- [ ] T030 [US4] Update `chonoi/runner.py`, `chonoi/headless.py`, and `chonoi/live.py` for `--mode day --days 1..5`, outer `pause` wrapper across all 3 modes, and v1.1 snapshot/event envelope (`day`, `day_plan`, `upgrades`, `active_upgrades`, `phase`, `stock` in shop, `day` on events)
- [ ] T031 [US4] Update `chonoi/web/index.html` with Menu (`Chơi`/`Thoát`), `DayIntro` (4s/key), `EveningIntro`, `DayResult`, `Summary`, Pause overlay (`Esc`/`P`), Shop UI, and Gather/Quan HUD v1.1 (`<25%` warning, `<=30s` time color, purple border `"Thủy quái!"`, `"Hết hơi!"`, ingredient checklist, sans-serif `>= 18px` at `1280x720`, `>= 30 FPS`; disabled in headless)
- [ ] T032 [US4] Rebase onto `main` (after T025), run `tests/test_day_shop_pause.py` and full `unittest` suite, log AI usage in `docs/ai-usage-log.md`, and merge `feat/p2-s4-day-shop-ui` to `main` (PR #4)

**Checkpoint**: All 4 Vertical Slices (`US1`–`US4`) integrated on `main`.

---

## Phase 6: Final Gates, Performance Benchmark, Retro & Tag `phase-2` (Minutes 40–55)

**Purpose**: Verify full end-to-end determinism, headless `<= 20s` performance, live `>= 30 FPS` / `>= 18px` UI, complete QA evidence & Phase 2 quick retro, and tag `phase-2` before `1:55`.

- [ ] T033 Run end-to-end headless determinism check (same seed -> byte-identical JSONL across `gather`, `quan`, `day`) and single-day `22,200`-tick performance benchmark (`<= 20s`), plus live `1280x720` `>= 30 FPS` / `>= 18px` verification; store logs in `docs/proof/phase-2/` (`Limdim1604` & `Lmeo2h`)
- [ ] T034 [P] Fill final `main`-commit evidence and honest `Đạt` / `Chưa đạt` status for all `AC-P2-01`..`AC-P2-12` rows in `docs/verification/phase-2.md` (`Limdim1604`)
- [ ] T035 [P] Update `docs/retro.md` (Phase 2 quick retro: Điều tốt / Điều tệ / 1 hành động cho Phase 3), `AGENTS.md` (document the 2 new `.agents/skills/` skills and `--mode day` commands), `docs/standup.md`, `docs/ai-usage-log.md`, and `docs/members/<handle>.md` (`Lmeo2h` & team)
- [ ] T036 Run final release gate on `main` (`python tools/check_team.py`, `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v`), verify `>= 3` meaningful commits per member, and create git tag `phase-2` before `1:55` (`Lmeo2h` / `duyhale95`)

---

## Dependencies & Execution Order

- **Phase 1 (`T001`–`T004`)** lands first on `main` (within minutes `0–8`) -> unblocks all 4 vertical slices (`T005`–`T006` run concurrently).
- **Test-First (`T007–T008`, `T013–T014`, `T019–T020`, `T026–T027`)**: Each slice writes its failing tests before implementation and can start immediately in parallel once `T001`–`T004` specs are clear.
- **Sequential Merge Order to `main`**:
  1. `US1` (`duyhale95` — `feat/p2-s1-contract-fish`) merges **1st** (`T012`).
  2. `US2` (`missher03` — `feat/p2-s2-crocodiles`) rebases onto `main`, hooks `monsters.py` into `gather.py` & `scenario.py`, merges **2nd** (`T018`).
  3. `US3` (`Limdim1604` — `feat/p2-s3-quan-v11-qa`) rebases onto `main` for `scenario.py`, runs 20-min smoke (`T024`), merges **3rd** (`T025`).
  4. `US4` (`Lmeo2h` — `feat/p2-s4-day-shop-ui`) rebases onto `main`, merges **4th** (`T032`).
- **Phase 6 (`T033`–`T036`)** runs on integrated `main` and finishes with tag `phase-2` before `1:55`.
