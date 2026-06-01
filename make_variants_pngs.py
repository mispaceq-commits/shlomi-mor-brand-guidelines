"""Render each .page section in variants.html to a 1440x900 PNG."""
import asyncio
import sys
from playwright.async_api import async_playwright


async def main(out_dir: str) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page = await ctx.new_page()
        await page.goto("http://localhost:8765/variants.html", wait_until="networkidle")
        await page.evaluate("document.fonts.ready")
        count = await page.locator(".page").count()
        names = [
            "premium-01-cover",
            "premium-02-contents",
            "premium-03-mission",
            "premium-04-colors",
            "premium-05-typography",
        ]
        for i in range(count):
            el = page.locator(".page").nth(i)
            await el.screenshot(path=f"{out_dir}/{names[i] if i < len(names) else f'page-{i:02d}'}.png", omit_background=False)
        await browser.close()
        print(f"Wrote {count} PNGs to {out_dir}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp"))
