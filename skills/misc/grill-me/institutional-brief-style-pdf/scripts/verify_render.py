#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

try:
    import fitz  # PyMuPDF
except Exception as exc:  # pragma: no cover
    raise SystemExit("PyMuPDF is required: pip install pymupdf") from exc


def render(pdf: Path, out_dir: Path, dpi: int = 144) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pix.save(out_dir / f"page-{i:02d}.png")
    print(f"rendered {len(doc)} page(s) to {out_dir}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Render a generated PDF to PNG pages for visual QA.")
    ap.add_argument("pdf")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--dpi", type=int, default=144)
    args = ap.parse_args()
    pdf = Path(args.pdf)
    out_dir = Path(args.out_dir) if args.out_dir else pdf.with_suffix("").parent / (pdf.stem + "_renders")
    render(pdf, out_dir, args.dpi)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
