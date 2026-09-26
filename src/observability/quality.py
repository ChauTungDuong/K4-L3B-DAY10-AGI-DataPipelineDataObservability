from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import great_expectations as gx
import pandas as pd

from core.config import Settings

def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})
    
    res1 = batch.validate(gx.expectations.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000))
    res2 = batch.validate(gx.expectations.ExpectColumnValuesToNotBeNull(column="paper_id"))
    res3 = batch.validate(gx.expectations.ExpectColumnValuesToNotBeNull(column="title"))
    res4 = batch.validate(gx.expectations.ExpectColumnValuesToNotBeNull(column="text_for_embedding"))
    res5 = batch.validate(gx.expectations.ExpectColumnValuesToBeUnique(column="paper_id"))
    res6 = batch.validate(gx.expectations.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30))
    
    success = res1.success and res2.success and res3.success and res4.success and res5.success and res6.success
    
    report = {
        "success": success,
        "results": {
            "row_count": res1.success,
            "id_not_null": res2.success,
            "title_not_null": res3.success,
            "text_not_null": res4.success,
            "id_unique": res5.success,
            "summary_length": res6.success
        }
    }
    
    out_path = settings.paths.quality_dir / f"{report_name}_quality_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    return report

def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    if df.empty:
        return {}
        
    latest_published = str(df["published"].max())
    oldest_published = str(df["published"].min())
    
    stale_mask = df["age_days"] > settings.freshness_threshold_days
    stale_rows = int(stale_mask.sum())
    total_rows = len(df)
    
    is_fresh = (stale_rows / total_rows) <= 0.25 if total_rows > 0 else True
    
    payload = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": is_fresh
    }
    
    out_path = Path(report_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        
    return payload
