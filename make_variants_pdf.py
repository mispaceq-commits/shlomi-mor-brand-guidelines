"""
Render variants.html (Premium Cover + Premium Contents) to a 2-page PDF
matching the book's 1440x900 logical-pixel page geometry (15in x 9.375in).

Usage:
    # In one terminal:
    python3 -m http.server 8765
    # In another:
    python3 make_variants_pdf.py [output_path]
"""
import asyncio
import sys
from playwright.async_api import async_playwright

PRINT_CSS = """
@page {
  size: 15in 9.375in;
  margin: 0;
}
html, body {
  background: #ffffff !important;
  margin: 0 !important;
  padding: 0 !important;
}
.book {
  display: block !important;
  padding: 0 !important;
  gap: 0 !important;
  margin: 0 !important;
  background: #ffffff !important;
}
.page {
  width: 1440px !important;
  height: 900px !important;
  aspect-ratio: auto !important;
  page-break-after: always !important;
  break-after: page !important;
  box-shadow: none !important;
  margin: 0 !important;
}
.page:last-of-type {
  page-break-after: auto !important;
  break-after: auto !important;
}
.pageinfo { display: none !important; }
"""


async def main(out_path: str) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page = await ctx.new_page()
        await page.goto("http://localhost:8765/variants.html", wait_until="networkidle")
        await page.add_style_tag(content=PRINT_CSS)
        await page.evaluate("document.fonts.ready")
        await page.emulate_media(media="print")
        await page.pdf(
            path=out_path,
            width="15in",
            height="9.375in",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        await browser.close()
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "exports/Shlomi-Mor-Wigs-Premium-Variants.pdf"
    asyncio.run(main(output))
