# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** Lạc Trôi
- **Mã Nhóm / Lớp:** K4-L3B-DAY10
- **Tên Repository Nộp Bài:** K4-L3B-DAY10-LacTroi-DataPipelineDataObservability

---

## 1. Danh sách thành viên

| STT | Họ và tên         | MSSV        | Email                   | Vai trò & Phân công công việc                                                | Báo cáo cá nhân                                     |
| --: | ----------------- | ----------- | ----------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------- |
|   1 | Nguyễn Công Thịnh | 2A202602781 | thinh20033101@gmail.com | Data & Observability Engineer (Ingestion, Quality Gate, Corruption Suite)    | `reports/individual_2A202602781_NguyenCongThinh.md` |
|   2 | Trần Quốc Toản    | 2A202602984 | toan1112004@gmail.com   | Pipeline & RAG Evaluation Engineer (ChromaDB Vector, Metrics, Pipeline Flow) | `reports/individual_2A202602984_TranQuocToan.md`    |

---

## 2. Báo cáo đóng góp chi tiết

### ## Nguyễn Công Thịnh - 2A202602781

- **Vai trò:** Trưởng nhóm & Data & Observability Engineer
- **Công việc chi tiết đã hoàn thành:**
  - Thu thập dữ liệu từ Crossref API (hỗ trợ Fallback snapshot) và xử lý làm sạch văn bản, chuẩn hóa schema (`src/ingestion/crossref.py`, `src/ingestion/cleaning.py`).
  - Cấu hình Great Expectations 1.x kiểm định Data Quality Gate và đo lường SLA Data Freshness (`src/observability/quality.py`).
  - Viết module `src/ingestion/corruption.py` tiêm 6 dạng lỗi thực nghiệm để kiểm thử hệ thống.
- **Điều học được / Đóng góp chính:**
  - Hiểu sâu sắc về Data Lineage, tầm quan trọng của Raw Snapshot và cách thiết lập Data Observability chặn đứng _Silent Failure_.

### ## Trần Quốc Toản - 2A202602984

- **Vai trò:** Pipeline & RAG Evaluation Engineer
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng Vector DB với ChromaDB, quản lý embedding mô hình `all-MiniLM-L6-v2` (`src/retrieval/index.py`).
  - Thiết lập bộ benchmark testset và đo lường chỉ số Retrieval Hit Rate & Token F1 (`src/evaluation/`).
  - Tích hợp và vận hành toàn tuyến Phase 1 (`src/pipelines/phase1.py`) và Phase 2 (`src/pipelines/corruption_flow.py`) tích hợp cơ chế khôi phục dữ liệu tự động.
  - Tự động hóa xuất báo cáo Markdown đối chiếu 3 trạng thái tại `data/reports/corruption_report.md`.
- **Điều học được / Đóng góp chính:**
  - Kỹ năng xây dựng Idempotent Pipeline, cô lập các vector collection và đo lường sự suy giảm hiệu năng của mô hình AI khi bị tác động bởi dữ liệu bẩn.
