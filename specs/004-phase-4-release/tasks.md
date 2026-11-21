---
description: "Phase 4 (TICKET-04, Test Contract v1.3) 30-minute task breakdown across 4 vertical slices"
---

# Tasks: Quán Ăn Chợ Nổi — Phase 4 (Phát hành v1.0.0)

**Timebox**: `30 phút` (`2:30–3:00`), tag `phase-4` & GitHub Release `v1.0.0` before `3:00`.

## Phase 1: Contract v1.3 & Soak Headless (`duyhale95`, Min 0–8)
- [ ] T001 [US1] Upgrade `game.contract.json` to `"contract_version": "1.3"` with `"bench_cmd": "python3 -m chonoi.bench"` and `"soak_cmd": "python3 -m chonoi.soak"`; update `chonoi/contract.py` to validate v1.3 root commands (`duyhale95`)
- [ ] T002 [US1] Fix `DaySim._get_day_plan` in `chonoi/sim/day.py` to cycle D1–D5 for Days 6–10 (`(day - 1) % len(plans)`) (`duyhale95`)
- [ ] T003 [US1] Implement `chonoi/soak.py` (`--seed`, `--days`, `--out soak.json`) with deterministic bot driving `gather -> quan -> shop` and recording `results[]` at each shop close (`duyhale95`)
- [ ] T004 [US1] Write `tests/test_soak_v13.py` (Contract v1.3 validation, 10-day soak `days_completed=10, crashes=0`, D6–D10 plan cycling, repeatability across runs, continuous item IDs) + `docs/members/duyhale95.md` (`duyhale95`)

## Phase 2: 3 Alerts, High-Contrast Mode & Retro (`missher03`, Parallel)
- [ ] T005 [US2] Update `chonoi/web/index.html` with icon+text alerts for Thủy quái gần, Oxy thấp/Hết hơi, Khách sắp giận (`patience < 25%`), and High-Contrast mode toggle (`C`/`H` + UI button) (`missher03`)
- [ ] T006 [US2] Write `tests/test_ui_warnings_v13.py` verifying alert logic/markers and high-contrast toggle (`missher03`)
- [ ] T007 [US2] Update `docs/clarify.md`, `docs/retro.md` (`## Phase 4 (cuối)`: review P2 action, Good/Bad/Next, commit stats, 1 AI error + verification), `docs/ai-usage-log.md`, and `docs/members/missher03.md` (`missher03`)

## Phase 3: Render Benchmark & Final QA (`Limdim1604`, Parallel)
- [ ] T008 [US3] Implement `chonoi/bench.py` (`--seed`, `--duration`, `--out bench.json`) rendering default gather scene at `1280×720` (3s warmup + `duration`s measure, headless browser Canvas primary + stdlib fallback) computing `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms` (`Limdim1604`)
- [ ] T009 [US3] Write `tests/test_bench_v13.py` validating `bench.json` 5-field schema and `p1_low_fps` math (`Limdim1604`)
- [ ] T010 [US3] After Slices 1–2 merge, run `bench --seed 42 --duration 30`, `soak --seed 7 --days 10`, and full P1–P4 regression; save `docs/proof/phase-4/{bench.json,soak.json,qa-summary.md}`, complete `docs/verification/phase-4.md`, and write `docs/members/Limdim1604.md` (`Limdim1604`)

## Phase 4: Packaging, Release Notes, Tag & GitHub Release (`Lmeo2h`, Parallel → Final)
- [ ] T011 [US4] Update `README.md` (clean-clone launch in `<= 3` cmds on macOS/Linux, env/controls/test/headless/bench/soak), add `LICENSE` (MIT), review `CREDITS.md`, update `CHANGELOG.md` (Phases 1–4) & `AGENTS.md` (`Lmeo2h`)
- [ ] T012 [US4] Add `tools/package_release.py` to build runnable release bundle (`dist/chonoi-v1.0.0.zip` / `.tar.gz`), test clean-clone launch (`<= 3` cmds), and write `docs/members/Lmeo2h.md` (`Lmeo2h`)
- [ ] T013 [US4] Merge all 4 PRs, verify `unittest discover`, `check_team.py`, all 4 `docs/members/*.md`, push tag `phase-4`, and publish GitHub Release `v1.0.0` with bundle + release notes before `3:00` (`Lmeo2h` + `duyhale95`)
