from __future__ import annotations

import html
import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from threading import Lock
from urllib.parse import quote_plus
from xml.etree import ElementTree

import requests

from config import NEWS


_CACHE_LOCK = Lock()
_CACHE = {"expires_at": None, "items": []}
_SESSION = requests.Session()
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


class NewsError(RuntimeError):
    pass


def _feed_url() -> str:
    if NEWS["feed_url"]:
        return NEWS["feed_url"]
    query = quote_plus(NEWS["query"])
    return f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"


def _clean_text(value: str) -> str:
    text = html.unescape(_TAG_RE.sub(" ", value or ""))
    return _WS_RE.sub(" ", text).strip()


def _parse_published(value: str) -> str:
    if not value:
        return ""
    try:
        return parsedate_to_datetime(value).isoformat()
    except (TypeError, ValueError, OverflowError):
        return ""


def _extract_items(xml_text: str) -> list[dict]:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        raise NewsError("Economics news feed could not be parsed.") from exc

    items = []
    limit = max(1, min(int(NEWS["max_items"]), 12))
    for node in root.findall("./channel/item")[:limit]:
        title = _clean_text(node.findtext("title", ""))
        link = (node.findtext("link", "") or "").strip()
        description = _clean_text(node.findtext("description", ""))
        source = _clean_text(node.findtext("source", ""))
        published_at = _parse_published(node.findtext("pubDate", ""))

        if not title or not link:
            continue

        items.append(
            {
                "title": title,
                "link": link,
                "summary": description,
                "source": source or "Live feed",
                "published_at": published_at,
            }
        )
    return items


def get_economy_news(force_refresh: bool = False) -> list[dict]:
    with _CACHE_LOCK:
        expires_at = _CACHE["expires_at"]
        if not force_refresh and expires_at and expires_at > datetime.utcnow() and _CACHE["items"]:
            return list(_CACHE["items"])

    try:
        response = _SESSION.get(
            _feed_url(),
            headers={"User-Agent": "STOCKMIND-AI/1.0"},
            timeout=12,
        )
    except requests.RequestException as exc:
        raise NewsError("Economics news feed is unreachable right now.") from exc

    if response.status_code >= 400:
        raise NewsError(f"Economics news feed returned HTTP {response.status_code}.")

    items = _extract_items(response.text)
    if not items:
        raise NewsError("No economics headlines were returned by the live feed.")

    with _CACHE_LOCK:
        _CACHE["items"] = items
        _CACHE["expires_at"] = datetime.utcnow() + timedelta(seconds=max(60, NEWS["cache_seconds"]))

    return list(items)
