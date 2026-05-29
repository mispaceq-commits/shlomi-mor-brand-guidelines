"""Render variants-toile.html (sand/beige LV heritage variant) to PDF + PNGs."""
import asyncio
import os
import sys
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
PDF_OUT = os.path.join(ROOT, "exports", "Shlomi-Mor-Wigs-Premium-Toile.pdf")
PNG_DIR = sys.argv[1] if len(sys.argv) > 1 else "/tmp"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page = await ctx.new_page()
        await page.goto("http://localhost:8765/variants-toile.html", wait_until="networkidle")
        await page.evaluate("document.fonts.ready")
        await page.emulate_media(media="print")
        await page.pdf(
            path=PDF_OUT,
            width="15in",
            height="9.375in",
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            print_background=True,
        )
        names = [
            "toile-01-cover",
            "toile-02-contents",
            "toile-03-foundation",
            "toile-04-colors",
            "toile-05-typography",
        ]
        count = await page.locator(".page").count()
        for i in range(count):
            el = page.locator(".page").nth(i)
            await el.screenshot(
                path=f"{PNG_DIR}/{names[i] if i < len(names) else f'toile-{i:02d}'}.png",
                omit_background=False,
            )
        await browser.close()
        print(f"Wrote {PDF_OUT} and {count} PNGs to {PNG_DIR}")

if __name__ == "__main__":
    asyncio.run(main())
