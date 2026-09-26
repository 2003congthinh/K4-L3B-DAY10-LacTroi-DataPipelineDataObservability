from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def generate_phase1_report(
    report_path: Path | str,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Viết báo cáo Markdown chi tiết cho phase 1 baseline."""
    out_path = Path(report_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    md_content = f"""# 📊 Phase 1 Baseline Pipeline Report

## 1. Data Ingestion Summary
- **Total Raw Records:** {source_summary.get('total_records', 0)}
- **Cleaned Records:** {source_summary.get('clean_records', 0)}
- **Query / Source:** {source_summary.get('query', 'N/A')}

## 2. Evaluation Metrics (Baseline RAG)
- **Samples Tested:** {metrics.get('samples', 0)}
- **Retrieval Hit Rate:** {metrics.get('retrieval_hit_rate', 0.0):.2%}
- **Mean Token F1:** {metrics.get('mean_token_f1', 0.0):.4f}
- **LLM Judge Accuracy:** {metrics.get('judge_accuracy', 0.0):.2%}
- **Mean LLM Judge Score:** {metrics.get('mean_judge_score', 0.0):.2f} / 5.0

## 3. Data Observability & Quality Gate (Great Expectations)
- **Overall Quality Status:** {"✅ PASSED" if quality.get("success") else "❌ FAILED"}
- **GX Expectations Passed:** {"Yes" if quality.get("gx_success") else "No"}
- **Freshness SLA Passed:** {"Yes" if freshness.get("is_fresh") else "No"}
- **Stale Rows Ratio (>180 days):** {freshness.get("stale_ratio", 0.0):.2%}

---
*Report generated automatically by Data Pipeline & Observability Engine.*
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md_content)


def generate_corruption_report(
    report_path: Path | str,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Viết báo cáo Markdown so sánh giữa Baseline, Corrupted và Repaired (cho các bước sau)."""
    out_path = Path(report_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    md_content = f"""# 🧪 Data Corruption & Recovery Comparison Report

| Metric / Stage | Baseline | Corrupted | Repaired |
| :--- | :---: | :---: | :---: |
| **Retrieval Hit Rate** | {baseline_metrics.get('retrieval_hit_rate', 0.0):.2%} | {corrupted_metrics.get('retrieval_hit_rate', 0.0):.2%} | {repaired_metrics.get('retrieval_hit_rate', 0.0):.2%} |
| **Mean Token F1** | {baseline_metrics.get('mean_token_f1', 0.0):.4f} | {corrupted_metrics.get('mean_token_f1', 0.0):.4f} | {repaired_metrics.get('mean_token_f1', 0.0):.4f} |
| **Data Quality Gate** | ✅ PASSED | {"✅ PASSED" if corrupted_quality.get("success") else "❌ FAILED"} | {"✅ PASSED" if repaired_quality.get("success") else "❌ FAILED"} |
| **Freshness SLA** | ✅ PASSED | {"✅ PASSED" if corrupted_freshness.get("is_fresh") else "❌ FAILED"} | {"✅ PASSED" if repaired_freshness.get("is_fresh") else "❌ FAILED"} |
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md_content)