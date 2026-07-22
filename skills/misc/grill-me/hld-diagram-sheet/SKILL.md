---
name: hld-diagram-sheet
description: >-
  Create one-page high-level design diagrams in the soft rounded architecture
  style shown by the reference: pale blueprint background, mono text,
  blue-gray cards, arrows, data stores, stream bus, small vector icons, and
  side labels.
metadata:
  version: "1.0.0"
---

# HLD Diagram Sheet Skill

Use this skill when the user wants a high-level architecture/design document that looks like a polished hand-laid system diagram rather than a generic flowchart.

The output should be a single-page diagram, usually SVG first, then PNG or PDF. Use `scripts/render_hld.py` with a YAML spec. Do not use Mermaid, Graphviz, or auto-layout for the final artifact; this style depends on fixed visual placement.

## Visual style

Canvas:
- Default size: `1080 x 779`.
- Background: very pale blue-gray, with faint blueprint/perspective linework near the edges.
- Title: centered, uppercase, heavy sans-serif, near the top edge.

Boxes:
- Rounded rectangles with light blue fill, blue-gray stroke, and soft shadow.
- Text is centered and set in a monospaced/typewriter face.
- Primary service boxes are medium-sized cards.
- Data stores use the same card treatment, plus a small cylinder icon.
- Derived/eventual stores can use the same card treatment but should be clearly labeled as derived/eventual.
- State-changing paths should land on the system of truth first.

Arrows:
- Main arrows are muted blue-gray, 2 px, with triangular heads.
- Eventual/derived fan-out paths are muted green.
- Prefer orthogonal paths when a connection crosses rows.
- Put short labels near the line, not inside arrows.

Special elements:
- Stream/change-log bus: long rounded capsule with a Kafka-style node icon on the left and a segmented pipe/cylinder on the right.
- Small icons should be vector shapes, not external image files. Use them sparingly: key, clock, route, calendar, clipboard, database, Redis stack, search, alarm, phone, bell, document, fan-out, sync, chart.
- Keep labels terse: `(SYNC)`, `CDC`, `claim`, `fan-out\n(delta)`, `GET ?range\n(1 hop)`.

## Workflow

1. Draft the system as rows:
   - clients and gateway
   - write/read services
   - systems of truth
   - change stream
   - indexes, schedulers, workers, derived stores
   - external wake/read labels
2. Create a YAML file based on `examples/calendar_booking.yaml`.
3. Run:

```bash
python scripts/render_hld.py examples/calendar_booking.yaml --out outputs/calendar_booking --format all
```

4. Open the PNG or SVG. Check for:
   - clipped text
   - crowded labels
   - arrows touching text
   - icons covering words
   - unclear source of truth vs derived storage
5. Adjust `x`, `y`, `w`, and `h` in the YAML. Re-render.

## YAML structure

Minimum:

```yaml
canvas:
  width: 1080
  height: 779
  title: "SYSTEM HIGH-LEVEL DESIGN (HLD)"

nodes:
  - id: api
    kind: box
    x: 320
    y: 47
    w: 597
    h: 53
    text: "API Gateway - authN->N, rate-limit, route"
  - id: service
    kind: box
    x: 420
    y: 148
    w: 200
    h: 79
    text: "Application Service"

edges:
  - from: api.bottom
    to: service.top

labels:
  - text: "(SYNC)"
    x: 230
    y: 260
```

Node kinds:
- `box`
- `green_box`
- `stream`

Edge endpoints:
- `node.top`, `node.bottom`, `node.left`, `node.right`, `node.center`
- absolute points like `[420, 510]`

Icons can be attached globally:

```yaml
icons:
  - name: db
    x: 306
    y: 352
    scale: 0.82
```

Supported icon names: `devices`, `key`, `clock`, `route`, `calendar`, `calendar_pen`, `calendar_check`, `clipboard`, `map`, `db`, `redis`, `kafka`, `search`, `alarm`, `phone_bell`, `doc`, `fanout`, `sync`, `chart`, `updown`.

## Layout rules

Use exact positions. The renderer intentionally avoids auto-layout, because auto-layout makes this style look generic.

Good spacing targets:
- 18-28 px between vertical rows.
- 16-28 px between cards in a row.
- 8-16 px between a label and its arrow.
- Keep stream bus centered and wide.
- Use blue arrows for authoritative writes and change-stream flow.
- Use green arrows for derived availability/index updates.

## Deliverables

For a user-facing result, provide at least:
- source YAML
- SVG
- PNG preview
- PDF when they need a printable page

Use the script's `--guides` option only while tuning. Do not deliver guide overlays unless requested.
