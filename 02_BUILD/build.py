#!/usr/bin/env python3
"""Builds the Seahorse Filmhouse site into ../01_SITE.

Run:  python3 02_BUILD/build.py
Films, news, team, shop products and site-wide details live in ../content (JSON); see CONTENT_EDITING.md.
This file holds the page layout, image processing, search-engine data and analytics consent.
"""
import hashlib
import html
import json
import re
import os
import shutil
import sys
from datetime import date
from pathlib import Path

from PIL import Image, features

from content_loader import ContentError, load_content

HERE = Path(__file__).parent
OUT = HERE.parent / "01_SITE"
SRC_IMG = HERE / "source_images"

SITE_URL = "https://seahorsefilmhouse.com"
FORM_ACTION = "https://formspree.io/f/movdyjgr"
# Visitor counting (Google Analytics). Put the Measurement ID here, e.g. "G-ABC123XYZ"; empty = off.
# Analytics loads only after the visitor presses Accept on the cookie notice.
GA_ID = "G-QYHK3HQZ3T"
YEAR = date.today().year
STAMP = __import__('time').strftime('%Y%m%d%H%M')  # cache-buster so browsers pick up new CSS/JS

CONTENT = HERE.parent / "content"
SHOP_PHOTOS = HERE / "shop_photos"

# Filled from the content/*.json files by main()
SITE, FILMS, NEWS, TEAM, PRODUCTS = {}, [], [], [], []
SOCIAL = {}  # only links that are filled in are shown; empty ones are skipped
IMAGE_ALT, IMAGE_JOBS = {}, []

CURRENT = ' class="current"'
CURRENT_PAGE = CURRENT + ' aria-current="page"'  # menu link of the page being shown
# how wide each kind of image is drawn, so the browser can choose a file (see the grid rules in site.css)
SIZES_POSTER = "(max-width: 900px) calc(50vw - 33px), 360px"
SIZES_CARD = "(max-width: 720px) calc(100vw - 48px), (max-width: 900px) calc(50vw - 39px), 360px"
SIZES_SHOP_ROW = "(max-width: 900px) calc(50vw - 39px), 270px"
SIZES_FILM_POSTER = "(max-width: 488px) calc(100vw - 48px), 440px"
SIZES_TEAM = "(max-width: 720px) calc(50vw - 35px), (max-width: 900px) calc(33vw - 31px), 210px"
NAV = [("Home", "index.html"), ("Films", "films.html"), ("News", "news.html"), ("Shop", "shop.html"), ("About", "about.html"), ("Contact", "contact.html")]


def stamp(uid, size=150):
    """The round Seahorse Filmhouse stamp as inline SVG (uses currentColor)."""
    return f"""<svg class="stamp" width="{size}" height="{size}" viewBox="0 0 250 250" role="img" aria-label="Seahorse Filmhouse">
<defs><path id="ring-{uid}" d="M125,125 m-96,0 a96,96 0 1,1 192,0 a96,96 0 1,1 -192,0"/></defs>
<circle cx="125" cy="125" r="120" fill="none" stroke="currentColor" stroke-width="0.9"/>
<text font-family="Cormorant Garamond, serif" font-weight="500" font-size="13" letter-spacing="7.45" fill="currentColor"><textPath href="#ring-{uid}">SEAHORSE FILMHOUSE &#8226; INDEPENDENT CINEMA &#8226;</textPath></text>
<text x="125" y="150" text-anchor="middle" font-family="Bodoni Moda, serif" font-weight="900" font-size="82" letter-spacing="-2.6" fill="currentColor" style="font-optical-sizing:none;font-variation-settings:'opsz' 96">sf<tspan dx="7.4">h</tspan></text>
</svg>"""


COUNTER = """<div class="cookie-note" id="cookie-note" role="region" aria-label="Cookie notice" hidden>
  <p>We use Google Analytics cookies to count visits to this site. Is that all right?</p>
  <div><button type="button" data-consent="no">Decline</button><button type="button" data-consent="yes">Accept</button></div>
</div>
<script>
(function () {
  var KEY = "sfh-analytics", note = document.getElementById("cookie-note"), choice = null;
  try { choice = localStorage.getItem(KEY); } catch (e) {}
  function start() {
    var s = document.createElement("script");
    s.async = true; s.src = "https://www.googletagmanager.com/gtag/js?id=GA_ID";
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { dataLayer.push(arguments); };
    gtag("js", new Date()); gtag("config", "GA_ID");
  }
  if (choice === "yes") { start(); return; }
  if (choice === "no") { return; }
  note.hidden = false;
  note.addEventListener("click", function (e) {
    var c = e.target.getAttribute("data-consent");
    if (!c) { return; }
    try { localStorage.setItem(KEY, c); } catch (err) {}
    note.hidden = true;
    // the buttons are gone, so keyboard focus moves on to the page itself
    document.getElementById("main").focus({ preventScroll: true });
    if (c === "yes") { start(); }
  });
})();
</script>"""


def plain(film):
    return film.get("plain_title", film["title"])


def text_only(markup):
    """Plain text from a snippet of page markup, for descriptions and search-engine data."""
    return html.unescape(re.sub(r"<[^>]+>", "", markup)).replace("\u2019", "'")


def image_alt(name):
    """A short description of a site image, read out by screen readers and used by image search (from content/)."""
    return IMAGE_ALT[name]


def ld(data):
    """Structured data for search engines (not shown on the page)."""
    data = {"@context": "https://schema.org", **data}
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


ORG = {"@type": "Organization", "name": "Seahorse Filmhouse", "url": f"{SITE_URL}/"}


def nice_date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return date(y, m, d).strftime("%-d %B %Y")


