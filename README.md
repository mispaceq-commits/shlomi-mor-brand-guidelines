# Shlomi Mor Wigs — Brand Guidelines

A static, single-page editorial brand book for **Shlomi Mor Wigs**, designed in the *Clean Luxury Editorial* style.

The guidelines cover:

- Brand story, mission and pillars
- Logo system, construction and misuse
- Color palette (main + applications)
- Typography (idot / Futura LT / Inter / Sacramento / Snell Roundhand)
- Grid, photography direction, tone of voice
- Pattern system (monogram field, hairline lattice, script watermark, strand texture)
- Type specimen, UI kit and H1–H6 hierarchy
- Instagram grid architecture, stories & reels templates, caption tone
- Applications and brand contact

## Running locally

This is a plain static site — no build step required.

```bash
# any static server works; e.g.
python3 -m http.server 8000
# then open http://localhost:8000
```

## Structure

```
index.html       # all pages of the brand book, as scrollable sections
styles.css       # all styles (editorial layout, typography, color tokens)
assets/
  logo/          # SM logo SVG masters (black/white, full/monogram)
  fonts/         # licensed font files (Didot, Futura LT, Snell Roundhand)
```

## Typography

Approved type system (used throughout the book and no others):

| Role               | Family                                      | Files in `assets/fonts/` |
| ------------------ | ------------------------------------------- | ------------------------ |
| Display Serif      | **idot** (mapped to licensed Didot)         | `Didot-Regular.otf`, `Didot-Italic.otf`, `Didot-Bold.otf`, `Didot-Title.otf` |
| Functional Sans    | **Futura LT** (primary) / **Inter** (fallback) | `FuturaLT-Light.ttf` ... `FuturaLT-BoldOblique.ttf` |
| Script Accent      | **Sacramento** (Google OFL) / **Snell Roundhand** (signature) | `SnellRoundhand-Bold.otf`, `SnellRoundhand-Black.otf` |

The full Futura LT package (including Condensed and Heavy/ExtraBold variants) is kept in the repo for downstream design work. Sacramento and Inter load from Google Fonts (OFL). No other typefaces are permitted in this brand book.

## Export to PDF

The book is print-ready: each `.page` section is sized at 1440 × 900 px, and Chromium's `Print → Save as PDF` (or the bundled `make_pdf.py` script) produces a 24-page PDF with vector text and SVG logos that opens cleanly in Adobe Illustrator for further editing.
