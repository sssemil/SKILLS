from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Optional, Sequence, Tuple, List

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors

from .style import Style


def as_color(value):
    if isinstance(value, str):
        return colors.HexColor(value)
    return value


def y_from_top(style: Style, y_top: float) -> float:
    return style.page.height - y_top


def set_stroke(c: Canvas, color, width: float = 0.6067, dash: Optional[Sequence[float]] = None) -> None:
    c.setStrokeColor(as_color(color))
    c.setLineWidth(width)
    if dash:
        c.setDash(list(dash))
    else:
        c.setDash()


def fill_page(c: Canvas, style: Style) -> None:
    """White paper with the inset warm panel visible in the reference."""
    pal = style.palette
    c.setFillColor(pal.white)
    c.rect(0, 0, style.page.width, style.page.height, stroke=0, fill=1)
    c.setFillColor(pal.page)
    # Reference artboard: 12 pt left/right, 18 pt top/bottom.
    c.rect(12, 18, style.page.width - 24, style.page.height - 36, stroke=0, fill=1)



def field_clip_path(c: Canvas, style: Style):
    path = c.beginPath()
    path.rect(12, 18, style.page.width - 24, style.page.height - 36)
    return path


def clip_artboard(c: Canvas, style: Style) -> None:
    path = c.beginPath()
    path.rect(12, 18, style.page.width - 24, style.page.height - 36)
    c.clipPath(path, stroke=0, fill=0)


def draw_text(
    c: Canvas,
    style: Style,
    x: float,
    y_top: float,
    text: str,
    font: Optional[str] = None,
    size: float = 9.3336,
    color=None,
    tracking: float = 0,
    hscale: float = 100.0,
) -> None:
    color = color or style.palette.text
    font = font or style.fonts.medium
    c.setFillColor(as_color(color))
    c.setFont(font, size)
    text = str(text).replace("\u2014", "-").replace("\u2013", "-")
    if tracking or float(hscale) != 100.0:
        tx = c.beginText(x, y_from_top(style, y_top) - size)
        tx.setFont(font, size)
        if float(hscale) != 100.0:
            tx.setHorizScale(float(hscale))
        if tracking:
            tx.setCharSpace(tracking)
        tx.textLine(text)
        c.drawText(tx)
    else:
        c.drawString(x, y_from_top(style, y_top) - size, text)


def draw_centered_text(
    c: Canvas,
    style: Style,
    x: float,
    y_top: float,
    w: float,
    text: str,
    font: Optional[str] = None,
    size: float = 9.3336,
    color=None,
) -> None:
    color = color or style.palette.text
    c.setFillColor(as_color(color))
    c.setFont(font or style.fonts.medium, size)
    c.drawCentredString(x + w / 2, y_from_top(style, y_top) - size, str(text))


def wrap_lines(text: str, font: str, size: float, width: float) -> List[str]:
    text = str(text).replace("\u2014", "-").replace("\u2013", "-").replace("\ufb02", "fl").replace("\ufb01", "fi").strip()
    if not text:
        return []
    result: List[str] = []
    for para in text.split("\n"):
        words = re.split(r"\s+", para.strip())
        line = ""
        for word in words:
            candidate = word if not line else f"{line} {word}"
            if pdfmetrics.stringWidth(candidate, font, size) <= width:
                line = candidate
            else:
                if line:
                    result.append(line)
                if pdfmetrics.stringWidth(word, font, size) > width:
                    chunk = ""
                    for ch in word:
                        cand = chunk + ch
                        if pdfmetrics.stringWidth(cand, font, size) <= width:
                            chunk = cand
                        else:
                            if chunk:
                                result.append(chunk)
                            chunk = ch
                    line = chunk
                else:
                    line = word
        if line:
            result.append(line)
    return result


