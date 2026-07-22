#!/usr/bin/env python3
"""
Render high-level design diagrams from YAML/JSON into SVG, PNG, and PDF.

The renderer is intentionally coordinate-driven. This is the right choice for
one-page architecture sheets where the spacing, labels, icons, and arrows need
to feel hand-composed rather than auto-laid-out.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback for JSON-only installs
    yaml = None

Point = Tuple[float, float]


# -----------------------------------------------------------------------------
# Theme
# -----------------------------------------------------------------------------

THEME = {
    "background": "#eef3f6",
    "blue": "#365f78",
    "blue_dark": "#25485d",
    "blue_light": "#eaf4fa",
    "stroke": "#8aa6b0",
    "text": "#111820",
    "muted_text": "#2b3740",
    "green": "#67915f",
    "green_dark": "#517a4d",
    "green_fill": "#ecf8e8",
    "card_fill": "#f3f9fc",
    "card_fill_2": "#eef6fb",
    "shadow": "#6f7f86",
    "faint": "#b8c8ce",
    "db_blue": "#5f88b8",
    "redis_red": "#b93325",
    "yellow": "#e6c44f",
    "orange": "#d29737",
    "phone": "#445966",
    "icon_blue": "#4d7ea8",
    "icon_green": "#62a66a",
    "icon_red": "#cf6a5d",
    "icon_gray": "#6e7f87",
}

MONO_FONT = "'Courier New', 'Courier Prime', 'DejaVu Sans Mono', Menlo, Consolas, monospace"
TITLE_FONT = "Inter, Arial, Helvetica, sans-serif"


# -----------------------------------------------------------------------------
# Small helpers
# -----------------------------------------------------------------------------

def esc(value: Any, *, quote: bool = False) -> str:
    return html.escape(str(value), quote=quote)


def num(v: Any) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    return float(str(v).strip())


def fmt(v: float) -> str:
    if abs(v - round(v)) < 0.001:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip("0").rstrip(".")


def color_value(value: str, fallback: str = "blue") -> str:
    if not value:
        value = fallback
    if value.startswith("#"):
        return value
    return THEME.get(value, value)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "item"


def wrap_lines(text: str, max_chars: int) -> List[str]:
    result: List[str] = []
    for raw in str(text).splitlines():
        if not raw.strip():
            result.append("")
            continue
        if len(raw) <= max_chars:
            result.append(raw)
        else:
            result.extend(textwrap.wrap(raw, width=max_chars, break_long_words=False, replace_whitespace=False))
    return result or [""]


@dataclass
class Node:
    id: str
    kind: str
    x: float
    y: float
    w: float
    h: float
    text: str = ""
    variant: str = "default"
    font_size: float = 18
    text_anchor: str = "middle"
    align: str = "center"
    padding: float = 14
    data: Mapping[str, Any] = None  # type: ignore

    def anchor(self, name: str) -> Point:
        name = name.lower().replace("-", "_")
        anchors = {
            "top": (self.x + self.w / 2, self.y),
            "bottom": (self.x + self.w / 2, self.y + self.h),
            "left": (self.x, self.y + self.h / 2),
            "right": (self.x + self.w, self.y + self.h / 2),
            "center": (self.x + self.w / 2, self.y + self.h / 2),
            "top_left": (self.x, self.y),
            "top_right": (self.x + self.w, self.y),
            "bottom_left": (self.x, self.y + self.h),
            "bottom_right": (self.x + self.w, self.y + self.h),
        }
        if name not in anchors:
            raise ValueError(f"Unknown anchor {name!r} on node {self.id!r}")
        return anchors[name]


# -----------------------------------------------------------------------------
# SVG renderer
# -----------------------------------------------------------------------------

class HLDRenderer:
    def __init__(self, spec: Mapping[str, Any], guides: bool = False):
        self.spec = spec
        canvas = spec.get("canvas", {})
        self.width = int(canvas.get("width", spec.get("width", 1080)))
        self.height = int(canvas.get("height", spec.get("height", 779)))
        self.title = str(canvas.get("title", spec.get("title", "HIGH-LEVEL DESIGN (HLD)")))
        self.guides = guides
        self.nodes: Dict[str, Node] = {}
        self.parts: List[str] = []
        self.edge_colors: Dict[str, str] = {}
        for raw in spec.get("nodes", []):
            n = Node(
                id=str(raw["id"]),
                kind=str(raw.get("kind", "box")),
                x=num(raw.get("x", 0)),
                y=num(raw.get("y", 0)),
                w=num(raw.get("w", 120)),
                h=num(raw.get("h", 70)),
                text=str(raw.get("text", "")),
                variant=str(raw.get("variant", raw.get("kind", "default"))),
                font_size=num(raw.get("font_size", raw.get("fontSize", 18))),
                text_anchor=str(raw.get("text_anchor", "middle")),
                align=str(raw.get("align", "center")),
                padding=num(raw.get("padding", 14)),
                data=raw,
            )
            self.nodes[n.id] = n

    def render(self) -> str:
        self.parts = []
        self.edge_colors = {}
        self._collect_edge_colors()
        self._svg_open()
        self._defs()
        self._background()
        self._title()
        self._draw_edges(layer="under")
        self._draw_nodes()
        self._draw_icons()
        self._draw_edges(layer="over")
        self._draw_labels()
        if self.guides:
            self._guides()
        self.parts.append("</svg>")
        return "\n".join(self.parts)

    def _svg_open(self) -> None:
        self.parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}" role="img" aria-label="{esc(self.title, quote=True)}">'
        )

    def _defs(self) -> None:
        # Arrow markers need stable ids because SVG ids cannot contain '#'.
        markers: List[str] = []
        for key, color in self.edge_colors.items():
            markers.append(
                f'''<marker id="arrow-{key}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/>
</marker>'''
            )
        marker_defs = "\n".join(markers)
        self.parts.append(f'''
<defs>
  <linearGradient id="bg-grad" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#f7fbfd"/>
    <stop offset="1" stop-color="{THEME['background']}"/>
  </linearGradient>
  <linearGradient id="card-grad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#fbfdfe"/>
    <stop offset="1" stop-color="{THEME['card_fill_2']}"/>
  </linearGradient>
  <linearGradient id="green-card-grad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#fbfef9"/>
    <stop offset="1" stop-color="{THEME['green_fill']}"/>
  </linearGradient>
  <linearGradient id="db-grad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#84a9d1"/>
    <stop offset="0.5" stop-color="{THEME['db_blue']}"/>
    <stop offset="1" stop-color="#3f668e"/>
  </linearGradient>
  <linearGradient id="redis-grad" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#dd5848"/>
    <stop offset="1" stop-color="{THEME['redis_red']}"/>
  </linearGradient>
  <filter id="card-shadow" x="-20%" y="-20%" width="140%" height="150%">
    <feDropShadow dx="0" dy="4" stdDeviation="3" flood-color="{THEME['shadow']}" flood-opacity="0.32"/>
  </filter>
  <filter id="soft-shadow" x="-20%" y="-20%" width="140%" height="150%">
    <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#4a5c65" flood-opacity="0.26"/>
  </filter>
  <style>
    .title {{ font-family: {TITLE_FONT}; font-weight: 800; letter-spacing: 0.2px; fill: #0f151a; }}
    .mono {{ font-family: {MONO_FONT}; fill: {THEME['text']}; }}
    .label {{ font-family: {MONO_FONT}; fill: {THEME['text']}; }}
  </style>
  {marker_defs}
</defs>
''')

    def _collect_edge_colors(self) -> None:
        colors = {"blue": THEME["blue"], "green": THEME["green"]}
        for edge in self.spec.get("edges", []):
            if edge.get("layer", "under") == "hidden":
                continue
            color = color_value(str(edge.get("color", "blue")))
            key = self._marker_key(color)
            colors[key] = color
        self.edge_colors = colors

    def _marker_key(self, color: str) -> str:
        if color.startswith("#"):
            return "c" + hashlib.sha1(color.encode()).hexdigest()[:8]
        return slug(color)

    def _background(self) -> None:
        self.parts.append(f'<rect width="{self.width}" height="{self.height}" fill="url(#bg-grad)"/>')
        faint = THEME["faint"]
        # faint paper grain / construction lines
        self.parts.append(f'<g opacity="0.23" stroke="{faint}" stroke-width="1" fill="none">')
        # right-side perspective grid
        for i in range(-120, 370, 42):
            x0 = self.width - 220 + i
            self.parts.append(f'<path d="M {x0} 0 L {self.width + 80} {180 + i * 0.35}"/>')
        for i in range(0, 380, 46):
            self.parts.append(f'<path d="M {self.width - 185 + i * 0.18} 0 L {self.width - 168 + i * 0.18} {280 + i}"/>')
        # left/bottom blueprint blocks
        for x, y, w, h in [(0, 468, 145, 180), (18, 512, 122, 155), (50, 585, 110, 114), (82, 634, 120, 88)]:
            self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3"/>')
            self.parts.append(f'<path d="M {x} {y} L {x+28} {y-18} L {x+w+28} {y-18} L {x+w} {y}"/>')
            self.parts.append(f'<path d="M {x+w} {y} L {x+w+28} {y-18} L {x+w+28} {y+h-18} L {x+w} {y+h}"/>')
        # subtle grid lines across lower portion
        for y in range(430, self.height, 60):
            self.parts.append(f'<line x1="0" y1="{y}" x2="{self.width}" y2="{y}" opacity="0.22"/>')
        for x in range(0, self.width, 90):
            self.parts.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{self.height}" opacity="0.10"/>')
        self.parts.append('</g>')

    def _title(self) -> None:
        title_size = num(self.spec.get("canvas", {}).get("title_size", 24))
        y = num(self.spec.get("canvas", {}).get("title_y", 30))
        self.parts.append(
            f'<text class="title" x="{self.width/2}" y="{fmt(y)}" font-size="{fmt(title_size)}" text-anchor="middle">{esc(self.title)}</text>'
        )

    # ------------------------------------------------------------------ nodes
    def _draw_nodes(self) -> None:
        for n in self.nodes.values():
            if n.kind == "stream":
                self._draw_stream(n)
            else:
                self._draw_card(n)

    def _draw_card(self, n: Node) -> None:
        variant = str(n.data.get("variant", n.kind) if n.data else n.variant)
        fill = str(n.data.get("fill", "") if n.data else "")
        stroke = str(n.data.get("stroke", "") if n.data else "")
        if not fill:
            fill = "url(#green-card-grad)" if variant in ("green", "green_box") or n.kind == "green_box" else "url(#card-grad)"
        if not stroke:
            stroke = THEME["green"] if variant in ("green", "green_box") or n.kind == "green_box" else THEME["stroke"]
        rx = num(n.data.get("rx", 8) if n.data else 8)
        sw = num(n.data.get("stroke_width", 1.8) if n.data else 1.8)
        self.parts.append(
            f'<rect x="{fmt(n.x)}" y="{fmt(n.y)}" width="{fmt(n.w)}" height="{fmt(n.h)}" rx="{fmt(rx)}" ry="{fmt(rx)}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{fmt(sw)}" filter="url(#card-shadow)"/>'
        )
        # light inner rim
        self.parts.append(
            f'<rect x="{fmt(n.x+1.5)}" y="{fmt(n.y+1.5)}" width="{fmt(n.w-3)}" height="{fmt(n.h-3)}" rx="{fmt(max(2, rx-1.5))}" ry="{fmt(max(2, rx-1.5))}" '
            f'fill="none" stroke="#ffffff" stroke-width="1" opacity="0.55"/>'
        )
        if n.text:
            self._card_text(n)

    def _card_text(self, n: Node) -> None:
        max_chars = max(6, int((n.w - 2 * n.padding) / (n.font_size * 0.57)))
        lines = wrap_lines(n.text, max_chars)
        lh = num(n.data.get("line_height", n.font_size * 1.22) if n.data else n.font_size * 1.22)
        total_h = lh * (len(lines) - 1)
        y0 = n.y + n.h / 2 - total_h / 2 + n.font_size * 0.35
        if n.align == "left" or n.text_anchor == "start":
            x0 = n.x + n.padding
            anchor = "start"
        elif n.align == "right" or n.text_anchor == "end":
            x0 = n.x + n.w - n.padding
            anchor = "end"
        else:
            x0 = n.x + n.w / 2
            anchor = "middle"
        self.parts.append(
            f'<text class="mono" x="{fmt(x0)}" y="{fmt(y0)}" font-size="{fmt(n.font_size)}" text-anchor="{anchor}">'
        )
        first = True
        for line in lines:
            dy = "0" if first else fmt(lh)
            self.parts.append(f'<tspan x="{fmt(x0)}" dy="{dy}">{esc(line)}</tspan>')
            first = False
        self.parts.append('</text>')

    def _draw_stream(self, n: Node) -> None:
        rx = num(n.data.get("rx", 9) if n.data else 9)
        self.parts.append(
            f'<rect x="{fmt(n.x)}" y="{fmt(n.y)}" width="{fmt(n.w)}" height="{fmt(n.h)}" rx="{fmt(rx)}" ry="{fmt(rx)}" '
            f'fill="url(#card-grad)" stroke="{THEME["stroke"]}" stroke-width="1.8" filter="url(#card-shadow)"/>'
        )
        # segmented pipe on the right, like a CDC/log cylinder.
        pipe_w = num(n.data.get("pipe_width", 154) if n.data else 154)
        px = n.x + n.w - pipe_w
        py = n.y + 1
        ph = n.h - 2
        self.parts.append(f'<g opacity="0.95">')
        self.parts.append(f'<rect x="{fmt(px)}" y="{fmt(py)}" width="{fmt(pipe_w-16)}" height="{fmt(ph)}" fill="#e2ebef" stroke="none"/>')
        for i in range(0, 5):
            sx = px + i * (pipe_w - 26) / 5
            col = "#dfe7ec" if i % 2 == 0 else "#c9d5dc"
            self.parts.append(f'<path d="M {fmt(sx)} {fmt(py+1)} C {fmt(sx+12)} {fmt(py+9)} {fmt(sx+12)} {fmt(py+ph-9)} {fmt(sx)} {fmt(py+ph-1)} L {fmt(sx+18)} {fmt(py+ph-1)} C {fmt(sx+30)} {fmt(py+ph-9)} {fmt(sx+30)} {fmt(py+9)} {fmt(sx+18)} {fmt(py+1)} Z" fill="{col}" stroke="#96a8b0" stroke-width="0.8"/>')
        # blue end segments
        for i, col in enumerate(["#b6c8d2", "#78a0bd", "#3e78a9"]):
            sx = n.x + n.w - 72 + i * 22
            self.parts.append(f'<path d="M {fmt(sx)} {fmt(py+1)} C {fmt(sx+12)} {fmt(py+9)} {fmt(sx+12)} {fmt(py+ph-9)} {fmt(sx)} {fmt(py+ph-1)} L {fmt(sx+19)} {fmt(py+ph-1)} C {fmt(sx+31)} {fmt(py+ph-9)} {fmt(sx+31)} {fmt(py+9)} {fmt(sx+19)} {fmt(py+1)} Z" fill="{col}" stroke="#567b93" stroke-width="0.9"/>')
        cap_x = n.x + n.w - 13
        self.parts.append(f'<ellipse cx="{fmt(cap_x)}" cy="{fmt(n.y+n.h/2)}" rx="15" ry="{fmt(n.h/2-2)}" fill="#d6e5ec" stroke="{THEME["stroke"]}" stroke-width="1.5"/>')
        self.parts.append('</g>')
        # Kafka icon and text
        self.parts.append(icon_svg("kafka", n.x + 31, n.y + n.h / 2 - 17, 0.82))
        label = n.text or "kafka Change Stream (Kafka / CDC)"
        self.parts.append(
            f'<text class="mono" x="{fmt(n.x + 68)}" y="{fmt(n.y + n.h/2 + n.font_size*0.35)}" font-size="{fmt(n.font_size)}" font-weight="700">{esc(label)}</text>'
        )

    # ------------------------------------------------------------------ edges
    def _draw_edges(self, layer: str) -> None:
        for edge in self.spec.get("edges", []):
            if str(edge.get("layer", "under")) != layer:
                continue
            self._draw_edge(edge)

    def _draw_edge(self, edge: Mapping[str, Any]) -> None:
        points: List[Point]
        if "points" in edge:
            points = [self._point(p) for p in edge["points"]]
        else:
            if "from" not in edge or "to" not in edge:
                raise ValueError(f"Edge must have points or from/to: {edge}")
            points = [self._point(edge["from"])]
            for p in edge.get("via", []) or []:
                points.append(self._point(p))
            points.append(self._point(edge["to"]))
        if len(points) < 2:
            return
        color = color_value(str(edge.get("color", "blue")))
        sw = num(edge.get("stroke_width", edge.get("strokeWidth", 2.1)))
        dash = edge.get("dash") or edge.get("dashed")
        dash_attr = ' stroke-dasharray="7 6"' if dash else ""
        arrow = bool(edge.get("arrow", True))
        marker = ""
        if arrow:
            key = self._marker_key(color)
            marker = f' marker-end="url(#arrow-{key})"'
        path = "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in points)
        self.parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{fmt(sw)}" stroke-linecap="round" stroke-linejoin="round"{dash_attr}{marker}/>' )
        if edge.get("label"):
            x, y = self._label_pos(edge, points)
            self._plain_text(str(edge["label"]), x, y, size=num(edge.get("label_size", 18)), anchor=str(edge.get("label_anchor", "middle")))

    def _label_pos(self, edge: Mapping[str, Any], points: Sequence[Point]) -> Point:
        if "label_x" in edge and "label_y" in edge:
            return (num(edge["label_x"]), num(edge["label_y"]))
        # by default place near the middle segment
        total = 0.0
        segs: List[Tuple[float, Point, Point]] = []
        for a, b in zip(points[:-1], points[1:]):
            d = math.hypot(b[0] - a[0], b[1] - a[1])
            segs.append((d, a, b))
            total += d
        target = total / 2
        seen = 0.0
        for d, a, b in segs:
            if seen + d >= target:
                t = (target - seen) / max(d, 1e-6)
                return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]) - 10)
            seen += d
        return points[len(points) // 2]

    def _point(self, value: Any) -> Point:
        if isinstance(value, str):
            if "." not in value:
                raise ValueError(f"Point string {value!r} must be node.anchor")
            node_id, anchor = value.rsplit(".", 1)
            if node_id not in self.nodes:
                raise ValueError(f"Unknown node id in endpoint: {node_id!r}")
            return self.nodes[node_id].anchor(anchor)
        if isinstance(value, Mapping):
            if "node" in value and "anchor" in value:
                return self.nodes[str(value["node"])].anchor(str(value["anchor"]))
            return (num(value["x"]), num(value["y"]))
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return (num(value[0]), num(value[1]))
        raise ValueError(f"Cannot parse point: {value!r}")

    # ------------------------------------------------------------------ icons / labels
    def _draw_icons(self) -> None:
        for item in self.spec.get("icons", []):
            name = str(item.get("name", ""))
            x = num(item.get("x", 0))
            y = num(item.get("y", 0))
            scale = num(item.get("scale", 1))
            self.parts.append(icon_svg(name, x, y, scale))

    def _draw_labels(self) -> None:
        for label in self.spec.get("labels", []):
            self._plain_text(
                str(label.get("text", "")),
                num(label.get("x", 0)),
                num(label.get("y", 0)),
                size=num(label.get("size", label.get("font_size", 18))),
                anchor=str(label.get("anchor", "start")),
                fill=color_value(str(label.get("color", "text")), fallback="text"),
                weight=str(label.get("weight", "400")),
            )

    def _plain_text(self, text: str, x: float, y: float, size: float = 18, anchor: str = "start", fill: str = "", weight: str = "400") -> None:
        if not fill:
            fill = THEME["text"]
        lines = str(text).splitlines() or [""]
        lh = size * 1.22
        self.parts.append(f'<text class="label" x="{fmt(x)}" y="{fmt(y)}" font-size="{fmt(size)}" text-anchor="{anchor}" fill="{fill}" font-weight="{esc(weight)}">')
        first = True
        for line in lines:
            dy = "0" if first else fmt(lh)
            self.parts.append(f'<tspan x="{fmt(x)}" dy="{dy}">{esc(line)}</tspan>')
            first = False
        self.parts.append('</text>')

    # ------------------------------------------------------------------ guides
    def _guides(self) -> None:
        self.parts.append('<g opacity="0.55" stroke="#b00020" stroke-width="0.6" fill="none">')
        for x in range(0, self.width + 1, 50):
            self.parts.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{self.height}"/>')
        for y in range(0, self.height + 1, 50):
            self.parts.append(f'<line x1="0" y1="{y}" x2="{self.width}" y2="{y}"/>')
        self.parts.append('</g>')
        self.parts.append('<g class="label" font-size="10" fill="#b00020" opacity="0.7">')
        for x in range(0, self.width + 1, 100):
            self.parts.append(f'<text x="{x+2}" y="12">{x}</text>')
        for y in range(0, self.height + 1, 100):
            self.parts.append(f'<text x="2" y="{y+12}">{y}</text>')
        self.parts.append('</g>')


# -----------------------------------------------------------------------------
# Icons: pure SVG vectors, no external assets.
# -----------------------------------------------------------------------------

def icon_svg(name: str, x: float, y: float, scale: float = 1.0) -> str:
    name = name.strip().lower().replace("-", "_")
    body = ICONS.get(name, icon_unknown)()
    return f'<g transform="translate({fmt(x)} {fmt(y)}) scale({fmt(scale)})" filter="url(#soft-shadow)">{body}</g>'


def icon_unknown() -> str:
    return '<circle cx="12" cy="12" r="10" fill="#eef" stroke="#789"/><text class="mono" x="12" y="17" font-size="14" text-anchor="middle">?</text>'


def icon_devices() -> str:
    return f'''
<rect x="4" y="0" width="20" height="40" rx="3" fill="#59636a" stroke="#2e353a" stroke-width="1.2"/>
<rect x="7" y="4" width="14" height="30" fill="#343b40" opacity="0.85"/>
<circle cx="14" cy="37" r="1.4" fill="#c8d0d4"/>
<rect x="34" y="3" width="55" height="35" rx="2" fill="#4f5d65" stroke="#2e353a" stroke-width="1.4"/>
<rect x="38" y="7" width="47" height="26" fill="#252b30" opacity="0.86"/>
<path d="M 55 39 L 69 39 L 72 45 L 52 45 Z" fill="#59636a" stroke="#2e353a" stroke-width="1"/>
<path d="M 41 31 L 82 9" stroke="#778790" stroke-width="1" opacity="0.45"/>
'''


def icon_key() -> str:
    return f'''
<circle cx="10" cy="14" r="7" fill="#f1d56b" stroke="#b58917" stroke-width="2"/>
<circle cx="10" cy="14" r="2.7" fill="#fff3b0" stroke="#b58917" stroke-width="1"/>
<path d="M 16 14 L 39 14" stroke="#b58917" stroke-width="4" stroke-linecap="round"/>
<path d="M 30 14 L 30 21 M 36 14 L 36 19" stroke="#b58917" stroke-width="3" stroke-linecap="round"/>
'''


def icon_clock() -> str:
    return f'''
<circle cx="18" cy="18" r="15" fill="#f4f5f6" stroke="#8e9aa0" stroke-width="2"/>
<circle cx="18" cy="18" r="2" fill="#8e9aa0"/>
<path d="M 18 18 L 18 8 M 18 18 L 25 22" stroke="#7d888e" stroke-width="2.4" stroke-linecap="round"/>
<path d="M 18 4 L 18 7 M 18 29 L 18 32 M 4 18 L 7 18 M 29 18 L 32 18" stroke="#b8c0c4" stroke-width="1.2"/>
'''


def icon_route() -> str:
    c = THEME["icon_blue"]
    return f'''
<circle cx="18" cy="18" r="5" fill="{c}"/>
<path d="M 18 4 L 18 32 M 4 18 L 32 18" stroke="{c}" stroke-width="4" stroke-linecap="round"/>
<path d="M 18 1 L 24 8 L 12 8 Z M 18 35 L 12 28 L 24 28 Z M 1 18 L 8 12 L 8 24 Z M 35 18 L 28 24 L 28 12 Z" fill="{c}"/>
'''


def icon_calendar() -> str:
    return f'''
<rect x="1" y="5" width="38" height="34" rx="4" fill="#f7fbfc" stroke="#607983" stroke-width="1.8"/>
<rect x="1" y="5" width="38" height="9" rx="4" fill="#cf6a5d"/>
<path d="M 1 13 L 39 13" stroke="#607983" stroke-width="1.2"/>
<path d="M 10 2 L 10 9 M 30 2 L 30 9" stroke="#607983" stroke-width="3" stroke-linecap="round"/>
<path d="M 9 20 L 31 20 M 9 27 L 31 27 M 9 34 L 25 34" stroke="#a9b8be" stroke-width="1.4"/>
'''


def icon_calendar_pen() -> str:
    return icon_calendar() + f'''
<path d="M 29 30 L 42 17 L 47 22 L 34 35 L 27 37 Z" fill="#e7c76b" stroke="#7d5c25" stroke-width="1.2"/>
<path d="M 40 19 L 45 24" stroke="#7d5c25" stroke-width="1.3"/>
<path d="M 27 37 L 30 32 L 34 35 Z" fill="#2f3538"/>
'''


def icon_calendar_check() -> str:
    return icon_calendar() + f'''
<circle cx="37" cy="35" r="11" fill="#65b96f" stroke="#477b4e" stroke-width="1.2"/>
<path d="M 31 35 L 35 39 L 43 30" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
'''


def icon_clipboard() -> str:
    return f'''
<rect x="6" y="4" width="32" height="42" rx="4" fill="#f7fbfc" stroke="#637c87" stroke-width="1.8"/>
<rect x="14" y="1" width="16" height="8" rx="3" fill="#e4e9ec" stroke="#637c87" stroke-width="1.4"/>
<path d="M 14 17 L 18 21 L 26 13 M 14 30 L 18 34 L 26 26" fill="none" stroke="#62a66a" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M 29 18 L 34 18 M 29 31 L 34 31" stroke="#a0aeb5" stroke-width="1.6"/>
'''


def icon_map() -> str:
    return f'''
<rect x="3" y="5" width="38" height="37" rx="3" fill="#d7e5f0" stroke="#45677e" stroke-width="1.6"/>
<path d="M 15 5 L 15 42 M 28 5 L 28 42" stroke="#7d98aa" stroke-width="1.2"/>
<path d="M 6 29 C 14 20 18 33 25 24 C 30 18 34 22 39 16" fill="none" stroke="#45677e" stroke-width="2"/>
<path d="M 9 12 L 12 16 L 9 20 L 6 16 Z M 31 31 L 34 35 L 31 39 L 28 35 Z" fill="#6f94b2"/>
'''


def icon_db() -> str:
    return f'''
<ellipse cx="20" cy="7" rx="18" ry="6" fill="#94b6d7" stroke="#335979" stroke-width="1.4"/>
<path d="M 2 7 L 2 37 C 2 45 38 45 38 37 L 38 7" fill="url(#db-grad)" stroke="#335979" stroke-width="1.4"/>
<ellipse cx="20" cy="37" rx="18" ry="6" fill="#5f88b8" stroke="#335979" stroke-width="1.4"/>
<path d="M 2 17 C 2 25 38 25 38 17 M 2 27 C 2 35 38 35 38 27" fill="none" stroke="#315573" stroke-width="1" opacity="0.7"/>
<ellipse cx="20" cy="7" rx="18" ry="6" fill="none" stroke="#c7d8e8" stroke-width="1" opacity="0.8"/>
'''


def icon_redis() -> str:
    return f'''
<g transform="skewY(-12)">
  <rect x="0" y="17" width="38" height="10" rx="2" fill="#7d261d" opacity="0.85"/>
  <rect x="0" y="9" width="38" height="10" rx="2" fill="#a92e24"/>
  <rect x="0" y="1" width="38" height="10" rx="2" fill="url(#redis-grad)"/>
</g>
<path d="M 9 4 L 20 1 L 31 4 L 20 7 Z" fill="#f06b5b" opacity="0.8"/>
<circle cx="13" cy="11" r="1.6" fill="#ffd7d1"/><circle cx="23" cy="9" r="1.5" fill="#ffd7d1"/>
'''


def icon_kafka() -> str:
    return f'''
<path d="M 19 9 L 19 30 M 19 19 L 7 13 M 19 20 L 8 27 M 19 12 L 31 7 M 19 27 L 31 33" stroke="#111820" stroke-width="3" stroke-linecap="round"/>
<circle cx="19" cy="9" r="5" fill="#f7fbfc" stroke="#111820" stroke-width="3"/>
<circle cx="19" cy="30" r="5" fill="#f7fbfc" stroke="#111820" stroke-width="3"/>
<circle cx="7" cy="13" r="4.2" fill="#f7fbfc" stroke="#111820" stroke-width="3"/>
<circle cx="8" cy="27" r="4.2" fill="#f7fbfc" stroke="#111820" stroke-width="3"/>
<circle cx="31" cy="7" r="4.2" fill="#f7fbfc" stroke="#111820" stroke-width="3"/>
<circle cx="31" cy="33" r="4.2" fill="#f7fbfc" stroke="#111820" stroke-width="3"/>
'''


def icon_search() -> str:
    return f'''
<circle cx="14" cy="14" r="9" fill="#f7fbfc" stroke="#324b5a" stroke-width="2.2"/>
<path d="M 21 21 L 34 34" stroke="#324b5a" stroke-width="4" stroke-linecap="round"/>
<circle cx="34" cy="36" r="6" fill="#5dbb74"/>
<circle cx="25" cy="36" r="6" fill="#42a5c7"/>
<circle cx="29" cy="27" r="6" fill="#e3c848"/>
<path d="M 10 14 C 14 9 18 10 21 14" fill="none" stroke="#9db0ba" stroke-width="1.3"/>
'''


def icon_alarm() -> str:
    return f'''
<circle cx="22" cy="24" r="14" fill="#fff8f4" stroke="#8f4b49" stroke-width="2.1"/>
<circle cx="22" cy="24" r="2" fill="#8f4b49"/>
<path d="M 22 24 L 22 15 M 22 24 L 29 29" stroke="#8f4b49" stroke-width="2.2" stroke-linecap="round"/>
<path d="M 10 8 C 3 10 1 17 6 21 M 34 8 C 41 10 43 17 38 21" fill="none" stroke="#b65f5b" stroke-width="3" stroke-linecap="round"/>
<path d="M 13 37 L 8 44 M 31 37 L 36 44" stroke="#8f4b49" stroke-width="2.4" stroke-linecap="round"/>
'''


def icon_phone_bell() -> str:
    return f'''
<rect x="0" y="5" width="34" height="58" rx="5" fill="#4f6470" stroke="#263640" stroke-width="1.8"/>
<rect x="5" y="11" width="24" height="41" fill="#9fc3df" opacity="0.92"/>
<circle cx="17" cy="58" r="2" fill="#d8e2e6"/>
<path d="M 16 30 C 16 23 27 23 27 30 L 27 39 L 31 43 L 12 43 L 16 39 Z" fill="#e4c344" stroke="#8a6b18" stroke-width="1.5"/>
<path d="M 18 43 C 19 48 24 48 26 43" fill="none" stroke="#8a6b18" stroke-width="1.6"/>
<path d="M 35 30 C 43 34 43 43 35 48" fill="none" stroke="#8a6b18" stroke-width="2.4" stroke-linecap="round"/>
'''


def icon_doc() -> str:
    return f'''
<path d="M 6 2 L 27 2 L 38 13 L 38 45 L 6 45 Z" fill="#d9e7f2" stroke="#496a80" stroke-width="1.7"/>
<path d="M 27 2 L 27 13 L 38 13" fill="#b7cedf" stroke="#496a80" stroke-width="1.2"/>
<path d="M 12 19 L 31 19 M 12 26 L 31 26 M 12 33 L 28 33" stroke="#6e8799" stroke-width="1.6"/>
<rect x="2" y="33" width="12" height="11" fill="#8aa7bd" stroke="#496a80" stroke-width="1"/>
'''


def icon_fanout() -> str:
    return f'''
<circle cx="22" cy="20" r="6" fill="#5f88b8" stroke="#345a75" stroke-width="1.5"/>
<circle cx="8" cy="8" r="5" fill="#86a7c3" stroke="#345a75" stroke-width="1.4"/>
<circle cx="39" cy="8" r="5" fill="#86a7c3" stroke="#345a75" stroke-width="1.4"/>
<circle cx="8" cy="35" r="5" fill="#86a7c3" stroke="#345a75" stroke-width="1.4"/>
<circle cx="39" cy="35" r="5" fill="#86a7c3" stroke="#345a75" stroke-width="1.4"/>
<path d="M 18 17 L 11 11 M 26 17 L 36 11 M 18 24 L 12 32 M 26 24 L 36 32" stroke="#345a75" stroke-width="2.2" stroke-linecap="round"/>
'''


def icon_sync() -> str:
    return f'''
<path d="M 8 24 C 11 10 26 4 38 12" fill="none" stroke="#4f8c79" stroke-width="4" stroke-linecap="round"/>
<path d="M 39 7 L 42 17 L 31 15 Z" fill="#4f8c79"/>
<path d="M 42 25 C 38 39 22 45 10 36" fill="none" stroke="#4f8c79" stroke-width="4" stroke-linecap="round"/>
<path d="M 9 41 L 7 30 L 18 33 Z" fill="#4f8c79"/>
'''


def icon_chart() -> str:
    return f'''
<path d="M 5 4 L 5 42 L 45 42" stroke="#5b6d76" stroke-width="2.1" fill="none"/>
<path d="M 9 35 L 18 27 L 25 31 L 34 15 L 43 20" fill="none" stroke="#455b68" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="18" cy="27" r="2.4" fill="#455b68"/><circle cx="34" cy="15" r="2.4" fill="#455b68"/>
<path d="M 14 42 L 14 36 M 24 42 L 24 36 M 34 42 L 34 36" stroke="#9daeb6" stroke-width="1.2"/>
'''


def icon_updown() -> str:
    return f'''
<path d="M 10 39 L 10 7" stroke="#4775a6" stroke-width="5" stroke-linecap="round"/>
<path d="M 10 1 L 2 13 L 18 13 Z" fill="#4775a6"/>
<path d="M 29 3 L 29 35" stroke="#66a160" stroke-width="5" stroke-linecap="round"/>
<path d="M 29 41 L 21 29 L 37 29 Z" fill="#66a160"/>
'''


ICONS = {
    "devices": icon_devices,
    "key": icon_key,
    "clock": icon_clock,
    "route": icon_route,
    "calendar": icon_calendar,
    "calendar_pen": icon_calendar_pen,
    "calendar_check": icon_calendar_check,
    "clipboard": icon_clipboard,
    "map": icon_map,
    "db": icon_db,
    "redis": icon_redis,
    "kafka": icon_kafka,
    "search": icon_search,
    "alarm": icon_alarm,
    "phone_bell": icon_phone_bell,
    "doc": icon_doc,
    "fanout": icon_fanout,
    "sync": icon_sync,
    "chart": icon_chart,
    "updown": icon_updown,
}


# -----------------------------------------------------------------------------
# Loading/export
# -----------------------------------------------------------------------------

def load_spec(path: Path) -> Mapping[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".json"}:
        return json.loads(text)
    if yaml is None:
        raise RuntimeError("PyYAML is not installed. Install requirements.txt or use JSON input.")
    data = yaml.safe_load(text)
    if not isinstance(data, Mapping):
        raise ValueError(f"Spec must be a mapping: {path}")
    return data


def export_svg(svg: str, out_base: Path) -> Path:
    out_path = out_base.with_suffix(".svg")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")
    return out_path


def export_png(svg: str, out_base: Path, scale: float = 1.0) -> Path:
    try:
        import cairosvg  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PNG export requires CairoSVG. Install requirements.txt.") from exc
    out_path = out_base.with_suffix(".png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(out_path), scale=scale)
    return out_path


def export_pdf(svg: str, out_base: Path) -> Path:
    try:
        import cairosvg  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PDF export requires CairoSVG. Install requirements.txt.") from exc
    out_path = out_base.with_suffix(".pdf")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2pdf(bytestring=svg.encode("utf-8"), write_to=str(out_path))
    return out_path


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Render fixed-layout HLD diagrams in the rounded blueprint style.")
    parser.add_argument("spec", type=Path, help="YAML or JSON diagram spec")
    parser.add_argument("--out", type=Path, default=None, help="Output base path without extension")
    parser.add_argument("--format", choices=["svg", "png", "pdf", "all"], default="svg", help="Export format")
    parser.add_argument("--scale", type=float, default=1.0, help="PNG scale factor")
    parser.add_argument("--guides", action="store_true", help="Overlay 50 px coordinate guides")
    args = parser.parse_args(argv)

    spec = load_spec(args.spec)
    svg = HLDRenderer(spec, guides=args.guides).render()
    out_base = args.out or args.spec.with_suffix("")

    written: List[Path] = []
    if args.format in ("svg", "all"):
        written.append(export_svg(svg, out_base))
    if args.format in ("png", "all"):
        written.append(export_png(svg, out_base, scale=args.scale))
    if args.format in ("pdf", "all"):
        written.append(export_pdf(svg, out_base))

    for p in written:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
