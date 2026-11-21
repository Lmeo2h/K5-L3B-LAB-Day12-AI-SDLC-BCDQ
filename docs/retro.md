# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: Chia 4 vertical slices độc lập (`gather` cá bơi/choke, `monsters.py`, `quan` v1.1 + 2 skills, `day.py`/`shop.py`/`pause`/UI) giúp phát triển song song ít xung đột; benchmark headless `22,200` ticks chỉ mất ~1.15s (`<= 20s`) và tất định từng byte.
- Điều tệ: Cross-site iframe trên lab board làm browser agent không đọc trực tiếp được TICKET-02; trên Windows alias `python3` gây `WinError 1920` với các test gọi `headless_cmd` qua `python3`.
- 1 hành động cho Phase 3: Chốt và xuất bản tóm tắt TICKET ngay đầu phase vào `docs/clarify.md` để mọi agent đọc cục bộ không bị nghẽn cross-site iframe, đồng thời duy trì rebase sớm Contract trước phút 8.

## Phase 3 (nhanh)
- Điều tốt: Chuyển schema kho cá thể `v1.2` (`FRESH_SCALE=240`) được tách rõ theo 4 slice và có `CHANGELOG.md` hướng dẫn migrate fixture; HUD độ tươi/ươn hiển thị trực quan mà vẫn giữ `headless` sạch và `22,200` ticks ~1.2s.
- Điều tệ: Khi chuyển breaking schema giữa các slice song song, phần test tích hợp liên pha cần đợi đủ Slice 1–3 merge mới kiểm tra end-to-end được.
- 1 hành động cho Phase 4: Chạy smoke bàn giao 2 tiến trình (`gather --inventory-out` -> `quan --inventory`) ngay tại mốc phút 20 sau khi Slice 3 merge để phát hiện lệch schema sớm.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
  - **Đã làm:** Nhóm đã chuẩn hóa quy trình chốt và công bố ngay làm rõ PRD/TICKET vào `docs/clarify.md` (mục 1–7) và SpecKit (`specs/001..004/`) ở đầu mỗi phase để các agent đọc cục bộ không bị nghẽn cross-site iframe, đồng thời duy trì rebase/merge tuần tự Slice 1 → 2 → 3 → 4.
  - **Còn vướng:** Alias `python3` trên Windows không trỏ tới `python` nên `tests/test_smoke_p1.py` gọi `headless_cmd` vẫn cần chạy trên Linux/CI hoặc dùng `sys.executable` trong unit test mới.
- Điều tốt / điều tệ:
  - **Điều tốt:** Kiến trúc Vertical Slices không chồng lấn file giúp cả 4 thành viên giữ tiến độ đúng hạn từng tag `phase-1`..`phase-3`; chế độ `headless` tất định 100% và `22,200` ticks chỉ ~1.2s; 2 skill nhóm (`.agents/skills/`) và Test-First phát hiện sớm lỗi schema/rounding.
  - **Điều tệ:** Chuyển breaking schema v1.2 ở Phase 3 đòi hỏi phải đợi Slice 1–3 cùng lên mới chạy được end-to-end 2 tiến trình.
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
  - **Commits trên `main` (tính đến hợp nhất đủ 4 PR Phase 4 tại `5e9bbda`, tổng 97 commits = 88 commits của nhóm + 9 commits starter của giảng viên `Hai Duong`):** `duyhale95` (gồm `HLD`: 40 commits, gồm 20 non-merge), `Limdim1604` (gồm `Nguyễn Thiên Bảo`/`NguyenThienBao`: 22 commits, gồm 17 non-merge), `Lmeo2h` (`TanChau`: 14 commits non-merge), `missher03` (12 commits non-merge). Riêng Phase 4 mỗi người có ≥ 3 commit không-merge đúng quy định (`duyhale95` 4, `Limdim1604` 5, `missher03` 3, `Lmeo2h` 3).
  - **Đọc code của nhau:** Mỗi PR qua `.github/pull_request_template.md`, cặp dự phòng (`duyhale95` ↔ `missher03`, `Limdim1604` ↔ `Lmeo2h`) và QA Lead kiểm chéo test + diff trước khi merge.
  - **Token ước tính (theo `docs/ai-usage-log.md`, P1–P4):** `duyhale95` ~115k, `Lmeo2h` ~100k, `missher03` ~69k, `Limdim1604` (Codex, chưa đo được).
- Một lần AI sai và cách nhóm phát hiện:
  - Ở Phase 1 (`missher03`), AI gọi sai signature `InputState(interact_edge=True)` thay vì `InputState(move, held, edges)` — phát hiện ngay khi chạy `unittest` Test-First; ở Phase 2 (`missher03`), AI đặt tọa độ test `chase` cách `[64,24]` là `[56,15]` (`~12.04 m > 10 m`) khiến test `FAIL` và nhóm tự tính lại khoảng cách Euclid sang `[58,18]`; ở Phase 3 (`duyhale95`), `jsonl.py` làm tròn 3 chữ số khác `write_inventory` 6 chữ số nên nhóm kiểm chứng đọc lại theo `240`-unit.
- Nếu làm lại, đổi gì: Chốt script/wrapper `python` đa nền tảng trong test helper ngay từ Phase 1 và viết sẵn smoke 2 tiến trình tự động ngay khi mở phase đổi schema.
