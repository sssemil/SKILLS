---
name: factory-design
description: Apply the Factory.ai visual design system to any UI. Use whenever the user asks for Factory-style, "factory.ai look", agent-native developer tooling aesthetics, or is building landing pages, dashboards, marketing sections, CLI install boxes, terminal mockups, or developer-tool UIs that should feel like Factory.ai / Vercel / Linear-adjacent dev brands. Triggers on phrases like "factory design", "factory style", "droid look", "make it look like factory.ai", or any task in a project using the color tokens `--color-accent-100`, `--color-base-*`, Geist Mono + orange `#ef6f2e`. Produces exact class strings, CSS variables, component shapes, motion, and enforcement rules — never guesses values.
---

# Factory Design System

A rigorous, pixel-level reproduction of the Factory.ai aesthetic. This skill defines **every measurement, variable, class combination, and animation** that must be used. When building UI in this system, copy these values verbatim — do not round, re-interpret, or "modernize" them.

## Core Philosophy

Factory's look is **"agent-native developer tooling"**. Five non-negotiable rules define the vibe:

1. **Monospace is the voice.** `Geist Mono` is the default typeface for ~90% of text (nav, labels, body paragraphs, buttons, badges, code). `Geist Sans` appears *only* for display/marketing headings and section titles — never for UI chrome.
2. **Dark-first, tokenized.** Always author in dark mode first. Never hardcode colors — always `var(--color-...)`. Light theme is the mirror, not a rewrite.
3. **Micro-typography.** Tracking is tight and negative almost everywhere (`tracking-[-0.015rem]`, `tracking-[-0.0175rem]`, `tracking-[-0.04em]` on headlines). Font sizes are specific pixels (`text-[12px]`, `text-[14px]`, `text-[60px]`), not Tailwind presets.
4. **Dashed borders and diagonal stripes.** Containers use `border-dashed border-[var(--color-base-700)]`. Buttons and hoverable cards reveal a 45° conveyor-belt stripe pattern on hover.
5. **Motion is earned.** Three signature animations: **character reveal** on the hero headline, **scramble** on section badges, **typewriter** inside the CLI install box. Everything else is `duration-150` / `duration-200` color and opacity transitions.

If a design decision isn't covered below, err toward: **mono, dashed, 8-12px radius, var(--color-base-XXX), tight tracking, stripe on hover**.

---

## 1. Design Tokens — copy these exactly

All tokens live in `app/globals.css` under `:root`, `html / [data-theme="dark"]`, and `[data-theme="light"]`. Never inline a hex/oklch. Reference via `var(--token-name)`.

### 1.1 Accent (orange — shared across themes)

```css
--color-accent-100: #ef6f2e;   /* primary orange — links, hero word, dots, "Copied" check */
--color-accent-200: #ee6018;   /* hover/active */
--color-accent-300: #d15010;   /* badge numerals, emphatic accents */
```

Usage rules:
- **Exactly one** accent word per headline. Example: `<span class="text-[var(--color-accent-100)]">Next-Gen</span> Platform`.
- Accent dot (`w-2 h-2 rounded-full bg-[var(--color-accent-100)]`) precedes "Trusted by" / section intros.
- `::selection` is always accent-100 on dark-primary.
- Nav links hover to `text-[var(--color-accent-100)]` via `transition-colors duration-200`.

### 1.2 Base Scale — inverts between themes

The `base` scale runs 100 (near-foreground) → 1000 (near-background). **Dark theme**: 100 is almost white, 1000 is near-black. **Light theme**: inverted. This means every component works in both themes without conditionals — you just reference the scale.

```css
/* DARK (default) */
--background: #020202;        /* page bg */
--foreground: #eee;           /* primary text */
--color-base-100:  #d6d3d2;   /* near-foreground */
--color-base-200:  #ccc9c7;
--color-base-300:  #b8b3b0;
--color-base-400:  #a49d9a;   /* nav links, subheading body text */
--color-base-500:  #8a8380;   /* muted body text, "Trusted by" copy, placeholders */
--color-base-600:  #5c5855;   /* terminal dots, social link separators */
--color-base-700:  #4d4947;   /* dashed borders, dropdown borders, theme-toggle border */
--color-base-800:  #3d3a39;   /* solid borders on cards, tab dividers */
--color-base-900:  #2e2c2b;   /* card backgrounds (CTA block, footer, terminal mockup) */
--color-base-1000: #1f1d1c;   /* deepest fill (command box inside terminal) */

/* LIGHT */
--background: #eee;
--foreground: #020202;
--color-base-100:  #1f1d1c;   /* (inverted) */
--color-base-1000: #d6d3d2;
/* ...the whole scale mirrors */
```

