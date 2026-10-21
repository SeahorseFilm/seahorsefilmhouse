"""Loads and checks the editorial content in ../content (JSON files). Standard library only.

build.py calls load_content(); every problem found is reported at once, as "file: where: what is wrong",
and the build stops. The schema is described in CONTENT_EDITING.md.
Keys starting with "_" are ignored everywhere, so a file can carry a note to its editors.
"""
import json
import re
from datetime import date
from pathlib import Path
from types import SimpleNamespace


class ContentError(Exception):
    def __init__(self, problems):
        self.problems = problems
        super().__init__("Content problems:\n  " + "\n  ".join(problems))


SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SOURCE_FILE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*\.(?:jpg|jpeg|png)$")
OUTPUT_FILE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.jpg$")
UPLOAD_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")
YOUTUBE = re.compile(r"^https://(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]{11})$")
# names build.py writes itself, so content may not use them
RESERVED_FILES = {"share.jpg"}


class _Check:
    """Collects problems for one content file."""

    def __init__(self, name, problems):
        self.name, self.problems = name, problems

    def err(self, where, msg):
        self.problems.append(f"{self.name}: {where}: {msg}")

    def keys(self, data, where, required, optional=()):
        """data must be an object with every required key and no unknown ones."""
        if not isinstance(data, dict):
            self.err(where, "must be an object {...}")
            return False
        for k in required:
            if k not in data:
                self.err(where, f'missing "{k}"')
        for k in data:
            if k not in required and k not in optional and not k.startswith("_"):
                self.err(where, f'unknown field "{k}" (typo? allowed: {", ".join(list(required) + list(optional))})')
        return True

    def text(self, data, key, where, required=True, empty=False):
        v = data.get(key)
        if v is None:
            if required and key in data:
                self.err(f"{where}.{key}", "must not be null")
            return None
        if not isinstance(v, str):
            self.err(f"{where}.{key}", "must be text")
            return None
        if not empty and not v.strip():
            self.err(f"{where}.{key}", "must not be empty")
        elif v != v.strip():
            self.err(f"{where}.{key}", "has spaces at the start or end")
        return v

    def items(self, data, key, where, required=True, nonempty=True):
        v = data.get(key)
        if v is None:
            return []
        if not isinstance(v, list):
            self.err(f"{where}.{key}", "must be a list [...]")
            return []
        if required and nonempty and not v:
            self.err(f"{where}.{key}", "must have at least one entry")
        return v

    def url(self, data, key, where, required=True):
        v = self.text(data, key, where, required, empty=not required)
        if v and not v.startswith("https://"):
            self.err(f"{where}.{key}", f'must start with "https://" (got "{v}")')
        return v

    def slug(self, data, where):
        v = self.text(data, "slug", where)
        if v is not None and not SLUG.match(v):
            self.err(f"{where}.slug", f'"{v}" must be lower-case letters, numbers and single hyphens')
        return v


def _read(path, problems):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        problems.append(f"{path.name}: file is missing")
    except json.JSONDecodeError as e:
        problems.append(f"{path.name}: not valid JSON, line {e.lineno} column {e.colno}: {e.msg}")
    except UnicodeDecodeError:
        problems.append(f"{path.name}: must be saved as UTF-8")
    return None


