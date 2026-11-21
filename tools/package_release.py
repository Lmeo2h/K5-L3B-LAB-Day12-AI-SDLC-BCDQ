"""Đóng gói bản phát hành sạch `chonoi-v1.0.0.zip` (chỉ thư viện chuẩn Python)."""

import argparse
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCLUDE_FILES = (
    "game.contract.json",
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "CREDITS.md",
    "TEAM.md",
    "AGENTS.md",
)
INCLUDE_DIRS = ("chonoi", "tools")
SKIP_NAMES = {"__pycache__", ".DS_Store"}


def build_package(out_path: str) -> int:
    count = 0
    prefix = "chonoi-v1.0.0"
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in INCLUDE_FILES:
            full = os.path.join(ROOT, rel)
            if os.path.isfile(full):
                zf.write(full, f"{prefix}/{rel}")
                count += 1
        for d in INCLUDE_DIRS:
            base = os.path.join(ROOT, d)
            if not os.path.isdir(base):
                continue
            for root, dirs, files in os.walk(base):
                dirs[:] = sorted(x for x in dirs if x not in SKIP_NAMES)
                for fn in sorted(files):
                    if fn in SKIP_NAMES or fn.endswith((".pyc", ".pyo")):
                        continue
                    full = os.path.join(root, fn)
                    rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
                    zf.write(full, f"{prefix}/{rel}")
                    count += 1
    return count


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Đóng gói bản phát hành Quán Ăn Chợ Nổi v1.0.0.")
    p.add_argument("--out", default=os.path.join(ROOT, "chonoi-v1.0.0.zip"))
    args = p.parse_args(argv)
    n = build_package(args.out)
    size_kb = os.path.getsize(args.out) / 1024.0
    print(f"OK: đã đóng gói {n} tệp -> {args.out} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