def page(path, title, description, body, current="", image="share.jpg", search_title="", head="",
         og_type="website", og_extra="", image_alt="", robots=""):
    """Wrap body in the shared layout and write it to OUT/path."""
    depth = path.count("/")
    root = "../" * depth
    links = [f'<a href="{root}{href}"{CURRENT_PAGE if href == current else ""}>{label}</a>' for label, href in NAV]
    half = (len(links) + 1) // 2
    # two groups, so the logo can sit in the centre of the header between them
    nav = f'<span class="g">{"".join(links[:half])}</span><span class="g">{"".join(links[half:])}</span>'
    social = "".join(
        f'<li><a href="{url}" target="_blank" rel="noopener">{name}</a></li>' for name, url in SOCIAL.items() if url
    )
    social_block = f'<div><h2 class="foot-h">Follow</h2><ul>{social}</ul></div>' if social else (
        f'<div><h2 class="foot-h">Stay in touch</h2><ul><li><a href="{root}index.html#signup">Join the mailing list</a></li>'
        f'<li><a href="{root}contact.html">Contact us</a></li></ul></div>'
    )
    counter = COUNTER.replace("GA_ID", GA_ID) if GA_ID else ""
    # the notice sits first in the page so keyboard users reach it straight away; it is fixed to the foot of the screen
    counter_note, counter = (counter.split("</div>\n<script>", 1) if counter else ("", ""))
    if counter:
        counter_note, counter = counter_note + "</div>", "<script>" + counter
    full_title = "Seahorse Filmhouse" if not title else f"{title} | Seahorse Filmhouse"
    # search_title is the longer line shown in search results and on the browser tab
    tab_title = (search_title if search_title.startswith("Seahorse Filmhouse")
                 else f"{search_title} | Seahorse Filmhouse" if search_title else full_title)
    description = description.replace('"', "&quot;")
    image_alt = (image_alt or full_title).replace('"', "&quot;")
    size = PIC.get(image, {})
    og_size = (f'\n<meta property="og:image:width" content="{size["w"]}">\n<meta property="og:image:height" content="{size["h"]}">'
               if size else "")
    robots = f'\n<meta name="robots" content="{robots}">' if robots else ""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{tab_title}</title>
<meta name="description" content="{description}">{robots}
<meta name="google-site-verification" content="RyrXxN7FP37vGVC3hiQqt4avTftQgCJ8jtQxv17IyrA">
<link rel="canonical" href="{SITE_URL}/{'' if path == 'index.html' else path}">
<meta property="og:site_name" content="Seahorse Filmhouse">
<meta property="og:title" content="{full_title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{SITE_URL}/{'' if path == 'index.html' else path}">
<meta property="og:image" content="{SITE_URL}/images/{image}">{og_size}
<meta property="og:image:alt" content="{image_alt}">{og_extra}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image:alt" content="{image_alt}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600&family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..900;1,6..96,400&family=Cormorant+Garamond:wght@500&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="icon" type="image/png" sizes="48x48" href="{img_url("icon-48.png", root)}">
<link rel="icon" type="image/png" sizes="512x512" href="{img_url("icon-512.png", root)}">
<link rel="apple-touch-icon" href="{img_url("icon-180.png", root)}">
<link rel="stylesheet" href="{root}css/site.css?v={STAMP}">
{head}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{counter_note}
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{root}index.html"><span class="m" aria-hidden="true">s<span class="f">f</span>h</span><span class="s">Seahorse Filmhouse</span></a>
    <button class="nav-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="site-nav"><span></span><span></span><span></span></button>
    <nav class="nav" id="site-nav" aria-label="Main">{nav}</nav>
  </div>
</header>
<main id="main" tabindex="-1">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <a class="footer-stamp" href="{root}index.html">{stamp("footer")}</a>
        <p>{"<br>".join(SITE["footer_lines"])}</p>
      </div>
      <div>
        <h2 class="foot-h">Explore</h2>
        <ul>
          <li><a href="{root}index.html">Home</a></li>
          <li><a href="{root}films.html">Films</a></li>
          <li><a href="{root}news.html">News</a></li>
          <li><a href="{root}shop.html">Shop</a></li>
          <li><a href="{root}about.html">About</a></li>
          <li><a href="{root}contact.html">Contact</a></li>
        </ul>
      </div>
      {social_block}
    </div>
    <p class="copyright">&copy; {YEAR} Seahorse Filmhouse. All rights reserved.</p>
  </div>
</footer>
<div class="modal" id="trailer-modal" role="dialog" aria-modal="true" aria-label="Trailer" hidden>
  <button class="close" type="button" aria-label="Close trailer">&times;</button>
  <div class="frame"><iframe src="" title="Trailer" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    <a class="yt-link" href="#" target="_blank" rel="noopener">Not playing? Watch on YouTube &rarr;</a></div>
</div>
<script src="{root}js/site.js?v={STAMP}"></script>
{counter}
</body>
</html>
"""
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")


def film_card(film, root=""):
    line = f'Directed by {film["director"]}' if film.get("director") else film["stage"]
    return f"""<a class="film-card" href="{root}films/{film['slug']}.html">
  <div class="poster">{picture(film['poster'], root, image_alt(film['poster']), SIZES_POSTER)}</div>
  <div class="meta"><span class="year">{film['year']}</span><h3>{film['title']}</h3><p>{line}</p></div>
</a>"""


def shop_card(pr, root=""):
    """Home page shop row: one product, its model photo where there is one, linking to it on the Shop page."""
    images = pr["images"]
    pick = next((im for im, src in zip(images, pr["photos"]) if "model" in src), images[0])
    return f"""<a class="shop-card" href="{root}shop.html#{pr['slug']}">
  <div class="shot">{picture(pick, root, pr['name'], SIZES_SHOP_ROW)}</div>
  <div class="meta"><h3>{pr['name']}</h3><span class="soon">{pr['price'] if pr['availability'] == 'available' else 'Coming soon'}</span></div>