class _Images:
    """Every output picture is defined once (it has a "source") and may then be used again by name."""

    def __init__(self, source_dir, problems):
        self.source_dir, self.problems = source_dir, problems
        self.jobs, self.defined, self.alts, self.uses = [], {}, {}, []

    def read(self, c, data, where, role, alt, define=None):
        """Check one image object. alt: "required", "optional" or "none". define: True/False/None (either)."""
        required = ["file"] + (["alt"] if alt == "required" else [])
        optional = (["alt"] if alt == "optional" else []) + ["source"] + (["phone"] if role == "home" else [])
        if not c.keys(data, where, required, optional):
            return None
        file = c.text(data, "file", where)
        a = c.text(data, "alt", where, required=alt == "required")
        if file is None:
            return None
        if not OUTPUT_FILE.match(file) or file in RESERVED_FILES:
            c.err(f"{where}.file", f'"{file}" must be a lower-case name ending .jpg, e.g. poster-my-film.jpg')
        if a is not None:
            if file in self.alts and self.alts[file] != a:
                c.err(f"{where}.alt", f'"{file}" already has different alt text elsewhere ("{self.alts[file]}")')
            self.alts.setdefault(file, a)
        if "source" in data:
            if define is False:
                c.err(where, 'this picture must already be defined elsewhere: give only "file"' + (' and "alt"' if alt != "none" else ""))
            self._define(c, data, where, role, file)
        else:
            if define is True:
                c.err(where, f'missing "source" (the file in 02_BUILD/source_images)')
            self.uses.append((c.name, where, file))
        return file

    def _define(self, c, data, where, role, file):
        source = self._source(c, data, where)
        if file in self.defined:
            c.err(where, f'"{file}" is already defined at {self.defined[file]}')
        self.defined[file] = f"{c.name} {where}"
        job = {"file": file, "source": source, "role": role, "phone": None}
        if "phone" in data:
            ph = data["phone"]
            if c.keys(ph, f"{where}.phone", ["file", "source"]):
                pfile = c.text(ph, "file", f"{where}.phone")
                psource = self._source(c, ph, f"{where}.phone")
                if pfile and not OUTPUT_FILE.match(pfile):
                    c.err(f"{where}.phone.file", f'"{pfile}" must be a lower-case name ending .jpg')
                if pfile in self.defined:
                    c.err(f"{where}.phone", f'"{pfile}" is already defined at {self.defined[pfile]}')
                if pfile:
                    self.defined[pfile] = f"{c.name} {where}.phone"
                job["phone"] = {"file": pfile, "source": psource}
        self.jobs.append(job)

    def _source(self, c, data, where):
        source = c.text(data, "source", where)
        if source is None:
            return None
        if not SOURCE_FILE.match(source):
            c.err(f"{where}.source", f'"{source}" is not a plain .jpg/.png file name')
        elif not (self.source_dir / source).is_file():
            c.err(f"{where}.source", f'"{source}" is not in 02_BUILD/{self.source_dir.name}/')
        return source

    def finish(self):
        for name, where, file in self.uses:
            if file not in self.defined:
                self.problems.append(f"{name}: {where}: picture \"{file}\" is not defined anywhere "
                                     f'(give it a "source" once, e.g. under the film\'s poster or stills)')


