from unittest.mock import patch

from player_availability.collectors.base import RawData
from player_availability.collectors.ipl_official import IPLOfficialCollector

_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>IPL News</title>
<item>
<title>Injury Update: Star Player Ruled Out</title>
<link>https://www.iplt20.com/news/1</link>
<description>&lt;p&gt;A star player has been ruled out of IPL 2026.&lt;/p&gt;</description>
<pubDate>Mon, 01 Apr 2026 12:00:00 GMT</pubDate>
</item>
<item>
<title>Team Announces Replacement</title>
<link>https://www.iplt20.com/news/2</link>
<description>Team management has announced a replacement player.</description>
<pubDate>Tue, 02 Apr 2026 08:30:00 GMT</pubDate>
</item>
</channel>
</rss>"""


@patch("player_availability.collectors.generic_rss.fetch_with_retry", return_value=_RSS_XML)
def test_collect_returns_raw_data_objects(mock_fetch) -> None:
    collector = IPLOfficialCollector(max_retries=1, timeout=5.0)
    results = collector.collect()

    assert len(results) == 2
    for item in results:
        assert isinstance(item, RawData)
        assert item.source_name == "ipl_official"
        assert item.title
        assert item.url
        assert item.content


@patch("player_availability.collectors.generic_rss.fetch_with_retry", return_value=_RSS_XML)
def test_collect_parses_all_items(mock_fetch) -> None:
    collector = IPLOfficialCollector(max_retries=1, timeout=5.0)
    results = collector.collect()

    assert results[0].title == "Injury Update: Star Player Ruled Out"
    assert results[0].url == "https://www.iplt20.com/news/1"
    assert results[0].content == "<p>A star player has been ruled out of IPL 2026.</p>"
    assert results[0].published_at is not None

    assert results[1].title == "Team Announces Replacement"


@patch("player_availability.collectors.generic_rss.fetch_with_retry", return_value=_RSS_XML)
def test_all_items_have_required_fields(mock_fetch) -> None:
    collector = IPLOfficialCollector(max_retries=1, timeout=5.0)
    results = collector.collect()

    for item in results:
        assert item.source_name == "ipl_official"
        assert isinstance(item.title, str) and len(item.title) > 0
        assert isinstance(item.content, str)
        assert isinstance(item.url, str) and len(item.url) > 0
        assert item.fetched_at is not None


def test_default_url_is_set() -> None:
    collector = IPLOfficialCollector()
    assert collector._url == "https://www.iplt20.com/rss/news"
