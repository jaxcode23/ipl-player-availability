from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree.ElementTree import fromstring


def parse_rss_items(xml_content: str) -> list[dict[str, str]]:
    root = fromstring(xml_content)
    items: list[dict[str, str]] = []

    channel = root.find("channel")
    if channel is None:
        return items

    for item_elem in channel.findall("item"):
        item: dict[str, str] = {}
        for child in item_elem:
            tag = _strip_ns(child.tag)
            if tag == "title":
                item["title"] = child.text or ""
            elif tag == "link":
                item["link"] = child.text or ""
            elif tag == "description":
                item["description"] = child.text or ""
            elif tag == "pubDate":
                item["pub_date"] = child.text or ""
            elif tag == "guid":
                item.setdefault("link", child.text or "")
        if "title" in item or "link" in item:
            items.append(item)

    return items


def parse_rss_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def _strip_ns(tag: str) -> str:
    idx = tag.rfind("}")
    return tag if idx == -1 else tag[idx + 1 :]
