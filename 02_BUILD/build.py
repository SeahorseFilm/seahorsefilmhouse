#!/usr/bin/env python3
"""Builds the Seahorse Filmhouse site into ../01_SITE.

Run:  python3 02_BUILD/build.py
To add news: add an entry to the top of NEWS below, then run the build again.
"""
import html
import json
import re
import shutil
from datetime import date
from pathlib import Path

from PIL import Image

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

# Only links that are confirmed go here; empty ones are not shown.
SOCIAL = {
    "YouTube": "https://www.youtube.com/@seahorsefilmhouse",
    "Instagram": "https://www.instagram.com/seahorsefilmhouse/",
    "IMDb": "",
    "LinkedIn": "https://www.linkedin.com/company/seahorsefilmhouse/",
}

# source file -> (output name, max width)
IMAGES = {
    "film1.jpg": ("still-open-24-hours-1.jpg", 1920),
    "film4.jpg": ("still-open-24-hours-2.jpg", 1920),
    "film2.jpg": ("still-dark-light-1.jpg", 1920),
    "film3.jpg": ("still-daddys-girl-1.jpg", 1920),
    # film5/film6 identified from the trailers: the man in the woods is in the Daddy's Girl trailer,
    # the mugshot belongs to Dark Light (whose trailer shows the same woman under arrest)
    "film5.jpg": ("still-daddys-girl-2.jpg", 1920),
    "film6.jpg": ("still-dark-light-2.jpg", 1920),
    "project-image2.jpg": ("poster-open-24-hours.jpg", 900),
    "project-image3.jpg": ("poster-dark-light.jpg", 900),
    "project-image1.jpg": ("poster-daddys-girl.jpg", 900),
    "project-image4.jpg": ("poster-chasm.jpg", 900),
    "project-image5.jpg": ("poster-winter-dreams.jpg", 900),
    "tokyo-poster.png": ("poster-tokyo.jpg", 900),
    "team-image1.jpg": ("team-rp-khemanand.jpg", 700),
    "team-image2.jpg": ("team-padraig-reynolds.jpg", 700),
    "team-image3.jpg": ("team-ed-marx.jpg", 700),
    "team-image5.jpg": ("team-holly-amber-church.jpg", 700),
    "team-image6.jpg": ("team-shibani-kapur.jpg", 700),
}