def _films(data, images, problems, site_slugs):
    c = _Check("films.json", problems)
    if not c.keys(data, "file", ["films"]):
        return []
    out, seen = [], set()
    for i, raw in enumerate(c.items(data, "films", "file")):
        where = f"films[{i}]"
        c.keys(raw, where, ["slug", "title", "year", "status", "tagline", "synopsis", "images"],
               ["director", "runtime", "genre", "languages", "title_note", "stage", "concept_art",
                "cast", "trailer_url", "trailer_uploaded", "watch_checked", "watch", "watch_url", "accolades"])
        if not isinstance(raw, dict):
            continue
        slug = c.slug(raw, where)
        where = f"films[{i}] ({slug})"
        if slug in seen:
            c.err(where, f'slug "{slug}" is used by another film')
        seen.add(slug)
        film = {"slug": slug}
        for k in ("title", "year", "tagline", "synopsis"):
            film[k] = c.text(raw, k, where)
        for k in ("director", "languages", "title_note", "stage", "genre"):
            if k in raw:
                film[k] = c.text(raw, k, where)
        status = film["status"] = c.text(raw, "status", where)
        if status not in ("released", "upcoming"):
            c.err(f"{where}.status", 'must be "released" or "upcoming"')
        if "runtime" in raw:
            film["runtime"] = c.text(raw, "runtime", where)
        if "concept_art" in raw:
            if not isinstance(raw["concept_art"], bool):
                c.err(f"{where}.concept_art", "must be true or false")
            film["concept_art"] = raw["concept_art"] is True
        if status == "released":
            for k in ("director", "runtime", "genre", "cast", "trailer_url", "trailer_uploaded", "watch", "watch_url", "accolades"):
                if k not in raw:
                    c.err(where, f'missing "{k}" (every released film needs it)')
            if film.get("runtime") and not re.match(r"^\d+ min$", film["runtime"]):
                c.err(f"{where}.runtime", f'released films use whole minutes like "102 min" (got "{film["runtime"]}")')
        elif status == "upcoming" and "stage" not in raw:
            c.err(where, 'missing "stage" (e.g. "In development")')
        if "cast" in raw:
            cast = c.items(raw, "cast", where)
            for n, name in enumerate(cast):
                if not isinstance(name, str) or not name.strip():
                    c.err(f"{where}.cast[{n}]", "must be a name")
            film["cast"] = [n for n in cast if isinstance(n, str)]
        if "trailer_url" in raw:
            url = c.text(raw, "trailer_url", where)
            m = YOUTUBE.match(url or "")
            if url and not m:
                c.err(f"{where}.trailer_url", f'must look like https://www.youtube.com/watch?v=XXXXXXXXXXX (got "{url}")')
            film["trailer"] = m.group(1) if m else None
        if "trailer_uploaded" in raw:
            t = c.text(raw, "trailer_uploaded", where)
            if t and not UPLOAD_TIME.match(t):
                c.err(f"{where}.trailer_uploaded", f'must look like 2022-08-06T10:29:17-07:00 (got "{t}")')
            film["trailer_date"] = t
        if "watch_checked" in raw:
            _iso(c, raw["watch_checked"], f"{where}.watch_checked")
        if "watch" in raw:
            film["watch"] = []
            for n, group in enumerate(c.items(raw, "watch", where)):
                w = f"{where}.watch[{n}]"
                if c.keys(group, w, ["label", "services"]):
                    label = c.text(group, "label", w)
                    services = []
                    for m_, s in enumerate(c.items(group, "services", w)):
                        if c.keys(s, f"{w}.services[{m_}]", ["name", "url"]):
                            services.append((c.text(s, "name", f"{w}.services[{m_}]"), c.url(s, "url", f"{w}.services[{m_}]")))
                    film["watch"].append((label, services))
        if "watch_url" in raw:
            film["watch_url"] = c.url(raw, "watch_url", where)
        if "accolades" in raw:
            film["accolades"] = []
            for n, a in enumerate(c.items(raw, "accolades", where, nonempty=False)):
                w = f"{where}.accolades[{n}]"
                if c.keys(a, w, ["text"], ["award"]):
                    if "award" in a and not isinstance(a["award"], bool):
                        c.err(f"{w}.award", "must be true or false")
                    film["accolades"].append(("win" if a.get("award") is True else "", c.text(a, "text", w)))
        img = raw.get("images")
        if c.keys(img, f"{where}.images", ["poster", "home", "lead"], ["stills"]):
            w = f"{where}.images"
            film["poster"] = images.read(c, img.get("poster"), f"{w}.poster", "poster", "required", define=True)
            film["stills"] = [images.read(c, s, f"{w}.stills[{n}]", "still", "required", define=True)
                              for n, s in enumerate(c.items(img, "stills", w, nonempty=False))]
            home = images.read(c, img.get("home"), f"{w}.home", "home", "optional")
            film["home_image"] = home
            film["home_phone"] = None
            if isinstance(img.get("home"), dict) and isinstance(img["home"].get("phone"), dict):
                film["home_phone"] = img["home"]["phone"].get("file")
            film["page_hero"] = images.read(c, img.get("lead"), f"{w}.lead", "lead", "required")
        out.append(film)
    site_slugs.update(seen)
    return out


def _iso(c, value, where):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        c.err(where, f'must be a real date written YYYY-MM-DD (got "{value}")')
        return None