</a>"""


def news_card(post, root="", h="h3"):
    """h: heading level of the card title, one below the heading of the section the card sits in."""
    return f"""<a class="news-card" href="{root}news/{post['slug']}.html">
  <div class="thumb">{picture(post['image'], root, image_alt(post['image']), SIZES_CARD)}</div>
  <div class="body"><time datetime="{post['date']}">{nice_date(post['date'])}</time><{h}>{post['title']}</{h}><p>{post['summary']}</p></div>
</a>"""


def signup_block(root="", heading="Be the first to know", text="Release dates, festival screenings and new projects, sent only when there is something to say."):
    return f"""<section class="block tint" id="signup">
  <div class="wrap signup">
    <div>
      <p class="eyebrow">Mailing list</p>
      <h2>{heading}</h2>
      <p class="muted" style="margin-top:14px">{text}</p>
    </div>
    <div>
      <form action="{FORM_ACTION}" method="POST">
        <input type="hidden" name="_subject" value="Mailing list sign-up (seahorsefilmhouse.com)">
        <input type="hidden" name="form" value="Mailing list sign-up">
        <input type="hidden" name="_next" value="{SITE_URL}/thank-you.html">
        <input type="text" name="_gotcha" style="display:none" tabindex="-1" autocomplete="off">
        <input class="field" type="email" name="email" placeholder="Your email address" aria-label="Email address" required>
        <button class="btn primary" type="submit">Join</button>
      </form>
      <p class="note">We will only use your email to send Seahorse Filmhouse updates.</p>
    </div>
  </div>
