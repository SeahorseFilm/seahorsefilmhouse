#!/usr/bin/env python3
"""Checks the content files and the loader's error messages. No extra packages needed.

Run:  python3 02_BUILD/test_content.py
"""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from content_loader import ContentError, load_content  # noqa: E402

CONTENT = HERE.parent / "content"
SOURCE_IMAGES, SHOP_PHOTOS = HERE / "source_images", HERE / "shop_photos"


class RealContent(unittest.TestCase):
    def test_content_is_valid(self):
        c = load_content(CONTENT, SOURCE_IMAGES, SHOP_PHOTOS)
        self.assertTrue(c.films and c.news and c.team and c.products)
        self.assertEqual([f["slug"] for f in c.films][:3], ["open-24-hours", "dark-light", "daddys-girl"])

    def test_news_is_newest_first(self):
        dates = [p["date"] for p in load_content(CONTENT, SOURCE_IMAGES, SHOP_PHOTOS).news]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_every_picture_has_alt_text(self):
        c = load_content(CONTENT, SOURCE_IMAGES, SHOP_PHOTOS)
        for p in c.news:
            self.assertTrue(p["image_alt"], p["slug"])
        for f in c.films:
            self.assertTrue(c.image_alts[f["poster"]] and c.image_alts[f["page_hero"]], f["slug"])


