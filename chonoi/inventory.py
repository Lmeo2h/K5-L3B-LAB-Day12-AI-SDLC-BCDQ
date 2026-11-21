"""File kho v1.2 (TICKET-03): {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}.

Hỗ trợ song song adapter chuyển tiếp v1.1 ({"items": {kind: n}}) khi contract_version == "1.1";
khi contract_version == "1.2" (hoặc gọi read_inventory_v12 / validate_items_v12), từ chối kho đếm cũ
và mọi sai schema bằng BadInput (mã thoát 2).
Ghi: qua file tạm cùng thư mục rồi thay thế nguyên tử, sắp theo id_key, byte-ổn-định.
"""

import json
import math
import os
import tempfile

from .errors import BadInput
from .ids import id_key, sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_P2 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
KINDS = KINDS_P2

FRESH_SCALE = 240
_DEFAULT_CONTRACT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json"
)


def fresh_to_units(fresh: float) -> int:
    """Chuyển độ tươi [0, 100] sang đơn vị nguyên (240 đơn vị / 1 điểm tươi)."""
    return int(round(float(fresh) * FRESH_SCALE))


def units_to_fresh(units: int) -> float:
    """Chuyển đơn vị nguyên về số thực/nguyên đủ chính xác cho ngưỡng 30 khi round-trip JSON."""
    u = int(units)
    if u % FRESH_SCALE == 0:
        return u // FRESH_SCALE
    return round(u / FRESH_SCALE, 6)


def is_spoiled_units(units: int, spoiled_below: float = 30) -> bool:
    """Kiểm tra ươn (< spoiled_below) trên đơn vị nguyên trước khi làm tròn."""
    return int(units) < fresh_to_units(spoiled_below)


def _current_contract_version() -> str:
    try:
        with open(_DEFAULT_CONTRACT_PATH, encoding="utf-8") as f:
            return str(json.load(f).get("contract_version", "1.1"))
    except (OSError, ValueError):
        return "1.1"


def validate_items(items, kinds=KINDS_P2):
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def validate_items_v12(items, kinds=KINDS_P2) -> list:
    """Kiểm tra danh sách cá thể v1.2: [{"id": str, "kind": str, "fresh": float in [0, 100]}]."""
    if not isinstance(items, list):
        raise BadInput("items v1.2 phải là mảng cá thể")
    seen_ids = set()
    out = []
    for idx, entry in enumerate(items):
        if not isinstance(entry, dict) or set(entry.keys()) != {"id", "kind", "fresh"}:
            raise BadInput(f"items[{idx}] phải có đúng khóa 'id', 'kind', 'fresh'")
        iid = entry["id"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"items[{idx}].id phải là chuỗi khác rỗng")
        if iid in seen_ids:
            raise BadInput(f"items[{idx}].id trùng: {iid!r}")
        seen_ids.add(iid)
        kind = entry["kind"]
        if kind not in kinds:
            raise BadInput(f"items[{idx}].kind nguyên liệu lạ: {kind!r}")
        fresh = entry["fresh"]
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not math.isfinite(fresh):
            raise BadInput(f"items[{idx}].fresh phải là số hữu hạn")
        if not (0 <= fresh <= 100):
            raise BadInput(f"items[{idx}].fresh phải trong [0, 100], đang là {fresh!r}")
        out.append({"id": iid, "kind": kind, "fresh": fresh})
    return out


def read_inventory_v12(path: str, kinds=KINDS_P2) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}") from e
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_items_v12(data["items"], kinds)


def read_inventory(path: str, kinds=KINDS_P2, contract_version: str | None = None):
    ver = _current_contract_version() if contract_version is None else contract_version
    if ver in ("1.2", "1.3"):
        return read_inventory_v12(path, kinds=kinds)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}") from e
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if isinstance(data["items"], list):
        return validate_items_v12(data["items"], kinds)
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list):
    """Chuyển giỏ sang schema xuất kho: v1.2 trả mảng cá thể sắp theo id_key; v1.1 giữ dict đếm."""
    if not hold:
        return [] if _current_contract_version() in ("1.2", "1.3") else {}
    if isinstance(hold[0], dict):
        return [
            {"id": it["id"], "kind": it["kind"], "fresh": it["fresh"]}
            for it in sort_by_id(hold)
        ]
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items):
    if isinstance(items, list):
        validated = validate_items_v12(items)
        payload_items = [
            {
                "id": it["id"],
                "kind": it["kind"],
                "fresh": units_to_fresh(fresh_to_units(it["fresh"])),
            }
            for it in sort_by_id(validated)
        ]
    else:
        payload_items = {k: items[k] for k in sorted(items) if items[k] > 0}
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": payload_items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
