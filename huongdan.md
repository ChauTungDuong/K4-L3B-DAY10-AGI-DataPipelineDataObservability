# Hướng Dẫn Kỹ Thuật Chi Tiết (Technical Guide) — Day 10
Chào mừng bạn đến với tài liệu hướng dẫn thực hành của bài lab Day 10 - Data Pipeline & Data Observability (Lớp L3B).

💡 **Lời khuyên trước khi bắt đầu:** Bài lab này sẽ dẫn dắt bạn qua toàn bộ quy trình xây dựng đường ống dữ liệu (Data Pipeline) chuẩn mực cho AI: từ khâu gom dữ liệu thô, làm sạch, thiết lập chốt kiểm soát chất lượng (Data Observability Gate) với Great Expectations 1.x, cho tới việc chủ động tiêm lỗi dữ liệu (Data Corruption) để quan sát sự suy giảm hiệu năng của mô hình AI và kích hoạt cơ chế phục hồi tự động (Idempotent Recovery). Hãy đi từng bước một cách cẩn thận, đọc kỹ hướng dẫn và đối chiếu đúng Tín hiệu hoàn thành (Pass Signal) ở mỗi bước trước khi chuyển sang bước tiếp theo.

---

## 🎯 CHECKPOINT 0: Khởi tạo Môi trường & Ingestion Raw Data (30 phút)
**Deliverables:** Môi trường venv, file `.env`, `crossref_response.json`, `crossref_records.json`

