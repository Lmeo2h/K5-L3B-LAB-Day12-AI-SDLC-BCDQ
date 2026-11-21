# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` (PowerShell: `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests -v`)
- Headless: `python3 -m chonoi.headless --mode gather|quan|day [--days 1..5] --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan|day [--days 1..5]` (mở địa chỉ in ra; WASD, E, Space, Esc/P, R)
- Kiểm thành viên: `python3 tools/check_team.py`

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/{gather,monsters,quan,day,shop}.py` (Test Contract `v1.1`).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- `chonoi-contract-guard` (`.agents/skills/chonoi-contract-guard/SKILL.md`): Dùng khi sửa hoặc rà soát simulation, scenario, tuning (`game.contract.json`), cấp/sắp ID (`IdAllocator`/`sort_by_id`), `Streams`, hoặc đối chiếu SHA-256 JSONL headless tất định.
- `chonoi-slice-qa` (`.agents/skills/chonoi-slice-qa/SKILL.md`): Dùng khi làm ticket theo Test-First, chạy tích hợp/hồi quy toàn suite, kiểm hiệu năng `22,200` ticks (`<= 20s`), và ghi bằng chứng vào `docs/proof/` & `docs/verification/`.
