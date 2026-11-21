---
description: "Phase 1 Core task breakdown across 4 vertical slices for Quán Ăn Chợ Nổi"
---

# Tasks: Quán Ăn Chợ Nổi — Phase 1 Core

**Input**: Design documents from `specs/001-phase-1-core/` (`spec.md`, `plan.md`)
**Prerequisites**: `specs/001-phase-1-core/plan.md`, `specs/001-phase-1-core/spec.md`, `.specify/memory/constitution.md`, `game.contract.json`, `AGENTS.md`

**Tests**: Test-First is REQUIRED for every vertical slice (unit tests + headless black-box tests written and verified failing before implementation).

**Organization**: Tasks are grouped into Setup, Foundational, 4 independent Vertical Slices (US1–US4, one per team member), and Polish/Release (`phase-1` tag).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no blocking dependency)
- **[Story]**: User story / vertical slice mapping (`US1`..`US4`)
- Exact file paths are included in every task.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify baseline environment, team roster, and starter smoke tests before branching.

- [ ] T001 Verify `TEAM.md` and `game.contract.json` (`team_size: 4`) pass `python tools/check_team.py` and `tests/test_team_check.py`
- [ ] T002 [P] Run baseline test suite (`PYTHONPATH=tests:. python -m unittest discover -s tests -v`) to confirm starter `tests/test_smoke_p1.py`, `tests/test_python_starter_units.py`, and `tests/test_live.py` pass
- [ ] T003 [P] Verify starter headless smoke execution (`python -m chonoi.headless --mode gather --seed 1 --ticks 60 --out out.jsonl` and `--mode quan`) and clean up temporary output

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock integration contracts, shared state conventions, and clarify open PRD-0 items before parallel slice implementation.

**CRITICAL**: Align these shared interfaces before starting US1–US4 edits to prevent `gather.py` / `quan.py` conflicts.

- [ ] T004 Confirm `docs/contracts/README.md` & `docs/contracts/inventory.sample.json` schema (`{"items": {...}}`) and event payload conventions across all 4 members
- [ ] T005 [P] Record any ambiguous PRD-0 formulas/tie-breakers (e.g., `catch` target selection/range behavior, `hold_full` partial vs all-or-nothing fish yield, `no_dish` / `customer` initial scenario state fields) in `docs/clarify.md` for PO (`missher03`) resolution
- [ ] T006 [P] Agree on shared helper boundaries in `chonoi/sim/gather.py` (Slice 1: step block 2 + LIFO hold; Slice 2: step blocks 3–4) and `chonoi/sim/quan.py` (Slice 3: customer schema, `reserved` stock, spawn/patience; Slice 4: stove/interact/eating/payment) per `specs/001-phase-1-core/plan.md`

**Checkpoint**: Foundation & clarifications agreed — US1 (`duyhale95`), US2 (`missher03`), US3 (`Limdim1604`), and US4 (`Lmeo2h`) can develop in parallel on separate feature branches.

---

## Phase 3: User Story 1 — `gather` Slice 1: Sinh tồn dưới nước & Giỏ LIFO (Priority: P1)

**Owner**: `duyhale95` (Hà Lê Duy — Nhóm trưởng / Scrum-Release) | **Branch**: `feat/p1-s1-gather-survival`
**Goal**: Implement surface/underwater transition events, oxygen drain/refill, asphyxiation (`choke`), fainting (`faint` + empty hold/inventory), and LIFO hold capacity enforcement in `chonoi/sim/gather.py`.
**Independent Test**: Run `tests/test_gather_survival.py` and headless scenarios verifying `dive`, `surface`, `oxygen_empty`, `choke`, `faint`, `gather_end(reason="fainted")`, empty `--inventory-out`, and LIFO hold order.

### Tests for User Story 1 (Write FIRST — ensure FAIL before implementation)

