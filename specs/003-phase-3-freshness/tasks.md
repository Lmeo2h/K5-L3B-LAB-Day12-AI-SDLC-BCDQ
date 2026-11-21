---
description: "Phase 3 (TICKET-03, Test Contract v1.2) 35-minute task breakdown across 4 vertical slices"
---

# Tasks: Quán Ăn Chợ Nổi — Phase 3 (Mùa Nước Nổi: Độ tươi & Kho cá thể)

**Input**: `specs/003-phase-3-freshness/spec.md`, `specs/003-phase-3-freshness/plan.md`, `TICKET-03`
**Timebox**: `35 phút` (`1:55–2:30`), target git tag `phase-3` before `2:30`.

---

## Phase 1: Foundational — Impact Analysis, Inventory v1.2 & Freshness Scale (Minutes 0–7)

- [ ] T001 [US1] Add `FRESH_SCALE = 240`, integer unit conversion (`fresh_to_units`, `units_to_fresh`, `is_spoiled_units`), and v1.2 individual-item validation/read/write (`{"items": [{"id", "kind", "fresh"}]}`) in `chonoi/inventory.py` (rejecting count dicts when `contract_version == "1.2"` with `BadInput` exit `2`) (`duyhale95`)
- [ ] T002 [US1] Update `chonoi/contract.py` to validate `tuning.freshness` (`initial: 100`, `gather_decay_per_s: 0.5`, `quan_decay_per_s: 0.25`, `spoiled_below: 30`) and accept `contract_version` `"1.1"` (during transition) and `"1.2"` (`duyhale95`)
- [ ] T003 [P] Document Phase 3 edge cases (threshold `< 30` before rounding, `spoiled` before re-reserve order, `unfulfillable` patience behavior, `base_price` floor before tip) in `docs/clarify.md` (`missher03`)
- [ ] T004 [P] Initialize `docs/proof/phase-3/` and prepare v1.2 fixture migration checklist (`Limdim1604`)

**Checkpoint**: `chonoi/inventory.py` v1.2 helpers & `chonoi/contract.py` on `main` by minute 7 — all 4 slices build in parallel.

---

## Phase 2: User Story 1 — `gather` Individual Hold, Freshness Decay & Spoiled Threshold (Priority: P1)

**Owner**: `duyhale95` (backup `missher03`) | **Branch**: `feat/p3-s1-contract-fresh-gather`

### Tests (Write FIRST)
- [ ] T005 [P] [US1] Write unit & headless tests in `tests/test_freshness_gather_v12.py` for v1.2 inventory read/write (atomic write, count-dict rejection exit `2`, duplicate ID / out-of-range `fresh`), `I1, I2...` monotonic ID assignment on harvest/catch, `fresh=100` no decay on acquisition tick, `0.5/s` decay on existing `hold`, pause freezing decay, and exact `fresh=30 -> spoiled(location="hold")` on tick 1

