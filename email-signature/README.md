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

| Field          | Default value                                                       |
| -------------- | ------------------------------------------------------------------- |
| Name           | `MICHAEL P`                                                         |
| Role           | `HEAD OF MARKETING`                                                 |
| Address        | `49 West 24th Street, New York, NY 10010`                           |
| Phone          | `917.440.2178` (link: `tel:+19174402178`)                           |
| Email          | `marketing@shlomimorwigs.com`                                       |
| Website        | `https://www.shlomimorwigs.com`                                     |
| CTA link       | `https://shlomimorwigs.com/booking-consultation/?type=saloonwig`    |

Edit those strings in `signature.html` (or directly in the Gmail editor after
pasting) before saving.

## Hosting the images

Gmail only renders images from publicly-reachable HTTPS URLs. The shipped
`signature.html` uses two image hosts:

- **Logo** is served from Cloudinary at
  `https://res.cloudinary.com/dnickckih/image/upload/v1779125002/shlomi-mor-logo_abmf6k.png`.
  This is the brand's existing CDN and the URL works immediately.
- **Line icons + CTA arrow** are served from `raw.githubusercontent.com` on the
  `main` branch of this repo. They start returning 200 the moment this PR is
  merged to `main`.

If you'd rather host the icons on the Cloudinary CDN too (recommended for
consistency), upload the contents of `email-signature/assets/` (everything
except the logo, which is already there) into the same Cloudinary folder and
find-replace this prefix in `signature.html`:

```
https://raw.githubusercontent.com/mispaceq-commits/shlomi-mor-brand-guidelines/main/email-signature/assets/
```

with the Cloudinary URL prefix for those uploads, e.g.:

```
https://res.cloudinary.com/dnickckih/image/upload/v.../
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