**Semantic aliases** (prefer these when the role is semantic, not shade-specific):

```css
--color-dark-base-primary:   #020202 / #eee;   /* background surface */
--color-dark-base-secondary: #101010 / #fafafa;
--color-light-base-primary:  #eee    / #020202; /* readable text surface */
--color-light-base-secondary:#fafafa / #101010;
```

**Button-specific tokens** (never hardcode button colors):

```css
/* dark */
--btn-primary-bg:       #1f1d1c;   --btn-primary-text:     #fafafa;
--btn-secondary-bg:     #fafafa;   --btn-secondary-text:   #1f1d1c;
--btn-secondary-border: var(--color-base-700);

/* light (inverted + transparent secondary border) */
--btn-primary-bg:       #eeeeee;   --btn-primary-text:     #101010;
--btn-secondary-bg:     #101010;   --btn-secondary-text:   #eeeeee;
--btn-secondary-border: transparent;
```

### 1.3 Typography

```css
--font-sans: var(--font-geist-sans), system-ui, sans-serif;
--font-mono: var(--font-geist-mono), monospace;
```

Load both Geists from `next/font/google` in `app/layout.tsx`:

```tsx
import { Geist, Geist_Mono } from "next/font/google";
const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });
```

Body default: `font-family: var(--font-sans)` + `antialiased`. All UI chrome explicitly overrides with `font-mono`.

### 1.4 Radius, Motion, Spacing

```css
--spacing: 0.25rem;  /* 4px base unit */

--radius-xs:  0.125rem;  /* 2px */
--radius-sm:  0.25rem;   /* 4px — buttons */
--radius-md:  0.375rem;  /* 6px */
--radius-lg:  0.5rem;    /* 8px — cards, CLI box, terminal mockup, CTA */
--radius-xl:  0.75rem;   /* 12px — product dropdown panel */
--radius-2xl: 1rem;
--radius-3xl: 1.5rem;

--ease-reveal:  cubic-bezier(0.645, 0.045, 0.355, 1);   /* char reveal, fade-in-up */
--ease-default: cubic-bezier(0.4,   0,     0.2,   1);
--duration-fast:   0.15s;   /* transition-colors default */
--duration-normal: 0.3s;
--duration-slow:   0.5s;
```

---

## 2. Layout Grid — the 4/12 column rule

Every `<section>` and the header use this container:

```tsx
<div className="mx-auto grid grid-cols-4 lg:grid-cols-12 gap-x-4 lg:gap-x-6 px-4 lg:px-9">
```

- Mobile: **4 columns**, `px-4` (16px), `gap-x-4`.
- Desktop (`lg` ≥ 1024px): **12 columns**, `px-9` (36px), `gap-x-6`.
- Never `container` or `max-w-7xl`. Horizontal centering comes from `mx-auto` + the grid itself.

**Column allocations** (memorize these):

| Block | Mobile | Desktop |
|---|---|---|
| Hero left (copy + CLI box) | `col-span-4` | `col-span-6` |
| Hero right (graphic) | hidden | `col-span-6` |
| Product copy | `col-span-4` | `col-span-5` |
| Product mockup | `col-span-4 mt-8` | `col-span-7 mt-0` |
| CLI install box | max-width `max-w-[480px]` inside col | same |
| CTA card | `max-w-[520px]` | `max-w-[520px]` |

**Vertical rhythm:**
- Hero margin: `mt-4 lg:mt-20 mb-20 lg:mb-30`.
- Section padding: `py-20 lg:py-30`.
- Header padding: `py-5`.
- Footer outer: `mx-4 lg:mx-9 mb-4 lg:mb-9` (the footer itself is a rounded card, not a full-bleed bar).
- Stack gaps inside columns: `gap-y-6 lg:gap-y-8`.

---

## 3. Typography Scale — exact sizes per role

**Rule: always use `text-[Npx]` bracket values** for UI chrome. Tailwind's `text-sm` / `text-base` are only acceptable in the `<Text>` / `<Heading>` CVA variants.

### 3.1 Hero headline (marketing display)

```tsx
<h1
  ref={heroTitleRef}
  className="text-[40px] lg:text-[60px] 2xl:text-[72px]
             font-mono font-normal leading-[100%] tracking-[-0.04em]"
>
  <span className="text-[var(--color-accent-100)]">Next-Gen</span>
  <span className="text-[var(--foreground)]"> Platform</span>
  <br />
  <span className="text-[var(--foreground)]">for Developers</span>
</h1>
```

