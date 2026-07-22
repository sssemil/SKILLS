---
name: institutional-brief-style-pdf
description: Create fixed-layout institutional brief PDFs with cream page fields, black/blue typography, Roman-numeral side rails, alternating footers, and dense linework diagrams calibrated to the supplied reference.
metadata:
  version: "1.3.0"
---

# Institutional Brief Style PDF Skill

Use this skill when the user wants a sober institutional strategy brief similar to the supplied reference: letter-size portrait pages, warm off-white page field, large black/blue cover type, Roman-numeral side headings, compact body copy, figure captions, and architecture/process diagrams drawn with thin boxes, arrows, dashed boundaries, and pale blue fills.

## Reference-calibrated visual tokens

- Page size: US Letter, 612 x 792 pt.
- Inset page field: x=11.9906, y=17.9879, w=588.0188, h=756.0242.
- Field fill: `#FFFFF8`; paper outside field: white.
- Primary text: `#212121`.
- Accent blue: `#5DACED`.
- Pale blue fill: `#E9F3F6`; pale rule: `#D9EEF8`.
- Orange risk accent: `#E87536`; orange fill: `#F9ECDC`.
- Body copy: 9.3336 pt with 13.0668 pt leading.
- Figure captions: 10.267 pt semibold; blue `Fig. N` followed by black title.
- Side heading: 16.8005 pt blue Roman numeral plus 16.8005 pt black title.
- Odd-page rail/body: x=70.8 / x=237.2.
- Even-page rail/body: x=58.7 / x=224.4.
- Figure stroke: about 0.6067 pt.
- Motif stroke: about 1.8667 pt.
- Dashed boundaries: 1.8667 / 0.9333 pt dash pattern.
- Footer baseline: y=722.7.
- Closing sequence: two full-page chevron pattern pages followed by a centered placeholder wordmark page.
- v4.1 calibration adds cover-width scaling, section-divider line breaks, section-surface hatching, inline rich body text helpers, ZDR architecture pictograms/risk cards, and a compact control-layer coordinate grid.

The reference embeds AllianceNo.2 Medium, SemiBold, and Bold. Do not bundle or share those fonts. The scripts auto-detect Noto Sans Display as the closest freely installed substitute on this runtime, then Lato, then fall back to Helvetica. Licensed font paths can be supplied under `fonts:`.

## Brand and legal handling

The package does not include the Palantir logo or any proprietary font files. The included wordmark is a generic vector placeholder. Replace it only with assets the user is allowed to use.

## Workflow

1. Start from `examples/example_brief.yaml`.
2. Build the PDF:

```bash
python scripts/build_brief.py examples/example_brief.yaml /mnt/data/output.pdf
```

3. Render for QA:

```bash
python scripts/verify_render.py /mnt/data/output.pdf --out-dir /mnt/data/output_renders --dpi 144
```

4. Inspect the PNGs. Adjust `caption_y`, `figure_y`, `height`, `body_after_y`, and paragraph length until text does not collide with figures or footers.

## Page types

### Cover

```yaml
- type: cover
  brand: YourCo
  title_y: 195
  title_lines:
    - text: Institutional
      color: text
    - text: Sovereignty
      color: text
    - text: in the
      color: blue
    - text: Age of AI
      color: blue
  subtitle: |-
    15 steps that every government
    and company can take to compound
    their alpha in the age of AI
```

### Pattern page

```yaml
- type: pattern
  page_mark: "02"
```

The pattern page uses the reference’s clipped family of kinked diagonal strokes.

### Contents page

```yaml
- type: toc
  sections:
    - title: Foundations
      items:
        - number: I.
          title: Establish clean data boundaries.
```

The contents renderer draws the thin section and row rules used in the reference.

### Section divider

```yaml
- type: section_divider
  title: Foundations
```

The divider uses the three calibrated diamond polylines from the reference section pages.

### Step page

```yaml
- type: step
  number: I.
  title: Establish clean data boundaries.
  body:
    - A compact paragraph.
    - type: list
      items:
        - First point
        - Second point
      rule: true
  figure:
    type: architecture_layers
    fig_no: 3
    caption: Architecture Layers
    caption_y: 385
    y: 412
    height: 285
```

### Full-figure page

```yaml
- type: figure_full
  fig_no: 2
  caption: AI Decision Tree
  x: 69.8
  y: 66.6
  figure_y: 88.0
  w: 483.2
  h: 604.8
  figure:
    type: decision_tree
```

## Figure types

Use these values under `figure.type`:

- `zdr_architecture` - side-by-side trusted/untrusted request flow with risk cards.
- `decision_tree` - stacked decision boxes with hold/no-go branches and eight end states.
- `architecture_layers` - three stacked layers with nested access/tier boxes.
- `tribal_ownership` - provider path vs enterprise path.
- `agent_harness` - production workload into evaluation loop and outcomes.
- `model_flywheel` - four-box feedback loop.
- `context_flywheel` - four-box context/ontology loop.
- `assurance_levels` - four assurance cards from structural to contractual.
- `on_prem_architecture` - stacked on-prem perimeter architecture.
- `attestation` - four-step confidential compute attestation flow.
- `control_layer` - control layer, modular model layer, and ontology layer.
- `permissions` - central dataset matrix with human/agent actors.
- `audit_logs` - five-stage trace, append-only stream, and audit actions.
- `security_forge` - circular adaptive security loop.
- `branching` - agent sandbox, branch grid, validate path, and production timeline.

## Placement rules

- Use explicit `caption_y` and `figure_y` for dense pages.
- Keep charts between x=58.7/69.8 and x about 553.
- Keep bottom content above y=700; the footer sits near y=722.7.
- Dense cards need short labels. Use manual line breaks in YAML where needed.
- Prefer ASCII hyphens and arrows (`->`) unless the licensed font handles the glyphs cleanly.

## Scripts

- `scripts/build_brief.py` - CLI entrypoint.
- `scripts/compare_to_reference.py` - render-and-score comparison against a reference PDF.
- `scripts/verify_render.py` - renders generated PDFs to PNGs for visual QA.
- `scripts/palantir_brief/style.py` - page, color, font, and footer tokens.
- `scripts/palantir_brief/primitives.py` - boxes, captions, arrows, wrapping, wordmark, footers.
- `scripts/palantir_brief/figures.py` - chart builders.
- `scripts/palantir_brief/renderer.py` - page-type renderer.
