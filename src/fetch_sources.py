"""
Obtiene entradas recientes (última semana) de fuentes fijas y confiables
de ciberseguridad mediante sus feeds RSS/Atom oficiales.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import feedparser

# Fuentes oficiales de ciberseguridad (RSS/Atom públicos)
SOURCES = {
    "CISA - Alertas": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
    "CISA - Blog": "https://www.cisa.gov/news.xml",
    "NIST - CSRC News": "https://csrc.nist.gov/news/rss",
    "OWASP - Noticias": "https://owasp.org/feed.xml",
    "The Hacker News": "https://feeds.feedburner.com/TheHackersNews",
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
}


@dataclass
class Entry:
    source: str
    title: str
    link: str
    summary: str
    published: datetime


def _parse_date(entry) -> datetime:
    for field in ("published_parsed", "updated_parsed"):
        value = entry.get(field)
        if value:
            return datetime.fromtimestamp(time.mktime(value), tz=timezone.utc)
    return datetime.now(tz=timezone.utc)


def fetch_weekly_entries(days: int = 7) -> list[Entry]:
    """Descarga y filtra entradas publicadas en los últimos `days` días."""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    results: list[Entry] = []

    for source_name, url in SOURCES.items():
        try:
            parsed = feedparser.parse(url)
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] No se pudo leer {source_name}: {exc}")
            continue

        for entry in parsed.entries:
            published = _parse_date(entry)
            if published < cutoff:
                continue
            results.append(
                Entry(
                    source=source_name,
                    title=entry.get("title", "Sin título"),
                    link=entry.get("link", ""),
                    summary=entry.get("summary", "")[:800],
                    published=published,
                )
            )

    results.sort(key=lambda e: e.published, reverse=True)
    return results


if __name__ == "__main__":
    for e in fetch_weekly_entries():
        print(f"[{e.source}] {e.title} ({e.published:%Y-%m-%d})")
