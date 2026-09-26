# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                                                                                |
| --------------- | --------------------------------------------------------------------------------------- |
| Họ và tên       | Trần Quốc Toản                                                                          |
| MSSV            | 2A202602984                                                                             |
| Khóa/Lớp        | [K4-L3B]                                                                                |
| Tên nhóm        | Lạc Trôi                                                                                |
| Vai trò chính   | Pipeline & RAG Evaluation Engineer                                                      |
| Repository      | https://github.com/2003congthinh/K4-L3B-DAY10-LacTroi-DataPipelineDataObservability.git |
| Ngày hoàn thành | 2026-09-26                                                                              |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable     | File/hàm phụ trách                              | Input nhận vào              | Output bàn giao                                | Trạng thái |
| ---------------------- | ----------------------------------------------- | --------------------------- | ---------------------------------------------- | ---------- |
| Retrieval & Vector DB  | `src/retrieval/index.py`, `embeddings.py`       | `df_clean` / `df_corrupted` | ChromaDB Collection & Embeddings JSON          | Hoàn thành |
| Benchmark Evaluation   | `src/evaluation/testset.py`, `metrics.py`       | Vector Index + Testset      | `baseline_metrics.json`, Hit Rate, Token F1    | Hoàn thành |
| Pipeline Orchestration | `src/pipelines/phase1.py`, `corruption_flow.py` | System Settings             | Báo cáo Markdown 3 trạng thái & Console Output | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động           | Thành viên/module được hỗ trợ                   | Kết quả                                                  |
| ------------------- | ----------------------------------------------- | -------------------------------------------------------- |
| Debug Data Pipeline | Nguyễn Công Thịnh (`src/ingestion/cleaning.py`) | Đảm bảo kiểu dữ liệu thời gian UTC đồng bộ toàn pipeline |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện          | File/hàm/artifact liên quan                       | Kết quả bàn giao                              | Cách xác minh                          |
| ------------------------------ | ------------------------------------------------- | --------------------------------------------- | -------------------------------------- |
| Khởi tạo ChromaDB Index        | `src/retrieval/index.py` (`LocalEmbeddingIndex`)  | Indexed 24 văn bản vào Vector Database        | Script Phase 1 & Phase 2               |
| Đánh giá RAG Metrics           | `src/evaluation/metrics.py` (`evaluate_pipeline`) | Đo lường Retrieval Hit Rate & Token F1        | Output JSON trong `data/results/`      |
| Báo cáo đối chiếu 3 trạng thái | `src/pipelines/corruption_flow.py`                | Báo cáo `corruption_report.md` & Bảng console | `python script/run_corruption_flow.py` |

**Artifact cụ thể:** Bảng đối chiếu 3 cột rõ ràng in trên Console và file báo cáo tổng hợp `data/reports/corruption_report.md`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Đo lường định lượng sự sụt giảm hiệu năng truy vấn (Retrieval Performance) của mô hình RAG AI khi dữ liệu đầu vào bị hỏng, và chứng minh hiệu quả của cơ chế phục hồi dữ liệu thô.

### Cách triển khai

- Khởi tạo 3 ChromaDB Vector Collections riêng biệt tương ứng với 3 trạng thái dữ liệu (Baseline, Corrupted, Repaired).
- Chạy bộ 10 câu hỏi Benchmark (`eval_testset.json`) qua từng Vector Store để tính toán `Retrieval Hit Rate` và `Mean Token F1`.
- Xuất báo cáo tổng hợp dạng Markdown tự động qua `generate_corruption_report()`.

### Input, output và contract

| Thành phần              | Mô tả                                                              |
| ----------------------- | ------------------------------------------------------------------ |
| Input                   | Cleaned / Corrupted / Repaired DataFrames & `eval_testset.json`    |
| Output                  | Evaluation Metrics Dict & Markdown Report (`corruption_report.md`) |
| Module phụ thuộc        | `retrieval.index`, `evaluation.metrics`, `observability.reporting` |
| Module sử dụng output   | User UI / System Logs / Console Report                             |
| Điều kiện lỗi cần xử lý | Trường hợp Vector Store trống -> Ném ngoại lệ hoặc trả metric 0.0  |

### Cách xác minh

```bash
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Console in bảng so sánh 3 cột (Baseline vs Corrupted vs Repaired) và tạo thành công `corruption_report.md`.
- **Kết quả thực tế:** Chạy thông suốt 8/8 bước, Hit Rate: 100% -> 70% -> 100%.
- **Artifact/log:** `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn kiến trúc lưu trữ Vector Store cho 3 giai đoạn thử nghiệm.
- **Các phương án đã cân nhắc:**
  1. Ghi đè (Overwrite) lên 1 ChromaDB collection duy nhất sau mỗi bước.
  2. Cô lập 3 ChromaDB Collections riêng biệt hoặc xuất file JSON Embedding riêng cho từng trạng thái (`baseline`, `corrupted`, `repaired`).
