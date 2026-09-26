from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import requests

from core.config import Settings

logger = logging.getLogger(__name__)

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


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord."""
    records = []
    items = payload.get("message", {}).get("items", [])
    
    for item in items:
        try:
            doi = item.get("DOI", "")
            title_list = item.get("title", [])
            title = title_list[0] if title_list else "Unknown Title"
            summary = item.get("abstract", "")
            
            author_list = []
            for author in item.get("author", []):
                name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                if name:
                    author_list.append(name)
            
            categories = item.get("subject", [])
            primary_category = categories[0] if categories else ""
            
            pub_date = item.get("published-print", {}).get("date-parts", [[None]])[0]
            published = "-".join([str(p).zfill(2) for p in pub_date if p]) if pub_date[0] else "1970-01-01"
            
            url = item.get("URL", f"https://doi.org/{doi}")
            
            record = PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=author_list,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=published,
                abs_url=url,
                pdf_url=url,
                comment=f"Crossref record {doi}"
            )
            records.append(record)
        except Exception as e:
            logger.warning(f"Lỗi khi parse bản ghi DOI={item.get('DOI')}: {e}")
            continue
            
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Gọi source API, lưu raw response, parse thành records."""
    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "select": "DOI,title,abstract,author,subject,published-print,URL"
    }
    
    headers = {
        "User-Agent": "DataObservabilityLab/1.0 (mailto:student@domain.com)"
    }
    
    try:
        logger.info(f"Đang fetch dữ liệu từ Crossref API: {url}")
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        payload = response.json()
        
        # 1. Lưu raw API response
        settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
        with open(settings.paths.raw_api_response, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            
        # 2. Parse payload
        records = parse_crossref_payload(payload)
        
        # 3. Lưu list records ra JSON
        records_dict = [vars(r) for r in records]
        with open(settings.paths.raw_records_json, "w", encoding="utf-8") as f:
            json.dump(records_dict, f, indent=2, ensure_ascii=False)
            
        return records
        
    except Exception as e:
        logger.warning(f"API fetch thất bại ({e}). Chuyển sang đọc snapshot dự phòng.")
        # Fallback đọc từ raw snapshot nếu mất mạng hoặc API limit
        return load_raw_records(settings.paths.raw_records_json)


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Đọc JSON snapshot và map thành `PaperRecord`."""
    if not path.exists():
        logger.error(f"Không tìm thấy file snapshot tại {path}")
        return []
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    return [PaperRecord(**item) for item in data]
