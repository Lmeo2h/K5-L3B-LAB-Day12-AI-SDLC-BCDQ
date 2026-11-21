---
name: chonoi-slice-qa
description: Use when implementing a Chợ Nổi ticket test-first, checking an integration milestone, or recording phase regression and benchmark evidence.
---

# QA cho một lát Chợ Nổi

1. Chọn AC từ TICKET. Viết fixture nhỏ tái hiện luật biên. Chạy test trước khi sửa code và ghi lỗi thấy được. Chạy lại test lát và suite sau khi sửa.
2. Ở mốc tích hợp, chạy hai tiến trình `gather --inventory-out` rồi `quan --inventory`. So `items` từ file kho với `stock` trong snapshot tick 0 của quán. Ghi kết quả theo commit đang chạy và liệt kê lát còn chờ merge.
3. Chạy hồi quy khi preset mới đã vào nhánh. Lưu lý do và báo người sở hữu nếu test cũ trông đợi thông số phase trước. Trên Windows, nếu suite gọi `python3` và trỏ vào Microsoft Store, dùng Python CLI thật qua PATH cho lần chạy và ghi lại thiết lập.

```powershell
$env:PYTHONPATH = 'tests;.'
$env:PYTHONUTF8 = '1'
python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Suite failed ($LASTEXITCODE)" }
python tools/check_team.py
if ($LASTEXITCODE -ne 0) { throw "Team check failed ($LASTEXITCODE)" }
```

4. Sau khi CLI `day` được tích hợp, đo Phase 2 bằng lệnh dưới. Kiểm mã thoát và dòng `end` xác nhận hoàn thành một ngày trước khi so ngưỡng `20 s`.

```powershell
$outFile = [System.IO.Path]::GetTempFileName()
try {
    $elapsed = Measure-Command {
        python -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out $outFile
        if ($LASTEXITCODE -ne 0) { throw "Day benchmark failed ($LASTEXITCODE)" }
    }
    $end = Get-Content -LiteralPath $outFile -Tail 1 | ConvertFrom-Json
    if ($end.type -ne 'end' -or $end.state -ne 'finished' -or
        $end.reason -ne 'days_complete' -or $end.days_completed -ne 1) {
        throw 'Day benchmark did not complete one day'
    }
    $elapsed.TotalSeconds
    if ($elapsed.TotalSeconds -gt 20) { throw 'Day benchmark exceeded 20 seconds' }
} finally {
    Remove-Item -LiteralPath $outFile
}
```

5. Ghi commit, preset, Python, lệnh, mã thoát, số test đạt/bỏ qua và kết quả đo vào `docs/proof/phase-n/`. Liên kết từng AC từ `docs/verification/phase-n.md`. Với CLI, preset hay lát chưa có, đánh dấu phần kiểm chứng đó là đang chờ. Kiểm lại trên commit bàn giao trước khi gắn tag.
