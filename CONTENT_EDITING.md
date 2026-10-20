# Editing the site's content

Films, news, team, shop products and site-wide details live in JSON files in `content/`. The page layout, styles,
image processing, search-engine data, analytics consent and forms stay in `02_BUILD/` and are not edited here.

The rules in `CLAUDE.md` still apply: no rewording of published copy without Raj's say-so, Tokyo uses only the
wording already published, and nothing goes live without a pull request that Raj approves.

## Where things live

| What | File | Holds |
|---|---|---|
| Films | `content/films.json` | every film's text, credits, trailer, where-to-watch links, awards and pictures |
| News | `content/news.json` | every post: title, date, summary, text, source links, picture |
| Team | `content/team.json` | name, role, IMDb link, photo (the About page) |
| Shop | `content/shop.json` | products, availability, price, buy link, photos |
| Site-wide | `content/site.json` | social links, "operating in" line, footer lines, About-page locations, company description for search engines, contact-form subjects |
| Pictures | `02_BUILD/source_images/` and `02_BUILD/shop_photos/` | the original image files (see below) |

Still in `02_BUILD/build.py` on purpose: the home-page statement, the About-page text and every other page heading
and button label, page titles and descriptions, the Formspree forms, analytics and the cookie notice.

## Writing the files

- Plain JSON: text in double quotes, entries separated by commas, no trailing comma. A comma or quote in the wrong place
  stops the build with the file, line and column.
- Text fields can hold a simple entity such as `&rsquo;` (an apostrophe) and `<em>…</em>`. Copy them from an existing entry.
- A key starting with `_` (for example `"_note"`) is ignored, so it can carry a note to the next editor.
- Run the check below after every change. It reports **every** problem at once, for example
  `films.json: films[2] (daddys-girl).images.lead: picture "still-typo.jpg" is not defined anywhere`.

## Pictures

Put the original file in the folder the table names. Any size; `.jpg` or `.png`. The build makes the web sizes
(AVIF, WebP and JPEG) and the final file names itself.

| Used for | Original goes in | Written to `01_SITE/images/` as |
|---|---|---|
| Posters, film stills, team photos, news pictures, a film's hero or lead image | `02_BUILD/source_images/` | the `file` you choose, e.g. `poster-my-film.jpg` |
| Shop product photos | `02_BUILD/shop_photos/` | `shop-<product>-<n>.jpg` |
| Share preview, favicons, the book photo | `02_BUILD/source_images/`, names starting `_` | fixed by the build; leave alone |

Every picture object has:

- `"source"`: the original file name (only where the picture is first defined),
- `"file"`: the output name: lower-case, hyphens, ending `.jpg`; use `poster-<film>.jpg`, `still-<film>-1.jpg`,
  `team-<name>.jpg`, `hero-<film>.jpg`,
- `"alt"`: what the picture shows, for people using screen readers and for image search.

A picture is defined **once** (with `source`). Anywhere else it is used again, give just its `file` (and `alt` where
asked): a news post can use a film's poster that way.

## Add a news post

1. Open `content/news.json` and add an entry inside `"posts"`. Order does not matter: the site sorts by date, newest
   first, and the home page shows the latest three.

```json
{
  "slug": "my-new-post",
  "date": "2026-11-02",
  "title": "A short headline",
  "summary": "One or two sentences, shown on the news cards and in search results.",
  "image": { "file": "poster-chasm.jpg", "alt": "Chasm poster" },
  "body": [
    "First paragraph.",
    "Second paragraph, with a link to <a href=\"../films/chasm.html\">the Chasm page</a>."
  ],
  "sources": [
    { "label": "Publication, 2 November 2026", "url": "https://example.com/article" }
  ]
}
```

2. `slug` becomes the address (`/news/my-new-post.html`): lower-case letters, numbers, hyphens, and unique.
3. `body` is a list of paragraphs without `<p>` tags. Link to a film page as `../films/<film-slug>.html`; other links
   must start with `https://`.
4. `sources` is optional. One source prints "Source: …", several print "Sources: … · …".
5. For a new picture instead of an existing one, add `"source": "my-photo.jpg"` to `image` and put that file in
   `02_BUILD/source_images/`.
