from __future__ import annotations

from typing import Callable, Dict, List, Sequence

from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics

from .style import Style
from .primitives import (
    arrow,
    blue_rule,
    box,
    connector,
    draw_centered_text,
    draw_text,
    draw_wrapped,
    line_top,
    rect_top,
    section_side_heading,
    set_stroke,
    tag,
    y_from_top,
)


def _items(data: dict, key: str, fallback: Sequence[str]) -> Sequence[str]:
    return data.get(key) or list(fallback)


def _labels(data: dict, fallback: Sequence[dict]) -> Sequence[dict]:
    return data.get("items") or list(fallback)


def figure_flywheel(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    items = _labels(data, [
        {"title": "Usage", "body": "creates signal"},
        {"title": "Signal", "body": "gets structured"},
        {"title": "Knowhow", "body": "improves system"},
        {"title": "System", "body": "drives usage"},
    ])
    n = len(items)
    gap = 13.0
    bw = (w - gap * (n - 1)) / n
    bh = min(42, h * 0.36)
    by = y + 18
    for i, item in enumerate(items):
        bx = x + i * (bw + gap)
        box(c, style, bx, by, bw, bh, item.get("title", ""), item.get("body", ""), fill=style.palette.page, title_size=8.5, body_size=7.1, pad=7)
        if i < n - 1:
            arrow(c, style, bx + bw, by + bh / 2, bx + bw + gap - 3, by + bh / 2, width=0.75)
    # return loop
    start_x = x + w - bw / 2
    end_x = x + bw / 2
    yy = by + bh + 22
    connector(c, style, [(start_x, by + bh), (start_x, yy), (end_x, yy), (end_x, by + bh)], width=0.75, head=True)
    note = data.get("note", "Loops back - the institution that generates signal must also capture it")
    draw_centered_text(c, style, x, yy + 6, w, note, font=style.fonts.medium, size=7.8, color=style.palette.text)


def figure_context_flywheel(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    default = [
        {"title": "Usage", "body": "in the digital twin"},
        {"title": "Signal", "body": "captured in ontology"},
        {"title": "Ontology", "body": "structures knowhow"},
        {"title": "Workflows", "body": "drive better usage"},
    ]
    figure_flywheel(c, style, x, y, w, h, {**data, "items": data.get("items") or default, "note": data.get("note", "")})


def figure_architecture_layers(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    layer_h = (h - 18) / 3
    layers = data.get("layers") or [
        {"title": "Control (Layer 3)", "body": "The system where models generate and compound institutional value.", "boxes": [{"label": "OWNED SURFACE", "title": "Workflows, Ontology, Agents", "body": "Tribal knowledge captured and structured."}]},
        {"title": "Models (Layer 2)", "body": "Commodity intelligence - swap as needed.", "boxes": [{"label": "ACCESS MODE A", "title": "Rented", "body": "Closed API, contractual assurance."}, {"label": "ACCESS MODE B", "title": "Owned", "body": "Open-weight, self-hosted or tuned."}]},
        {"title": "Compute (Layer 1)", "body": "Infrastructure that runs models and software.", "boxes": [{"label": "TIER I", "title": "Own Hardware", "body": "Air-gapped or on-prem."}, {"label": "TIER II", "title": "Dedicated / Attested", "body": "Verified enclave."}, {"label": "TIER III", "title": "Standard Cloud", "body": "Contractual controls."}]},
    ]
    for i, layer in enumerate(layers[:3]):
        ly = y + i * (layer_h + 9)
        box(c, style, x, ly, w, layer_h, "", "", fill=pal.page, stroke=pal.text, pad=7)
        draw_text(c, style, x + 9, ly + 8, layer.get("title", ""), font=style.fonts.semibold, size=9.0, color=pal.text)
        # color parenthetical layer text by drawing a blue overlay if provided separately.
        body_y = ly + 22
        draw_wrapped(c, style, x + 9, body_y, w - 18, layer.get("body", ""), font=style.fonts.medium, size=6.7, leading=8.0)
        boxes = layer.get("boxes") or []
        gap = 10
        bx_w = (w - 26 - gap * (len(boxes) - 1)) / max(1, len(boxes))
        by = ly + 45
        bh = layer_h - 56
        for j, b in enumerate(boxes):
            box(c, style, x + 13 + j * (bx_w + gap), by, bx_w, bh, b.get("title", ""), b.get("body", ""), b.get("label", ""), fill=pal.blue_faint, stroke=pal.blue, title_size=7.6, body_size=5.8, label_size=5.1, pad=7)


def figure_tribal_ownership(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    top_h = 34
    box(c, style, x, y, w, top_h, data.get("root_title", "Enterprise Tribal Knowledge"), data.get("root_body", "Unique operational knowhow, IP, and workflows. Captured once."), fill=pal.page, stroke=pal.blue, center=True, title_size=8.0, body_size=6.4, pad=7)
    draw_centered_text(c, style, x, y + top_h + 24, w, data.get("question", "Who profits?"), font=style.fonts.semibold, size=8.0)
    mid = x + w / 2
    connector(c, style, [(mid, y + top_h + 33), (mid - w * 0.25, y + top_h + 53)], color=pal.blue, width=0.7, dash=[1.5, 1.6], head=True)
    connector(c, style, [(mid, y + top_h + 33), (mid + w * 0.25, y + top_h + 53)], color=pal.blue, width=0.7, head=True)
    col_gap = 25
    col_w = (w - col_gap) / 2
    left_x = x
    right_x = x + col_w + col_gap
    start_y = y + top_h + 60
    row_h = 48
    row_gap = 10
    left = data.get("provider_path") or [
        {"label": "PROVIDER PATH", "title": "External Model Weights", "body": "Knowhow flows into a closed provider surface."},
        {"title": "Leased to Competitors", "body": "Workflows become generic capability."},
        {"title": "Rent-Seeking on Workflows", "body": "Per-token pricing on high-margin operations."},
        {"title": "Provider Replaces You", "body": "The vendor owns the customer relationship."},
    ]
    right = data.get("enterprise_path") or [
        {"label": "ENTERPRISE PATH", "title": "Enterprise-Controlled System", "body": "Owned weights, ontology, and control layer."},
        {"title": "Compounding Alpha", "body": "Usage cycles sharpen the moat you retain."},
        {"title": "Leverage Over Providers", "body": "Switch vendors without losing the knowhow."},
        {"title": "Own the Flywheel", "body": "Signal and knowhow stay inside the institution."},
    ]
    for i, b in enumerate(left[:4]):
        box(c, style, left_x, start_y + i * (row_h + row_gap), col_w, row_h, b.get("title", ""), b.get("body", ""), b.get("label", ""), fill=pal.page, stroke=pal.gray, dashed=True, center=True, title_size=7.6, body_size=6.0, label_size=5.0)
    for i, b in enumerate(right[:4]):
        box(c, style, right_x, start_y + i * (row_h + row_gap), col_w, row_h, b.get("title", ""), b.get("body", ""), b.get("label", ""), fill=pal.blue_light, stroke=pal.blue, center=True, title_size=7.6, body_size=6.0, label_size=5.0)
        if i < 3:
            arrow(c, style, right_x + col_w / 2, start_y + i * (row_h + row_gap) + row_h, right_x + col_w / 2, start_y + (i + 1) * (row_h + row_gap) - 3)


def figure_agent_harness(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    left_w = 75
    out_w = 76
    loop_x = x + left_w + 15
    loop_w = w - left_w - out_w - 35
    loop_h = min(105, h - 8)
    box(c, style, x, y + 25, left_w, 62, data.get("source_title", "Production workload"), data.get("source_body", "Live traffic, evals, latency and cost budgets."), fill=pal.page, title_size=7.1, body_size=5.7, pad=6)
    draw_text(c, style, loop_x, y + 10, data.get("loop_label", "Continuous evaluation loop"), font=style.fonts.medium, size=6.6)
    box(c, style, loop_x, y + 23, loop_w, loop_h, "", "", fill=pal.page, stroke=pal.gray, dashed=True)
    step_gap = 12
    step_w = (loop_w - 28 - step_gap * 2) / 3
    steps = data.get("steps") or [
        {"label": "01", "title": "Swap models", "body": "Rotate providers by eval score, price, latency."},
        {"label": "02", "title": "Tune prompts", "body": "Rewrite, test, and feed winners back."},
        {"label": "03", "title": "Validate outputs", "body": "Automatic checks before promotion."},
    ]
    sx = loop_x + 14
    sy = y + 37
    for i, step in enumerate(steps[:3]):
        bx = sx + i * (step_w + step_gap)
        box(c, style, bx, sy, step_w, 63, step.get("title", ""), step.get("body", ""), step.get("label", ""), fill=pal.page, stroke=pal.text, title_size=6.8, body_size=5.4, label_size=5.0, pad=5)
        if i < 2:
            arrow(c, style, bx + step_w, sy + 31, bx + step_w + step_gap - 3, sy + 31)
    connector(c, style, [(sx + step_w * 2.5 + step_gap * 2, sy + 63), (sx + step_w * 2.5 + step_gap * 2, sy + 82), (sx + step_w * 0.5, sy + 82), (sx + step_w * 0.5, sy + 63)], width=0.75, head=True)
    arrow(c, style, x + left_w, y + 56, loop_x - 4, y + 56)
    out_x = x + w - out_w
    outcomes = data.get("outcomes") or [
        {"title": "Lower compute cost", "body": "Cheaper models slot in where quality holds."},
        {"title": "Higher accuracy", "body": "Prompts and models improve against evals."},
    ]
    for i, o in enumerate(outcomes[:2]):
        box(c, style, out_x, y + 24 + i * 56, out_w, 46, o.get("title", ""), o.get("body", ""), "OUTCOME", fill=pal.blue_light, stroke=pal.blue, title_size=6.4, body_size=5.2, label_size=4.8, pad=5)


def figure_assurance_levels(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    draw_centered_text(c, style, x, y + 0, w, data.get("axis_title", "Assurance shifts"), font=style.fonts.medium, size=6.8)
    draw_centered_text(c, style, x, y + 18, w / 2, "Structural", font=style.fonts.medium, size=6.2)
    draw_centered_text(c, style, x + w / 2, y + 18, w / 2, "Contractual", font=style.fonts.medium, size=6.2)
    set_stroke(c, pal.blue, 0.6, [1.2, 2])
    line_top(c, style, x, y + 31, x + w / 2 - 4, y + 31)
    line_top(c, style, x + w / 2 + 4, y + 31, x + w, y + 31)
    draw_text(c, style, x, y + 45, "Strongest", font=style.fonts.semibold, size=6.5)
    draw_text(c, style, x + w - 44, y + 45, "Weakest", font=style.fonts.semibold, size=6.5)
    cards = data.get("cards") or [
        {"num": "1", "label": "TIER 1 - STRUCTURAL", "title": "Owned Hardware", "body": "Air-gapped infrastructure on GPUs the institution owns. No egress; physical boundary is the assurance.", "workload": "Classified / core secrets"},
        {"num": "2", "label": "TIER 2 - STRUCTURAL", "title": "Attested Compute", "body": "Rented GPUs with hardware attestation and confidential computing. Silicon proves enclave execution.", "workload": "Sensitive workflows"},
        {"num": "3", "label": "TIER 3 - CONTRACTUAL", "title": "ZDR Cloud", "body": "Closed frontier model under zero data retention. Assurance rests on contract, not isolation.", "workload": "Sensitive day-to-day"},
        {"num": "4", "label": "TIER 4 - CONTRACTUAL", "title": "Standard Third-Party", "body": "Default API access. Treat prompts and outputs as observed.", "workload": "Public / discrete"},
    ]
    gap = 12
    cw = (w - gap * 3) / 4
    cy = y + 60
    ch = h - 66
    for i, card in enumerate(cards[:4]):
        bx = x + i * (cw + gap)
        fill = pal.blue_faint if i < 3 else pal.page
        box(c, style, bx, cy, cw, ch, "", "", fill=fill, stroke=pal.text, accent="top" if i < 3 else None)
        # number circle
        c.saveState()
        c.setFillColor(pal.blue_light if i < 3 else pal.page)
        set_stroke(c, pal.blue if i < 3 else pal.gray, 0.8)
        c.circle(bx + 15, y_from_top(style, cy + 20), 7, stroke=1, fill=1)
        draw_centered_text(c, style, bx + 8, cy + 15.2, 14, str(card.get("num", i + 1)), font=style.fonts.semibold, size=6.8, color=pal.blue if i < 3 else pal.gray)
        c.restoreState()
        draw_wrapped(c, style, bx + 10, cy + 39, cw - 20, card.get("label", ""), font=style.fonts.semibold, size=5.4, leading=6.5, color=pal.blue if i < 3 else pal.gray)
        draw_wrapped(c, style, bx + 10, cy + 55, cw - 20, card.get("title", ""), font=style.fonts.semibold, size=8.0, leading=9.0)
        draw_wrapped(c, style, bx + 10, cy + 76, cw - 20, card.get("body", ""), font=style.fonts.medium, size=6.2, leading=7.1)
        draw_wrapped(c, style, bx + 10, cy + ch - 36, cw - 20, "Workload Class", font=style.fonts.semibold, size=5.2, leading=6)
        tag(c, style, bx + 10, cy + ch - 22, card.get("workload", ""), size=4.4, fill=pal.page if i == 3 else pal.blue_faint, stroke=pal.blue if i < 3 else pal.gray)


def figure_on_prem(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    draw_text(c, style, x, y, data.get("label", "Institutional perimeter"), font=style.fonts.semibold, size=7.5)
    box(c, style, x, y + 12, w, h - 12, "", "", fill=pal.page, stroke=pal.text, dashed=True)
    layers = data.get("layers") or [
        {"label": "LAYER 5 - TOP", "title": "Users & Agents", "body": "Analysts and internal agents operate on institutional data."},
        {"label": "LAYER 4", "title": "Application Layer (Ontology)", "body": "Structured knowledge layer: entities, relations, provenance."},
        {"label": "LAYER 3", "title": "Control Layer", "body": "Permissions, audit logs, routing, rollback."},
        {"label": "LAYER 2", "title": "Open-Weight Models", "body": "Weights run locally. Inference and fine-tune inside perimeter."},
        {"label": "LAYER 1 - BOTTOM", "title": "Owned GPUs / Adaptable Hardware", "body": "Hardware across the AI stack."},
    ]
    inner_x = x + 12
    inner_w = w - 24
    row_gap = 9
    row_h = (h - 40 - row_gap * 4) / 5
    start_y = y + 25
    for i, layer in enumerate(layers[:5]):
        ly = start_y + i * (row_h + row_gap)
        box(c, style, inner_x, ly, inner_w, row_h, layer.get("title", ""), layer.get("body", ""), layer.get("label", ""), fill=pal.page, stroke=pal.text, title_size=7.7, body_size=5.9, label_size=5.1, pad=7)
        draw_text(c, style, inner_x + inner_w - 40, ly + 8, data.get("status", "Blocked"), font=style.fonts.medium, size=5.8)
        if i < 4:
            arrow(c, style, inner_x + inner_w / 2, ly + row_h + 6, inner_x + inner_w / 2, ly + row_h + row_gap - 2)
    # GPU tiles on bottom layer
    tile_y = start_y + 4 * (row_h + row_gap) + row_h - 22
    tile_w = 49
    for i in range(6):
        tx = inner_x + 8 + i * ((inner_w - 16 - tile_w) / 5)
        fill = pal.blue_faint if i < 4 else pal.page
        box(c, style, tx, tile_y, tile_w, 14, "GPU", "", fill=fill, stroke=pal.blue if i < 4 else pal.text, center=True, title_size=5.8, pad=3)


def figure_attestation(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    draw_centered_text(c, style, x, y, w * 0.25, "Enterprise", font=style.fonts.medium, size=6.4, color=pal.gray)
    draw_centered_text(c, style, x + w * 0.25, y, w * 0.5, "TEE Inside Third-Party Host", font=style.fonts.semibold, size=6.4, color=pal.blue)
    draw_centered_text(c, style, x + w * 0.75, y, w * 0.25, "Enterprise", font=style.fonts.medium, size=6.4, color=pal.gray)
    steps = data.get("steps") or [
        {"label": "1", "title": "Encrypt & Send", "body": "Enterprise seals workload to target enclave key and dispatches it."},
        {"label": "2", "title": "Execute in TEE", "body": "Silicon-isolated memory. Host operators cannot inspect."},
        {"label": "3", "title": "Sign Attestation", "body": "Hardware root of trust signs a quote for this run."},
        {"label": "4", "title": "Verify Proof", "body": "Enterprise checks the signature chain."},
    ]
    gap = 12
    bw = (w - gap * 3) / 4
    by = y + 25
    bh = min(h - 35, 96)
    for i, step in enumerate(steps[:4]):
        fill = pal.blue_light if i in (1, 2) else pal.page
        box(c, style, x + i * (bw + gap), by, bw, bh, step.get("title", ""), step.get("body", ""), step.get("label", ""), fill=fill, stroke=pal.blue if i in (1, 2) else pal.text, title_size=7.7, body_size=6.0, label_size=7.0, pad=8)
        if i < 3:
            arrow(c, style, x + i * (bw + gap) + bw, by + bh / 2, x + i * (bw + gap) + bw + gap - 3, by + bh / 2)
    # proof line
    yy = by + bh + 26
    set_stroke(c, pal.blue, 0.6, [1.2, 1.8])
    line_top(c, style, x + bw * 1.25, yy, x + bw * 3.4, yy)
    tag(c, style, x + bw * 2.25, yy - 6, data.get("proof", "Signed Attestation"), size=5.2, fill=pal.page, stroke=pal.blue)


def figure_control_layer(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    box(c, style, x, y, w, 48, data.get("control_title", "Control layer"), data.get("control_body", "Governs every workload across the stack"), fill=pal.page, stroke=pal.text, title_size=8.2, body_size=6.8, pad=8)
    controls = data.get("controls") or ["Model-agnostic routing", "Granular permissions", "Auditability & logs", "Branching"]
    cx = x + 22
    for item in controls[:4]:
        draw_text(c, style, cx, y + 32, item, font=style.fonts.medium, size=6.8)
        cx += pdfmetrics.stringWidth(item, style.fonts.medium, 6.8) + 18
    # model layer
    my = y + 72
    mh = 108
    box(c, style, x, my, w, mh, data.get("model_title", "Modular intelligence layer"), data.get("model_body", "Treated as a commodity, not a foundation"), fill=pal.blue_faint, stroke=pal.blue, title_size=8.2, body_size=6.8, pad=10)
    models = data.get("models") or [
        {"title": "Model A", "body": "External, under ZDR"}, {"title": "Model B", "body": "External, under ZDR"},
        {"title": "Model C", "body": "External, under ZDR"}, {"title": "Self-hosted", "body": "Open-weight, owned", "dashed": True},
    ]
    gap = 12
    bx_w = (w - 32 - gap * 3) / 4
    for i, m in enumerate(models[:4]):
        box(c, style, x + 16 + i * (bx_w + gap), my + 45, bx_w, 36, m.get("title", ""), m.get("body", ""), fill=pal.page, stroke=pal.blue, dashed=m.get("dashed", False), title_size=7.2, body_size=5.8, pad=6)
    box(c, style, x + 16, my + mh - 30, w - 32, 20, data.get("liquidity", "Model liquidity - switch with minimal friction"), "", fill=pal.page, stroke=pal.blue, center=True, title_size=7.0, pad=5)
    draw_centered_text(c, style, x, my + mh + 24, w / 2, "Context, prompts, permissions", font=style.fonts.medium, size=7)
    draw_centered_text(c, style, x + w / 2, my + mh + 24, w / 2, "Outputs, knowhow, weights", font=style.fonts.medium, size=7)
    # ontology layer
    oy = my + mh + 55
    oh = h - (oy - y)
    box(c, style, x, oy, w, oh, data.get("ontology_title", "Owned knowledge layer - ontology"), data.get("ontology_body", "A digital twin of your organization"), fill=pal.blue_faint, stroke=pal.blue, title_size=8.2, body_size=6.8, pad=10)
    objs = data.get("ontology_items") or [
        {"title": "Objects", "body": "Nouns - entities, events"}, {"title": "Properties", "body": "Attributes of each object"},
        {"title": "Links", "body": "Relations between objects"}, {"title": "Actions", "body": "Verbs - structured change"},
    ]
    item_w = (w - 38 - gap * 3) / 4
    for i, o in enumerate(objs[:4]):
        box(c, style, x + 19 + i * (item_w + gap), oy + 52, item_w, 43, o.get("title", ""), o.get("body", ""), fill=pal.page, stroke=pal.blue, title_size=7.2, body_size=5.8, pad=6)
    half_w = (w - 38 - gap) / 2
    box(c, style, x + 19, oy + 108, half_w, 36, "Transactional data", "Records you already generate", fill=pal.page, stroke=pal.blue, title_size=7.2, body_size=5.8, pad=6)
    box(c, style, x + 19 + half_w + gap, oy + 108, half_w, 36, "Action data", "Captured only if structured", fill=pal.page, stroke=pal.blue, title_size=7.2, body_size=5.8, pad=6)
    box(c, style, x + 19, oy + oh - 32, w - 38, 20, data.get("eval", "Eval loop - captures usage and compounds it back into the ontology"), "", fill=pal.page, stroke=pal.blue, center=True, title_size=6.8, pad=5)


def figure_permissions(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    grid_w = min(160, w * 0.32)
    grid_x = x + (w - grid_w) / 2
    grid_y = y + 45
    cell = grid_w / 5
    headers = data.get("headers") or ["Name", "Region", "Salary", "PII", "Notes"]
    draw_centered_text(c, style, grid_x, y + 28, grid_w, data.get("dataset", "DATASET - EMPLOYEES"), font=style.fonts.semibold, size=6.6)
    # header
    for i, head in enumerate(headers):
        box(c, style, grid_x + i * cell, grid_y, cell, 18, head, "", fill=pal.page, stroke=pal.text, center=True, title_size=4.8, pad=4)
    # data cells
    mask = data.get("mask") or [
        [0, 1, 0, 2, 1], [1, 0, 3, 2, 1], [0, 1, 0, 2, 0], [0, 0, 1, 2, 0], [0, 0, 0, 1, 0]
    ]
    for r in range(5):
        for col in range(5):
            val = mask[r][col]
            fill = pal.blue_light if val in (0, 1) else pal.text
            if val == 3:
                fill = pal.gray_light
            c.saveState()
            c.setFillColor(fill)
            set_stroke(c, pal.text, 0.65)
            rect_top(c, style, grid_x + col * cell, grid_y + 18 + r * cell, cell, cell, stroke=1, fill=1)
            if val == 1:
                # hatch clipped to the cell
                set_stroke(c, pal.gray, 0.35)
                step = 5
                xx0 = grid_x + col * cell
                yy0 = grid_y + 18 + r * cell
                clip = c.beginPath()
                clip.rect(xx0, y_from_top(style, yy0 + cell), cell, cell)
                c.clipPath(clip, stroke=0, fill=0)
                for k in range(-int(cell), int(cell * 2), step):
                    line_top(c, style, xx0 + k, yy0 + cell, xx0 + k + cell, yy0)
            c.restoreState()
    actors = data.get("actors") or [
        {"xside": "left", "yoff": 10, "label": "HUMAN - ANALYST", "title": "Analyst", "body": "Read: Name, Region, Notes. PII hidden."},
        {"xside": "left", "yoff": 150, "label": "AGENT", "title": "Reporting Agent", "body": "Aggregates non-PII columns only."},
        {"xside": "right", "yoff": 10, "label": "HUMAN - EXECUTIVE", "title": "Executive", "body": "Salary + Region for own division."},
        {"xside": "right", "yoff": 150, "label": "AGENT", "title": "Compliance Agent", "body": "Scoped to PII + flagged rows."},
    ]
    bw, bh = 93, 58
    for a in actors:
        bx = x if a["xside"] == "left" else x + w - bw
        by = y + a["yoff"]
        box(c, style, bx, by, bw, bh, a.get("title", ""), a.get("body", ""), a.get("label", ""), fill=pal.page, stroke=pal.text, accent="left", title_size=7.7, body_size=5.8, label_size=5.1, pad=7)
        start = (bx + bw, by + bh / 2) if a["xside"] == "left" else (bx, by + bh / 2)
        end = (grid_x, by + bh / 2) if a["xside"] == "left" else (grid_x + grid_w, by + bh / 2)
        arrow(c, style, start[0], start[1], end[0], end[1])
    set_stroke(c, pal.blue, 0.6)
    line_top(c, style, x, y + h - 10, x + w, y + h - 10)


def figure_audit_logs(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    steps = data.get("steps") or [
        {"label": "01", "title": "User / Agent", "body": "Identity, role, and session."},
        {"label": "02", "title": "Prompt / Query", "body": "Exact text, tool calls, parameters."},
        {"label": "03", "title": "Model Called", "body": "Provider, model, route."},
        {"label": "04", "title": "Data Accessed", "body": "Ontology objects and rows read."},
        {"label": "05", "title": "Action / Result", "body": "Response or side effect."},
    ]
    gap = 12
    bw = (w - gap * 4) / 5
    step_y = y + 10
    log_y = y + 105
    for i, s in enumerate(steps[:5]):
        bx = x + i * (bw + gap)
        box(c, style, bx, step_y, bw, 75, s.get("title", ""), s.get("body", ""), s.get("label", ""), fill=pal.page, stroke=pal.text, accent="left", title_size=7.0, body_size=5.4, label_size=5.0, pad=6)
        arrow(c, style, bx + bw / 2, step_y + 75, bx + bw / 2, log_y - 5)
        box(c, style, bx, log_y, bw, 49, data.get("log_title", "10:24:07Z"), data.get("log_body", "trace item"), "", fill=pal.page, stroke=pal.gray, dashed=True, title_size=5.7, body_size=5.3, pad=6)
        if i < 4:
            arrow(c, style, bx + bw, step_y + 37, bx + bw + gap - 3, step_y + 37)
    stream_y = y + 172
    box(c, style, x, stream_y, w, 20, "", "", fill=pal.page, stroke=pal.text, pad=4)
    draw_text(c, style, x + 8, stream_y + 6, data.get("stream", "Append-only log stream"), font=style.fonts.semibold, size=6.4)
    draw_text(c, style, x + w - 190, stream_y + 6, "trace_id = t.9c1e - signed - immutable", font=style.fonts.medium, size=5.2)
    arrow(c, style, x + w / 2, stream_y + 20, x + w / 2, stream_y + 34)
    audit_y = stream_y + 42
    box(c, style, x, audit_y, w, h - (audit_y - y), "Audit", "Reads the trace - Enforces sovereignty", fill=pal.blue_faint, stroke=pal.blue, title_size=7.5, body_size=5.7, pad=8)
    cards = data.get("audit_cards") or [
        {"title": "Replay", "body": "Reconstruct decisions from actor, prompt, model, and data."},
        {"title": "Query", "body": "Filter by user, model, object, or time."},
        {"title": "Detect misappropriation", "body": "Compare external outputs against canaries."},
    ]
    card_gap = 10
    card_w = (w - 36 - card_gap * 2) / 3
    for i, card in enumerate(cards[:3]):
        box(c, style, x + 18 + i * (card_w + card_gap), audit_y + 45, card_w, 40, card.get("title", ""), card.get("body", ""), fill=pal.blue_light, stroke=pal.blue, title_size=6.5, body_size=5.2, pad=6)


def figure_security_forge(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    """Apollo-style circular security forge diagram."""
    pal = style.palette
    bx0, by0, bw0, bh0 = 70.8, 456.7, 482.1, 194.2
    sx, sy = w / bw0, h / bh0
    ss = min(sx, sy)
    def X(v): return x + (v - bx0) * sx
    def Y(v): return y + (v - by0) * sy
    def line(x1,y1,x2,y2,color=None,width=0.61):
        set_stroke(c, color or pal.text, width*ss)
        line_top(c, style, X(x1), Y(y1), X(x2), Y(y2))
    def txt(tx,ty,text,size=8.4,font=None,align='left',color=None,leading=None,width=None):
        font = font or style.fonts.medium
        color = color or pal.text
        if width:
            if align == 'right':
                # crude right alignment per line
                for i,ln in enumerate(str(text).split('\n')):
                    tw=pdfmetrics.stringWidth(ln,font,size*ss)
                    draw_text(c, style, X(tx)-tw, Y(ty)+i*(leading or size*1.18)*ss, ln, font=font, size=size*ss, color=color)
            elif align == 'center':
                for i,ln in enumerate(str(text).split('\n')):
                    draw_centered_text(c, style, X(tx-width/2), Y(ty)+i*(leading or size*1.18)*ss, W(width), ln, font=font, size=size*ss, color=color)
            else:
                draw_wrapped(c, style, X(tx), Y(ty), W(width), text, font=font, size=size*ss, leading=(leading or size*1.18)*ss, color=color)
        else:
            draw_text(c, style, X(tx), Y(ty), text, font=font, size=size*ss, color=color)
    def W(v): return v*sx
    # horizontal rules
    line(70.8,472.97,263.98,472.97)
    line(359.68,472.97,552.87,472.97)
    line(70.8,563.84,234.86,563.84)
    line(388.80,563.84,552.87,563.84)
    # segmented circle
    xc, yc, r = 311.8, 538.75, 81.2
    c.saveState()
    set_stroke(c, pal.blue, 1.87*ss)
    # ReportLab arcs use bottom-left coordinates; convert the top-coord box.
    x1, x2 = X(xc-r), X(xc+r)
    y_bottom = y_from_top(style, Y(yc+r))
    y_top = y_from_top(style, Y(yc-r))
    for start_ang, extent in [(96,66),(18,55),(-55,78),(-152,54),(168,54)]:
        c.arc(x1, y_bottom, x2, y_top, start_ang, extent)
    c.restoreState()
    draw_centered_text(c, style, X(xc-60), Y(531.0), W(120), data.get('center','Apollo'), font=style.fonts.medium, size=20*ss)
    # text groups
    txt(70.8,481.5,'Discovery',size=9.3,font=style.fonts.semibold)
    txt(70.8,498.0,'Agentic security harness\nSBOM\nDrift detection\nExploit-path reasoning',size=7.1,leading=9.5,width=150)
    txt(70.8,572.5,'Observation',size=9.3,font=style.fonts.semibold)
    txt(70.8,589.0,'Telemetry\nHealth probes\nAudit emission\nCompliance reporting',size=7.1,leading=9.5,width=150)
    txt(552.9,481.5,'Adjudication',size=9.3,font=style.fonts.semibold,align='right',width=160)
    txt(552.9,498.0,'Channels\nConstraints\nSoak time\nBlue / green criteria\nCompliance gates',size=7.1,leading=9.5,align='right',width=160)
    txt(552.9,572.5,'Remediation',size=9.3,font=style.fonts.semibold,align='right',width=160)
    txt(552.9,589.0,'Patch agents\nChange drafting\nDependency rewrites\nForward-fix synthesis',size=7.1,leading=9.5,align='right',width=160)
    draw_centered_text(c, style, X(xc-70), Y(635.0), W(140), 'Discovery', font=style.fonts.semibold, size=9.3*ss)
    draw_centered_text(c, style, X(xc-70), Y(652.0), W(140), 'Plans', font=style.fonts.medium, size=7.1*ss)
    for i,ln in enumerate(['Blue/green','Dependency-aware ordering','Recall','Rollback']):
        draw_centered_text(c, style, X(xc-80), Y(668.0+i*9.5), W(160), ln, font=style.fonts.medium, size=7.1*ss)

def figure_branching(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    sandbox_h = h * 0.72
    box(c, style, x, y, w * 0.86, sandbox_h, "Agent sandbox", "Scoped branch - isolated from production", fill=pal.page, stroke=pal.blue, dashed=True, title_size=6.8, body_size=5.5, pad=8)
    tag(c, style, x + w * 0.78, y + 9, data.get("branch", "Branch - #AF73"), size=5.4, fill=pal.page)
    # agent bubble
    c.saveState()
    c.setFillColor(pal.blue_light)
    set_stroke(c, pal.blue, 1)
    c.circle(x + 30, y_from_top(style, y + sandbox_h * 0.47), 14, stroke=1, fill=1)
    c.restoreState()
    draw_centered_text(c, style, x + 12, y + sandbox_h * 0.47 + 16, 36, "Agent", font=style.fonts.medium, size=5.5)
    draw_centered_text(c, style, x + 4, y + sandbox_h * 0.47 + 25, 52, "operates", font=style.fonts.medium, size=5.5)
    # grid path
    gx = x + 118
    gy = y + 58
    gw = w * 0.55
    gh = sandbox_h - 105
    set_stroke(c, pal.blue, 0.8, [1.2, 1.8])
    for i in range(6):
        xx = gx + i * gw / 5
        line_top(c, style, xx, gy, xx, gy + gh)
    for j in range(3):
        yy = gy + j * gh / 2
        line_top(c, style, gx, yy, gx + gw, yy)
    # rounded outline approximation
    c.setDash()
    connector(c, style, [(gx, gy + gh * 0.25), (gx + 10, gy), (gx + gw - 12, gy), (gx + gw, gy + gh * 0.25), (gx + gw, gy + gh * 0.75), (gx + gw - 12, gy + gh), (gx + 10, gy + gh), (gx, gy + gh * 0.75), (gx, gy + gh * 0.25)], head=False)
    for i in range(6):
        for j in range(3):
            c.saveState()
            c.setFillColor(pal.blue)
            c.circle(gx + i * gw / 5, y_from_top(style, gy + j * gh / 2), 2, stroke=0, fill=1)
            c.restoreState()
    label_x = gx - 48
    draw_text(c, style, label_x, gy + 15, "Objects", font=style.fonts.semibold, size=5.8)
    draw_wrapped(c, style, label_x, gy + 24, 44, "New twin entities created", font=style.fonts.medium, size=5.0, leading=5.8)
    draw_text(c, style, label_x, gy + gh * 0.5 + 8, "Links", font=style.fonts.semibold, size=5.8)
    draw_wrapped(c, style, label_x, gy + gh * 0.5 + 17, 44, "Ontology relations drawn", font=style.fonts.medium, size=5.0, leading=5.8)
    draw_text(c, style, label_x, gy + gh - 35, "Actions", font=style.fonts.semibold, size=5.8)
    draw_wrapped(c, style, label_x, gy + gh - 26, 44, "Workflow steps executed", font=style.fonts.medium, size=5.0, leading=5.8)
    # Validate and outcomes
    draw_text(c, style, gx + gw - 14, gy + gh * 0.55, "Validate", font=style.fonts.medium, size=5.5, color=pal.blue)
    connector(c, style, [(gx + gw, gy + gh * 0.55), (x + w * 0.93, gy + gh * 0.55), (x + w * 0.93, y + 65)], color=pal.gray, width=0.7, dash=[1.5,1.7], head=True)
    tag(c, style, x + w * 0.9, y + 76, "Discarded", size=5.0, fill=pal.page, stroke=pal.gray, color=pal.gray)
    connector(c, style, [(gx + gw, gy + gh * 0.55), (x + w * 0.93, gy + gh * 0.55), (x + w * 0.93, y + sandbox_h + 53)], color=pal.blue, width=0.7, head=True)
    tag(c, style, x + w * 0.9, y + sandbox_h + 20, "Promoted", size=5.0, fill=pal.page, stroke=pal.blue)
    draw_wrapped(c, style, x + w * 0.88, y + sandbox_h + 40, 55, "Either outcome is safe", font=style.fonts.medium, size=5.4, leading=6.2)
    # timeline
    ty = y + h - 35
    set_stroke(c, pal.text, 0.8)
    line_top(c, style, x + 4, ty, x + w - 16, ty)
    arrow(c, style, x + w - 16, ty, x + w - 4, ty, color=pal.text, width=0.8)
    points = [x + 20, x + 52, x + 105, x + 195, x + 280, x + 400, x + w - 60]
    for px in points:
        c.setFillColor(pal.text)
        c.circle(px, y_from_top(style, ty), 2, stroke=0, fill=1)
    line_top(c, style, x + 52, ty, x + 52, ty - 25)
    draw_text(c, style, x + 18, ty + 11, "Production", font=style.fonts.medium, size=5.5)
    draw_text(c, style, x + 18, ty + 20, "Main - untouched", font=style.fonts.medium, size=5.5)
    draw_text(c, style, x + 42, ty - 36, "Fork", font=style.fonts.medium, size=5.5)
    draw_text(c, style, x + w - 70, ty + 11, "Continues", font=style.fonts.medium, size=5.5)


def figure_decision_tree(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    """Reference-like version of Fig. 2.

    This intentionally uses the same visual grammar and approximate geometry as
    the source page: narrow decision rows, three side outcomes, split assurance
    choices, four workload classes, and eight vertical end-state cards.
    """
    pal = style.palette
    # Helper to map coordinates from the source page's figure area into the given box.
    bx0, by0, bw0, bh0 = 69.8, 90.5, 483.2, 604.0
    sx, sy = w / bw0, h / bh0
    def X(v: float) -> float: return x + (v - bx0) * sx
    def Y(v: float) -> float: return y + (v - by0) * sy
    def W(v: float) -> float: return v * sx
    def H(v: float) -> float: return v * sy
    def mini_tag(tx: float, ty: float, txt: str) -> float:
        return tag(c, style, X(tx), Y(ty), txt, size=4.35 * min(sx, sy), fill=pal.page, stroke=pal.blue)
    def rbox(rx, ry, rw, rh, title, body="", label="", fill=None, stroke=None, dashed=False, title_size=7.4, body_size=5.7, label_size=4.8, center=False):
        box(c, style, X(rx), Y(ry), W(rw), H(rh), title, body, label, fill=fill or pal.page, stroke=stroke or pal.text, dashed=dashed, title_size=title_size*min(sx, sy), body_size=body_size*min(sx, sy), label_size=label_size*min(sx, sy), pad=6.3*min(sx, sy), center=center)
    def arr(x1,y1,x2,y2, dash=None, color=None):
        arrow(c, style, X(x1), Y(y1), X(x2), Y(y2), color=color or pal.blue, width=0.61*min(sx, sy), dash=dash)
    def conn(points, dash=None, color=None, head=True):
        connector(c, style, [(X(px), Y(py)) for px,py in points], color=color or pal.blue, width=0.61*min(sx, sy), dash=dash, head=head)

    # Legend.
    box(c, style, X(71.3), Y(93.2), W(10.2), H(7.7), "", "", fill=pal.blue_light, stroke=pal.blue, pad=1)
    draw_text(c, style, X(85.1), Y(91.5), "Decision", font=style.fonts.medium, size=6.3*min(sx, sy))
    box(c, style, X(129.7), Y(93.2), W(10.2), H(7.7), "", "", fill=pal.page, stroke=pal.text, pad=1)
    draw_text(c, style, X(143.6), Y(91.5), "End State", font=style.fonts.medium, size=6.3*min(sx, sy))
    box(c, style, X(193.1), Y(93.2), W(10.2), H(7.7), "", "", fill=pal.page, stroke=pal.gray, dashed=True, pad=1)
    draw_text(c, style, X(206.0), Y(91.5), "Hold / No-Go", font=style.fonts.medium, size=6.3*min(sx, sy))
    box(c, style, X(269.2), Y(93.2), W(11.1), H(7.7), "", "", fill=pal.page, stroke=pal.blue, pad=1)
    draw_text(c, style, X(278.5), Y(90.6), "Source Step", font=style.fonts.medium, size=6.3*min(sx, sy))

    # Top routing rows.
    rbox(71.3, 117.6, 295.7, 40.4, "How should we implement this AI workflow?", "Route the whole stack before choosing any model or compute.", title_size=7.7, body_size=5.6)
    mini_tag(79.6, 140.2, "S2")
    rbox(71.3, 173.9, 295.7, 49.7, "ZDR + zero-trust review complete?", "ZDR negotiated per provider; model, compute, and control layers reviewed.\nAny non-ZDR frontier model is treated as extraction-prone (EPM).", title_size=7.2, body_size=5.25)
    tx=79.6
    for lab in ["S1","S3","S4"]:
        mini_tag(tx, 182.8, lab); tx += 12.4
    rbox(381.1, 173.9, 171.7, 49.7, "End: Do not implement yet", "Close ZDR gaps and EPM exposure.", "NO", dashed=True, title_size=7.2, body_size=5.4)
    rbox(71.3, 239.3, 295.7, 49.7, "Does this workflow need model inference?", "If deterministic software solves it, own the tool in your control layer instead\n- no model, no extraction surface.", title_size=7.2, body_size=5.25)
    rbox(381.1, 239.3, 171.7, 49.7, "End: Own a deterministic tool", "Build it in the layer you control.", "NO / TOOL-ONLY", fill=pal.blue_light, stroke=pal.blue, title_size=7.2, body_size=5.4)
    rbox(71.3, 304.3, 295.7, 63.0, "Does your control layer meet sovereignty criteria?", "Model agnostic     Granular permissions     Audit + log\nAdaptive cyber     Reversible branching\nOwned context flywheel / ontology", title_size=7.2, body_size=5.1)
    # draw representative source tags in the control box
    for tx,ty,lab in [(79.6,327.0,"S10"),(153.4,327.0,"S11"),(248.2,327.0,"S12"),(79.6,338.7,"S13"),(153.4,338.7,"S14"),(79.6,350.4,"S15")]:
        mini_tag(tx,ty,lab)
    rbox(381.1, 304.3, 171.7, 63.0, "Hold: Human-in-loop only", "Read-only AI until the control\nlayer passes.", "NOT READY", dashed=True, title_size=7.2, body_size=5.4)
    rbox(71.3, 383.1, 481.6, 39.9, "Classify knowledge -> Pick assurance level", "Structural assurance beats contractual. Match each workload to the strongest rung it needs.", title_size=7.2, body_size=5.35)
    for tx,lab in [(79.6,"S8"),(93.0,"S9")]: mini_tag(tx,392.0,lab)

    # Flow arrows between rows.
    cx=219.2
    for y1,y2 in [(158.0,173.9),(223.6,239.3),(289.1,304.3),(367.3,383.1)]: arr(cx,y1,cx,y2-5)
    for yy in [198.8,264.2,335.8]: arr(367.0, yy, 381.1-4, yy)

    # Assurance split.
    rbox(71.3, 444.8, 233.2, 48.3, "Structural assurance needed?", "Physical / technical isolation\n- own or dedicate the compute.", title_size=7.0, body_size=5.35)
    mini_tag(79.6,453.7,"S7")
    rbox(319.4, 444.8, 233.2, 48.3, "Contractual or public tier?", "External service only with limits and\nexit leverage (model liquidity).", title_size=7.0, body_size=5.35)
    for tx,lab in [(327.7,"S5"),(341.1,"S9")]: mini_tag(tx,453.7,lab)
    conn([(312,423.0),(312,433.5),(187.9,433.5),(187.9,444.8)], head=True)
    conn([(312,423.0),(312,433.5),(436.0,433.5),(436.0,444.8)], head=True)

    # Workload classes.
    classes = [
        (71.3,514.6,"Classified / sensitive","Low or zero-tolerance data.",[]),
        (195.3,514.6,"High-alpha knowhow","Signal must compound\nin-house.",[(203.9,523.6,"S6")]),
        (319.3,514.6,"Internal / regulated","No classified data;\ncontract must hold.",[]),
        (443.2,514.6,"Public / low-alpha","Retention risk\nis accepted.",[]),
    ]
    for rx,ry,t,b,tags in classes:
        rbox(rx,ry,109.8,57.9,t,b,title_size=6.8,body_size=5.15)
        for tx,ty,lab in tags: mini_tag(tx,ty,lab)
    # Split connectors from assurance to classes.
    conn([(187.9,493.1),(187.9,503.0),(126.2,503.0),(126.2,514.6)], head=True)
    conn([(187.9,493.1),(187.9,503.0),(250.2,503.0),(250.2,514.6)], head=True)
    conn([(436.0,493.1),(436.0,503.0),(374.2,503.0),(374.2,514.6)], head=True)
    conn([(436.0,493.1),(436.0,503.0),(498.1,503.0),(498.1,514.6)], head=True)

    # Vertical end states.
    end_cards = [
        (71.3, "NO EGRESS", "End:\nAir-gapped\nsovereign", "Owned\nadaptable\nGPUs,\nisolated.", "S8", True),
        (130.4, "DEDICATED", "End:\nSelf-hosted\nopen model", "Owned or\ndedicated\nGPU.", "S8", False),
        (195.4, "TRAIN\nWEIGHTS", "End:\nFine-tuned\nopen model", "Model\nflywheel\nstays yours.", "S6", False),
        (254.4, "COMPOUND", "End:\nOwned\nontology +\ncontext", "Context\nflywheel,\nmodel-agnostic.", "S15", True),
        (319.3, "ATTESTED", "End:\nRented GPU\n+ Attestation", "Confidential\ncompute,\nverified\nexecution.", "S9", False),
        (378.4, "ZDR CLOUD", "End:\nClosed\nmodel\nunder ZDR", "No retention\nor training.", "S1", False),
        (443.2, "LOW-RISK\nDATA", "End:\nEnterprise\nprivacy\nmode", "Redact;\ncap retention;\naudit.", "S12", False),
        (502.3, "PUBLIC\nONLY", "End:\nAny model,\nswappable", "Commodity\ntasks;\nno secrets.", "S10", False),
    ]
    for rx,label,title,body,src,filled in end_cards:
        rbox(rx,595.0,50.6,97.8,title,body,label,fill=pal.blue_light if filled else pal.page,stroke=pal.blue,title_size=5.5,body_size=4.55,label_size=4.25)
        mini_tag(rx+6.7,611.9 if label not in {"TRAIN\nWEIGHTS","PUBLIC\nONLY"} else 618.5, src)
    # Brackets from workload classes to end states.
    pairs = [(126.2,96.6),(126.2,155.7),(250.2,220.7),(250.2,279.7),(374.2,344.6),(374.2,403.7),(498.1,468.5),(498.1,527.6)]
    for parent,child in pairs:
        conn([(parent,572.5),(parent,583.0),(child,583.0),(child,595.0)], head=True)


def figure_zdr_architecture(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    # Reference coordinates are normalized to a figure region beginning at page x=58.7,y=220.6.
    bx0, by0, bw0, bh0 = 58.7, 220.6, 480.7, 395.2
    sx, sy = w / bw0, h / bh0
    def X(v: float) -> float: return x + (v - bx0) * sx
    def Y(v: float) -> float: return y + (v - by0) * sy
    def W(v: float) -> float: return v * sx
    def H(v: float) -> float: return v * sy
    def rbox(rx, ry, rw, rh, title, body="", label="", fill=None, stroke=None, dashed=False, title_size=6.5, body_size=5.0, label_size=4.8, center=False):
        box(c, style, X(rx), Y(ry), W(rw), H(rh), title, body, label, fill=fill or pal.page, stroke=stroke or pal.text, dashed=dashed, title_size=title_size*min(sx, sy), body_size=body_size*min(sx, sy), label_size=label_size*min(sx, sy), pad=6*min(sx, sy), center=center)
    def arr(x1,y1,x2,y2,color=None):
        arrow(c, style, X(x1), Y(y1), X(x2), Y(y2), color=color or pal.blue, width=0.61*min(sx, sy))
    def conn(points, color=None, dash=None, head=True):
        connector(c, style, [(X(px),Y(py)) for px,py in points], color=color or pal.blue, width=0.61*min(sx, sy), dash=dash, head=head)

    def _pt(rx: float, ry: float) -> tuple[float, float]:
        return X(rx), y_from_top(style, Y(ry))

    def shield_icon(rx: float, ry: float, size: float = 16.0) -> None:
        s = size * min(sx, sy)
        px, py = _pt(rx, ry)
        c.saveState()
        c.setFillColor(pal.blue)
        c.setStrokeColor(pal.blue)
        path = c.beginPath()
        path.moveTo(px + 0.50*s, py)
        path.lineTo(px + 0.92*s, py - 0.18*s)
        path.lineTo(px + 0.82*s, py - 0.72*s)
        path.lineTo(px + 0.50*s, py - 1.00*s)
        path.lineTo(px + 0.18*s, py - 0.72*s)
        path.lineTo(px + 0.08*s, py - 0.18*s)
        path.close()
        c.drawPath(path, stroke=0, fill=1)
        set_stroke(c, pal.white, max(1.0 * min(sx, sy), 0.6))
        c.line(px + 0.32*s, py - 0.50*s, px + 0.46*s, py - 0.66*s)
        c.line(px + 0.46*s, py - 0.66*s, px + 0.72*s, py - 0.33*s)
        c.restoreState()

    def database_icon(rx: float, ry: float, size: float = 16.0) -> None:
        s = size * min(sx, sy)
        px, py = _pt(rx, ry)
        c.saveState()
        c.setFillColor(pal.text)
        # Three stacked disks. This keeps the icon open instead of rendering as a block.
        for off in (0.00, 0.30, 0.60):
            c.ellipse(px, py - (off + 0.22)*s, px + s, py - off*s, stroke=0, fill=1)
        c.restoreState()

    def warning_icon(rx: float, ry: float, size: float = 16.0) -> None:
        s = size * min(sx, sy)
        px, py = _pt(rx, ry)
        c.saveState()
        c.setFillColor(pal.orange)
        path = c.beginPath()
        path.moveTo(px + 0.50*s, py)
        path.lineTo(px + s, py - 0.90*s)
        path.lineTo(px, py - 0.90*s)
        path.close()
        c.drawPath(path, stroke=0, fill=1)
        draw_centered_text(c, style, px, Y(ry + 4.2), s, "!", font=style.fonts.bold, size=8.2*min(sx, sy), color=pal.white)
        c.restoreState()

    draw_text(c, style, X(58.7), Y(220.6), data.get("left_title", "With ZDR"), font=style.fonts.semibold, size=7.0*min(sx, sy))
    draw_text(c, style, X(309.1), Y(220.6), data.get("right_title", "Without ZDR"), font=style.fonts.semibold, size=7.0*min(sx, sy))
    if data.get("right_subtitle", "or through employees' personal accounts"):
        draw_text(c, style, X(365.5), Y(222.6), data.get("right_subtitle", "or through employees' personal accounts"), font=style.fonts.medium, size=5.55*min(sx, sy), color=pal.text)

    # Four request/response boxes per column.
    left_flow = [
        (58.7,241.4,"Enterprise","Sends request from inside\nthe trust boundary.","ORIGIN"),
        (181.5,241.4,"Prompt","Question • context\n• instructions.","STEP 1"),
        (58.7,315.6,"Model","Processes in-memory.\nNothing written to disk.","STEP 2"),
        (181.5,315.6,"Response","Returned to\ncaller only.","STEP 3"),
    ]
    right_flow = [
        (309.1,241.4,"Enterprise","Sends request from inside\nthe trust boundary.","ORIGIN"),
        (431.9,241.4,"Prompt","Question • context\n• instructions.","STEP 1"),
        (309.1,315.6,"Model","Third-party inference. Logs,\ncaches, and telemetry are on.","STEP 2"),
        (431.9,315.6,"Response","Returned to caller\n- and copied aside.","STEP 3"),
    ]
    for rx,ry,t,b,l in left_flow + right_flow:
        rbox(rx,ry,107.4,50.6,t,b,l,title_size=6.4,body_size=4.9,label_size=4.55)
    # flow arrows and turnbacks
    for colx in [58.7,309.1]:
        arr(colx+107.4,266.7,colx+122.8-3,266.7)
        conn([(colx+176.4,292.0),(colx+176.4,303.5),(colx+53.7,303.5),(colx+53.7,315.6)], head=True)
        arr(colx+107.4,340.9,colx+122.8-3,340.9)
        conn([(colx+176.4,366.2),(colx+176.4,379.5),(colx+115.1,379.5),(colx+115.1,389.2)], head=True)

    rbox(58.7,389.2,230.2,43.1,"Enterprise","Receives output. Trust boundary intact.","END",stroke=pal.blue,title_size=6.5,body_size=5.1,label_size=4.55)
    rbox(309.1,389.2,230.3,43.1,"Enterprise","Receives output. Trust boundary already crossed.","END",dashed=True,stroke=pal.text,title_size=6.5,body_size=5.1,label_size=4.55)
    # Summary callouts with small pictograms, matching the icon density in the reference.
    box(c, style, X(58.7), Y(440.7), W(230.2), H(51.5), "", "", fill=pal.blue_light, stroke=pal.blue, pad=0)
    shield_icon(68.0, 452.8, 16.0)
    draw_text(c, style, X(92.5), Y(450.6), "No data retained", font=style.fonts.semibold, size=6.4*min(sx, sy))
    draw_wrapped(c, style, X(92.5), Y(461.0), W(165.0), "No training on your inputs.\nNo content stored, no discovery trail on the text.\nContent is never written to disk.", font=style.fonts.medium, size=4.7*min(sx, sy), leading=5.9*min(sx, sy))
    box(c, style, X(309.1), Y(440.7), W(230.3), H(51.5), "", "", fill=pal.gray_light, stroke=pal.text, pad=0)
    database_icon(319.6, 453.2, 16.0)
    draw_text(c, style, X(342.0), Y(450.6), "Your data stored by third-party providers", font=style.fonts.semibold, size=6.4*min(sx, sy))
    draw_wrapped(c, style, X(342.0), Y(461.0), W(170.0), "Prompts, outputs, and telemetry persist in\nthe provider's systems. Metadata is kept\neven when content isn't.", font=style.fonts.medium, size=4.7*min(sx, sy), leading=5.9*min(sx, sy))
    # shared risk note and four orange risk cards
    box(c, style, X(58.7), Y(541.2), W(230.2), H(74.5), "", "", fill=pal.page, stroke=pal.orange, dashed=True, pad=0)
    warning_icon(75.0, 556.2, 16.0)
    draw_text(c, style, X(92.5), Y(551.6), "APPLIES TO BOTH SIDES", font=style.fonts.semibold, size=5.6*min(sx, sy))
    draw_text(c, style, X(92.5), Y(560.4), "Safety classifiers may store data for up to two years", font=style.fonts.semibold, size=5.6*min(sx, sy))
    draw_wrapped(c, style, X(92.5), Y(574.0), W(165.0), "Even under ZDR, classifiers read your inputs and outputs.\nThe derived metadata can persist.\nZDR is necessary, but not sufficient - hold your leverage.", font=style.fonts.medium, size=4.7*min(sx, sy), leading=5.7*min(sx, sy))
    def risk_card(rx: float, ry: float, title: str, body: str) -> None:
        box(c, style, X(rx), Y(ry), W(107.5), H(49.7), "", "", fill="#F9ECDC", stroke=pal.orange, pad=0)
        warning_icon(rx + 7.2, ry + 8.0, 7.8)
        draw_text(c, style, X(rx + 17.1), Y(ry + 8.0), "RISK", font=style.fonts.semibold, size=4.9*min(sx, sy), color=pal.text)
        draw_wrapped(c, style, X(rx + 9.0), Y(ry + 18.0), W(88.0), title, font=style.fonts.semibold, size=6.05*min(sx, sy), leading=6.9*min(sx, sy))
        draw_wrapped(c, style, X(rx + 9.0), Y(ry + 31.0), W(88.0), body, font=style.fonts.medium, size=4.85*min(sx, sy), leading=5.8*min(sx, sy))

    risks=[(309.1,516.5,"Trains future models","Your work sharpens\nsomeone else's system."),(431.9,516.5,"Feeds competitors","Capability drifts towards\nthe vendor."),(309.1,566.1,"Usable in litigation","Stored prompts become\ndiscovery targets."),(431.9,566.1,"Metadata abuse","Who asked what, when\n- retained regardless.")]
    for rx,ry,t,b in risks:
        risk_card(rx,ry,t,b)
    # connector from stored-data box to risk cards.
    conn([(424.2,492.2),(424.2,503.0),(362.8,503.0),(362.8,516.5)], head=True)
    conn([(424.2,492.2),(424.2,503.0),(485.6,503.0),(485.6,516.5)], head=True)
def draw_figure(c: Canvas, style: Style, figure: dict, x: float, y: float, w: float, h: float) -> None:
    fig_type = (figure.get("type") or "flywheel").strip().lower().replace("-", "_")
    builder = FIGURE_BUILDERS.get(fig_type)
    if not builder:
        valid = ", ".join(sorted(FIGURE_BUILDERS))
        raise ValueError(f"unknown figure type '{fig_type}'. Valid types: {valid}")
    builder(c, style, x, y, w, h, figure)


FIGURE_BUILDERS: Dict[str, Callable[[Canvas, Style, float, float, float, float, dict], None]] = {
    "zdr_architecture": figure_zdr_architecture,
    "decision_tree": figure_decision_tree,
    "architecture_layers": figure_architecture_layers,
    "tribal_ownership": figure_tribal_ownership,
    "agent_harness": figure_agent_harness,
    "model_flywheel": figure_flywheel,
    "context_flywheel": figure_context_flywheel,
    "assurance_levels": figure_assurance_levels,
    "on_prem_architecture": figure_on_prem,
    "attestation": figure_attestation,
    "control_layer": figure_control_layer,
    "permissions": figure_permissions,
    "audit_logs": figure_audit_logs,
    "security_forge": figure_security_forge,
    "branching": figure_branching,
    "flywheel": figure_flywheel,
}


def figure_decision_tree_reference(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    """Dense page-figure decision tree based on the reference geometry."""
    pal = style.palette
    ref_w, ref_h = 481.6, 599.6
    sx = w / ref_w if ref_w else 1.0
    sy = h / ref_h if ref_h else 1.0
    sc = min(sx, sy)

    def X(v: float) -> float:
        return x + v * sx

    def Y(v: float) -> float:
        return y + v * sy

    def W(v: float) -> float:
        return v * sx

    def H(v: float) -> float:
        return v * sy

    def small_square(rx, ry, fill, stroke, dashed=False):
        c.saveState()
        c.setFillColor(fill)
        set_stroke(c, stroke, style.line_width, [1.8667, 0.9334] if dashed else None)
        rect_top(c, style, X(rx), Y(ry), W(10.2), H(7.7), stroke=1, fill=1 if fill else 0)
        c.restoreState()

    def source_tags(rx, ry, tags, size=5.2):
        cx = X(rx)
        for t in tags:
            tw = tag(c, style, cx, Y(ry), t, size=size * sc, fill=pal.blue_faint, stroke=pal.blue)
            cx += tw + 2.8 * sc
        return cx

    def decision_box(rx, ry, rw, rh, title, body, tags=None, dashed=False, fill=None, stroke=None):
        box(c, style, X(rx), Y(ry), W(rw), H(rh), "", "", fill=fill or pal.page, stroke=stroke or pal.text, dashed=dashed, pad=0)
        tx = X(rx + 8)
        ty = Y(ry + 8)
        if tags:
            after = source_tags(rx + 8, ry + 8.5, tags)
            tx = after + 5 * sc
        draw_wrapped(c, style, tx, ty, W(rw - 16) - (tx - X(rx + 8)), title, font=style.fonts.semibold, size=8.0 * sc, leading=9.3 * sc)
        draw_wrapped(c, style, X(rx + 8), Y(ry + 25.0), W(rw - 16), body, font=style.fonts.medium, size=6.9 * sc, leading=8.4 * sc)

    # Legend.
    small_square(0, 0, pal.blue_faint, pal.blue)
    draw_text(c, style, X(15), Y(-1), "Decision", font=style.fonts.medium, size=7.1 * sc)
    small_square(58.4, 0, None, pal.text)
    draw_text(c, style, X(73.4), Y(-1), "End State", font=style.fonts.medium, size=7.1 * sc)
    small_square(149.0, 0, None, pal.gray, dashed=True)
    draw_text(c, style, X(164.0), Y(-1), "Hold / No-Go", font=style.fonts.medium, size=7.1 * sc)
    source_tags(210.0, 0, ["S#"], size=5.2)
    draw_text(c, style, X(230.0), Y(-1), "Source Step", font=style.fonts.medium, size=7.1 * sc)

    # Top decision stack.
    decision_box(0, 24.4, 295.7, 40.4, "How should we implement this AI workflow?", "Route the whole stack before choosing any model or compute.", tags=["S2"])
    decision_box(0, 80.7, 295.7, 49.7, "ZDR + zero-trust review complete?", "ZDR negotiated per provider; model, compute, and control layers reviewed. Any non-ZDR frontier model is treated as extraction-prone (EPM).", tags=["S1", "S3", "S4"])
    decision_box(309.8, 80.7, 171.7, 49.7, "End: Do not implement yet", "Close ZDR gaps and EPM exposure.", tags=None, dashed=True, stroke=pal.text)
    draw_text(c, style, X(317.8), Y(91.2), "NO", font=style.fonts.semibold, size=6.3 * sc, color=pal.text)
    decision_box(0, 146.1, 295.7, 49.7, "Does this workflow need model inference?", "If deterministic software solves it, own the tool in your control layer instead - no model, no extraction surface.")
    decision_box(309.8, 146.1, 171.7, 49.7, "End: Own a deterministic tool", "Build it in the layer you control.", fill=pal.blue_light, stroke=pal.blue)
    draw_text(c, style, X(317.8), Y(156.5), "NO / TOOL-ONLY", font=style.fonts.semibold, size=6.3 * sc, color=pal.blue)
    decision_box(0, 211.1, 295.7, 63.0, "Does your control layer meet sovereignty criteria?", "Model agnostic     Granular permissions     Audit + log\nAdaptive cyber     Reversible branching\nOwned context flywheel / ontology", tags=["S10"])
    # More tags for control layer row.
    source_tags(83.0, 235.0, ["S11"])
    source_tags(176.8, 235.0, ["S12"])
    source_tags(8.0, 246.7, ["S13"])
    source_tags(83.0, 246.7, ["S14"])
    source_tags(8.0, 258.4, ["S15"])
    decision_box(309.8, 211.1, 171.7, 63.0, "Hold: Human-in-loop only", "Read-only AI until the control layer passes.", dashed=True, stroke=pal.text)
    draw_text(c, style, X(317.8), Y(221.6), "NOT READY", font=style.fonts.semibold, size=6.3 * sc, color=pal.text)
    decision_box(0, 289.9, 481.6, 39.9, "Classify knowledge -> Pick assurance level", "Structural assurance beats contractual. Match each workload to the strongest rung it needs.", tags=["S8", "S9"])

    # Vertical and side connectors.
    mid_x = 147.85
    for y1, y2 in [(64.8, 80.7), (130.4, 146.1), (195.8, 211.1), (274.1, 289.9)]:
        arrow(c, style, X(mid_x), Y(y1), X(mid_x), Y(y2 - 4), width=style.line_width)
    for ry, rh in [(80.7, 49.7), (146.1, 49.7), (211.1, 63.0)]:
        arrow(c, style, X(295.7), Y(ry + rh/2), X(309.8 - 4), Y(ry + rh/2), width=style.line_width)

    # Middle assurance split.
    decision_box(0, 351.6, 233.2, 48.3, "Structural assurance needed?", "Physical / technical isolation - own or dedicate the compute.", tags=["S7"])
    decision_box(248.1, 351.6, 233.2, 48.3, "Contractual or public tier?", "External service only with limits and exit leverage (model liquidity).", tags=["S5", "S9"])
    connector(c, style, [(X(240.8), Y(329.8)), (X(240.8), Y(339.4)), (X(116.6), Y(339.4)), (X(116.6), Y(351.6))], width=style.line_width, head=True)
    connector(c, style, [(X(240.8), Y(329.8)), (X(240.8), Y(339.4)), (X(364.7), Y(339.4)), (X(364.7), Y(351.6))], width=style.line_width, head=True)

    # Workload classes.
    classes = [
        (0, 421.4, 109.8, 57.9, "Classified / sensitive", "Low or zero-tolerance data.", []),
        (124.0, 421.4, 109.8, 57.9, "High-alpha knowhow", "Signal must compound in-house.", ["S6"]),
        (248.0, 421.4, 109.8, 57.9, "Internal / regulated", "No classified data; contract must hold.", []),
        (371.9, 421.4, 109.8, 57.9, "Public / low-alpha", "Retention risk is accepted.", []),
    ]
    for rx, ry, rw, rh, title, body, tags in classes:
        decision_box(rx, ry, rw, rh, title, body, tags=tags)
    for top_c, left_c, right_c in [(116.6, 54.9, 178.9), (364.7, 302.9, 426.8)]:
        connector(c, style, [(X(top_c), Y(399.9)), (X(top_c), Y(410.8)), (X(left_c), Y(410.8)), (X(left_c), Y(421.4))], width=style.line_width, head=True)
        connector(c, style, [(X(top_c), Y(399.9)), (X(top_c), Y(410.8)), (X(right_c), Y(410.8)), (X(right_c), Y(421.4))], width=style.line_width, head=True)

    # End state cards.
    end_cards = [
        (0, "NO EGRESS", "S8", "End:\nAir-gapped\nsovereign", "Owned adaptable GPUs, isolated.", True),
        (59.1, "DEDICATED", "S8", "End:\nSelf-hosted\nopen model", "Owned or dedicated GPU.", False),
        (124.1, "TRAIN\nWEIGHTS", "S6", "End:\nFine-tuned\nopen model", "Model flywheel stays yours.", False),
        (183.1, "COMPOUND", "S15", "End:\nOwned ontology +\ncontext", "Context flywheel, model-agnostic.", True),
        (248.0, "ATTESTED", "S9", "End:\nRented GPU\n+Attestation", "Confidential compute, verified execution.", False),
        (307.1, "ZDR CLOUD", "S1", "End:\nClosed model\nunder ZDR", "No retention or training.", False),
        (371.9, "LOW-RISK\nDATA", "S12", "End:\nEnterprise\nprivacy mode", "Redact; cap retention; audit.", False),
        (431.0, "PUBLIC\nONLY", "S10", "End:\nAny model,\nswappable", "Commodity tasks; no secrets.", False),
    ]
    for rx, label, st, title, body, light in end_cards:
        box(c, style, X(rx), Y(501.8), W(50.6), H(97.8), "", "", fill=pal.blue_light if light else pal.page, stroke=pal.blue, pad=0)
        draw_wrapped(c, style, X(rx + 6), Y(511.3), W(40), label, font=style.fonts.semibold, size=5.4 * sc, leading=6.5 * sc, color=pal.blue)
        tag(c, style, X(rx + 6), Y(528.5), st, size=5.0 * sc, fill=pal.blue_faint, stroke=pal.blue)
        draw_wrapped(c, style, X(rx + 6), Y(546.0), W(40), title, font=style.fonts.semibold, size=6.5 * sc, leading=7.2 * sc)
        draw_wrapped(c, style, X(rx + 6), Y(586.0), W(40), body, font=style.fonts.medium, size=5.6 * sc, leading=6.3 * sc)

    # Bottom split connectors from classes to end cards.
    splits = [(54.9, 25.3, 84.4), (178.9, 149.4, 208.4), (302.9, 273.3, 332.4), (426.8, 397.2, 456.3)]
    for class_c, left_c, right_c in splits:
        connector(c, style, [(X(class_c), Y(479.3)), (X(class_c), Y(490.5)), (X(left_c), Y(490.5)), (X(left_c), Y(501.8))], width=style.line_width, head=True)
        connector(c, style, [(X(class_c), Y(479.3)), (X(class_c), Y(490.5)), (X(right_c), Y(490.5)), (X(right_c), Y(501.8))], width=style.line_width, head=True)


# Override the simpler default with the denser reference-like version.
FIGURE_BUILDERS["decision_tree"] = figure_decision_tree_reference

# v2 overrides: calibrated against the uploaded reference page geometry.
def figure_decision_tree_v2(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    sx = w / 483.1
    sy = h / 604.8
    x0, y0 = 69.8, 88.0
    def X(v): return x + (v - x0) * sx
    def Y(v): return y + (v - y0) * sy
    def W(v): return v * sx
    def H(v): return v * sy

    def small_tags(tags, tx, ty):
        xx = tx
        for t in tags:
            xx += tag(c, style, xx, ty, t, size=4.7, fill=pal.blue_faint, stroke=pal.blue) + 3.0 * sx
        return xx

    def card(rx, ry, rw, rh, title, body="", tags=None, fill=None, stroke=None, dashed=False, label=None, title_size=7.6, body_size=6.0, pad=8, blue_label=False):
        box(c, style, X(rx), Y(ry), W(rw), H(rh), "", "", fill=fill or pal.page, stroke=stroke or pal.text, dashed=dashed, pad=0)
        tx = X(rx) + W(pad)
        yy = Y(ry) + H(9)
        if label:
            yy = draw_wrapped(c, style, tx, yy, W(rw) - W(2 * pad), label, font=style.fonts.semibold, size=5.7 * min(sx, sy), leading=6.3 * sy, color=pal.blue if blue_label else pal.text)
            yy += H(3)
        if tags:
            tx2 = small_tags(tags, tx, yy - H(1))
            draw_wrapped(c, style, tx2 + W(3), yy, W(rw) - (tx2 - X(rx)) - W(pad + 3), title, font=style.fonts.semibold, size=title_size * min(sx, sy), leading=title_size * 1.15 * sy)
            yy += H(14)
        else:
            yy = draw_wrapped(c, style, tx, yy, W(rw) - W(2 * pad), title, font=style.fonts.semibold, size=title_size * min(sx, sy), leading=title_size * 1.2 * sy)
            yy += H(3)
        if body:
            draw_wrapped(c, style, tx, yy, W(rw) - W(2 * pad), body, font=style.fonts.medium, size=body_size * min(sx, sy), leading=body_size * 1.23 * sy)

    # Legend row.
    ly = Y(93.16)
    lx = X(71.3)
    def legend_square(xp, fill, stroke, dashed=False):
        box(c, style, xp, ly, W(10.2), H(7.7), "", "", fill=fill, stroke=stroke, dashed=dashed, pad=0)
    legend_square(lx, pal.blue_faint, pal.blue)
    draw_text(c, style, lx + W(15), Y(91.0), "Decision", size=8.4 * min(sx, sy))
    legend_square(X(129.7), pal.page, pal.text)
    draw_text(c, style, X(144.5), Y(91.0), "End State", size=8.4 * min(sx, sy))
    legend_square(X(192.1), pal.page, pal.gray, dashed=True)
    draw_text(c, style, X(207.0), Y(91.0), "Hold / No-Go", size=8.4 * min(sx, sy))
    tag(c, style, X(269.2), Y(93.2), "S#", size=4.8 * min(sx, sy), fill=pal.blue_faint, stroke=pal.blue)
    draw_text(c, style, X(286.0), Y(91.0), "Source Step", size=8.4 * min(sx, sy))

    # Main route. The first row has its source-step chip on the subline in the reference.
    box(c, style, X(71.3), Y(117.6), W(295.7), H(40.4), "", "", fill=pal.page, stroke=pal.text, pad=0)
    draw_text(c, style, X(78.3), Y(123.2), "How should we implement this AI workflow?", font=style.fonts.semibold, size=10.267 * min(sx, sy))
    small_tags(["S2"], X(81.2), Y(140.3))
    draw_text(c, style, X(94.1), Y(139.6), "Route the whole stack before choosing any model or compute.", font=style.fonts.medium, size=7.467 * min(sx, sy))
    card(71.3, 173.9, 295.7, 49.7, "ZDR + zero-trust review complete?", "ZDR negotiated per provider; model, compute, and control layers reviewed.\nAny non-ZDR frontier model is treated as extraction-prone (EPM).", tags=["S1", "S3", "S4"], title_size=8.4, body_size=7.1)
    card(381.1, 173.9, 171.8, 49.7, "End: Do not implement yet", "Close ZDR gaps and EPM exposure.", label="NO", dashed=True, stroke=pal.gray, title_size=8.4, body_size=7.0)
    card(71.3, 239.3, 295.7, 49.8, "Does this workflow need model inference?", "If deterministic software solves it, own the tool in your control layer instead\n- no model, no extraction surface.", title_size=8.4, body_size=7.1)
    card(381.1, 239.3, 171.8, 49.8, "End: Own a deterministic tool", "Build it in the layer you control.", label="NO / TOOL-ONLY", fill=pal.blue_light, stroke=pal.blue, title_size=8.4, body_size=7.1, blue_label=True)
    card(71.3, 304.3, 295.7, 63.0, "Does your control layer meet sovereignty criteria?", "", title_size=8.4, body_size=7.05)

    def criteria_row(items, tx, ty):
        xx = X(tx)
        for st, text in items:
            xx += tag(c, style, xx, Y(ty - 0.4), st, size=4.6 * min(sx, sy), fill=pal.blue_faint, stroke=pal.blue) + W(3.0)
            draw_text(c, style, xx, Y(ty), text, font=style.fonts.medium, size=7.05 * min(sx, sy))
            xx += pdfmetrics.stringWidth(text, style.fonts.medium, 7.05 * min(sx, sy)) + W(8.0)

    criteria_row([("S10", "Model agnostic"), ("S11", "Granular permissions"), ("S12", "Audit + log")], 79.0, 329.1)
    criteria_row([("S13", "Adaptive cyber"), ("S14", "Reversible branching")], 79.0, 341.0)
    criteria_row([("S15", "Owned context flywheel / ontology")], 79.0, 352.9)
    card(381.1, 304.3, 171.8, 63.0, "Hold: Human-in-loop only", "Read-only AI until the control layer passes.", label="NOT READY", dashed=True, stroke=pal.gray, title_size=8.4, body_size=7.0)
    card(71.3, 383.1, 481.6, 39.9, "Classify knowledge -> Pick assurance level", "Structural assurance beats contractual. Match each workload to the strongest rung it needs.", tags=["S8", "S9"], title_size=8.4, body_size=7.1)

    # Connectors.
    for (a, b) in [(158.0, 173.9), (223.6, 239.3), (289.1, 304.3), (367.3, 383.1)]:
        arrow(c, style, X(219.2), Y(a), X(219.2), Y(b - 4), width=0.6)
    arrow(c, style, X(367.0), Y(198.8), X(381.1 - 5), Y(198.8), width=0.6)
    arrow(c, style, X(367.0), Y(264.2), X(381.1 - 5), Y(264.2), width=0.6)
    arrow(c, style, X(367.0), Y(335.8), X(381.1 - 5), Y(335.8), width=0.6)

    # Assurance / public branches.
    card(71.3, 444.8, 233.2, 48.3, "Structural assurance needed?", "Physical / technical isolation\n- own or dedicate the compute.", tags=["S7"], title_size=8.4, body_size=7.2)
    card(319.4, 444.8, 233.3, 48.3, "Contractual or public tier?", "External service only with limits and\nexit leverage (model liquidity).", tags=["S5", "S9"], title_size=8.4, body_size=7.2)
    connector(c, style, [(X(219.2), Y(423.0)), (X(219.2), Y(431.0)), (X(187.9), Y(431.0)), (X(187.9), Y(444.8))], width=0.6)
    connector(c, style, [(X(219.2), Y(423.0)), (X(219.2), Y(431.0)), (X(436.0), Y(431.0)), (X(436.0), Y(444.8))], width=0.6)

    # Workload classes.
    mids = [126.2, 250.2, 374.2, 498.1]
    class_cards = [
        (71.3, 514.6, 109.8, 57.9, "Classified / sensitive", "Low or zero-\ntolerance data."),
        (195.3, 514.6, 109.8, 57.9, "High-alpha knowhow", "Signal must compound\nin-house."),
        (319.3, 514.6, 109.8, 57.9, "Internal / regulated", "No classified data;\ncontract must hold."),
        (443.2, 514.6, 109.8, 57.9, "Public / low-alpha", "Retention risk\nis accepted."),
    ]
    for cc in class_cards:
        card(*cc, title_size=8.4, body_size=7.2)
    # Optional S6 tag in the high-alpha card is omitted by default for legibility.
    # curly-ish branch connectors above class cards.
    for cx in mids:
        connector(c, style, [(X(cx), Y(493.1)), (X(cx), Y(501.5)), (X(cx - 28), Y(501.5)), (X(cx - 28), Y(514.6))], width=0.6)
        connector(c, style, [(X(cx), Y(493.1)), (X(cx), Y(501.5)), (X(cx + 28), Y(501.5)), (X(cx + 28), Y(514.6))], width=0.6)

    endpoints = [
        (71.3, 595.0, 50.6, 97.8, "NO EGRESS", "End:\nAir-gapped\nsovereign", "Owned\nadaptable\nGPUs,\nisolated.", True, "S8"),
        (130.4, 595.0, 50.6, 97.8, "DEDICATED", "End:\nSelf-hosted\nopen model", "Owned or\ndedicated\nGPU.", False, "S8"),
        (195.4, 595.0, 50.6, 97.8, "TRAIN\nWEIGHTS", "End:\nFine-tuned\nopen model", "Model\nflywheel\nstays yours.", False, "S6"),
        (254.4, 595.0, 50.6, 97.8, "COMPOUND", "End:\nOwned\nontology +\ncontext", "Context\nflywheel,\nmodel-\nagnostic.", True, "S15"),
        (319.3, 595.0, 50.6, 97.8, "ATTESTED", "End:\nRented GPU\n+Attestation", "Confidential\ncompute,\nverified\nexecution.", False, "S9"),
        (378.4, 595.0, 50.6, 97.8, "ZDR CLOUD", "End:\nClosed\nmodel\nunder ZDR", "No retention\nor training.", False, "S1"),
        (443.2, 595.0, 50.6, 97.8, "LOW-RISK\nDATA", "End:\nEnterprise\nprivacy\nmode", "Redact;\ncap retention;\naudit.", False, "S12"),
        (502.3, 595.0, 50.6, 97.8, "PUBLIC\nONLY", "End:\nAny model,\nswappable", "Commodity\ntasks;\nno secrets.", False, "S10"),
    ]
    for rx, ry, rw, rh, lab, title, body, filled, step in endpoints:
        card(rx, ry, rw, rh, title, body, label=lab, fill=pal.blue_light if filled else pal.page, stroke=pal.blue, title_size=6.0, body_size=4.9, pad=6, blue_label=True)
        # Source-step chip intentionally omitted in the narrow end-state cards for legibility.


def _install_v2_overrides() -> None:
    FIGURE_BUILDERS["decision_tree"] = figure_decision_tree_v2

_install_v2_overrides()

# v4 override: fixed reference geometry for Fig. 10.
def figure_control_layer_v4(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    sx = w / 482.1
    ss = sx
    def X(v: float) -> float: return x + v * sx
    def Y(v: float) -> float: return y + v * sx
    def W(v: float) -> float: return v * sx
    def H(v: float) -> float: return v * sx
    blue_dark = getattr(pal, "blue_dark", pal.blue)

    # Top control layer.
    box(c, style, X(0), Y(0), W(482.1), H(67.2), "Control layer", "Governs every workload across the stack", fill=pal.page, stroke=pal.text, title_size=10.1*ss, body_size=8.55*ss, pad=12*ss)
    controls = data.get("controls") or ["$ Model-agnostic routing", "▣ Granular permissions", "◉ Auditability & logs", "↯ Branching"]
    cx = 26.0
    for i, item in enumerate(controls[:4]):
        draw_text(c, style, X(cx), Y(51.8), item, font=style.fonts.medium, size=7.55*ss, color=pal.text)
        cx += [112, 108, 110, 70][i]

    # Modular intelligence layer.
    my, mh = 80.4, 144.0
    box(c, style, X(0), Y(my), W(482.1), H(mh), "", "", fill=pal.page, stroke=blue_dark, pad=0)
    draw_text(c, style, X(26), Y(my+16.6), "Modular intelligence layer", font=style.fonts.semibold, size=10.1*ss, color=pal.text)
    draw_text(c, style, X(26), Y(my+36.6), "Treated as a commodity, not a foundation", font=style.fonts.medium, size=8.7*ss, color=pal.text)
    card_y = my + 49.2
    card_w, card_h = 105.6, 38.4
    card_xs = [12.6, 129.9, 247.2, 364.5]
    models = data.get("models") or [
        {"title": "Model A", "body": "External, under ZDR"},
        {"title": "Model B", "body": "External, under ZDR"},
        {"title": "Model C", "body": "External, under ZDR"},
        {"title": "Self-hosted", "body": "Open-weight, owned", "dashed": True},
    ]
    for i, m in enumerate(models[:4]):
        box(c, style, X(card_xs[i]), Y(card_y), W(card_w), H(card_h), m.get("title", ""), m.get("body", ""), fill=pal.page, stroke=blue_dark, dashed=m.get("dashed", False), title_size=8.15*ss, body_size=6.85*ss, pad=8*ss)
    box(c, style, X(12.6), Y(my+100.2), W(456.9), H(31.2), "↔  Model liquidity - switch with minimal friction", "", fill=pal.page, stroke=blue_dark, center=True, title_size=8.2*ss, pad=7*ss)

    draw_text(c, style, X(117), Y(246.0), "↓ Context, prompts, permissions", font=style.fonts.semibold, size=8.1*ss, color=pal.text)
    draw_text(c, style, X(253), Y(246.0), "↑ Outputs, knowhow, weights", font=style.fonts.semibold, size=8.1*ss, color=pal.text)

    # Owned knowledge / ontology layer.
    oy, oh = 262.0, 205.2
    box(c, style, X(0), Y(oy), W(482.1), H(oh), "", "", fill=pal.page, stroke=pal.blue, pad=0)
    draw_text(c, style, X(26), Y(oy+16.5), "Owned knowledge layer • ontology", font=style.fonts.semibold, size=10.1*ss, color=pal.text)
    draw_text(c, style, X(26), Y(oy+36.5), "A digital twin of your organization", font=style.fonts.medium, size=8.8*ss, color=pal.text)
    objs = data.get("ontology_items") or [
        {"title": "Objects", "body": "Nouns\n- entities, events"},
        {"title": "Properties", "body": "Attributes of\neach object"},
        {"title": "Links", "body": "Relations between\nobjects"},
        {"title": "Actions", "body": "Verbs\n- structured change"},
    ]
    for i, o in enumerate(objs[:4]):
        box(c, style, X(card_xs[i]), Y(oy+49.2), W(card_w), H(48.6), o.get("title", ""), o.get("body", ""), fill=pal.page, stroke=pal.blue, title_size=8.25*ss, body_size=7.0*ss, pad=8*ss)
    half_w = 222.6
    box(c, style, X(12.6), Y(oy+110.4), W(half_w), H(39.0), "Transactional data", "Records you already generate", fill=pal.page, stroke=pal.blue, title_size=8.1*ss, body_size=6.8*ss, pad=8*ss)
    box(c, style, X(247.2), Y(oy+110.4), W(half_w), H(39.0), "Action data", "Captured only if structured", fill=pal.page, stroke=pal.blue, title_size=8.1*ss, body_size=6.8*ss, pad=8*ss)
    box(c, style, X(12.6), Y(oy+161.4), W(456.9), H(31.2), "↻  Eval loop - captures usage, compounds it back into the ontology", "", fill=pal.page, stroke=pal.blue, center=True, title_size=8.0*ss, pad=7*ss)

FIGURE_BUILDERS["control_layer"] = figure_control_layer_v4

# v4.1 override: denser Fig. 12 audit-log chain with per-field records.
def figure_audit_logs_dense(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    gap = 12.0
    bw = (w - gap * 4) / 5.0
    top_y = y + 10
    detail_y = y + 105
    stream_y = y + 172
    audit_y = y + 214
    steps = [
        ("01", "INITIATOR", "User / Agent", "Identity, role, and\nsession that initiated\nthe request.", "10:24:07.412Z", "actor", "u_9142 - role=analyst"),
        ("02", "INPUT", "Prompt / Query", "Exact text, tool calls,\nand parameters\nsubmitted.", "10:24:07.418Z", "prompt", "sha256: a4f1 - 812 tok"),
        ("03", "INFERENCE", "Model Called", "Provider, model\nname, version, and\nrouting choice.", "10:24:07.611Z", "model", "frontier-model-6.5\nroute=zdr"),
        ("04", "RETRIEVAL", "Data Accessed", "Ontology objects and\nrows read from the\nknowledge layer.", "10:24:07.634Z", "object", "Orderx14 - Customerx3"),
        ("05", "OUTPUT", "Action / Result", "Response returned\nor side effect\ncommitted.", "10:24:08.902Z", "result", "write=Report:R-8821"),
    ]
    for i, (num, lab, title, body, ts, key, val) in enumerate(steps):
        bx = x + i * (bw + gap)
        box(c, style, bx, top_y, bw, 75, title, body, num, fill=pal.page, stroke=pal.text, accent="left", title_size=7.0, body_size=5.35, label_size=5.0, pad=6)
        draw_text(c, style, bx + 7, top_y + 22, lab, font=style.fonts.semibold, size=5.2, color=pal.blue)
        if i < 4:
            arrow(c, style, bx + bw, top_y + 37, bx + bw + gap - 3, top_y + 37, width=0.6)
        arrow(c, style, bx + bw / 2, top_y + 75, bx + bw / 2, detail_y - 5, width=0.6)
        box(c, style, bx, detail_y, bw, 50, "", "", fill=pal.page, stroke=pal.gray, dashed=True, pad=0)
        draw_text(c, style, bx + 7, detail_y + 8, ts, font=style.fonts.semibold, size=5.2, color=pal.blue)
        draw_text(c, style, bx + 7, detail_y + 22, key, font=style.fonts.medium, size=5.4, color=pal.text)
        draw_wrapped(c, style, bx + 7, detail_y + 34, bw - 14, val, font=style.fonts.medium, size=5.1, leading=6.0)
    box(c, style, x, stream_y, w, 20, "", "", fill=pal.page, stroke=pal.text, pad=0)
    draw_text(c, style, x + 8, stream_y + 6, "Append-only log stream", font=style.fonts.semibold, size=6.4)
    draw_text(c, style, x + w - 248, stream_y + 6, "trace_id = t.9c1e-4b - 5/5 entries - signed - immutable", font=style.fonts.medium, size=5.2)
    arrow(c, style, x + w / 2, stream_y + 20, x + w / 2, audit_y - 8, width=0.6)
    box(c, style, x, audit_y, w, max(70, h - (audit_y - y)), "Audit", "Reads the trace - Enforces sovereignty", fill=pal.blue_faint, stroke=pal.blue, title_size=7.5, body_size=5.7, pad=8)
    cards = [
        ("Replay", "Reconstruct any decision step-by-step from\nactor, prompt, model, and data touched."),
        ("Query", "Filter across traces by user, model, object, or\ntime to answer 'who touched what.'"),
        ("Detect misappropriation", "Trigger canaries and compare external model\noutputs against material only you provided."),
    ]
    card_gap = 10
    card_w = (w - 36 - card_gap * 2) / 3
    for i, (title, body) in enumerate(cards):
        box(c, style, x + 18 + i * (card_w + card_gap), audit_y + 45, card_w, 40, title, body, fill=pal.blue_light, stroke=pal.blue, title_size=6.5, body_size=5.05, pad=6)

FIGURE_BUILDERS["audit_logs"] = figure_audit_logs_dense

# v4 reference-geometry overrides.
def figure_tribal_ownership_v4(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    """Tribal-knowledge ownership flow, scaled from the reference page geometry."""
    pal = style.palette
    sx = w / 480.7
    sy = h / 383.0
    x0, y0 = 58.7, 321.0
    def X(v): return x + (v - x0) * sx
    def Y(v): return y + (v - y0) * sy
    def W(v): return v * sx
    def H(v): return v * sy
    def card(rx, ry, rw, rh, title, body='', label='', dashed=False, fill=None, stroke=None, blue_label=False, title_size=9.33, body_size=7.47):
        box(c, style, X(rx), Y(ry), W(rw), H(rh), '', '', fill=fill or pal.page, stroke=stroke or (pal.blue if blue_label else pal.text), dashed=dashed, pad=0)
        yy = Y(ry) + H(12.0)
        if label:
            draw_centered_text(c, style, X(rx), yy, W(rw), label, font=style.fonts.semibold, size=7.47*min(sx,sy), color=pal.blue if blue_label else pal.gray)
            yy += H(16)
        draw_centered_text(c, style, X(rx), yy, W(rw), title, font=style.fonts.semibold, size=title_size*min(sx,sy), color=pal.text)
        if body:
            yy += H(15)
            # Preserve a reference-like two-line body by accepting explicit newlines.
            for j, line in enumerate(str(body).split('\n')):
                draw_centered_text(c, style, X(rx)+W(8), yy + H(j*8.5), W(rw-16), line, font=style.fonts.medium, size=body_size*min(sx,sy), color=pal.text)
    # Root asset card.
    card(60.0, 327.3, 479.0, 43.4, 'Enterprise Tribal Knowledge', 'Unique operational knowhow, IP, and workflows. The same asset - captured only once.', stroke=pal.blue, title_size=9.33, body_size=8.4)
    draw_centered_text(c, style, X(60.0), Y(390.0), W(479.0), 'Who profits?', font=style.fonts.semibold, size=8.0*min(sx,sy), color=pal.text)
    # Split connectors.
    connector(c, style, [(X(300.0), Y(370.7)), (X(300.0), Y(405.0)), (X(174.0), Y(405.0)), (X(174.0), Y(438.0))], color=pal.gray, width=0.6, dash=style.dash, head=True)
    connector(c, style, [(X(300.0), Y(370.7)), (X(300.0), Y(405.0)), (X(425.0), Y(405.0)), (X(425.0), Y(438.0))], color=pal.blue, width=0.6, head=True)
    # Provider path.
    card(60.0, 441.5, 227.3, 67.4, 'External Model Weights', "Knowhow flows into a closed-provider's\ntraining set and API surface.", label='PROVIDER PATH', dashed=True, stroke=pal.gray, title_size=9.33, body_size=7.47)
    provider = [
        (60.0, 530.2, 'Leased to Competitors', 'Your workflows resold as\ngeneric capability to your rivals.'),
        (60.0, 590.0, 'Rent-Seeking on Workflows', 'Per-token pricing on your\nhighest-margin operations.'),
        (60.0, 649.9, 'Provider Replaces You', 'Vertical entry - the model owns\nthe customer relationship.'),
    ]
    for rx, ry, title, body in provider:
        card(rx, ry, 227.3, 54.1, title, body, dashed=True, stroke=pal.gray, title_size=9.33, body_size=7.47)
    for y1, y2 in [(508.9, 530.2), (584.3, 590.0), (644.1, 649.9)]:
        arrow(c, style, X(173.65), Y(y1), X(173.65), Y(y2-4), color=pal.gray, width=0.6)
    # Enterprise path.
    card(311.7, 441.5, 227.3, 67.4, 'Enterprise-Controlled System', 'Owned weights, owned ontology,\nsovereign control layer.', label='ENTERPRISE PATH', fill=pal.blue_light, stroke=pal.blue, blue_label=True, title_size=9.33, body_size=7.47)
    enterprise = [
        (311.7, 530.2, 'Compounding Alpha', 'Each cycle of usage sharpens\nthe moat you retain.'),
        (311.7, 590.0, 'Leverage Over Providers', 'Model liquidity - swap vendors\nwithout losing the knowhow.'),
        (311.7, 649.9, 'Own the Flywheel', 'Usage -> signal -> knowhow -> system\nstays inside the institution.'),
    ]
    for rx, ry, title, body in enterprise:
        card(rx, ry, 227.3, 54.1, title, body, fill=pal.blue_light, stroke=pal.blue, title_size=9.33, body_size=7.47)
    for y1, y2 in [(508.9, 530.2), (584.3, 590.0), (644.1, 649.9)]:
        arrow(c, style, X(425.35), Y(y1), X(425.35), Y(y2-4), color=pal.blue, width=0.6)

FIGURE_BUILDERS['tribal_ownership'] = figure_tribal_ownership_v4

def figure_flywheel_v4(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    """Reference-like four-box feedback loop; y is the top of the boxes."""
    pal = style.palette
    items = _labels(data, [
        {"title": "Usage", "body": "creates signal"},
        {"title": "Signal", "body": "gets structured"},
        {"title": "Knowhow", "body": "improves system"},
        {"title": "System", "body": "drives usage"},
    ])
    n = len(items)
    gap = 14.3
    bw = (w - gap * (n - 1)) / n
    bh = 38.6 if h > 70 else min(38.6, h * 0.55)
    by = y
    for i, item in enumerate(items):
        bx = x + i * (bw + gap)
        box(c, style, bx, by, bw, bh, item.get('title',''), item.get('body',''), fill=pal.page, stroke=pal.text, title_size=9.33, body_size=9.33, pad=8)
        if i < n - 1:
            arrow(c, style, bx + bw, by + bh / 2, bx + bw + gap - 3, by + bh / 2, width=0.6)
    start_x = x + w - bw / 2
    end_x = x + bw / 2
    yy = by + bh + 22
    connector(c, style, [(start_x, by + bh), (start_x, yy), (end_x, yy), (end_x, by + bh)], width=0.6, head=True)
    note = data.get('note')
    if note is None:
        note = 'Loops back - the institution that generates signal must also capture it'
    if str(note).strip():
        draw_centered_text(c, style, x, yy + 8.5, w, str(note), font=style.fonts.medium, size=9.33, color=pal.text)

def figure_context_flywheel_v4(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    default = [
        {"title": "Usage", "body": "in the digital twin"},
        {"title": "Signal", "body": "captured in ontology"},
        {"title": "Ontology", "body": "structures knowhow"},
        {"title": "Workflows", "body": "drive better usage"},
    ]
    figure_flywheel_v4(c, style, x, y, w, h, {**data, 'items': data.get('items') or default, 'note': data.get('note', '')})

FIGURE_BUILDERS['model_flywheel'] = figure_flywheel_v4
FIGURE_BUILDERS['context_flywheel'] = figure_context_flywheel_v4
FIGURE_BUILDERS['flywheel'] = figure_flywheel_v4

# v4.1 closer override: fixed Fig. 10 geometry with small vector icons and
# bolder section/card labels. Kept here as an override so older YAML remains valid.
def figure_control_layer_v5(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    base_w = 482.1
    base_h = 467.2
    ss = min(w / base_w, h / base_h)
    ss = max(0.82, min(1.08, ss))

    def X(v): return x + v * ss
    def Y(v): return y + v * ss
    def W(v): return v * ss
    def H(v): return v * ss

    def rect(rx, ry, rw, rh, stroke=None, fill=None, dash=None, lw=None):
        c.saveState()
        c.setFillColor(fill or pal.page)
        set_stroke(c, stroke or pal.text, lw or style.fig_stroke, dash)
        rect_top(c, style, X(rx), Y(ry), W(rw), H(rh), stroke=1, fill=1)
        c.setDash()
        c.restoreState()

    def t(rx, ry, text, font=None, size=8.2, color=None):
        draw_text(c, style, X(rx), Y(ry), text, font=font or style.fonts.medium, size=size * ss, color=color or pal.text)

    def tw(rx, ry, rw, text, font=None, size=7.0, leading=None, color=None):
        return draw_wrapped(c, style, X(rx), Y(ry), W(rw), text, font=font or style.fonts.medium, size=size * ss, leading=(leading or size * 1.24) * ss, color=color or pal.text)

    def poly(points, color=None, width=0.9):
        connector(c, style, [(X(px), Y(py)) for px, py in points], color=color or pal.text, width=width * ss, head=False)

    def icon(kind, rx, ry, size=8.0):
        s = size
        c.saveState()
        set_stroke(c, pal.text, 0.95 * ss)
        if kind == "shield":
            poly([(rx+s*.50, ry), (rx+s*.90, ry+s*.17), (rx+s*.83, ry+s*.68), (rx+s*.50, ry+s), (rx+s*.17, ry+s*.68), (rx+s*.10, ry+s*.17), (rx+s*.50, ry)], width=.95)
            poly([(rx+s*.50, ry+s*.28), (rx+s*.50, ry+s*.68)], width=.75)
        elif kind == "modular":
            poly([(rx+s*.18, ry+s*.18), (rx+s*.82, ry+s*.82)], width=.9)
            poly([(rx+s*.82, ry+s*.18), (rx+s*.18, ry+s*.82)], width=.9)
            c.circle(X(rx+s*.18), y_from_top(style, Y(ry+s*.18)), 1.3*ss, stroke=1, fill=0)
            c.circle(X(rx+s*.82), y_from_top(style, Y(ry+s*.82)), 1.3*ss, stroke=1, fill=0)
        elif kind == "cloud":
            poly([(rx+s*.10, ry+s*.62), (rx+s*.23, ry+s*.45), (rx+s*.38, ry+s*.39), (rx+s*.50, ry+s*.24), (rx+s*.70, ry+s*.34), (rx+s*.86, ry+s*.48), (rx+s*.92, ry+s*.70), (rx+s*.14, ry+s*.70), (rx+s*.10, ry+s*.62)], width=.85)
        elif kind == "database":
            c.ellipse(X(rx+s*.18), y_from_top(style, Y(ry+s*.30)), X(rx+s*.82), y_from_top(style, Y(ry+s*.05)), stroke=1, fill=0)
            line_top(c, style, X(rx+s*.18), Y(ry+s*.17), X(rx+s*.18), Y(ry+s*.78))
            line_top(c, style, X(rx+s*.82), Y(ry+s*.17), X(rx+s*.82), Y(ry+s*.78))
            c.ellipse(X(rx+s*.18), y_from_top(style, Y(ry+s*.88)), X(rx+s*.82), y_from_top(style, Y(ry+s*.62)), stroke=1, fill=0)
        elif kind == "globe":
            c.circle(X(rx+s*.50), y_from_top(style, Y(ry+s*.50)), s*.43*ss, stroke=1, fill=0)
            line_top(c, style, X(rx+s*.10), Y(ry+s*.50), X(rx+s*.90), Y(ry+s*.50))
            line_top(c, style, X(rx+s*.50), Y(ry+s*.10), X(rx+s*.50), Y(ry+s*.90))
        elif kind == "cube":
            poly([(rx+s*.50, ry+s*.08), (rx+s*.86, ry+s*.29), (rx+s*.86, ry+s*.71), (rx+s*.50, ry+s*.92), (rx+s*.14, ry+s*.71), (rx+s*.14, ry+s*.29), (rx+s*.50, ry+s*.08)], width=.8)
            poly([(rx+s*.14, ry+s*.29), (rx+s*.50, ry+s*.50), (rx+s*.86, ry+s*.29)], width=.65)
            poly([(rx+s*.50, ry+s*.50), (rx+s*.50, ry+s*.92)], width=.65)
        elif kind == "sliders":
            line_top(c, style, X(rx+s*.15), Y(ry+s*.28), X(rx+s*.85), Y(ry+s*.28)); c.circle(X(rx+s*.38), y_from_top(style, Y(ry+s*.28)), 1.2*ss, stroke=1, fill=0)
            line_top(c, style, X(rx+s*.15), Y(ry+s*.58), X(rx+s*.85), Y(ry+s*.58)); c.circle(X(rx+s*.66), y_from_top(style, Y(ry+s*.58)), 1.2*ss, stroke=1, fill=0)
        elif kind == "link":
            poly([(rx+s*.33, ry+s*.28), (rx+s*.18, ry+s*.44), (rx+s*.28, ry+s*.58), (rx+s*.48, ry+s*.40)], width=.8)
            poly([(rx+s*.52, ry+s*.60), (rx+s*.72, ry+s*.42), (rx+s*.82, ry+s*.56), (rx+s*.67, ry+s*.72)], width=.8)
        elif kind == "bolt":
            poly([(rx+s*.58, ry+s*.05), (rx+s*.25, ry+s*.55), (rx+s*.50, ry+s*.55), (rx+s*.38, ry+s*.95), (rx+s*.75, ry+s*.43), (rx+s*.52, ry+s*.43), (rx+s*.58, ry+s*.05)], width=.8)
        elif kind == "lock":
            rect(rx+s*.22, ry+s*.43, s*.56, s*.42, stroke=pal.text, fill=pal.page, lw=.75*ss)
            # simple shackle
            poly([(rx+s*.32, ry+s*.43), (rx+s*.32, ry+s*.27), (rx+s*.50, ry+s*.14), (rx+s*.68, ry+s*.27), (rx+s*.68, ry+s*.43)], width=.8)
        elif kind == "eye":
            poly([(rx+s*.08, ry+s*.50), (rx+s*.30, ry+s*.28), (rx+s*.50, ry+s*.22), (rx+s*.70, ry+s*.28), (rx+s*.92, ry+s*.50), (rx+s*.70, ry+s*.72), (rx+s*.50, ry+s*.78), (rx+s*.30, ry+s*.72), (rx+s*.08, ry+s*.50)], width=.8)
            c.circle(X(rx+s*.50), y_from_top(style, Y(ry+s*.50)), 1.2*ss, stroke=1, fill=0)
        elif kind == "branch":
            line_top(c, style, X(rx+s*.25), Y(ry+s*.18), X(rx+s*.25), Y(ry+s*.82))
            connector(c, style, [(X(rx+s*.25), Y(ry+s*.42)), (X(rx+s*.68), Y(ry+s*.25))], color=pal.text, width=.8*ss, head=False)
            connector(c, style, [(X(rx+s*.25), Y(ry+s*.62)), (X(rx+s*.68), Y(ry+s*.78))], color=pal.text, width=.8*ss, head=False)
            c.circle(X(rx+s*.25), y_from_top(style, Y(ry+s*.18)), 1.1*ss, stroke=1, fill=0)
            c.circle(X(rx+s*.68), y_from_top(style, Y(ry+s*.25)), 1.1*ss, stroke=1, fill=0)
            c.circle(X(rx+s*.68), y_from_top(style, Y(ry+s*.78)), 1.1*ss, stroke=1, fill=0)
        else:
            c.circle(X(rx+s*.50), y_from_top(style, Y(ry+s*.50)), s*.40*ss, stroke=1, fill=0)
        c.restoreState()

    # Control layer
    rect(0, 0, 482.1, 67.2, stroke=pal.text)
    icon("shield", 12.0, 13.0, 9.0)
    t(26.0, 12.3, "Control layer", font=style.fonts.semibold, size=10.4)
    t(26.0, 30.0, "Governs every workload across the stack", size=8.8)
    features = [("$", 40.4, "Model-agnostic routing"), ("lock", 154.0, "Granular permissions"), ("eye", 264.0, "Auditability & logs"), ("branch", 378.0, "Branching")]
    for kind, fx, label in features:
        if kind == "$":
            t(fx, 49.6, "$", font=style.fonts.semibold, size=9.5)
            t(fx + 12.0, 50.3, label, size=7.9)
        else:
            icon(kind, fx, 48.9, 8.0)
            t(fx + 12.0, 50.3, label, size=7.9)

    # Modular model layer
    my, mh = 80.4, 144.0
    rect(0, my, 482.1, mh, stroke=pal.blue)
    icon("modular", 12.0, my + 13.0, 8.2)
    t(26.0, my + 12.6, "Modular intelligence layer", font=style.fonts.semibold, size=10.4)
    t(26.0, my + 30.8, "Treated as a commodity, not a foundation", size=8.8)
    card_y, card_h = my + 61.0, 39.0
    card_w, gap = 105.0, 12.5
    card_xs = [12.6, 12.6 + card_w + gap, 12.6 + 2 * (card_w + gap), 12.6 + 3 * (card_w + gap)]
    model_labels = [("Model A", "External, under ZDR", False), ("Model B", "External, under ZDR", False), ("Model C", "External, under ZDR", False), ("Self-hosted", "Open-weight, owned", True)]
    for i, (title, body, dashed) in enumerate(model_labels):
        rect(card_xs[i], card_y, card_w, card_h, stroke=pal.blue, dash=style.dash if dashed else None)
        icon("database" if dashed else "cloud", card_xs[i] + 9.0, card_y + 9.6, 8.0)
        t(card_xs[i] + 21.0, card_y + 9.4, title, font=style.fonts.semibold, size=8.5)
        t(card_xs[i] + 9.0, card_y + 24.0, body, size=7.2)
    rect(12.6, my + 110.5, 456.9, 31.2, stroke=pal.blue)
    t(151.0, my + 123.0, "<->  Model liquidity - switch with minimal friction", font=style.fonts.semibold, size=8.5)

    # Flow notes
    t(101.0, 257.0, "↓ Context, prompts, permissions", size=8.4)
    t(252.0, 257.0, "↑ Outputs, knowhow, weights", size=8.4)

    # Ontology layer
    oy, oh = 262.0, 205.2
    rect(0, oy, 482.1, oh, stroke=pal.blue)
    icon("globe", 12.0, oy + 13.0, 8.5)
    t(26.0, oy + 13.0, "Owned knowledge layer • ontology", font=style.fonts.semibold, size=10.4)
    t(26.0, oy + 32.0, "A digital twin of your organization", size=8.8)
    top_cards_y = oy + 61.0
    small_w, small_h = 105.0, 49.0
    smalls = [("cube", "Objects", "Nouns\n- entities, events"), ("sliders", "Properties", "Attributes of\neach object"), ("link", "Links", "Relations between\nobjects"), ("bolt", "Actions", "Verbs\n- structured change")]
    for i, (ik, title, body) in enumerate(smalls):
        rx = card_xs[i]
        rect(rx, top_cards_y, small_w, small_h, stroke=pal.blue)
        icon(ik, rx + 9.0, top_cards_y + 10.3, 7.5)
        t(rx + 21.0, top_cards_y + 10.0, title, font=style.fonts.semibold, size=8.7)
        tw(rx + 9.0, top_cards_y + 27.0, small_w - 18.0, body, size=7.2, leading=8.1)
    wide_y, wide_h = oy + 123.0, 39.0
    wide_w = 222.4
    for rx, ik, title, body in [(12.6, "database", "Transactional data", "Records you already generate"), (246.0, "bolt", "Action data", "Captured only if structured")]:
        rect(rx, wide_y, wide_w, wide_h, stroke=pal.blue)
        icon(ik, rx + 9.0, wide_y + 10.3, 7.5)
        t(rx + 21.0, wide_y + 10.0, title, font=style.fonts.semibold, size=8.7)
        t(rx + 9.0, wide_y + 25.5, body, size=7.2)
    rect(12.6, oy + 174.0, 456.9, 31.5, stroke=pal.blue)
    t(138.5, oy + 187.0, "↻  Eval loop - captures usage, compounds it back into the ontology", font=style.fonts.semibold, size=8.3)

FIGURE_BUILDERS["control_layer"] = figure_control_layer_v5

# v4.2 override: Fig. 10 with vector pictograms rather than font-dependent symbols.
def figure_control_layer_v5(c: Canvas, style: Style, x: float, y: float, w: float, h: float, data: dict) -> None:
    pal = style.palette
    sx = w / 482.1
    ss = sx
    def X(v: float) -> float: return x + v * sx
    def Y(v: float) -> float: return y + v * sx
    def W(v: float) -> float: return v * sx
    def H(v: float) -> float: return v * sx
    def P(rx: float, ry: float): return X(rx), y_from_top(style, Y(ry))
    blue = pal.blue

    def icon(kind: str, rx: float, ry: float, s: float = 8.0) -> None:
        S = s * sx
        px, py = P(rx, ry)
        c.saveState()
        c.setFillColor(pal.text)
        set_stroke(c, pal.text, max(0.85 * sx, 0.5))
        if kind == 'shield':
            path = c.beginPath()
            path.moveTo(px + .5*S, py)
            path.lineTo(px + .9*S, py - .15*S)
            path.lineTo(px + .78*S, py - .68*S)
            path.lineTo(px + .5*S, py - .95*S)
            path.lineTo(px + .22*S, py - .68*S)
            path.lineTo(px + .1*S, py - .15*S)
            path.close(); c.drawPath(path, stroke=1, fill=0)
            c.line(px+.35*S, py-.48*S, px+.47*S, py-.62*S); c.line(px+.47*S, py-.62*S, px+.68*S, py-.34*S)
        elif kind == 'route':
            c.line(px+.1*S, py-.25*S, px+.85*S, py-.25*S); c.line(px+.7*S, py-.1*S, px+.85*S, py-.25*S); c.line(px+.7*S, py-.4*S, px+.85*S, py-.25*S)
            c.line(px+.85*S, py-.70*S, px+.1*S, py-.70*S); c.line(px+.25*S, py-.55*S, px+.1*S, py-.70*S); c.line(px+.25*S, py-.85*S, px+.1*S, py-.70*S)
        elif kind == 'lock':
            rect_top(c, style, X(rx+.18*s), Y(ry+.42*s), W(.64*s), H(.45*s), stroke=1, fill=0)
            c.arc(px+.25*S, py-.58*S, px+.75*S, py-.05*S, 0, 180)
        elif kind == 'eye':
            c.ellipse(px+.05*S, py-.75*S, px+.95*S, py-.20*S, stroke=1, fill=0)
            c.circle(px+.5*S, py-.48*S, .12*S, stroke=1, fill=1)
        elif kind == 'branch':
            c.line(px+.25*S, py-.12*S, px+.25*S, py-.85*S)
            c.line(px+.25*S, py-.38*S, px+.78*S, py-.18*S)
            c.line(px+.25*S, py-.62*S, px+.78*S, py-.82*S)
            for xx, yy in [(px+.25*S,py-.12*S),(px+.78*S,py-.18*S),(px+.78*S,py-.82*S)]: c.circle(xx, yy, .07*S, stroke=1, fill=1)
        elif kind == 'atom':
            c.ellipse(px+.12*S, py-.75*S, px+.88*S, py-.25*S, stroke=1, fill=0)
            c.ellipse(px+.25*S, py-.88*S, px+.75*S, py-.12*S, stroke=1, fill=0)
            c.line(px+.18*S, py-.82*S, px+.82*S, py-.18*S)
        elif kind == 'cloud':
            c.arc(px+.05*S, py-.65*S, px+.45*S, py-.25*S, 90, 180)
            c.arc(px+.32*S, py-.78*S, px+.78*S, py-.18*S, 40, 180)
            c.arc(px+.62*S, py-.68*S, px+.98*S, py-.30*S, 300, 160)
            c.line(px+.18*S, py-.65*S, px+.88*S, py-.65*S)
        elif kind == 'db':
            for off in (0.0, .28, .56): c.ellipse(px+.08*S, py-(off+.18)*S, px+.92*S, py-off*S, stroke=1, fill=0)
        elif kind == 'cube':
            c.rect(px+.2*S, py-.8*S, .55*S, .55*S, stroke=1, fill=0); c.line(px+.2*S,py-.25*S,px+.48*S,py-.08*S); c.line(px+.75*S,py-.25*S,px+.48*S,py-.08*S); c.line(px+.48*S,py-.08*S,px+.48*S,py-.62*S)
        elif kind == 'sliders':
            for yy, knob in [(py-.25*S, px+.35*S), (py-.50*S, px+.65*S), (py-.75*S, px+.45*S)]:
                c.line(px+.12*S, yy, px+.88*S, yy); c.circle(knob, yy, .07*S, stroke=1, fill=1)
        elif kind == 'link':
            c.roundRect(px+.08*S, py-.58*S, .48*S, .22*S, .1*S, stroke=1, fill=0); c.roundRect(px+.44*S, py-.40*S, .48*S, .22*S, .1*S, stroke=1, fill=0)
        elif kind == 'bolt':
            path=c.beginPath(); path.moveTo(px+.58*S,py-.05*S); path.lineTo(px+.25*S,py-.55*S); path.lineTo(px+.52*S,py-.55*S); path.lineTo(px+.38*S,py-.95*S); path.lineTo(px+.78*S,py-.42*S); path.lineTo(px+.53*S,py-.42*S); path.close(); c.drawPath(path, stroke=1, fill=0)
        elif kind == 'loop':
            c.arc(px+.15*S, py-.82*S, px+.85*S, py-.18*S, 30, 260); c.line(px+.75*S,py-.2*S,px+.87*S,py-.27*S); c.line(px+.75*S,py-.2*S,px+.77*S,py-.36*S)
        c.restoreState()

    # Top control layer.
    box(c, style, X(0), Y(0), W(482.1), H(67.2), '', '', fill=pal.page, stroke=pal.text, pad=0)
    icon('shield', 13.0, 16.0, 8.0)
    draw_text(c, style, X(26), Y(14.2), 'Control layer', font=style.fonts.semibold, size=10.1*ss, color=pal.text)
    draw_text(c, style, X(26), Y(34.2), 'Governs every workload across the stack', font=style.fonts.medium, size=8.55*ss, color=pal.text)
    controls=[('route','Model-agnostic routing', 32),('lock','Granular permissions', 148),('eye','Auditability & logs', 258),('branch','Branching', 348)]
    for k, txt, rx in controls:
        icon(k, rx, 51.5, 7.2)
        draw_text(c, style, X(rx+10), Y(51.1), txt, font=style.fonts.medium, size=7.55*ss, color=pal.text)

    # Modular intelligence layer.
    my, mh = 80.4, 144.0
    box(c, style, X(0), Y(my), W(482.1), H(mh), '', '', fill=pal.page, stroke=blue, pad=0)
    icon('atom', 13.0, my+16.6, 8.0)
    draw_text(c, style, X(26), Y(my+16.6), 'Modular intelligence layer', font=style.fonts.semibold, size=10.1*ss, color=pal.text)
    draw_text(c, style, X(26), Y(my+36.6), 'Treated as a commodity, not a foundation', font=style.fonts.medium, size=8.7*ss, color=pal.text)
    card_y = my + 49.2
    card_w, card_h = 105.6, 38.4
    card_xs = [12.6, 129.9, 247.2, 364.5]
    models = [('cloud','Model A','External, under ZDR', False),('cloud','Model B','External, under ZDR', False),('cloud','Model C','External, under ZDR', False),('db','Self-hosted','Open-weight, owned', True)]
    for i,(ik,t,b,dashed) in enumerate(models):
        box(c, style, X(card_xs[i]), Y(card_y), W(card_w), H(card_h), '', '', fill=pal.page, stroke=blue, dashed=dashed, pad=0)
        icon(ik, card_xs[i]+8.0, card_y+13.8, 7.0)
        draw_text(c, style, X(card_xs[i]+18.5), Y(card_y+12.8), t, font=style.fonts.semibold, size=8.15*ss, color=pal.text)
        draw_text(c, style, X(card_xs[i]+8.0), Y(card_y+27.0), b, font=style.fonts.medium, size=6.85*ss, color=pal.text)
    box(c, style, X(12.6), Y(my+100.2), W(456.9), H(31.2), '', '', fill=pal.page, stroke=blue, pad=0)
    icon('route', 151.0, my+112.0, 7.0)
    draw_text(c, style, X(165.0), Y(my+111.2), 'Model liquidity - switch with minimal friction', font=style.fonts.semibold, size=8.2*ss, color=pal.text)

    draw_text(c, style, X(117), Y(246.0), 'Context, prompts, permissions', font=style.fonts.semibold, size=8.1*ss, color=pal.text)
    arrow(c, style, X(107), Y(244.0), X(107), Y(254.0), width=0.6, color=pal.text)
    draw_text(c, style, X(253), Y(246.0), 'Outputs, knowhow, weights', font=style.fonts.semibold, size=8.1*ss, color=pal.text)
    arrow(c, style, X(245), Y(254.0), X(245), Y(244.0), width=0.6, color=pal.text)

    # Owned knowledge / ontology layer.
    oy, oh = 262.0, 205.2
    box(c, style, X(0), Y(oy), W(482.1), H(oh), '', '', fill=pal.page, stroke=blue, pad=0)
    icon('atom', 13.0, oy+16.5, 8.0)
    draw_text(c, style, X(26), Y(oy+16.5), 'Owned knowledge layer • ontology', font=style.fonts.semibold, size=10.1*ss, color=pal.text)
    draw_text(c, style, X(26), Y(oy+36.5), 'A digital twin of your organization', font=style.fonts.medium, size=8.8*ss, color=pal.text)
    objs=[('cube','Objects','Nouns\n- entities, events'),('sliders','Properties','Attributes of\neach object'),('link','Links','Relations between\nobjects'),('bolt','Actions','Verbs\n- structured change')]
    for i,(ik,t,b) in enumerate(objs):
        box(c, style, X(card_xs[i]), Y(oy+49.2), W(card_w), H(48.6), '', '', fill=pal.page, stroke=blue, pad=0)
        icon(ik, card_xs[i]+8.0, oy+62.0, 7.2)
        draw_text(c, style, X(card_xs[i]+18.5), Y(oy+61.0), t, font=style.fonts.semibold, size=8.25*ss, color=pal.text)
        draw_wrapped(c, style, X(card_xs[i]+8.0), Y(oy+76.0), W(card_w-16), b, font=style.fonts.medium, size=7.0*ss, leading=8.0*ss)
    half_w = 222.6
    for ik, rx, t, b in [('db',12.6,'Transactional data','Records you already generate'),('branch',247.2,'Action data','Captured only if structured')]:
        box(c, style, X(rx), Y(oy+110.4), W(half_w), H(39.0), '', '', fill=pal.page, stroke=blue, pad=0)
        icon(ik, rx+8.0, oy+123.5, 7.2)
        draw_text(c, style, X(rx+18.5), Y(oy+122.0), t, font=style.fonts.semibold, size=8.1*ss, color=pal.text)
        draw_text(c, style, X(rx+8.0), Y(oy+136.5), b, font=style.fonts.medium, size=6.8*ss, color=pal.text)
    box(c, style, X(12.6), Y(oy+161.4), W(456.9), H(31.2), '', '', fill=pal.page, stroke=blue, pad=0)
    icon('loop', 151.0, oy+173.0, 7.0)
    draw_text(c, style, X(165.0), Y(oy+172.2), 'Eval loop - captures usage, compounds it back into the ontology', font=style.fonts.semibold, size=8.0*ss, color=pal.text)

FIGURE_BUILDERS['control_layer'] = figure_control_layer_v5
