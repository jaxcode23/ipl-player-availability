from unittest.mock import patch

from player_availability.collectors.base import RawData
from player_availability.collectors.generic_rss import GenericRSSCollector

_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Cricket News</title>
<item>
<title>Star Player Injury Update</title>
<link>https://example.com/news/1</link>
<description>A star player has been ruled out of the tournament.</description>
<pubDate>Mon, 01 Apr 2026 12:00:00 GMT</pubDate>
</item>
<item>
<title>Team Names Replacement</title>
<link>https://example.com/news/2</link>
<description>Management has announced a replacement signing.</description>
<pubDate>Tue, 02 Apr 2026 08:30:00 GMT</pubDate>
</item>
</channel>
</rss>"""


@patch("player_availability.collectors.generic_rss.fetch_with_retry", return_value=_RSS_XML)
def test_collect_returns_raw_data_objects(mock_fetch) -> None:
    collector = GenericRSSCollector(
        source_name="rediff_cricket",
        url="https://cricket.rediff.com/rss/cricketrss.xml",
        max_retries=1,
        timeout=5.0,
    )
    results = collector.collect()

    assert len(results) == 2
    for item in results:
        assert isinstance(item, RawData)
        assert item.source_name == "rediff_cricket"
        assert item.title
        assert item.url
        assert item.content


@patch("player_availability.collectors.generic_rss.fetch_with_retry", return_value=_RSS_XML)
def test_source_name_is_configurable(mock_fetch) -> None:
    collector = GenericRSSCollector(
        source_name="icc_schedule",
        url="https://www.icccricketschedule.com/rss/news.xml",
        max_retries=1,
        timeout=5.0,
    )
    results = collector.collect()

    assert len(results) == 2
    assert results[0].source_name == "icc_schedule"
    assert results[1].source_name == "icc_schedule"


@patch("player_availability.collectors.generic_rss.fetch_with_retry", return_value=_RSS_XML)
def test_collect_parses_article_data(mock_fetch) -> None:
    collector = GenericRSSCollector(
        source_name="test_source",
        url="https://example.com/rss",
        max_retries=1,
        timeout=5.0,
    )
    results = collector.collect()

    assert results[0].title == "Star Player Injury Update"
    assert results[0].url == "https://example.com/news/1"
    assert results[0].content == "A star player has been ruled out of the tournament."
    assert results[0].published_at is not None

    assert results[1].title == "Team Names Replacement"


@patch("player_availability.collectors.generic_rss.fetch_with_retry", return_value=_RSS_XML)
def test_all_items_have_required_fields(mock_fetch) -> None:
    collector = GenericRSSCollector(
        source_name="test_source",
        url="https://example.com/rss",
        max_retries=1,
        timeout=5.0,
    )
    results = collector.collect()

    for item in results:
        assert isinstance(item.title, str)
        assert isinstance(item.content, str)
        assert isinstance(item.url, str)
        assert item.fetched_at is not None


def test_collector_stores_constructor_params() -> None:
    collector = GenericRSSCollector(
        source_name="my_source",
        url="https://example.com/rss",
        max_retries=5,
        timeout=60.0,
        fetch_full_article=True,
    )
    assert collector.source_name == "my_source"
    assert collector._url == "https://example.com/rss"
    assert collector._max_retries == 5
    assert collector._timeout == 60.0
    assert collector._fetch_full_article is True