</section>"""


# Every image is also written at smaller widths and as AVIF and WebP, so each browser downloads the smallest
# copy that is still sharp on its screen. The full-size JPEG keeps its old name: share previews and search data use it.
HAS_AVIF = features.check("avif")
WIDTHS = (150, 350, 400, 450, 600, 640, 720, 960, 1280, 1920, 2560)
PIC = {}  # output name -> {"w", "h", "v", "sizes": [widths], "formats": [...]}, filled as images are written
BLANK = "data:image/gif;base64,R0lGODlhAQABAAAAACw="  # stand-in for hero images that load after the page


def save_image(im, name, widths=(), quality=82, copy_from=None, avif=65, webp=86, **jpeg):
    """Write `name` (full-size JPEG) plus the smaller widths listed, each as JPEG, AVIF and WebP.
    copy_from: use that file unchanged as the full-size JPEG instead of re-encoding it."""
    out = OUT / "images"
    stem = name.rsplit(".", 1)[0]
    if copy_from:
        shutil.copy(copy_from, out / name)
    else:
        im.save(out / name, "JPEG", quality=quality, optimize=True, progressive=True, **jpeg)
    sizes = sorted({w for w in widths if w < im.width} | {im.width})
    formats = (["avif"] if HAS_AVIF and avif else []) + (["webp"] if webp else [])
    for w in sizes:
        small = im if w == im.width else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        if w != im.width:
            small.save(out / f"{stem}-{w}.jpg", "JPEG", quality=quality, optimize=True, progressive=True, **jpeg)
        base = stem if w == im.width else f"{stem}-{w}"
        if "avif" in formats:
            small.save(out / f"{base}.avif", "AVIF", quality=avif, speed=6,
                       subsampling="4:4:4" if jpeg.get("subsampling") == 0 else "4:2:0")
        if "webp" in formats:
            small.save(out / f"{base}.webp", "WEBP", quality=webp, method=6)
    # short fingerprint of the picture: changes when the image does, so browsers may cache images for a long time
    v = hashlib.md5((out / name).read_bytes()).hexdigest()[:8]
    PIC[name] = {"w": im.width, "h": im.height, "v": v, "sizes": sizes, "formats": formats}


def srcset(name, root, fmt):
    info, stem = PIC[name], name.rsplit(".", 1)[0]
    return ", ".join(f"{root}images/{stem if w == info['w'] else f'{stem}-{w}'}.{fmt}?v={info['v']} {w}w"
                     for w in info["sizes"])


def picture(name, root, alt, sizes, lazy=True, high=False, defer=False, phone=None):
    """<picture> for a site image: AVIF, then WebP, then JPEG, each at several widths, with the image's own
    width and height so the page does not jump while it loads.
    defer: leave the files for site.js to fetch once the page has loaded (the hero images not shown first).
    phone: (name, sizes) of a different crop used on tall, narrow screens."""
    info = PIC[name]
    # deferred: a blank placeholder now, the real files in data-srcset for site.js
    pre = f'srcset="{BLANK}" data-' if defer else ""
    sources = ""
    if phone:
        for fmt in PIC[phone[0]]["formats"] + ["jpg"]:
            kind = "jpeg" if fmt == "jpg" else fmt
            sources += (f'<source media="(max-aspect-ratio: 4/5)" type="image/{kind}" '
                        f'{pre}srcset="{srcset(phone[0], root, fmt)}" sizes="{phone[1]}">')
    for fmt in info["formats"]:
        sources += f'<source type="image/{fmt}" {pre}srcset="{srcset(name, root, fmt)}" sizes="{sizes}">'
    src = f'{root}images/{name}?v={info["v"]}'
    load = (' loading="lazy"' if lazy else "") + (' fetchpriority="high"' if high else "")
    img = (f'<img src="{BLANK}" data-src="{src}" data-srcset="{srcset(name, root, "jpg")}"' if defer
           else f'<img src="{src}" srcset="{srcset(name, root, "jpg")}"')
    return (f'<picture>{sources}{img} sizes="{sizes}" width="{info["w"]}" height="{info["h"]}" '
            f'alt="{alt}"{load} decoding="async"></picture>')


def cover_sizes(name, extra="0px", height="100vh"):
    """`sizes` for an image that fills a box (background-style, cropped to fit) of 100vw + extra by height + extra:
    on screens narrower than the picture, its width is set by the height of the box."""
    info = PIC[name]
    return (f"(max-aspect-ratio: {info['w']}/{info['h']}) calc(({height} + {extra}) * {info['w'] / info['h']:.3f}), "
            f"calc(100vw + {extra})")


def img_url(name, root=""):
    """Plain URL of the full-size JPEG, with its fingerprint."""
    return f"{root}images/{name}?v={PIC[name]['v']}"


# How each kind of picture in content/ is processed: widest size kept, the smaller widths also written, and the
# colour treatment. The kind is set by where the picture is used (poster, stills, team photo, ...).
TREATMENTS = {
    "poster": dict(width=900, widths=(400, 600)),
    "still": dict(width=1920, widths=(640, 960, 1280), enhance=True),  # a touch more punch for film stills
    "portrait": dict(width=700, widths=(350, 400, 600)),
    "news": dict(width=1920, widths=(640, 960, 1280)),
}
# full-screen hero pictures: the sources can be small, so they are enlarged and sharpened; "lead" is a film page's
# own lead image where it is not a still
HERO_WIDTHS = {"home": (960, 1280), "lead": (640, 960, 1280)}


def save_phone_hero(source, name):
    """Phone version of the panoramic Tokyo image: on a tall, narrow screen the wide picture would lose both
    sides, so it is shown whole-ish as a band, zoomed out, over a blurred copy of itself."""
    from PIL import ImageEnhance, ImageFilter
    wide = Image.open(SRC_IMG / source).convert("RGB")
    if wide.width >= 3000:
        crop_w = round(wide.height * 1.6)
        left = round(wide.width * 0.175)
        band = wide.crop((left, 0, left + crop_w, wide.height)).resize((1080, 675), Image.LANCZOS)
        W, H = 1080, 2100
        fill = band.resize((round(H * 1.6), H), Image.LANCZOS)
        fill = fill.crop(((fill.width - W) // 2, 0, (fill.width - W) // 2 + W, H))
        fill = fill.filter(ImageFilter.GaussianBlur(46))
        fill = ImageEnhance.Brightness(fill).enhance(0.55)
        mask = Image.new("L", band.size, 255)
        feather = 70
        for y in range(feather):
            v = round(255 * y / feather)
            mask.paste(v, (0, y, band.width, y + 1))
            mask.paste(v, (0, band.height - 1 - y, band.width, band.height - y))
        fill.paste(band, (0, 520), mask)
        save_image(fill, name, (720,), quality=88)


def build_images():
    out = OUT / "images"
    out.mkdir(parents=True, exist_ok=True)
    from PIL import ImageEnhance, ImageFilter
    for job in IMAGE_JOBS:
        name, role = job["file"], job["role"]
        im = Image.open(SRC_IMG / job["source"]).convert("RGB")
        if role == "shop":
            # the book photo is already finished: copied as it is
            save_image(im, name, (150, 450, 900), copy_from=SRC_IMG / job["source"])
        elif role in HERO_WIDTHS:
            if im.width >= 3000:
                # already high resolution (the 4K panoramic Tokyo image): keep it at its original size and
                # save with full colour detail, at Raj's request (AVIF also keeps full colour; WebP cannot, so none)
                save_image(im, name, (1280, 1920, 2560), quality=92, subsampling=0, avif=85, webp=0)
            else:
                im = im.resize((1920, round(im.height * 1920 / im.width)), Image.LANCZOS)
                im = im.filter(ImageFilter.UnsharpMask(radius=2.4, percent=150, threshold=2))
                save_image(im, name, HERO_WIDTHS[role], quality=84)
            if job["phone"]:
                save_phone_hero(job["phone"]["source"], job["phone"]["file"])
        else:
            t = TREATMENTS[role]
            if im.width > t["width"]:
                im = im.resize((t["width"], round(im.height * t["width"] / im.width)), Image.LANCZOS)
            if t.get("enhance"):
                im = ImageEnhance.Brightness(im).enhance(1.06)
                im = ImageEnhance.Contrast(im).enhance(1.12)
                im = ImageEnhance.Color(im).enhance(1.18)
            save_image(im, name, t["widths"])
    shutil.copy(SRC_IMG / "_share.jpg", out / "share.jpg")
    with Image.open(SRC_IMG / "_share.jpg") as im:
        PIC["share.jpg"] = {"w": im.width, "h": im.height}
    for size in (48, 180, 512):
        shutil.copy(SRC_IMG / f"_icon-{size}.png", out / f"icon-{size}.png")
        PIC[f"icon-{size}.png"] = {"w": size, "h": size, "v": hashlib.md5((out / f"icon-{size}.png").read_bytes()).hexdigest()[:8]}


def build_home():
    released = [f for f in FILMS if f["status"] == "released"]
    upcoming = [f for f in FILMS if f["status"] == "upcoming"]
    # Hero: every film as a line of the list, in the order of content/films.json; hovering a title brings its
    # image into focus.
    layers = titles = notes = ""
    for i, f in enumerate(FILMS):
        slug = f["slug"]
        active = " active" if i == 0 else ""
        soft = " soft" if f["status"] == "upcoming" else ""
        img = f["home_image"]
        year = f["year"] if f["year"].isdigit() else "Soon"
        # only the first film's image loads with the page; site.js fetches the others once the page has loaded
        phone = (f["home_phone"], cover_sizes(f["home_phone"], "120px")) if f.get("home_phone") else None
        pic = picture(img, "", "", cover_sizes(img, "120px"), lazy=False, high=i == 0, defer=i > 0, phone=phone)
        layers += f"""<div class="hero-bg bg-{slug}{soft}{active}">{pic}</div>\n"""
        titles += (f"""<a class="hero-title{active}" href="films/{slug}.html" data-i="{i}">"""
                   f"""<span class="t">{f['title']}</span><span class="y">{year}</span></a>\n""")
        # released films show the tagline only; upcoming ones also show their status
        action = "" if f.get("trailer") else f"""<a class="text-link" href="films/{slug}.html">{f['stage']}</a>"""
        notes += f"""<div class="hero-note{active}"><p class="tagline">{f['tagline']}</p>{action}</div>\n"""

    body = f"""<section class="hero" id="hero">
{layers}<div class="hero-shade"></div>
<div class="hero-inner wrap">
  <nav class="hero-list" aria-label="Films">
{titles}  </nav>
  <div class="hero-notes">
{notes}  </div>
</div>
</section>

