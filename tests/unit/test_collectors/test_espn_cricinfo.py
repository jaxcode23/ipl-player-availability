from unittest.mock import patch

from player_availability.collectors.base import RawData
from player_availability.collectors.espn_cricinfo import ESPNCricinfoRSSCollector

_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>ESPN Cricinfo</title>
<item>
<title>Kohli returns to form with century</title>
<link>https://www.espncricinfo.com/story/1</link>
<description>Virat Kohli scored a brilliant century in the warm-up match.</description>
<pubDate>Wed, 03 Apr 2026 16:45:00 GMT</pubDate>
</item>
</channel>
</rss>"""


@patch(
    "player_availability.collectors.generic_rss.fetch_with_retry",
    return_value=_RSS_XML,
)
def test_collect_returns_raw_data_objects(mock_fetch) -> None:
    collector = ESPNCricinfoRSSCollector(max_retries=1, timeout=5.0)
    results = collector.collect()

    assert len(results) == 1
    item = results[0]
    assert isinstance(item, RawData)
    assert item.source_name == "espn_cricinfo"
    assert item.title == "Kohli returns to form with century"
    assert item.url == "https://www.espncricinfo.com/story/1"
    assert item.content == "Virat Kohli scored a brilliant century in the warm-up match."
    assert item.published_at is not None


@patch(
    "player_availability.collectors.generic_rss.fetch_with_retry",
    return_value=_RSS_XML,
)
def test_source_name_consistent(mock_fetch) -> None:
    collector = ESPNCricinfoRSSCollector(max_retries=1, timeout=5.0)
    results = collector.collect()

    for item in results:
        assert item.source_name == "espn_cricinfo"


def test_default_url_is_set() -> None:
    collector = ESPNCricinfoRSSCollector()
    assert collector._url == "https://www.espncricinfo.com/rss/content/story/feeds"
