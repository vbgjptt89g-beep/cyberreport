"""Obtiene fuentes RSS y conserva una ventana acumulada de siete días."""

from __future__ import annotations

import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
from urllib.request import Request, urlopen

SOURCES = {
    "CISA - Alertas": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
    "CISA - Blog": "https://www.cisa.gov/news.xml",
    "NIST - CSRC News": "https://csrc.nist.gov/news/rss",
    "OWASP - Noticias": "https://owasp.org/feed.xml",
    "The Hacker News": "https://feeds.feedburner.com/TheHackersNews",
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
}
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "weekly_entries.json"


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
            return datetime(*value[:6], tzinfo=timezone.utc)
    return datetime.now(tz=timezone.utc)


def _clean_summary(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(value)).strip()[:1200]


def _fetch_one_source(source_name: str, url: str, cutoff: datetime) -> list[Entry]:
    try:
        print(f"Consultando {source_name}...", flush=True)
        request = Request(url, headers={"User-Agent": "cyberreport/1.0"})
        with urlopen(request, timeout=5) as response:
            payload = response.read(2_000_000)
        parsed = feedparser.parse(payload)
        recent = []
        for item in parsed.entries:
            published = _parse_date(item)
            if published < cutoff:
                continue
            link = item.get("link", "").strip()
            title = _clean_summary(item.get("title", "Sin título"))
            if not link or not title:
                continue
            recent.append(Entry(
                source=source_name,
                title=title,
                link=link,
                summary=_clean_summary(item.get("summary", item.get("description", ""))),
                published=published,
            ))
        print(f"    -> {len(recent)} publicaciones recientes de {source_name}", flush=True)
        if parsed.bozo and not parsed.entries:
            print(f"[WARN] No se pudo leer {source_name}: {parsed.bozo_exception}", flush=True)
        return recent
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] Se omitió {source_name}: {exc}", flush=True)
        return []


def fetch_weekly_entries(days: int = 7) -> list[Entry]:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    with ThreadPoolExecutor(max_workers=len(SOURCES)) as pool:
        tasks = [
            pool.submit(_fetch_one_source, source_name, url, cutoff)
            for source_name, url in SOURCES.items()
        ]
        results = {}
        for task in tasks:
            for entry in task.result():
                results[entry.link] = entry
    return sorted(results.values(), key=lambda entry: entry.published, reverse=True)

def collect_and_store_weekly_entries(days: int = 7) -> list[Entry]:
    """Ejecutar a diario: vuelve a leer la ventana semanal, combina y guarda por URL."""
    fresh = fetch_weekly_entries(days=days)
    existing = load_weekly_entries(days=days, missing_ok=True)
    combined = {entry.link: entry for entry in existing}
    combined.update({entry.link: entry for entry in fresh})
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    kept = sorted(
        (entry for entry in combined.values() if entry.published >= cutoff),
        key=lambda entry: entry.published,
        reverse=True,
    )
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps(
            [{**asdict(entry), "published": entry.published.isoformat()} for entry in kept],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"    -> {len(fresh)} publicaciones encontradas; {len(kept)} conservadas en la semana")
    return kept


def load_weekly_entries(days: int = 7, missing_ok: bool = False) -> list[Entry]:
    if not DATA_PATH.exists():
        if missing_ok:
            return []
        raise RuntimeError("Aún no hay publicaciones guardadas. Ejecuta primero: python main.py collect")
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    stored = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    entries = []
    for item in stored:
        published = datetime.fromisoformat(item["published"])
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        if published >= cutoff:
            entries.append(Entry(
                source=item["source"], title=item["title"], link=item["link"],
                summary=item["summary"], published=published,
            ))
    return sorted(entries, key=lambda entry: entry.published, reverse=True)


if __name__ == "__main__":
    for entry in collect_and_store_weekly_entries():
        print(f"[{entry.source}] {entry.title} ({entry.published:%Y-%m-%d})")
