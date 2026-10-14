# -*- coding: utf-8 -*-
"""Tests for the browser snippets in scripts/web (nearby_lookup.js, portal_views.js, hero_photo.js).

    python -m unittest tests.test_web_snippets      (from the skill folder)

The snippets run in the in-app browser against a real site. Here they run under Node against a pretend site
(tests/web_harness.js) that answers the way the real one has: a {}&& prefix on every answer, a property type
filter that lets the wrong homes through, event times in UTC. Skipped when Node is not installed. Synthetic
data only.
"""
import json
import os
import shutil
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
WEB = os.path.join(SKILL, "scripts", "web")
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node is not installed")
class Snippets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run = subprocess.run([NODE, os.path.join(HERE, "web_harness.js"), WEB], capture_output=True, text=True, timeout=120)
        if run.returncode:
            raise AssertionError("the snippets did not run under Node:\n" + run.stderr[-2000:])
        cls.out = json.loads(run.stdout)
        cls.raw = run.stdout

    def test_candidates_are_the_same_type_city_beds_and_size_and_never_the_subject(self):
        r = self.out["nearby"]["candidates"]
        self.assertTrue(r["ok"])
        self.assertEqual((r["mode"], r["as_of"], r["subject"]), ("candidates", "2026-04-13", {"id": 9000, "found": True}))
        self.assertEqual([h["address"] for h in r["homes"]], ["14 Sample Fern Ln", "9 Sample Cedar Ct", "52 Sample Birch Dr"])
        self.assertEqual(r["dropped"], {"city": 1, "size": 1, "beds": 1, "type": 1})     # the filter let a mobile home through; its own type did not
        self.assertTrue(all(h["type"] == "Single Family Residential" and h["city"] == "Fixture City" for h in r["homes"]))
        self.assertLessEqual(len(r["homes"]), 12)

    def test_dates_are_pacific_and_the_first_contract_date_wins(self):
        homes = dict((h["id"], h) for h in self.out["nearby"]["candidates"]["homes"])
        self.assertEqual(homes[9003]["list_date"], "2026-03-28")          # 04:30 UTC on Mar 29 is the evening of Mar 28 in California
        self.assertEqual(homes[9003]["pending_date"], "2026-04-09")       # the first Pending event, not the later copy
        self.assertEqual(homes[9003]["status"], "pending")
        self.assertEqual((homes[9004]["status"], homes[9004]["pending_date"], homes[9004]["sold_date"], homes[9004]["sold_price"], homes[9004]["list_price"]),
                         ("sold", "2026-03-19", "2026-04-07", 1182000, 1175000))
        self.assertEqual((homes[9001]["status"], homes[9001]["list_price"], homes[9001]["list_date"]), ("active", 1210000, "2026-04-10"))

    def test_the_search_is_asked_the_way_that_works(self):
        calls = self.out["nearby"]["candidates_calls"]
        self.assertIn("mpt=99", calls[0])                                 # without it the site ignores the filters
        self.assertIn("status=131", calls[0])
        self.assertIn("status=9&sold_within_days=120", calls[1])
        self.assertEqual(len([c for c in calls if "/gis?" in c]), 2)
        self.assertLessEqual(len(calls), 3 + 2 * 12)

    def test_the_watch_list_comes_back_one_home_each_even_when_one_has_left_the_market(self):
        r = self.out["nearby"]["watch"]
        self.assertEqual([h["id"] for h in r["homes"]], [9003, 9004, 9020])
        gone = r["homes"][2]
        self.assertEqual((gone["status"], gone["off_date"], gone["address"]), ("withdrawn", "2026-03-20", "60 Sample Gone Way"))
        self.assertEqual(gone["price_change"], {"date": "2026-02-01", "from": 1300000, "to": 1250000})
        self.assertEqual(self.out["nearby"]["watch_calls"], 5)            # two searches and one history each

    def test_a_block_or_a_human_check_stops_at_the_first_request(self):
        n = self.out["nearby"]
        self.assertEqual(n["blocked"], {"ok": False, "blocked": True, "status": 403, "requests": 1})
        self.assertEqual(n["blocked_calls"], 1)                           # nothing is retried and nothing else is tried
        self.assertEqual((n["captcha"]["ok"], n["captcha"]["captcha"], n["captcha"]["requests"]), (False, True, 1))
        self.assertEqual((n["no_region"]["ok"], n["no_region_calls"]), (False, 0))
        with open(os.path.join(WEB, "nearby_lookup.js"), encoding="utf-8") as f:
            code = f.read()
        self.assertNotIn("retry", code.lower().replace("nothing is retried", "").replace("do not add retries", ""))

    def test_the_results_are_compact(self):
        for key in ("candidates", "watch"):
            self.assertLess(len(json.dumps(self.out["nearby"][key], separators=(",", ":"))), 12000)
        for h in self.out["nearby"]["candidates"]["homes"]:
            self.assertLessEqual(set(h), set(("id", "address", "city", "type", "beds", "baths", "sqft", "status", "list_price", "list_date",
                                              "pending_date", "sold_date", "sold_price", "off_date", "price_change")))

    def test_portal_views_returns_only_the_four_fields(self):
        p = self.out["portal"]
        self.assertEqual(p[0], {"portal": "Zillow", "views": 1812, "saves": 31, "as_of": "2026-04-13"})       # 03:00 UTC on Apr 14 is still Apr 13 Pacific
        self.assertEqual(p[1], {"portal": "Redfin", "views": 240, "saves": 12, "as_of": "2026-04-13"})        # 'Views: 240 Favorites 12' is not 240 saves
        self.assertEqual(p[2], {"portal": "Zillow", "captcha": True})
        self.assertEqual((p[3]["views"], p[3]["saves"]), (None, None))    # 'mountain views' is not a count
        self.assertEqual(p[4], {"portal": "example-portal.com", "blocked": True})

    def test_hero_photo_is_an_https_share_image_or_the_first_large_photo_or_nothing(self):
        h = self.out["hero"]
        self.assertEqual(h[0], {"photo_url": "https://photos.example.test/218/front.jpg", "width": 1600, "height": 1067,
                                "page": "https://example.test/homes/218-sample-glen", "from": "share image"})
        self.assertEqual([x["photo_url"] for x in h[1:4]], [None, None, None])
        self.assertIn("not at an https address", h[1]["why"])
        self.assertIn("names no share image and shows no photo", h[2]["why"])
        self.assertEqual(h[4], {"photo_url": "https://media.example.test/218/living.jpg", "width": 2400, "height": 1600,
                                "page": "https://example.test/homes/218-sample-glen", "from": "first large photo on the page"})

    def test_no_snippet_types_into_a_page_or_sends_anything_elsewhere(self):
        for name in os.listdir(WEB):
            with open(os.path.join(WEB, name), encoding="utf-8") as f:
                code = f.read()
            with self.subTest(snippet=name):
                for word in (".submit(", ".click(", ".value =", "XMLHttpRequest", "sendBeacon", "localStorage", "document.cookie", "method:", "POST"):
                    self.assertNotIn(word, code)
                self.assertNotRegex(code, r"https?://(?!\.\.\.)[a-z0-9.-]+\.[a-z]{2,}")        # no address but the page's own origin
                self.assertFalse(any(ord(ch) > 126 for ch in code))


if __name__ == "__main__":
    unittest.main()