<section class="block tint">
  <div class="wrap statement">
    <p class="eyebrow">Independent film production</p>
    <p>Seahorse Filmhouse crafts bold, evocative cinema that lingers in the mind and stirs the soul: intimate dramas,
    socially conscious stories, and narratives that challenge perception and invite reflection.</p>
    <p>Our films have been recognized at international festivals and released on global platforms.</p>
    <a class="text-link" href="about.html">About the company &rarr;</a>
  </div>
</section>

<section class="block alt">
  <div class="wrap">
    <div class="section-head">
      <div><p class="eyebrow">Latest</p><h2>News</h2></div>
      <a class="text-link" href="news.html">All news &rarr;</a>
    </div>
    <div class="grid three">{''.join(news_card(p) for p in NEWS[:3])}</div>
  </div>
</section>

<section class="block">
  <div class="wrap">
    <div class="section-head">
      <div><p class="eyebrow">In production</p><h2>Coming next</h2></div>
    </div>
    <div class="grid three posters">{''.join(film_card(f) for f in upcoming)}</div>
  </div>
</section>

<section class="block" style="padding-top:0">
  <div class="wrap">
    <div class="section-head">
      <div><p class="eyebrow">Released</p><h2>Films</h2></div>
      <a class="text-link" href="films.html">All films &rarr;</a>
    </div>
    <div class="grid three posters">{''.join(film_card(f) for f in released)}</div>
  </div>
</section>

<section class="block alt" id="shop-row">
  <div class="wrap">
    <div class="section-head">
      <div><p class="eyebrow">Shop</p><h2>Objects from the filmhouse</h2></div>
      <a class="text-link" href="shop.html">Visit the shop &rarr;</a>
    </div>
    <div class="grid four home-shop">{''.join(shop_card(pr) for pr in PRODUCTS if pr.get('images'))}</div>
  </div>
</section>

{signup_block()}"""
    org = ld({**ORG, "logo": f"{SITE_URL}/images/icon-512.png", "foundingDate": SITE["founding_year"],
              "description": SITE["org_description"],
              "sameAs": [url for url in SOCIAL.values() if url]})
    site = ld({"@type": "WebSite", "name": "Seahorse Filmhouse", "url": f"{SITE_URL}/"})
    page("index.html", "",
         "Seahorse Filmhouse is an independent film production company with operations in Los Angeles, "
         "London, Mumbai and the UAE. Films include Open 24 Hours, Dark Light and Daddy's Girl.",
         body, current="index.html", head=org + "\n" + site,
         search_title="Seahorse Filmhouse: Independent Film Production Company")


def build_films():
    released = [f for f in FILMS if f["status"] == "released"]
    upcoming = [f for f in FILMS if f["status"] == "upcoming"]
    body = f"""<section class="page-head"><div class="wrap">
  <p class="eyebrow">Our work</p><h1>Films</h1>
  <p class="lead">Three released features, selected for festivals including Sitges, FrightFest, Fantastic Fest and Raindance, and three projects on the way.</p>
</div></section>
<section class="block">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">In production</p><h2>Coming next</h2></div></div>
    <div class="grid three posters">{''.join(film_card(f) for f in upcoming)}</div>
  </div>
</section>
<section class="block" style="padding-top:0">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">Released</p><h2>Feature films</h2></div></div>
    <div class="grid three posters">{''.join(film_card(f) for f in released)}</div>
  </div>
</section>
{signup_block()}"""
    page("films.html", "Films",
         "Films from Seahorse Filmhouse: Open 24 Hours, Dark Light, Daddy's Girl, and the upcoming Chasm, Tokyo and Winter Dreams.",
         body, current="films.html", search_title="Films: Open 24 Hours, Dark Light, Daddy's Girl and more")

    for f in FILMS:
        # the film's own page leads with a different image from the one used on the home page
        bg = f["page_hero"]
        def credit(label, value):
            return f'<div><span>{label}</span><strong>{value}</strong></div>'

        if f["status"] == "released":
            credits = (credit("Directed by", f["director"]) + credit("Year", f["year"])
                       + credit("Running time", f["runtime"]) + credit("Genre", f["genre"]))
            accolades = "".join(f'<li class="{c}">{t}</li>' for c, t in f["accolades"])
            watch_rows = "".join(
                f"<div><dt>{label}</dt><dd>" + " &middot; ".join(
                    f'<a href="{url}" target="_blank" rel="noopener">{name}</a>' for name, url in services) + "</dd></div>"
                for label, services in f["watch"])
            centre = f"""<p class="synopsis">{f['synopsis']}</p>
