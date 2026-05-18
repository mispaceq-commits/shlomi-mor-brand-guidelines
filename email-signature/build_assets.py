"""Regenerate the email-signature PNG assets from the SVG masters.

Run from the repo root:

    pip install cairosvg pillow
    python3 email-signature/build_assets.py
"""
from __future__ import annotations

import os
from pathlib import Path

import cairosvg
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "email-signature" / "assets"
OUT.mkdir(parents=True, exist_ok=True)


def render_logo() -> None:
    """Render assets/logo/shlomi-mor-logo-black.svg → assets/shlomi-mor-logo.png."""
    raw = OUT / "_full.png"
    cairosvg.svg2png(
        url=str(REPO / "assets" / "logo" / "shlomi-mor-logo-black.svg"),
        write_to=str(raw),
        output_width=2000,
        output_height=2000,
    )
    im = Image.open(raw).convert("RGBA")
    bbox = im.split()[-1].getbbox()
    if bbox is None:
        raise RuntimeError("logo render is empty")
    cropped = im.crop(bbox)
    pad_x = int(cropped.size[0] * 0.06)
    pad_y = int(cropped.size[1] * 0.08)
    padded = Image.new(
        "RGBA",
        (cropped.size[0] + pad_x * 2, cropped.size[1] + pad_y * 2),
        (255, 255, 255, 0),
    )
    padded.paste(cropped, (pad_x, pad_y), cropped)
    bg = Image.new("RGB", padded.size, (255, 255, 255))
    bg.paste(padded, (0, 0), padded)
    target_w = 480
    target_h = int(bg.size[1] * (target_w / bg.size[0]))
    final = bg.resize((target_w, target_h), Image.LANCZOS)
    final.save(OUT / "shlomi-mor-logo.png", optimize=True)
    os.remove(raw)


# Inline SVG sources for the line icons — kept here so the build is hermetic.
ICONS: dict[str, str] = {
    "location": """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>
  <g fill='none' stroke='#0E0E0E' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>
    <path d='M12 22s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12z'/>
    <circle cx='12' cy='10' r='2.5'/>
  </g>
</svg>""",
    "phone": """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>
  <path fill='none' stroke='#0E0E0E' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'
        d='M5 4.5C5 3.7 5.7 3 6.5 3h2.3c.6 0 1.2.4 1.4 1l1 3a1.5 1.5 0 0 1-.4 1.6L9.4 9.8a14 14 0 0 0 4.8 4.8l1.2-1.4c.4-.5 1-.6 1.6-.4l3 1c.6.2 1 .8 1 1.4v2.3c0 .8-.7 1.5-1.5 1.5C10.6 19 5 13.4 5 4.5z'/>
</svg>""",
    "mail": """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>
  <g fill='none' stroke='#0E0E0E' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>
    <rect x='3' y='5' width='18' height='14' rx='1.5'/>
    <path d='M3.5 6.5l8.5 7 8.5-7'/>
  </g>
</svg>""",
    "globe": """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>
  <g fill='none' stroke='#0E0E0E' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>
    <circle cx='12' cy='12' r='9'/>
    <path d='M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18'/>
  </g>
</svg>""",
}

ARROW_SVG = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 12'>
  <g fill='none' stroke='#0E0E0E' stroke-width='1.4' stroke-linecap='round' stroke-linejoin='round'>
    <line x1='1' y1='6' x2='30' y2='6'/>
    <polyline points='24,1 30,6 24,11'/>
  </g>
</svg>"""


def render_icons() -> None:
    for name, src in ICONS.items():
        cairosvg.svg2png(
            bytestring=src.encode("utf-8"),
            write_to=str(OUT / f"icon-{name}.png"),
            output_width=96,
            output_height=96,
        )
    cairosvg.svg2png(
        bytestring=ARROW_SVG.encode("utf-8"),
        write_to=str(OUT / "icon-arrow.png"),
        output_width=128,
        output_height=48,
    )


if __name__ == "__main__":
    render_logo()
    render_icons()
    print(f"Wrote assets to {OUT}")