- **Phương án đã chọn:** Phương án 2 (Cô lập hoàn toàn không gian vector của 3 trạng thái).
- **Lý do:** Tránh nhiễm bẩn chéo (cross-contamination) giữa các vector embedding dữ liệu cũ và dữ liệu mới, đảm bảo tính chính xác tuyệt đối khi so sánh metrics.
- **Bằng chứng:** Kết quả đo lường phản ánh chính xác sự sụt giảm từ 100% xuống 70% và quay về 100%.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Warning liên quan đến HuggingFace Token: `Warning: You are sending unauthenticated requests to the HF Hub...`.
- **Lệnh hoặc bước tái hiện:** Chạy `python script/run_corruption_flow.py` tại bước khởi tạo Embedding Index.
- **Nguyên nhân gốc:** Mô hình `all-MiniLM-L6-v2` tải trực tiếp từ HuggingFace Hub mà chưa cấu hình token.
- **Cách xử lý:** Kiểm tra xác nhận đây chỉ là Warning rate-limit nhẹ, mô hình vẫn fallback dùng local cache mượt mà. Đã xử lý suppressor warning để console output sạch đẹp.
- **Cách xác minh sau khi sửa:** Chạy pipeline không bị gián đoạn hay crash.
- **Điều học được:** Phân biệt rõ giữa Warning phi rủi ro và Error làm sập pipeline.

## 7. Hiểu biết về luồng end-to-end

1. **Từ Crossref đến vector index:** Dữ liệu thô từ Crossref API được parse -> lưu raw snapshot -> làm sạch & làm phong phú (`text_for_embedding`) -> tạo embedding bằng `all-MiniLM-L6-v2` -> lưu vào ChromaDB collection.
2. **Evaluation set & Ground-truth:** Dùng 10 câu hỏi benchmark với `expected_paper_ids` để so sánh trực tiếp ID bài báo do ChromaDB truy xuất nhằm tính Hit Rate & Token F1.
3. **Quality checks vs Freshness monitoring:** Quality checks kiểm tra ràng buộc cấu trúc (null, unique, format); Freshness monitoring kiểm tra SLA về thời gian (tuổi bài báo `age_days <= 180`).
4. **Vì sao dùng chung test set:** Để đảm bảo tính nhất quán (controlled environment) khi đo lường tác động của lỗi dữ liệu giữa 3 trạng thái.
5. **Repair thành công khi nào:** Khi Retrieval Hit Rate khôi phục về 100%, Quality Gate chuyển từ `FAILED` sang `PASSED` và file `corruption_report.md` xuất thành công.

## 8. Phân tích kết quả

### Metrics chính

| **Metric/signal**    | **Baseline** | **Corrupted** | **Repaired** | **Nhận xét của cá nhân**               |
| -------------------- | -----------: | ------------: | -----------: | -------------------------------------- |
| `retrieval_hit_rate` |      100.00% |        70.00% |      100.00% | Tự động khôi phục hoàn toàn sau repair |
| `mean_token_f1`      |       0.3088 |        0.3006 |       0.3088 | F1-Score phục hồi về mức ban đầu       |
| Quality checks       |       PASSED |        FAILED |       PASSED | Quality Gate hoạt động đúng kỳ vọng    |
| Freshness status     |           OK |       WARNING |           OK | SLA khôi phục về trạng thái chuẩn      |

### Kết luận từ số liệu

1. **[Data corruption]** → **[Quality Gate báo FAILED & Freshness WARNING]** → **[Retrieval Hit Rate giảm từ 100% xuống 70%]**.
2. **[Repair action từ Raw Snapshot]** → **[Quality Gate trở lại PASSED]** → **[Retrieval Hit Rate phục hồi hoàn toàn về 100%]**.

_Dữ liệu bẩn thực sự làm suy giảm đáng kể khả năng tìm kiếm thông tin chính xác của AI._

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Cách thiết lập bộ chỉ số RAG Benchmark (Retrieval Hit Rate, Token F1).
2. Tầm quan trọng của việc cô lập môi trường thử nghiệm Vector Database.
3. Luồng khôi phục dữ liệu Idempotent Pipeline giúp hệ thống AI chống chịu tốt với sự cố dữ liệu.

### Nếu có thêm thời gian

Xây dựng một Dashboard giao diện Streamlit/Gradio để hiển thị trực quan đồ thị so sánh 3 trạng thái theo thời gian thực.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trần Quốc Toản

**Ngày xác nhận:** 2026-09-26
