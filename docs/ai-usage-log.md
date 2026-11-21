# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | `duyhale95` (Hà Lê Duy) | Antigravity / Gemini 4 Hydrogen (High) | Slice 1 (`gather` sinh tồn: `dive`/`surface`, oxy trừ/hồi, `oxygen_empty`, `zero_oxy_ticks`/`choke`, `faint` rỗng giỏ, helper giỏ LIFO + `tests/test_gather_survival.py`) | ~25k tokens | Lần chạy đầu `test_gather_survival.py` AI dùng walrus `:=` trực tiếp làm giá trị dict gây `SyntaxError`, đã sửa lại biến cục bộ; browser agent bị chặn cross-site iframe khi đọc PRD-0 nên đã ghi các điểm payload/quy tắc giả định vào `docs/clarify.md` để PO chốt. |
