"""
Build an editable PowerPoint version of the Shlomi Mor Wigs brand book.
Each of the 24 pages becomes one slide with native text boxes and embedded
logo images. Fonts: idot (Didot) / Futura LT / Snell Roundhand.
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from copy import deepcopy
from lxml import etree

LOGO_DIR = "/tmp/logo_png"
# Actual logo content aspect ratios (width / height) after trimming transparent pad
FULL_LOGO_AR = 1.225
MONO_AR = 1.182

def logo_size(target_w=None, target_h=None, mono=False):
    """Return (w, h) preserving aspect ratio. Pass either target_w or target_h."""
    ar = MONO_AR if mono else FULL_LOGO_AR
    if target_w is not None:
        return target_w, target_w / ar
    return target_h * ar, target_h

# Colors
C_INK = RGBColor(0x0E, 0x0E, 0x0E)
C_PAPER = RGBColor(0xFF, 0xFF, 0xFF)
C_CREAM = RGBColor(0xFB, 0xF8, 0xF4)
C_MUTE = RGBColor(0x8B, 0x84, 0x80)
C_RULE = RGBColor(0xD9, 0xD2, 0xCB)
C_BLUSH = RGBColor(0xFC, 0xE3, 0xE5)
C_ROSE = RGBColor(0xB6, 0x8F, 0x90)
C_GOLD = RGBColor(0xA7, 0x8D, 0x52)
C_CHAMPAGNE = RGBColor(0xC9, 0xAC, 0x7F)
C_GRAY = RGBColor(0x6E, 0x66, 0x63)

# Fonts
F_SERIF = "Didot"
F_SANS = "Futura LT"
F_SCRIPT = "Snell Roundhand"
F_SANS_FALLBACK = "Inter"

# Slide size: 13.333 x 8.333 inches (matches 1440x900)
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(8.333)
SCALE_X = SLIDE_W / 1440  # EMU per CSS px
SCALE_Y = SLIDE_H / 900

def px(x):   return Emu(int(round(x * SCALE_X)))
def py(y):   return Emu(int(round(y * SCALE_Y)))

def add_bg(slide, color):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    bg.line.fill.background()
    bg.fill.solid(); bg.fill.fore_color.rgb = color
    return bg

def add_text(slide, x, y, w, h, text, *, font=F_SANS, size=12, color=C_INK,
             bold=False, italic=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             tracking=None, upper=False, line_spacing=None):
    """Add a single-paragraph text box with controlled formatting."""
    tb = slide.shapes.add_textbox(px(x), py(y), px(w), py(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    if line_spacing:
        p.line_spacing = line_spacing
    r = p.add_run()
    r.text = text.upper() if upper else text
    r.font.name = font
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    if tracking is not None:
        # set character spacing (in 1/100 pt) via XML
        rPr = r._r.get_or_add_rPr()
        rPr.set("spc", str(tracking))
    return tb

def add_rich_text(slide, x, y, w, h, runs, *, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    """Add a textbox with multiple runs. Each run = dict(text, font, size, color, bold, italic, tracking, upper)."""
    tb = slide.shapes.add_textbox(px(x), py(y), px(w), py(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor
    paragraphs = []
    current = tf.paragraphs[0]
    current.alignment = align
    paragraphs.append(current)
    for spec in runs:
        if spec.get("br"):
            current = tf.add_paragraph(); current.alignment = align
            paragraphs.append(current)
            continue
        r = current.add_run()
        text = spec["text"]
        r.text = text.upper() if spec.get("upper") else text
        r.font.name = spec.get("font", F_SANS)
        r.font.size = Pt(spec.get("size", 12))
        r.font.bold = spec.get("bold", False)
        r.font.italic = spec.get("italic", False)
        r.font.color.rgb = spec.get("color", C_INK)
        spacing = spec.get("tracking")
        if spacing is not None:
            rPr = r._r.get_or_add_rPr()
            rPr.set("spc", str(spacing))
    return tb

def add_line(slide, x1, y1, x2, y2, *, color=C_RULE, weight=0.5):
    from pptx.util import Pt as PT
    ln = slide.shapes.add_connector(1, px(x1), py(y1), px(x2), py(y2))
    ln.line.color.rgb = color
    ln.line.width = PT(weight)
    return ln

def add_rect(slide, x, y, w, h, *, fill=None, line=None, line_weight=0.5):
    r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x), py(y), px(w), py(h))
    if fill is None:
        r.fill.background()
    else:
        r.fill.solid(); r.fill.fore_color.rgb = fill
    if line is None:
        r.line.fill.background()
    else:
        r.line.color.rgb = line
        from pptx.util import Pt as PT
        r.line.width = PT(line_weight)
    return r

def add_oval(slide, x, y, w, h, *, fill=None, line=None, line_weight=0.5):
    r = slide.shapes.add_shape(MSO_SHAPE.OVAL, px(x), py(y), px(w), py(h))
    if fill is None: r.fill.background()
    else: r.fill.solid(); r.fill.fore_color.rgb = fill
    if line is None: r.line.fill.background()
    else:
        r.line.color.rgb = line
        from pptx.util import Pt as PT
        r.line.width = PT(line_weight)
    return r

def add_image(slide, x, y, w, h, path):
    return slide.shapes.add_picture(path, px(x), py(y), width=px(w), height=py(h))

# Common rails
def rails(slide, page_num, label_left, label_right):
    # Top rail (eyebrow + page number)
    add_text(slide, 72, 56, 700, 16, label_left, font=F_SANS, size=10,
             color=C_MUTE, upper=True, tracking=180)
    add_text(slide, 1440-72-100, 56, 100, 16, str(page_num).zfill(2),
             font=F_SANS, size=10, color=C_MUTE, align=PP_ALIGN.RIGHT, tracking=180)
    add_line(slide, 72, 84, 1440-72, 84)
    # Bottom rail
    add_line(slide, 72, 820, 1440-72, 820)
    add_text(slide, 72, 832, 700, 16, label_right, font=F_SANS, size=10,
             color=C_MUTE, upper=True, tracking=180)
    add_text(slide, 1440-72-100, 832, 100, 16, str(page_num).zfill(2),
             font=F_SANS, size=10, color=C_MUTE, align=PP_ALIGN.RIGHT, tracking=180)

# ============================================================
prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
blank = prs.slide_layouts[6]

# ------- PAGE 01: COVER -------
s = prs.slides.add_slide(blank); add_bg(s, C_CREAM)
add_text(s, 72, 56, 600, 16, "Shlomi Mor Wigs · NYC", font=F_SANS, size=10,
         color=C_INK, upper=True, tracking=220)
add_text(s, 1440-72-300, 56, 300, 16, "Edition 01 · 2025", font=F_SANS, size=10,
         color=C_INK, upper=True, tracking=220, align=PP_ALIGN.RIGHT)
lw, lh = logo_size(target_h=130, mono=True)
add_image(s, (1440-lw)/2, 130, lw, lh, f"{LOGO_DIR}/shlomi-mor-monogram-black.png")
add_rich_text(s, 72, 440, 1180, 280, [
    {"text":"the","font":F_SCRIPT,"size":48,"color":C_GOLD,"italic":True},
    {"br":True},
    {"text":"Brand ","font":F_SERIF,"size":120,"color":C_INK},
    {"text":"Book.","font":F_SERIF,"size":120,"color":C_INK,"italic":True},
])
# Seal (circle on right)
add_oval(s, 1260, 420, 140, 140, line=C_INK, line_weight=0.5)
add_rich_text(s, 1260, 440, 140, 100, [
    {"text":"Crown","font":F_SCRIPT,"size":14,"color":C_INK,"italic":True},
    {"br":True},
    {"text":"Your","font":F_SCRIPT,"size":14,"color":C_INK,"italic":True},
    {"br":True},
    {"text":"Confidence","font":F_SCRIPT,"size":14,"color":C_INK,"italic":True},
], align=PP_ALIGN.CENTER)
add_text(s, 72, 832, 320, 16, "Visual Identity Guidelines", font=F_SANS,
         size=10, color=C_INK, upper=True, tracking=200)
add_text(s, 560, 832, 320, 16, "Vol. I — Foundations", font=F_SANS,
         size=10, color=C_INK, upper=True, tracking=200, align=PP_ALIGN.CENTER)
add_text(s, 1440-72-280, 832, 280, 16, "Made in NY · USA", font=F_SANS,
         size=10, color=C_INK, upper=True, tracking=200, align=PP_ALIGN.RIGHT)

# Helper for content pages
def content_slide(num, eyebrow, title_parts, body, *, bg=C_CREAM, foot=None):
    s = prs.slides.add_slide(blank); add_bg(s, bg)
    rails(s, num, eyebrow, foot or eyebrow)
    add_text(s, 72, 124, 1100, 20, f"{num:02d} — {eyebrow}", font=F_SANS,
             size=10, color=C_MUTE, upper=True, tracking=200)
    add_rich_text(s, 72, 160, 1296, 80, title_parts)
    if body:
        add_text(s, 72, 280, 700, 200, body, font=F_SANS, size=13,
                 color=C_INK, line_spacing=1.55)
    return s

# ------- PAGE 02: CONTENTS -------
toc_items = [
    ("01","Cover"),("02","Contents"),("03","Welcome & Brand Story"),
    ("04","Mission · Vision · Values"),("05","Two Streams — Medical & Luxury"),
    ("06","Logo Variations"),("07","Logo Construction & Clear Space"),
    ("08","Logo Misuse"),("09","The Main Colors"),
    ("10","Color Usage & Proportions"),("11","Display Serif — idot"),
    ("12","Functional Sans — Futura LT / Inter"),
    ("13","Script Accent — Sacramento / Snell Roundhand"),
    ("14","Hierarchy & Pairing"),("15","Grid System"),
    ("16","Photography Direction"),("17","Tone of Voice"),
    ("18","Patterns — The System"),("19","Patterns — Rules & Application"),
    ("20","Type Specimen & UI Kit"),
    ("21","Instagram — Grid Architecture"),
    ("22","Instagram — Stories, Reels & Captions"),
    ("23","Applications"),("24","Contact & Credits"),
]
s = content_slide(2, "Contents", [
    {"text":"Table of ","font":F_SERIF,"size":64,"color":C_INK},
    {"text":"contents.","font":F_SERIF,"size":64,"color":C_INK,"italic":True},
], "A twenty-four-section brand book covering identity foundations, visual language and brand applications. Designed to be read in sequence, referenced as a system.")
# Three columns of TOC (8 rows each)
col_y_start = 360
for i, (num, name) in enumerate(toc_items):
    col = i // 8
    row = i % 8
    cx = 72 + col * 432
    cy = col_y_start + row * 44
    add_text(s, cx, cy, 36, 24, num, font=F_SANS, size=10, color=C_MUTE, tracking=160)
    add_text(s, cx+44, cy, 360, 24, name, font=F_SERIF, size=16, color=C_INK)
    add_line(s, cx, cy+32, cx+400, cy+32)

# ------- PAGE 03: WELCOME -------
content_slide(3, "Welcome", [
    {"text":"A house of ","font":F_SERIF,"size":64,"color":C_INK},
    {"text":"hair","font":F_SERIF,"size":64,"color":C_INK,"italic":True},
    {"text":", confidence","font":F_SERIF,"size":64,"color":C_INK},
    {"br":True},
    {"text":"and quiet ","font":F_SERIF,"size":64,"color":C_INK},
    {"text":"craft","font":F_SERIF,"size":64,"color":C_INK,"italic":True},
    {"text":".","font":F_SERIF,"size":64,"color":C_INK},
],
"Shlomi Mor Wigs is a luxury custom-wig atelier based in New York City. We work with two women: the one rebuilding her sense of self after medical hair loss, and the one looking for the most exquisite, undetectable wig of her life. Both deserve the same level of craft, intimacy and editorial restraint — and both find it here.")

# ------- PAGE 04: MISSION / VISION / VALUES -------
s = content_slide(4, "Foundations", [
    {"text":"Mission ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"·","font":F_SERIF,"size":56,"color":C_MUTE},
    {"text":" Vision ","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
    {"text":"·","font":F_SERIF,"size":56,"color":C_MUTE},
    {"text":" Values","font":F_SERIF,"size":56,"color":C_INK},
], None)
# Three columns
cols = [
    ("Mission","To return a woman's reflection to her — through European hair, hand-tied craftsmanship and a private, unhurried experience."),
    ("Vision","To become the most trusted custom-wig atelier between Tel Aviv and New York, known equally for medical sensitivity and editorial excellence."),
    ("Values","Discretion · Craft · Empathy · Longevity · Beauty without compromise."),
]
for i, (label, body) in enumerate(cols):
    cx = 72 + i*440
    add_text(s, cx, 340, 200, 16, label, font=F_SANS, size=10,
             color=C_MUTE, upper=True, tracking=200)
    add_text(s, cx, 372, 400, 60, label, font=F_SERIF, size=32, color=C_INK)
    add_text(s, cx, 440, 380, 300, body, font=F_SANS, size=13,
             color=C_INK, line_spacing=1.55)

# ------- PAGE 05: TWO STREAMS -------
s = content_slide(5, "Streams", [
    {"text":"Two women, ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"one ","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
    {"br":True},
    {"text":"atelier","font":F_SERIF,"size":56,"color":C_INK},
    {"text":".","font":F_SERIF,"size":56,"color":C_INK},
], None)
# Two streams side by side
streams = [
    (C_BLUSH, "Medical Hair Loss", "Restoration",
     "Soft, supportive, undetectable. We meet her where she is — with European hair, custom caps and the quiet space to recognise herself again."),
    (RGBColor(0x14,0x14,0x14), "Luxury Custom Wigs", "Style & status",
     "Fashion-editorial restraint with the craft of a couture house. Made for clients who never compromise on the quality of their hair.")
]
for i, (bg, eyebrow, head, body) in enumerate(streams):
    cx = 72 + i * 660
    add_rect(s, cx, 320, 620, 400, fill=bg)
    text_color = C_INK if bg == C_BLUSH else C_PAPER
    add_text(s, cx+40, 350, 540, 16, eyebrow, font=F_SANS, size=10,
             color=text_color if bg!=C_BLUSH else C_GRAY, upper=True, tracking=200)
    add_text(s, cx+40, 392, 540, 80, head, font=F_SERIF, size=32, color=text_color)
    add_text(s, cx+40, 480, 540, 200, body, font=F_SANS, size=13,
             color=text_color, line_spacing=1.55)

# ------- PAGE 06: LOGO VARIATIONS -------
s = content_slide(6, "Identity", [
    {"text":"The ","font":F_SERIF,"size":64,"color":C_INK},
    {"text":"Logo","font":F_SERIF,"size":64,"color":C_INK,"italic":True},
], None)
# 3 panels: primary on cream, reversed on black, monogram on blush
panels = [
    (72,  260, 540, 320, C_CREAM, "Primary · Cream",    f"{LOGO_DIR}/shlomi-mor-logo-black.png",     180, False),
    (652, 260, 716, 200, C_INK,   "Reversed · Black",   f"{LOGO_DIR}/shlomi-mor-logo-white.png",     110, False),
    (652, 480, 716, 100, C_BLUSH, "Monogram · Blush",   f"{LOGO_DIR}/shlomi-mor-monogram-black.png", 64,  True),
]
for x, y, w, h, bg, label, logo, lh, mono in panels:
    add_rect(s, x, y, w, h, fill=bg, line=C_RULE)
    add_text(s, x+20, y+12, w-40, 16, label, font=F_SANS, size=9,
             color=C_MUTE if bg!=C_INK else RGBColor(0xC9,0xC4,0xBF),
             upper=True, tracking=200)
    lw, lh2 = logo_size(target_h=lh, mono=mono)
    add_image(s, x + (w-lw)/2, y + (h-lh2)/2 + 10, lw, lh2, logo)

# Captions row
caps = [
    ("Primary lockup","The full mark: SM monogram crowning the SHLOMI MOR WIGS wordmark. Used on cover, packaging, signage and editorial."),
    ("Reversed","For dark surfaces and editorial imagery the full mark is set in soft paper white. Always reserve quiet contrast around it."),
    ("Monogram","The SM monogram alone. Used for stamps, favicons, embroidery, dust-bag corner marks and any small applications."),
]
for i, (h, b) in enumerate(caps):
    cx = 72 + i*440
    add_text(s, cx, 620, 200, 16, h, font=F_SANS, size=10,
             color=C_INK, upper=True, tracking=200)
    add_text(s, cx, 644, 400, 200, b, font=F_SANS, size=12,
             color=C_INK, line_spacing=1.55)

# ------- PAGE 07: LOGO CONSTRUCTION -------
s = content_slide(7, "Construction & Clear Space", [
    {"text":"Built on ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"x.","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
], None)
# Construction frame with logo
add_rect(s, 72, 280, 760, 440, fill=C_CREAM, line=C_RULE)
clw, clh = logo_size(target_h=240)
add_image(s, 72 + (760-clw)/2, 280 + (440-clh)/2, clw, clh, f"{LOGO_DIR}/shlomi-mor-logo-black.png")
# Grid lines (visualized)
for i in range(1, 8):
    x = 72 + (760/8)*i
    add_line(s, x, 280, x, 720, color=C_RULE, weight=0.25)
for i in range(1, 5):
    y = 280 + (440/5)*i
    add_line(s, 72, y, 832, y, color=C_RULE, weight=0.25)

add_text(s, 880, 300, 480, 20, "Clear Space", font=F_SANS,
         size=10, color=C_MUTE, upper=True, tracking=200)
add_text(s, 880, 326, 480, 60, "x = height of the M stem", font=F_SERIF, size=22, color=C_INK)
add_text(s, 880, 380, 480, 200,
         "Reserve at least one x of empty space on all sides of the mark. This is a non-negotiable minimum — never crowd the logo with text, imagery or color blocks.",
         font=F_SANS, size=13, color=C_INK, line_spacing=1.55)
add_text(s, 880, 540, 480, 20, "Minimum Size", font=F_SANS,
         size=10, color=C_MUTE, upper=True, tracking=200)
add_text(s, 880, 566, 480, 60, "Digital 28 px · Print 16 mm", font=F_SERIF, size=22, color=C_INK)

# ------- PAGE 08: LOGO MISUSE -------
s = content_slide(8, "Misuse", [
    {"text":"Please, ","font":F_SERIF,"size":64,"color":C_INK},
    {"text":"don't.","font":F_SERIF,"size":64,"color":C_INK,"italic":True},
], "The logo is a quiet object. The following alterations damage its tone, legibility or accessibility — and are never permitted in brand communication.")
# 6 misuse tiles
misuses = [
    ("01 · Never rotate", "Keep the mark upright."),
    ("02 · Never stretch", "Always uniform scale."),
    ("03 · Never low contrast", "Always legible."),
    ("04 · Never add shadows", "The mark stands flat."),
    ("05 · Never apply gradients", "Solid brand color only."),
    ("06 · Never off-brand color", "Use approved palette."),
]
for i, (label, hint) in enumerate(misuses):
    col = i % 3; row = i // 3
    cx = 72 + col * 432
    cy = 440 + row * 180
    add_rect(s, cx, cy, 412, 160, fill=C_CREAM, line=C_RULE)
    mw, mh = logo_size(target_h=80)
    add_image(s, cx + (412-mw)/2, cy + 24, mw, mh, f"{LOGO_DIR}/shlomi-mor-logo-black.png")
    add_text(s, cx+16, cy+128, 380, 14, label, font=F_SANS, size=10,
             color=C_INK, upper=True, tracking=180)
    add_text(s, cx+16, cy+146, 380, 14, hint, font=F_SANS, size=9,
             color=C_MUTE, italic=True)
    # X marker
    add_oval(s, cx+412-32, cy+12, 24, 24, fill=C_INK)
    add_text(s, cx+412-32, cy+12, 24, 24, "×", font=F_SANS, size=12,
             color=C_PAPER, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# ------- PAGE 09: MAIN COLORS -------
s = content_slide(9, "Color", [
    {"text":"The main ","font":F_SERIF,"size":64,"color":C_INK},
    {"text":"colors","font":F_SERIF,"size":64,"color":C_INK,"italic":True},
    {"text":".","font":F_SERIF,"size":64,"color":C_INK},
], None)
colors = [
    ("Rich Dusty Rose","B68F90","182 · 143 · 144","30 · 47 · 36 · 11", C_ROSE),
    ("Soft Powder Blush","FCE3E5","252 · 227 · 229","0 · 13 · 5 · 0", C_BLUSH),
    ("Muted Antique Gold","A78D52","167 · 141 · 82","30 · 38 · 75 · 16", C_GOLD),
    ("Soft Champagne","C9AC7F","201 · 172 · 127","20 · 30 · 53 · 5", C_CHAMPAGNE),
    ("Signature Black","0E0E0E","14 · 14 · 14","0 · 0 · 0 · 95", C_INK),
    ("Elegant Stone Gray","6E6663","110 · 102 · 99","48 · 50 · 51 · 38", C_GRAY),
]
sw_w = (1440 - 144 - 5*20) / 6
for i, (name, hexv, rgb, cmyk, color) in enumerate(colors):
    cx = 72 + i*(sw_w+20)
    add_rect(s, cx, 320, sw_w, 280, fill=color, line=C_RULE)
    add_text(s, cx, 620, sw_w, 16, name, font=F_SANS, size=10,
             color=C_INK, upper=True, tracking=160)
    add_text(s, cx, 640, sw_w, 12, f"#{hexv}", font=F_SANS, size=9, color=C_MUTE)
    add_text(s, cx, 656, sw_w, 12, f"R {rgb}", font=F_SANS, size=9, color=C_MUTE)
    add_text(s, cx, 672, sw_w, 12, f"C {cmyk}", font=F_SANS, size=9, color=C_MUTE)

# ------- PAGE 10: COLOR USAGE -------
s = content_slide(10, "Proportions", [
    {"text":"How the ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"palette","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
    {"br":True},
    {"text":"breathes.","font":F_SERIF,"size":56,"color":C_INK},
], None)
# Proportion bar
add_text(s, 72, 360, 600, 16, "Recommended distribution",
         font=F_SANS, size=10, color=C_MUTE, upper=True, tracking=200)
totals = [(C_CREAM, "Paper Cream", 45), (C_INK, "Signature Black", 25),
          (C_BLUSH, "Powder Blush", 15), (C_GOLD, "Antique Gold", 8),
          (C_ROSE, "Dusty Rose", 5), (C_CHAMPAGNE, "Champagne", 2)]
bx = 72
for color, name, pct in totals:
    w = (1440 - 144) * pct / 100
    add_rect(s, bx, 400, w, 80, fill=color)
    add_text(s, bx, 488, w, 14, f"{pct}%", font=F_SERIF, size=11, color=C_INK)
    add_text(s, bx, 504, w, 14, name, font=F_SANS, size=8,
             color=C_MUTE, upper=True, tracking=160)
    bx += w
add_text(s, 72, 600, 900, 100,
         "Cream and black form the canvas. Blush and gold deliver warmth and luxury. Rose and champagne are reserved for accents and seasonal materials.",
         font=F_SANS, size=13, color=C_INK, line_spacing=1.55)

# ------- PAGE 11: DISPLAY SERIF -------
s = content_slide(11, "Display Serif", [
    {"text":"Headlines — ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"idot.","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
], None)
# Sample
add_text(s, 72, 320, 700, 300, "AaBb", font=F_SERIF, size=180, color=C_INK)
# Meta
meta = [("Typeface","idot — high-contrast didone"),
        ("Role","Headlines, covers, editorial titles"),
        ("Mood","Vogue · Harper's Bazaar · Couture"),
        ("Tracking","-1% to -2% at display sizes"),
        ("Style mix","Roman for statements, italic for emphasis")]
for i, (k, v) in enumerate(meta):
    add_text(s, 850, 320+i*52, 200, 14, k, font=F_SANS, size=10,
             color=C_MUTE, upper=True, tracking=200)
    add_text(s, 850, 340+i*52, 480, 16, v, font=F_SANS, size=13, color=C_INK)

# ------- PAGE 12: FUNCTIONAL SANS -------
s = content_slide(12, "Functional Sans", [
    {"text":"Body & UI — ","font":F_SERIF,"size":52,"color":C_INK},
    {"text":"Futura LT / Inter.","font":F_SERIF,"size":52,"color":C_INK,"italic":True},
], None)
add_text(s, 72, 320, 700, 300, "Aa Bb", font=F_SANS, size=160, color=C_INK)
meta = [("Typeface","Futura LT — with Inter as digital alternative"),
        ("Role","Body, captions, navigation, CTAs, microcopy"),
        ("Mood","Clean, geometric, modern"),
        ("Tracking","+22% for eyebrows · 0% for body"),
        ("Weights","Light · Book · Medium · Bold")]
for i, (k, v) in enumerate(meta):
    add_text(s, 850, 320+i*52, 200, 14, k, font=F_SANS, size=10,
             color=C_MUTE, upper=True, tracking=200)
    add_text(s, 850, 340+i*52, 480, 16, v, font=F_SANS, size=13, color=C_INK)

# ------- PAGE 13: SCRIPT ACCENT -------
s = content_slide(13, "Accent", [
    {"text":"A whisper — ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"Sacramento.","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
], None, bg=C_BLUSH)
add_text(s, 72, 320, 700, 300, "she", font=F_SCRIPT, size=200,
         color=C_GOLD, italic=True)
meta = [("Typeface","Sacramento / Snell Roundhand"),
        ("Role","Accent only — one or two words per page"),
        ("Use cases","Hero accents · taglines · signatures · social"),
        ("Color","Muted Antique Gold or Soft Champagne"),
        ("Tracking","0%, never tracked or stretched")]
for i, (k, v) in enumerate(meta):
    add_text(s, 850, 320+i*52, 200, 14, k, font=F_SANS, size=10,
             color=C_GRAY, upper=True, tracking=200)
    add_text(s, 850, 340+i*52, 480, 16, v, font=F_SANS, size=13, color=C_INK)

# ------- PAGE 14: HIERARCHY -------
s = content_slide(14, "Pairing & Hierarchy", [
    {"text":"How they ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"speak.","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
], None)
add_text(s, 72, 320, 1100, 16, "Eyebrow / 11 / 220",
         font=F_SANS, size=10, color=C_MUTE, upper=True, tracking=200)
add_text(s, 72, 344, 1100, 16, "HAND-CRAFTED IN NYC",
         font=F_SANS, size=10, color=C_INK, upper=True, tracking=200)
add_text(s, 72, 384, 1100, 100, "Display headline / 56 / Didot",
         font=F_SANS, size=10, color=C_MUTE, upper=True, tracking=200)
add_text(s, 72, 408, 1296, 100, "A wig that feels like you, only quieter.",
         font=F_SERIF, size=56, color=C_INK)
add_text(s, 72, 524, 1100, 16, "Body / 14 / 1.7",
         font=F_SANS, size=10, color=C_MUTE, upper=True, tracking=200)
add_text(s, 72, 548, 800, 200,
         "Each piece is custom-made for the woman who wears it — European hair, hand-knotted lace, a private fitting. The work happens slowly; the result feels inevitable.",
         font=F_SANS, size=14, color=C_INK, line_spacing=1.7)
add_text(s, 72, 692, 1100, 16, "CTA / 12 / 180 / uppercase",
         font=F_SANS, size=10, color=C_MUTE, upper=True, tracking=200)
add_text(s, 72, 716, 400, 24, "Book Consultation →",
         font=F_SANS, size=12, color=C_INK, upper=True, tracking=180, bold=True)

# ------- PAGE 15: GRID -------
s = content_slide(15, "Grid", [
    {"text":"A quiet ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"twelve.","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
], "The book is built on a 12-column grid with a 72 px outer margin and a 24 px gutter, on a 1440 × 900 px stage. Each page is structured around an editorial silence — content occupies roughly 60% of the surface; the rest breathes.")
# Visualize grid
add_rect(s, 72, 400, 1296, 360, line=C_RULE)
for i in range(1, 12):
    x = 72 + (1296/12)*i
    add_line(s, x, 400, x, 760, color=C_RULE, weight=0.25)
add_text(s, 72, 768, 1296, 14, "12 columns · 72 px margin · 24 px gutter",
         font=F_SANS, size=10, color=C_MUTE, upper=True, tracking=200, align=PP_ALIGN.CENTER)

# ------- PAGE 16: PHOTOGRAPHY -------
s = content_slide(16, "Photography", [
    {"text":"Light, ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"skin","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
    {"text":", silence.","font":F_SERIF,"size":56,"color":C_INK},
], None)
moods = [
    ("Medical · Restoration","Warm window light. Hands, jewellery, the back of a neck. The wig as a quiet companion, not a performance."),
    ("Luxury · Editorial","Studio lighting. Bare shoulders, ironed silk, the architecture of a face. The wig as couture, photographed like couture.")
]
for i, (h, b) in enumerate(moods):
    cx = 72 + i * 660
    add_rect(s, cx, 320, 620, 300, fill=C_CREAM, line=C_RULE)
    add_text(s, cx+30, 340, 540, 16, h, font=F_SANS, size=10,
             color=C_MUTE, upper=True, tracking=200)
    add_text(s, cx+30, 380, 540, 200, b,
             font=F_SANS, size=13, color=C_INK, line_spacing=1.55)
add_text(s, 72, 660, 1296, 100,
         "Always shoot on neutral grounds — paper white, cream, clay. Never on saturated color. Models are calm, off-centre, never looking at the camera.",
         font=F_SANS, size=13, color=C_INK, line_spacing=1.6)

# ------- PAGE 17: TONE OF VOICE -------
s = content_slide(17, "Tone of Voice", [
    {"text":"Speak ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"softly.","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
], None)
pillars = [("Intimate","Like a fitting in a quiet room."),
           ("Confident","Without ornament or proof."),
           ("Editorial","Composed sentences, generous space."),
           ("Empathic","Especially with the medical client.")]
for i, (h, b) in enumerate(pillars):
    cx = 72 + (i % 2) * 660
    cy = 320 + (i // 2) * 180
    add_text(s, cx, cy, 200, 16, h, font=F_SANS, size=10,
             color=C_MUTE, upper=True, tracking=200)
    add_text(s, cx, cy+24, 540, 50, h, font=F_SERIF, size=28, color=C_INK)
    add_text(s, cx, cy+70, 540, 100, b, font=F_SANS, size=14,
             color=C_INK, italic=True, line_spacing=1.55)

# ============================================================
# PAGE 18: PATTERNS · THE SYSTEM
# ============================================================
s = content_slide(18, "Patterns", [
    {"text":"A quiet ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"repeat.","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
],
"Four discreet patterns extend the brand beyond the logo — for endpapers, dust-bag interiors, packaging linings, story backgrounds and stationery. Each is built from a single brand asset and is meant to be felt, never read.",
   foot="The system — four discreet repeats")

# 2x2 grid of pattern tiles
tile_w = 636; tile_h = 174
tiles_18 = [
    (72,  430, "01 — Monogram Field",  "monogram"),
    (732, 430, "02 — Hairline Lattice", "lattice"),
    (72,  624, "03 — Script Watermark", "script"),
    (732, 624, "04 — Strand Texture",   "strand"),
]
for tx, ty, label, kind in tiles_18:
    add_rect(s, tx, ty, tile_w, tile_h, fill=C_CREAM, line=C_RULE)
    add_text(s, tx+22, ty+18, 400, 14, label, font=F_SANS, size=10,
             color=C_INK, upper=True, tracking=200)
    if kind == "monogram":
        mlw, mlh = logo_size(target_h=14, mono=True)
        for col in range(7):
            for row in range(3):
                rx = tx + 70 + col * 80 + (row % 2) * 30
                ry = ty + 60 + row * 38
                img = add_image(s, rx, ry, mlw, mlh, f"{LOGO_DIR}/shlomi-mor-monogram-black.png")
                img.rotation = -22
    elif kind == "lattice":
        # Diagonal cross-hatch
        for d in range(-12, 18):
            x0 = tx + d * 26
            add_line(s, x0,           ty+20, x0+tile_h-40, ty+tile_h-20, color=C_GOLD, weight=0.4)
            add_line(s, x0,           ty+tile_h-20, x0+tile_h-40, ty+20, color=C_GOLD, weight=0.4)
    elif kind == "script":
        add_text(s, tx+34, ty+58, 580, 28, "crown · confidence · she · crown",
                 font=F_SCRIPT, size=26, color=C_GOLD, italic=True)
        add_text(s, tx+88, ty+102, 580, 28, "she · crown · confidence · she",
                 font=F_SCRIPT, size=26, color=C_GOLD, italic=True)
    elif kind == "strand":
        for i in range(7):
            sx = tx + 30 + i*85
            add_line(s, sx,    ty+40,  sx+70, ty+tile_h-20, color=C_GOLD, weight=0.5)
            add_line(s, sx+10, ty+30,  sx+80, ty+tile_h-30, color=C_GOLD, weight=0.5)

# ============================================================
# PAGE 19: PATTERNS · RULES & APPLICATION
# ============================================================
s = content_slide(19, "Patterns", [
    {"text":"Where it ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"lives.","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
], None, foot="Rules & application")

# Four small mock tiles in a row at y=300
mock_w = 306; mock_h = 200
mocks_19 = [
    (72,  300, "Dust-bag interior · Monogram field", "monogram-mock", "she"),
    (402, 300, "Thank-you card · Hairline lattice",  "lattice-mock", "Thank you"),
    (732, 300, "IG story background · Script",       "script-mock", "Crown"),
    (1062,300, "Box endpaper · Strand texture",      "strand-mock", "M"),
]
for mx, my, label, kind, sample in mocks_19:
    if kind == "strand-mock":
        add_rect(s, mx, my, mock_w, mock_h, fill=C_INK)
        # subtle strand lines on dark
        for i in range(5):
            sx = mx + 20 + i*60
            add_line(s, sx, my+20, sx+50, my+mock_h-20, color=C_CHAMPAGNE, weight=0.4)
        mlw, mlh = logo_size(target_h=66, mono=True)
        add_image(s, mx + (mock_w-mlw)/2, my + (mock_h-mlh)/2, mlw, mlh,
                  f"{LOGO_DIR}/shlomi-mor-monogram-white.png")
        add_text(s, mx, my+mock_h+14, mock_w, 16, label, font=F_SANS, size=9,
                 color=C_MUTE, upper=True, tracking=200)
    else:
        add_rect(s, mx, my, mock_w, mock_h, fill=C_CREAM, line=C_RULE)
        # Background hint by pattern type
        if kind == "monogram-mock":
            mlw, mlh = logo_size(target_h=14, mono=True)
            for col in range(5):
                for row in range(3):
                    rx = mx + 30 + col * 60 + (row % 2) * 20
                    ry = my + 40 + row * 44
                    img = add_image(s, rx, ry, mlw, mlh, f"{LOGO_DIR}/shlomi-mor-monogram-black.png")
                    img.rotation = -22
            add_text(s, mx+90, my+80, 140, 50, sample, font=F_SCRIPT, size=36,
                     color=C_INK, italic=True, align=PP_ALIGN.CENTER)
        elif kind == "lattice-mock":
            for d in range(-8, 16):
                x0 = mx + d * 24
                add_line(s, x0, my+20, x0+mock_h-40, my+mock_h-20, color=C_GOLD, weight=0.35)
                add_line(s, x0, my+mock_h-20, x0+mock_h-40, my+20, color=C_GOLD, weight=0.35)
            add_text(s, mx+24, my+72, mock_w-48, 30, sample, font=F_SERIF, size=22,
                     color=C_INK, align=PP_ALIGN.CENTER)
            add_text(s, mx+24, my+108, mock_w-48, 30, "Shlomi", font=F_SERIF, size=22,
                     color=C_INK, italic=True, align=PP_ALIGN.CENTER)
        elif kind == "script-mock":
            add_text(s, mx+10, my+50, mock_w-20, 28, "crown · confidence · she",
                     font=F_SCRIPT, size=22, color=C_GOLD, italic=True)
            add_text(s, mx+30, my+90, mock_w-20, 28, "she · crown · confidence",
                     font=F_SCRIPT, size=22, color=C_GOLD, italic=True)
            add_text(s, mx+24, my+70, mock_w-48, 40, sample, font=F_SERIF, size=22,
                     color=C_INK, italic=True, align=PP_ALIGN.CENTER)
            add_text(s, mx+24, my+102, mock_w-48, 40, "your confidence",
                     font=F_SERIF, size=22, color=C_INK, italic=True, align=PP_ALIGN.CENTER)
        add_text(s, mx, my+mock_h+14, mock_w, 16, label, font=F_SANS, size=9,
                 color=C_MUTE, upper=True, tracking=200)

# Rules row at y=560
add_line(s, 72, 552, 1368, 552)
rules_19 = [
    ("Scale",       "Monogram tile 48–72 px on stationery, 96–128 px on packaging. Never below 32 px on print."),
    ("Opacity",     "8–14% on cream surfaces, 18–22% on ink. Always sit at least one tone below the foreground."),
    ("Color rules", "Antique Gold or Ink only. Never tint with Dusty Rose, Champagne or Blush — those are voice colors, not pattern colors."),
    ("Never",       "Never on portraits, never over the logo, never mix two patterns on one surface, never animate on web."),
]
for i, (head, body) in enumerate(rules_19):
    cx = 72 + i * 324
    add_text(s, cx, 572, 280, 16, head, font=F_SANS, size=10,
             color=C_INK, upper=True, tracking=200)
    add_text(s, cx, 600, 300, 200, body, font=F_SANS, size=12,
             color=C_INK, line_spacing=1.55)

# ============================================================
# PAGE 20: TYPE SPECIMEN & UI KIT
# ============================================================
s = content_slide(20, "Specimen", [
    {"text":"The ideal ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"stack.","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
], None, foot="Specimen & UI Kit")

# Left column — typographic stack
add_text(s, 72, 280, 540, 16, "Hand-crafted in NYC", font=F_SANS, size=11,
         color=C_INK, upper=True, tracking=320)
add_text(s, 72, 310, 540, 50, "virgin european", font=F_SCRIPT, size=32,
         color=C_GOLD, italic=True)
add_text(s, 72, 358, 540, 80, "Couture for the hairline.",
         font=F_SERIF, size=44, color=C_INK)
add_text(s, 72, 432, 540, 40, "A wig that feels like you, only quieter.",
         font=F_SERIF, size=22, color=C_INK, italic=True)
add_text(s, 72, 480, 540, 100,
         "Each piece is hand-ventilated in our New York atelier, knot by knot — a hairline that disappears into skin, a parting that moves like memory.",
         font=F_SANS, size=13, color=C_INK, line_spacing=1.55)
# Primary button mock
add_rect(s, 72, 588, 200, 38, fill=C_INK)
add_text(s, 72, 596, 200, 24, "BOOK CONSULTATION", font=F_SANS, size=11,
         color=C_PAPER, upper=True, tracking=220, bold=True, align=PP_ALIGN.CENTER)

# Right column — UI Kit (2x2 grid)
ui_cells = [
    (660, 280, "Buttons"),
    (1018, 280, "Tags & badges"),
    (660, 432, "Form field"),
    (1018, 432, "Pull-quote"),
]
for cx, cy, label in ui_cells:
    add_rect(s, cx, cy, 332, 138, fill=C_PAPER, line=C_RULE)
    add_text(s, cx+18, cy+14, 300, 14, label, font=F_SANS, size=10,
             color=C_MUTE, upper=True, tracking=220)
# Buttons cell content
add_rect(s, 660+18, 280+42, 130, 32, fill=C_INK)
add_text(s, 660+18, 280+48, 130, 24, "PRIMARY CTA", font=F_SANS, size=10,
         color=C_PAPER, upper=True, tracking=220, bold=True, align=PP_ALIGN.CENTER)
add_rect(s, 660+158, 280+42, 130, 32, fill=None, line=C_INK)
add_text(s, 660+158, 280+48, 130, 24, "SECONDARY", font=F_SANS, size=10,
         color=C_INK, upper=True, tracking=220, bold=True, align=PP_ALIGN.CENTER)
add_text(s, 660+18, 280+88, 290, 18, "read the story →", font=F_SANS, size=11,
         color=C_INK, italic=True)
# Tags cell content
add_rect(s, 1018+18, 280+44, 56, 22, fill=None, line=C_INK)
add_text(s, 1018+18, 280+48, 56, 18, "NEW", font=F_SANS, size=9,
         color=C_INK, upper=True, tracking=200, align=PP_ALIGN.CENTER)
add_rect(s, 1018+82, 280+44, 130, 22, fill=C_GOLD)
add_text(s, 1018+82, 280+48, 130, 18, "MEDICAL STREAM", font=F_SANS, size=9,
         color=C_PAPER, upper=True, tracking=200, align=PP_ALIGN.CENTER)
add_rect(s, 1018+220, 280+44, 80, 22, fill=C_INK)
add_text(s, 1018+220, 280+48, 80, 18, "CUSTOM", font=F_SANS, size=9,
         color=C_PAPER, upper=True, tracking=200, align=PP_ALIGN.CENTER)
add_text(s, 1018+18, 280+86, 290, 18,
         "Use sparingly — one per surface, never more than two per page.",
         font=F_SANS, size=10, color=C_MUTE, italic=True, line_spacing=1.4)
# Form field cell
add_text(s, 660+18, 432+44, 290, 16, "Your email", font=F_SANS, size=10,
         color=C_MUTE, upper=True, tracking=220)
add_text(s, 660+18, 432+66, 290, 28, "name@studio.com", font=F_SERIF,
         size=18, color=C_INK, italic=True)
add_line(s, 660+18, 432+98, 660+18+290, 432+98, color=C_INK, weight=0.8)
add_text(s, 660+18, 432+106, 290, 18, "Underlined italic · 32 px field height",
         font=F_SANS, size=9, color=C_MUTE, italic=True)
# Pull-quote cell
add_rich_text(s, 1018+18, 432+42, 290, 80, [
    {"text":"\u201cShe felt like herself, only ","font":F_SERIF,"size":18,"color":C_INK,"italic":True},
    {"text":"quieter","font":F_SCRIPT,"size":24,"color":C_GOLD,"italic":True},
    {"text":".\u201d","font":F_SERIF,"size":18,"color":C_INK,"italic":True},
])

# Hierarchy table at bottom (y=600)
add_line(s, 660, 588, 1368, 588)
hier_y = 600
add_text(s, 660, hier_y, 200, 16, "Role", font=F_SANS, size=9,
         color=C_MUTE, upper=True, tracking=200)
add_text(s, 860, hier_y, 220, 16, "Family", font=F_SANS, size=9,
         color=C_MUTE, upper=True, tracking=200)
add_text(s, 1080, hier_y, 160, 16, "Size / line", font=F_SANS, size=9,
         color=C_MUTE, upper=True, tracking=200)
add_text(s, 1240, hier_y, 120, 16, "Tracking", font=F_SANS, size=9,
         color=C_MUTE, upper=True, tracking=200)
hier_rows = [
    ("H1 · Display","idot · Regular","72 / 76","-0.005em"),
    ("H2 · Section","idot · Italic","48 / 52","-0.005em"),
    ("H3 · Sub","idot · Regular","32 / 38","0"),
    ("Body","Futura LT · Light","15 / 26","0"),
    ("Eyebrow","Futura LT · Medium","11 / 16","+0.32em"),
    ("CTA","Futura LT · Medium","12 / 16","+0.18em"),
]
for i, (role, family, size_line, tracking) in enumerate(hier_rows):
    ry = hier_y + 22 + i * 26
    add_text(s, 660, ry, 200, 18, role, font=F_SANS, size=11, color=C_INK)
    add_text(s, 860, ry, 220, 18, family, font=F_SANS, size=11, color=C_INK)
    add_text(s, 1080, ry, 160, 18, size_line, font=F_SANS, size=11, color=C_INK)
    add_text(s, 1240, ry, 120, 18, tracking, font=F_SANS, size=11, color=C_INK)
    add_line(s, 660, ry+22, 1368, ry+22, color=C_RULE, weight=0.25)

# ============================================================
# PAGE 21: INSTAGRAM · GRID ARCHITECTURE
# ============================================================
s = content_slide(21, "Instagram", [
    {"text":"Quiet, in ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"nine tiles.","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
],
"With 50k+ followers, the grid is our biggest storefront. It rotates three voices — portrait, word, detail — on a 3-3-3 rhythm, so the profile reads as one editorial spread, not nine separate posts.",
   foot="Grid & profile anatomy")

# 3x3 grid on the left
grid_x = 72; grid_y = 420; tile_size = 132; gap = 6
grid_tiles = [
    (C_CREAM,  "01 · Portrait",  None, None),
    (C_BLUSH,  "02 · Quote",     "crown\nyours", "script-gold"),
    (C_ROSE,   "03 · Detail",    None, None),
    (C_INK,    "04 · Monogram",  "logo", "monogram-white"),
    (C_BLUSH,  "05 · Portrait",  None, None),
    (C_GOLD,   "06 · Detail",    None, None),
    (C_GRAY,   "07 · Portrait",  None, None),
    (C_BLUSH,  "08 · Quote",     "She,\nagain.", "serif-italic"),
    (C_INK,    "09 · Detail",    None, None),
]
for i, (color, cap, sample, kind) in enumerate(grid_tiles):
    col = i % 3; row = i // 3
    tx = grid_x + col * (tile_size + gap)
    ty = grid_y + row * (tile_size + gap)
    add_rect(s, tx, ty, tile_size, tile_size, fill=color)
    cap_color = C_PAPER if color in (C_INK, C_GOLD, C_ROSE, C_GRAY) else C_MUTE
    add_text(s, tx+8, ty+tile_size-22, tile_size-16, 14, cap, font=F_SANS,
             size=8, color=cap_color, upper=True, tracking=160)
    if kind == "script-gold":
        add_text(s, tx+16, ty+30, tile_size-32, 80, sample, font=F_SCRIPT,
                 size=22, color=C_GOLD, italic=True, align=PP_ALIGN.CENTER)
    elif kind == "monogram-white":
        mlw, mlh = logo_size(target_h=54, mono=True)
        add_image(s, tx + (tile_size-mlw)/2, ty + (tile_size-mlh)/2 - 6, mlw, mlh,
                  f"{LOGO_DIR}/shlomi-mor-monogram-white.png")
    elif kind == "serif-italic":
        add_text(s, tx+12, ty+30, tile_size-24, 60, sample, font=F_SERIF,
                 size=16, color=C_INK, italic=True, align=PP_ALIGN.CENTER)

# Right column — profile anatomy + highlights
prof_x = 700
# Avatar
add_oval(s, prof_x, 420, 78, 78, fill=C_CREAM, line=C_RULE)
mlw, mlh = logo_size(target_h=46, mono=True)
add_image(s, prof_x + (78-mlw)/2, 420 + (78-mlh)/2, mlw, mlh,
          f"{LOGO_DIR}/shlomi-mor-monogram-black.png")
# Handle + bio
add_text(s, prof_x+96, 422, 540, 22, "shlomimorwigs", font=F_SANS, size=14,
         color=C_INK, bold=True)
add_text(s, prof_x+96, 446, 540, 16, "50.4k followers · NYC atelier",
         font=F_SANS, size=9, color=C_MUTE, upper=True, tracking=220)
add_text(s, prof_x+96, 472, 540, 50,
         "Custom human-hair wigs, handmade in New York. Crown your confidence. → shlomimorwigs.com",
         font=F_SANS, size=12, color=C_INK, line_spacing=1.5)
# Highlight covers
add_text(s, prof_x, 552, 540, 16, "Highlight covers", font=F_SANS, size=10,
         color=C_MUTE, upper=True, tracking=220)
highlights = [
    (C_CREAM, "Atelier",      C_INK),
    (C_INK,   "Medical",      C_PAPER),
    (C_GOLD,  "Custom",       C_PAPER),
    (C_BLUSH, "Before / After",C_INK),
    (C_CREAM, "Press",        C_INK),
    (C_INK,   "Care",         C_PAPER),
]
hc_size = 72
for i, (fill, label, txt_color) in enumerate(highlights):
    col = i % 3; row = i // 3
    hx = prof_x + col * (hc_size + 18)
    hy = 580 + row * (hc_size + 18)
    border = C_RULE if fill in (C_CREAM, C_BLUSH) else None
    add_oval(s, hx, hy, hc_size, hc_size, fill=fill, line=border)
    add_text(s, hx, hy + (hc_size-18)/2, hc_size, 22, label, font=F_SERIF,
             size=10, color=txt_color, italic=True, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE)

# ============================================================
# PAGE 22: INSTAGRAM · STORIES & REELS
# ============================================================
s = content_slide(22, "Instagram", [
    {"text":"Stories, ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"in motion.","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
], None, foot="Stories · Reels · Cadence")

# 4 vertical 9:16 mock frames
story_w = 200; story_h = 330  # 1.65 ratio (close enough to 9:16 = 1.78)
stories = [
    (72,  308, C_CREAM, "Quote", "script", None, C_INK),
    (388, 308, C_ROSE,  "Behind the scenes", "bts", None, C_PAPER),
    (704, 308, C_INK,   "FAQ", "faq", None, C_PAPER),
    (1020,308, C_GRAY,  "Reels · Cover", "reels", "0:32", C_PAPER),
]
for sx, sy, fill, top_label, kind, foot_label, fg in stories:
    add_rect(s, sx, sy, story_w, story_h, fill=fill)
    # Top eyebrow
    top_color = fg if fg != C_INK else C_MUTE
    add_text(s, sx+14, sy+14, story_w-28, 14, top_label, font=F_SANS, size=8,
             color=top_color, upper=True, tracking=220)
    if kind == "script":
        add_text(s, sx+14, sy+130, story_w-28, 40, "she, again.",
                 font=F_SCRIPT, size=30, color=C_INK, italic=True, align=PP_ALIGN.CENTER)
        add_text(s, sx+18, sy+180, story_w-36, 60,
                 "A hairline that disappears into skin.",
                 font=F_SERIF, size=12, color=C_INK, italic=True,
                 line_spacing=1.35, align=PP_ALIGN.CENTER)
    elif kind == "bts":
        add_rich_text(s, sx+14, sy+140, story_w-28, 90, [
            {"text":"Knot by\n","font":F_SERIF,"size":22,"color":C_PAPER},
            {"text":"knot.","font":F_SERIF,"size":22,"color":C_PAPER,"italic":True},
        ])
        add_text(s, sx+14, sy+story_h-44, story_w-28, 14, "Atelier · NYC",
                 font=F_SANS, size=8, color=C_PAPER, upper=True, tracking=220)
    elif kind == "faq":
        add_text(s, sx+14, sy+130, story_w-28, 16, "Question 03",
                 font=F_SANS, size=8, color=C_CHAMPAGNE, upper=True, tracking=240)
        add_text(s, sx+14, sy+156, story_w-28, 60,
                 "How long does a fitting take?",
                 font=F_SERIF, size=15, color=C_PAPER, italic=True, line_spacing=1.25)
        add_text(s, sx+14, sy+228, story_w-28, 60,
                 "About ninety minutes. We start with listening.",
                 font=F_SANS, size=10, color=C_PAPER, line_spacing=1.55)
    elif kind == "reels":
        add_rich_text(s, sx+14, sy+140, story_w-28, 90, [
            {"text":"Crown\nyour ","font":F_SERIF,"size":20,"color":C_PAPER},
            {"text":"confidence","font":F_SCRIPT,"size":32,"color":C_CHAMPAGNE,"italic":True},
        ])
        if foot_label:
            add_text(s, sx+14, sy+story_h-30, story_w-28, 16,
                     f"Episode 04 · {foot_label}", font=F_SANS, size=8,
                     color=C_PAPER, upper=True, tracking=220)
    # Caption below
    add_text(s, sx, sy+story_h+14, story_w, 16, top_label, font=F_SANS,
             size=9, color=C_MUTE, upper=True, tracking=200)

# Rules row at y=680
add_line(s, 72, 672, 1368, 672)
rules_22 = [
    ("Caption tone","3–5 short sentences. Lower-case for warmth, full stops always. No emoji. Em-dash and middle-dot welcome."),
    ("Hashtags",    "3 brand · 3 niche · 3 NYC. e.g. #shlomimorwigs #crownyourconfidence #customwigs #medicalwigs #nycatelier"),
    ("Cadence",     "4 grid posts / week · 5–7 stories / day · 1 reel / week. Tuesday + Friday are story-heavy days."),
    ("Safe zones",  "Story 1080×1920. Keep type 220 px from top, 320 px from bottom. Reels cover 1080×1920, centered lockup."),
]
for i, (head, body) in enumerate(rules_22):
    cx = 72 + i * 324
    add_text(s, cx, 692, 280, 16, head, font=F_SANS, size=10,
             color=C_INK, upper=True, tracking=200)
    add_text(s, cx, 720, 300, 90, body, font=F_SANS, size=11,
             color=C_INK, line_spacing=1.5)

# ============================================================
# PAGE 23: APPLICATIONS (was page 18 in 19-page edition)
# ============================================================
s = content_slide(23, "Applications", [
    {"text":"In the ","font":F_SERIF,"size":56,"color":C_INK},
    {"text":"world.","font":F_SERIF,"size":56,"color":C_INK,"italic":True},
], None)
# Business card front
add_rect(s, 72, 320, 320, 200, fill=C_CREAM, line=C_RULE)
bclw, bclh = logo_size(target_h=70)
add_image(s, 72 + (320-bclw)/2, 320 + (200-bclh)/2, bclw, bclh, f"{LOGO_DIR}/shlomi-mor-logo-black.png")
add_text(s, 90, 488, 280, 14, "BUSINESS CARD · FRONT", font=F_SANS, size=9,
         color=C_MUTE, upper=True, tracking=200, align=PP_ALIGN.CENTER)
# Business card back (black)
add_rect(s, 410, 320, 320, 200, fill=C_INK)
add_text(s, 430, 340, 280, 14, "Shlomi Mor", font=F_SERIF, size=22, color=C_PAPER)
add_text(s, 430, 376, 280, 14, "Master Wigmaker · Owner", font=F_SANS,
         size=9, color=RGBColor(0xC9,0xC4,0xBF), tracking=180, upper=True)
add_text(s, 430, 470, 280, 14, "shlomimorwigs.com", font=F_SANS, size=9,
         color=C_PAPER, tracking=180, upper=True)
# Dust bag
add_rect(s, 748, 320, 240, 200, fill=C_BLUSH)
dlw, dlh = logo_size(target_h=70, mono=True)
add_image(s, 748 + (240-dlw)/2, 320 + (200-dlh)/2, dlw, dlh, f"{LOGO_DIR}/shlomi-mor-monogram-black.png")
add_text(s, 768, 488, 200, 14, "DUST BAG", font=F_SANS, size=9,
         color=C_GRAY, upper=True, tracking=200, align=PP_ALIGN.CENTER)
# Instagram card
add_rect(s, 1006, 320, 250, 250, fill=C_INK)
ilw, ilh = logo_size(target_h=90, mono=True)
add_image(s, 1006 + (250-ilw)/2, 320 + (250-ilh)/2 - 20, ilw, ilh, f"{LOGO_DIR}/shlomi-mor-monogram-white.png")
add_text(s, 1006, 488, 250, 14, "@shlomimorwigs", font=F_SANS,
         size=10, color=C_PAPER, align=PP_ALIGN.CENTER, tracking=180)
add_text(s, 1006, 510, 250, 14, "SOCIAL · INSTAGRAM 1:1",
         font=F_SANS, size=9, color=RGBColor(0xC9,0xC4,0xBF),
         upper=True, tracking=200, align=PP_ALIGN.CENTER)
# Ad banner mockup
add_rect(s, 72, 580, 1184, 180, fill=C_CREAM, line=C_RULE)
add_text(s, 110, 620, 600, 60, "A wig that feels like you, only quieter.",
         font=F_SERIF, size=28, color=C_INK)
add_text(s, 110, 690, 200, 24, "Book Consultation →",
         font=F_SANS, size=11, color=C_INK, upper=True, tracking=180, bold=True)
alw, alh = logo_size(target_h=100, mono=True)
add_image(s, 1184-alw, 620, alw, alh, f"{LOGO_DIR}/shlomi-mor-monogram-black.png")
add_text(s, 72, 776, 1184, 14, "AD BANNER · 1200 × 600",
         font=F_SANS, size=9, color=C_MUTE, upper=True, tracking=200)

# ------- PAGE 19: CONTACT -------
s = prs.slides.add_slide(blank); add_bg(s, C_INK)
rlw, rlh = logo_size(target_h=180, mono=True)
add_image(s, (1440-rlw)/2, 240, rlw, rlh, f"{LOGO_DIR}/shlomi-mor-monogram-white.png")
add_rich_text(s, 72, 500, 1296, 120, [
    {"text":"Crown ","font":F_SCRIPT,"size":52,"color":C_CHAMPAGNE,"italic":True},
    {"text":"your ","font":F_SERIF,"size":52,"color":C_PAPER,"italic":True},
    {"text":"confidence.","font":F_SERIF,"size":52,"color":C_PAPER},
], align=PP_ALIGN.CENTER)
add_text(s, 72, 640, 1296, 16,
         "shlomimorwigs.com   ·   info@shlomimorwigs.com   ·   @shlomimorwigs",
         font=F_SANS, size=11, color=RGBColor(0xC9,0xC4,0xBF),
         tracking=200, upper=True, align=PP_ALIGN.CENTER)
add_text(s, 72, 680, 1296, 16,
         "Shlomi Mor Wigs · 580 5th Avenue · New York, NY",
         font=F_SANS, size=10, color=C_MUTE, tracking=200, upper=True,
         align=PP_ALIGN.CENTER)
add_text(s, 72, 832, 1296, 16,
         "Brand Guidelines · Edition 01 · 2025",
         font=F_SANS, size=10, color=C_MUTE, tracking=200, upper=True,
         align=PP_ALIGN.CENTER)

out = "/tmp/Shlomi-Mor-Wigs-Brand-Guidelines.pptx"
prs.save(out)
print("OK", out)
