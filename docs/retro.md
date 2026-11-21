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
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