def draw_wrapped(
    c: Canvas,
    style: Style,
    x: float,
    y_top: float,
    width: float,
    text: str,
    font: Optional[str] = None,
    size: float = 9.3336,
    leading: Optional[float] = None,
    color=None,
    max_lines: Optional[int] = None,
) -> float:
    font = font or style.fonts.medium
    leading = leading or size * 1.4
    color = color or style.palette.text
    lines = wrap_lines(text, font, size, width)
    if max_lines is not None:
        lines = lines[:max_lines]
    c.setFillColor(as_color(color))
    c.setFont(font, size)
    y = y_top
    for line in lines:
        c.drawString(x, y_from_top(style, y) - size, line)
        y += leading
    return y




def _rich_tokens(text: str):
    """Tiny inline markup: **bold**, [[blue:text]], [[link:text]]."""
    pattern = re.compile(r"(\*\*.*?\*\*|\[\[(?:blue|link):.*?\]\])")
    pos = 0
    for m in pattern.finditer(str(text)):
        if m.start() > pos:
            yield {"text": text[pos:m.start()], "font": "medium", "color": "text"}
        tok = m.group(0)
        if tok.startswith("**"):
            yield {"text": tok[2:-2], "font": "semibold", "color": "text"}
        elif tok.startswith("[[blue:"):
            yield {"text": tok[7:-2], "font": "medium", "color": "blue"}
        elif tok.startswith("[[link:"):
            yield {"text": tok[7:-2], "font": "medium", "color": "blue", "underline": True}
        pos = m.end()
    if pos < len(str(text)):
        yield {"text": str(text)[pos:], "font": "medium", "color": "text"}


def draw_rich_wrapped(
    c: Canvas,
    style: Style,
    x: float,
    y_top: float,
    width: float,
    text: str,
    size: Optional[float] = None,
    leading: Optional[float] = None,
) -> float:
    """Draw a compact paragraph with minimal inline bold/blue/link markup."""
    size = size or style.body_size
    leading = leading or style.body_leading
    font_map = {"regular": style.fonts.regular, "medium": style.fonts.medium, "semibold": style.fonts.semibold, "bold": style.fonts.bold}
    color_map = {"text": style.palette.text, "blue": style.palette.blue}
    tokens = []
    for t in _rich_tokens(str(text).replace("\u2014", "-").replace("\u2013", "-")):
        # Preserve spaces as tokens while still wrapping on words.
        for part in re.findall(r"\S+\s*|\s+", t["text"]):
            if not part:
                continue
            nt = dict(t)
            nt["text"] = part
            tokens.append(nt)
    lines = []
    cur = []
    cur_w = 0.0
    for t in tokens:
        piece = t["text"]
        fnt = font_map.get(t.get("font", "medium"), style.fonts.medium)
        pw = pdfmetrics.stringWidth(piece, fnt, size)
        if cur and cur_w + pw > width and piece.strip():
            lines.append(cur)
            cur, cur_w = [], 0.0
        cur.append(t)
        cur_w += pw
    if cur:
        lines.append(cur)
    y = y_top
    for line in lines:
        xx = x
        for t in line:
            piece = t["text"]
            fnt = font_map.get(t.get("font", "medium"), style.fonts.medium)
            col = color_map.get(t.get("color", "text"), style.palette.text)
            draw_text(c, style, xx, y, piece, font=fnt, size=size, color=col)
            tw = pdfmetrics.stringWidth(piece, fnt, size)
            if t.get("underline"):
                set_stroke(c, style.palette.blue, 0.45)
                line_top(c, style, xx, y + size + 1.7, xx + tw, y + size + 1.7)
            xx += tw
        y += leading
    return y


def measure_wrapped(style: Style, width: float, text: str, font: Optional[str] = None, size: float = 9.3336, leading: Optional[float] = None) -> float:
    font = font or style.fonts.medium
    leading = leading or size * 1.4
    return len(wrap_lines(text, font, size, width)) * leading


