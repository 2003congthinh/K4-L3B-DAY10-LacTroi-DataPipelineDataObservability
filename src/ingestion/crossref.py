from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import re
import time
from pathlib import Path
import requests

from core.config import Settings


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_text(text: str | None) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", "", text)
    return " ".join(cleaned.split()).strip()


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        paper_id = item.get("DOI", "").strip()
        if not paper_id:
            continue

        titles = item.get("title", [])
        title = _clean_text(titles[0]) if titles else "Untitled"

        raw_abstract = item.get("abstract", "")
        summary = _clean_text(raw_abstract)

        authors_raw = item.get("author", [])
        authors: list[str] = []
        for a in authors_raw:
            given = a.get("given", "").strip()
            family = a.get("family", "").strip()
            name = f"{given} {family}".strip()
            if name:
                authors.append(name)

        categories = [str(cat).strip() for cat in item.get("subject", []) if cat]
        primary_category = categories[0] if categories else "General"

        published = ""
        created_parts = item.get("created", {}).get("date-parts", [])
        if created_parts and created_parts[0]:
            published = "-".join(f"{x:02d}" for x in created_parts[0])

        updated = published
        deposited_parts = item.get("deposited", {}).get("date-parts", [])
        if deposited_parts and deposited_parts[0]:
            updated = "-".join(f"{x:02d}" for x in deposited_parts[0])

        abs_url = item.get("URL", f"https://doi.org/{paper_id}")
        pdf_url = ""
        for link in item.get("link", []):
            if link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", "")
                break

        comment = item.get("publisher", "")

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    raw_api_path = settings.paths.raw_api_response
    raw_records_path = settings.paths.raw_records_json

    raw_api_path.parent.mkdir(parents=True, exist_ok=True)
    raw_records_path.parent.mkdir(parents=True, exist_ok=True)

    payload = None

    url = "https://api.crossref.org/works"
    params = {
        "query": getattr(settings, "source_query", "data pipeline"),
        "filter": getattr(settings, "source_filter", "has-abstract:true"),
        "rows": getattr(settings, "max_results", 24),
    }
    headers = {"User-Agent": "LabAI-DataPipeline/1.0 (mailto:student@example.com)"}

    for attempt in range(3):
        try:
            res = requests.get(url, params=params, headers=headers, timeout=10)
            if res.status_code == 200:
                payload = res.json()
                break
            elif res.status_code in (429, 503):
                time.sleep(2 * (attempt + 1))
        except Exception:
            time.sleep(1)

    if not payload:
        if raw_api_path.exists():
            with open(raw_api_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        else:
            raise RuntimeError(f"Không thể kết nối API và không tìm thấy snapshot tại {raw_api_path}")

    with open(raw_api_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    records = parse_crossref_payload(payload)

    records_dict = [asdict(r) for r in records]
    with open(raw_records_path, "w", encoding="utf-8") as f:
        json.dump(records_dict, f, ensure_ascii=False, indent=2)

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [PaperRecord(**item) for item in data]