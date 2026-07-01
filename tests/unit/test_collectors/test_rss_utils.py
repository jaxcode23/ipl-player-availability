from datetime import datetime
from xml.etree.ElementTree import ParseError

import pytest

from player_availability.collectors.rss_utils import parse_rss_date, parse_rss_items

_RSS_WITH_ITEMS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Test Feed</title>
<item>
<title>Player A injured</title>
<link>https://example.com/a</link>
<description>&lt;p&gt;Player A is out&lt;/p&gt;</description>
<pubDate>Mon, 01 Apr 2026 10:30:00 GMT</pubDate>
</item>
<item>
<title>Player B returns</title>
<link>https://example.com/b</link>
<description>Player B is back in squad</description>
<pubDate>Tue, 02 Apr 2026 14:00:00 GMT</pubDate>
</item>
</channel>
</rss>"""

_RSS_EMPTY = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Empty Feed</title>
</channel>
</rss>"""


def test_parse_valid_rss() -> None:
    items = parse_rss_items(_RSS_WITH_ITEMS)
    assert len(items) == 2
    assert items[0]["title"] == "Player A injured"
    assert items[0]["link"] == "https://example.com/a"
    assert items[0]["description"] == "<p>Player A is out</p>"
    assert items[0]["pub_date"] == "Mon, 01 Apr 2026 10:30:00 GMT"
    assert items[1]["title"] == "Player B returns"


def test_parse_empty_feed() -> None:
    items = parse_rss_items(_RSS_EMPTY)
    assert items == []


def test_parse_malformed_xml() -> None:
    with pytest.raises(ParseError):
        parse_rss_items("not xml")


def test_item_missing_title_uses_link() -> None:
    xml = """<?xml version="1.0"?>
<rss version="2.0"><channel>
<item><link>https://example.com/no-title</link></item>
</channel></rss>"""
    items = parse_rss_items(xml)
    assert len(items) == 1
    assert items[0].get("title", "") == ""
    assert items[0]["link"] == "https://example.com/no-title"


def test_parse_rss_date_valid() -> None:
    dt = parse_rss_date("Mon, 01 Apr 2026 10:30:00 GMT")
    assert dt == datetime(2026, 4, 1, 10, 30, 0)


def test_parse_rss_date_none() -> None:
    assert parse_rss_date(None) is None


def test_parse_rss_date_empty() -> None:
    assert parse_rss_date("") is None


def test_parse_rss_date_invalid() -> None:
    assert parse_rss_date("not a date") is None
