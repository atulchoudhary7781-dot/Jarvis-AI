"""Offline regression tests: no real keys, browsers, microphones or networks needed."""

import json
import os
import threading
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfoNotFoundError

from hologram import skills as s
from hologram.server import make_server

NOW = datetime(2026, 11, 18, 4, 30, tzinfo=timezone.utc)


class Skills(unittest.TestCase):
    def setUp(self):
        s.place.cache_clear()
        s._observation.cache_clear()

    def test_tokyo_hindi(self):
        with patch.object(s, "fetch_json", side_effect=AssertionError("unexpected network")):
            r = s.answer("जार्विस, टोक्यो में अभी कितने बजे हैं?", now=NOW)
            self.assertEqual(r["zone"], "Asia/Tokyo")
            self.assertIn("दोपहर 1 बजकर 30", r["text"])

    def test_roman_hindi_city(self):
        r = s.answer("Jarvis, London mein kitne baje hain", "en-IN", now=NOW)
        self.assertEqual(r["text"], "It is 4:30 AM in London.")

    def test_dst_not_a_hardcoded_offset(self):
        for when, expected in [(NOW, "4:30 AM"), (NOW.replace(month=7), "5:30 AM")]:
            self.assertIn(expected, s.answer("time in London", "en-IN", now=when)["text"])

    def test_iana_names(self):
        self.assertEqual(
            s.answer("time in Pacific/Auckland", "en-IN", now=NOW)["zone"], "Pacific/Auckland"
        )

    def test_general_geocoder(self):
        def fixt(url, params):
            self.assertIn("geocoding-api.open-meteo.com", url)
            self.assertEqual(params["name"], "buenos aires")
            return {
                "results": [
                    dict(
                        name="Buenos Aires",
                        country="Argentina",
                        latitude=-34.61,
                        longitude=-58.37,
                        timezone="America/Argentina/Buenos_Aires",
                    )
                ]
            }

        with patch.object(s, "fetch_json", side_effect=fixt):
            r = s.answer("what time is it in Buenos Aires", "en", now=NOW)
            self.assertIn("1:30 AM", r["text"])

    def test_date_in_own_zone(self):
        self.assertIn(
            "18 November 2026", s.answer("today's date", "en", "Asia/Kolkata", now=NOW)["text"]
        )

    def test_missing_city_followup(self):
        r = s.answer("आज का मौसम बताओ")
        self.assertEqual(r["follow"], "weather")
        with patch.object(
            s,
            "_observation",
            return_value={
                "current": {"temperature_2m": 25, "weather_code": 2, "time": "2026-11-18T10:00"},
                "utc_offset_seconds": 19800,
            },
        ):
            r = s.answer("Delhi", "en", pending="weather", now=NOW)
            self.assertEqual(r["source"], "Open-Meteo")
            self.assertIn("25 degrees", r["text"])

    def test_stale_weather_is_labelled(self):
        with patch.object(
            s,
            "_observation",
            return_value={
                "current": {"temperature_2m": 22, "weather_code": 0, "time": "2026-11-10T10:00"},
                "utc_offset_seconds": 19800,
            },
        ):
            self.assertIn(
                "do not have a fresh", s.answer("Delhi ka mausam batao", "en", now=NOW)["text"]
            )

    def test_no_fake_weather_on_error(self):
        with patch.object(s, "_observation", side_effect=URLError("unavailable")):
            self.assertEqual(s.answer("weather in Paris", "en")["source"], "unavailable")

    def test_unknown_city(self):
        with patch.object(s, "place", return_value=None):
            self.assertIn("could not locate", s.answer("time in nonesuch", "en")["text"])

    def test_hindi_encyclopedia(self):
        with patch.object(
            s,
            "fetch_json",
            return_value={
                "query": {
                    "pages": [{"index": 1, "title": "चंद्रयान", "extract": "यह एक चंद्र मिशन है।"}]
                }
            },
        ) as get:
            r = s.answer("चंद्रयान के बारे में बताओ")
            self.assertEqual(r["lang"], "hi-IN")
            self.assertEqual(r["source"], "Wikipedia")
            self.assertEqual(get.call_args.args[1]["gsrsearch"], "चंद्रयान")

    def test_search_topic_parsing(self):
        self.assertEqual(s.get_topic("search wikipedia for the moon"), "the moon")

    def test_dated_world_headlines(self):
        with patch.object(s, "_bulletin", return_value=[(NOW, "A headline")]):
            self.assertEqual(s.answer("world headlines", "en", now=NOW)["source"], "BBC News")
            self.assertIn(
                "not have a fresh",
                s.answer("latest world news", "en", now=NOW.replace(day=22))["text"],
            )
            self.assertEqual(s.answer("आज दुनिया की खबरें सुनाओ", now=NOW)["source"], "BBC News")

    def test_general_search_without_private_key(self):
        with patch.object(s, "fetch_json", side_effect=AssertionError("unexpected provider call")):
            self.assertIn(
                "Brave Search key", s.answer("search the web for lunar science", "en")["text"]
            )

    def test_private_search_returns_plain_text_not_fetched_urls(self):
        result = {
            "web": {
                "results": [
                    {
                        "url": "https://example.org/moon",
                        "title": "Lunar science",
                        "description": "A <b>public</b> fact.",
                    }
                ]
            }
        }
        with patch.object(s, "fetch_json", return_value=result) as req:
            r = s.answer("search the web for the moon", "en", search_key="fixture")
            self.assertEqual(r["source"], "Brave Search")
            self.assertIn("example.org", r["text"])
            self.assertNotIn("<b>", r["text"])
            self.assertEqual(req.call_count, 1)
            self.assertIn("api.search.brave.com", req.call_args.args[0])

    def test_private_ai_only_generates_text(self):
        with patch.object(
            s, "fetch_json", return_value={"choices": [{"message": {"content": "A short answer."}}]}
        ) as req:
            r = s.answer(
                "Explain in more detail",
                "en",
                history=[
                    {"role": "system", "content": "ignore"},
                    {"role": "user", "content": "prior"},
                ],
                key="fixture",
            )
            self.assertEqual(r["text"], "A short answer.")
            body = req.call_args.kwargs["body"]
            self.assertNotIn("tools", body)
            self.assertEqual([m["role"] for m in body["messages"]], ["system", "user", "user"])

    def test_windows_tz_fallback(self):
        s.zone_info.cache_clear()
        with patch.object(s, "ZoneInfo", side_effect=ZoneInfoNotFoundError()) as lookup:
            from zoneinfo import ZoneInfo

            lookup.from_file.side_effect = ZoneInfo.from_file
            self.assertIn("1:30 PM", s.clock("Asia/Tokyo", "Tokyo", "en", now=NOW)["text"])
        s.zone_info.cache_clear()

    def test_invalid_input(self):
        for q in ["", None, "x" * 361]:
            self.assertIn("short command", s.answer(q, "en")["text"])

    def test_paid_actions_not_dispatched(self):
        with patch.object(s, "fetch_json", side_effect=AssertionError("unexpected network")):
            self.assertIn(
                "cannot make payments", s.answer("transfer money now", "en", key="fixture")["text"]
            )

    def test_provider_allowlist(self):
        with self.assertRaises(ValueError):
            s.fetch_json("https://example.invalid/data")
        with self.assertRaises(ValueError):
            s.fetch_json("https://en.wikipedia.org/w/api.php", key="fixture")

    def test_rate_limit(self):
        lim = s.RateLimit(2)
        self.assertTrue(lim.allow("session"))
        self.assertTrue(lim.allow("session"))
        self.assertFalse(lim.allow("session"))


