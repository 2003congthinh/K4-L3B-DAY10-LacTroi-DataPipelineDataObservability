from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import great_expectations as gx

# Import các Expectation từ Great Expectations 1.x
from great_expectations.expectations import (
    ExpectColumnValueLengthsToBeBetween,
    ExpectColumnValuesToNotBeNull,
    ExpectColumnValuesToBeUnique,
    ExpectTableRowCountToBeBetween,
)
import pandas as pd

from core.config import Settings


def build_freshness_report(
    df: pd.DataFrame, settings: Settings, report_path: Path | str | None = None
) -> dict[str, Any]:
    """Tổng hợp freshness report và đo lường độ tươi mới của dữ liệu."""
    if df.empty:
        report = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": 0,
            "stale_ratio": 0.0,
            "is_fresh": False,
        }
    else:
        total_rows = len(df)
        
        # Lấy ngày xuất bản mới nhất và cũ nhất
        pub_dates = pd.to_datetime(df["published"], errors="coerce")
        latest_pub = str(pub_dates.max()) if not pub_dates.dropna().empty else None
        oldest_pub = str(pub_dates.min()) if not pub_dates.dropna().empty else None

        # Đếm số dòng stale (age_days > 180)
        stale_rows = int((df["age_days"] > 180).sum()) if "age_days" in df.columns else 0
        stale_ratio = stale_rows / total_rows if total_rows > 0 else 0.0

        # Nếu tỉ lệ bài báo cũ (> 180 ngày) vượt quá 25% -> is_fresh = False
        is_fresh = stale_ratio <= 0.25

        report = {
            "latest_published": latest_pub,
            "oldest_published": oldest_pub,
            "stale_rows": stale_rows,
            "total_rows": total_rows,
            "stale_ratio": stale_ratio,
            "is_fresh": is_fresh,
        }

    # Ghi report ra file JSON nếu được chỉ định
    if report_path:
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    return report


def run_data_quality_checks(
    df: pd.DataFrame, settings: Settings, report_name: str
) -> dict[str, Any]:
    """Tạo bộ Data Quality Checks với Great Expectations 1.x (Ephemeral Context)."""
    # 1. Khởi tạo Ephemeral Context trên GX 1.x
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    # 2. Định nghĩa 4 Expectations bắt buộc
    expectations = [
        # Expectation 1: Số lượng bản ghi nằm trong ngưỡng 5 đến 5000
        ExpectTableRowCountToBeBetween(min_value=5, max_value=5000),
        # Expectation 2: Các cột quan trọng không được null
        ExpectColumnValuesToNotBeNull(column="paper_id"),
        ExpectColumnValuesToNotBeNull(column="title"),
        ExpectColumnValuesToNotBeNull(column="text_for_embedding"),
        # Expectation 3: Mỗi paper_id là duy nhất
        ExpectColumnValuesToBeUnique(column="paper_id"),
        # Expectation 4: Trường summary có độ dài tối thiểu 30 ký tự
        ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30),
    ]

    # 3. Validate batch dữ liệu
    results = []
    success = True
    for exp in expectations:
        res = batch.validate(exp)
        results.append(res.to_json_dict())
        if not res.success:
            success = False

    # 4. Giám sát độ tươi mới của dữ liệu
    freshness_res = build_freshness_report(df, settings)

    # 5. Tổng hợp kết quả
    output = {
        "report_name": report_name,
        "success": success and freshness_res["is_fresh"],
        "gx_success": success,
        "is_fresh": freshness_res["is_fresh"],
        "freshness": freshness_res,
        "results": results,
    }

    # 6. Ghi kết quả vào thư mục data/quality/
    out_dir = Path("data/quality")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{report_name}_quality_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    return output