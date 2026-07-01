from datetime import datetime

from player_availability.collectors.base import RawData
from player_availability.collectors.mock import MockCollector


def test_default_items_deterministic() -> None:
    collector = MockCollector()
    results = collector.collect()
    assert len(results) == 3
    for item in results:
        assert item.source_name == "mock"
        assert isinstance(item.title, str)
        assert isinstance(item.content, str)
        assert isinstance(item.url, str)


def test_default_items_have_expected_titles() -> None:
    collector = MockCollector()
    results = collector.collect()
    assert results[0].title == "MS Dhoni suffers knee injury during training"
    assert results[1].title == "Virat Kohli declared fit for IPL 2026"
    assert results[2].title == "Jasprit Bumrah ruled out of IPL 2026 due to back injury"


def test_custom_items() -> None:
    custom = [
        RawData(
            source_name="mock",
            title="Custom Article",
            content="Custom content",
            url="https://example.com/custom",
            published_at=datetime(2026, 4, 1, 0, 0, 0),
        ),
    ]
    collector = MockCollector(items=custom)
    results = collector.collect()
    assert len(results) == 1
    assert results[0].title == "Custom Article"
    assert results[0].source_name == "mock"


def test_collect_returns_copy() -> None:
    collector = MockCollector()
    first = collector.collect()
    second = collector.collect()
    assert first == second
    assert first is not second


def test_source_name_consistent() -> None:
    collector = MockCollector()
    for item in collector.collect():
        assert item.source_name == "mock"
