from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd
from core.config import load_settings
import json

from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()

    if run_date.tzinfo is None:
        run_date = run_date.replace(tzinfo=timezone.utc)

    rows = []
    for r in records:
        paper_id = r.paper_id.strip() if r.paper_id else ""
        title = " ".join(r.title.split()) if r.title else ""
        summary = " ".join(r.summary.split()) if r.summary else ""
        authors = [a.strip() for a in r.authors if a.strip()]
        categories = [c.strip() for c in r.categories if c.strip()]
        
        authors_joined = ", ".join(authors)
        categories_joined = ", ".join(categories)

        published_str = r.published.strip() if r.published else ""
        pub_dt = pd.to_datetime(published_str, errors="coerce")
        
        if pd.isna(pub_dt):
            pub_dt = run_date
        elif pub_dt.tzinfo is None:
            pub_dt = pub_dt.tz_localize(timezone.utc)

        age_days = (run_date - pub_dt).days

        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {published_str}\n"
            f"Categories: {categories_joined}\n"
            f"Summary: {summary}"
        )

        rows.append({
            "paper_id": paper_id,
            "title": title,
            "summary": summary,
            "authors": authors,
            "categories": categories,
            "primary_category": getattr(r, "primary_category", categories[0] if categories else ""),
            "published": published_str,
            "updated": getattr(r, "updated", published_str),
            "abs_url": getattr(r, "abs_url", ""),
            "pdf_url": getattr(r, "pdf_url", ""),
            "comment": getattr(r, "comment", ""),
            "published_dt": pub_dt,
            "age_days": age_days,
            "authors_joined": authors_joined,
            "categories_joined": categories_joined,
            "summary_chars": len(summary),
            "text_for_embedding": text_for_embedding,
        })

    df = pd.DataFrame(rows)

    df = df.drop_duplicates(subset=["paper_id"]).reset_index(drop=True)

    df = df[df["paper_id"].str.len() > 0]
    df = df[df["title"].str.len() > 0]

    clean_csv_path = load_settings().paths.clean_csv
    clean_json_path = load_settings().paths.clean_json

    clean_csv_path.parent.mkdir(parents=True, exist_ok=True)
    clean_json_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_json(clean_json_path, orient="records", force_ascii=False, indent=2)
    df.to_csv(clean_csv_path)

    return df.reset_index(drop=True)