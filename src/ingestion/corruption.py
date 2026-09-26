from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate 6 realistic data corruption scenarios and log transformations."""
    corrupted_df = df.copy()
    logs: list[dict[str, Any]] = []

    if corrupted_df.empty:
        out_path = Path(output_log_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        return corrupted_df

    # 1. Drop latest records (drop ~20% newest records)
    drop_count = max(1, int(len(corrupted_df) * 0.20))
    dropped_records = corrupted_df.head(drop_count)
    dropped_ids = dropped_records["paper_id"].tolist()
    corrupted_df = corrupted_df.iloc[drop_count:].copy().reset_index(drop=True)
    logs.append({
        "scenario": "drop_latest_records",
        "description": "Dropped 20% of the most recent publications",
        "count": drop_count,
        "affected_paper_ids": dropped_ids,
    })

    # 2. Blank summary on 2 records (violates summary length >= 30)
    blank_indices = [0, min(1, len(corrupted_df) - 1)]
    blank_ids = []
    for idx in set(blank_indices):
        if idx < len(corrupted_df):
            pid = corrupted_df.at[idx, "paper_id"]
            corrupted_df.at[idx, "summary"] = ""
            corrupted_df.at[idx, "summary_chars"] = 0
            blank_ids.append(pid)
    logs.append({
        "scenario": "blank_summary",
        "description": "Cleared summary field entirely on selected papers",
        "count": len(blank_ids),
        "affected_paper_ids": blank_ids,
    })

    # 3. Inject noise into summary on 2 records
    noise_indices = [min(2, len(corrupted_df) - 1), min(3, len(corrupted_df) - 1)]
    noise_ids = []
    for idx in set(noise_indices):
        if idx < len(corrupted_df):
            pid = corrupted_df.at[idx, "paper_id"]
            orig_summary = str(corrupted_df.at[idx, "summary"])
            corrupted_df.at[idx, "summary"] = (
                "[CORRUPTED_NOISE_GARBAGE_XYZ_#$@!%] " + orig_summary
            )
            noise_ids.append(pid)
    logs.append({
        "scenario": "inject_noise",
        "description": "Injected synthetic noise and corrupt tokens into summary",
        "count": len(noise_ids),
        "affected_paper_ids": noise_ids,
    })

    # 4. Truncate title (< 8 characters) on 2 records
    trunc_indices = [min(4, len(corrupted_df) - 1), min(5, len(corrupted_df) - 1)]
    trunc_ids = []
    for idx in set(trunc_indices):
        if idx < len(corrupted_df):
            pid = corrupted_df.at[idx, "paper_id"]
            corrupted_df.at[idx, "title"] = "Bad."
            trunc_ids.append(pid)
    logs.append({
        "scenario": "truncate_title",
        "description": "Truncated paper title down to under 8 characters",
        "count": len(trunc_ids),
        "affected_paper_ids": trunc_ids,
    })

    # 5. Make publication dates stale (> 180 days, shifts > 25% rows to stale)
    stale_count = max(4, int(len(corrupted_df) * 0.40))
    stale_indices = list(range(min(stale_count, len(corrupted_df))))
    stale_ids = []
    for idx in stale_indices:
        pid = corrupted_df.at[idx, "paper_id"]
        orig_published = str(corrupted_df.at[idx, "published"])
        try:
            parsed_date = date.fromisoformat(orig_published[:10])
            stale_date = (parsed_date - timedelta(days=365)).isoformat()
            corrupted_df.at[idx, "published"] = stale_date
            corrupted_df.at[idx, "age_days"] = int(corrupted_df.at[idx, "age_days"]) + 365
            stale_ids.append(pid)
        except Exception:
            pass
    logs.append({
        "scenario": "stale_date",
        "description": "Shifted publication date back by 365 days to violate freshness SLA",
        "count": len(stale_ids),
        "affected_paper_ids": stale_ids,
    })

    # 6. Duplicate rows (violates uniqueness of paper_id)
    dup_rows = corrupted_df.tail(2).copy()
    dup_ids = dup_rows["paper_id"].tolist()
    corrupted_df = pd.concat([corrupted_df, dup_rows], ignore_index=True)
    logs.append({
        "scenario": "duplicate_rows",
        "description": "Duplicated rows to trigger uniqueness expectation violation",
        "count": len(dup_ids),
        "affected_paper_ids": dup_ids,
    })

    # Rebuild helper columns and text_for_embedding on corrupted dataframe
    corrupted_df["summary_chars"] = corrupted_df["summary"].astype(str).str.len()
    corrupted_df["text_for_embedding"] = corrupted_df.apply(
        lambda r: (
            f"Title: {r['title']}\n"
            f"Authors: {r['authors_joined']}\n"
            f"Published: {r['published']}\n"
            f"Categories: {r['categories_joined']}\n"
            f"Summary: {r['summary']}"
        ),
        axis=1,
    )

    out_path = Path(output_log_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

    return corrupted_df
