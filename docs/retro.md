# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: Chia 4 vertical slices độc lập (`gather` cá bơi/choke, `monsters.py`, `quan` v1.1 + 2 skills, `day.py`/`shop.py`/`pause`/UI) giúp phát triển song song ít xung đột; benchmark headless `22,200` ticks chỉ mất ~1.15s (`<= 20s`) và tất định từng byte.
- Điều tệ: Cross-site iframe trên lab board làm browser agent không đọc trực tiếp được TICKET-02; trên Windows alias `python3` gây `WinError 1920` với các test gọi `headless_cmd` qua `python3`.
- 1 hành động cho Phase 3: Chốt và xuất bản tóm tắt TICKET ngay đầu phase vào `docs/clarify.md` để mọi agent đọc cục bộ không bị nghẽn cross-site iframe, đồng thời duy trì rebase sớm Contract trước phút 8.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
