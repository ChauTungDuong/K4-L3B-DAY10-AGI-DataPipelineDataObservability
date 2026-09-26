from __future__ import annotations

import logging
from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_phase1_pipeline(settings: Settings | None = None) -> dict:
    """Execute end-to-end Phase 1 baseline pipeline."""
    if settings is None:
        settings = load_settings()

    logger.info("=== BẮT ĐẦU PHASE 1: BASELINE DATA PIPELINE ===")

    # 1. Fetch or Load Raw Records
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        logger.info("Đang lấy dữ liệu thô từ Crossref API (hoặc snapshot)...")
        raw_records = fetch_source_records(settings)
    else:
        logger.info(f"Đọc dữ liệu thô đã lưu tại: {settings.paths.raw_records_json}")
        raw_records = load_raw_records(settings.paths.raw_records_json)
        if not raw_records:
            logger.info("Snapshot rỗng, đang gọi fetch_source_records...")
            raw_records = fetch_source_records(settings)

    logger.info(f"-> Thu thập thành công {len(raw_records)} bài báo thô.")

    # 2. Clean Data & Model for Embedding
    logger.info("Đang làm sạch dữ liệu và tính toán embedding context...")
    clean_df = build_clean_dataframe(raw_records, now_utc())
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))
    logger.info(f"-> Đã lưu dữ liệu sạch: {settings.paths.clean_csv} ({len(clean_df)} dòng)")

    # 3. Vector Store Indexing (ChromaDB)
    logger.info("Đang sinh vector embedding (all-MiniLM-L6-v2) và nạp vào ChromaDB...")
    index = LocalEmbeddingIndex.build(
        clean_df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    logger.info(f"-> Đã index thành công collection '{settings.baseline_collection_name}' trong ChromaDB.")

    # 4. Generate or Load Evaluation Benchmark Test Set
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        logger.info("Đang sinh bộ câu hỏi đánh giá chuẩn (10 câu Ground Truth)...")
        test_set = build_test_set(clean_df, settings.paths.eval_testset)
    else:
        logger.info(f"Đang đọc bộ câu hỏi đánh giá tại: {settings.paths.eval_testset}")
        test_set = read_json(settings.paths.eval_testset)
    logger.info(f"-> Bộ test set gồm {len(test_set)} câu hỏi sẵn sàng.")

    # 5. Evaluate Baseline RAG Agent
    logger.info("Đang đánh giá hiệu năng Baseline RAG (Hit Rate & Token F1)...")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    logger.info(
        f"-> Baseline Metrics: Retrieval Hit Rate = {bundle.summary['retrieval_hit_rate']:.4f}, "
        f"Mean Token F1 = {bundle.summary['mean_token_f1']:.4f}"
    )

    # 6. Observability Gate (GX 1.x & Freshness SLA)
    logger.info("Đang kiểm định chất lượng bằng Great Expectations 1.x...")
    quality_report = run_data_quality_checks(clean_df, settings, "baseline")
    freshness_report = build_freshness_report(clean_df, settings, settings.paths.freshness_report)
    logger.info(
        f"-> Data Quality Gate Passed: {quality_report['success']} | "
        f"Freshness SLA Passed: {freshness_report['is_fresh']}"
    )

    # 7. Generate Phase 1 Markdown Report
    source_summary = {
        "total_records": len(clean_df),
        "source_api": settings.source_api,
        "query": settings.source_query,
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality_report,
        freshness=freshness_report,
    )
    logger.info(f"-> Đã xuất báo cáo Phase 1 tại: {settings.paths.baseline_report}")
    logger.info("=== HOÀN THÀNH PHASE 1 THÀNH CÔNG ===")
    return bundle.summary


def main() -> None:
    run_phase1_pipeline()


if __name__ == "__main__":
    main()
