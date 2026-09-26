# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Công Thịnh |
| MSSV | 2A202602781 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | Lạc Trôi |
| Vai trò chính | Data & Observability Engineer |
| Repository | https://github.com/2003congthinh/K4-L3B-DAY10-LacTroi-DataPipelineDataObservability.git |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Ingestion & Cleaning | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py` | API Crossref / `raw_records.json` | `papers_clean.csv`, `papers_clean.json` | Hoàn thành |
| Data Observability | `src/observability/quality.py` | DataFrame dữ liệu (`df_clean`) | Quality Report & Freshness SLA | Hoàn thành |
| Data Corruption Suite | `src/ingestion/corruption.py` | `df_clean` | `df_corrupted`, `corruption_log.json` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Hỗ trợ định dạng Input | Trần Quốc Toản (`src/pipelines/corruption_flow.py`) | Định dạng dữ liệu dạng Object/SimpleNamespace tương thích với hàm cleaning |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Thu thập & Làm sạch dữ liệu | `src/ingestion/cleaning.py` (`build_clean_dataframe`) | 24 records sạch, sinh cột `text_for_embedding` | `python script/run_phase1.py` |
| Kiểm định GX 1.x & Freshness | `src/observability/quality.py` (`run_data_quality_checks`) | Báo cáo Quality Gate (PASSED/FAILED) | Kiểm tra log console khi chạy Phase 1 & 2 |
| Giả lập 6 dạng lỗi dữ liệu | `src/ingestion/corruption.py` (`corrupt_clean_dataframe`) | Dataset bị bẩn + `corruption_log.json` | Re-run `corruption_flow.py` |

**Artifact cụ thể:** Tải thành công dữ liệu thô, loại bỏ tag XML JATS, tính cột `age_days` và `text_for_embedding` đúng cấu trúc 5 phần, xuất thành công `data/clean/papers_clean.json`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Đảm bảo dữ liệu đầu vào RAG được chuẩn hóa, loại bỏ nhiễu và thiết lập cơ chế giám sát chất lượng (Data Observability) để phát hiện sớm các lỗi dữ liệu (tiêu đề bị mất, bài báo quá hạn SLA 180 ngày) trước khi nạp vào Vector DB.

### Cách triển khai

- Dùng Great Expectations 1.x để thiết lập các Validation Rules (non-null, unique paper_id).
- Xây dựng thuật toán `corrupt_clean_dataframe` thực hiện tiêm 6 loại lỗi thực nghiệm: xóa tóm tắt, chèn ký tự rác, lùi ngày xuất bản,... để thử nghiệm độ bền của hệ thống.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Raw JSON từ Crossref API hoặc local fallback snapshot |
| Output | Processed DataFrame / Quality Check Report (Dict) |
| Module phụ thuộc | `core.config`, `core.utils` |
| Module sử dụng output | `retrieval.index` (ChromaDB) |
| Điều kiện lỗi cần xử lý | Mất kết nối API Crossref -> tự động đọc từ fallback snapshot |

### Cách xác minh

```bash
python script/run_phase1.py
```