def _news(data, images, problems, film_slugs):
    c = _Check("news.json", problems)
    if not c.keys(data, "file", ["posts"]):
        return []
    out, seen = [], set()
    for i, raw in enumerate(c.items(data, "posts", "file")):
        where = f"posts[{i}]"
        c.keys(raw, where, ["slug", "date", "title", "summary", "image", "body"], ["sources"])
        if not isinstance(raw, dict):
            continue
        slug = c.slug(raw, where)
        where = f"posts[{i}] ({slug})"
        if slug in seen:
            c.err(where, f'slug "{slug}" is used by another post')
        seen.add(slug)
        post = {"slug": slug, "title": c.text(raw, "title", where), "summary": c.text(raw, "summary", where)}
        post["date"] = c.text(raw, "date", where)
        if post["date"] is not None:
            _iso(c, post["date"], f"{where}.date")
        post["image"] = images.read(c, raw.get("image"), f"{where}.image", "news", "required")
        if isinstance(raw.get("image"), dict):
            post["image_alt"] = raw["image"].get("alt")
        post["body"] = []
        for n, para in enumerate(c.items(raw, "body", where)):
            if not isinstance(para, str) or not para.strip():
                c.err(f"{where}.body[{n}]", "must be a paragraph of text")
                continue
            if re.search(r"</?(?:p|script|style|iframe|div)\b", para, re.I):
                c.err(f"{where}.body[{n}]", "give the paragraph's text only: no <p>, <div>, <script> (use <em> and <a> if needed)")
            for href in re.findall(r'href="([^"]*)"', para):
                m = re.match(r"^\.\./films/([a-z0-9-]+)\.html$", href)
                if m and m.group(1) not in film_slugs:
                    c.err(f"{where}.body[{n}]", f'links to film "{m.group(1)}", which is not in films.json')
                elif not m and not href.startswith("https://"):
                    c.err(f"{where}.body[{n}]", f'link "{href}" must be https://... or ../films/<slug>.html')
            post["body"].append(para)
        post["sources"] = []
        for n, s in enumerate(c.items(raw, "sources", where, required=False)):
            w = f"{where}.sources[{n}]"
            if c.keys(s, w, ["label", "url"]):
                post["sources"].append((c.text(s, "label", w), c.url(s, "url", w)))
        out.append(post)
    # newest first; posts on the same day keep the order they have in the file
    return sorted(out, key=lambda p: p["date"] or "", reverse=True)


def _team(data, images, problems):
    c = _Check("team.json", problems)
    if not c.keys(data, "file", ["people"]):
        return []
    out, seen = [], set()
    for i, raw in enumerate(c.items(data, "people", "file")):
        where = f"people[{i}]"
        c.keys(raw, where, ["name", "role", "imdb", "photo"])
        if not isinstance(raw, dict):
            continue
        name = c.text(raw, "name", where)
        where = f"people[{i}] ({name})"
        if name in seen:
            c.err(where, f'"{name}" is listed twice')
        seen.add(name)
        out.append({"name": name, "role": c.text(raw, "role", where), "imdb": c.url(raw, "imdb", where),
                    "photo": images.read(c, raw.get("photo"), f"{where}.photo", "portrait", "required", define=True),
                    "alt": (raw.get("photo") or {}).get("alt") if isinstance(raw.get("photo"), dict) else None})
    return out


def _shop(data, images, problems, shop_photos):
    c = _Check("shop.json", problems)
    if not c.keys(data, "file", ["products"]):
        return []
    out, seen = [], set()
    for i, raw in enumerate(c.items(data, "products", "file")):
        where = f"products[{i}]"
        c.keys(raw, where, ["slug", "name", "text", "availability"], ["price", "url", "photos", "image"])
        if not isinstance(raw, dict):
            continue
        slug = c.slug(raw, where)
        where = f"products[{i}] ({slug})"
        if slug in seen:
            c.err(where, f'slug "{slug}" is used by another product')
        seen.add(slug)
        pr = {"slug": slug, "name": c.text(raw, "name", where), "text": c.text(raw, "text", where),
              "price": c.text(raw, "price", where, empty=True) or "", "url": c.text(raw, "url", where, empty=True) or ""}
        avail = pr["availability"] = c.text(raw, "availability", where)
        if avail not in ("coming-soon", "available"):
            c.err(f"{where}.availability", 'must be "coming-soon" or "available"')
        elif avail == "available" and not (pr["url"] and pr["price"]):
            c.err(where, 'an "available" product needs both "price" and "url"')
        elif avail == "coming-soon" and pr["url"]:
            c.err(where, 'a "coming-soon" product must have an empty "url" (or set availability to "available")')
        if pr["url"] and not pr["url"].startswith("https://"):
            c.err(f"{where}.url", f'must start with "https://" (got "{pr["url"]}")')
        if ("photos" in raw) == ("image" in raw):
            c.err(where, 'give either "photos" (files in 02_BUILD/shop_photos) or "image" (one file in 02_BUILD/source_images)')
        if "photos" in raw:
            pr["photos"] = []
            for n, p in enumerate(c.items(raw, "photos", where)):
                if not isinstance(p, str) or not SOURCE_FILE.match(p):
                    c.err(f"{where}.photos[{n}]", "must be a .png/.jpg file name")
                elif not (shop_photos / p).is_file():
                    c.err(f"{where}.photos[{n}]", f'"{p}" is not in 02_BUILD/shop_photos/')
                else:
                    pr["photos"].append(p)
        if "image" in raw:
            pr["image"] = images.read(c, raw["image"], f"{where}.image", "shop", "none", define=True)
        out.append(pr)
    return out


