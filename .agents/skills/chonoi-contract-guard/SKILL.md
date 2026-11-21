---
name: chonoi-contract-guard
description: Use when changing or reviewing Chợ Nổi simulation, scenario fixtures, tuning, entity IDs, or deterministic headless output.
---

# Kiểm Test Contract Chợ Nổi

1. Đọc TICKET của phase, `AGENTS.md`, hợp đồng kho và `game.contract.json`. Kiểm phiên bản trên nhánh và trên `origin/main`. Khi preset thuộc slice khác, dùng fixture riêng từ TICKET để test sớm và ghi rõ nguồn dữ liệu.
2. Xem diff bằng `git diff origin/main...HEAD -- chonoi game.contract.json` và `git diff -- chonoi game.contract.json`. Đối chiếu từng số luật với tuning, kể cả Hz và chu kỳ tính bằng tick. Giữ nguyên tên và payload event mà contract yêu cầu.
3. Dùng `Streams.get("purpose")` cho RNG. Sắp ứng viên trước khi chọn, dùng `sort_by_id` hoặc `id_key` đúng chỗ và cấp ID bằng `IdAllocator`. Kiểm nhiều seed nếu phép chọn có nhiều ứng viên.
4. Dùng các lệnh sau ở gốc repo. Khi dùng scenario, inputs hoặc inventory, truyền cùng file cho cả hai lần.

```powershell
$paths = 1..3 | ForEach-Object { [System.IO.Path]::GetTempFileName() }
$inventory, $outA, $outB = $paths
try {
    '{"items":{"ca_loc":2,"bong_sung":4}}' | Set-Content -LiteralPath $inventory -Encoding utf8
    foreach ($outFile in @($outA, $outB)) {
        python -m chonoi.headless --mode quan --seed 1 --ticks 1200 --inventory $inventory --out $outFile
        if ($LASTEXITCODE -ne 0) { throw "Headless failed ($LASTEXITCODE)" }
    }
    $a, $b = @($outA, $outB) | Get-FileHash -Algorithm SHA256
    if ($a.Hash -ne $b.Hash) { throw 'JSONL differs with identical inputs' }
    $a.Hash
} finally {
    $paths | Remove-Item -ErrorAction SilentlyContinue
}
```

Lưu phiên bản contract, commit, lệnh, hash và kết quả trong `docs/proof/phase-n/`. So hash kiểm tính tất định. Dùng assertion riêng để kiểm luật, thứ tự event và lỗi mã 2 trước khi ghi output.