### Bước 0: Khởi Tạo Repo Nhóm & Thiết Lập Git Teamwork
1. **Trưởng nhóm:** Fork repo mẫu (https://github.com/VinUni-AI20k/K4-L3B-Day10-Data-Pipeline-Data-Observability) và đổi tên thành `K4-L3B-DAY10-<TenNhom>-DataPipelineDataObservability`. Mời các thành viên (Collaborators).
2. **Thành viên:** Clone repo về máy, **BẮT BUỘC** cấu hình Git để được ghi nhận Contributor:
```bash
git config --global user.name "Họ và Tên của bạn"
git config --global user.email "email_dang_ky_github@domain.com"
```
*(Nếu không cấu hình đúng email GitHub, bạn sẽ bị mất toàn bộ điểm đóng góp cá nhân theo RUBRIC)*

### Bước 1: Khởi Tạo Môi Trường & Cấu Hình
1. Mở terminal tại thư mục gốc, kiểm tra Python (3.11 - 3.13): `python --version`.
2. Tạo và kích hoạt môi trường ảo (`.venv`):
```bash
source .venv/bin/activate  # Trên macOS/Linux
# Hoặc .\.venv\Scripts\Activate.ps1 trên Windows
```
3. Cài đặt thư viện: `python -m pip install -e .` hoặc `uv sync`.
4. Tạo tệp `.env` từ `.env.example` và dán `GOOGLE_API_KEY` của bạn vào.
5. **Kiểm tra tín hiệu hoàn thành:**
```bash
python -c "import chromadb, great_expectations, sentence_transformers; print('Môi trường sẵn sàng')"
```
*(Yêu cầu in ra: `Môi trường sẵn sàng`)*

### Bước 2: Thu Thập Dữ Liệu & Cất Giữ Bản Gốc (`src/ingestion/crossref.py`)
- **Mục tiêu:** Thu thập metadata từ Crossref REST API, bóc tách `paper_id`, `title`, `summary`... Lưu 2 file thô để bảo vệ Data Lineage (dùng làm điểm phục hồi khi có lỗi).
- **Nhiệm vụ:** Hoàn thiện `parse_crossref_payload` và `fetch_source_records`.
- **Kiểm tra tín hiệu hoàn thành:**
```bash
python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s=load_settings(); r=fetch_source_records(s); print(f'Tín hiệu hoàn thành: Đã tải {len(r)} bài báo')"
```
*(Yêu cầu in ra: `Tín hiệu hoàn thành: Đã tải 24 bài báo`)*

---

## 🎯 CHECKPOINT 1: Data Cleaning & Data Observability (35 phút)
**Deliverables:** Clean DataFrame, `papers_clean.csv`, GX suite & Freshness SLA

### Bước 3: Làm Sạch Dữ Liệu & Chuẩn Bị Văn Bản Tạo Vector (`src/ingestion/cleaning.py`)
- **Nhiệm vụ:** Hoàn thiện `build_clean_dataframe`. Tính `age_days`, tạo cột `text_for_embedding`, khử trùng lặp theo `paper_id`.
- **Kiểm tra tín hiệu hoàn thành:**
```bash
python -c "from datetime import datetime, timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), datetime.now(timezone.utc)); print(f'Tín hiệu hoàn thành: Clean thành công {len(df)} dòng')"
```

### Bước 4: Thiết Lập Chốt Kiểm Soát Dữ Liệu (Observability Gate) với Great Expectations 1.x
- **Nhiệm vụ:** Sử dụng GX 1.x Ephemeral Context. Cài đặt 4 Expectations bắt buộc (Count, NotNull, Unique, Length) và Freshness SLA (cảnh báo nếu >25% bài báo cũ hơn 180 ngày).
- **Kiểm tra tín hiệu hoàn thành:**
```bash
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print('Tín hiệu hoàn thành: Quality check status =', res['success'])"
```

---

## 🎯 CHECKPOINT 2: Benchmark Test Set & ChromaDB Indexing (30 phút)
**Deliverables:** `test_set.json`, ChromaDB collection `papers-baseline`

### Bước 5: Tạo Bộ Đề Đánh Giá Chuẩn (Benchmark Test Set) (`src/evaluation/testset.py`)
- **Nhiệm vụ:** Trích xuất 10 câu hỏi Ground Truth chia đều 4 dạng: summary, authors, date, categories.
- **Kiểm tra tín hiệu hoàn thành:**
```bash
python -c "from core.config import load_settings; from evaluation.testset import build_test_set; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); ts=build_test_set(df, s.paths.eval_testset); print(f'Tín hiệu hoàn thành: Sinh được {len(ts)} câu hỏi test')"
```

---

## 🎯 CHECKPOINT 3: Baseline Pipeline End-to-End & Báo Cáo Pha 1 (25 phút)
**Deliverables:** `baseline_metrics.json`, `phase1_report.md`

### Bước 6: Chạy Toàn Tuyến Dữ Liệu Sạch (Baseline Pipeline)
- **Nhiệm vụ:** Chạy kịch bản kết nối Ingest -> Clean -> Index -> Testset -> Evaluate.
- **Lệnh chạy:** `python script/run_phase1.py`
- **Tín hiệu hoàn thành:** Sinh ra `baseline_metrics.json` và `phase1_report.md`.

---

## 🎯 CHECKPOINT 4: Synthetic Data Corruption & Đo Lường Suy Giảm (45 phút)
**Deliverables:** `corruption_log.json`, `corrupted_metrics.json`

### Bước 7: Tiêm Lỗi Dữ Liệu Thực Nghiệm (Data Corruption Suite)
- **Nhiệm vụ:** Hoàn thiện `corrupt_clean_dataframe` tiêm 6 lỗi (Drop, Blank, Noise, Truncate, Stale, Duplicate). Ghi log vào `corruption_log.json`.
- **Kiểm tra tín hiệu hoàn thành:**
```bash
python -c "from core.config import load_settings; from ingestion.corruption import corrupt_clean_dataframe; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); c=corrupt_clean_dataframe(df, s.paths.corruption_log); print(f'Tín hiệu hoàn thành: Corrupted {len(c)} dòng')"
```

---

## 🎯 CHECKPOINT 5: Idempotent Repair & Báo Cáo Đối Chiếu (45 phút)
**Deliverables:** `corruption_report.md`, `repaired_metrics.json`

### Bước 8: Đo Lường Suy Giảm, Phục Hồi Dữ Liệu & Đối Chiếu 3 Trạng Thái
- **Nhiệm vụ:** Chạy `run_corruption_flow_pipeline` để đo lường RAG khi lỗi, sau đó kích hoạt hàm `repair_from_raw_snapshot()` phục hồi dữ liệu gốc.
- **Lệnh chạy:** `python script/run_corruption_flow.py`
- **Tín hiệu hoàn thành:** Bảng so sánh hiệu năng 3 cột (Baseline vs Corrupted vs Repaired) và file báo cáo `corruption_report.md`.

---

## 🎯 CHECKPOINT 6: Live Demo Trên Bảng, Q&A & Nghiệm Thu Nộp Bài (30 phút)
**Deliverables:** Toàn bộ code trên nhánh `main`, nộp link VLearn LMS

### Bước 9: Rà Soát Cuối Cùng & Chốt Nộp Bài (Pre-Submission Checklist)
1. **Checkout & Đồng bộ Git:** `git checkout main && git pull origin main`.
2. **Kiểm tra trạng thái Git:** Tuyệt đối không commit `.env`, `.venv/`, `__pycache__/`.
3. **Hoàn thiện Hồ Sơ:** Cập nhật `docs/TEAM.md` và từng cá nhân tạo file `reports/individual_<MSSV>_<HoTen>.md`.
4. **Kiểm tra chạy toàn tuyến (Sanity Check):** `python script/run_phase1.py` (Không được có lỗi).
5. **Nộp bài:** Commit và push toàn bộ lên GitHub. Trưởng nhóm nộp link repository (đã public) lên hệ thống VLearn LMS trước hạn chót.