FILMS = [
    {
        "slug": "open-24-hours",
        "title": "Open 24 Hours",
        "year": "2019",
        "status": "released",
        "tagline": "Some doors should stay closed",
        "director": "Padraig Reynolds",
        "runtime": "102 min",
        "genre": "Psychological thriller",
        "synopsis": "A psychological thriller about a woman who takes a job at a 24-hour "
                    "convenience store after being released from prison.",
        "trailer": "iI7yLprZheA",
        "trailer_date": "2022-08-06T10:29:17-07:00",  # when the trailer was uploaded to YouTube; Google requires it
        "poster": "poster-open-24-hours.jpg",
        "stills": ["still-open-24-hours-1.jpg", "still-open-24-hours-2.jpg"],
        "page_hero": "still-open-24-hours-2.jpg",
        "cast": ["Vanessa Grasse", "Brendan Fletcher", "Emily Tennant", "Cole Vigue", "Daniel O'Meara"],
        # United States availability and links, from JustWatch (checked 2026-10-11); recheck every few months
        "watch": [
            ("Stream", [("Amazon Prime Video", "https://watch.amazon.com/detail?gti=amzn1.dv.gti.a4b97701-668c-2fc6-5783-1dc577e5d187")]),
            ("Rent or buy", [("Apple TV", "https://tv.apple.com/us/movie/open-24-hours/umc.cmc.dhqll3nmnujvbzkgf15l0c11"),
                             ("Amazon", "https://watch.amazon.com/detail?gti=amzn1.dv.gti.a4b97701-668c-2fc6-5783-1dc577e5d187"),
                             ("Fandango at Home", "https://athome.fandango.com/content/browse/details/Open-24-Hours/1450145")]),
            ("Free with ads", [("Tubi", "https://tubitv.com/movies/562781"),
                               ("Pluto TV", "https://pluto.tv/on-demand/movies/open-24-hours-2020-1-1")]),
        ],
        "watch_url": "https://www.justwatch.com/us/movie/open-24-hours",
        "accolades": [
            ("win", "Winner: Best Special Effects / Make-Up, Screamfest Horror Film Festival, Los Angeles (2018)"),
            ("", "Official Selection: FrightFest, London (2018)"),
            ("", "Official Selection: Sitges International Film Festival, Spain (2018)"),
            ("", "Official Selection: Fantastic Fest, USA (2018)"),
            ("", "Official Selection: Telluride Horror Show, USA (2018)"),
            ("", "Official Selection: BIFAN, South Korea (2019)"),
        ],
    },
    {
        "slug": "dark-light",
        "title": "Dark Light",
        "year": "2019",
        "status": "released",
        "tagline": "What hides in the shadows?",
        "director": "Padraig Reynolds",
        "runtime": "90 min",
        "genre": "Horror",
        "synopsis": "A mother fights to protect her daughter from a terrifying presence "
                    "she believes is in her house.",
        "trailer": "Isls30Tok3E",
        "trailer_date": "2025-05-14T13:53:31-07:00",  # when the trailer was uploaded to YouTube; Google requires it
        "poster": "poster-dark-light.jpg",
        "stills": ["still-dark-light-1.jpg", "still-dark-light-2.jpg"],
        "page_hero": "still-dark-light-2.jpg",
        "cast": ["Jessica Madsen", "Opal Littleton", "Ed Brody", "Kristina Clifford"],
        "watch": [
            ("Stream", [("Amazon Prime Video", "https://watch.amazon.com/detail?gti=amzn1.dv.gti.f0b76568-916d-5c83-23e6-af5f892b63b2")]),
            ("Rent or buy", [("Apple TV", "https://tv.apple.com/us/movie/dark-light/umc.cmc.101z9fm2f5zv8j2k25ux4ub1"),
                             ("Amazon", "https://watch.amazon.com/detail?gti=amzn1.dv.gti.f0b76568-916d-5c83-23e6-af5f892b63b2"),
                             ("Fandango at Home", "https://athome.fandango.com/content/browse/details/Dark-Light/1304711")]),
            ("Free with ads", [("YouTube", "https://www.youtube.com/watch?v=2EMJyNB70pQ"),
                               ("Tubi", "https://tubitv.com/movies/661319")]),
        ],
        "watch_url": "https://www.justwatch.com/us/movie/dark-light-2019",
        "accolades": [
            ("", "Premiered at FrightFest, London"),
        ],
    },
    {
        "slug": "daddys-girl",
        "title": "Daddy&rsquo;s Girl",
        "plain_title": "Daddy's Girl",
        "year": "2018",
        "status": "released",
        "tagline": "Family ties that bind too tight",
        "director": "Julian Richards",
        "runtime": "89 min",
        "genre": "Horror thriller",
        "synopsis": "A young woman held captive by her father must uncover a dark family secret.",
        "trailer": "PkVRva3AiOE",
        "trailer_date": "2022-08-06T12:26:58-07:00",  # when the trailer was uploaded to YouTube; Google requires it
        "poster": "poster-daddys-girl.jpg",
        "stills": ["still-daddys-girl-1.jpg", "still-daddys-girl-2.jpg"],
        "page_hero": "still-daddys-girl-2.jpg",
        "cast": ["Jemma Dallender", "Costas Mandylor"],
        "watch": [
            ("Rent or buy", [("Apple TV", "https://tv.apple.com/us/movie/daddys-girl/umc.cmc.300g7xw5ei16q106pmizd81iy"),
                             ("Fandango at Home", "https://athome.fandango.com/content/browse/details/Daddy-s-Girl/1521389")]),
            ("Free with ads", [("Tubi", "https://tubitv.com/movies/100032317"),
                               ("Fandango at Home", "https://athome.fandango.com/content/browse/details/Daddy-s-Girl/1521389")]),
        ],
        "watch_url": "https://www.justwatch.com/us/movie/daddys-girl-2018",
        "accolades": [
            ("win", "Winner: Best Director, Fantasporto Film Festival, Portugal (2019)"),
            ("", "Buffalo Dreams Fantastic Film Festival (2020): 4 nominations"),
            ("", "Official Selection: Raindance, London (2018)"),
            ("", "Official Selection: BIFAN, South Korea (2019)"),
            ("", "National Film and Television Awards, USA (2019)"),
        ],
    },
    {
        "slug": "chasm",
        "title": "Chasm",
        "year": "2027",
        "status": "upcoming",
        "tagline": "The space between silence, mystery, and becoming",
        "synopsis": "An atmospheric portrait of Ila, a woman on the edge of quiet transformation. "
                    "A soulful exploration of the space between silence, mystery, and becoming.",
        "poster": "poster-chasm.jpg",
        "stills": [],
        "stage": "Coming 2027",
    },
    {
        "slug": "tokyo",
        "title": "Tokyo",
        "year": "2027",
        "status": "upcoming",
        "tagline": "Some destinations don&rsquo;t set you free",
        "director": "R P Khemanand",
        # Raj asked (2026-10-12) for a synopsis that does not give away the plot: no gun, no destination
        "synopsis": "A woman hires a private driver for a long journey west out of Tokyo. They share almost no language, each carrying something they can’t bring themselves to say.",
        "title_note": "working title",
        "runtime": "c. 95 min",
        "languages": "Japanese / English / Hindi",
        "poster": "poster-tokyo.jpg",
        "stills": [],
        "page_hero": "still-tokyo-mirror.jpg",
        "stage": "In development",
        "concept_art": True,
    },
    {
        "slug": "winter-dreams",
        "title": "Winter Dreams",
        "year": "In development",
        "status": "upcoming",
        "tagline": "Chasing dreams, loving illusions, and waking up too late",
        "synopsis": "A modern reimagining of F. Scott Fitzgerald&rsquo;s <em>Winter Dreams</em>, where "
                    "ambition and desire blur the line between success and self-loss. Set in today&rsquo;s "
                    "world, it is a story of chasing dreams, loving illusions, and waking up too late.",
        "poster": "poster-winter-dreams.jpg",
        "stills": [],
        "stage": "In development",
    },
]

