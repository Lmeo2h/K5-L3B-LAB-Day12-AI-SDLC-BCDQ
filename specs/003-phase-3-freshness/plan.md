# Implementation Plan: Quán Ăn Chợ Nổi — Phase 3 (Mùa Nước Nổi: Độ tươi & Kho cá thể)

**Branch**: `003-phase-3-freshness` | **Date**: 2026-11-21 | **Spec**: [spec.md](spec.md)

**Input**: TICKET-03 ("Mùa Nước Nổi", Test Contract `v1.2`, 35-minute sprint `1:55–2:30`, target git tag `phase-3`).

## Summary

Upgrade the Phase 2 simulation (`v1.1`) to **Test Contract v1.2** within the **35-minute (`1:55–2:30`)** sprint:
1. **Schema Migration (`{"items": {kind: n}}` → `{"items": [{"id", "kind", "fresh"}]}`)** across `chonoi/inventory.py`, `game.contract.json`, `chonoi/contract.py`, `chonoi/scenario.py`, and all simulation modules (`gather.py`, `monsters.py`, `quan.py`, `day.py`, `shop.py`, `runner.py`).
2. **Exact Integer Freshness Arithmetic (`FRESH_SCALE = 240`)**: `100` = `24,000` units, `30` = `7,200` units; `gather` decays `2 units/tick` (`0.5/s`); `quan` decays `1 unit/tick` (`0.25/s`); threshold `< 30` checked BEFORE rounding; `spoiled` emitted once per crossing sorted by `id_key`.
3. **Monotonic Item IDs (`I1, I2, ...`) & Per-ID Reservations**: Shared `item_ids: IdAllocator` in `DaySim`/`Session` so IDs never reset or collide across phases/days; `quan` reserves freshest unspoiled IDs (tie-break smallest `id_key`), releases & re-reserves once on spoilage by `(order_tick, id_key(table_id))`, and locks `base_price = floor(list_price * avg_fresh / 100)` at `cook_started`.
4. **HUD Freshness/Spoiled Indicators, `CHANGELOG.md` & QA Verification**: Visual freshness bars/percentages & spoiled markers in `chonoi/web/index.html` (`>= 18px` at `1280x720`, `>= 30 FPS`, off in `headless`), `CHANGELOG.md` breaking-change guide, migrated P1–P3 regression tests, and `phase-3` tag before `2:30`.

## Technical Context

- **Language/Version**: Python 3 standard library only (`chonoi/`) + HTML5 Canvas / ES6 JS (`chonoi/web/index.html`).
- **Precision Representation**: Represent internal freshness as `fresh_units: int` (`1.0` fresh = `240` units via `FRESH_SCALE = 240`, so `0.5 / 60 = 2 / 240` in `gather` and `0.25 / 60 = 1 / 240` in `quan`). Serialize `fresh` to JSON with `round(units / 240, 6)` (preserves exact `< 30` vs `>= 30` discrimination across `--inventory-out` -> `--inventory` roundtrips).
- **Performance Goal**: `22,200` ticks/day headless `<= 20s` (currently ~1.2s; integer unit decay adds negligible O(N) overhead where `N <= 12` in `gather` and bounded raw stock in `quan`).
- **Optional Extensions (`current`, `reservations`)**: Per TICKET-03 Section 2, optional for 4-person teams; strictly deferred until all core v1.2 DoD gates pass.

## Impact Analysis & Schema Migration Decision

