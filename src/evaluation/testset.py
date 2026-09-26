from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    test_set = []
    
    if len(df) < 4:
        return []
        
    sample_df = df.sample(min(10, len(df)), random_state=42)
    q_types = ["summary", "authors", "date", "categories"]
    
    for i, (_, row) in enumerate(sample_df.iterrows()):
        q_type = q_types[i % 4]
        paper_id = str(row["paper_id"])
        title = str(row["title"])
        
        if q_type == "summary":
            question = f"What is the summary of the paper '{title}'?"
            gt = str(row["summary"]).split(". ")[0] + "."
        elif q_type == "authors":
            question = f"Who are the authors of the paper '{title}'?"
            gt = str(row["authors_joined"])
        elif q_type == "date":
            question = f"When was the paper '{title}' published?"
            gt = str(row["published"])
        elif q_type == "categories":
            question = f"What categories does the paper '{title}' belong to?"
            gt = str(row["categories_joined"])
            
        test_set.append({
            "id": f"eval_{i:03d}",
            "question_type": q_type,
            "question": question,
            "ground_truth": gt,
            "ground_truth_doc_ids": [paper_id]
        })
        
        if len(test_set) >= 10:
            break
            
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(test_set, f, indent=2)
        
    return test_set