class BadContent(unittest.TestCase):
    """Each case breaks a copy of the content in one way and expects a clear error naming the problem."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        shutil.copytree(CONTENT, self.dir / "content")
        self.addCleanup(shutil.rmtree, self.dir)

    def edit(self, name, change):
        path = self.dir / "content" / f"{name}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        change(data)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def expect(self, *fragments):
        with self.assertRaises(ContentError) as ctx:
            load_content(self.dir / "content", SOURCE_IMAGES, SHOP_PHOTOS)
        text = str(ctx.exception)
        for fragment in fragments:
            self.assertIn(fragment, text)

    def test_missing_required_field(self):
        self.edit("films", lambda d: d["films"][0].pop("tagline"))
        self.expect('films.json', 'films[0]', 'missing "tagline"')

    def test_released_film_needs_its_watch_details(self):
        self.edit("films", lambda d: d["films"][0].pop("trailer_url"))
        self.expect('missing "trailer_url"')

    def test_duplicate_film_slug(self):
        self.edit("films", lambda d: d["films"][1].update(slug="open-24-hours"))
        self.expect('slug "open-24-hours" is used by another film')

    def test_duplicate_news_slug(self):
        self.edit("news", lambda d: d["posts"][1].update(slug=d["posts"][0]["slug"]))
        self.expect("is used by another post")

    def test_malformed_json(self):
        path = self.dir / "content" / "team.json"
        path.write_text(path.read_text(encoding="utf-8")[:-40], encoding="utf-8")
        self.expect("team.json: not valid JSON, line")

    def test_missing_file(self):
        (self.dir / "content" / "shop.json").unlink()
        self.expect("shop.json: file is missing")

    def test_bad_date(self):
        self.edit("news", lambda d: d["posts"][0].update(date="2026-13-40"))
        self.expect("must be a real date written YYYY-MM-DD")

    def test_bad_trailer_url(self):
        self.edit("films", lambda d: d["films"][0].update(trailer_url="https://youtu.be/iI7yLprZheA"))
        self.expect("trailer_url", "must look like https://www.youtube.com/watch?v=")

    def test_picture_not_defined(self):
        self.edit("films", lambda d: d["films"][0]["images"]["lead"].update(file="still-nowhere.jpg"))
        self.expect('picture "still-nowhere.jpg" is not defined anywhere')

    def test_source_image_missing(self):
        self.edit("films", lambda d: d["films"][0]["images"]["poster"].update(source="not-there.jpg"))
        self.expect('"not-there.jpg" is not in 02_BUILD/source_images/')

    def test_news_link_to_unknown_film(self):
        self.edit("news", lambda d: d["posts"][0]["body"].append('See <a href="../films/nothing.html">this</a>'))
        self.expect('links to film "nothing"')

    def test_available_product_needs_price_and_url(self):
        self.edit("shop", lambda d: d["products"][0].update(availability="available"))
        self.expect('needs both "price" and "url"')

    def test_duplicate_product_slug(self):
        self.edit("shop", lambda d: d["products"][1].update(slug=d["products"][0]["slug"]))
        self.expect("is used by another product")

    def test_shop_photo_missing(self):
        self.edit("shop", lambda d: d["products"][0]["photos"].append("not-there.png"))
        self.expect('"not-there.png" is not in 02_BUILD/shop_photos/')

    def test_buy_link_must_be_https(self):
        self.edit("shop", lambda d: d["products"][0].update(
            availability="available", price="$35", url="http://example.com/tee"))
        self.expect('must start with "https://"')

    def test_available_product_with_todo_raj(self):
        self.edit("shop", lambda d: d["products"][0].update(
            availability="available", price="$35", url="https://example.com/tee", text="TODO-RAJ: description"))
        self.expect('still contains "TODO-RAJ"')
        self.edit("shop", lambda d: d["products"][1].update(slug="tee-black"))
        self.expect('slug "tee-black" is used by another product')

    def test_duplicate_person(self):
        self.edit("team", lambda d: d["people"][1].update(name=d["people"][0]["name"]))
        self.expect("is listed twice")

    def test_dates_must_be_written_exactly(self):
        for bad in ("2026-1-5", "20261105", "2026-W45-1", "5 November 2026", ""):
            with self.subTest(date=bad):
                self.edit("news", lambda d: d["posts"][0].update(date=bad))
                with self.assertRaises(ContentError):
                    load_content(self.dir / "content", SOURCE_IMAGES, SHOP_PHOTOS)

    def test_news_picture_missing(self):
        self.edit("news", lambda d: d["posts"][0]["image"].update(file="never-defined.jpg"))
        self.expect('picture "never-defined.jpg" is not defined anywhere')

    def test_phone_picture_missing(self):
        def change(d):
            home = next(f["images"]["home"] for f in d["films"] if "phone" in f["images"].get("home", {}))
            home["phone"]["source"] = "no-phone-image.jpg"
        self.edit("films", change)
        self.expect('"no-phone-image.jpg" is not in 02_BUILD/source_images/')

    def test_bad_web_addresses(self):
        cases = {"http://example.com/x": 'must start with "https://"',
                 "https://exa mple.com/x": "has a space in it",
                 "https://localhost/x": "is not a full web address",
                 "https://": "is not a full web address"}
        for url, message in cases.items():
            with self.subTest(url=url):
                self.edit("news", lambda d: d["posts"][0].update(sources=[{"label": "x", "url": url}]))
                self.expect(message)
                self.edit("shop", lambda d: d["products"][0].update(availability="available", price="£1", url=url))
                self.expect("products[0] (tee-black).url", message)

    def test_available_product_with_no_price(self):
        self.edit("shop", lambda d: d["products"][0].update(availability="available", url="https://example.com/tee"))
        self.expect('needs both "price" and "url"')

    def test_available_product_with_no_url(self):
        self.edit("shop", lambda d: d["products"][0].update(availability="available", price="£25"))
        self.expect('needs both "price" and "url"')

    def test_todo_left_in_available_product(self):
        self.edit("shop", lambda d: d["products"][0].update(
            availability="available", price="£25", url="https://example.com/tee",
            text="TODO-RAJ: product description"))
        self.expect("products[0] (tee-black).text", "TODO-RAJ", 'set availability back to "coming-soon"')

    def test_todo_is_fine_while_coming_soon(self):
        self.edit("shop", lambda d: d["products"][0].update(text="TODO-RAJ: product description"))
        load_content(self.dir / "content", SOURCE_IMAGES, SHOP_PHOTOS)

    def test_unknown_field_is_a_typo(self):
        self.edit("films", lambda d: d["films"][0].update(taglin="x"))
        self.expect('unknown field "taglin"')

    def test_empty_text(self):
        self.edit("team", lambda d: d["people"][0].update(role="  "))
        self.expect("must not be empty")

    def test_all_problems_reported_together(self):
        self.edit("films", lambda d: (d["films"][0].pop("tagline"), d["films"][1].update(status="finished")))
        self.edit("news", lambda d: d["posts"][0].update(date="yesterday"))
        self.expect('missing "tagline"', '"released" or "upcoming"', "YYYY-MM-DD")

    def test_underscore_notes_are_allowed(self):
        self.edit("films", lambda d: d["films"][0].update(_note="a note for editors"))
        load_content(self.dir / "content", SOURCE_IMAGES, SHOP_PHOTOS)


class BuildStopsOnBadContent(unittest.TestCase):
    def test_build_exits_with_the_message(self):
        import build  # needs Pillow, which the build needs anyway

        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        shutil.copytree(CONTENT, tmp / "content")
        path = tmp / "content" / "films.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["films"][0].pop("synopsis")
        path.write_text(json.dumps(data), encoding="utf-8")
        old = build.CONTENT
        build.CONTENT = tmp / "content"
        self.addCleanup(setattr, build, "CONTENT", old)
        with self.assertRaises(SystemExit) as ctx:
            build.load_site_content()
        self.assertIn('missing "synopsis"', str(ctx.exception))
        self.assertIn("CONTENT_EDITING.md", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
