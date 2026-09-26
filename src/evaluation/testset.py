from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def build_test_set(df: pd.DataFrame, output_path: Path | str) -> list[dict[str, Any]]:
    """Tạo bộ dữ liệu đánh giá Ground Truth (10 câu hỏi) từ cleaned DataFrame."""
    if len(df) == 0:
        raise ValueError("DataFrame dữ liệu rỗng, không thể tạo test set.")

    # Định nghĩa danh sách phân bổ 10 câu hỏi theo 4 dạng
    # 3 summary, 3 authors, 2 date, 2 categories = 10 câu
    question_types = [
        "summary", "authors", "date", "categories",
        "summary", "authors", "date", "categories",
        "summary", "authors"
    ]

    test_set: list[dict[str, Any]] = []

    for idx, q_type in enumerate(question_types):
        # Lấy dòng bài báo tương ứng (quay vòng nếu df nhỏ hơn 10 dòng)
        row = df.iloc[idx % len(df)]
        
        paper_id = str(row["paper_id"])
        title = str(row["title"])
        
        # Xử lý lấy thông tin tác giả
        authors = row.get("authors", [])
        if isinstance(authors, list):
            authors_str = ", ".join(authors) if authors else "Unknown"
        else:
            authors_str = str(authors)

        # Xử lý lấy lĩnh vực
        categories = row.get("categories", [])
        if isinstance(categories, list):
            categories_str = ", ".join(categories) if categories else "General"
        else:
            categories_str = str(categories)

        published = str(row.get("published", ""))
        summary = str(row.get("summary", ""))

        # Xây dựng câu hỏi & ground_truth theo dạng
        if q_type == "summary":
            question = f"What is the summary of the paper '{title}'?"
            # Lấy câu đầu tiên hoặc 200 ký tự đầu của summary làm ground_truth chuẩn
            ground_truth = summary.split(". ")[0] if ". " in summary else summary[:200]
        
        elif q_type == "authors":
            question = f"Who wrote the paper '{title}'?"
            ground_truth = f"The authors are {authors_str}."
        
        elif q_type == "date":
            question = f"When was the paper '{title}' published?"
            ground_truth = f"It was published on {published}."
        
        else:  # categories
            question = f"What categories or subjects does the paper '{title}' belong to?"
            ground_truth = f"It belongs to {categories_str}."

        test_item = {
            "id": f"eval_{idx+1:03d}",
            "question_type": q_type,
            "question": question,
            "ground_truth": ground_truth,
            "ground_truth_doc_ids": [paper_id],
        }
        test_set.append(test_item)

    # Ghi bộ test set vào file JSON output_path
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(test_set, f, ensure_ascii=False, indent=2)

    return test_set