<div class="film-poster">{picture(f['poster'], "../", image_alt(f['poster']), SIZES_FILM_POSTER)}</div>
<p class="sub-head">Where to watch <span class="where">United States</span></p>
<dl class="watch">{watch_rows}</dl>
<p class="watch-more"><a href="{f['watch_url']}" target="_blank" rel="noopener">All current options &rarr;</a></p>
<p class="sub-head">Festivals and awards</p>
<ul class="accolades">{accolades}</ul>"""
            after = ""
            desc = (f"{plain(f)} ({f['year']}), directed by {f['director']}, with {f['cast'][0]}. "
                    f"{text_only(f['synopsis'])} Watch the trailer and see where to stream it.")
            search_title = f"{plain(f)} ({f['year']}): Trailer and Where to Watch"
        else:
            credits = (credit("Status", f["stage"])
                       + (credit("Directed by", f["director"]) if f.get("director") else "")
                       + (credit("Running time", f["runtime"]) if f.get("runtime") else "")
                       + (credit("Languages", f["languages"]) if f.get("languages") else "")
                       + ("" if f.get("runtime") else credit("Produced by", "Seahorse Filmhouse")))
            centre = f"""<p class="synopsis">{f['synopsis']}</p>
<div class="film-poster">{picture(f['poster'], "../", image_alt(f['poster']), SIZES_FILM_POSTER)}</div>
{'<p class="muted concept-note">Images shown are concept artwork; the film has not yet been shot.</p>' if f.get("concept_art") else ''}
<p class="muted">Updates on this project are posted in <a href="../news.html" style="color:var(--accent)">News</a> and sent to the mailing list.</p>
<div class="btn-row" style="margin-top:26px"><a class="btn primary" href="#signup">Get updates</a><a class="btn" href="../contact.html">Distribution and press enquiries</a></div>"""
            after = signup_block("../", f"Follow {f['title']}", "Join the mailing list and we will tell you when there is news on this film.")
            first = re.split(r"(?<=[a-z])\. ", text_only(f["synopsis"]))[0].rstrip(".") + "."
            by = f", directed by {f['director']}" if f.get("director") else ""
            desc = f"{plain(f)}, an upcoming film from Seahorse Filmhouse{by}. {f['stage']}. {first}"
            search_title = f"{plain(f)}: Upcoming Film, {f['stage'].title()}"

        # released films: the trailer plays from a thin play mark on the lead image, in an overlay
        play = (f"""<a class="play" href="https://www.youtube.com/watch?v={f['trailer']}" data-trailer="{f['trailer']}" aria-label="Play the {plain(f)} trailer">
  <svg viewBox="0 0 100 100" aria-hidden="true"><polygon points="30,14 86,50 30,86"/></svg></a>"""
                if f.get("trailer") else "")
        hero = picture(bg, "../", "", cover_sizes(bg, height="80vh"), lazy=False, high=True)
        body = f"""<section class="film-hero tall bg-{f['slug']}">{hero}{play}<div class="wrap">
  <h1>{f['title']}{' <span class="title-note">(' + f['title_note'] + ')</span>' if f.get('title_note') else ''}</h1>
  <p class="tagline">{f['tagline']}</p>
</div></section>
<section class="film-credits"><div class="wrap">{credits}</div></section>
<section class="block tight">
  <div class="wrap"><div class="film-centre">{centre}</div></div>
</section>
{after}
<section class="block tight"><div class="wrap"><a class="text-link" href="../films.html">&larr; All films</a></div></section>"""
        movie = {"@type": "Movie", "name": plain(f), "url": f"{SITE_URL}/films/{f['slug']}.html",
                 "image": f"{SITE_URL}/images/{f['poster']}", "description": text_only(f["synopsis"]),
                 "productionCompany": ORG}
        if f.get("director"):
            movie["director"] = {"@type": "Person", "name": f["director"]}
        if f["status"] == "released":
            movie["dateCreated"] = f["year"]
            movie["genre"] = f["genre"]
            movie["duration"] = f"PT{f['runtime'].split()[0]}M"
            movie["actor"] = [{"@type": "Person", "name": n} for n in f["cast"]]
            movie["trailer"] = {"@type": "VideoObject", "name": f"{plain(f)} trailer",
                                "description": f"Official trailer for {plain(f)} ({f['year']}).",
                                "thumbnailUrl": f"https://i.ytimg.com/vi/{f['trailer']}/hqdefault.jpg",
                                "uploadDate": f["trailer_date"],
                                "contentUrl": f"https://www.youtube.com/watch?v={f['trailer']}",
                                "embedUrl": f"https://www.youtube.com/embed/{f['trailer']}"}
        page(f"films/{f['slug']}.html", plain(f), desc, body, current="films.html", image=bg,
             search_title=search_title, head=ld(movie), og_type="video.movie", image_alt=image_alt(bg))


def post_body(p):
    """A news post's paragraphs, then its source links, as page markup."""
    parts = [f"<p>{text}</p>" for text in p["body"]]
    if p["sources"]:
        links = " &middot; ".join(f'<a href="{url}" target="_blank" rel="noopener">{label}</a>' for label, url in p["sources"])
        parts.append(f'<p class="source">{"Source" if len(p["sources"]) == 1 else "Sources"}: {links}</p>')
    return "\n" + "\n".join(parts) + "\n"