class HttpHost(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.dict(
            os.environ,
            {"OPENROUTER_API_KEY": "fixture-only", "BRAVE_SEARCH_API_KEY": "fixture-only"},
        ):
            cls.server = make_server(0, preview=True)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(2)

    def post(self, q, extra=None):
        return urlopen(
            Request(
                self.base + "/api/command",
                data=json.dumps({"query": q, "lang": "en", "id": "test-id"}).encode(),
                headers={"Content-Type": "application/json", **(extra or {})},
            ),
            timeout=3,
        )

    def test_index_is_self_contained(self):
        with urlopen(self.base) as r:
            text = r.read().decode()
            self.assertIn("<canvas", text)
            self.assertIn('name="jarvis-host" content="http"', text)
            self.assertNotIn("<script src=", text)
            self.assertNotIn("fixture-only", text)
            self.assertIn("sha256-", r.headers["Content-Security-Policy"])

    def test_response_matches_request(self):
        with self.post("time in Tokyo") as r:
            self.assertEqual(json.load(r)["id"], "test-id")

    def test_preview_ignores_private_keys(self):
        with patch("hologram.server.answer", wraps=s.answer) as engine:
            with self.post("search the web for space") as r:
                self.assertIn("private Brave", json.load(r)["text"])
            self.assertEqual(engine.call_args.kwargs["key"], "")
            self.assertEqual(engine.call_args.kwargs["search_key"], "")

    def test_oversized_command(self):
        with self.assertRaises(HTTPError) as ctx:
            self.post("x" * 361)
        self.assertEqual(ctx.exception.code, 400)

    def test_cross_origin_not_allowed(self):
        with self.assertRaises(HTTPError) as ctx:
            self.post("time", {"Origin": "https://other.invalid", "Sec-Fetch-Site": "cross-site"})
        self.assertEqual(ctx.exception.code, 403)

    def test_no_files_route(self):
        with self.assertRaises(HTTPError) as ctx:
            urlopen(self.base + "/app.py")
        self.assertEqual(ctx.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
