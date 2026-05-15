# Shlomi Mor Wigs — Brand Guidelines

A static, single-page editorial brand book for **Shlomi Mor Wigs**, designed in the *Clean Luxury Editorial* style.

The guidelines cover:

- Brand story, mission and pillars
- Logo system, construction and misuse
- Color palette (main + applications)
- Typography (idot / Futura LT / Articulat CF / Sacramento)
- Grid, photography direction, tone of voice
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
assets/          # SVG icons and decorative graphics
```

## Typography notes

The brand uses **idot** (display serif) and **Futura LT / Articulat CF** as functional sans-serif. For this static brand book preview, license-friendly Google Font substitutes are used (Playfair Display, Jost, Sacramento). When delivering final assets, swap the `@font-face` declarations in `styles.css` for the licensed fonts.
