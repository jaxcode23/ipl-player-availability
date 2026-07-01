from ..collectors.base import RawData
from .base import BaseParser, ParsedRecord
from .rule_engine import parse_article


class ESPNCricinfoParser(BaseParser):
    @property
    def supported_source(self) -> str:
        return "espn_cricinfo"

    def parse(self, raw_data: RawData) -> list[ParsedRecord]:
        return parse_article(raw_data, source_name=self.supported_source)
