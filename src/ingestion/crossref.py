from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.config import Settings
from core.utils import ensure_parent, normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


class _PlainText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _clean_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    parser = _PlainText()
    parser.feed(value)
    return normalize_whitespace(unescape(" ".join(parser.parts)))


def _first_text(value: object) -> str:
    if isinstance(value, list):
        return next((text for item in value if (text := _clean_text(item))), "")
    return _clean_text(value)


def _crossref_date(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    parts = value.get("date-parts")
    if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
        try:
            year, *rest = parts[0]
            return date(int(year), int(rest[0]) if rest else 1,
                        int(rest[1]) if len(rest) > 1 else 1).isoformat()
        except (TypeError, ValueError, OverflowError):
            pass
    timestamp = value.get("date-time")
    if isinstance(timestamp, str):
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            pass
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Extract usable papers from a Crossref works response, preserving item order."""
    message = payload.get("message")
    items = message.get("items") if isinstance(message, dict) else None
    if not isinstance(items, list):
        raise ValueError("Crossref payload must contain message.items as a list")

    records: list[PaperRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        doi = _clean_text(item.get("DOI"))
        title = _first_text(item.get("title"))
        summary = _clean_text(item.get("abstract"))
        published = next((day for key in ("published", "published-online", "published-print", "issued", "created")
                          if (day := _crossref_date(item.get(key)))), "")
        if not (doi and title and summary and published):
            continue

        authors = []
        for author in item.get("author") or []:
            if isinstance(author, dict):
                name = normalize_whitespace(" ".join(
                    part for key in ("given", "family") if (part := _clean_text(author.get(key)))
                ))
                if name:
                    authors.append(name)
        categories = [_clean_text(subject) for subject in (item.get("subject") or [])]
        categories = [subject for subject in categories if subject]
        abs_url = _clean_text(item.get("URL")) or f"https://doi.org/{doi}"
        pdf_url = next((url for link in (item.get("link") or []) if isinstance(link, dict)
                        and "pdf" in str(link.get("content-type", "")).lower()
                        if (url := _clean_text(link.get("URL")))), abs_url)
        updated = next((day for key in ("deposited", "indexed", "created")
                        if (day := _crossref_date(item.get(key)))), published)
        records.append(PaperRecord(
            paper_id=doi, title=title, summary=summary, authors=authors,
            categories=categories, primary_category=categories[0] if categories else "",
            published=published, updated=updated, abs_url=abs_url, pdf_url=pdf_url,
            comment=f"Crossref record {doi}",
        ))
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch Crossref works and save lineage artifacts; use the raw snapshot offline."""
    raw_path = settings.paths.raw_api_response
    retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    try:
        response = session.get(
            "https://api.crossref.org/works",
            params={"query": settings.source_query, "filter": settings.source_filter,
                    "rows": settings.max_results},
            headers={"User-Agent": "Day10-DataObservability-Lab/1.0 (academic metadata exercise)"},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        records = parse_crossref_payload(payload)
        if not records:
            raise ValueError("Crossref returned no usable papers")
        ensure_parent(raw_path)
        raw_path.write_bytes(response.content)
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        if not raw_path.is_file():
            raise RuntimeError("Crossref fetch failed and no raw snapshot is available") from exc
        payload = read_json(raw_path)
        records = parse_crossref_payload(payload)
        if not records:
            raise RuntimeError("Crossref snapshot contains no usable papers") from exc
    finally:
        session.close()

    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Reload the extracted record artifact for later pipeline stages."""
    data = read_json(path)
    if not isinstance(data, list):
        raise ValueError("Raw records artifact must be a JSON list")
    return [PaperRecord(**item) for item in data]