- [ ] T007 [P] [US1] Create unit & headless black-box tests for `dive`/`surface` transitions, oxygen drain (`d > surface_depth`) and refill (`oxygen_refill_per_tick` clamped to `[0, oxygen_max_ticks]`), and `oxygen_empty` event in `tests/test_gather_survival.py`
- [ ] T008 [P] [US1] Add tests for `zero_oxy_ticks` counting up to `choke_interval_ticks`, `choke` HP loss, `faint` -> `gather_end(reason="fainted")` clearing `hold` & writing empty inventory, and LIFO `hold` capacity (`hold_capacity`) in `tests/test_gather_survival.py`

### Implementation for User Story 1

- [ ] T009 [US1] Implement `_step_region_transition` (`dive` / `surface` events with `pos`) and `_step_oxygen_and_choke` (refill/drain, `oxygen_empty`, `zero_oxy_ticks`, `choke`, `faint`, clearing `self.hold`, `_finish("fainted", events)`) in `chonoi/sim/gather.py`
- [ ] T010 [US1] Implement LIFO hold helper methods (`_push_hold` / `_pop_hold` / capacity check against `hold_capacity`) and wire step block 2 in `GatherSim.step()` in `chonoi/sim/gather.py`

### Verification for User Story 1

- [ ] T011 [US1] Run `tests/test_gather_survival.py`, full `unittest discover`, and deterministic `python -m chonoi.headless --mode gather` checks; log AI usage in `docs/ai-usage-log.md` and merge Slice 1 PR into `main`

**Checkpoint**: US1 complete & merged on `main` — oxygen, choke, faint, and LIFO hold work independently and pass all tests.

---

## Phase 4: User Story 2 — `gather` Slice 2: Thu hoạch mặt nước & Bắt cá (Priority: P1)

**Owner**: `missher03` (Nguyễn Văn Quốc — PO) | **Branch**: `feat/p1-s2-gather-harvest`
**Goal**: Implement surface node harvesting (`gather`, `hold_full`, `regrow_s`), underwater fish catching (`catch` -> `fish_caught`, `hold_full`, `catch_cooldown_s`), and dock priority before node harvest in `chonoi/sim/gather.py`.
**Independent Test**: Run `tests/test_gather_harvest.py` and headless gather scenarios confirming node harvest, regrow cycle, fish catching with cooldown, `hold_full`, dock priority over nearby nodes, and `--inventory-out` JSON output.

### Tests for User Story 2 (Write FIRST — ensure FAIL before implementation)

- [ ] T012 [P] [US2] Create unit & headless tests for surface node harvesting (`interact` at surface within `interact_radius`, nearest then `id_key` tie-break, `gather` event, `regrow_ticks` reset, `node_regrown`, and `hold_full`) in `tests/test_gather_harvest.py`
- [ ] T013 [P] [US2] Add tests for dock-before-gather priority when inside `dock_radius` and underwater `catch` (`catch_cd_ticks == 0`, `catch_radius`, `fish_yield`, `fish_caught`, `hold_full`, cooldown reset) in `tests/test_gather_harvest.py`

### Implementation for User Story 2

- [ ] T014 [US2] Rebase onto `main` (after US1) and implement `_try_gather_node(events)` in `chonoi/sim/gather.py` using `sort_by_id` / `id_key` tie-breaking, `node_yield`, `regrow_s`, and `hold_capacity`
- [ ] T015 [US2] Implement `_try_catch_fish(events)` in `chonoi/sim/gather.py` checking `not self._at_surface()` and `catch_cd_ticks == 0`, reading `catch_radius`, `fish_yield`, and `catch_cooldown_s` from `self.t`, and wire step blocks 3–4 in `GatherSim.step()`

### Verification for User Story 2

- [ ] T016 [US2] Run `tests/test_gather_harvest.py`, `tests/test_smoke_p1.py`, and headless `--mode gather --inventory-out` deterministic checks; log AI usage in `docs/ai-usage-log.md` and open/merge Slice 2 PR

**Checkpoint**: US1 + US2 integrated — full `gather` mode gameplay (swim, oxygen/choke/faint, harvest, catch, dock, inventory export) works end-to-end.

---

## Phase 5: User Story 3 — `quan` Slice 3: Đón khách, Giữ chỗ, Kiên nhẫn & Kiểm mâu thuẫn Scenario (Priority: P1)