def _site(data, problems):
    c = _Check("site.json", problems)
    site = {}
    if not c.keys(data, "file", ["social", "operating_in", "footer_lines", "locations", "organization", "enquiry_subjects"]):
        return site
    site["social"], names = [], set()
    for i, s in enumerate(c.items(data, "social", "file")):
        w = f"social[{i}]"
        if c.keys(s, w, ["name"], ["url"]):
            name = c.text(s, "name", w)
            if name in names:
                c.err(w, f'"{name}" is listed twice')
            names.add(name)
            site["social"].append((name, c.url(s, "url", w, required=False) or ""))
    site["operating_in"] = c.text(data, "operating_in", "file")
    site["footer_lines"] = [t for t in c.items(data, "footer_lines", "file") if isinstance(t, str)]
    site["locations"] = []
    for i, loc in enumerate(c.items(data, "locations", "file")):
        w = f"locations[{i}]"
        if c.keys(loc, w, ["place", "country"]):
            site["locations"].append((c.text(loc, "place", w), c.text(loc, "country", w)))
    org = data.get("organization")
    if c.keys(org, "organization", ["description", "founding_year"]):
        site["org_description"] = c.text(org, "description", "organization")
        site["founding_year"] = c.text(org, "founding_year", "organization")
        if site["founding_year"] and not re.match(r"^\d{4}$", site["founding_year"]):
            c.err("organization.founding_year", "must be a four-digit year")
    site["enquiry_subjects"] = [t for t in c.items(data, "enquiry_subjects", "file") if isinstance(t, str) and t.strip()]
    if len(set(site["enquiry_subjects"])) != len(site["enquiry_subjects"]):
        c.err("enquiry_subjects", "has a repeated subject")
    return site


def load_content(content_dir, source_images, shop_photos):
    """Read and check everything in content_dir. Returns a namespace; raises ContentError listing every problem."""
    content_dir = Path(content_dir)
    problems = []
    raw = {n: _read(content_dir / f"{n}.json", problems) for n in ("site", "films", "news", "team", "shop")}
    images = _Images(Path(source_images), problems)
    film_slugs = set()
    films = _films(raw["films"], images, problems, film_slugs) if raw["films"] is not None else []
    news = _news(raw["news"], images, problems, film_slugs) if raw["news"] is not None else []
    team = _team(raw["team"], images, problems) if raw["team"] is not None else []
    products = _shop(raw["shop"], images, problems, Path(shop_photos)) if raw["shop"] is not None else []
    site = _site(raw["site"], problems) if raw["site"] is not None else {}
    images.finish()
    for job in images.jobs:
        if job["file"].startswith("shop-") and job["role"] != "shop":
            problems.append(f'picture "{job["file"]}": names starting "shop-" are reserved for the shop')
    if problems:
        raise ContentError(problems)
    return SimpleNamespace(site=site, films=films, news=news, team=team, products=products,
                           image_jobs=images.jobs, image_alts=images.alts)