def draw_marked_list(
    c: Canvas,
    style: Style,
    x: float,
    y_top: float,
    width: float,
    items: Sequence,
    markers: Optional[Sequence[str]] = None,
    size: Optional[float] = None,
    leading: Optional[float] = None,
    row_gap: float = 26.1,
    rule: bool = True,
    marker_w: float = 8.0,
) -> float:
    size = size or style.body_size
    leading = leading or style.body_leading
    markers = markers or ["i) ", "ii) ", "iii) ", "iv) ", "v) ", "vi) "]
    y = y_top
    for i, item in enumerate(items):
        if isinstance(item, dict):
            marker = str(item.get("marker", markers[i] if i < len(markers) else f"{i + 1})"))
            text = str(item.get("text", item.get("body", "")))
        else:
            marker = markers[i] if i < len(markers) else f"{i + 1})"
            text = str(item)
        draw_text(c, style, x, y, marker, font=style.fonts.medium, size=size, color=style.palette.blue)
        this_marker_w = max(marker_w, pdfmetrics.stringWidth(marker, style.fonts.medium, size))
        text_w = width - this_marker_w
        draw_wrapped(c, style, x + this_marker_w, y, text_w, text, font=style.fonts.medium, size=size, leading=leading)
        line_count = max(1, len(wrap_lines(text, style.fonts.medium, size, text_w)))
        item_h = line_count * leading
        if rule and i < len(items) - 1:
            set_stroke(c, style.palette.line_pale, 0.55)
            line_top(c, style, x, y + max(18.55, item_h + 2.5), x + width, y + max(18.55, item_h + 2.5))
        y += max(row_gap, item_h + 8.0)
    return y


def draw_body_blocks(
    c: Canvas,
    style: Style,
    x: float,
    y_top: float,
    width: float,
    blocks,
    gap: float = 12.0,
    size: Optional[float] = None,
    leading: Optional[float] = None,
) -> float:
    y = y_top
    if isinstance(blocks, str):
        blocks = [blocks]
    for block in blocks or []:
        if block is None:
            continue
        if isinstance(block, dict):
            btype = str(block.get("type", "paragraph")).lower().strip()
            if btype in {"spacer", "space"}:
                y += float(block.get("height", block.get("amount", gap)))
                continue
            if btype in {"list", "marked_list", "roman_list", "blue_list"}:
                y = draw_marked_list(
                    c,
                    style,
                    x + float(block.get("indent", 0)),
                    y,
                    width - float(block.get("indent", 0)),
                    block.get("items", []),
                    markers=block.get("markers"),
                    size=float(block.get("size", size or style.body_size)),
                    leading=float(block.get("leading", leading or style.body_leading)),
                    row_gap=float(block.get("row_gap", 26.1)),
                    rule=bool(block.get("rule", True)),
                    marker_w=float(block.get("marker_w", 8.0)),
                )
                y += float(block.get("gap", gap))
                continue
            if btype == "rule":
                set_stroke(c, style.palette.line_pale, float(block.get("width", 0.55)))
                line_top(c, style, x, y, x + width, y)
                y += float(block.get("gap", gap))
                continue
            if btype in {"rich", "markup", "rich_paragraph"}:
                indent = float(block.get("indent", 0))
                wrap_width = (width - indent) * float(block.get("wrap_factor", getattr(style, "body_wrap_width_factor", 1.0)))
                y = draw_rich_wrapped(c, style, x + indent, y, wrap_width, block.get("text", block.get("body", "")), size=float(block.get("size", size or style.body_size)), leading=float(block.get("leading", leading or style.body_leading)))
                y += float(block.get("gap", gap))
                continue
            if btype in {"absolute_lines", "fixed_lines", "line_art"}:
                # Draw source-measured spans at absolute page coordinates.
                # Useful when reproducing a reference brief where line breaks and
                # inline styling must not be recalculated by ReportLab.
                font_map = {
                    "regular": style.fonts.regular,
                    "medium": style.fonts.medium,
                    "semibold": style.fonts.semibold,
                    "bold": style.fonts.bold,
                }
                max_baseline = y
                for item in block.get("lines", []):
                    if not item:
                        continue
                    text = str(item.get("text", "")).replace("\ufb01", "fi").replace("\ufb02", "fl").replace("\u2013", "-").replace("\u2014", "-")
                    if not text:
                        continue
                    fkey = str(item.get("font", block.get("font", "medium"))).lower().strip()
                    fnt = font_map.get(fkey, style.fonts.medium)
                    fsize = float(item.get("size", size or style.body_size))
                    color = item.get("color", style.palette.text)
                    c.setFillColor(as_color(color))
                    c.setFont(fnt, fsize)
                    xx = float(item.get("x", x))
                    if "baseline_y" in item:
                        baseline = float(item["baseline_y"])
                        c.drawString(xx, y_from_top(style, baseline), text)
                        max_baseline = max(max_baseline, baseline)
                    else:
                        y_abs = float(item.get("y", item.get("y_top", y)))
                        c.drawString(xx, y_from_top(style, y_abs) - fsize, text)
                        max_baseline = max(max_baseline, y_abs + fsize)
                y = max(y, max_baseline + float(block.get("gap", 0)))
                continue
            text = block.get("text") or block.get("body") or ""
            bfont_key = str(block.get("font", "medium")).lower()
            bfont = {"regular": style.fonts.regular, "medium": style.fonts.medium, "semibold": style.fonts.semibold, "bold": style.fonts.bold}.get(bfont_key, style.fonts.medium)
            indent = float(block.get("indent", 0))
            wrap_width = (width - indent) * float(block.get("wrap_factor", getattr(style, "body_wrap_width_factor", 1.0)))
            y = draw_wrapped(c, style, x + indent, y, wrap_width, text, font=bfont, size=float(block.get("size", size or style.body_size)), leading=float(block.get("leading", leading or style.body_leading)))
            y += float(block.get("gap", gap))
        else:
            wrap_width = width * getattr(style, "body_wrap_width_factor", 1.0)
            y = draw_wrapped(c, style, x, y, wrap_width, str(block), font=style.fonts.medium, size=size or style.body_size, leading=leading or style.body_leading)
            y += gap
    return y


