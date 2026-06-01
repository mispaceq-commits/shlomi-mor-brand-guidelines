"""Render variants-couture-noir.html (Chanel x Dior 6-page sampler) to PDF + PNGs."""
import asyncio
import os
import sys
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
PDF_OUT = os.path.join(ROOT, "exports", "Shlomi-Mor-Wigs-Premium-Couture-Noir.pdf")
PNG_DIR = sys.argv[1] if len(sys.argv) > 1 else "/tmp"

PRINT_CSS = """
@page {
  size: 15in 9.375in;
  margin: 0;
}
html, body {
  background: #0E0E0E !important;
  margin: 0 !important;
  padding: 0 !important;
}
.book {
  display: block !important;
  padding: 0 !important;
  gap: 0 !important;
  margin: 0 !important;
  background: #0E0E0E !important;
}
.page {
  width: 1440px !important;
  height: 900px !important;
  aspect-ratio: auto !important;
  page-break-after: always !important;
  break-after: page !important;
  box-shadow: none !important;
  margin: 0 !important;
  overflow: hidden !important;
}
.page:last-of-type {
  page-break-after: auto !important;
  break-after: auto !important;
}
.pageinfo { display: none !important; }
"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page = await ctx.new_page()
        await page.goto("http://localhost:8765/variants-couture-noir.html", wait_until="networkidle")
        await page.add_style_tag(content=PRINT_CSS)
        await page.evaluate("document.fonts.ready")
        await page.emulate_media(media="print")
        await page.pdf(
            path=PDF_OUT,
            width="15in",
            height="9.375in",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        names = [
            "couture-noir-01-cover",
            "couture-noir-02-house",
            "couture-noir-03-palette",
            "couture-noir-04-typography",
            "couture-noir-05-voice",
            "couture-noir-06-applications",
        ]
        count = await page.locator(".page").count()
        for i in range(count):
            el = page.locator(".page").nth(i)
            await el.screenshot(
                path=f"{PNG_DIR}/{names[i] if i < len(names) else f'couture-{i:02d}'}.png",
                omit_background=False,
            )
        await browser.close()
        print(f"Wrote {PDF_OUT} and {count} PNGs to {PNG_DIR}")

if __name__ == "__main__":
    asyncio.run(main())
