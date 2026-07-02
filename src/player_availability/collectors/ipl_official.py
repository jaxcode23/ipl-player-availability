from .generic_rss import GenericRSSCollector


class IPLOfficialCollector(GenericRSSCollector):
    def __init__(
        self,
        url: str | None = None,
        *,
        max_retries: int = 3,
        timeout: float = 30.0,
    ) -> None:
        super().__init__(
            source_name="ipl_official",
            url=url or "https://www.iplt20.com/rss/news",
            max_retries=max_retries,
            timeout=timeout,
        )