TEAM = [
    ("R P Khemanand", "Producer / Director / Screenwriter", "team-rp-khemanand.jpg", "https://www.imdb.com/name/nm11359091/"),
    ("Padraig Reynolds", "Director / Screenwriter", "team-padraig-reynolds.jpg", "https://www.imdb.com/name/nm1754478/"),
    ("Ed Marx", "Film Editor", "team-ed-marx.jpg", "https://www.imdb.com/name/nm0003759/"),
    ("Holly Amber Church", "Music Composer", "team-holly-amber-church.jpg", "https://www.imdb.com/name/nm1498772/"),
    ("Shibani Kapur", "Producer", "team-shibani-kapur.jpg", "https://www.imdb.com/name/nm11359090/"),
]

# Newest first. Every post must be factual and approved before the site goes live.
NEWS = [
    {
        "slug": "tokyo-announced-for-2027",
        "date": "2026-10-11",
        "title": "Tokyo: a new film for 2027",
        "summary": "A woman, the driver she has hired, and a long road west out of Tokyo. A new film from Seahorse Filmhouse.",
        "image": "hero-tokyo.jpg",
        "body": """
<p>Seahorse Filmhouse is developing <em>Tokyo</em> (working title), a new feature directed by R P Khemanand and
planned for 2027.</p>
<p>A woman hires a private driver for a long journey west out of Tokyo. They share almost no language, each carrying something they can’t bring themselves to say.</p>
<p>The film is a feature of about 95 minutes, in Japanese, English and Hindi.</p>
<p>Follow the project on the <a href="../films/tokyo.html">Tokyo page</a>.</p>
""",
    },
    {
        "slug": "chasm-coming-2027",
        "date": "2026-10-10",
        "title": "Chasm is coming in 2027",
        "summary": "An atmospheric portrait of Ila, a woman on the edge of quiet transformation.",
        "image": "poster-chasm.jpg",
        "body": """
<p><em>Chasm</em>, from Seahorse Filmhouse, is set for 2027.</p>
<p>The film is an atmospheric portrait of Ila, a woman on the edge of quiet transformation, and a soulful
exploration of the space between silence, mystery, and becoming.</p>
<p>More details will be posted on the <a href="../films/chasm.html">Chasm page</a> as the release approaches.</p>
""",
    },
    {
        "slug": "winter-dreams-in-development",
        "date": "2026-10-10",
        "title": "Winter Dreams: a Fitzgerald story for today",
        "summary": "In development: a modern reimagining of F. Scott Fitzgerald's Winter Dreams.",
        "image": "poster-winter-dreams.jpg",
        "body": """
<p>Seahorse Filmhouse is developing <em>Winter Dreams</em>, a modern reimagining of F. Scott Fitzgerald&rsquo;s
short story.</p>
<p>Set in today&rsquo;s world, it follows ambition and desire as they blur the line between success and
self-loss: a story of chasing dreams, loving illusions, and waking up too late.</p>
<p>Follow the project on the <a href="../films/winter-dreams.html">Winter Dreams page</a>.</p>
""",
    },
    # --- Press archive: each item is written from a published source, linked at the foot of the post ---
    {
        "slug": "daddys-girl-dvd-and-vod-release",
        "date": "2020-09-23",
        "title": "Daddy&rsquo;s Girl arrives on DVD and on demand",
        "summary": "Rue Morgue reports the North American release of Julian Richards' award-winning thriller.",
        "image": "still-daddys-girl-2.jpg",
        "body": """
<p>Rue Morgue has announced the North American home release of <em><a href="../films/daddys-girl.html">Daddy&rsquo;s Girl</a></em>,
with the DVD out on 29 September 2020 and video on demand following on 2 October, through Cleopatra Entertainment.</p>
<p>The magazine notes that director Julian Richards won the Best Director prize at the Fantasporto International Film
Festival for the film. The cast is led by Jemma Dallender and Costas Mandylor, from a screenplay by Timothy Hill and Sean Hogan.</p>
<p class="source">Source: <a href="https://rue-morgue.com/award-winning-rural-shocker-daddys-girl-is-coming-next-week-trailer-and-poster/" target="_blank" rel="noopener">Rue Morgue, 23 September 2020</a></p>
""",
    },
    {
        "slug": "open-24-hours-trailer-and-release-date",
        "date": "2020-07-21",
        "title": "Open 24 Hours: new trailer and an August release",
        "summary": "Dread Central shares the official trailer and poster, with the film out on 18 August 2020.",
        "image": "still-open-24-hours-2.jpg",
        "body": """
<p>Dread Central has published the official trailer and poster for <em><a href="../films/open-24-hours.html">Open 24 Hours</a></em>,
released by 4Digital Media, and reports that the film is available on video on demand and DVD from 18 August 2020.</p>
<p>Written and directed by Padraig Reynolds, the film stars Vanessa Grasse as Mary, alongside Brendan Fletcher, Emily Tennant,
Cole Vigue and Daniel O&rsquo;Meara.</p>
<p class="source">Source: <a href="https://dreadcentral.com/news/334050/trailer-poster-for-gruesome-sadistic-horror-open-24-hours" target="_blank" rel="noopener">Dread Central, 21 July 2020</a></p>
""",
    },
    {
        "slug": "dark-light-us-release",
        "date": "2019-12-06",
        "title": "Dark Light released in the United States",
        "summary": "Vertical Entertainment releases Padraig Reynolds' creature feature in the US.",
        "image": "still-dark-light-1.jpg",
        "body": """
<p><em><a href="../films/dark-light.html">Dark Light</a></em> was released in the United States on 6 December 2019, distributed by
Vertical Entertainment, according to Box Office Mojo&rsquo;s listing for the film.</p>
<p>The release followed the film&rsquo;s world premiere at Arrow Video FrightFest in London that August.</p>
<p class="source">Source: <a href="https://www.boxofficemojo.com/title/tt9135260/credits" target="_blank" rel="noopener">Box Office Mojo</a></p>
""",
    },
    {
        "slug": "dark-light-world-premiere-frightfest",
        "date": "2019-08-25",
        "title": "Dark Light has its world premiere at FrightFest",
        "summary": "Padraig Reynolds' sci-fi horror premieres at Arrow Video FrightFest 2019 in London.",
        "image": "still-dark-light-2.jpg",
        "body": """
<p><em><a href="../films/dark-light.html">Dark Light</a></em> had its world premiere at Arrow Video FrightFest 2019 in London.</p>
<p>Written and directed by Padraig Reynolds, the film stars Jessica Madsen as Annie Knox, a mother whose daughter disappears from
the family&rsquo;s rural home, with Opal Littleton, Ed Brody and Kristina Clifford. SciFiNow covered the film from the festival,
and Britflicks spoke to Reynolds ahead of the premiere.</p>
<p class="source">Sources: <a href="https://www.scifinow.co.uk/reviews/dark-light-first-look-review-arrow-frightfest-2019/" target="_blank" rel="noopener">SciFiNow, 25 August 2019</a>
&middot; <a href="https://www.britflicks.com/blog/post/8998/Writer-Director-Padraig-Reynolds-Talks-About-His-Horror-Movie-DARK-LIGHT-Ahead-Of-Arrow-Video-FrightFest-World-Premiere/" target="_blank" rel="noopener">Britflicks</a></p>
""",
    },
    {
        "slug": "open-24-hours-at-screamfest",
        "date": "2018-10-12",
        "title": "Open 24 Hours screens at Screamfest in Los Angeles",
        "summary": "The film's West Coast premiere follows FrightFest in London and Fantastic Fest in Austin.",
        "image": "still-open-24-hours-1.jpg",
        "body": """
<p><em><a href="../films/open-24-hours.html">Open 24 Hours</a></em> screened at the Screamfest Horror Film Festival in Los Angeles
on 12 October 2018, its West Coast premiere.</p>
<p>The festival&rsquo;s programme notes that the film had already had its European premiere at FrightFest in London and its North
American premiere at Fantastic Fest in Austin. Screamfest lists Seahorse Filmhouse as producer, and credits Josh and Sierra
Russell for Best Makeup.</p>
<p class="source">Source: <a href="https://www.screamfest.com/2018/film/open-24-hours" target="_blank" rel="noopener">Screamfest 2018</a></p>
""",
    },
]

