#!/usr/bin/env python3
"""Generate assets/og-image.png (1200x630 social share card). Needs Pillow."""
import os
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RED, NAVY, WHITE = (181, 18, 27), (37, 52, 74), (255, 255, 255)
def font(size):
    for p in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()
im = Image.new("RGB", (1200, 630), NAVY)
d = ImageDraw.Draw(im)
d.rectangle((0, 0, 1200, 16), fill=RED)
d.text((80, 150), "BC VOTE WATCH", font=font(44), fill=(255, 190, 190))
d.text((80, 230), "BC Election 2026", font=font(110), fill=WHITE)
d.text((80, 370), "Polls · Candidates · Ridings", font=font(48), fill=WHITE)
d.text((80, 440), "How to vote · By-election results", font=font(48), fill=WHITE)
d.text((80, 545), "bcvotewatch.ca  |  Independent, sourced from Elections BC", font=font(30), fill=(200, 208, 220))
im.save(os.path.join(ROOT, "assets", "og-image.png"), optimize=True)
