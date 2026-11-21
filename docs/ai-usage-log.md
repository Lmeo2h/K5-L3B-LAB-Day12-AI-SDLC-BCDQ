# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | `missher03` | Antigravity (Gemini 4 Hydrogen Medium) | Slice 2 (`chonoi/sim/gather.py`: `_try_gather_node`, `_try_catch_fish`), `tests/test_gather_harvest.py`, `docs/clarify.md` | ~18k tokens | Lần đầu gọi `InputState(interact_edge=True)` sai signature của `chonoi/inputs.py` (`InputState(move, held, edges)`); đã sửa lại theo `inputs.py` và kiểm chứng pass 100%. |
