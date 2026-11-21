# TEAM

**Tên nhóm:** BCDQ  **Số người:** 4  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Hà Lê Duy (2A202603851) | `duyhale95` | `sim/gather (Slice 1: oxy/ngạt/giỏ)` | `Scrum / Release (Nhóm trưởng)` | `missher03` |
| Nguyễn Văn Quốc (2A202603864) | `missher03` | `sim/gather (Slice 2: hái/bắt cá/kho)` | `PO (clarify.md)` | `duyhale95` |
| Nguyễn Thiên Bảo (2A202603861) | `Limdim1604` | `sim/quan (Slice 3: khách/giữ chỗ) + qa` | `QA Lead` | `Lmeo2h` |
| Nguyễn Tấn Châu (2A202603846) | `Lmeo2h` | `sim/quan (Slice 4: bếp/phục vụ/tiền)` | `Integrator` | `Limdim1604` |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (≤ 10 dòng)

- Kênh liên lạc: Nhóm chat chung (Discord/Zalo) & swarm board; cập nhật tiến độ tức thời khi mở/gộp PR.
- Khi bất đồng về thiết kế: Thảo luận tối đa 2 phút; chưa chốt được thì Integrator (`Lmeo2h`) quyết định và ghi lại lý do vào PR/commit.
- Khi ai đó trễ hoặc vướng quá 10 phút: Báo ngay trong kênh chung để người dự phòng (`duyhale95` ↔ `missher03`, `Limdim1604` ↔ `Lmeo2h`) nhận tiếp việc.
- Giờ standup giữa phase: Họp nhanh 3 phút ngay trước/sau mỗi mốc gắn tag (`1:00`, `1:55`, `2:30`) để chốt phạm vi và kiểm mâu thuẫn.
- Cách đọc code của nhau: Mỗi PR có ít nhất 1 thành viên đọc chéo (ưu tiên cặp dự phòng hoặc QA Lead kiểm tra trước khi merge).
- Cách làm việc với Git: Chia nhánh ngắn theo slice (`feat/p1-s1-...`), mở PR qua template, pass test + headless rồi merge vào `main`; Integrator gắn tag `phase-1`..`phase-4` và `v1.0.0`.