| Module / Layer | Files to Change | Key Behavioral / Schema Change | Tests Affected (Adapt with Commit Reason) | Owner |
|---|---|---|---|---|
| **Contract, Inventory & Gather Freshness** | `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/sim/gather.py`, `chonoi/scenario.py` (`_validate_gather`) | `contract_version: "1.2"`, `freshness` block, `FRESH_SCALE = 240`, `[{"id","kind","fresh"}]`, `I1..` IDs, `0.5/s` decay at step start, `spoiled(hold)`, strict v1.2 rejection (exit `2`) of count-dict inventory. | `tests/test_gather_harvest.py`, `tests/test_gather_survival.py`, `tests/test_gather_fish_v11.py`, `tests/test_python_starter_units.py` + new `tests/test_freshness_gather_v12.py` | `duyhale95` (Slice 1) |
| **Monsters LIFO & Multi-Day Item IDs** | `chonoi/sim/monsters.py`, `chonoi/sim/day.py`, `docs/clarify.md` | `monster_hit.lost` & `faint.lost` emit LIFO item dicts; `DaySim` owns shared monotonic `item_ids`; Day 1 keeps scenario `hold` IDs, Day 2+ allocates fresh IDs; zero extra decay on handoff tick. | `tests/test_gather_monsters.py`, `tests/test_day_shop_pause.py` (`DaySim` assertions) + new `tests/test_monsters_day_v12.py` | `missher03` (Slice 2) |
| **Quan Freshness, ID Reservations, Pricing & Scenario** | `chonoi/sim/quan.py`, `chonoi/scenario.py` (`_validate_quan`, `prepare_quan_customers`), `docs/verification/phase-3.md`, `docs/proof/phase-3/` | Individual-item `stock`, `0.25/s` decay, `spoiled(stock)`, re-reserve once by `(order_tick, id_key(table_id))` -> `unfulfillable`, freshest-first + `id_key`, `cook_started.items` sorted `(kind, id_key)`, `base_price` floor by avg fresh, `tip` on locked `base_price`. | `tests/test_quan_customers.py`, `tests/test_quan_service.py`, `tests/test_quan_v11.py`, `tests/test_smoke_p1.py` + new `tests/test_quan_freshness_v12.py` | `Limdim1604` (Slice 3) |
| **Shop, Runner, Live HUD & Release** | `chonoi/sim/shop.py`, `chonoi/runner.py`, `chonoi/web/index.html`, `CHANGELOG.md`, `AGENTS.md`, `docs/retro.md` | `ShopSim` preserves v1.2 `stock` without decay; `runner.py` wires `item_ids` / `contract_version`; HUD shows item freshness & spoiled indicator; `CHANGELOG.md` breaking change guide; final gate & tag `phase-3`. | `tests/test_day_shop_pause.py` (`ShopSim`), `tests/test_live.py` (if needed) + new `tests/test_v12_handoff_ui.py` | `Lmeo2h` (Slice 4) |

### Keeping `main` Green During Migration (Phased Toggle)
1. **Minutes 0–7 (Foundation Adapter)**: `duyhale95` lands `chonoi/inventory.py` (supporting both `validate_items_v12` / `FRESH_SCALE = 240` AND temporary v1.1 fallback when `contract_version == "1.1"`) and `chonoi/contract.py` (`freshness` validation). `game.contract.json` temporarily stays `"1.1"` (or Slice 1 sets `"1.2"` after Slice 3 is ready) OR Slice 1 -> Slice 2 -> Slice 3 merge rapidly in sequence (`minutes 12–22`) where Slice 3 flips `"contract_version": "1.2"` once both `gather` and `quan` speak v1.2!
   - **Recommended safest path**: `duyhale95` lands `inventory.py` v1.2 helpers + `contract.py` (`freshness` allowed in 1.1 & required in 1.2) by **minute 7** (`main` stays 104/104 green!). Then Slice 1 (`GatherSim`) + Slice 2 (`monsters`/`day`) + Slice 3 (`QuanSim`/`scenario`) migrate all callers and flip `contract_version: "1.2"` in `game.contract.json` when Slice 3 merges (at **minute 20–22**), followed immediately by Slice 4 (`shop`/`runner`/`web`/`CHANGELOG`)!
   - **Under `contract_version: "1.2"`**: `read_inventory()` strictly requires `[{"id", "kind", "fresh"}]` and rejects count-based `{"items": {"ca_loc": 1}}` with `BadInput` (exit code `2`).

## Processing Order Alignment (TICKET-03)

