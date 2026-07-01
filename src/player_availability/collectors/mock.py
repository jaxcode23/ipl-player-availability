from datetime import datetime

from .base import BaseCollector, RawData


class MockCollector(BaseCollector):
    def __init__(self, items: list[RawData] | None = None) -> None:
        self._items = items if items is not None else _default_items()

    @property
    def source_name(self) -> str:
        return "mock"

    def collect(self) -> list[RawData]:
        return list(self._items)


def _default_items() -> list[RawData]:
    return [
        RawData(
            source_name="mock",
            title="MS Dhoni suffers knee injury during training",
            content=(
                "<p>Chennai Super Kings captain MS Dhoni has suffered a knee injury"
                " during a training session at the MA Chidambaram Stadium.</p>"
            ),
            url="https://example.com/dhoni-injury",
            published_at=datetime(2026, 4, 1, 10, 30, 0),
        ),
        RawData(
            source_name="mock",
            title="Virat Kohli declared fit for IPL 2026",
            content=(
                "<p>Royal Challengers Bengaluru star Virat Kohli has been declared"
                " fully fit ahead of the upcoming IPL 2026 season.</p>"
            ),
            url="https://example.com/kohli-fit",
            published_at=datetime(2026, 4, 2, 14, 0, 0),
        ),
        RawData(
            source_name="mock",
            title="Jasprit Bumrah ruled out of IPL 2026 due to back injury",
            content=(
                "<p>Mumbai Indians pace spearhead Jasprit Bumrah has been ruled out"
                " of the entire IPL 2026 season due to a recurring back injury.</p>"
            ),
            url="https://example.com/bumrah-out",
            published_at=datetime(2026, 4, 3, 9, 15, 0),
        ),
    ]
