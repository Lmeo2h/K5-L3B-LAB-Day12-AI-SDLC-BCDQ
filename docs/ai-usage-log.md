# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | Limdim1604 | Codex (GPT-6) | Đối chiếu PRD-0 mục D–F, viết test trước, cài luật Slice 3, kiểm chứng và rà diff | Chưa đo được | Lần chạy live đầu lỗi bảng mã Windows; chạy lại với `PYTHONUTF8=1` và xác nhận `/` và `/state` trả HTTP 200. |
| Phase 1 | `duyhale95` (Hà Lê Duy) | Antigravity / Gemini 4 Hydrogen (High) | Slice 1 (`gather` sinh tồn: `dive`/`surface`, oxy trừ/hồi, `oxygen_empty`, `zero_oxy_ticks`/`choke`, `faint` rỗng giỏ, helper giỏ LIFO + `tests/test_gather_survival.py`) | ~25k tokens | Lần chạy đầu `test_gather_survival.py` AI dùng walrus `:=` trực tiếp làm giá trị dict gây `SyntaxError`, đã sửa lại biến cục bộ; browser agent bị chặn cross-site iframe khi đọc PRD-0 nên đã ghi các điểm payload/quy tắc giả định vào `docs/clarify.md` để PO chốt. |