def draw_paragraphs(
    c: Canvas,
    style: Style,
    x: float,
    y_top: float,
    width: float,
    paragraphs: Sequence[str],
    font: Optional[str] = None,
    size: Optional[float] = None,
    leading: Optional[float] = None,
    gap: float = 12.0,
) -> float:
    # Keep old name; now delegates to block-aware body drawing.
    return draw_body_blocks(c, style, x, y_top, width, paragraphs, gap=gap, size=size, leading=leading)


def rect_top(c: Canvas, style: Style, x: float, y_top: float, w: float, h: float, stroke=1, fill=0, radius: float = 0) -> None:
    y = style.page.height - y_top - h
    if radius and radius > 0:
        c.roundRect(x, y, w, h, radius, stroke=stroke, fill=fill)
    else:
        c.rect(x, y, w, h, stroke=stroke, fill=fill)


def line_top(c: Canvas, style: Style, x1: float, y1_top: float, x2: float, y2_top: float) -> None:
    c.line(x1, y_from_top(style, y1_top), x2, y_from_top(style, y2_top))


def polyline_top(c: Canvas, style: Style, points: Sequence[Tuple[float, float]]) -> None:
    if len(points) < 2:
        return
    path = c.beginPath()
    x0, y0 = points[0]
    path.moveTo(x0, y_from_top(style, y0))
    for x, y in points[1:]:
        path.lineTo(x, y_from_top(style, y))
    c.drawPath(path, stroke=1, fill=0)