CURRENT = ' class="current"'
NAV = [("Home", "index.html"), ("Films", "films.html"), ("News", "news.html"), ("Shop", "shop.html"), ("About", "about.html"), ("Contact", "contact.html")]


def stamp(uid, size=150):
    """The round Seahorse Filmhouse stamp as inline SVG (uses currentColor)."""
    return f"""<svg class="stamp" width="{size}" height="{size}" viewBox="0 0 250 250" role="img" aria-label="Seahorse Filmhouse">
<defs><path id="ring-{uid}" d="M125,125 m-96,0 a96,96 0 1,1 192,0 a96,96 0 1,1 -192,0"/></defs>
<circle cx="125" cy="125" r="120" fill="none" stroke="currentColor" stroke-width="0.9"/>
<text font-family="Cormorant Garamond, serif" font-weight="500" font-size="13" letter-spacing="7.45" fill="currentColor"><textPath href="#ring-{uid}">SEAHORSE FILMHOUSE &#8226; INDEPENDENT CINEMA &#8226;</textPath></text>
<text x="125" y="150" text-anchor="middle" font-family="Bodoni Moda, serif" font-weight="900" font-size="82" letter-spacing="-2.6" fill="currentColor" style="font-optical-sizing:none;font-variation-settings:'opsz' 96">sf<tspan dx="7.4">h</tspan></text>
</svg>"""


