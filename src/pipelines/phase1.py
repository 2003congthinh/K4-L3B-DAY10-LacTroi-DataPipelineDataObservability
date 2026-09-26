from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.config import load_settings, Settings
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def run_phase1_pipeline(settings: Settings) -> dict[str, Any]:
    """Thực thi toàn tuyến Baseline Pipeline Phase 1."""
    # 1. Ingest: Thu thập / nạp dữ liệu thô
    print("1/6. Fetching raw records...")
    records = fetch_source_records(settings)

    # 2. Clean: Làm sạch và chuẩn hóa dữ liệu
    print("2/6. Cleaning data...")
    now_utc = datetime.now(timezone.utc)
    df_clean = build_clean_dataframe(records, run_date=now_utc)

    # Lưu kết quả Clean ra CSV và JSON
    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(settings.paths.clean_csv, index=False, encoding="utf-8")
    df_clean.to_json(settings.paths.clean_json, orient="records", force_ascii=False, indent=2)

    # 3. Index ChromaDB: Xây dựng Vector Store
    print("3/6. Building ChromaDB Index...")
    index = LocalEmbeddingIndex.build(df=df_clean, settings=settings)

    # 4. Sinh Testset: Tạo bộ đề đánh giá Ground Truth
    print("4/6. Generating Evaluation Testset...")
    test_set = build_test_set(df_clean, settings.paths.eval_testset)

    # 5. Evaluate: Đánh giá Baseline RAG
    print("5/6. Evaluating Baseline Pipeline...")
    eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    # 6. Quality Check & Report: Kiểm tra Great Expectations và xuất báo cáo
    print("6/6. Running Quality Checks and generating report...")
    quality_res = run_data_quality_checks(df_clean, settings, report_name="phase1")

    source_summary = {
        "total_records": len(records),
        "clean_records": len(df_clean),
        "query": getattr(settings, "source_query", "data pipeline"),
    }

    # Xuất báo cáo markdown bằng thuộc tính đúng baseline_report
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=eval_bundle.summary,
        quality=quality_res,
        freshness=quality_res.get("freshness", {}),
    )

    print("✅ Baseline Phase 1 Pipeline hoàn thành xuất sắc!")
    return {
        "metrics": eval_bundle.summary,
        "quality": quality_res,
        "clean_count": len(df_clean),
    }


def main() -> None:
    """Hàm main thực thi toàn tuyến baseline pipeline."""
    settings = load_settings()
    run_phase1_pipeline(settings)


if __name__ == "__main__":
    main()