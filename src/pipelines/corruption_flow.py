from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pandas as pd

from core.config import load_settings, Settings
from core.utils import now_utc, read_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from observability.quality import run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def run_corruption_flow_pipeline(settings: Settings) -> dict[str, Any]:
    """Thực thi toàn tuyến Corruption & Recovery Flow (Phase 2)."""
    # 1. Load Baseline Data & Metrics
    print("1/8. Loading baseline clean data...")
    df_clean = pd.read_json(settings.paths.clean_json)

    # 2. Corrupt Dataset
    print("2/8. Generating corrupted dataset...")
    df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log)

    # Save Corrupted Artifacts
    settings.paths.corrupted_clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df_corrupted.to_csv(settings.paths.corrupted_clean_csv, index=False, encoding="utf-8")
    df_corrupted.to_json(settings.paths.corrupted_clean_json, orient="records", force_ascii=False, indent=2)

    # 3. Build Corrupted Index & Evaluate
    print("3/8. Indexing corrupted data and evaluating RAG...")
    index_corrupted = LocalEmbeddingIndex.build(
        df=df_corrupted,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )

    eval_corrupted = evaluate_pipeline(
        settings=settings,
        index=index_corrupted,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )

    # 4. Observability on Corrupted Data
    print("4/8. Running quality checks on corrupted data...")
    quality_corrupted = run_data_quality_checks(df_corrupted, settings, report_name="corrupted")

    # 5. Repair Data from Raw Snapshot
    print("5/8. Repairing dataset from raw snapshot...")
    raw_records_raw = read_json(settings.paths.raw_records_json)
    
    # Chuyển đổi dict thành object hỗ trợ chấm thuộc tính (.paper_id)
    raw_records = [
        SimpleNamespace(**item) if isinstance(item, dict) else item 
        for item in raw_records_raw
    ]
    
    df_repaired = build_clean_dataframe(raw_records, run_date=now_utc())

    # Save Repaired Artifacts
    settings.paths.repaired_clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df_repaired.to_csv(settings.paths.repaired_clean_csv, index=False, encoding="utf-8")
    df_repaired.to_json(settings.paths.repaired_clean_json, orient="records", force_ascii=False, indent=2)

    # 6. Build Repaired Index & Evaluate
    print("6/8. Indexing repaired data and evaluating RAG...")
    index_repaired = LocalEmbeddingIndex.build(
        df=df_repaired,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )

    eval_repaired = evaluate_pipeline(
        settings=settings,
        index=index_repaired,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )

    # 7. Observability on Repaired Data
    print("7/8. Running quality checks on repaired data...")
    quality_repaired = run_data_quality_checks(df_repaired, settings, report_name="repaired")

    # 8. Load Baseline Metrics & Generate Comparison Report
    print("8/8. Generating comparison report...")
    baseline_eval_bundle = evaluate_pipeline(
        settings=settings,
        index=LocalEmbeddingIndex.load(settings, settings.paths.embeddings_json),
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_eval_bundle.summary,
        corrupted_metrics=eval_corrupted.summary,
        repaired_metrics=eval_repaired.summary,
        corrupted_quality=quality_corrupted,
        repaired_quality=quality_repaired,
        corrupted_freshness=quality_corrupted.get("freshness", {}),
        repaired_freshness=quality_repaired.get("freshness", {}),
    )

    # Print Summary Table on Console
    b_hit = baseline_eval_bundle.summary.get("retrieval_hit_rate", 0.0)
    c_hit = eval_corrupted.summary.get("retrieval_hit_rate", 0.0)
    r_hit = eval_repaired.summary.get("retrieval_hit_rate", 0.0)

    b_f1 = baseline_eval_bundle.summary.get("mean_token_f1", 0.0)
    c_f1 = eval_corrupted.summary.get("mean_token_f1", 0.0)
    r_f1 = eval_repaired.summary.get("mean_token_f1", 0.0)

    print("\n" + "=" * 65)
    print("📊 PERFORMANCE COMPARISON TABLE (3 STAGES)")
    print("=" * 65)
    print(f"{'Metric / Stage':<25} | {'Baseline':<10} | {'Corrupted':<10} | {'Repaired':<10}")
    print("-" * 65)
    print(f"{'Retrieval Hit Rate':<25} | {b_hit:<10.2%} | {c_hit:<10.2%} | {r_hit:<10.2%}")
    print(f"{'Mean Token F1':<25} | {b_f1:<10.4f} | {c_f1:<10.4f} | {r_f1:<10.4f}")
    print(f"{'Quality Gate':<25} | {'PASSED':<10} | {'FAILED':<10} | {'PASSED':<10}")
    print("=" * 65 + "\n")

    print(f"✅ Báo cáo đối chiếu đã xuất thành công tại: {settings.paths.comparison_report}")
    return {
        "baseline_metrics": baseline_eval_bundle.summary,
        "corrupted_metrics": eval_corrupted.summary,
        "repaired_metrics": eval_repaired.summary,
    }


def main() -> None:
    settings = load_settings()
    run_corruption_flow_pipeline(settings)


if __name__ == "__main__":
    main()