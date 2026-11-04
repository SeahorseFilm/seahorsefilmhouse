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

    def test_featured_must_be_true_or_false(self):
        self.edit("shop", lambda d: d["products"][0].update(featured="yes"))
        self.expect("products[0] (tee-black).featured", "must be true or false")

    def test_at_most_four_featured(self):
        def change(d):
            for p in d["products"]:
                p["featured"] = True
        self.edit("shop", change)
        self.expect("5 products are featured", "room for 4")

    def test_unknown_category(self):
        self.edit("shop", lambda d: d["products"][0].update(category="Hats"))
        self.expect("products[0] (tee-black).category", "Clothing, Prints, Accessories", '"Hats"')

    def test_featured_and_category_are_optional(self):
        def change(d):
            d["products"][0].update(featured=True, category="Clothing")
            d["products"][1].update(featured=False, category="")  # as a CMS form may save an unticked box / empty select
        self.edit("shop", change)
        products = load_content(self.dir / "content", SOURCE_IMAGES, SHOP_PHOTOS).products
        self.assertEqual([(p["featured"], p["category"]) for p in products[:3]],
                         [(True, "Clothing"), (False, None), (False, None)])

    def test_grouped_shop_needs_every_category(self):
        def change(d):
            base = d["products"][0]
            d["products"] += [dict(base, slug=f"extra-{n}", category="Clothing") for n in range(5)]
        self.edit("shop", change)
        self.expect('products[1] (tee-grey): missing "category"', "more than 9 products")

    def test_underscore_notes_are_allowed(self):
        self.edit("films", lambda d: d["films"][0].update(_note="a note for editors"))
        load_content(self.dir / "content", SOURCE_IMAGES, SHOP_PHOTOS)


class ShopLayout(unittest.TestCase):
    """The home-page shop row and the grouping of the Shop page (build.py), with pictures stubbed out."""

    def setUp(self):
        import build  # needs Pillow, which the build needs anyway

        self.build = build
        for name, value in (("picture", lambda name, *a, **k: f"[{name}]"), ("PRODUCTS", [])):
            self.addCleanup(setattr, build, name, getattr(build, name))
            setattr(build, name, value)

    def products(self, n, **extra):
        return [dict({"slug": f"p{i}", "name": f"P{i}", "text": "t", "availability": "coming-soon", "price": "",
                      "url": "", "featured": False, "category": None, "image": f"shop-p{i}.jpg"}, **extra)
                for i in range(n)]

    def test_home_row_falls_back_to_first_four(self):
        self.build.PRODUCTS = self.products(6)
        self.assertEqual([p["slug"] for p in self.build.home_products()], ["p0", "p1", "p2", "p3"])

    def test_home_row_shows_only_featured(self):
        self.build.PRODUCTS = self.products(6)
        for i in (5, 2):
            self.build.PRODUCTS[i]["featured"] = True
        self.assertEqual([p["slug"] for p in self.build.home_products()], ["p2", "p5"])
        # a product with a single picture (like the book) can be featured too
        self.assertIn("[shop-p5.jpg]", self.build.shop_card(self.build.PRODUCTS[5]))

    def test_shop_not_grouped_up_to_nine(self):
        self.build.PRODUCTS = self.products(9, category="Prints")
        html = self.build.shop_sections()
        self.assertEqual(html.count('class="grid three shop-grid"'), 1)
        self.assertNotIn("Prints</h2>", html)
        self.assertEqual(html.count('<h2 class="product-name">'), 9)

    def test_shop_grouped_above_nine(self):
        self.build.PRODUCTS = self.products(10)
        for p, cat in zip(self.build.PRODUCTS, ["Accessories", "Clothing"] * 5):
            p["category"] = cat
        html = self.build.shop_sections()
        # categories in fixed order, empty ones (Prints) left out, products as h3 under each h2
        self.assertLess(html.index(">Clothing</h2>"), html.index(">Accessories</h2>"))
        self.assertNotIn("Prints", html)
        self.assertEqual(html.count('class="grid three shop-grid"'), 2)
        self.assertEqual(html.count('<h3 class="product-name">'), 10)
        self.assertLess(html.index('id="p1"'), html.index('id="p3"'))  # file order inside a group
        self.assertEqual(html.count('class="product"'), 10)


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
