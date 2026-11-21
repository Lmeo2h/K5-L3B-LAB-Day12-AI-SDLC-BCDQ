# Bằng chứng QA Slice 3 — 2026-11-21

Chạy trên Windows PowerShell, Python 3.12.2, nhánh `feat/p1-s3-quan-customers`. Dùng `$env:PYTHONPATH='tests;.'` và `$env:PYTHONUTF8='1'`. Suite gọi `python3` từ contract, nên đặt bản sao tạm của executable Python 3.12 trên `PATH` để tránh alias Microsoft Store, rồi dọn sau khi chạy.

| Lệnh | Kết quả quan sát |
|---|---|
| `python -m unittest tests.test_quan_customers -v` | 8 test, `OK`. Trước khi sửa luật, bộ test ban đầu chạy đỏ. |
| `python -m unittest discover -s tests -v` | 41 test, `OK`. |
| `python tools/check_team.py` | `OK: 4 thành viên: duyhale95, missher03, Limdim1604, Lmeo2h` |
| `python -m chonoi.live --mode quan --seed 1` | `/` và `/state` trả HTTP 200. Snapshot `/state` ở tick 1174 có `mode: quan` và hai event `no_dish` ở tick 120 và 1020. |

`python -m chonoi.headless --mode quan --seed 1 --ticks 1200 --out out_p1_s3.jsonl` trả mã 0. Các dòng event và dòng cuối của lượt kho rỗng:

```jsonl
{"type":"event","tick":120,"phase":"quan","name":"no_dish","data":{}}
{"type":"event","tick":1020,"phase":"quan","name":"no_dish","data":{}}
{"type":"end","ticks":1200,"sim_tick":1200,"mode":"quan","state":"playing","reason":"tick_limit","money":0,"earned":0,"reputation":3.0,"score":300}
```
