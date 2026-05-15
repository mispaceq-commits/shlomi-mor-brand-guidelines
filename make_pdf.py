import asyncio
from playwright.async_api import async_playwright

# Page is 1440x900 logical pixels. PDF in inches at 96dpi -> 15.00 x 9.375 inches
# Use page-size based on aspect ratio. Set landscape A4 isn't right; use a custom width/height in pixels.
# Playwright's page.pdf supports width/height with units. We'll use 15in x 9.375in to match 1440/96 x 900/96.

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

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = await ctx.new_page()
        await page.goto("http://localhost:8765/", wait_until="networkidle")
        await page.add_style_tag(content=PRINT_CSS)
        # Wait for web fonts (Sacramento) to load.
        await page.evaluate("document.fonts.ready")
        await page.emulate_media(media="print")
        await page.pdf(
            path="/tmp/Shlomi-Mor-Wigs-Brand-Guidelines.pdf",
            width="15in",
            height="9.375in",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        await browser.close()
        print("OK")

asyncio.run(main())
