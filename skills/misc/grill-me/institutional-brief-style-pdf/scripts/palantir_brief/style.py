"""Style tokens for a Palantir-style institutional brief.

No proprietary fonts or logos are bundled. The renderer accepts licensed font
paths in YAML. Without those paths it auto-detects Noto Sans Display, then Lato, then falls
back to built-in Helvetica.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def hex_color(value: str) -> colors.Color:
    value = value.strip().lstrip("#")
    return colors.HexColor("#" + value)


@dataclass(frozen=True)
class Palette:
    page: colors.Color = hex_color("FFFFF8")
    paper: colors.Color = hex_color("FFFFFF")
    text: colors.Color = hex_color("212121")
    blue: colors.Color = hex_color("5DACED")
    blue_dark: colors.Color = hex_color("1E75BB")
    blue_light: colors.Color = hex_color("E9F3F6")
    blue_faint: colors.Color = hex_color("E9F3F6")
    line_pale: colors.Color = hex_color("D9EEF8")
    gray: colors.Color = hex_color("919191")
    gray_light: colors.Color = hex_color("F0F1F2")
    orange: colors.Color = hex_color("E87536")
    orange_light: colors.Color = hex_color("F9ECDD")
    white: colors.Color = hex_color("FFFFFF")


@dataclass
class Fonts:
    regular: str = "Helvetica"
    medium: str = "Helvetica"
    semibold: str = "Helvetica-Bold"
    bold: str = "Helvetica-Bold"


_REGISTERED: dict[str, str] = {}


def register_font(name: str, path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"font path not found: {p}")
    key = f"{name}:{p}"
    if key not in _REGISTERED:
        pdfmetrics.registerFont(TTFont(name, str(p)))
        _REGISTERED[key] = name
    return name


def _first_existing(paths: list[str]) -> Optional[str]:
    for path in paths:
        if Path(path).exists():
            return path
    return None


def _auto_font_family(prefix: str, regular_paths: list[str], medium_paths: list[str], semibold_paths: list[str], bold_paths: list[str]) -> Optional[Fonts]:
    regular = _first_existing(regular_paths)
    medium = _first_existing(medium_paths) or regular
    semibold = _first_existing(semibold_paths)
    bold = _first_existing(bold_paths) or semibold
    if not medium or not semibold:
        return None
    return Fonts(
        regular=register_font(f"Brief{prefix}Regular", regular or medium) or "Helvetica",
        medium=register_font(f"Brief{prefix}Medium", medium) or "Helvetica",
        semibold=register_font(f"Brief{prefix}Semibold", semibold) or "Helvetica-Bold",
        bold=register_font(f"Brief{prefix}Bold", bold or semibold) or "Helvetica-Bold",
    )


def _auto_system_fonts() -> Optional[Fonts]:
    # Noto Sans Display is the closest freely installed substitute on this
    # runtime by measured body-line width. Lato remains the next fallback.
    return (
        _auto_font_family(
            "NotoDisplay",
            ["/usr/share/fonts/truetype/noto/NotoSansDisplay-Regular.ttf"],
            ["/usr/share/fonts/truetype/noto/NotoSansDisplay-Medium.ttf", "/usr/share/fonts/truetype/noto/NotoSansDisplay-Regular.ttf"],
            ["/usr/share/fonts/truetype/noto/NotoSansDisplay-SemiBold.ttf", "/usr/share/fonts/truetype/noto/NotoSansDisplay-Bold.ttf"],
            ["/usr/share/fonts/truetype/noto/NotoSansDisplay-Bold.ttf"],
        )
        or _auto_font_family(
            "Lato",
            ["/usr/share/fonts/truetype/lato/Lato-Regular.ttf", "/usr/share/fonts/truetype/lato/Lato-Medium.ttf"],
            ["/usr/share/fonts/truetype/lato/Lato-Medium.ttf", "/usr/share/fonts/truetype/lato/Lato-Regular.ttf"],
            ["/usr/share/fonts/truetype/lato/Lato-Semibold.ttf", "/usr/share/fonts/truetype/lato/Lato-Bold.ttf"],
            ["/usr/share/fonts/truetype/lato/Lato-Bold.ttf", "/usr/share/fonts/truetype/lato/Lato-Heavy.ttf"],
        )
    )


def load_fonts(font_config: Optional[dict] = None) -> Fonts:
    """Register optional user-supplied fonts.

    The reference PDF embeds AllianceNo.2 Medium, SemiBold, and Bold. These files
    are not redistributed here. Use YAML `fonts:` when licensed copies exist.
    """
    if font_config:
        return Fonts(
            regular=register_font("BriefRegular", font_config.get("regular") or font_config.get("medium")) or "Helvetica",
            medium=register_font("BriefMedium", font_config.get("medium") or font_config.get("regular")) or "Helvetica",
            semibold=register_font("BriefSemibold", font_config.get("semibold") or font_config.get("bold")) or "Helvetica-Bold",
            bold=register_font("BriefBold", font_config.get("bold") or font_config.get("semibold")) or "Helvetica-Bold",
        )
    return _auto_system_fonts() or Fonts()


@dataclass
class PageSpec:
    width: float = letter[0]
    height: float = letter[1]
    # Reference artboard: 11.9906, 17.9879, 588.0188, 756.0242.
    bg_x: float = 11.9906
    bg_y_top: float = 17.9879
    bg_w: float = 588.0188
    bg_h: float = 756.0242
    field_x: float = 11.9906
    field_y_top: float = 17.9879
    field_w: float = 588.0188
    field_h: float = 756.0242
    footer_y_top: float = 722.7
    logo_x_odd: float = 70.8
    footer_title_x_even: float = 417.0
    rail_x_even: float = 58.7
    rail_x_odd: float = 70.8
    rail_w: float = 120.0
    body_x_even: float = 224.4
    body_x_odd: float = 237.2
    body_w_even: float = 316.0
    body_w_odd: float = 316.0
    fig_x_even: float = 58.7
    fig_x_odd: float = 70.8
    fig_w_even: float = 480.7
    fig_w_odd: float = 482.5


@dataclass
class Style:
    palette: Palette
    fonts: Fonts
    page: PageSpec
    doc_title: str = "Institutional Sovereignty"
    doc_title_accent: str = "in the Age of AI"
    brand: str = "YourCo"
    draw_brand: bool = True
    logo_path: Optional[str] = None

    body_size: float = 9.3336
    body_leading: float = 13.0668
    # Lato is slightly narrower than AllianceNo.2. Use a narrower wrap width
    # so paragraphs break like the reference without increasing glyph size.
    body_wrap_width_factor: float = 0.975
    caption_size: float = 10.2670
    section_num_size: float = 16.8005
    rail_title_size: float = 16.8005
    footer_size: float = 6.5335
    toc_size: float = 9.3336
    toc_section_size: float = 12.1337
    motif_stroke: float = 1.8667
    line_width: float = 0.6067
    hairline: float = 0.6067
    fig_stroke: float = 0.6067
    box_line: float = 0.6067
    blue_line: float = 0.6067
    motif_line_width: float = 1.8667
    dash: tuple[float, float] = (1.8667, 0.9333)


def build_style(config: Optional[dict] = None) -> Style:
    config = config or {}
    palette = Palette()
    fonts = load_fonts(config.get("fonts"))
    page = PageSpec()
    doc = config.get("document", {})
    return Style(
        palette=palette,
        fonts=fonts,
        page=page,
        doc_title=doc.get("footer_title", doc.get("title", "Institutional Sovereignty")),
        doc_title_accent=doc.get("footer_accent", "in the Age of AI"),
        brand=doc.get("brand", "YourCo"),
        draw_brand=doc.get("draw_brand", True),
        logo_path=doc.get("logo_path"),
    )