COUNTER = """<div class="cookie-note" id="cookie-note" hidden>
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
    """A short description of a site image, read out by screen readers and used by image search."""
    if name == "hero-tokyo.jpg":
        return "Concept artwork for Tokyo: the city skyline at sunset"
    for f in FILMS:
        if name == f["poster"]:
            return f"{plain(f)} poster"
        if name in f.get("stills", []):
            return f"Still from {plain(f)}"
    return "Seahorse Filmhouse"


def ld(data):
    """Structured data for search engines (not shown on the page)."""
    data = {"@context": "https://schema.org", **data}
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


ORG = {"@type": "Organization", "name": "Seahorse Filmhouse", "url": f"{SITE_URL}/"}


def nice_date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return date(y, m, d).strftime("%-d %B %Y")


def page(path, title, description, body, current="", image="share.jpg", search_title="", head=""):
    """Wrap body in the shared layout and write it to OUT/path."""
    depth = path.count("/")
    root = "../" * depth
    links = [f'<a href="{root}{href}"{CURRENT if href == current else ""}>{label}</a>' for label, href in NAV]
    half = (len(links) + 1) // 2
    # two groups, so the logo can sit in the centre of the header between them
    nav = f'<span class="g">{"".join(links[:half])}</span><span class="g">{"".join(links[half:])}</span>'
    social = "".join(
        f'<li><a href="{url}" target="_blank" rel="noopener">{name}</a></li>' for name, url in SOCIAL.items() if url
    )
    social_block = f"<div><h4>Follow</h4><ul>{social}</ul></div>" if social else (
        f'<div><h4>Stay in touch</h4><ul><li><a href="{root}index.html#signup">Join the mailing list</a></li>'
        f'<li><a href="{root}contact.html">Contact us</a></li></ul></div>'
    )
    counter = COUNTER.replace("GA_ID", GA_ID) if GA_ID else ""
    full_title = "Seahorse Filmhouse" if not title else f"{title} | Seahorse Filmhouse"
    # search_title is the longer line shown in search results and on the browser tab
    tab_title = (search_title if search_title.startswith("Seahorse Filmhouse")
                 else f"{search_title} | Seahorse Filmhouse" if search_title else full_title)
    description = description.replace('"', "&quot;")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{tab_title}</title>
<meta name="description" content="{description}">
<meta name="google-site-verification" content="RyrXxN7FP37vGVC3hiQqt4avTftQgCJ8jtQxv17IyrA">
<link rel="canonical" href="{SITE_URL}/{'' if path == 'index.html' else path}">
<meta property="og:site_name" content="Seahorse Filmhouse">
<meta property="og:title" content="{full_title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_URL}/{'' if path == 'index.html' else path}">
<meta property="og:image" content="{SITE_URL}/images/{image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600&family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..900;1,6..96,400..900&family=Gloock&family=Cormorant+Garamond:wght@500&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="icon" type="image/png" sizes="48x48" href="{root}images/icon-48.png">
<link rel="icon" type="image/png" sizes="512x512" href="{root}images/icon-512.png">
<link rel="apple-touch-icon" href="{root}images/icon-180.png">
<link rel="stylesheet" href="{root}css/site.css?v={STAMP}">
{head}
</head>
<body>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{root}index.html" aria-label="Seahorse Filmhouse"><span class="m">s<span class="f">f</span>h</span><span class="s">Seahorse Filmhouse</span></a>
    <button class="nav-toggle" aria-label="Menu" aria-expanded="false"><span></span><span></span><span></span></button>
    <nav class="nav">{nav}</nav>
  </div>
</header>
<main>
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <a class="footer-stamp" href="{root}index.html">{stamp("footer")}</a>
        <p>Independent film production.<br>With operations in Los Angeles, London, Mumbai and the UAE.</p>
      </div>
      <div>
        <h4>Explore</h4>
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
<div class="modal" id="trailer-modal" role="dialog" aria-label="Trailer">
  <button class="close" aria-label="Close trailer">&times;</button>
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
  <div class="poster"><img src="{root}images/{film['poster']}" alt="{plain(film)} poster" loading="lazy"></div>
  <div class="meta"><span class="year">{film['year']}</span><h3>{film['title']}</h3><p>{line}</p></div>
</a>"""