def arrow_head(c: Canvas, style: Style, x1: float, y1_top: float, x2: float, y2_top: float, size: float = 3.8) -> None:
    dx = x2 - x1
    dy = y2_top - y1_top
    angle = math.atan2(dy, dx)
    a1 = angle + math.pi * 0.82
    a2 = angle - math.pi * 0.82
    p1 = (x2 + size * math.cos(a1), y2_top + size * math.sin(a1))
    p2 = (x2 + size * math.cos(a2), y2_top + size * math.sin(a2))
    polyline_top(c, style, [(x2, y2_top), p1])
    polyline_top(c, style, [(x2, y2_top), p2])


def arrow(c: Canvas, style: Style, x1: float, y1_top: float, x2: float, y2_top: float, color=None, width: float = 0.6067, dash=None) -> None:
    set_stroke(c, color or style.palette.blue, width, dash)
    line_top(c, style, x1, y1_top, x2, y2_top)
    arrow_head(c, style, x1, y1_top, x2, y2_top, 3.5)
    c.setDash()


def connector(c: Canvas, style: Style, points: Sequence[Tuple[float, float]], color=None, width: float = 0.6067, dash=None, head: bool = True) -> None:
    if len(points) < 2:
        return
    set_stroke(c, color or style.palette.blue, width, dash)
    polyline_top(c, style, points)
    if head:
        arrow_head(c, style, points[-2][0], points[-2][1], points[-1][0], points[-1][1], 3.5)
    c.setDash()


def box(
    c: Canvas,
    style: Style,
    x: float,
    y_top: float,
    w: float,
    h: float,
    title: str = "",
    body: str = "",
    label: str = "",
    fill=None,
    stroke=None,
    dashed: bool = False,
    accent: Optional[str] = None,
    title_size: float = 8.4,
    body_size: float = 7.0,
    label_size: float = 5.6,
    pad: float = 8,
    center: bool = False,
) -> None:
    pal = style.palette
    c.saveState()
    c.setFillColor(as_color(fill or pal.page))
    set_stroke(c, as_color(stroke or pal.text), style.box_line, style.dash if dashed else None)
    rect_top(c, style, x, y_top, w, h, stroke=1, fill=1)
    c.setDash()
    if accent == "left":
        c.setFillColor(pal.blue)
        rect_top(c, style, x, y_top, 3, h, stroke=0, fill=1)
    elif accent == "top":
        c.setFillColor(pal.blue)
        rect_top(c, style, x, y_top, w, 3, stroke=0, fill=1)
    yy = y_top + pad
    if label:
        draw_wrapped(c, style, x + pad, yy, w - 2 * pad, label.upper(), font=style.fonts.semibold, size=label_size, leading=label_size * 1.25, color=pal.blue)
        yy += label_size * 1.35 + 2
    if title:
        if center:
            draw_centered_text(c, style, x + pad, yy, w - 2 * pad, title, font=style.fonts.semibold, size=title_size, color=pal.text)
            yy += title_size * 1.25
        else:
            yy = draw_wrapped(c, style, x + pad, yy, w - 2 * pad, title, font=style.fonts.semibold, size=title_size, leading=title_size * 1.25, color=pal.text)
            yy += 2
    if body:
        if center:
            lines = wrap_lines(body, style.fonts.medium, body_size, w - 2 * pad)
            for line in lines[:5]:
                draw_centered_text(c, style, x + pad, yy, w - 2 * pad, line, font=style.fonts.medium, size=body_size, color=pal.text)
                yy += body_size * 1.25
        else:
            draw_wrapped(c, style, x + pad, yy, w - 2 * pad, body, font=style.fonts.medium, size=body_size, leading=body_size * 1.25, color=pal.text)
    c.restoreState()


def tag(c: Canvas, style: Style, x: float, y_top: float, text: str, size: float = 5.6, fill=None, stroke=None, color=None) -> float:
    font = style.fonts.semibold
    pad_x, pad_y = 2.2, 1.5
    text = str(text)
    w = pdfmetrics.stringWidth(text, font, size) + pad_x * 2
    h = size + pad_y * 2
    c.saveState()
    c.setFillColor(as_color(fill or style.palette.blue_faint))
    set_stroke(c, as_color(stroke or style.palette.blue), 0.6)
    rect_top(c, style, x, y_top, w, h, stroke=1, fill=1)
    draw_text(c, style, x + pad_x, y_top + pad_y, text, font=font, size=size, color=color or style.palette.blue)
    c.restoreState()
    return w