- **Kết quả mong đợi:** Tải/đọc dữ liệu thành công, vượt qua Quality Check (PASSED).
- **Kết quả thực tế:** Phase 1 chạy 100% không lỗi, xuất file `papers_clean.json`.
- **Artifact/log:** `data/clean/papers_clean.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Chọn phương án lưu trữ dữ liệu thô (Data Lineage).
- **Các phương án đã cân nhắc:**
  1. Chỉ lưu dữ liệu sau khi đã qua xử lý làm sạch.
  2. Lưu cả hai: Raw Snapshot (`raw_records.json`) và Cleaned Data (`papers_clean.json`).
- **Phương án đã chọn:** Phương án 2 (Lưu Raw Snapshot nguyên bản).
- **Lý do:** Giúp đảm bảo khả năng **Idempotent Repair** (phục hồi dữ liệu sạch 100% từ Snapshot thô khi hệ thống bị nhiễm dữ liệu bẩn mà không phụ thuộc lại vào API bên ngoài).
- **Bằng chứng:** Trong Bước 8 Phase 2, hệ thống đã khôi phục thành công performance từ `raw_records.json`.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `TypeError: build_clean_dataframe() missing 1 required positional argument: 'run_date'` và `AttributeError: 'dict' object has no attribute 'paper_id'`.
- **Lệnh hoặc bước tái hiện:** `python script/run_corruption_flow.py` tại Bước 5.
- **Nguyên nhân gốc:** Hàm `build_clean_dataframe` nhận vào danh sách Object hỗ trợ thuộc tính `.paper_id` và yêu cầu tham số `run_date`.
- **Cách xử lý:** Bổ sung tham số `run_date=now_utc()` và ép kiểu danh sách dict thành `SimpleNamespace` bằng danh sách nén (List Comprehension).
- **Cách xác minh sau khi sửa:** Chạy lại `python script/run_corruption_flow.py` - bước 5 chạy thành công.
- **Điều học được:** Cần thống nhất Type Contract / Schema Interface giữa các module đọc dữ liệu.

## 7. Hiểu biết về luồng end-to-end

1. **Từ Crossref đến vector index:** Dữ liệu thô từ Crossref API được parse -> lưu raw snapshot -> làm sạch & làm phong phú (`text_for_embedding`) -> tạo embedding bằng `all-MiniLM-L6-v2` -> lưu vào ChromaDB collection.
2. **Evaluation set & Ground-truth:** Dùng 10 câu hỏi benchmark với `expected_paper_ids` để so sánh trực tiếp ID bài báo do ChromaDB truy xuất nhằm tính Hit Rate & Token F1.
3. **Quality checks vs Freshness monitoring:** Quality checks kiểm tra ràng buộc cấu trúc (null, unique, format); Freshness monitoring kiểm tra SLA về thời gian (tuổi bài báo `age_days <= 180`).
4. **Vì sao dùng chung test set:** Để đảm bảo tính nhất quán (controlled environment) khi đo lường tác động của lỗi dữ liệu giữa 3 trạng thái.
5. **Repair thành công khi nào:** Khi Retrieval Hit Rate khôi phục về 100%, Quality Gate chuyển từ `FAILED` sang `PASSED` và file `corruption_report.md` xuất thành công.

## 8. Phân tích kết quả

### Metrics chính

| **Metric/signal** | **Baseline** | **Corrupted** | **Repaired** | **Nhận xét của cá nhân** |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | 100.00% | 70.00% | 100.00% | Dữ liệu bẩn khiến Hit Rate giảm 30% |
| `mean_token_f1` | 0.3088 | 0.3006 | 0.3088 | F1-Score suy giảm do thông tin bị nhiễu |
| Quality checks | PASSED | FAILED | PASSED | Phát hiện chính xác dữ liệu vi phạm |
| Freshness status | OK | WARNING | OK | Cảnh báo đúng bài báo bị lùi ngày |

### Kết luận từ số liệu

1. **[Data corruption]** → **[Quality Gate báo FAILED & Freshness WARNING]** → **[Retrieval Hit Rate giảm từ 100% xuống 70%]**.
2. **[Repair action từ Raw Snapshot]** → **[Quality Gate trở lại PASSED]** → **[Retrieval Hit Rate phục hồi hoàn toàn về 100%]**.

*Dạng corruption ảnh hưởng rõ nhất là Xóa Tóm tắt (Abstract Removal) và Cắt ngắn Tiêu đề vì làm mất trực tiếp ngữ cảnh embedding.*

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Dữ liệu bẩn gây ra *Silent Failure* vô cùng nguy hiểm cho AI/RAG.
2. Great Expectations là công cụ đắc lực tạo "chốt chặn" (Quality Gate) cho Data Pipeline.
3. Việc duy trì Data Lineage & Raw Snapshot là chìa khóa để khôi phục hệ thống tự động.

### Nếu có thêm thời gian

Tự động hóa phát hiện lỗi schema và kích hoạt cơ chế Auto-rollback / Auto-repair mà không cần chạy lại script bằng tay.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Công Thịnh

**Ngày xác nhận:** 2026-09-26
