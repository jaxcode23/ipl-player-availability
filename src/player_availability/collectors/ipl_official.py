from datetime import datetime

from .base import BaseCollector, RawData
from .http_client import fetch_with_retry
from .rss_utils import parse_rss_date, parse_rss_items


class IPLOfficialCollector(BaseCollector):
    def __init__(
        self,
        url: str | None = None,
        *,
        max_retries: int = 3,
        timeout: float = 30.0,
    ) -> None:
        self._url = url or "https://www.iplt20.com/rss/news"
        self._max_retries = max_retries
        self._timeout = timeout

    @property
    def source_name(self) -> str:
        return "ipl_official"

    def collect(self) -> list[RawData]:
        xml_text = fetch_with_retry(
            self._url,
            max_retries=self._max_retries,
            timeout=self._timeout,
        )
        items = parse_rss_items(xml_text)
        return [
            RawData(
                source_name=self.source_name,
                title=item.get("title", ""),
                content=item.get("description", ""),
                url=item.get("link", ""),
                published_at=_parse(item.get("pub_date")),
            )
            for item in items
        ]


def _parse(date_str: str | None) -> datetime | None:
    return parse_rss_date(date_str)
