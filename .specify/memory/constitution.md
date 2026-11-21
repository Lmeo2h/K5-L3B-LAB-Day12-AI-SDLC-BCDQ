# Quán Ăn Chợ Nổi — Project Constitution

## Core Principles

### I. Determinism & Seeded RNG
Mọi số ngẫu nhiên trong mô phỏng bắt buộc phải đi qua `Streams` (`chonoi/rng.py`, tách luồng theo tên mục đích như `rng.get("<luồng>")`) để việc thêm tính năng không làm lệch chuỗi ngẫu nhiên của luồng khác. Tuyệt đối không dùng `random` toàn cục và không dùng đồng hồ hệ thống. Với cùng `--seed`, `--inputs`, `--scenario` và `--inventory`, đầu ra JSONL (tại `tick_hz = 60`, làm tròn 3 chữ số) và file kho phải tái lập giống hệt nhau từng byte.

### II. Single Source of Truth for Tuning
Mọi thông số cân bằng game, kích thước vùng chơi, tọa độ mặc định, tốc độ, bán kính tương tác, thời lượng và công thức món ăn chỉ được khai báo trong `game.contract.json` (`tuning.*`). Luật chơi trong `chonoi/sim/gather.py` và `chonoi/sim/quan.py` phải đọc từ `tuning`, tuyệt đối không hard-code số liệu cân bằng trong mã nguồn mô phỏng.

### III. Canonical IDs & Entity Ordering
Mọi tập hợp thực thể khi duyệt xử lý theo thứ tự ưu tiên hoặc xuất ra snapshot phải được sắp xếp nhất quán qua `ids.sort_by_id` (`chonoi/ids.py`, sắp theo tiền tố và hậu tố số để `F2` đứng trước `F10`). Mọi thực thể sinh mới trong lượt chơi phải được cấp phát ID qua `IdAllocator` (`reserve()` toàn bộ ID nạp từ tuning/scenario trước khi gọi `new()`).

### IV. Contract Lock & Clarification Discipline
Các hợp đồng tích hợp trong `docs/contracts/`, `game.contract.json`, schema file kho v1.0 (`{"items": {id: int >= 0}}`), định dạng JSONL và các trường snapshot/sự kiện công khai được khóa theo phase. Không tự ý sửa hợp đồng khi chưa thông báo cả nhóm và ghi lại lý do. Khi gặp điểm mơ hồ hoặc thiếu chi tiết từ PRD, không tự bịa yêu cầu: phải ghi vào `docs/clarify.md` và hỏi PO/giảng viên.

### V. Vertical Slices, Small PRs & Honest Testing
Tính năng được chia thành các Vertical Slice độc lập, mỗi thành viên phụ trách một lát cắt rõ ràng; mỗi PR/lát cắt giữ quy mô gọn gàng (<= ~400 dòng thay đổi). Không sửa test cho xanh khi luật mô phỏng sai — phải sửa luật hoặc ghi rõ lý do đổi test trong commit. Mở rộng sáng tạo được khuyến khích ở phần hiển thị/trải nghiệm nhưng phải tắt ở chế độ `headless` và không phá vỡ phần lõi.

## Technical & Verification Constraints

- **Ranh giới mã nguồn**: Khung giảng viên cấp (`chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`) hạn chế sửa (trừ phần kiểm mâu thuẫn `scenario.py` hoặc kiểm tuning `contract.py` theo `TODO(nhóm)` đã thống nhất). Trọng tâm lập trình của nhóm nằm ở `chonoi/sim/gather.py`, `chonoi/sim/quan.py` và kiểm thử bổ sung trong `tests/`.
- **Kiểm chứng bắt buộc (Headless & Unit Tests)**: Mọi lát cắt sau khi hoàn thiện đều phải chạy qua:
  - Bộ test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
  - Chế độ headless: `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`
  - Kiểm lỗi đầu vào/mâu thuẫn scenario phải trả về mã thoát `2` trước khi ghi bất kỳ file đầu ra nào.

## Development Workflow & Quality Gates

- Trước khi code, đọc kỹ spec của phase, hợp đồng tích hợp (`docs/contracts/README.md`) và các file cấu hình liên quan.
- Nhánh chính phải luôn ở trạng thái chạy được và pass test, đặc biệt tại các mốc gắn tag (`phase-1` … `phase-4`).
- Cập nhật `AGENTS.md` qua các phase; lưu bằng chứng kiểm chứng tại `docs/verification/phase-n.md` (hoặc `docs/proof/`), nhật ký AI tại `docs/ai-usage-log.md`, và nhật ký cá nhân tại `docs/members/<handle>.md`.

## Governance

Hiến chương (Constitution) này là quy chuẩn ưu tiên cao nhất cho mọi thành viên và agent AI tham gia dự án. Mọi thay đổi đối với hiến chương hoặc hợp đồng tích hợp cần được Integrator và nhóm thống nhất, ghi nhận lý do rõ ràng trong tài liệu dự án.

**Version**: 1.0.0 | **Ratified**: 2026-11-21 | **Last Amended**: 2026-11-21
