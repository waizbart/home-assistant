"""
Coleta notícias de:
- Hacker News API (top 10 stories — sem chave)
- G1 RSS feed (sem chave)

A filtragem e sumarização final é feita pela LLM no prompt.
"""

import logging
from typing import Optional

import feedparser
import requests

logger = logging.getLogger(__name__)

HN_TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
G1_RSS_URL = "https://g1.globo.com/rss/g1/"

HN_FETCH_COUNT = 10  # Fetch top N to give LLM enough to pick from
G1_FETCH_COUNT = 5


def collect() -> Optional[dict]:
    """
    Returns raw headlines for LLM filtering.

    {
        "hacker_news": [
            {"title": "...", "url": "...", "score": 320, "comments": 145},
            ...
        ],
        "g1": [
            {"title": "...", "url": "..."},
            ...
        ]
    }
    """
    hn = _fetch_hacker_news()
    g1 = _fetch_g1()

    if hn is None and g1 is None:
        return None

    return {
        "hacker_news": hn or [],
        "g1": g1 or [],
    }


def _fetch_hacker_news() -> Optional[list]:
    try:
        resp = requests.get(HN_TOP_STORIES_URL, timeout=10)
        resp.raise_for_status()
        top_ids = resp.json()[:HN_FETCH_COUNT]

        stories = []
        for story_id in top_ids:
            try:
                item_resp = requests.get(
                    HN_ITEM_URL.format(id=story_id),
                    timeout=8,
                )
                item_resp.raise_for_status()
                item = item_resp.json()
                if item and item.get("type") == "story" and item.get("title"):
                    stories.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                        "score": item.get("score", 0),
                        "comments": item.get("descendants", 0),
                    })
            except Exception as exc:
                logger.debug("HN item %s failed: %s", story_id, exc)
                continue

        return stories if stories else None
    except Exception as exc:
        logger.warning("Hacker News fetch failed: %s", exc)
        return None


def _fetch_g1() -> Optional[list]:
    try:
        feed = feedparser.parse(G1_RSS_URL)
        if not feed.entries:
            return None

        items = []
        for entry in feed.entries[:G1_FETCH_COUNT]:
            items.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
            })

        return items if items else None
    except Exception as exc:
        logger.warning("G1 RSS fetch failed: %s", exc)
        return None