6. The post, its sitemap entry and its search-engine data are created automatically. Posts must be factual and
   approved before they go live.

## Add a film

1. Put the poster (and any stills) in `02_BUILD/source_images/`.
2. Add an entry to `"films"` in `content/films.json`. **Position matters:** the home-page film list follows the order of
   this file.
3. A **released** film needs everything in the first example; an **upcoming** film needs only the second.

```json
{
  "slug": "my-film", "title": "My Film", "year": "2028", "status": "released",
  "tagline": "A short line", "synopsis": "One or two sentences.",
  "director": "Director Name", "runtime": "95 min", "genre": "Thriller",
  "cast": ["First Actor", "Second Actor"],
  "trailer_url": "https://www.youtube.com/watch?v=XXXXXXXXXXX",
  "trailer_uploaded": "2028-01-31T10:00:00-07:00",
  "watch": [ { "label": "Stream", "services": [ { "name": "Service", "url": "https://example.com/my-film" } ] } ],
  "watch_url": "https://www.justwatch.com/us/movie/my-film",
  "accolades": [ { "text": "Winner: Best Film, Some Festival (2028)", "award": true }, { "text": "Official Selection: Another Festival (2028)" } ],
  "images": {
    "poster": { "source": "my-poster.jpg", "file": "poster-my-film.jpg", "alt": "My Film poster" },
    "stills": [ { "source": "my-still-1.jpg", "file": "still-my-film-1.jpg", "alt": "Still from My Film" },
                { "source": "my-still-2.jpg", "file": "still-my-film-2.jpg", "alt": "Still from My Film" } ],
    "home": { "file": "still-my-film-1.jpg" },
    "lead": { "file": "still-my-film-2.jpg", "alt": "Still from My Film" }
  }
}
```

```json
{
  "slug": "next-film", "title": "Next Film", "year": "2028", "status": "upcoming", "stage": "In development",
  "tagline": "A short line", "synopsis": "One or two sentences.",
  "images": {
    "poster": { "source": "next-poster.jpg", "file": "poster-next-film.jpg", "alt": "Next Film poster" },
    "stills": [],
    "home": { "source": "next-poster.jpg", "file": "hero-next-film.jpg", "alt": "Next Film poster" },
    "lead": { "file": "hero-next-film.jpg", "alt": "Next Film poster" }
  }
}
```

- `home` is the picture shown full-screen on the home page when the title is hovered; `lead` is the picture at the top
  of the film's own page. A released film normally reuses its stills; an upcoming film gets an enlarged, sharpened
  copy of its poster or artwork (`source` plus a `hero-…` file name).
- Optional extras, as used by existing films: `plain_title` (a version of the title without entities, used in search
  data), `director`/`runtime`/`languages` on upcoming films, `title_note`, `concept_art`, `watch_checked`.
- `trailer_uploaded` is the date and time the trailer was uploaded to YouTube; Google requires it.

## Shop products, team, site-wide

- **Switch a product on:** in `content/shop.json` set `"availability": "available"` and fill in `"price"` and `"url"`
  (its Fourthwall page). Back to `"coming-soon"` means an empty `"url"`.
- **Team:** one entry per person in `content/team.json`; the photo is defined like any other picture.
- **Social links:** `content/site.json` → `social`. An empty `"url"` hides that link.

## Preview and publish

```sh
pip install -r requirements.txt          # once (only Pillow)
python3 02_BUILD/test_content.py         # checks the content files and the checker itself
python3 02_BUILD/build.py                # checks the content, then writes the site into 01_SITE/
python3 02_BUILD/preview_server.py       # open http://127.0.0.1:4173
```

`01_SITE/` is generated output: never edit or commit it.

1. Work on a branch, never on `main`: `git checkout -b news-my-new-post`.
2. Commit the changed `content/` files and any new pictures, push, and open a pull request.
3. Netlify builds a deploy preview for the pull request. Check the new page there.
4. Raj approves and merges; the live site updates about a minute later.
