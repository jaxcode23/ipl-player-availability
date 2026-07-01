from time import sleep

import httpx
from loguru import logger

from .exceptions import SourceUnavailableError

_RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


def fetch_with_retry(
    url: str,
    *,
    max_retries: int = 3,
    timeout: float = 30.0,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
) -> str:
    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                return response.text

        except httpx.TimeoutException as exc:
            last_exception = exc
            logger.warning(
                "Timeout fetching {} (attempt {}/{})",
                url,
                attempt + 1,
                max_retries,
            )

        except httpx.HTTPStatusError as exc:
            last_exception = exc
            status = exc.response.status_code
            logger.warning(
                "HTTP {} fetching {} (attempt {}/{})",
                status,
                url,
                attempt + 1,
                max_retries,
            )
            if status not in _RETRYABLE_STATUSES:
                raise SourceUnavailableError(f"Non-retryable HTTP {status} fetching {url}") from exc

        except httpx.RequestError as exc:
            last_exception = exc
            logger.warning(
                "Request error fetching {} (attempt {}/{})",
                url,
                attempt + 1,
                max_retries,
            )

        if attempt < max_retries - 1:
            delay = min(base_delay * (2**attempt), max_delay)
            sleep(delay)

    raise SourceUnavailableError(f"Failed to fetch {url} after {max_retries} attempts") from last_exception
