"""
Fetch headlines from news sources.
"""

import re
from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup

from .models import NewsStory


def get_selectors_for_language(language: str) -> List[str]:
    """Return CSS selectors for headline extraction for the given language."""
    base = [
        "h1, h2, h3",
        '[data-testid*="headline"]',
        ".headline",
        ".title",
        "article h1, article h2",
    ]
    if language == "fr_FR":
        return base + [
            ".article__title",
            ".fig-headline",
            ".teaser__title",
            ".t-content__title",
            ".article-title",
            ".titre",
            ".headline-title",
        ]
    if language == "de_DE":
        return base + [
            ".article-title",
            ".zon-teaser__title",
            ".entry-title",
            ".js-headline",
            ".headline",
            ".titel",
            ".schlagzeile",
        ]
    if language == "es_ES":
        return base + [
            ".c_h_t",
            ".ue-c-cover-content__headline",
            ".titular",
            ".tit",
            ".headline",
            ".titulo",
            ".cabecera",
        ]
    if language == "it_IT":
        return base + [
            ".title-art",
            ".entry-title",
            ".gazzetta-title",
            ".article-title",
            ".headline",
            ".titolo",
            ".intestazione",
        ]
    if language == "nl_NL":
        return base + [
            ".sc-1x7olzq",
            ".ArticleTeaser__title",
            ".teaser__title",
            ".article__title",
            ".headline",
            ".titel",
            ".kop",
        ]
    if language in ("en_GB_LON", "en_GB_LIV"):
        return base + [
            ".fc-item__title",
            ".story-headline",
            ".headline-text",
            ".standard-headline",
            ".echo-headline",
            ".article-headline",
        ]
    return base + [".fc-item__title", ".story-headline", ".headline-text"]


def fetch_headlines_from_source(
    language: str,
    source_name: str,
    url: str,
    headers: dict,
) -> List[NewsStory]:
    """Extract headlines from a single source and return NewsStory list."""
    try:
        print(f"📡 Scanning {source_name}...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        stories = []
        selectors = get_selectors_for_language(language)
        seen = set()

        for selector in selectors:
            for element in soup.select(selector)[:15]:
                text = element.get_text(strip=True)
                if not text or len(text) < 16 or len(text) > 199 or text in seen:
                    continue
                if text.lower().startswith(("cookie", "accept", "subscribe", "sign up", "follow us")):
                    continue

                if language == "pl_PL":
                    english_sources = [
                        "BBC", "Guardian", "Reuters", "Sky News", "Independent",
                        "Telegraph", "Financial Times", "Bloomberg",
                    ]
                    if any(es.lower() in source_name.lower() for es in english_sources):
                        continue
                    english_indicators = [
                        r"\b(the|and|or|but|in|on|at|to|for|of|with|by|from|as|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|could|should|may|might|must|can|this|that|these|those|a|an)\b",
                        r"\b(breaking|news|update|latest|report|says|told|according|source)\b",
                    ]
                    eng_count = sum(1 for p in english_indicators if re.search(p, text, re.IGNORECASE))
                    polish_chars = len(re.findall(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]", text))
                    if eng_count >= 3 and polish_chars < 2:
                        continue

                link = None
                link_elem = element.find("a") or element.find_parent("a")
                if link_elem and link_elem.get("href"):
                    href = link_elem.get("href", "")
                    if href.startswith("/"):
                        link = url.rstrip("/") + href
                    elif href.startswith("http"):
                        link = href

                stories.append(
                    NewsStory(
                        title=text,
                        source=source_name,
                        link=link,
                        timestamp=datetime.now().isoformat(),
                    )
                )
                seen.add(text)
                if len(stories) >= 12:
                    break
            if stories:
                break

        print(f"   ✅ Found {len(stories)} stories from {source_name}")
        return stories
    except Exception as e:
        print(f"   ❌ Error fetching from {source_name}: {e}")
        return []
