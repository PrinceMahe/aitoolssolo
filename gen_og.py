#!/usr/bin/env python3
"""Generate a branded default OG/Twitter share image (1200x630) for aitoolssolo.com."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 630
OUT = os.path.join(os.path.dirname(__file__), "static", "og-default.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

BG = (30, 31, 34)          # --theme dark
ACCENT = (124, 92, 252)    # violet
TEXT = (236, 236, 237)
MUTED = (155, 156, 157)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# accent bar
d.rectangle([0, 0, 12, H], fill=ACCENT)

def font(sz, bold=False):
    cands = [
        "C:/Windows/Fonts/SegoeUI%s.ttf" % ("-Bold" if bold else ""),
        "C:/Windows/Fonts/arial%s.ttf" % ("bd" if bold else ""),
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for c in cands:
        if os.path.exists(c):
            return ImageFont.truetype(c, sz)
    return ImageFont.load_default()

# Site name
d.text((80, 210), "AI Tools Solo", font=font(72, bold=True), fill=TEXT)
# Tagline
d.text((80, 310), "Smart AI Tools for Solopreneurs", font=font(40, bold=False), fill=MUTED)
# Sub
d.text((80, 400), "Real reviews. No fluff. Built for one-person businesses.", font=font(28), fill=MUTED)

# accent dot motif (top-right)
d.ellipse([1020, 90, 1110, 180], fill=ACCENT)
d.ellipse([1060, 150, 1130, 220], fill=(80, 60, 160))

img.save(OUT, "PNG")
print("wrote", OUT, img.size)
