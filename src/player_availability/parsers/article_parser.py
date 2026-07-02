from ..collectors.base import RawData
from .base import BaseParser, ParsedRecord
from .rule_engine import parse_article


class GenericArticleParser(BaseParser):
    def __init__(self, source_name: str) -> None:
        self._source_name = source_name

    @property
    def supported_source(self) -> str:
        return self._source_name

    def parse(self, raw_data: RawData) -> list[ParsedRecord]:
        return parse_article(raw_data, source_name=self.supported_source)
