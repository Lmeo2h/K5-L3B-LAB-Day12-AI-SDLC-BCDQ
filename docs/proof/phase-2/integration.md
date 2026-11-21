# Smoke chuyển kho Phase 2

Chạy ngày 2026-11-21 (UTC+7) trên nhánh `feat/p2-s3-quan-v11-qa`, gốc `origin/main` ở `f71785e`. Đây là ca smoke theo checklist phút 20 của TICKET-02. Repo lúc chạy dùng Contract 1.0. Nhánh cá sấu đã có trên remote, Contract 1.1 và CLI `day` chưa vào `main`.

Fixture `dock.json` chứa `{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}` và `input.json` chứa `{"frames":[{"tick":0,"interact":true}]}`.

```powershell
python -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs input.json --ticks 1 --out gather.jsonl --inventory-out stock.json
python -m chonoi.headless --mode quan --seed 42 --inventory stock.json --ticks 0 --out quan.jsonl
```

Cả hai tiến trình trả mã 0. Kết quả đối chiếu thực tế:

```text
inventory={"bong_sung":2,"ca_loc":1} snapshot_tick=0 stock={"bong_sung":2,"ca_loc":1} same=True
{"type":"event","tick":1,"phase":"gather","name":"gather_end","data":{"reason":"docked","inventory":{"items":{"bong_sung":2,"ca_loc":1}}}}
```
