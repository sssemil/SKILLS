#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running this file directly from the scripts directory.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from palantir_brief.renderer import BriefRenderer, load_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Palantir-style institutional brief PDF from YAML/JSON.")
    parser.add_argument("input", help="YAML or JSON brief spec")
    parser.add_argument("output", help="Output PDF path")
    args = parser.parse_args()
    cfg = load_config(args.input)
    out = BriefRenderer(cfg, args.output).save()
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
