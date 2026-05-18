# Email signature — Shlomi Mor Wigs

A Gmail-ready HTML email signature in the *Clean Luxury Editorial* style of the
brand book. Built with old-school table layout and inline CSS so it renders
reliably in Gmail, Outlook, Apple Mail and mobile clients.

![Preview](preview.png)

## Files

```
email-signature/
  signature.html     # the markup to paste into Gmail (uses absolute image URLs)
  preview.html       # browser preview using relative image paths
  preview.png        # rendered screenshot of the signature
  assets/
    shlomi-mor-logo.png      # logo, retina-ready
    icon-location.png        # 14×14 line icons (rendered at 2× = 28×28)
    icon-phone.png
    icon-mail.png
    icon-globe.png
    icon-arrow.png           # 32×12 CTA arrow
```

## Install in Gmail (per user)

1. Open the rendered preview in a browser:
   ```bash
   cd email-signature
   python3 -m http.server 8000
   # then open http://localhost:8000/preview.html
   ```
2. **Select the entire signature block** (everything inside the white card on
   `preview.html`) with `Ctrl/Cmd + A` after clicking inside the card, or just
   triple-click to select and drag.
3. Copy with `Ctrl/Cmd + C`.
4. In Gmail, go to **Settings (gear icon) → See all settings → General →
   Signature**.
5. Click **Create new** and name it (e.g. *Default*).
6. Paste with `Ctrl/Cmd + V` into the signature editor.
7. Under **Signature defaults**, set the new signature for *FOR NEW EMAILS USE*
   and *ON REPLY/FORWARD USE*.
8. Scroll to the bottom of the page and click **Save Changes**.

> Tip: Gmail also exposes a paperclip-like *Insert signature* button in the
> compose window if you want to pick the signature per email instead of always
> appending it.

## Editing the personal fields

The four lines you'll usually want to change live near the top of
`signature.html`:

| Field          | Default value                            |
| -------------- | ---------------------------------------- |
| Name           | `MICHAEL P`                              |
| Role           | `HEAD OF MARKETING`                      |
| Address        | `49 West 24th Street, New York, NY 10010`|
| Phone          | `917.440.2178` (link: `tel:+19174402178`)|
| Email          | `marketing@shlomimorwigs.com`            |
| Website        | `https://www.shlomimorwigs.com`          |
| CTA link       | `https://www.shlomimorwigs.com/book`     |

Edit those strings in `signature.html` (or directly in the Gmail editor after
pasting) before saving.

## Hosting the images

Gmail only renders images from publicly-reachable HTTPS URLs. The shipped
`signature.html` references the assets from this repository via
`raw.githubusercontent.com`, which works out of the box once the repo is on the
default branch.

If you'd rather host the images on the brand domain (recommended once
`shlomimorwigs.com` is live), upload the contents of `email-signature/assets/`
to e.g. `https://www.shlomimorwigs.com/assets/email/` and find-replace this
prefix in `signature.html`:

```
https://raw.githubusercontent.com/mispaceq-commits/shlomi-mor-brand-guidelines/main/email-signature/assets/
```

with:

```
https://www.shlomimorwigs.com/assets/email/
```

## Notes on client support

- **Gmail (web, iOS, Android)** — full support, matches preview.
- **Apple Mail / iOS Mail** — full support, including retina rendering.
- **Outlook 2016+ (Windows)** — works; Outlook doesn't honor `width:auto` on
  `<img>`, so the explicit `width` / `height` attributes are kept on every image.
- **Dark mode** — text uses the brand ink `#0E0E0E`; the logo and icons are
  authored on white so they remain readable when Apple Mail / Gmail invert the
  background.
- SVG is intentionally **not** used in the signature because Gmail strips it.
  Source masters live under `../assets/logo/` and the PNG assets in this folder
  are regenerated from them.

## Regenerating the assets

The PNG logo and line icons are produced from the SVG masters with CairoSVG +
Pillow:

```bash
pip install cairosvg pillow
python3 email-signature/build_assets.py
```