### Implementation & Migration
- [ ] T006 [US1] Update `GatherSim` (`chonoi/sim/gather.py`) to accept optional `item_ids: IdAllocator`, store `hold` as individual item dicts (`240`-unit precision), decay existing `hold` at step start, emit `spoiled` sorted by `id_key`, assign `I1..` on harvest/catch, and output v1.2 `inventory_items()` / `gather_end.inventory`
- [ ] T007 [US1] Update `_validate_gather` in `chonoi/scenario.py` to validate `gather.hold[]` as v1.2 individual items (`id`, `kind`, `fresh ∈ [0, 100]`, unique IDs); migrate `tests/test_gather_harvest.py`, `tests/test_gather_survival.py`, `tests/test_gather_fish_v11.py`, `tests/test_python_starter_units.py` to v1.2 `hold` fixtures with commit rationale
- [ ] T008 [US1] Run Slice 1 tests + log AI usage in `docs/ai-usage-log.md` and merge `feat/p3-s1-contract-fresh-gather` to `main` (PR #1)

---

## Phase 3: User Story 2 — Crocodile LIFO Individual Drops & Continuous Multi-Day IDs (Priority: P1)

**Owner**: `missher03` (backup `duyhale95`) | **Branch**: `feat/p3-s2-monsters-day-v12`

### Tests (Write FIRST)
- [ ] T009 [P] [US2] Write unit & headless tests in `tests/test_monsters_day_v12.py` for `monster_hit.lost` and `faint.lost` returning LIFO item dicts with exact current `fresh`, `DaySim` shared monotonic `item_ids` across phases and Days 1–5 (Day 1 preserves scenario `hold` IDs, Day 2+ allocates new IDs), zero extra decay on `gather -> quan` transition tick, and spoiled items carried to `quan`

### Implementation & Migration
- [ ] T010 [US2] Update `chonoi/sim/monsters.py` so `monster_hit.lost` and `faint.lost` return individual item dicts (without mutating `fresh`) and `chonoi/sim/day.py` to maintain a shared `self.item_ids = IdAllocator()`, reserve Day 1 scenario IDs, pass `item_ids` to `GatherSim` and `QuanSim`, and re-assign IDs on Day 2+ `gather.hold` fixtures
- [ ] T011 [US2] Rebase onto `main` (after T008), update `tests/test_gather_monsters.py` for individual-item `hold`/`lost`, update `docs/clarify.md` & `docs/ai-usage-log.md`, and merge `feat/p3-s2-monsters-day-v12` to `main` (PR #2)

---

## Phase 4: User Story 3 — `quan` Freshness Decay, ID Reservations, Freshness Pricing & Scenario v1.2 (Priority: P1)

**Owner**: `Limdim1604` (backup `Lmeo2h`) | **Branch**: `feat/p3-s3-quan-freshness-qa`

### Tests (Write FIRST)
- [ ] T012 [P] [US3] Write unit & headless tests in `tests/test_quan_freshness_v12.py` for `0.25/s` stock decay (including reserved items, excluding cooked dishes), `spoiled(location="stock")` sorted by `id_key`, single re-reserve attempt ordered by `(order_tick, id_key(table_id))` -> `unfulfillable`, freshest-first + smallest `id_key`, `cook_started.items` sorted `(kind, id_key)`, `base_price = floor(price * avg_fresh / 100)`, `tip` on locked `base_price`, and `scenario.py` v1.2 conflict checks (exit `2`)

### Implementation, Flip v1.2 & Migration
- [ ] T013 [US3] Update `chonoi/sim/quan.py` for v1.2 individual-item `stock`, step-start decay, `spoiled` + re-reserve pass, freshest-first reservation, exact ID consumption, and freshness-adjusted `base_price` / `tip`
- [ ] T014 [US3] Rebase onto `main` (after T011), update `_validate_quan` and `prepare_quan_customers` in `chonoi/scenario.py` for v1.2 `stock[]` & `customers[].reserved[]` (array of unique unspoiled item IDs), flip `game.contract.json` to `"contract_version": "1.2"` with `freshness` tuning block, and migrate `tests/test_quan_customers.py`, `tests/test_quan_service.py`, `tests/test_quan_v11.py`, `tests/test_smoke_p1.py` with commit rationale
- [ ] T015 [US3] **Minute-20 Handoff Smoke (`2:15`)**: Run 2-process `gather --inventory-out` → `quan --inventory --ticks 0` and verify exact `id`, `kind`, `fresh` match; save proof to `docs/proof/phase-3/integration.md`; merge `feat/p3-s3-quan-freshness-qa` to `main` (PR #3)

---

## Phase 5: User Story 4 — `ShopSim`/`runner` v1.2, Freshness HUD, `CHANGELOG.md` & Tag `phase-3` (Priority: P1)

**Owner**: `Lmeo2h` (backup `Limdim1604`) | **Branch**: `feat/p3-s4-shop-ui-changelog`

### Tests (Write FIRST)
- [ ] T016 [P] [US4] Write tests in `tests/test_v12_handoff_ui.py` for `ShopSim` preserving v1.2 `stock` without freshness decay over `600` ticks, `runner.py` passing `item_ids` and rejecting count-based `--inventory` with exit `2`, and `gather -> quan` + `day` handoff parity

### Implementation & Release Gate
- [ ] T017 [US4] Update `chonoi/sim/shop.py` (keep v1.2 `stock` list format untouched), `chonoi/runner.py` (support v1.2 `inventory` list & `item_ids` if needed), and `chonoi/web/index.html` (display item freshness `%`/bar and spoiled `< 30` indicator on `hold` and `stock` at `>= 18px sans-serif`, `>= 30 FPS`, off in `headless`)
- [ ] T018 [US4] Rebase onto `main` (after T015), migrate `tests/test_day_shop_pause.py` (`ShopSim` / `DaySim` v1.2 fixtures), write `CHANGELOG.md` (v1.2 breaking changes & fixture migration guide), update `AGENTS.md` and `docs/retro.md` (Phase 3 quick), and merge `feat/p3-s4-shop-ui-changelog` to `main` (PR #4)
- [ ] T019 [US3/US4] Final release gates on `main`: run full `unittest discover -s tests -v`, `python tools/check_team.py`, byte-identical JSONL checks across all 3 modes, `22,200`-tick perf `<= 20s`, finalize `docs/verification/phase-3.md` & `docs/proof/phase-3/`, verify `>= 3` commits/member, and push tag `phase-3` before **`2:30`**
