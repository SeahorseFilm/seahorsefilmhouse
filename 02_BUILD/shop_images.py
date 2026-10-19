#!/usr/bin/env python3
"""Draws the illustrated shop mock-ups (tee, hoodie, cap) into source_images/.

Run:  python3 02_BUILD/shop_images.py   then rebuild the site with build.py.
These are drawings, not product photographs; replace them with real photos when the shop opens.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
OUT = HERE / "source_images"
LOGO = HERE.parent / "03_LOGO" / "sfh_logo_white.png"

S = 2            # drawn at twice the size, then reduced, for smooth edges
SIZE = 1200
BG = (229, 225, 216)
CLOTH = (28, 22, 22)
SHADE = (16, 12, 12)     # inside of a neck or hood, underside of a brim
SEAM = (50, 43, 42)
BONE = (241, 238, 232)


def bez(p0, p1, p2, p3=None, n=40):
    """Points along a quadratic (3 points) or cubic (4 points) curve."""
    pts = []
    for i in range(n + 1):
        t = i / n
        if p3 is None:
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        else:
            x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t ** 2 * p2[0] + t ** 3 * p3[0]
            y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t ** 2 * p2[1] + t ** 3 * p3[1]
        pts.append((x, y))
    return pts


def mirror(pts):
    return [(SIZE - x, y) for x, y in reversed(pts)]


def sc(pts):
    return [(x * S, y * S) for x, y in pts]


class Canvas:
    def __init__(self):
        self.im = Image.new("RGB", (SIZE * S, SIZE * S), BG)
        self.d = ImageDraw.Draw(self.im)

    def shadow(self, pts, dy=26, blur=34, strength=70):
        layer = Image.new("L", self.im.size, 0)
        ImageDraw.Draw(layer).polygon(sc([(x, y + dy) for x, y in pts]), fill=strength)
        layer = layer.filter(ImageFilter.GaussianBlur(blur * S))
        self.im.paste((120, 108, 96), (0, 0), layer)
        self.d = ImageDraw.Draw(self.im)

    def shape(self, pts, fill=CLOTH):
        self.d.polygon(sc(pts), fill=fill)

    def line(self, pts, fill=SEAM, width=2.5):
        self.d.line(sc(pts), fill=fill, width=round(width * S), joint="curve")

    def logo(self, cx, cy, width):
        logo = Image.open(LOGO).convert("RGBA")
        logo = logo.crop(logo.split()[-1].getbbox())
        w = round(width * S)
        logo = logo.resize((w, round(logo.height * w / logo.width)), Image.LANCZOS)
        tint = Image.new("RGB", logo.size, BONE)
        self.im.paste(tint, (round(cx * S - logo.width / 2), round(cy * S - logo.height / 2)), logo.split()[-1])
        self.d = ImageDraw.Draw(self.im)

    def text(self, cx, cy, words, size, spacing):
        font = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", round(size * S), index=10)  # Medium
        widths = [self.d.textlength(ch, font=font) for ch in words]
        total = sum(widths) + spacing * S * (len(words) - 1)
        x = cx * S - total / 2
        for ch, w in zip(words, widths):
            self.d.text((x, cy * S), ch, font=font, fill=BONE, anchor="lm")
            x += w + spacing * S

    def save(self, name):
        self.im.resize((SIZE, SIZE), Image.LANCZOS).save(OUT / name, "JPEG", quality=92, optimize=True)


def tee():
    """A loose, boxy tee: dropped shoulders, wide half sleeves, straight wide body."""
    c = Canvas()
    left = ([(505, 232)]
            + bez((505, 232), (380, 262), (262, 318))            # shoulder, sloping down and out
            + bez((262, 318), (176, 430), (128, 628))            # outside of the sleeve, hanging
            + bez((128, 628), (210, 668), (296, 676))            # sleeve opening
            + bez((296, 676), (318, 600), (332, 548))            # inside of the sleeve up to the underarm
            + bez((332, 548), (318, 800), (312, 1028)))          # side of the body
    hem = bez((312, 1028), (600, 1046), (888, 1028))
    outline = left + hem + mirror(left)
    c.shadow(outline)
    c.shape(outline)
    # neck: the back of the collar shows as a darker crescent, with a ribbed band in front
    c.shape(bez((505, 232), (600, 262), (695, 232)) + bez((695, 232), (600, 318), (505, 232)), fill=SHADE)
    c.line(bez((500, 233), (600, 326), (700, 233)), width=7)
    # soft folds where the loose cloth hangs from the underarm
    c.line(bez((338, 560), (372, 700), (360, 860)), width=2)
    c.line(mirror(bez((338, 560), (372, 700), (360, 860))), width=2)
    c.logo(600, 520, 228)
    c.save("_shop-tee.jpg")


def hoodie():
    """An oversize hoodie: hood, long dropped sleeves, front pocket, ribbed cuffs and hem."""
    c = Canvas()
    hood = (bez((452, 318), (430, 150), (600, 138)) + bez((600, 138), (770, 150), (748, 318)))
    left = ([(470, 300)]
            + bez((470, 300), (350, 322), (246, 372))            # shoulder
            + bez((246, 372), (150, 560), (120, 880))            # outside of the long sleeve
            + [(118, 938), (226, 952)]                           # cuff
            + bez((230, 890), (290, 720), (330, 590))            # inside of the sleeve up to the underarm
            + bez((330, 590), (312, 800), (316, 968))            # side of the body
            + [(330, 1040)])                                     # ribbed hem, drawn in slightly
    outline = left + mirror(left)
    c.shadow(hood + outline)
    c.shape(hood)
    c.shape(outline)
    # hood opening
    c.shape(bez((486, 318), (480, 196), (600, 190)) + bez((600, 190), (720, 196), (714, 318))
            + bez((714, 318), (600, 392), (486, 318)), fill=SHADE)
    c.line(bez((470, 306), (600, 404), (730, 306)), width=5)
    # drawstrings
    for x in (566, 634):
        c.line([(x, 372), (x + (4 if x > 600 else -4), 470)], fill=BONE, width=4)
    # ribbing at the cuffs and hem, front pocket
    c.line([(124, 880), (232, 896)], width=2.5)
    c.line(mirror([(124, 880), (232, 896)]), width=2.5)
    c.line([(318, 972), (882, 972)], width=2.5)
    pocket = [(446, 950)] + bez((446, 950), (440, 840), (486, 760)) + [(714, 760)] + bez((714, 760), (760, 840), (754, 950))
    c.line(pocket, width=2.5)
    c.logo(600, 520, 130)
    c.text(600, 628, "OPEN 24 HOURS", 38, 10)
    c.save("_shop-hoodie.jpg")


def cap():
    """A low, sporty tennis cap seen from the front, with a long curved peak."""
    c = Canvas()
    k = 1.3                                                  # drawn small, then enlarged about its centre
    grow = lambda pts: [(600 + (x - 600) * k, 620 + (y - 620) * k) for x, y in pts]
    crown = (bez((396, 716), (372, 470), (600, 452)) + bez((600, 452), (828, 470), (804, 716)))
    peak_top = bez((312, 808), (600, 596), (888, 808))      # where the peak meets the crown, curving down at the sides
    peak_bottom = bez((888, 808), (600, 742), (312, 808))
    crown, peak_top, peak_bottom = grow(crown), grow(peak_top), grow(peak_bottom)
    peak = peak_top + peak_bottom
    c.shadow(crown + peak_bottom, dy=30)
    c.shape(crown)
    # panel seams and the button on top
    seam = grow(bez((600, 456), (520, 540), (498, 700)))
    c.line(seam, width=2.5)
    c.line(mirror(seam), width=2.5)
    c.shape(grow(bez((578, 452), (600, 436), (622, 452)) + bez((622, 452), (600, 462), (578, 452))), fill=SHADE)
    c.shape(peak, fill=SHADE)
    c.line(peak_top, width=2.5)
    c.logo(600, 574, 190)
    c.save("_shop-cap.jpg")


if __name__ == "__main__":
    tee()
    hoodie()
    cap()
    print("Drew tee, hoodie and cap into", OUT)
