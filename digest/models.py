"""Data models for the digest pipeline."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class NewsStory:
    title: str
    source: str
    link: Optional[str]
    timestamp: str
    theme: Optional[str] = None
    significance_score: Optional[float] = None