Hero headline is **font-mono, font-normal** (not bold) with `leading-[100%]`. `useCharReveal(heroTitleRef)` splits it into char spans and fades them in on intersection.

### 3.2 Section headings (h2)

```tsx
<h2 className="text-[32px] lg:text-[48px] font-normal leading-[100%]
               tracking-[-0.04em] text-[var(--foreground)]">
  Droids meet you<br />wherever you work.
</h2>
```

Section h2 uses default sans (not mono), `font-normal`, forced line breaks with `<br />`.

### 3.3 CTA headings

```tsx
<h2 className="text-[28px] lg:text-[36px] font-normal leading-[110%]
               tracking-[-0.02em]">
```

### 3.4 Subheadings / body (mono)

Paragraph body is `font-mono text-[14px] lg:text-[16px] leading-[140%] tracking-[-0.0175rem]` colored by role:

| Role | Class |
|---|---|
| Primary body | `text-[var(--color-base-400)]` |
| Muted body | `text-[var(--color-base-500)]` |

Always use `<br />` to enforce specific line breaks in marketing copy — never let the browser wrap.

### 3.5 Labels (micro-UI)

```tsx
className="font-mono text-[12px] uppercase tracking-[-0.015rem]
           text-[var(--color-base-400)]
           hover:text-[var(--foreground)]
           transition-colors duration-200"
```

Use for: nav links, tab labels, section eyebrow labels, terminal window titles ("01 — TERMINAL / IDE" at `text-[12px]`).

### 3.6 Tab pills inside CLI box

```tsx
className="px-2 py-0.5 rounded text-[11px] font-mono
           uppercase tracking-[-0.01rem] transition-colors"
/* active */  "border border-[var(--color-base-800)] bg-[var(--color-base-1000)] text-[var(--foreground)]"
/* inactive */ "border border-transparent text-[var(--color-base-500)] hover:text-[var(--foreground)]"
```

### 3.7 Code / command strings

```tsx
<code className="font-mono text-[14px] text-[var(--foreground)]">...</code>
```

Prefix with an accent caret: `<span className="text-[var(--color-accent-100)] font-mono text-[14px]">&gt;</span>`.

### 3.8 `<Heading>` and `<Text>` CVA variants (for reusable cases)

`components/ui/heading.tsx` exposes seven variants — use them when a **reusable heading** is appropriate:

| variant | sizes | weight |
|---|---|---|
| `display` | 40 / 56 / 72 | semibold |
| `heading-1` | 30 / 36 / 48 | semibold |
| `heading-2` | 24 / 28 / 36 | semibold |
| `subheading-1` | 18 / 20 / 24 | medium |
| `subheading-2` | 16 / 18 / 20 | medium |
| `subheading-3` | 14 / 16 | medium |
| `metrics` | 48 / 64 / 80 | bold |

`color` prop: `"default" | "secondary" | "muted" | "accent"`.

`<Text>` variants: `paragraph` / `paragraph-lg` / `paragraph-sm` / `label-1` / `label-1-mono` / `label-2` / `label-2-mono` / `caption` / `code`.

**Note the conflict**: `display` and `heading-1` in CVA use `font-sans font-semibold`. The **hero in `page.tsx` overrides** to `font-mono font-normal` because the marketing hero has its own look. When in doubt for the home hero: **mono, normal, tracking -0.04em**. For dashboard/product page headings: use the CVA `display`/`heading-1` directly.

---

## 4. Components — exact shapes

### 4.1 `<Button>` (`components/ui/button.tsx`)

Built with `cva` + `forwardRef` + optional Radix `Slot` (`asChild`).

**Base classes (always applied):**
```
group relative inline-flex w-max cursor-pointer items-center justify-center
border font-mono uppercase transition-colors duration-150
disabled:cursor-not-allowed disabled:opacity-50
[&_*]:transition-colors [&_*]:duration-150
focus-visible:outline focus-visible:outline-offset-4
```

**Variants (exact classes):**

| variant | classes |
|---|---|
| `primary` (default) | `bg-[var(--btn-primary-bg)] text-[var(--btn-primary-text)] border-[var(--color-base-700)] hover:opacity-80 overflow-hidden rounded-[4px]` |
| `secondary` | `bg-[var(--btn-secondary-bg)] text-[var(--btn-secondary-text)] border-transparent hover:opacity-80 overflow-hidden rounded-[4px]` |
| `ghost` | `bg-transparent text-[var(--foreground)] hover:bg-[var(--color-base-900)] hover:text-[var(--color-accent-100)]` |
| `link` | `bg-transparent text-[var(--foreground)] hover:text-[var(--color-accent-100)] underline-offset-4 hover:underline` |
| `outline` | `border-[var(--color-base-700)] text-[var(--foreground)] hover:border-[var(--color-accent-100)] hover:text-[var(--color-accent-100)]` |

