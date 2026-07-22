#!/usr/bin/env python3
"""Quick sanity checks for generated HLD outputs."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def check_png(path: Path, expected_w: int, expected_h: int) -> int:
    try:
        from PIL import Image  # type: ignore
    except Exception:
        print("Pillow is not installed; cannot check PNG dimensions.")
        return 2
    with Image.open(path) as im:
        w, h = im.size
    print(f"{path}: PNG {w}x{h}")
    if (w, h) != (expected_w, expected_h):
        print(f"  warning: expected {expected_w}x{expected_h}")
        return 1
    return 0


def check_svg(path: Path, expected_w: int, expected_h: int) -> int:
    text = path.read_text(encoding="utf-8", errors="ignore")[:1000]
    mw = re.search(r'width="([0-9.]+)"', text)
    mh = re.search(r'height="([0-9.]+)"', text)
    w = int(float(mw.group(1))) if mw else -1
    h = int(float(mh.group(1))) if mh else -1
    print(f"{path}: SVG {w}x{h}")
    if (w, h) != (expected_w, expected_h):
        print(f"  warning: expected {expected_w}x{expected_h}")
        return 1
    return 0


def check_pdf(path: Path, expected_w: int, expected_h: int) -> int:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception:
            print(f"{path}: PDF exists ({path.stat().st_size} bytes); install pypdf for page-size checks.")
            return 0
    reader = PdfReader(str(path))
    page = reader.pages[0]
    box = page.mediabox
    w = float(box.width)
    h = float(box.height)
    # CairoSVG uses CSS px at 96 dpi: 1 px = 0.75 pt.
    exp_w_pt = expected_w * 0.75
    exp_h_pt = expected_h * 0.75
    print(f"{path}: PDF {w:.1f}x{h:.1f} pt")
    if abs(w - exp_w_pt) > 1 or abs(h - exp_h_pt) > 1:
        print(f"  warning: expected about {exp_w_pt:.1f}x{exp_h_pt:.1f} pt")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Check dimensions of rendered HLD outputs.")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--expected", default="1080x779", help="Expected raster/SVG dimensions, e.g. 1080x779")
    args = ap.parse_args()
    m = re.match(r"^(\d+)x(\d+)$", args.expected)
    if not m:
        raise SystemExit("--expected must look like 1080x779")
    expected_w, expected_h = int(m.group(1)), int(m.group(2))
    status = 0
    for path in args.files:
        if not path.exists():
            print(f"{path}: missing")
            status = 2
            continue
        ext = path.suffix.lower()
        if ext == ".png":
            status = max(status, check_png(path, expected_w, expected_h))
        elif ext == ".svg":
            status = max(status, check_svg(path, expected_w, expected_h))
        elif ext == ".pdf":
            status = max(status, check_pdf(path, expected_w, expected_h))
        else:
            print(f"{path}: unsupported extension")
            status = max(status, 2)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
