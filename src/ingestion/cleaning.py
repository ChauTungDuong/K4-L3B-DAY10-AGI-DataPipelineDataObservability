from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from html import unescape
import re

import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Normalize raw papers into a deduplicated, embedding-ready DataFrame."""
    columns = list(PaperRecord.__dataclass_fields__) + [
        "authors_joined", "categories_joined", "summary_chars", "age_days",
        "text_for_embedding",
    ]
    rows: list[dict] = []
    seen_ids: set[str] = set()

    def clean_text(value: str) -> str:
        # The raw artifact may contain JATS tags even when loaded without step 2.
        return normalize_whitespace(unescape(re.sub(r"<[^>]+>", " ", value or "")))

    for record in records:
        paper_id = normalize_whitespace(record.paper_id)
        title = clean_text(record.title)
        summary = clean_text(record.summary)
        try:
            published = date.fromisoformat(record.published[:10]).isoformat()
        except (TypeError, ValueError):
            continue
        if not (paper_id and title and summary) or paper_id.casefold() in seen_ids:
            continue
        seen_ids.add(paper_id.casefold())

        try:
            updated = date.fromisoformat(record.updated[:10]).isoformat()
        except (TypeError, ValueError):
            updated = published
        authors = [name for item in record.authors if (name := clean_text(item))]
        categories = [name for item in record.categories if (name := clean_text(item))]
        authors_joined = ", ".join(authors)
        categories_joined = ", ".join(categories)
        row = asdict(record)
        row.update(
            paper_id=paper_id,
            title=title,
            summary=summary,
            authors=authors,
            categories=categories,
            primary_category=clean_text(record.primary_category) or (categories[0] if categories else ""),
            published=published,
            updated=updated,
            abs_url=normalize_whitespace(record.abs_url),
            pdf_url=normalize_whitespace(record.pdf_url),
            comment=clean_text(record.comment),
            authors_joined=authors_joined,
            categories_joined=categories_joined,
            summary_chars=len(summary),
            age_days=(run_date.date() - date.fromisoformat(published)).days,
            text_for_embedding=(
                f"Title: {title}\n"
                f"Authors: {authors_joined}\n"
                f"Published: {published}\n"
                f"Categories: {categories_joined}\n"
                f"Summary: {summary}"
            ),
        )
        rows.append(row)

    return pd.DataFrame(rows, columns=columns).sort_values(
        ["published", "paper_id"], ascending=[False, True], kind="stable"
    ).reset_index(drop=True)
