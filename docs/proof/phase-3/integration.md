# Smoke bàn giao kho Phase 3

Ngày 2026-11-21, Windows PowerShell, Python 3.12.2. Nhánh Slice 3 lấy từ `origin/main` ở `608baaa`, còn Contract 1.1.

`dock.json`: `{"gather":{"hold":["ca_loc","bong_sung"]}}`. `inputs.json`: `{"frames":[{"tick":0,"interact":true}]}`.

```powershell
python -m chonoi.headless --mode gather --seed 1 --ticks 1 --scenario dock.json --inputs inputs.json --inventory-out stock.json --out gather.jsonl
python -m chonoi.headless --mode quan --seed 1 --ticks 0 --inventory stock.json --out quan.jsonl
```

Cả hai lệnh trả mã 0. Kho ở snapshot tick 0 khớp file: `{"bong_sung":1,"ca_loc":1}`.

## Sau khi Slice 1 merge (`7c31363`)

Chạy lại hai lệnh trên với fixture `hold` chứa `I10/ca_loc/30` và `I2/bong_sung/100`. Cả hai lệnh trả mã 0. Gather phát `spoiled` cho `I10` ở tick 1 trước khi cập bến. Hai bản ghi xuất theo thứ tự `I2, I10`.

```text
file kho:       [{"id":"I2","kind":"bong_sung","fresh":99.991667},{"id":"I10","kind":"ca_loc","fresh":29.991667}]
snapshot tick 0: [{"id":"I2","kind":"bong_sung","fresh":99.992},{"id":"I10","kind":"ca_loc","fresh":29.992}]
Đơn vị 1/240: I2/bong_sung/23998, I10/ca_loc/7198, giống nhau ở file kho, gather_end và snapshot.
```

JSONL dùng 3 chữ số thập phân, bộ ghi file kho dùng 6 chữ số. Hai luồng phục hồi chính xác cùng đơn vị độ tươi; biểu diễn số thập phân giữa file kho và JSONL có khác biệt. Hai lượt Quán 1.200 tick cùng seed và file kho giống từng byte, SHA-256 `48ca18b046d2758e111e97d6566d09ed0b2a9af59e9110f000629e4daf66e4f9`.