def draw_caption(c: Canvas, style: Style, x: float, y_top: float, fig_no: str, title: str) -> None:
    prefix = f"Fig. {fig_no} "
    draw_text(c, style, x, y_top, prefix, font=style.fonts.semibold, size=style.caption_size, color=style.palette.blue)
    prefix_w = pdfmetrics.stringWidth(prefix, style.fonts.semibold, style.caption_size)
    draw_text(c, style, x + prefix_w, y_top, title, font=style.fonts.semibold, size=style.caption_size, color=style.palette.text)


def draw_wordmark(c: Canvas, style: Style, x: float, y_top: float, word: Optional[str] = None, size: float = 10) -> None:
    """Draw a small generic wordmark, or a user-supplied logo image if provided.

    No proprietary logo asset is included. `style.logo_path` may point to an image
    that the user is allowed to use.
    """
    if not style.draw_brand:
        return
    if style.logo_path:
        logo = Path(style.logo_path).expanduser()
        if logo.exists():
            c.drawImage(str(logo), x, y_from_top(style, y_top) - size, height=size, width=size * 4.0,
                        preserveAspectRatio=True, mask="auto")
            return
    word = word if word is not None else style.brand
    pal = style.palette
    c.saveState()
    set_stroke(c, pal.text, max(size * 0.12, 0.8))
    cy = y_from_top(style, y_top) - size * 0.55
    c.circle(x + size * 0.42, cy + size * 0.28, size * 0.38, stroke=1, fill=0)
    c.line(x + size * 0.12, cy - size * 0.12, x + size * 0.42, cy - size * 0.28)
    c.line(x + size * 0.42, cy - size * 0.28, x + size * 0.72, cy - size * 0.12)
    c.setFont(style.fonts.medium, size)
    c.setFillColor(pal.text)
    c.drawString(x + size * 0.95, y_from_top(style, y_top) - size, word)
    c.restoreState()


def draw_footer(c: Canvas, style: Style, page_num: int, cover: bool = False) -> None:
    if cover:
        return
    pal = style.palette
    y = style.page.footer_y_top
    if page_num % 2 == 1:
        draw_wordmark(c, style, 70.8, y - 2, size=8.6)
        draw_text(c, style, style.page.width - 65.5, y, str(page_num), font=style.fonts.medium, size=style.footer_size, color=pal.text)
    else:
        draw_text(c, style, 58.7, y, str(page_num), font=style.fonts.medium, size=style.footer_size, color=pal.text)
        x = 417.0
        base = style.doc_title + (" " if style.doc_title_accent else "")
        draw_text(c, style, x, y, base, font=style.fonts.medium, size=style.footer_size, color=pal.text)
        w = pdfmetrics.stringWidth(base, style.fonts.medium, style.footer_size)
        if style.doc_title_accent:
            draw_text(c, style, x + w, y, style.doc_title_accent, font=style.fonts.medium, size=style.footer_size, color=pal.blue)


def section_side_heading(c: Canvas, style: Style, x: float, y_top: float, number: str, title: str) -> None:
    draw_text(c, style, x, y_top, number, font=style.fonts.semibold, size=style.section_num_size, color=style.palette.blue)
    y = y_top + 17.7
    for line in str(title).split("\n"):
        draw_text(c, style, x, y, line, font=style.fonts.semibold, size=style.rail_title_size, color=style.palette.text)
        y += 17.75


def blue_rule(c: Canvas, style: Style, x1: float, y_top: float, x2: float) -> None:
    set_stroke(c, style.palette.blue, style.blue_line)
    line_top(c, style, x1, y_top, x2, y_top)
