from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

import pandas as pd


def corrupt_clean_dataframe(clean_df: pd.DataFrame, log_path: Path | str) -> pd.DataFrame:
    """Tiêm 6 dạng lỗi thực nghiệm vào DataFrame sạch và ghi log các dòng bị biến đổi."""
    df = clean_df.copy()
    corruption_logs: list[dict[str, Any]] = []

    if len(df) == 0:
        return df

    # 1. Drop latest records: Bỏ rơi 20% các bài báo mới nhất (nếu có cột published)
    if "published" in df.columns:
        df["_parsed_date"] = pd.to_datetime(df["published"], errors="coerce")
        df = df.sort_values(by="_parsed_date", ascending=False).reset_index(drop=True)
        num_to_drop = max(1, int(len(df) * 0.20))
        
        dropped_ids = df.iloc[:num_to_drop]["paper_id"].tolist() if "paper_id" in df.columns else []
        df = df.iloc[num_to_drop:].reset_index(drop=True)
        df = df.drop(columns=["_parsed_date"])
        
        corruption_logs.append({
            "corruption_type": "drop_latest_records",
            "count": num_to_drop,
            "affected_paper_ids": dropped_ids,
            "description": f"Dropped top {num_to_drop} latest records (20%)."
        })

    total_rows = len(df)
    if total_rows == 0:
        return df

    # 2. Blank summary: Xóa trắng phần tóm tắt ở ~15% số dòng
    if "summary" in df.columns:
        blank_idx = list(range(0, total_rows, 7))  # Chọn khoảng 15% số dòng
        affected_ids = []
        for idx in blank_idx:
            df.loc[idx, "summary"] = ""
            if "paper_id" in df.columns:
                affected_ids.append(str(df.loc[idx, "paper_id"]))
        
        corruption_logs.append({
            "corruption_type": "blank_summary",
            "count": len(blank_idx),
            "affected_paper_ids": affected_ids,
            "description": "Cleared summary content for selected rows."
        })

    # 3. Inject noise: Chèn chuỗi ký tự rác vào tóm tắt ở ~15% số dòng
    if "summary" in df.columns:
        noise_idx = list(range(1, total_rows, 7))
        affected_ids = []
        noise_text = " [CORRUPTED_NOISE_###_RND_TEXT] "
        for idx in noise_idx:
            original = str(df.loc[idx, "summary"])
            df.loc[idx, "summary"] = original + noise_text
            if "paper_id" in df.columns:
                affected_ids.append(str(df.loc[idx, "paper_id"]))

        corruption_logs.append({
            "corruption_type": "inject_noise",
            "count": len(noise_idx),
            "affected_paper_ids": affected_ids,
            "description": "Injected random noise string into summary."
        })

    # 4. Truncate title: Cắt ngắn tiêu đề xuống dưới 8 ký tự ở ~15% số dòng
    if "title" in df.columns:
        trunc_idx = list(range(2, total_rows, 7))
        affected_ids = []
        for idx in trunc_idx:
            original_title = str(df.loc[idx, "title"])
            df.loc[idx, "title"] = original_title[:5] if len(original_title) >= 5 else "Short"
            if "paper_id" in df.columns:
                affected_ids.append(str(df.loc[idx, "paper_id"]))

        corruption_logs.append({
            "corruption_type": "truncate_title",
            "count": len(trunc_idx),
            "affected_paper_ids": affected_ids,
            "description": "Truncated paper title to under 8 characters."
        })

    # 5. Stale date: Lùi ngày xuất bản về 365 ngày trước ở ~20% số dòng
    if "published" in df.columns:
        stale_idx = list(range(3, total_rows, 5))
        affected_ids = []
        for idx in stale_idx:
            try:
                curr_date = pd.to_datetime(df.loc[idx, "published"])
                stale_date = curr_date - timedelta(days=365)
                df.loc[idx, "published"] = stale_date.strftime("%Y-%m-%d")
            except Exception:
                df.loc[idx, "published"] = "2020-01-01"
            
            if "paper_id" in df.columns:
                affected_ids.append(str(df.loc[idx, "paper_id"]))

        corruption_logs.append({
            "corruption_type": "stale_date",
            "count": len(stale_idx),
            "affected_paper_ids": affected_ids,
            "description": "Shifted publication date back by 365 days."
        })

    # 6. Duplicate rows: Nhân đôi một số dòng để tạo trùng lặp dữ liệu
    dup_count = max(1, int(total_rows * 0.10))
    dup_rows = df.iloc[:dup_count].copy()
    affected_ids = dup_rows["paper_id"].tolist() if "paper_id" in dup_rows.columns else []
    
    df = pd.concat([df, dup_rows], ignore_index=True)

    corruption_logs.append({
        "corruption_type": "duplicate_rows",
        "count": dup_count,
        "affected_paper_ids": affected_ids,
        "description": f"Duplicated {dup_count} existing rows."
    })

    # Cập nhật lại trường text_for_embedding nếu có để khớp với dữ liệu đã bị biến đổi
    if "text_for_embedding" in df.columns:
        df["text_for_embedding"] = (
            df["title"].fillna("") + ". " + df["summary"].fillna("")
        )

    # Ghi log nhật ký hư hại dữ liệu vào file JSON
    out_log_path = Path(log_path)
    out_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_log_path, "w", encoding="utf-8") as f:
        json.dump(corruption_logs, f, ensure_ascii=False, indent=2)

    return df