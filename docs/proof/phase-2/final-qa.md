# Bằng chứng QA tổng hợp Phase 2 (trên `main`)

Ngày 2026-11-21 (UTC+7). Windows PowerShell, Python 3.12, Test Contract `v1.1`, sau khi hợp nhất đầy đủ 4 Vertical Slices (`PR #6`, `PR #7`, `PR #8`, `PR #9`) vào `main` (`0dc8d1c`).

| Kiểm tra | Lệnh | Kết quả quan sát |
|---|---|---|
| Toàn bộ unit & headless test (`P1 + P2`) | `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v` | `Ran 104 tests in 18.691s — OK` (0 fail, 0 skip, 0 error) |
| Kiểm danh sách thành viên | `python tools/check_team.py` | `OK: 4 thành viên: duyhale95, missher03, Limdim1604, Lmeo2h` |
| Tất định `--mode gather` (`600` ticks, `--seed 1`) | `python -m chonoi.headless --mode gather --seed 1 --ticks 600 --out ...` (2 lần) | `SHA-256` trùng khớp: `DD829853118959189FD363E53C8092E68E5C6CFB6392CC66CCDC1B073B977344` |
| Tất định `--mode quan` (`1200` ticks, `--seed 1`) | `python -m chonoi.headless --mode quan --seed 1 --ticks 1200 --out ...` (2 lần) | `SHA-256` trùng khớp: `4F157EF80A5CD31E5A88958ABFBABFD32442BC930C072F06E2874B398EE6B65B` |
| Tất định `--mode day --days 1` (`22,200` ticks, `--seed 1`) | `python -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out ...` (2 lần) | `SHA-256` trùng khớp: `EC8F4571D8B6E037DB9DC365A41E9C1AEBC1DC2980F89B485D3C73868C4D05ED` |
| Hiệu năng 1 ngày `22,200` ticks (`<= 20s`) | `Measure-Command { python -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out ... }` | `1.225s` (`<= 20s`); dòng `end`: `{"type":"end","ticks":22200,"sim_tick":22200,"mode":"day","state":"finished","reason":"days_complete","money":0,"earned":0,"reputation":3.0,"score":300,"days_completed":1}` |
| Smoke vòng lặp 5 ngày | `python -m chonoi.headless --mode day --days 5 --seed 1 --ticks 111000 --out ...` | Mã thoát `0`, `reason: "days_complete"`, `days_completed: 5` |
| Live HTTP & Web UI | `tests/test_live.py` + kiểm mã nguồn `chonoi/web/index.html` | `test_live.py` OK; `chonoi/web/index.html` đủ Menu, DayIntro, EveningIntro, DayResult, Summary, Pause (`Esc`/`P`), Shop UI, HUD v1.1 (`18px+ sans-serif` ở `1280x720`) |
