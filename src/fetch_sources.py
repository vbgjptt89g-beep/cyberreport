"""Obtiene fuentes RSS y conserva una ventana acumulada de siete días."""

from __future__ import annotations

import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import feedparser
from urllib.request import Request, urlopen

SOURCES = {
    "Xataka": "https://feeds.weblogssl.com/xataka2",
    "Applesfera": "https://feeds.weblogssl.com/applesfera",
    "MuyComputer": "https://www.muycomputer.com/feed/",
    "Hipertextual": "https://hipertextual.com/feed/",
}
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "weekly_entries.json"
TECH_TERMS = (
    "tecnolog", "inteligencia artificial", " ia ", " ai ", "chatgpt", "gemini", "copilot", "openai",
    "software", "aplicación", "app ", "sistema operativo", "windows", "macos", "ios", "android",
    "apple", "iphone", "ipad", "macbook", "samsung", "google pixel", "nvidia", "microsoft",
    "chip", "semiconductor", "procesador", "gpu", "cpu", "ordenador", "computadora", "portátil",
    "smartphone", "móvil", "robot", "automatización", "ciencia", "espacio", "satélite", "nasa",
    "telescopio", "física", "investigación", "innovación", "energía nuclear", "energía solar",
    "batería", "vehículo eléctrico", "coche eléctrico", "coche autónomo", "videojuego", "consola",
    "playstation", "xbox", "nintendo", "streaming", "televisor", "televisión", "redes sociales",
    "tiktok", "instagram", "youtube", "whatsapp", "internet", "nube", "cloud", "5g", "6g",
    "telecomunic", "realidad virtual", "realidad aumentada", "blockchain", "impresión 3d", "dron",
)


EXCLUDED_TERMS = (
    "recesión sexual", "crisis de vivienda", "crisis de empleo", "celíaco", "celíaca", "alérgico",
    "alérgica", "multa", "robando tanto cobre", "chollos", "ofertas de hoy", "phishing", "malware",
    "antivirus", "ciberseguridad", "hackeo", "robo de cobre",
)


def _is_technology_entry(title: str, summary: str) -> bool:
    text = f" {title} {summary} ".casefold()
    return not any(term in text for term in EXCLUDED_TERMS) and any(term in text for term in TECH_TERMS)


@dataclass
class Entry:
    source: str
    title: str
    link: str
    summary: str
    published: datetime
    image: str = ""


def _parse_date(entry) -> datetime:
    for field in ("published_parsed", "updated_parsed"):
        value = entry.get(field)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return datetime.now(tz=timezone.utc)


def _clean_summary(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(value)).strip()[:1200]


def _entry_image(entry) -> str:
    """Obtiene una imagen de portada declarada en el feed RSS, si existe."""
    candidates = []
    for key in ("media_content", "media_thumbnail", "enclosures"):
        value = entry.get(key, []) or []
        if isinstance(value, dict):
            value = [value]
        candidates.extend(value)
    for item in candidates:
        if not isinstance(item, dict):
            continue
        url = item.get("url") or item.get("href")
        if not url and item.get("type", "").startswith("image/"):
            url = item.get("href")
        if url and urlparse(url).scheme in {"https", "http"} and urlparse(url).netloc:
            return url
    raw = entry.get("summary", entry.get("description", "")) or ""
    match = re.search(r"<img[^>]+src=[\"']([^\"']+)", raw, re.IGNORECASE)
    if match:
        url = html.unescape(match.group(1))
        if urlparse(url).scheme in {"https", "http"} and urlparse(url).netloc:
            return url
    return ""


def _fetch_one_source(source_name: str, url: str, cutoff: datetime) -> list[Entry]:
    try:
        print(f"Consultando {source_name}...", flush=True)
        request = Request(url, headers={"User-Agent": "technology-bulletin/1.0"})
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
            if not link or not title or not _is_technology_entry(title, item.get("summary", item.get("description", ""))):
                continue
            recent.append(Entry(
                source=source_name,
                title=title,
                link=link,
                summary=_clean_summary(item.get("summary", item.get("description", ""))),
                published=published,
                image=_entry_image(item),
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
        (entry for entry in combined.values() if entry.published >= cutoff and _is_technology_entry(entry.title, entry.summary)),
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
        if published >= cutoff and item.get("source") in SOURCES and _is_technology_entry(item.get("title", ""), item.get("summary", "")):
            entries.append(Entry(
                source=item["source"], title=item["title"], link=item["link"],
                summary=item.get("summary", ""), published=published,
                image=item.get("image", ""),
            ))
    return sorted(entries, key=lambda entry: entry.published, reverse=True)


if __name__ == "__main__":
    for entry in collect_and_store_weekly_entries():
        print(f"[{entry.source}] {entry.title} ({entry.published:%Y-%m-%d})")



