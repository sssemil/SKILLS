from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import yaml
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics

from .figures import draw_figure
from .primitives import (
    arrow,
    blue_rule,
    box,
    clip_artboard,
    connector,
    draw_body_blocks,
    draw_caption,
    draw_footer,
    draw_paragraphs,
    draw_text,
    draw_wordmark,
    draw_wrapped,
    fill_page,
    line_top,
    rect_top,
    section_side_heading,
    set_stroke,
    wrap_lines,
    y_from_top,
)
from .style import Style, build_style


def load_config(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text) or {}
    return json.loads(text)


def rail_title_lines(style: Style, title: str, width: float | None = None) -> str:
    if "\n" in title:
        return title
    width = width or style.page.rail_w
    lines = wrap_lines(title, style.fonts.semibold, style.rail_title_size, width)
    return "\n".join(lines)


class BriefRenderer:
    def __init__(self, config: Dict[str, Any], output: str | Path):
        self.config = config
        self.style = build_style(config)
        self.output = Path(output)
        self.c = Canvas(str(self.output), pagesize=(self.style.page.width, self.style.page.height))
        self.page_num = 0

    def save(self) -> Path:
        pages = self.config.get("pages") or []
        if not isinstance(pages, list) or not pages:
            raise ValueError("brief config must contain a non-empty 'pages' list")
        for page in pages:
            self.render_page(page)
        self.c.save()
        return self.output

    def start_page(self) -> None:
        self.page_num += 1
        fill_page(self.c, self.style)

    def end_page(self, cover: bool = False, footer: bool = True) -> None:
        if footer:
            draw_footer(self.c, self.style, self.page_num, cover=cover)
        self.c.showPage()

    def render_page(self, page: Dict[str, Any]) -> None:
        ptype = (page.get("type") or "step").strip().lower().replace("-", "_")
        if ptype == "cover":
            self.render_cover(page)
        elif ptype in {"pattern", "pattern_page"}:
            self.render_pattern_page(page)
        elif ptype in {"toc", "contents"}:
            self.render_toc(page)
        elif ptype in {"section_divider", "section"}:
            self.render_section_divider(page)
        elif ptype in {"figure_full", "full_figure"}:
            self.render_full_figure(page)
        elif ptype in {"back_cover", "logo_page"}:
            self.render_back_cover(page)
        elif ptype == "blank":
            self.start_page()
            self.end_page(footer=page.get("footer", True))
        elif ptype in {"step", "text_page", "text"}:
            self.render_step(page)
        else:
            raise ValueError(f"unknown page type: {ptype!r}")

    def render_cover(self, page: Dict[str, Any]) -> None:
        s = self.style
        p = s.palette
        self.start_page()
        brand = page.get("brand", s.brand)
        if page.get("draw_brand", s.draw_brand):
            draw_wordmark(self.c, s, float(page.get("brand_x", 54.7)), float(page.get("brand_y", 64.0)), word=brand, size=float(page.get("brand_size", 19.0)))
        title_lines = page.get("title_lines") or [
            {"text": page.get("title", "Institutional\nSovereignty\nin the\nAge of AI"), "color": "auto"}
        ]
        y = float(page.get("title_y", 211.0))
        x = float(page.get("title_x", 52.1))
        size = float(page.get("title_size", 87.08))
        leading = float(page.get("title_leading", 78.1))
        # Support either a list of strings or list of {text,color} spans; color applies per line block.
        for item in title_lines:
            if isinstance(item, str):
                text = item
                color = p.text
            else:
                text = item.get("text", "")
                cval = item.get("color", "text")
                color = p.blue if cval in {"blue", "accent"} else p.text
            item_x = float(item.get("x", x)) if isinstance(item, dict) else x
            item_hscale = float(item.get("scale_x", item.get("hscale", 100.0))) if isinstance(item, dict) else 100.0
            for line in str(text).split("\n"):
                draw_text(self.c, s, item_x, y, line, font=s.fonts.medium, size=size, color=color, hscale=item_hscale)
                y += leading
        subtitle = page.get("subtitle")
        if subtitle:
            draw_wrapped(self.c, s, float(page.get("subtitle_x", 55.9)), float(page.get("subtitle_y", 669.5)), float(page.get("subtitle_w", 285)), subtitle, font=s.fonts.semibold, size=float(page.get("subtitle_size", 15.87)), leading=float(page.get("subtitle_leading", 17.74)))
        self.end_page(cover=True, footer=False)

    def render_pattern_page(self, page: Dict[str, Any]) -> None:
        s = self.style
        pal = s.palette
        self.start_page()
        # Reference construction: a field-clipped family of kinked diagonals.
        # Each stroke runs from above the page to the center crease and out below it.
        y0 = float(page.get("line_y0", -4.8076))
        ymid = float(page.get("line_ymid", 395.9973))
        y2 = float(page.get("line_y2", 796.8114))
        x0 = float(page.get("line_x0", -384.3107))
        dx = float(page.get("line_dx", 400.8049))
        spacing = float(page.get("spacing", 12.96815))
        count = int(page.get("line_count", 74))
        line_w = float(page.get("line_width", s.motif_stroke))
        self.c.saveState()
        clip_artboard(self.c, s)
        for i in range(count):
            xx = x0 + i * spacing
            connector(self.c, s, [(xx, y0), (xx + dx, ymid), (xx, y2)], color=pal.blue, width=line_w, head=False)
        self.c.restoreState()
        mark = page.get("page_mark")
        if mark:
            draw_text(self.c, s, 58.7, 722.7, str(mark), font=s.fonts.medium, size=s.footer_size, color=pal.blue)
        self.end_page(cover=False, footer=False)

    def render_toc(self, page: Dict[str, Any]) -> None:
        s = self.style
        pal = s.palette
        self.start_page()
        sections = page.get("sections") or []
        x_sec = float(page.get("section_x", 70.8))
        x_num = float(page.get("number_x", 237.2))
        x_title = float(page.get("title_x", 262.2))
        y_positions = page.get("section_y") or [61.793, 152.017, 241.266, 331.371]
        row_gap = float(page.get("row_gap", 26.134))

        # Reference-like blue rules: thin item separators plus full-width section breaks.
        set_stroke(self.c, pal.blue, 0.7467)
        for yy in page.get("section_rules", [140.844, 230.092, 320.422]):
            line_top(self.c, s, 72.219, yy, 552.929, yy)
        set_stroke(self.c, pal.line_pale, 0.7467)
        for si, sec in enumerate(sections):
            y = float(y_positions[si]) if si < len(y_positions) else float(y_positions[-1]) + 90 * (si - len(y_positions) + 1)
            row_y = y + 1.9
            items = sec.get("items", [])
            for i in range(max(0, len(items) - 1)):
                rule_y = row_y + (i + 1) * row_gap - 7.48
                line_top(self.c, s, x_num, rule_y, 553.34, rule_y)

        for si, sec in enumerate(sections):
            y = float(y_positions[si]) if si < len(y_positions) else float(y_positions[-1]) + 90 * (si - len(y_positions) + 1)
            draw_text(self.c, s, x_sec, y, sec.get("title", "Section"), font=s.fonts.semibold, size=s.toc_section_size, color=pal.text)
            row_y = y + 1.9
            for item in sec.get("items", []):
                draw_text(self.c, s, x_num, row_y, item.get("number", ""), font=s.fonts.medium, size=s.toc_size, color=pal.blue)
                draw_wrapped(self.c, s, x_title, row_y, 290, item.get("title", ""), font=s.fonts.medium, size=s.toc_size, leading=13.0)
                row_y += row_gap
        note = page.get("note")
        if note:
            draw_wrapped(self.c, s, x_num, float(page.get("note_y", 492.1)), float(page.get("note_w", 316.0)), note, font=s.fonts.medium, size=s.toc_size, leading=13.07)
        self.end_page()

    def _draw_section_surface_blank(self, polygon: Sequence[tuple[float, float]]) -> None:
        """Mask lower motif lines with a cream section surface and re-stroke its edge."""
        s = self.style
        pal = s.palette
        c = self.c
        path = c.beginPath()
        x0, y0 = polygon[0]
        path.moveTo(x0, y_from_top(s, y0))
        for x1, y1 in polygon[1:]:
            path.lineTo(x1, y_from_top(s, y1))
        path.close()
        c.saveState()
        clip_artboard(c, s)
        c.setFillColor(pal.page)
        c.drawPath(path, stroke=0, fill=1)
        c.restoreState()
        closed = list(polygon) + [polygon[0]]
        connector(c, s, closed, color=pal.blue, width=s.motif_stroke, head=False)


    def _draw_hatched_section_surface(self, polygon: Sequence[tuple[float, float]], spacing: float = 7.2) -> None:
        """Draw reference-style blue diagonal hatching clipped to a section-surface polygon."""
        s = self.style
        pal = s.palette
        c = self.c
        # Mask any lower motif lines that would sit behind this surface.
        base_path = c.beginPath()
        x0, y0 = polygon[0]
        base_path.moveTo(x0, y_from_top(s, y0))
        for x1, y1 in polygon[1:]:
            base_path.lineTo(x1, y_from_top(s, y1))
        base_path.close()
        c.saveState()
        clip_artboard(c, s)
        c.setFillColor(pal.page)
        c.drawPath(base_path, stroke=0, fill=1)
        c.restoreState()

        c.saveState()
        clip_artboard(c, s)
        clip_path = c.beginPath()
        clip_path.moveTo(x0, y_from_top(s, y0))
        for x1, y1 in polygon[1:]:
            clip_path.lineTo(x1, y_from_top(s, y1))
        clip_path.close()
        c.clipPath(clip_path, stroke=0, fill=0)
        set_stroke(c, pal.blue, s.motif_stroke)
        slope = 136.3924 / 325.7438
        x_left, x_right = -360.0, 970.0
        # b is the top-coordinate intercept in y = b + slope*x.
        b_min = min(y - slope * x for x, y in polygon) - 360
        b_max = max(y - slope * x for x, y in polygon) + 360
        b = b_min
        while b <= b_max:
            line_top(c, s, x_left, b + slope * x_left, x_right, b + slope * x_right)
            b += spacing
        c.restoreState()

        # Re-stroke the surface outline after clipping, matching the reference layer edge.
        closed = list(polygon) + [polygon[0]]
        connector(c, s, closed, color=pal.blue, width=s.motif_stroke, head=False)


    def render_section_divider(self, page: Dict[str, Any]) -> None:
        s = self.style
        pal = s.palette
        self.start_page()
        title = page.get("title", "Section")
        title_x = float(page.get("title_x", 54.0))
        title_y = float(page.get("title_y", 49.0))
        title_size = float(page.get("title_size", 59.7353))
        for i, line in enumerate(str(title).split("\n")):
            draw_text(self.c, s, title_x, title_y + 52.3 * i, line, font=s.fonts.medium, size=title_size, color=pal.text, hscale=float(page.get("title_scale_x", 103.7)))
        motif_width = float(page.get("motif_line_width", s.motif_stroke))
        motif = page.get("motif") or [
            [(306.0, 188.3705), (631.7438, 324.7629), (306.0, 461.1646), (-19.7438, 324.7629), (306.0, 188.3705)],
            [(306.0, 288.1825), (631.7438, 424.5749), (306.0, 560.9766), (-19.7438, 424.5749), (306.0, 288.1825)],
            [(305.8805, 388.2260), (631.6243, 524.6184), (305.8805, 661.0201), (-19.8633, 524.6184), (305.8805, 388.2260)],
        ]
        self.c.saveState()
        clip_artboard(self.c, s)
        for pts in motif:
            connector(self.c, s, pts, color=pal.blue, width=motif_width, head=False)
        self.c.restoreState()

        hatch = str(page.get("hatch", "")).lower().strip()
        if hatch:
            d1 = [(-19.7438, 324.7629), (306.0, 188.3705), (631.7438, 324.7629), (306.0, 461.1646)]
            band12 = [(-19.7438, 324.7629), (306.0, 461.1646), (631.7438, 324.7629), (631.7438, 424.5749), (306.0, 560.9766), (-19.7438, 424.5749)]
            band23 = [(-19.8633, 424.5749), (305.8805, 560.9766), (631.6243, 424.5749), (631.6243, 524.6184), (305.8805, 661.0201), (-19.8633, 524.6184)]
            spacing = float(page.get("hatch_spacing", 7.2))
            if hatch in {"top", "model"}:
                self._draw_hatched_section_surface(d1, spacing=spacing)
            elif hatch in {"middle", "compute"}:
                self._draw_section_surface_blank(d1)
                self._draw_hatched_section_surface(band12, spacing=spacing)
            elif hatch in {"bottom", "control"}:
                self._draw_section_surface_blank(d1)
                self._draw_section_surface_blank(band12)
                self._draw_hatched_section_surface(band23, spacing=spacing)
            else:
                self._draw_hatched_section_surface(d1, spacing=spacing)

        self.end_page()

    def render_full_figure(self, page: Dict[str, Any]) -> None:
        s = self.style
        self.start_page()
        x = float(page.get("x", s.page.fig_x_odd if self.page_num % 2 == 1 else s.page.fig_x_even))
        w = float(page.get("w", s.page.fig_w_odd if self.page_num % 2 == 1 else s.page.fig_w_even))
        y = float(page.get("y", 62))
        body_y = y
        if "caption" in page or "fig_no" in page:
            draw_caption(self.c, s, x, y, str(page.get("fig_no", "")), page.get("caption", ""))
            body_y = float(page.get("figure_y", y + 26))
        h = float(page.get("h", 600))
        draw_figure(self.c, s, page.get("figure", page), x, body_y, w, h)
        self.end_page()

    def render_back_cover(self, page: Dict[str, Any]) -> None:
        s = self.style
        self.start_page()
        draw_wordmark(self.c, s, float(page.get("brand_x", 255.0)), float(page.get("brand_y", 394.0)), word=page.get("brand", s.brand), size=float(page.get("brand_size", 19.0)))
        self.end_page(cover=True, footer=False)

    def render_step(self, page: Dict[str, Any]) -> None:
        s = self.style
        pal = s.palette
        self.start_page()
        odd = self.page_num % 2 == 1
        rail_x = s.page.rail_x_odd if odd else s.page.rail_x_even
        body_x = s.page.body_x_odd if odd else s.page.body_x_even
        body_w = s.page.body_w_odd if odd else s.page.body_w_even
        fig_x = s.page.fig_x_odd if odd else s.page.fig_x_even
        fig_w = s.page.fig_w_odd if odd else s.page.fig_w_even
        top = float(page.get("top", 60.0))
        number = page.get("number", "I.")
        title = rail_title_lines(s, page.get("title", "Section Title"), width=float(page.get("rail_width", s.page.rail_w)))
        section_side_heading(self.c, s, rail_x, top, number, title)
        body_y = float(page.get("body_y", 62.3))
        paragraphs = page.get("body") or []
        if isinstance(paragraphs, str):
            paragraphs = [paragraphs]
        y_after_body = draw_paragraphs(self.c, s, body_x, body_y, body_w, paragraphs, gap=float(page.get("paragraph_gap", 12.0)))
        figure = page.get("figure")
        if figure:
            cap_y = float(figure.get("caption_y", page.get("caption_y", max(y_after_body + 2, 300))))
            draw_caption(self.c, s, fig_x, cap_y, str(figure.get("fig_no", page.get("fig_no", ""))), figure.get("caption", page.get("caption", "")))
            fig_body_y = float(figure.get("y", cap_y + 26))
            fig_h = float(figure.get("height", figure.get("h", 230)))
            fig_w_actual = float(figure.get("width", fig_w))
            fig_x_actual = float(figure.get("x", fig_x))
            draw_figure(self.c, s, figure, fig_x_actual, fig_body_y, fig_w_actual, fig_h)
            after_body = page.get("body_after_figure") or page.get("after_figure_body") or figure.get("body_after")
            if after_body:
                if isinstance(after_body, str):
                    after_body = [after_body]
                draw_paragraphs(self.c, s, body_x, float(page.get("body_after_y", page.get("after_figure_body_y", fig_body_y + fig_h + 22))), body_w, after_body, gap=float(page.get("paragraph_gap", 12.0)))
        # Optional second section on same page.
        for extra in page.get("extra_sections", []):
            blue_rule(self.c, s, fig_x, float(extra.get("rule_y", 520)), fig_x + fig_w)
            section_side_heading(self.c, s, rail_x, float(extra.get("top", 542)), extra.get("number", ""), rail_title_lines(s, extra.get("title", "")))
            body = extra.get("body") or []
            if isinstance(body, str):
                body = [body]
            draw_paragraphs(self.c, s, body_x, float(extra.get("body_y", extra.get("top", 542) + 2)), body_w, body, gap=float(extra.get("paragraph_gap", 12.0)))
        self.end_page()
