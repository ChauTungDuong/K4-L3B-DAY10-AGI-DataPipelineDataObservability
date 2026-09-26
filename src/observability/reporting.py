from __future__ import annotations

from pathlib import Path
from typing import Any


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    content = f"""# Phase 1: Baseline Pipeline Report

## 1. Source Summary
- Total records: {source_summary.get('total_records', 0)}
- Freshness SLA Status: {'✅ Passed' if freshness.get('is_fresh') else '❌ Failed'}
- Stale Rows: {freshness.get('stale_rows', 0)} / {freshness.get('total_rows', 0)}

## 2. Data Quality (Great Expectations)
- All Checks Passed: {'✅ Yes' if quality.get('success') else '❌ No'}

## 3. Baseline Evaluation Metrics
- Hit Rate: {metrics.get('retrieval_hit_rate', 0.0):.4f}
- Token F1: {metrics.get('mean_token_f1', 0.0):.4f}
"""
    out_path = Path(report_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    content = f"""# Data Corruption & Idempotent Repair Report

## 1. Performance Comparison

| Metric | Baseline | Corrupted | Repaired |
| :--- | :--- | :--- | :--- |
| Hit Rate | {baseline_metrics.get('retrieval_hit_rate', 0.0):.4f} | {corrupted_metrics.get('retrieval_hit_rate', 0.0):.4f} | {repaired_metrics.get('retrieval_hit_rate', 0.0):.4f} |
| Token F1 | {baseline_metrics.get('mean_token_f1', 0.0):.4f} | {corrupted_metrics.get('mean_token_f1', 0.0):.4f} | {repaired_metrics.get('mean_token_f1', 0.0):.4f} |

## 2. Quality Gates Status
- Corrupted Data Quality Passed: {corrupted_quality.get('success', False)}
- Repaired Data Quality Passed: {repaired_quality.get('success', False)}

## 3. Freshness SLA
- Corrupted Data Fresh: {corrupted_freshness.get('is_fresh', False)}
- Repaired Data Fresh: {repaired_freshness.get('is_fresh', False)}
"""
    out_path = Path(report_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
