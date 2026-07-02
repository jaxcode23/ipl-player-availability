from datetime import datetime

from .base import BaseCollector, RawData
from .http_client import fetch_with_retry
from .rss_utils import parse_rss_date, parse_rss_items


class GenericRSSCollector(BaseCollector):
    def __init__(
        self,
        source_name: str,
        url: str,
        *,
        max_retries: int = 3,
        timeout: float = 30.0,
        fetch_full_article: bool = False,
    ) -> None:
        self._source_name = source_name
        self._url = url
        self._max_retries = max_retries
        self._timeout = timeout
        self._fetch_full_article = fetch_full_article

    @property
    def source_name(self) -> str:
        return self._source_name

    def collect(self) -> list[RawData]:
        xml_text = fetch_with_retry(
            self._url,
            max_retries=self._max_retries,
            timeout=self._timeout,
        )
        items = parse_rss_items(xml_text)
        results: list[RawData] = []
        for item in items:
            content = item.get("description", "")
            article_url = item.get("link", "")
            if self._fetch_full_article and article_url:
                try:
                    content = self._fetch_article_text(article_url)
                except Exception:
                    pass
            results.append(
                RawData(
                    source_name=self.source_name,
                    title=item.get("title", ""),
                    content=content,
                    url=article_url,
                    published_at=_parse(item.get("pub_date")),
                )
            )
        return results

    def _fetch_article_text(self, url: str) -> str:
        html = fetch_with_retry(
            url,
            max_retries=self._max_retries,
            timeout=self._timeout,
        )
        from ..parsers.utils import clean_html

        return clean_html(html)


def _parse(date_str: str | None) -> datetime | None:
    return parse_rss_date(date_str)