**Owner**: `Limdim1604` (Nguyễn Thiên Bảo — QA Lead) | **Branch**: `feat/p1-s3-quan-customers`
**Goal**: Complete rule-level scenario conflict validation in `chonoi/scenario.py` and customer arrival, cookable dish selection, ingredient reservation (`reserved`), `no_dish`, and patience/departure (`customer_left`, `left_reputation_delta`) in `chonoi/sim/quan.py`.
**Independent Test**: Run `tests/test_quan_customers.py` and headless `quan` scenarios verifying exit code `2` on conflicting scenarios and deterministic customer spawn/reserve/`no_dish`/`customer_left` JSONL events.

### Tests for User Story 3 (Write FIRST — ensure FAIL before implementation)

- [ ] T017 [P] [US3] Create scenario rule-level validation tests (over-reserved stock, invalid assigned dish, missing/invalid `eating` customer fields, invalid table/stove/customer states -> `BadInput` / exit code `2`) in `tests/test_quan_customers.py`
- [ ] T018 [P] [US3] Add `QuanSim` unit & headless tests for customer spawn (`first_customer_tick`, `customer_interval_s`), deterministic cookable dish selection via `Streams`, `reserved` stock accounting, `no_dish` event when uncookable, and patience expiry (`customer_left`, `left_reputation_delta`, reservation release) in `tests/test_quan_customers.py`

### Implementation for User Story 3

- [ ] T019 [US3] Extend `_validate_quan` (and shared rule checks) in `chonoi/scenario.py` to reject rule-level scenario conflicts with `BadInput` (exit code `2`)
- [ ] T020 [US3] Implement customer initialization/reservation reconstruction (`_init_customer_reservations`), `_available_stock`, `_pick_cookable_dish` (via `Streams`), `_spawn_customer_if_due`, and `_step_customer_patience` in `chonoi/sim/quan.py`

### Verification for User Story 3

- [ ] T021 [US3] Run `tests/test_quan_customers.py`, `tests/test_smoke_p1.py`, and headless `--mode quan` scenario checks; log AI usage in `docs/ai-usage-log.md` and merge Slice 3 PR into `main`

**Checkpoint**: US3 complete & merged on `main` — scenario validation and customer lifecycle (spawn, dish selection, stock reservation, `no_dish`, `customer_left`) verified.

---

## Phase 6: User Story 4 — `quan` Slice 4: Bếp, Phục vụ, Thanh toán/Boa/Uy tín & `quan_end` (Priority: P1)

**Owner**: `Lmeo2h` (Nguyễn Tấn Châu — Integrator) | **Branch**: `feat/p1-s4-quan-service`
**Goal**: Implement `interact` targeting priority `(distance, stove-before-table, id)`, cooking (`cook_started`, `dish_ready`), picking/serving (`dish_picked`, `served`), eating, payment/tip/reputation (`paid`, `tip_min_patience_ratio`, `tip_rate`, `tip_reputation`), and `quan_end` in `chonoi/sim/quan.py`.
**Independent Test**: Run `tests/test_quan_service.py` and headless `quan` runs with `--inventory` verifying full stove-to-table service loop, tip/reputation math, score formula, and `quan_end`.

### Tests for User Story 4 (Write FIRST — ensure FAIL before implementation)

- [ ] T022 [P] [US4] Create unit & headless tests for `interact` target selection priority (`(distance, stove before table, id_key)` within `interact_radius`), `cook_started`, `cook_ticks_left` countdown, `dish_ready`, and `dish_picked` (`carry_limit: 1`) in `tests/test_quan_service.py`
- [ ] T023 [P] [US4] Add tests for `served`, `eat_s` countdown, `paid` calculation with tip eligibility (`tip_min_patience_ratio`, `tip_rate`), `tip_reputation` clamped to `[reputation_min, reputation_max]`, and `quan_end` totals in `tests/test_quan_service.py`

### Implementation for User Story 4

