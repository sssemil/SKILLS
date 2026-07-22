#!/usr/bin/env python3
"""Create a starter YAML diagram spec for the HLD renderer."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

try:
    import yaml  # type: ignore
except Exception as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install requirements.txt.") from exc


def split_csv(value: str, fallback: List[str]) -> List[str]:
    if not value:
        return fallback
    return [x.strip() for x in value.split(",") if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit a fixed-coordinate starter HLD YAML spec.")
    ap.add_argument("--title", default="SYSTEM HIGH-LEVEL DESIGN (HLD)")
    ap.add_argument("--services", default="Write Service,Read Service,Availability Service")
    ap.add_argument("--stores", default="Primary DB\n(SoT),Read Model\n(derived),Booking DB\n(SoT)")
    ap.add_argument("--workers", default="Search\nIndex,Reminder\nScheduler,Fan-out\nWorker,Updater")
    ap.add_argument("--out", type=Path, default=Path("starter_hld.yaml"))
    args = ap.parse_args()

    services = split_csv(args.services, [])
    stores = split_csv(args.stores, [])
    workers = split_csv(args.workers, [])
    n = max(1, len(services))
    service_w = 176
    gap = 24
    row_w = n * service_w + (n - 1) * gap
    start_x = int((1080 - row_w) / 2)

    nodes = [
        {"id": "client", "kind": "box", "x": 37, "y": 47, "w": 236, "h": 52, "text": "Client (web/mobile)", "font_size": 18},
        {"id": "api", "kind": "box", "x": 320, "y": 47, "w": 597, "h": 53, "text": "API Gateway - authN->N, rate-limit, route", "font_size": 18},
    ]

    for idx, svc in enumerate(services):
        x = start_x + idx * (service_w + gap)
        nodes.append({"id": f"service_{idx+1}", "kind": "box", "x": x, "y": 148, "w": service_w, "h": 79, "text": svc, "font_size": 18})
        store_text = stores[idx] if idx < len(stores) else f"Store {idx+1}\n(SoT)"
        nodes.append({"id": f"store_{idx+1}", "kind": "box", "x": x + 22, "y": 281, "w": service_w - 44, "h": 107, "text": store_text, "font_size": 17})

    nodes.append({"id": "stream", "kind": "stream", "x": 209, "y": 438, "w": 595, "h": 57, "text": "kafka Change Stream (Kafka / CDC)", "font_size": 19})

    worker_w = 104
    worker_gap = 20
    row_w = len(workers) * worker_w + max(0, len(workers) - 1) * worker_gap
    wx0 = int((1080 - row_w) / 2)
    for idx, worker in enumerate(workers):
        nodes.append({"id": f"worker_{idx+1}", "kind": "green_box" if idx == len(workers)-1 else "box", "variant": "green" if idx == len(workers)-1 else "default", "x": wx0 + idx * (worker_w + worker_gap), "y": 520, "w": worker_w, "h": 106, "text": worker, "font_size": 16})

    edges = [{"from": "client.right", "to": "api.left", "color": "blue"}]
    for idx in range(n):
        svc_x = start_x + idx * (service_w + gap) + service_w / 2
        store_x = start_x + idx * (service_w + gap) + service_w / 2
        edges.append({"points": [[int(svc_x), 100], [int(svc_x), 148]], "color": "blue"})
        edges.append({"points": [[int(svc_x), 227], [int(store_x), 281]], "color": "blue"})
        edges.append({"points": [[int(store_x), 388], [int(store_x), 438]], "color": "blue"})
    for idx in range(len(workers)):
        x = wx0 + idx * (worker_w + worker_gap) + worker_w / 2
        edges.append({"points": [[int(x), 495], [int(x), 520]], "color": "blue"})

    labels = []
    for idx in range(n):
        x = start_x + idx * (service_w + gap) + service_w / 2 - 45
        labels.append({"text": "(SYNC)", "x": int(x), "y": 261, "size": 18})
        labels.append({"text": "CDC", "x": int(x + 52), "y": 419, "size": 17})

    icons = [
        {"name": "devices", "x": 116, "y": 88, "scale": 0.94},
        {"name": "key", "x": 505, "y": 60, "scale": 0.72},
        {"name": "clock", "x": 646, "y": 59, "scale": 0.80},
        {"name": "route", "x": 812, "y": 59, "scale": 0.80},
    ]
    for idx in range(n):
        sx = start_x + idx * (service_w + gap) + service_w - 54
        icons.append({"name": "calendar", "x": int(sx), "y": 174, "scale": 0.82})
        icons.append({"name": "db", "x": int(start_x + idx * (service_w + gap) + service_w - 50), "y": 352, "scale": 0.86})

    spec = {"canvas": {"width": 1080, "height": 779, "title": args.title, "title_y": 31, "title_size": 24}, "nodes": nodes, "edges": edges, "labels": labels, "icons": icons}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=1000), encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
