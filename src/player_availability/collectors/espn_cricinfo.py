from .generic_rss import GenericRSSCollector


class ESPNCricinfoRSSCollector(GenericRSSCollector):
    def __init__(
        self,
        url: str | None = None,
        *,
        max_retries: int = 3,
        timeout: float = 30.0,
    ) -> None:
        super().__init__(
            source_name="espn_cricinfo",
            url=url or "https://www.espncricinfo.com/rss/content/story/feeds",
            max_retries=max_retries,
            timeout=timeout,
        )