def build_news():
    body = f"""<section class="page-head"><div class="wrap">
  <p class="eyebrow">Latest</p><h1>News</h1>
  <p class="lead">Updates on our films, festival screenings and new projects.</p>
</div></section>
<section class="block"><div class="wrap"><div class="grid three">{''.join(news_card(p, h="h2") for p in NEWS)}</div></div></section>
{signup_block()}"""
    page("news.html", "News", "News and updates from Seahorse Filmhouse: films, festivals and new projects.",
         body, current="news.html")

    for p in NEWS:
        portrait = p["image"].startswith("poster-")
        img_style = ' style="max-width:360px"' if portrait else ""
        post_sizes = "(max-width: 408px) calc(100vw - 48px), 360px" if portrait else "(max-width: 760px) calc(100vw - 48px), 712px"
        body = f"""<section class="page-head"><div class="wrap post">
  <time datetime="{p['date']}">{nice_date(p['date'])}</time>
  <h1 style="margin-top:12px;font-size:clamp(2rem,4.6vw,3.2rem)">{p['title']}</h1>
</div></section>
<section class="block tight"><div class="wrap post">
  <div class="post-image"{img_style}>{picture(p['image'], "../", image_alt(p['image']), post_sizes, lazy=False, high=True)}</div>
  <div class="post-body">{post_body(p)}</div>
  <p style="margin-top:40px"><a class="text-link" href="../news.html">&larr; All news</a></p>
</div></section>
{signup_block("../")}"""
        article = ld({"@type": "NewsArticle", "headline": text_only(p["title"]), "datePublished": p["date"],
                      "image": f"{SITE_URL}/images/{p['image']}", "description": p["summary"],
                      "author": ORG, "publisher": ORG,
                      "mainEntityOfPage": f"{SITE_URL}/news/{p['slug']}.html"})
        page(f"news/{p['slug']}.html", p["title"], p["summary"], body, current="news.html", image=p["image"], head=article,
             og_type="article", og_extra=f'\n<meta property="article:published_time" content="{p["date"]}">',
             image_alt=image_alt(p["image"]))


def build_about():
    people = "".join(
        f"""<div class="person">
  <div class="photo">{picture(t["photo"], "", t["alt"], SIZES_TEAM)}</div>
  <h3>{t["name"]}</h3><p>{t["role"]}</p>
  <a class="text-link" href="{t["imdb"]}" target="_blank" rel="noopener">IMDb</a>
</div>""" for t in TEAM
    )
    locations = "\n".join(f"      <div><strong>{place}</strong><span>{country}</span></div>" for place, country in SITE["locations"])
    body = f"""<section class="page-head"><div class="wrap">
  <p class="eyebrow">About</p><h1>A studio of ideas</h1>
  <p class="lead">Seahorse Filmhouse is an independent production company with operations in Los Angeles, London, Mumbai and the UAE.</p>
</div></section>
<section class="block">
  <div class="wrap about-intro">
  <div class="statement">
    <p>Seahorse Filmhouse is an independent production company crafting bold, evocative cinema that lingers in the mind
    and stirs the soul. Our work explores intimate dramas, socially conscious stories, and narratives that challenge
    perception and invite reflection.</p>
    <p>Our films, recognized at international festivals and on global platforms, balance narrative depth with striking
    visual precision.</p>
    <p>At our core, we are a studio of ideas. We champion the strange, the beautiful, and the poetic, shaping them into
    films that leave a lasting mark.</p>
  </div>
  <div class="about-stamp">{stamp("about", 220)}</div>
  </div>
</section>
<section class="block alt">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">Where we work</p><h2>Four places</h2></div></div>
    <div class="locations">
{locations}
    </div>
  </div>
</section>
<section class="block">
  <div class="wrap">
    <div class="section-head"><div><p class="eyebrow">People</p><h2>The creative collective</h2></div></div>
    <div class="grid five">{people}</div>
  </div>
</section>
<section class="block alt">
  <div class="wrap signup">
    <div><p class="eyebrow">Press and partners</p><h2>Working with us</h2></div>
    <div>
      <p class="muted">For distribution, festival programming, co-production and press enquiries, write to us and we will
      send the materials you need.</p>
      <a class="btn" href="contact.html">Get in touch</a>
    </div>
  </div>
</section>"""
    page("about.html", "About",
         "About Seahorse Filmhouse, an independent film production company with operations in Los Angeles, London, Mumbai and the UAE.",
         body, current="about.html")


def build_contact():
    options = "".join(f"<option>{o}</option>" for o in SITE["enquiry_subjects"])
    follow = " &nbsp;&middot;&nbsp; ".join(
        f'<a class="text-link" href="{url}" target="_blank" rel="noopener">{name}</a>' for name, url in SOCIAL.items() if url)
    body = f"""<section class="page-head"><div class="wrap">
  <p class="eyebrow">Contact</p><h1>Get in touch</h1>
  <p class="lead">Have a question or a project idea, or want to talk about one of our films? We would love to hear from you.</p>
</div></section>
<section class="block">
  <div class="wrap contact-layout">
    <div>
      <p class="sub-head">Operating in</p>
      <p>{SITE["operating_in"]}</p>
      <p class="sub-head" style="margin-top:26px">Follow</p>
      <p>{follow}</p>
      <p class="sub-head" style="margin-top:26px">Updates</p>
      <p><a class="text-link" href="index.html#signup">Join the mailing list &rarr;</a></p>
    </div>
    <form class="contact-form" action="{FORM_ACTION}" method="POST">
      <input type="hidden" name="_next" value="{SITE_URL}/thank-you.html">
      <input type="text" name="_gotcha" style="display:none" tabindex="-1" autocomplete="off">
      <label>Your name<input name="name" type="text" required></label>
      <label>Your email<input name="email" type="email" required></label>
      <label>Subject<select name="subject">{options}</select></label>
      <label>Message<textarea name="message" rows="6" required></textarea></label>
      <div><button class="btn primary" type="submit">Send message</button></div>
    </form>
  </div>
</section>"""
    page("contact.html", "Contact", "Contact Seahorse Filmhouse for distribution, festival, press and collaboration enquiries.",
         body, current="contact.html")

    body = """<section class="page-head" style="border:0;min-height:70vh"><div class="wrap">
  <p class="eyebrow">Thank you</p><h1>We have got it</h1>
  <p class="lead">Thanks for getting in touch. If you sent a message, we will reply as soon as we can.</p>
  <p style="margin-top:30px"><a class="btn" href="index.html">Back to home</a></p>
</div></section>"""
    page("thank-you.html", "Thank you", "Thank you for contacting Seahorse Filmhouse.", body, robots="noindex")


