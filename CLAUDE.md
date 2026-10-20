# Seahorse Filmhouse website — rules for agents

Live site: https://seahorsefilmhouse.com (Netlify). **Merging into `main` publishes the live site within about a minute.**
Never push to `main`. Work on a branch and open a pull request; Raj (the owner) approves every merge.

## How the site is built

- Editorial content lives in `content/*.json`: films, news, team, shop products, social links and contact details (see `CONTENT_EDITING.md`). Page templates, layout, `<head>` metadata, structured data and the sitemap live in `02_BUILD/build.py`; the build checks the content files and stops with a clear message if one is wrong.
- Styles: `02_BUILD/site.css`. Script: `02_BUILD/site.js`. Images: `02_BUILD/source_images/` and `02_BUILD/shop_photos/` (resized by build.py with Pillow).
- Build: `pip install -r requirements.txt && python3 02_BUILD/build.py` writes the site into `01_SITE/`. Check the content files with `python3 02_BUILD/test_content.py`.
- `01_SITE/` is generated output. It is git-ignored and never committed or edited by hand.
- Preview locally: `python3 02_BUILD/preview_server.py`, then open http://127.0.0.1:4173.
- Netlify runs the same build (see `netlify.toml`) and makes a deploy preview for every pull request. Use it for before/after checks: live site = before, deploy preview = after.
- `02_BUILD/shop_images.py` draws illustrated shop mock-ups. It is a manual tool and not part of the build.

## Do not change without Raj's explicit say-so

- **Copy.** No rewording of any visible text: film synopses, news posts, About text, button labels. Fix typos only if asked. If a new page needs text that doesn't exist yet, write `TODO-RAJ: <what is needed>`. Never invent facts, credits, dates, quotes or reviews.
- **Look ("Bone & Blur", A24-style layout).** Keep the colour tokens in `:root` of `site.css` (bone ground `#f1eee8`, warm black ink `#1a1714`). Image areas and the footer stay dark.
- **Fonts:** Inter Tight (headings and body), Bodoni Moda (taglines and editorial lines), DM Mono (dates and labels). No new fonts.
- **Logo:** lowercase "sfh" in heavy Bodoni Moda, centred over SEAHORSE FILMHOUSE in small sans capitals. Don't redraw, recolour or swap it.
- **Signature effects:** the home hero film list, where hovering a title brings that film's image into focus out of blur, and sections that resolve out of blur on scroll. You may make them cheaper (for example GPU-friendly properties or smaller images) and respect `prefers-reduced-motion`, but don't remove them or change how they look.
- **Location wording:** Los Angeles, London, Mumbai and UAE are listed as places of operation. Never call any of them a head office, base or registered address. Never mention Burbank.
- **Tokyo (upcoming film):** use only the synopsis already in `content/films.json`. The pitch deck is confidential: no plot details, characters, casting or partners.

## Keep working

- Google Analytics (`GA_ID`) loads only after the visitor presses Accept in the cookie notice. Never load it earlier.
- Contact and mailing-list forms post to Formspree. Keep the endpoint and hidden fields (`_next`, `_subject`).
- Keep the Google Search Console verification meta tag on every page.
- Keep the structured data (Organization, WebSite, Movie with trailer `uploadDate`, NewsArticle) valid.
- Keep `sitemap.xml` and `robots.txt` generation in step with the pages.

## Every pull request

- `python3 02_BUILD/build.py` runs without errors, and the Netlify deploy preview builds.
- No new dependencies, frameworks or external services without a stated reason.
- No secrets or API keys. The repo is public.
- The PR description lists every changed file, gives before/after PageSpeed Insights mobile scores (live site vs deploy preview) for pages you touched, and has a "Not verified" section for anything you couldn't check.
