# Smoke bàn giao kho Phase 3

Ngày 2026-11-21, Windows PowerShell, Python 3.12.2. Nhánh Slice 3 lấy từ `origin/main` ở `608baaa`, còn Contract 1.1.

`dock.json`: `{"gather":{"hold":["ca_loc","bong_sung"]}}`. `inputs.json`: `{"frames":[{"tick":0,"interact":true}]}`.

```powershell
python -m chonoi.headless --mode gather --seed 1 --ticks 1 --scenario dock.json --inputs inputs.json --inventory-out stock.json --out gather.jsonl
python -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory stock.json --out quan.jsonl
```

Cả hai lệnh trả mã 0. Kho ở snapshot tick 0 khớp file: `{"bong_sung":1,"ca_loc":1}`.

Đây là lần chạy thử checklist phút 20 trên preset cũ. Cần lặp lại sau khi bật v1.2 bằng fixture `hold` dạng cá thể. Khi đó đối chiếu mảng `items` với `stock` theo `id`, `kind`, `fresh` và chạy thêm ca kho đếm cũ trả mã 2 trước khi tạo output.