def news_card(post, root=""):
    return f"""<a class="news-card" href="{root}news/{post['slug']}.html">
  <div class="thumb"><img src="{root}images/{post['image']}" alt="{image_alt(post['image'])}" loading="lazy"></div>
  <div class="body"><time datetime="{post['date']}">{nice_date(post['date'])}</time><h3>{post['title']}</h3><p>{post['summary']}</p></div>
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


def build_images():
    out = OUT / "images"
    out.mkdir(parents=True, exist_ok=True)
    for src, (name, width) in IMAGES.items():
        im = Image.open(SRC_IMG / src).convert("RGB")
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        if name.startswith("still-"):
            # give the film stills more punch: a touch brighter, more contrast and richer colour
            from PIL import ImageEnhance
            im = ImageEnhance.Brightness(im).enhance(1.06)
            im = ImageEnhance.Contrast(im).enhance(1.12)
            im = ImageEnhance.Color(im).enhance(1.18)
        im.save(out / name, "JPEG", quality=82, optimize=True, progressive=True)
    # Full-screen hero versions of the two posters: the sources are only 1024px wide, so they are
    # enlarged and sharpened here; otherwise they look soft when stretched across a wide screen.
    from PIL import ImageFilter
    for src, name in (("project-image4.jpg", "hero-chasm.jpg"), ("project-image5.jpg", "hero-winter-dreams.jpg"),
                      ("tokyo-skyline.png", "hero-tokyo.jpg"), ("tokyo-mirror.png", "still-tokyo-mirror.jpg")):
        im = Image.open(SRC_IMG / src).convert("RGB")
        if im.width >= 3000:
            # already high resolution (the 4K panoramic Tokyo image): keep it at its original size and
            # save with full colour detail, at Raj's request
            im.save(out / name, "JPEG", quality=92, subsampling=0, optimize=True, progressive=True)
            continue
        im = im.resize((1920, round(im.height * 1920 / im.width)), Image.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(radius=2.4, percent=150, threshold=2))
        im.save(out / name, "JPEG", quality=84, optimize=True, progressive=True)
    # Phone version of the panoramic Tokyo image: on a tall, narrow screen the wide picture would lose both
    # sides, so it is shown whole-ish as a band, zoomed out, over a blurred copy of itself.
    from PIL import ImageEnhance
    wide = Image.open(SRC_IMG / "tokyo-skyline.png").convert("RGB")
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
        fill.save(out / "hero-tokyo-phone.jpg", "JPEG", quality=88, optimize=True, progressive=True)
    shutil.copy(SRC_IMG / "_share.jpg", out / "share.jpg")
    for name in ("shop-book.jpg",):
        shutil.copy(SRC_IMG / f"_{name}", out / name)
    for size in (48, 180, 512):
        shutil.copy(SRC_IMG / f"_icon-{size}.png", out / f"icon-{size}.png")


def build_home():
    released = [f for f in FILMS if f["status"] == "released"]
    upcoming = [f for f in FILMS if f["status"] == "upcoming"]
    by_slug = {f["slug"]: f for f in FILMS}
    # Hero: every film as a line of the list; hovering a title brings its image into focus.
    hero_img = {
        "open-24-hours": "still-open-24-hours-1.jpg",
        "dark-light": "still-dark-light-1.jpg",
        "daddys-girl": "still-daddys-girl-1.jpg",
    }
    order = ["open-24-hours", "dark-light", "daddys-girl", "chasm", "tokyo", "winter-dreams"]
    layers = titles = notes = ""
    for i, slug in enumerate(order):
        f = by_slug[slug]
        active = " active" if i == 0 else ""
        soft = " soft" if f["status"] == "upcoming" else ""
        img = hero_img.get(slug, f"hero-{slug}.jpg")
        year = f["year"] if f["year"].isdigit() else "Soon"
        layers += f"""<div class="hero-bg bg-{slug}{soft}{active}" style="background-image:url('images/{img}')"></div>\n"""
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

{signup_block()}"""
    org = ld({**ORG, "logo": f"{SITE_URL}/images/icon-512.png", "foundingDate": "2017",
              "description": "Independent film production company with operations in Los Angeles, London, Mumbai and the UAE.",
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
        bg = f.get("page_hero") or (f["stills"][0] if f["stills"] else f"hero-{f['slug']}.jpg")
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
<div class="film-poster"><img src="../images/{f['poster']}" alt="{plain(f)} poster"></div>
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
<div class="film-poster"><img src="../images/{f['poster']}" alt="{plain(f)} poster"></div>
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
        body = f"""<section class="film-hero tall bg-{f['slug']}" style="background-image:url('../images/{bg}')">{play}<div class="wrap">
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
             search_title=search_title, head=ld(movie))


def build_news():
    body = f"""<section class="page-head"><div class="wrap">
  <p class="eyebrow">Latest</p><h1>News</h1>
  <p class="lead">Updates on our films, festival screenings and new projects.</p>
</div></section>
<section class="block"><div class="wrap"><div class="grid three">{''.join(news_card(p) for p in NEWS)}</div></div></section>
{signup_block()}"""
    page("news.html", "News", "News and updates from Seahorse Filmhouse: films, festivals and new projects.",
         body, current="news.html")

    for p in NEWS:
        portrait = p["image"].startswith("poster-")
        img_style = ' style="max-width:360px"' if portrait else ""
        body = f"""<section class="page-head"><div class="wrap post">
  <time datetime="{p['date']}">{nice_date(p['date'])}</time>
  <h1 style="margin-top:12px;font-size:clamp(2rem,4.6vw,3.2rem)">{p['title']}</h1>
</div></section>
<section class="block tight"><div class="wrap post">
  <div class="post-image"{img_style}><img src="../images/{p['image']}" alt="{image_alt(p['image'])}"></div>
  <div class="post-body">{p['body']}</div>
  <p style="margin-top:40px"><a class="text-link" href="../news.html">&larr; All news</a></p>
</div></section>
{signup_block("../")}"""
        article = ld({"@type": "NewsArticle", "headline": text_only(p["title"]), "datePublished": p["date"],
                      "image": f"{SITE_URL}/images/{p['image']}", "description": p["summary"],
                      "author": ORG, "publisher": ORG,
                      "mainEntityOfPage": f"{SITE_URL}/news/{p['slug']}.html"})
        page(f"news/{p['slug']}.html", p["title"], p["summary"], body, current="news.html", image=p["image"], head=article)


def build_about():
    people = "".join(
        f"""<div class="person">
  <div class="photo"><img src="images/{img}" alt="{name}" loading="lazy"></div>
  <h3>{name}</h3><p>{role}</p>
  <a class="text-link" href="{imdb}" target="_blank" rel="noopener">IMDb</a>
</div>""" for name, role, img, imdb in TEAM
    )
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
      <div><strong>Los Angeles</strong><span>United States</span></div>
      <div><strong>London</strong><span>United Kingdom</span></div>
      <div><strong>Mumbai</strong><span>India</span></div>
      <div><strong>UAE</strong><span>United Arab Emirates</span></div>
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
    options = "".join(f"<option>{o}</option>" for o in
                      ["General enquiry", "Distribution", "Festivals and programming", "Press", "Collaboration"])
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
      <p>Los Angeles, London, Mumbai and the UAE</p>
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
    page("thank-you.html", "Thank you", "Thank you for contacting Seahorse Filmhouse.", body)


# Shop: products are "coming soon" until the Fourthwall shop is live. To switch one on, give it a
# "url" (its Fourthwall product page) and a "price"; the card then shows a Buy button instead.
PRODUCTS = [
    {"name": "sfh tee, black", "slug": "tee-black",
     "photos": ["tee-black-front.png", "tee-black-model-front.png", "tee-black-back.png", "tee-black-model-back.png"],
     "text": "An oversized black tee with the sfh mark in white on the front and the Seahorse Filmhouse stamp on the back.", "price": "", "url": ""},
    {"name": "sfh tee, grey", "slug": "tee-grey",
     "photos": ["tee-grey-back.png", "tee-grey-model.png", "tee-grey-front.png"],
     "text": "A relaxed grey tee with the sfh mark large across the back and small on the sleeve.", "price": "", "url": ""},
    {"name": "sfh crop top", "slug": "top",
     "photos": ["top-model-front.png", "top-front.png", "top-back.png", "top-model-back.png"],
     "text": "A black cropped tee with the sfh mark tone on tone on the front and the stamp on the back.", "price": "", "url": ""},
    {"name": "sfh cap", "slug": "cap",
     "photos": ["cap-front.png", "cap-model-front.png", "cap-side.png", "cap-model-side.png"],
     "text": "A black cap with the sfh mark on a front patch and again at the back.", "price": "", "url": ""},
    {"name": "Open 24 Hours: the book", "slug": "book", "image": "shop-book.jpg",
     "text": "A coffee table book of photographs from the film.", "price": "", "url": ""},
]

SHOP_PHOTOS = HERE / "shop_photos"


def build_shop_photos():
    """Raj's product photos (02_BUILD/shop_photos) -> images/shop-<slug>-<n>.jpg, 3:4, on white."""
    out = OUT / "images"
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
            im.save(out / name, "JPEG", quality=86, optimize=True, progressive=True)
            names.append(name)
        if names:
            pr["images"] = names


def build_shop():
    cards = ""
    for pr in PRODUCTS:
        if pr["url"]:
            action = f'<span class="price">{pr["price"]}</span><a class="btn primary" href="{pr["url"]}" target="_blank" rel="noopener">Buy</a>'
        else:
            action = '<span class="soon">Coming soon</span><a class="text-link" href="#signup">Notify me &rarr;</a>'
        images = pr.get("images") or [pr["image"]]
        thumbs = ""
        if len(images) > 1:
            thumbs = '<div class="thumbs">' + "".join(
                f'<button type="button" class="{"on" if i == 0 else ""}" data-src="images/{im}" aria-label="{pr["name"]}, view {i + 1}">'
                f'<img src="images/{im}" alt="" loading="lazy"></button>' for i, im in enumerate(images)) + "</div>"
        cards += f"""<div class="product">
  <div class="shot"><img src="images/{images[0]}" alt="{pr['name']}" loading="lazy"></div>
  {thumbs}
  <h3>{pr['name']}</h3>
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


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "css").mkdir(parents=True)
    (OUT / "js").mkdir()
    shutil.copy(HERE / "site.css", OUT / "css" / "site.css")
    shutil.copy(HERE / "site.js", OUT / "js" / "site.js")
    build_images()
    build_home()
    build_films()
    build_news()
    build_about()
    build_shop_photos()
    build_shop()
    build_contact()
    build_meta()
    print(f"Built {len(list(OUT.rglob('*.html')))} pages into {OUT}")


if __name__ == "__main__":
    main()