1. **`GatherSim.step` (v1.2)**:
   1. Decrement timers (`time_left_ticks`, `invuln_ticks`, `catch_cd_ticks`, node `regrow_ticks` -> `node_regrown`), increment `phase_tick`, **and decay freshness of items currently in `hold` (`-2` units = `-0.5/s`)**; emit `spoiled(item_id, kind, location="hold")` in `id_key` order for items crossing `>= 30` to `< 30` (before rounding).
   2. *(Extension hook: flood current if enabled)*
   3. Player move + survival (`dive`/`surface`, `oxygen_empty`, choke-on-zero -> if `hp == 0`, LIFO clear `hold` into `faint.lost` + `gather_end("fainted")`, return).
   4. Monsters (`step_monsters` -> `monster_hit.lost` / `faint.lost` as LIFO item dicts; if `hp == 0`, `gather_end("fainted")`, return).
   5. `interact` (dock check first -> `docked`; else harvest surface node creating new item `I_k` with `fresh = 100`, decaying from next tick).
   6. `catch` (catch fish creating `yield` new items `I_k...` with `fresh = 100`, decaying from next tick).
   7. `time_left_ticks <= 0` -> `gather_end("time")`.
   8. If `not self.done` and `random_fish`: fish swim & fish spawn.
2. **`QuanSim.step` (v1.2)**:
   1. Decrement `time_left_ticks`, `phase_tick += 1`, customer patience, stove cook/ready, eat timers.
   2. **Decay freshness of ALL raw `stock` items (`-1` unit = `-0.25/s`, including reserved items)**; emit ALL `spoiled(item_id, kind, location="stock")` events in `id_key` order for items crossing `< 30`.
   3. **After all `spoiled` events**: find `reserved` customers holding any newly spoiled ID, sort by `(order_tick, id_key(table_id))`, release all reserved IDs of that customer, and attempt 1 re-reservation from unreserved unspoiled (`fresh >= 30`) stock by `(-fresh_units, id_key(id))`; if insufficient, set `reserved = []`, `order_status = "unfulfillable"`.
   4. Player move + `interact` (at most 1 target `(dist, stove<table, id_key)`): `cook_started` consumes exact reserved IDs, sorts `items` by `(kind, id_key(id))`, locks `base_price = math.floor(list_price * avg_fresh / 100)`; `served` computes `tip = math.floor(base_price * tip_rate)` on locked `base_price`.
   5. Settle finished eating (`paid`), expire waiting customers (`customer_left`) / closing (`_settle_closing`), and if `time_left_ticks > 0`, spawn due customer at `120 + 900 * k` using `day_plan` filter + unreserved unspoiled stock.

## 35-Minute Sprint Schedule (TICKET-03 Section 3)

| Window | Elapsed | Focus & Milestones | Owners |
|---|---|---|---|
| `1:55–2:02` | `0–7m` | **Impact Analysis & Adapter Foundation**: Land `docs/plan/phase-3.md`, `chonoi/inventory.py` v1.2 helpers (`FRESH_SCALE=240`), `chonoi/contract.py` (`freshness` validation); all 4 write Test-First v1.2 skeletons in parallel. | `duyhale95` (leads), all |
| `2:02–2:15` | `7–20m` | **Parallel Core Build & Sequential Merge 1→2→3**: `gather.py` freshness (Slice 1) → `monsters.py`/`day.py` LIFO & `item_ids` (Slice 2) → `quan.py`/`scenario.py` v1.2 + flip `contract_version: "1.2"` (Slice 3). | `duyhale95`, `missher03`, `Limdim1604` |
| `2:15` | `20m` | **Inventory Handoff Smoke (`T018`)**: 2-process `gather --inventory-out` → `quan --inventory --ticks 0` + `--mode day` handoff check; save `docs/proof/phase-3/integration.md`. | `Limdim1604` + `Lmeo2h` |
| `2:15–2:25` | `20–30m` | **Slice 4 UI/Shop, `CHANGELOG.md` & Regression**: `shop.py`, `runner.py`, `web/index.html` freshness HUD (`>= 18px`, `>= 30 FPS`), `CHANGELOG.md`, `AGENTS.md`, `docs/retro.md`, full P1–P3 regression. | `Lmeo2h` + all |
| `2:25–2:30` | `30–35m` | **Final Gates & Tag `phase-3`**: `unittest discover`, `check_team.py`, `22,200`-tick perf (`<= 20s`), SHA-256 determinism, `docs/verification/phase-3.md`, push tag `phase-3` before `2:30`. | `Lmeo2h` + `duyhale95` |
