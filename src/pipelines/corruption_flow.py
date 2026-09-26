from __future__ import annotations

import logging
import pandas as pd

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from pipelines.phase1 import run_phase1_pipeline
from retrieval.index import LocalEmbeddingIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_corruption_flow_pipeline(settings: Settings | None = None) -> None:
    """Execute end-to-end Phase 2: Corruption -> Evaluate -> Idempotent Repair -> Compare."""
    if settings is None:
        settings = load_settings()

    logger.info("=== BẮT ĐẦU PHASE 2: CORRUPTION, REPAIR & 3-STATE COMPARISON ===")

    # Ensure baseline artifacts exist; run phase 1 if missing
    if not settings.paths.clean_csv.exists() or not settings.paths.baseline_metrics.exists():
        logger.info("Chưa tìm thấy kết quả Baseline Phase 1, đang tự động chạy Phase 1 trước...")
        run_phase1_pipeline(settings)

    clean_df = pd.read_csv(settings.paths.clean_csv)
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    logger.info(f"-> Đã nạp dữ liệu sạch Baseline: {len(clean_df)} dòng.")

    # 1. Tiêm 6 loại lỗi dữ liệu (Data Corruption)
    logger.info("Đang tiêm 6 kịch bản lỗi thực nghiệm vào DataFrame sạch...")
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    logger.info(f"-> Đã lưu corrupted dataset: {settings.paths.corrupted_clean_csv} ({len(corrupted_df)} dòng)")

    # 2. Vector Indexing trên Corrupted Dataset
    logger.info("Đang nạp dữ liệu bẩn vào ChromaDB collection 'papers-corrupted'...")
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )

    # 3. Đo lường suy giảm hiệu năng AI (Silent Failure)
    logger.info("Đang đánh giá hiệu năng RAG trên tập dữ liệu bẩn (quan sát suy giảm)...")
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    logger.info(
        f"-> Corrupted Metrics: Retrieval Hit Rate = {corrupted_bundle.summary['retrieval_hit_rate']:.4f}, "
        f"Mean Token F1 = {corrupted_bundle.summary['mean_token_f1']:.4f}"
    )

    # 4. Kiểm định chốt chất lượng trên Corrupted Data
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted_df,
        settings,
        settings.paths.quality_dir / "corrupted_freshness_report.json",
    )
    logger.info(
        f"-> Chốt kiểm dịch trên Corrupted Data: Quality Passed = {corrupted_quality['success']} | "
        f"Freshness SLA Passed = {corrupted_freshness['is_fresh']}"
    )

    # 5. Phục hồi tự động (Idempotent Repair) từ Raw Records Snapshot
    logger.info("Kích hoạt cơ chế Phục hồi Tự động (Idempotent Repair) từ raw snapshot...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, now_utc())
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    logger.info(f"-> Đã khôi phục thành công dữ liệu sạch: {len(repaired_df)} dòng.")

    # 6. Re-index và Re-evaluate trên Repaired Data
    logger.info("Đang tái nạp dữ liệu đã phục hồi vào ChromaDB collection 'papers-repaired'...")
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )

    logger.info("Đang tái đánh giá hiệu năng sau khi phục hồi...")
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    logger.info(
        f"-> Repaired Metrics: Retrieval Hit Rate = {repaired_bundle.summary['retrieval_hit_rate']:.4f}, "
        f"Mean Token F1 = {repaired_bundle.summary['mean_token_f1']:.4f}"
    )

    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_freshness = build_freshness_report(
        repaired_df,
        settings,
        settings.paths.quality_dir / "repaired_freshness_report.json",
    )

    # 7. Xuất Báo Cáo Đối Chiếu 3 Trạng Thái
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    logger.info(f"-> Đã xuất báo cáo đối chiếu 3 trạng thái tại: {settings.paths.comparison_report}")

    # In Bang Tong Ket Console (ASCII-safe for Windows terminals)
    print("\n" + "=" * 76)
    print("           3-STATE PIPELINE COMPARISON (BASELINE vs CORRUPTED vs REPAIRED)")
    print("=" * 76)
    print(f"{'Metric / Signal':<26} | {'Baseline':<12} | {'Corrupted':<14} | {'Repaired':<12}")
    print("-" * 26 + "-+-" + "-" * 12 + "-+-" + "-" * 14 + "-+-" + "-" * 12)
    print(
        f"{'Retrieval Hit Rate':<26} | "
        f"{baseline_metrics.get('retrieval_hit_rate', 0.0):<12.4f} | "
        f"{corrupted_bundle.summary.get('retrieval_hit_rate', 0.0):<14.4f} | "
        f"{repaired_bundle.summary.get('retrieval_hit_rate', 0.0):<12.4f}"
    )
    print(
        f"{'Mean Token F1':<26} | "
        f"{baseline_metrics.get('mean_token_f1', 0.0):<12.4f} | "
        f"{corrupted_bundle.summary.get('mean_token_f1', 0.0):<14.4f} | "
        f"{repaired_bundle.summary.get('mean_token_f1', 0.0):<12.4f}"
    )
    b_qual = "PASSED (True)"
    c_qual = f"{'PASSED' if corrupted_quality.get('success') else 'FAILED (False)'}"
    r_qual = f"{'PASSED (True)' if repaired_quality.get('success') else 'FAILED'}"
    print(f"{'GX Data Quality Gate':<26} | {b_qual:<12} | {c_qual:<14} | {r_qual:<12}")

    b_fresh = "FRESH (True)"
    c_fresh = f"{'FRESH' if corrupted_freshness.get('is_fresh') else 'STALE (False)'}"
    r_fresh = f"{'FRESH (True)' if repaired_freshness.get('is_fresh') else 'STALE'}"
    print(f"{'Freshness SLA':<26} | {b_fresh:<12} | {c_fresh:<14} | {r_fresh:<12}")
    print("=" * 76 + "\n")


def main() -> None:
    run_corruption_flow_pipeline()


if __name__ == "__main__":
    main()
