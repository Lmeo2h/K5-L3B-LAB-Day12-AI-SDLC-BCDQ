# Implementation Plan: Quán Ăn Chợ Nổi — Phase 4 (Phát hành v1.0.0)

**Branch**: `004-phase-4-release` | **Date**: 2026-11-21 | **Spec**: [spec.md](spec.md)

## Summary

Deliver **Test Contract v1.3** and **GitHub Release v1.0.0** within the **30-minute (`2:30–3:00`)** sprint without breaking any v1.2 gameplay/inventory/JSONL contracts:
1. **Contract v1.3 + `soak_cmd` (`duyhale95`)**: Upgrade `game.contract.json` (`contract_version: "1.3"`, `"bench_cmd": "python3 -m chonoi.bench"`, `"soak_cmd": "python3 -m chonoi.soak"`), validate in `chonoi/contract.py`, fix `DaySim._get_day_plan` to cycle D1–D5 via `(day - 1) % len(plans)` for Days 6–10, and build `chonoi/soak.py` (`--seed`, `--days`, `--out soak.json`).
2. **3 Alerts + High-Contrast Mode + Retro Coordination (`missher03`)**: Add explicit icon+text alerts for monster proximity/chase, low/empty oxygen, and impatient customer (`patience < 25%`) plus high-contrast toggle (`C`/`H` & UI button) in `chonoi/web/index.html`; coordinate `docs/retro.md` (reviewing Phase 2 action) & `docs/clarify.md`.
3. **Render Benchmark (`bench_cmd`) + QA (`Limdim1604`)**: Implement `chonoi/bench.py` (`1280×720` default gather scene, `3s` warmup + `duration`s measure, computing `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`), capture `docs/proof/phase-4/{bench.json,soak.json}`, and complete `docs/verification/phase-4.md`.
4. **Packaging, Docs & Release (`Lmeo2h`)**: Finalize `README.md` (`<= 3` clean-clone UI launch commands on macOS/Linux), `LICENSE` (MIT), `CREDITS.md`, `CHANGELOG.md` (Phase 1–4), `AGENTS.md`, build release archive (`tools/package_release.py`), collect all 4 `docs/members/<handle>.md` (`<= 200` words), push tag **`phase-4`** and publish **GitHub Release `v1.0.0`**.

## File Ownership (Zero Overlap Across 4 Branches)

| Owner | Branch | Owned Files | Do Not Touch |
|---|---|---|---|
| `duyhale95` | `feat/p4-s1-contract-soak` | `game.contract.json`, `chonoi/contract.py`, `chonoi/sim/day.py`, `chonoi/soak.py`, `tests/test_soak_v13.py`, `docs/members/duyhale95.md` | `chonoi/bench.py`, `chonoi/web/`, `README.md`, `CHANGELOG.md` |
| `missher03` | `feat/p4-s2-warnings-contrast` | `chonoi/web/index.html`, `tests/test_ui_warnings_v13.py`, `docs/clarify.md`, `docs/retro.md`, `docs/members/missher03.md` | `chonoi/bench.py`, `chonoi/soak.py`, `game.contract.json`, `chonoi/contract.py` |
| `Limdim1604` | `feat/p4-s3-bench-qa` | `chonoi/bench.py`, `tests/test_bench_v13.py`, `docs/proof/phase-4/*`, `docs/verification/phase-4.md`, `docs/members/Limdim1604.md` | `chonoi/soak.py`, `chonoi/web/`, `README.md`, `docs/retro.md` |
| `Lmeo2h` | `feat/p4-s4-package-release` | `README.md`, `LICENSE`, `CREDITS.md`, `CHANGELOG.md`, `AGENTS.md`, `tools/package_release.py`, `docs/members/Lmeo2h.md` | `chonoi/bench.py`, `chonoi/soak.py`, `chonoi/sim/*` |