**Sizes (exact heights):**

| size | classes |
|---|---|
| `sm` | `h-[25px] px-3 text-[12px] tracking-[-0.015rem]` |
| `default` | `h-[31px] px-[14px] text-[12px] tracking-[-0.015rem]` |
| `lg` | `h-[40px] px-6 text-[14px] tracking-[-0.0175rem]` |
| `icon` | `h-[31px] w-[31px] p-0` |

**The stripe-hover overlay (required for primary/secondary):**

Every primary/secondary button renders an absolute overlay that contains an animated 45° stripe pattern, visible only on hover / focus-visible. Copy this verbatim inside the button body:

```tsx
{showPattern && isPrimaryOrSecondary && (
  <div className="pointer-events-none absolute inset-0 opacity-0 will-change-transform
                  group-hover:opacity-100 group-focus-visible:opacity-100
                  transition-opacity duration-100 delay-75">
    <div
      className="btn-stripe-pattern absolute inset-0"
      style={{ "--lines-color": linesColor } as React.CSSProperties}
    />
  </div>
)}
<span className="relative z-10 flex items-center gap-1">{children}</span>
```

`linesColor` rule:
- `variant === "secondary"` → `var(--color-base-600)` (darker lines on light bg)
- else → `var(--color-base-500)`

The `.btn-stripe-pattern` CSS lives in `globals.css` and **must not be modified**:

```css
.btn-stripe-pattern {
  background-image: repeating-linear-gradient(
    45deg,
    transparent 0px,  transparent 2px,
    var(--lines-color, var(--color-base-400)) 2px,
    var(--lines-color, var(--color-base-400)) 3px,
    transparent 3px,  transparent 5px
  );
  background-size: 7.07px 7.07px;
  animation: slidePattern 2s linear infinite;
}
@keyframes slidePattern {
  0%   { background-position: 0 0; }
  100% { background-position: 28.28px -28.28px; }
}
```

Children inside a button that should animate (e.g. arrow icons) go after the text with `gap-1` spacing: `<Button>Learn More <ArrowIcon className="w-3 h-3" /></Button>`.

### 4.2 `<Badge>` (`components/ui/badge.tsx`)

An all-caps mono label with either (a) an accent **dot** or (b) a numbered prefix. Accompanied by a scramble-text animation on the label.

```tsx
<Badge text="PLATFORM" />              // dot + scrambled text
<Badge text="PRODUCT" variant="numbered" number={1} />
```

**Base:**
```
inline-flex items-center uppercase font-mono text-xs tracking-wider
```

**Variants:**
- `default`: `gap-3 text-[var(--color-base-500)]` + prefixed by `<span class="w-2 h-2 rounded-full bg-[var(--color-accent-300)]">`.
- `numbered`: `gap-2 text-[var(--color-base-500)]` + prefixed by the number rendered in `text-[var(--color-accent-300)] font-semibold`.
- `off`: identical to default but typically used on inactive states (still dot-prefixed).

Use one Badge at the top of every major section (`PLATFORM`, `PRODUCT`, `FOOTER`, etc.). Always uppercase, ≤ 12 characters.

### 4.3 CLI Install Box (hero right of copy)

```tsx
<div className="flex flex-col max-w-[480px] rounded-lg
                border border-[var(--color-base-800)] bg-[var(--background)]
                overflow-hidden">
  {/* tabs row */}
  <div className="flex gap-1 px-3 py-2">
    <button className={tabClass(active)}>macOS / Linux</button>
    <button className={tabClass(active)}>Windows</button>
  </div>
  <div className="border-t border-[var(--color-base-800)]" />
  {/* command row */}
  <div className="flex items-center justify-between px-4 py-3 gap-4">
    <div className="flex items-center gap-2 min-w-0">
      <span className="text-[var(--color-accent-100)] font-mono text-[14px]">&gt;</span>
      <code className="font-mono text-[14px] text-[var(--foreground)]">
        {displayedText}
        {isTyping && (
          <span className="inline-block w-[8px] h-[16px] bg-[var(--foreground)]
                           ml-[1px] align-middle translate-y-[1px]" />
        )}
      </code>
    </div>
    <button onClick={handleCopy}
      className="flex-shrink-0 p-1.5 rounded border border-transparent
                 hover:border-[var(--color-base-700)] transition-all">
      {copied ? <CheckIcon className="w-4 h-4 text-[var(--color-accent-100)]" />
              : <CopyIcon  className="w-4 h-4 text-[var(--color-base-500)]" />}
    </button>
  </div>
</div>
```

