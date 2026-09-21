#!/usr/bin/env python3
"""Generate BC Vote Watch's icon set: a ballot with a check mark and a ballot-box slot.

    python3 scripts/make_icons.py     # needs Pillow

Writes favicon.svg, favicon.ico (16/32/48), apple-touch-icon.png, icon-192.png,
icon-512.png, icon-maskable-512.png and site.webmanifest at the site root.
The SVG and the bitmaps use the same geometry (64x64 grid).
"""
import json
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RED, NAVY, WHITE = (181, 18, 27), (37, 52, 74), (255, 255, 255)
SS = 16  # supersampling

# geometry on a 64 grid: (ballot x0,y0,x1,y1), check points, check stroke, slot bar
FULL = dict(ballot=(16, 9, 48, 42), check=[(23, 25), (30, 32), (41, 18)], stroke=6.5, bar=(10, 46, 54, 55))
SMALL = dict(ballot=(14, 8, 50, 44), check=[(21, 26), (29, 34), (43, 17)], stroke=9.0, bar=(9, 48, 55, 56))


def stroke(d, pts, w, fill, s):
    d.line([(x * s, y * s) for x, y in pts], fill=fill, width=int(w * s), joint="curve")
    for x, y in (pts[0], pts[-1]):
        r = w * s / 2
        d.ellipse((x * s - r, y * s - r, x * s + r, y * s + r), fill=fill)


def render(px, radius=14, scale=1.0, geo=None):
    """radius=0 gives a full-bleed square (Apple/maskable); scale shrinks the artwork inside the field."""
    geo = geo or (SMALL if px <= 20 else FULL)
    big = px * SS
    s = big / 64
    im = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, big - 1, big - 1), radius=radius * s, fill=RED)
    # optional inset: scale artwork about the centre
    def T(x, y):
        return (32 + (x - 32) * scale, 32 + (y - 32) * scale)
    b = geo["ballot"]
    x0, y0 = T(b[0], b[1]); x1, y1 = T(b[2], b[3])
    d.rounded_rectangle((x0 * s, y0 * s, x1 * s, y1 * s), radius=5 * scale * s, fill=WHITE)
    stroke(d, [T(*p) for p in geo["check"]], geo["stroke"] * scale, RED, s)
    r = geo["bar"]
    x0, y0 = T(r[0], r[1]); x1, y1 = T(r[2], r[3])
    d.rounded_rectangle((x0 * s, y0 * s, x1 * s, y1 * s), radius=4.5 * scale * s, fill=NAVY)
    return im.resize((px, px), Image.LANCZOS)


def svg():
    g = FULL
    b, r = g["ballot"], g["bar"]
    pts = " ".join(f"{x},{y}" for x, y in g["check"])
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="BC Vote Watch">'
        '<rect width="64" height="64" rx="14" fill="#b5121b"/>'
        f'<rect x="{b[0]}" y="{b[1]}" width="{b[2]-b[0]}" height="{b[3]-b[1]}" rx="5" fill="#fff"/>'
        f'<polyline points="{pts}" fill="none" stroke="#b5121b" stroke-width="{g["stroke"]}" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<rect x="{r[0]}" y="{r[1]}" width="{r[2]-r[0]}" height="{r[3]-r[1]}" rx="4.5" fill="#25344a"/>'
        "</svg>\n"
    )


def write_ico(path, images):
    """ICO container holding one PNG per size (Pillow only writes the base size)."""
    import io
    import struct

    blobs = []
    for im in images:
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        blobs.append((im.width, im.height, buf.getvalue()))
    head = struct.pack("<HHH", 0, 1, len(blobs))
    offset = 6 + 16 * len(blobs)
    entries, data = b"", b""
    for w, h, blob in blobs:
        entries += struct.pack("<BBBBHHII", w % 256, h % 256, 0, 0, 1, 32, len(blob), offset + len(data))
        data += blob
    with open(path, "wb") as f:
        f.write(head + entries + data)


def main():
    out = lambda n: os.path.join(ROOT, n)
    open(out("favicon.svg"), "w").write(svg())
    write_ico(out("favicon.ico"), [render(16), render(32), render(48)])
    render(180, radius=0, scale=0.92).convert("RGB").save(out("apple-touch-icon.png"))
    render(192).save(out("icon-192.png"))
    render(512).save(out("icon-512.png"))
    render(512, radius=0, scale=0.74).convert("RGB").save(out("icon-maskable-512.png"))
    manifest = {
        "name": "BC Vote Watch",
        "short_name": "BC Vote Watch",
        "description": "Independent, source-backed tracking of British Columbia provincial elections.",
        "start_url": "/",
        "display": "browser",
        "background_color": "#ffffff",
        "theme_color": "#b5121b",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    open(out("site.webmanifest"), "w").write(json.dumps(manifest, indent=1) + "\n")
    print("icons written")


if __name__ == "__main__":
    main()