- [ ] T024 [US4] Rebase onto `main` (after US3) and implement `_step_stoves(events)` and `_handle_interact(events)` (max 1 interact per tick, target priority `(dist, is_table, id_key)`, stove start/pickup, table serve) in `chonoi/sim/quan.py`
- [ ] T025 [US4] Implement `_step_eating_customers(events)` (payment, tip ratio check, `earned`/`money`/`shift_earned`/`reputation` update, `paid` event, customer cleanup) and verify `quan_end` payload in `chonoi/sim/quan.py`

### Verification for User Story 4

- [ ] T026 [US4] Run `tests/test_quan_service.py`, `tests/test_quan_customers.py`, and headless `--mode quan --inventory` checks; log AI usage in `docs/ai-usage-log.md` and merge Slice 4 PR into `main`

**Checkpoint**: All 4 vertical slices (`US1`–`US4`) integrated on `main` — both `gather` and `quan` modes are functionally complete for Phase 1.

---

## Phase 7: Polish, Cross-Slice Integration, QA & Tag `phase-1`

**Purpose**: End-to-end cross-mode verification, QA traceability evidence, documentation updates, and `phase-1` release tag.

- [ ] T027 [P] Run end-to-end cross-mode headless check (`gather --inventory-out` -> `quan --inventory`) and byte-for-byte determinism check across repeated seeds (`Lmeo2h`)
- [ ] T028 [P] Run `python -m chonoi.live --mode gather` & `--mode quan` manual/live smoke test (`tests/test_live.py`) to confirm browser preview renders live snapshots cleanly
- [ ] T029 Complete traceability matrix and honest pass/fail summary in `docs/verification/phase-1.md` and save test/headless outputs in `docs/proof/phase-1/` (`Limdim1604`)
- [ ] T030 [P] Update `AGENTS.md`, `docs/standup.md`, `docs/ai-usage-log.md`, and individual member logs in `docs/members/<handle>.md`
- [ ] T031 Run final gate on `main`: `python tools/check_team.py` and `PYTHONPATH=tests:. python -m unittest discover -s tests -v`, verify >= 3 commits per member, and create git tag `phase-1` (`Lmeo2h` / `duyhale95`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)** -> **Phase 2 (Foundational)**: Sequential prerequisite before slice implementation.
- **Phase 3 (US1)** & **Phase 4 (US2)** (`chonoi/sim/gather.py`): Can implement in parallel on separate branches; **US1 merges to `main` first**, then **US2 rebases and merges**.
- **Phase 5 (US3)** & **Phase 6 (US4)** (`chonoi/sim/quan.py`, `chonoi/scenario.py`): Can start immediately after Phase 2 in parallel with `gather` slices; **US3 merges to `main` first**, then **US4 rebases and merges**.
- **Phase 7 (Polish & Tag)**: Runs once US1–US4 are all merged into `main`.

### Within Each User Story

1. Write test cases FIRST in the slice's dedicated `tests/test_*.py` file and confirm they fail before editing sim code.
2. Implement slice-owned helper methods without modifying another slice's helpers or test files.
3. Verify via unit tests, full `unittest discover`, and `python -m chonoi.headless` before opening PR.
4. Peer review PR -> merge cleanly -> log AI usage in `docs/ai-usage-log.md`.

### Parallel Team Strategy

| Member | Handle | Slice | Primary Files | Independent Test File |
|---|---|---|---|---|
| Hà Lê Duy | `duyhale95` | US1 (gather survival & LIFO) | `chonoi/sim/gather.py` | `tests/test_gather_survival.py` |
| Nguyễn Văn Quốc | `missher03` | US2 (gather harvest & fish) | `chonoi/sim/gather.py` | `tests/test_gather_harvest.py` |
| Nguyễn Thiên Bảo | `Limdim1604` | US3 (quan customers + scenario + QA) | `chonoi/sim/quan.py`, `chonoi/scenario.py`, `docs/verification/phase-1.md` | `tests/test_quan_customers.py` |
| Nguyễn Tấn Châu | `Lmeo2h` | US4 (quan service + integration + tag) | `chonoi/sim/quan.py` | `tests/test_quan_service.py` |
