#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import fitz
from PIL import Image, ImageChops, ImageStat


def render_page(page: fitz.Page, dpi: int) -> Image.Image:
    zoom = dpi / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def compare_images(ref: Image.Image, cand: Image.Image) -> tuple[float, float, Image.Image]:
    w = max(ref.width, cand.width)
    h = max(ref.height, cand.height)
    bg = (255, 255, 255)
    r = Image.new("RGB", (w, h), bg)
    c = Image.new("RGB", (w, h), bg)
    r.paste(ref, (0, 0))
    c.paste(cand, (0, 0))
    diff = ImageChops.difference(r, c)
    stat = ImageStat.Stat(diff)
    mean_abs = sum(stat.mean) / 3.0
    sq = sum(v * v for v in stat.rms) / 3.0
    rms = math.sqrt(sq)
    return mean_abs, rms, diff


def main() -> int:
    ap = argparse.ArgumentParser(description="Render and compare a generated institutional brief against a reference PDF.")
    ap.add_argument("reference_pdf")
    ap.add_argument("candidate_pdf")
    ap.add_argument("--out-dir", default="comparison")
    ap.add_argument("--dpi", type=int, default=120)
    args = ap.parse_args()

    ref_path = Path(args.reference_pdf)
    cand_path = Path(args.candidate_pdf)
    out_dir = Path(args.out_dir)
    diff_dir = out_dir / "diffs"
    diff_dir.mkdir(parents=True, exist_ok=True)

    ref = fitz.open(ref_path)
    cand = fitz.open(cand_path)
    if len(ref) != len(cand):
        raise SystemExit(
            f"page-count mismatch: reference has {len(ref)}, candidate has {len(cand)}"
        )
    n = min(len(ref), len(cand))
    rows = []
    for i in range(n):
        ref_img = render_page(ref[i], args.dpi)
        cand_img = render_page(cand[i], args.dpi)
        mean_abs, rms, diff = compare_images(ref_img, cand_img)
        diff.save(diff_dir / f"page-{i + 1:02d}.png")
        rows.append({"page": i + 1, "mean_abs_rgb": round(mean_abs, 4), "rms_rgb": round(rms, 4)})

    out_csv = out_dir / "scores.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["page", "mean_abs_rgb", "rms_rgb"])
        writer.writeheader()
        writer.writerows(rows)

    avg = sum(row["mean_abs_rgb"] for row in rows) / n if n else 0
    print(f"compared {n} page(s); reference has {len(ref)}, candidate has {len(cand)}")
    print(f"average mean absolute RGB difference: {avg:.4f}")
    print(f"wrote {out_csv} and {diff_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
