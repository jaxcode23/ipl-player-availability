from unittest.mock import MagicMock, patch

import httpx
import pytest

from player_availability.collectors.exceptions import SourceUnavailableError
from player_availability.collectors.http_client import fetch_with_retry

_RSS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Test</title></channel></rss>"""


def _mock_response(text: str, status: int = 200) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.text = text
    resp.status_code = status
    resp.raise_for_status.return_value = None
    if status >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(f"HTTP {status}", request=MagicMock(), response=resp)
    return resp


def test_successful_fetch() -> None:
    resp = _mock_response(_RSS_SAMPLE)
    client = MagicMock(spec=httpx.Client)
    client.__enter__.return_value = client
    client.get.return_value = resp

    with patch("player_availability.collectors.http_client.httpx.Client", return_value=client):
        result = fetch_with_retry("https://example.com/rss", max_retries=1)

    assert result == _RSS_SAMPLE


def test_timeout_retries_and_raises() -> None:
    client = MagicMock(spec=httpx.Client)
    client.__enter__.return_value = client
    client.get.side_effect = httpx.TimeoutException("timeout")

    with patch("player_availability.collectors.http_client.httpx.Client", return_value=client):
        with pytest.raises(SourceUnavailableError):
            fetch_with_retry("https://example.com/rss", max_retries=2, base_delay=0.0)

    assert client.get.call_count == 2


def test_http_500_retries_and_raises() -> None:
    resp = _mock_response("", 500)
    client = MagicMock(spec=httpx.Client)
    client.__enter__.return_value = client
    client.get.return_value = resp

    with patch("player_availability.collectors.http_client.httpx.Client", return_value=client):
        with pytest.raises(SourceUnavailableError):
            fetch_with_retry("https://example.com/rss", max_retries=3, base_delay=0.0)

    assert client.get.call_count == 3


def test_http_404_does_not_retry() -> None:
    resp = _mock_response("", 404)
    client = MagicMock(spec=httpx.Client)
    client.__enter__.return_value = client
    client.get.return_value = resp

    with patch("player_availability.collectors.http_client.httpx.Client", return_value=client):
        with pytest.raises(SourceUnavailableError):
            fetch_with_retry("https://example.com/rss", max_retries=3, base_delay=0.0)

    assert client.get.call_count == 1


def test_http_429_retries() -> None:
    resp = _mock_response("", 429)
    client = MagicMock(spec=httpx.Client)
    client.__enter__.return_value = client
    client.get.return_value = resp

    with patch("player_availability.collectors.http_client.httpx.Client", return_value=client):
        with pytest.raises(SourceUnavailableError):
            fetch_with_retry("https://example.com/rss", max_retries=2, base_delay=0.0)

    assert client.get.call_count == 2


def test_success_after_retry() -> None:
    fail_resp = _mock_response("", 502)
    ok_resp = _mock_response(_RSS_SAMPLE)
    client = MagicMock(spec=httpx.Client)
    client.__enter__.return_value = client
    client.get.side_effect = [fail_resp, ok_resp]

    with patch("player_availability.collectors.http_client.httpx.Client", return_value=client):
        result = fetch_with_retry("https://example.com/rss", max_retries=2, base_delay=0.0)

    assert result == _RSS_SAMPLE
    assert client.get.call_count == 2


def test_request_error_retries() -> None:
    client = MagicMock(spec=httpx.Client)
    client.__enter__.return_value = client
    client.get.side_effect = httpx.RequestError("connection error")

    with patch("player_availability.collectors.http_client.httpx.Client", return_value=client):
        with pytest.raises(SourceUnavailableError):
            fetch_with_retry("https://example.com/rss", max_retries=2, base_delay=0.0)

    assert client.get.call_count == 2