def build_shop_photos():
    """Raj's product photos (02_BUILD/shop_photos) -> images/shop-<slug>-<n>.jpg, 3:4, on white."""
    for pr in PRODUCTS:
        names = []
        for n, src in enumerate(pr.get("photos", []), 1):
            im = Image.open(SHOP_PHOTOS / src).convert("RGBA")
            flat = Image.new("RGBA", im.size, (255, 255, 255, 255))
            flat.alpha_composite(im)
            im = flat.convert("RGB")
            if im.width != 900:
                im = im.resize((900, round(im.height * 900 / im.width)), Image.LANCZOS)
            name = f"shop-{pr['slug']}-{n}.jpg"
            save_image(im, name, (150, 450), quality=86)
            names.append(name)
        if names:
            pr["images"] = names


def build_shop():
    cards = ""
    for n, pr in enumerate(PRODUCTS):
        if pr["availability"] == "available":
            action = f'<span class="price">{pr["price"]}</span><a class="btn primary" href="{pr["url"]}" target="_blank" rel="noopener">Buy</a>'
        else:
            action = '<span class="soon">Coming soon</span><a class="text-link" href="#signup">Notify me &rarr;</a>'
        images = pr.get("images") or [pr["image"]]
        thumbs = ""
        if len(images) > 1:
            thumbs = '<div class="thumbs">' + "".join(
                f'<button type="button" class="{"on" if i == 0 else ""}" aria-pressed="{"true" if i == 0 else "false"}" aria-label="{pr["name"]}, view {i + 1}">'
                f'{picture(im, "", "", "46px")}</button>' for i, im in enumerate(images)) + "</div>"
        cards += f"""<div class="product" id="{pr['slug']}">
  <div class="shot">{picture(images[0], "", pr['name'], SIZES_CARD, lazy=n > 0, high=n == 0)}</div>
  {thumbs}
  <h2 class="product-name">{pr['name']}</h2>
  <p>{pr['text']}</p>
  <div class="buy">{action}</div>
</div>"""
    notify = signup_block("", "Be first in line",
                          "Leave your email and we will tell you the day the shop opens.").replace(
        'value="Mailing list sign-up"', 'value="Shop: notify me"').replace(
        "Mailing list sign-up (seahorsefilmhouse.com)", "Shop notify-me sign-up (seahorsefilmhouse.com)").replace(
        '<p class="eyebrow">Mailing list</p>', '<p class="eyebrow">Shop opening soon</p>')
    body = f"""<section class="page-head"><div class="wrap">
  <p class="eyebrow">Shop</p><h1>Objects from the filmhouse</h1>
  <p class="lead">Clothing, books and prints from Seahorse Filmhouse. The shop is opening soon.</p>
</div></section>
<section class="block"><div class="wrap"><div class="grid three shop-grid">{cards}</div></div></section>
{notify}"""
    page("shop.html", "Shop", "The Seahorse Filmhouse shop: sfh tees, crop top, cap and the Open 24 Hours book. Opening soon.",
         body, current="shop.html")


def build_meta():
    urls = [""] + ["films.html", "news.html", "shop.html", "about.html", "contact.html"]
    urls += [f"films/{f['slug']}.html" for f in FILMS] + [f"news/{p['slug']}.html" for p in NEWS]
    entries = "".join(f"<url><loc>{SITE_URL}/{u}</loc></url>" for u in urls)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{entries}</urlset>\n')
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")


def add_hero_gl():
    """Trial only, off unless HERO_GL=1: the WebGL home hero (hero-gl.js) on the home page."""
    shutil.copy(HERE / "hero-gl.js", OUT / "js" / "hero-gl.js")
    home = OUT / "index.html"
    tag = f'<script src="js/site.js?v={STAMP}"></script>'
    html = home.read_text(encoding="utf-8")
    assert tag in html
    home.write_text(html.replace(tag, tag + f'\n<script src="js/hero-gl.js?v={STAMP}"></script>'), encoding="utf-8")


def load_site_content():
    """Read and check content/*.json (see content_loader.py); stop with a clear message if anything is wrong."""
    global SITE, FILMS, NEWS, TEAM, PRODUCTS, SOCIAL, IMAGE_ALT, IMAGE_JOBS
    try:
        c = load_content(CONTENT, SRC_IMG, SHOP_PHOTOS)
    except ContentError as e:
        sys.exit(f"\n{e}\n\nFix the file(s) in content/ and run the build again (see CONTENT_EDITING.md).")
    SITE, FILMS, NEWS, TEAM, PRODUCTS = c.site, c.films, c.news, c.team, c.products
    SOCIAL = dict(c.site["social"])
    IMAGE_ALT, IMAGE_JOBS = c.image_alts, c.image_jobs


def main():
    load_site_content()
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "css").mkdir(parents=True)
    (OUT / "js").mkdir()
    shutil.copy(HERE / "site.css", OUT / "css" / "site.css")
    shutil.copy(HERE / "site.js", OUT / "js" / "site.js")
    build_images()
    build_shop_photos()
    build_home()
    build_films()
    build_news()
    build_about()
    build_shop()
    build_contact()
    build_meta()
    if os.environ.get("HERO_GL") == "1":
        add_hero_gl()
    print(f"Built {len(list(OUT.rglob('*.html')))} pages into {OUT}")


if __name__ == "__main__":
    main()
