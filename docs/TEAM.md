# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** Nhóm 3 người
- **Mã Nhóm / Lớp:** K4-L3B-DAY10
- **Tên Repository Nộp Bài:** K4-L3B-DAY10-AGI-DataPipelineDataObservability

---

## 1. Danh sách thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | Châu Tùng Dương | (Trưởng nhóm) | duong@... | Trưởng nhóm / Pipeline Orchestration (`corruption.py`, `phase1.py`, `corruption_flow.py`, `core/`) | `report/ChauTungDuong.md` |
| 2 | Nguyễn Gia Khánh | Thành viên 1 | nguyenkhanh9122005@gmail.com | Data Foundation & Ingestion (`crossref.py`, `cleaning.py`, raw data snapshot) | `report/NguyenGiaKhanh.md` |
| 3 | Nguyễn Đình Tuấn Anh | Thành viên 2 | tuananh@... | Observability & Evaluation (`quality.py` GX 1.x, `testset.py`, `reporting.py`) | `report/NguyenDinhTuanAnh.md` |

---

## 2. Chi tiết phân công công việc

### Thành viên 1: Nguyễn Gia Khánh
- **Vai trò:** Data Foundation & Ingestion.
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng module thu thập Crossref API với cơ chế Fallback offline trong `src/ingestion/crossref.py`.
  - Chuẩn hóa schema, tính toán trường `age_days` và `text_for_embedding` trong `src/ingestion/cleaning.py`.
  - Lưu trữ raw snapshot bất biến tại `data/raw/papers_raw.json` để phục vụ idempotent repair.
- **Đóng góp chính:**
  - Đảm bảo 24 bài báo khoa học chất lượng cao, chuẩn hóa ngày tháng đa nguồn (`published`, `issued`, `created`).

### Thành viên 2: Nguyễn Đình Tuấn Anh
- **Vai trò:** Observability & Benchmark Evaluation.
- **Công việc chi tiết đã hoàn thành:**
  - Thiết lập Quality Gate theo chuẩn mới **Great Expectations 1.x** (Ephemeral Data Context, In-memory Pandas Batch) và Freshness SLA trong `src/observability/quality.py`.
  - Xây dựng bộ câu hỏi chuẩn 10 câu đa dạng 4 category (`factoid`, `author`, `date`, `summary`) trong `src/evaluation/testset.py`.
  - Xuất báo cáo Markdown chi tiết cho Phase 1 và Corruption flow trong `src/observability/reporting.py`.
- **Đóng góp chính:**
  - Thiết lập chốt kiểm dịch dữ liệu chặn đứng Silent Failure trước khi dữ liệu vào Vector DB.

### Thành viên 3 (Trưởng nhóm): Châu Tùng Dương
- **Vai trò:** Pipeline Orchestrator & Corruption Engine.
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng module giả lập lỗi dữ liệu đa dạng 6 kịch bản (`drop_latest`, `blank_summary`, `inject_noise`, `truncate_title`, `stale_date`, `duplicate_rows`) trong `src/ingestion/corruption.py`.
  - Kết nối luồng thực thi end-to-end trong `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`.
  - Cấu hình LLM (`gemini-3.8-flash`) và ChromaDB vector storage.
  - Hiện thực cơ chế phục hồi tự động Idempotent Repair từ snapshot và bảng đối chiếu 3 trạng thái (`Baseline` vs `Corrupted` vs `Repaired`).
- **Đóng góp chính:**
  - Chứng minh định lượng sự suy giảm hiệu năng khi dữ liệu bị lỗi (Hit Rate giảm từ 100% xuống 90%) và sự phục hồi hoàn toàn sau Idempotent Repair (Hit Rate trở lại 100%).