Typewriter interval is exactly **25 ms / char** (see §6.3). Reset + retype on tab switch. Clipboard copy → swap to accent check icon for **2000 ms**, then revert.

### 4.4 Terminal Mockup (product section)

Mac-style traffic-light dots with a text title on the right:

```tsx
<div className="rounded-lg border border-[var(--color-base-800)] bg-[var(--color-base-900)] overflow-hidden">
  <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--color-base-800)]">
    <div className="flex items-center gap-2">
      <div className="w-3 h-3 rounded-full bg-[var(--color-base-600)]" />
      <div className="w-3 h-3 rounded-full bg-[var(--color-base-600)]" />
      <div className="w-3 h-3 rounded-full bg-[var(--color-base-600)]" />
    </div>
    <span className="font-mono text-[12px] text-[var(--color-base-500)]">
      01 — TERMINAL / IDE
    </span>
  </div>
  <div className="p-6 min-h-[300px]">{/* content */}</div>
</div>
```

Traffic-light dots are **monochromatic grey** (never red/yellow/green — that's macOS, not Factory). Title format: `NN — CATEGORY`.

### 4.5 Navigation Dropdown ("Product" menu)

Two-column grid of icon-tiles inside a **rounded-xl dashed-border panel**:

```tsx
<div className="w-[520px] p-3 rounded-xl border border-dashed
                border-[var(--color-base-700)] bg-[var(--background)] shadow-2xl">
  <div className="grid grid-cols-2 gap-1">
    {/* each tile: */}
    <a className="group relative flex items-start gap-3 p-2.5 rounded-lg
                  border border-dashed border-transparent
                  hover:border-[var(--color-base-700)]
                  transition-colors overflow-hidden">
      {/* stripe overlay on hover */}
      <div className="pointer-events-none absolute inset-0 opacity-0
                      group-hover:opacity-30 transition-opacity duration-100">
        <div className="btn-stripe-pattern absolute inset-0"
             style={{ "--lines-color": "var(--color-base-600)" } as React.CSSProperties} />
      </div>
      {/* icon square */}
      <div className="relative z-10 w-11 h-11 flex-shrink-0 rounded-lg
                      border border-[var(--color-base-700)] bg-[var(--background)]
                      flex items-center justify-center text-[var(--color-base-500)]">
        <TerminalIcon className="w-[18px] h-[18px]" />
      </div>
      {/* labels */}
      <div className="relative z-10">
        <div className="font-mono text-[13px] text-[var(--foreground)]">Terminal / IDE</div>
        <div className="font-mono text-[11px] text-[var(--color-base-500)]">Code where you work</div>
      </div>
    </a>
  </div>
</div>
```

Wrapper that toggles visibility:
```tsx
className={`absolute top-full left-1/2 -translate-x-1/2 pt-3 z-50
            transition-all duration-200 origin-top ${
  open ? "opacity-100 scale-100 translate-y-0"
       : "opacity-0 scale-95 -translate-y-2 pointer-events-none"
}`}
```

### 4.6 CTA Card

```tsx
<div className="rounded-lg border border-[var(--color-base-800)]
                bg-[var(--color-base-900)] p-8 lg:p-12 max-w-[520px]">
  <LogoMark className="w-12 h-12 text-[var(--color-base-400)] mb-6" />
  <h2 className="text-[28px] lg:text-[36px] font-normal leading-[110%]
                 tracking-[-0.02em] text-[var(--foreground)] mb-6">
    Ready to build the<br />software of the future?
  </h2>
  <Button size="sm">Start Building <ArrowIcon className="w-3 h-3" /></Button>
</div>
```

### 4.7 Footer (inset rounded card, not full-bleed)

```tsx
<footer className="mx-4 lg:mx-9 mb-4 lg:mb-9 rounded-lg
                   border border-[var(--color-base-800)] bg-[var(--color-base-900)]
                   p-8 lg:p-12 min-h-[360px] flex flex-col">
```

Footer layout (top → bottom):
1. `<Badge text="FOOTER" />`
2. Link grid (2-3 columns) with section titles `text-[var(--foreground)] font-normal text-[14px] mb-4`, items `font-mono text-[14px] text-[var(--color-base-500)] hover:text-[var(--foreground)] transition-colors`.
3. Theme toggle (right-aligned pill).
4. Bottom bar: `border-t border-[var(--color-base-800)] pt-8` with `LogoMark` left, comma-separated social links center, copyright right — all `font-mono text-[14px]`.

### 4.8 Theme Toggle

```tsx
<div className="flex items-center gap-1 rounded-full
                border border-[var(--color-base-700)] p-1">
  {/* three circular buttons */}
  <button className={`p-2 rounded-full transition-colors ${
    theme === mode
      ? "bg-[var(--color-base-800)] text-[var(--foreground)]"
      : "text-[var(--color-base-500)] hover:text-[var(--foreground)]"
  }`}>
    <MoonIcon className="w-4 h-4" />
  </button>
  {/* SunIcon, MonitorIcon similarly */}
</div>
```

The `system` button pairs the monitor icon with a `font-mono text-[10px] uppercase` "System" label.

**Theme switching logic** (verbatim):
```tsx
useEffect(() => {
  const root = document.documentElement;
  root.classList.add("disable-transitions");
  if (theme === "system") {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    root.setAttribute("data-theme", prefersDark ? "dark" : "light");
  } else {
    root.setAttribute("data-theme", theme);
  }
  localStorage.setItem("theme", theme);
  setTimeout(() => root.classList.remove("disable-transitions"), 100);
}, [theme]);
```

The `.disable-transitions` class freezes all transitions during the swap to avoid 300ms color animations on every token.

### 4.9 Hover Underline (nav links)

Apply `hover-underline` to nav links for the sliding-underline effect. Do **not** use Tailwind's `hover:underline`.

```css
.hover-underline { position: relative; }
.hover-underline::after {
  content: ''; position: absolute; bottom: -1px; left: 0;
  width: 0; height: 1px; background-color: currentColor;
  transition: width 0.3s ease-in-out;
}
.hover-underline:hover::after { width: 100%; }
```

### 4.10 Logo & LogoMark

`Logo` is word-based (`ACME` in Geist Sans, fontWeight 600, letter-spacing -0.02em) inside an SVG. `LogoMark` is a rounded square with a plus sign. Both accept `className` and use `currentColor` — drive color through parent `text-[var(--color-base-XXX)]`.

---

## 5. Patterns & Surfaces

### 5.1 Dashed vs solid borders

- **Dashed** `border-dashed border-[var(--color-base-700)]` → interactive containers (dropdown panel, hoverable tiles, diagonal accent areas).
- **Solid** `border-[var(--color-base-800)]` → structural surfaces (cards, CTA, footer, terminal chrome, CLI box, tab dividers).

Never mix: a single container uses one or the other.

### 5.2 Stripe pattern — three uses

1. **Animated** `.btn-stripe-pattern` → buttons + nav tiles (hover-revealed overlay).
2. **Static** `.btn-pattern` (`currentColor` lines, no animation) → decorative backgrounds when the parent color should drive the lines.
3. **Inline SVG URL** for entire section backgrounds:

```tsx
<section className="relative overflow-hidden bg-[#fafafa]">
  <div
    className="absolute inset-0 opacity-[0.11]"
    style={{
      backgroundImage: `url("data:image/svg+xml,%3Csvg width='7' height='7' viewBox='0 0 7 7' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 0L7 7' stroke='%23888' stroke-width='1.2' fill='none'/%3E%3C/svg%3E")`,
      backgroundSize: '7px 7px'
    }}
  />
  <div className="relative ...grid...">{/* content */}</div>
</section>
```

The product section inverts to a near-white (`#fafafa`) surface with 11%-opacity diagonal lines. Always wrap content in a `relative` child so it sits above the `absolute inset-0` pattern.

### 5.3 Marquee (brand strip)

`animate-marquee` (30s linear infinite, `translateX(0) → translateX(-50%)`). To loop seamlessly, render the brand list **twice** inside an `overflow-hidden` flex row, then apply `animate-marquee`. `.animate-marquee-reverse` flips direction.

### 5.4 Scrollbar

Custom 8px webkit scrollbar: track `var(--color-base-900)`, thumb `var(--color-base-600)` (hover `-500`). Do not restyle.

---

## 6. Motion & Animation — signatures

All motion respects `prefers-reduced-motion` via the rule at the bottom of `globals.css` which forces `animation-duration: 0.01ms` and `transition-duration: 0.01ms`.

### 6.1 Character Reveal — hero headline

Use the `useCharReveal(heroRef)` hook. It:
1. Splits text into `<span class="char">` spans via `splitTextIntoChars`.
2. Sets `opacity:0, y:initialY, color:initialColor` on all chars.
3. On `IntersectionObserver` hit, GSAPs them to `opacity:1, y:0, color:finalColor` with stagger + `ease-reveal` (`cubic-bezier(0.645, 0.045, 0.355, 1)`).

Defaults live in `ANIMATION_CONFIG.charReveal`. **Only the hero `<h1>` gets this.** Section h2s stay static.

### 6.2 Scramble Text — badges

`useScrambleText(textRef, iconRef, { text, triggerOnScroll: true, infinite: true })`. Characters cycle through `XO01` before resolving. Duration 800ms, reveal begins at 50% progress. Every `<Badge>` uses this — if you want it static, pass `animated={false}`.

### 6.3 Typewriter — CLI command

Interval `25ms`/char. Cursor is an 8×16px filled `<span>` block, visible only while `isTyping`. Triggered on tab change by clearing state and restarting the interval. Keep the Unix command exactly: `curl -fsSL https://app.example.com/cli | sh`. Windows: `irm https://app.example.com/cli/windows | iex`.

### 6.4 Blink — static cursor (alternative)

```css
.animate-blink { animation: blink 1s step-end infinite; }
.typewriter-cursor {
  display: inline-block; width: 2px; height: 1em;
  background-color: currentColor; margin-left: 2px;
  animation: blink 1.06s step-end infinite;
}
```

### 6.5 Scale / Slide (menus, modals, nav content)

All 250ms eased. Use the ready-made utilities:
- `.animate-scale-in` / `.animate-scale-out`
- `.animate-enter-from-left` / `-right`, `.animate-exit-to-left` / `-right`
- `.animate-accordion-down` / `-up` (bind to `--radix-accordion-content-height`)
- `.animate-fade-in-up` (600ms, `--ease-reveal`)

Radix NavigationMenu content auto-binds via `.nav-menu-content[data-state|data-motion]` selectors in `globals.css`.

### 6.6 Transitions (the default)

For all non-signature motion: `transition-colors duration-150` or `transition-all duration-200`. Never `duration-500` for hovers.

### 6.7 GPU / perf helpers

- `.gpu-accelerated` → `will-change: transform; transform: translateZ(0); backface-visibility: hidden;` — apply to elements under GSAP control.
- `.invisible-animated` → hides pre-animated elements without layout shift (for GSAP `autoAlpha`).
- `.paused` / `.running` → control `animation-play-state`.

---

## 7. Iconography

**Style**: stroke-based `<svg viewBox="0 0 24 24">`, `fill="none"`, `stroke="currentColor"`, `strokeWidth="2"`, `strokeLinecap="round"`, `strokeLinejoin="round"`. **Never** fill icons. Size with `w-3 h-3` (button), `w-4 h-4` (theme toggle, copy), `w-[18px] h-[18px]` (nav tile icons), `w-12 h-12` (section LogoMarks), `w-16 h-16` (empty-state LogoMarks).

Icons are inline React components in the page, not imported from `lucide-react` — **keep them inline**, named exactly: `ChevronIcon`, `ArrowIcon`, `CopyIcon`, `CheckIcon`, `MoonIcon`, `SunIcon`, `MonitorIcon`, `TerminalIcon`, `SlackIcon`, `WebIcon`, `ProjectIcon`, `CLIIcon`. If a new icon is needed, follow the same 24×24 stroke-2 pattern.

---

## 8. File Structure

When scaffolding or extending a Factory-style project, mirror this layout:

```
app/
  globals.css              ← tokens, keyframes, utility classes (authoritative)
  layout.tsx               ← Geist fonts, data-theme="dark"
  page.tsx                 ← landing page with inline icons
  {route}/page.tsx
components/
  ui/
    button.tsx  badge.tsx  heading.tsx  text.tsx  index.ts
  shared/
    logo.tsx   theme-toggle.tsx
  home/
    animated-chart.tsx  brands-marquee.tsx
hooks/
  useCharReveal.ts  useScrambleText.ts  useReveal.ts
  useReducedMotion.ts  useTheme.ts  index.ts
lib/
  utils.ts   ← cn(), splitTextIntoChars, scrambleText, typewriterText, debounce, throttle
  gsap.ts    ← ANIMATION_CONFIG, revealEase, registered plugins
```

Tooling:
- **Next.js App Router** (≥ 16), **React 19**, **TypeScript strict**.
- **Tailwind CSS 4** via `@tailwindcss/postcss` and `@import "tailwindcss"` (no `tailwind.config.js`; the `@theme inline` block in `globals.css` wires tokens).
- **class-variance-authority** for every reusable component.
- **clsx + tailwind-merge** behind `cn()`.
- **@radix-ui/react-slot** for `asChild`, plus `@radix-ui/react-accordion` / `-navigation-menu` / `-select`.
- **gsap** (core only — paid plugins are replaced by `splitTextIntoChars` + `scrambleText` in `lib/utils.ts`).
- **geist** package + `next/font/google`.

### `cn` utility (copy verbatim)

```ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }
```

### HTML root attributes

`<html lang="en" data-theme="dark" suppressHydrationWarning>` — always.

---

## 9. Authoring Rules (enforcement)

When generating or editing UI in a Factory-style codebase, **do**:

- Reference colors via `var(--token)` — never `#xxxxxx` or `oklch(...)` inline except inside `globals.css`.
- Use `font-mono` by default; only drop to sans for display/section headings.
- Prefer pixel-exact `text-[Npx]` values from §3.
- Set `tracking-[-0.015rem]` on small mono labels, `tracking-[-0.0175rem]` on body, `tracking-[-0.04em]` on display headlines.
- Wrap every section in the 4/12 grid.
- Place one `<Badge>` at the top of every major section.
- Use dashed borders for interactive containers, solid for structural.
- Use the `btn-stripe-pattern` overlay on any hoverable surface that's "primary" in feel.
- Always provide dark and light via token inversion — don't ship single-theme UI.
- Always guard motion with `useReducedMotion` / the global media query.
- Keep icons inline, 24×24, stroke-2, `currentColor`.
- On route changes or tab swaps that re-trigger typewriters: reset state then restart intervals (don't just mutate text).

**Do not**:

- Introduce `bg-gray-900`, `text-slate-500`, arbitrary shadcn tokens, or `dark:` variants — the theme comes from `data-theme` + CSS vars, not Tailwind's `dark` class.
- Use `rounded-full` on buttons or `rounded-2xl` on cards — the system is **4px button / 8px card / 12px panel**.
- Add drop shadows (except `shadow-2xl` on the product-menu dropdown). The look is flat with borders, not elevated.
- Import `lucide-react` / `heroicons`. Icons are handcrafted inline SVGs.
- Use Tailwind's `container` class or `max-w-7xl`. Grid + `mx-auto` only.
- Use emoji in UI copy.
- Use bold weights on marketing headlines — they are **font-normal**. Bold is reserved for the `metrics` CVA variant.
- Animate anything longer than 300ms except the signature reveals.
- Use red, green, yellow, blue, or purple for UI state. Success/confirm is `--color-accent-100` (orange check). Error states, if needed, desaturate to `--color-base-400` or use a new token you add to `:root`.

---

## 10. Quick-Reference Cheat Sheet

```
BG page:            bg-[var(--background)]
Text primary:       text-[var(--foreground)]
Text body:          text-[var(--color-base-400)]
Text muted:         text-[var(--color-base-500)]
Accent:             text-[var(--color-accent-100)]
Card bg:            bg-[var(--color-base-900)]
Deep fill:          bg-[var(--color-base-1000)]
Solid border:       border-[var(--color-base-800)]
Dashed border:      border-dashed border-[var(--color-base-700)]

Hero h1:   text-[40px] lg:text-[60px] 2xl:text-[72px] font-mono font-normal leading-[100%] tracking-[-0.04em]
Section h2:text-[32px] lg:text-[48px] font-normal  leading-[100%] tracking-[-0.04em]
CTA h2:    text-[28px] lg:text-[36px] font-normal  leading-[110%] tracking-[-0.02em]
Body:      font-mono text-[14px] lg:text-[16px] leading-[140%] tracking-[-0.0175rem]
Label:     font-mono text-[12px] uppercase tracking-[-0.015rem]
Tab pill:  px-2 py-0.5 rounded text-[11px] font-mono uppercase tracking-[-0.01rem]

Button sm: h-[25px] px-3 text-[12px] rounded-[4px]
Button md: h-[31px] px-[14px] text-[12px] rounded-[4px]
Button lg: h-[40px] px-6 text-[14px] rounded-[4px]

Card radius: rounded-lg (8px)
Panel radius:rounded-xl (12px)
Icon stroke: stroke="currentColor" strokeWidth="2" fill="none"
Transition:  transition-colors duration-150  (hovers)
             transition-all    duration-200  (menus)
```

When in doubt, open `app/globals.css`, `app/page.tsx`, `components/ui/button.tsx`, and `components/ui/badge.tsx` — those four files are the design law. Copy their patterns verbatim before inventing new ones.
