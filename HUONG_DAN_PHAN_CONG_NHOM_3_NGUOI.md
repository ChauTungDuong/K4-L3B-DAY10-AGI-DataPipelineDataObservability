# HƯỚNG DẪN PHỐI HỢP NHÓM 3 NGƯỜI (PARALLEL TEAMWORK & WORKFLOW)

> **Mục tiêu:** Nhóm 3 người làm việc song song 100% bằng AI trên nhánh Git riêng biệt, thống nhất chuẩn giao tiếp (Contract) ngay từ đầu để không bị lệch pha và **merge vào `main` không bao giờ bị xung đột (conflict)**.

---

## 🤝 0. NHỮNG ĐIỀU BẮT BUỘC CẢ NHÓM PHẢI THỐNG NHẤT TỪ ĐẦU (DATA CONTRACTS)

Trước khi mỗi người tản ra gõ code trên nhánh riêng, cả 3 người cần ngồi lại 5 phút để thống nhất 6 nguyên tắc bất di bất dịch sau:

### 1. Thống nhất Data Schema của Clean DataFrame
Cả 3 người đều tương tác với DataFrame này (Thành viên 1 tạo ra, Thành viên 2 kiểm định chất lượng, Thành viên 3 tiêm lỗi & phục hồi):
- `paper_id` *(str)*: Khóa duy nhất (DOI bài báo, ví dụ: `10.1145/3637528.3671801`).
- `title` *(str)*: Tiêu đề bài báo đã chuẩn hóa khoảng trắng.
- `summary` *(str)*: Tóm tắt bài báo (đã lọc sạch thẻ XML/JATS `<jats:p>`).
- `authors_joined` *(str)*: Tên các tác giả nối nhau bằng dấu phẩy (ví dụ: `Minh Nguyen, Hoang Le`).
- `categories_joined` *(str)*: Các lĩnh vực nối bằng dấu phẩy (ví dụ: `Artificial Intelligence, Information Retrieval`).
- `published` *(str)*: Ngày xuất bản dạng chuẩn `YYYY-MM-DD`.
- `age_days` *(int)*: Số ngày tính từ lúc xuất bản đến hiện tại (`(run_date - published).days`).
- `summary_chars` *(int)*: Độ dài ký tự của summary (`len(summary)`).
- `text_for_embedding` *(str)*: Đoạn văn bản hoàn chỉnh để nạp vào ChromaDB theo mẫu 5 dòng:
  ```text
  Title: <Tiêu đề>
  Authors: <Tác giả>
  Published: <YYYY-MM-DD>
  Categories: <Lĩnh vực>
  Summary: <Tóm tắt>
  ```

### 2. Thống nhất dùng chung 1 Bộ Test Set cho cả 3 Trạng thái
- Bộ đề đánh giá `data/eval/test_set.json` (10 câu hỏi) do Thành viên 2 sinh ra.
- **Quy tắc:** Cả 3 trạng thái **Baseline**, **Corrupted** và **Repaired** BẮT BUỘC phải dùng chung đúng file `test_set.json` này để đảm bảo phép so sánh công bằng và khoa học.

### 3. Không bao giờ đổi tên hàm (Function Signature)
Tất cả hàm trong thư mục `src/` đã được định nghĩa sẵn tên hàm và kiểu dữ liệu tham số. Tuyệt đối không ai được tự ý đổi tên hàm hoặc thay đổi kiểu dữ liệu trả về vì sẽ làm gãy pipeline của đồng đội.

### 4. Không bao giờ hardcode đường dẫn file
Tuyệt đối không gõ cứng đường dẫn như `D:\VinUni-AI\...` hoặc `C:\Users\...`. Luôn luôn sử dụng đường dẫn thông qua `settings.paths` từ `core/config.py` (ví dụ: `settings.paths.raw_records_json`, `settings.paths.clean_json`).

### 5. Thống nhất cấu hình môi trường (.env)
- Mỗi thành viên tự tạo file `.env` từ `.env.example` và dán `GOOGLE_API_KEY` cá nhân.
- Tuyệt đối KHÔNG commit file `.env` lên GitHub (mất 20 điểm theo Rubric).

### 6. Cấu hình Git Email cá nhân trước khi Commit
Mỗi thành viên chạy lệnh:
```bash
git config --global user.name "Họ và Tên của bạn"
git config --global user.email "email_dang_ky_github@domain.com"
```
*(Nếu không làm bước này, commit bị coi là "Anonymous" và hệ thống chấm 0 điểm chuyên cần cá nhân).*

---

## 🗺️ 1. PHÂN CHIA RANH GIỚI FILE (FILE OWNERSHIP)

Mỗi thành viên chỉ được chỉnh sửa đúng các file được phân quyền sau:

| Thành viên | Nhánh Git | File ĐƯỢC PHÉP chỉnh sửa | Artifacts đầu ra bàn giao |
| :--- | :--- | :--- | :--- |
| **👤 Thành viên 1**<br>*(Ingestion & Cleaning)* | `feat/ingestion-cleaning` | - `src/ingestion/crossref.py`<br>- `src/ingestion/cleaning.py` | - `data/raw/crossref_response.json`<br>- `data/raw/crossref_records.json`<br>- `data/clean/papers_clean.csv` / `.json` |
| **👤 Thành viên 2**<br>*(Observability & Test)* | `feat/observability-evaluation` | - `src/observability/quality.py`<br>- `src/evaluation/testset.py`<br>- `src/observability/reporting.py` | - `data/eval/test_set.json`<br>- `data/quality/*_quality_report.json`<br>- `data/quality/freshness_report.json`<br>- Báo cáo Markdown Phase 1 & 2 |
| **👤 Thành viên 3 (Lead)**<br>*(Corruption & Pipelines)* | `feat/corruption-pipelines` | - `src/ingestion/corruption.py`<br>- `src/pipelines/phase1.py`<br>- `src/pipelines/corruption_flow.py`<br>- `docs/TEAM.md` | - `data/results/corruption_log.json`<br>- `data/results/*_metrics.json`<br>- `data/reports/phase1_report.md`<br>- `data/reports/corruption_report.md` |

---

## 📋 2. CHI TIẾT ĐẦU VIỆC & CÁCH LÀM TỪNG NGƯỜI

---

### 👤 THÀNH VIÊN 1: Ingestion & Cleaning Owner
- **Nhánh Git:** `feat/ingestion-cleaning`
- **File phụ trách:** `src/ingestion/crossref.py` & `src/ingestion/cleaning.py`

#### Công việc cần làm:
1. Trong `src/ingestion/crossref.py`:
   - `parse_crossref_payload(payload)`: Lấy các trường DOI, title, summary (lọc bỏ thẻ `<jats:p>`), authors, categories, published.
   - `fetch_source_records(settings)`: Gọi Crossref API lấy 24 bài báo. **Tích hợp cơ chế Fallback:** nếu API bị lỗi mạng hoặc HTTP 429, tự động đọc snapshot có sẵn tại `data/raw/crossref_response.json`. Lưu kết quả ra `data/raw/crossref_records.json`.
   - `load_raw_records(path)`: Đọc JSON thành danh sách `PaperRecord`.
2. Trong `src/ingestion/cleaning.py`:
   - `build_clean_dataframe(records, run_date)`: Loại bỏ trùng lặp `paper_id`, tính `age_days`, ghép `text_for_embedding` đúng 5 phần.

#### Lệnh tự kiểm tra (Pass Signals):
```bash
# Kiểm tra tải đủ 24 bài:
python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s=load_settings(); r=fetch_source_records(s); print(f'Tín hiệu hoàn thành: Đã tải {len(r)} bài báo')"

# Kiểm tra làm sạch 24 dòng:
python -c "from datetime import datetime, timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), datetime.now(timezone.utc)); print(f'Tín hiệu hoàn thành: Clean thành công {len(df)} dòng')"
```

#### Prompt đưa cho AI Assistant:
> "Hãy hoàn thiện `src/ingestion/crossref.py` và `src/ingestion/cleaning.py`. Yêu cầu: giữ nguyên chữ ký hàm, xử lý parse payload Crossref có offline fallback đọc file `data/raw/crossref_response.json`, tính `age_days`, loại bỏ duplicate `paper_id` và tạo cột `text_for_embedding` theo đúng contract."

---

### 👤 THÀNH VIÊN 2: Observability Gate & Evaluation Owner
- **Nhánh Git:** `feat/observability-evaluation`
- **File phụ trách:** `src/observability/quality.py`, `src/evaluation/testset.py`, `src/observability/reporting.py`

#### Công việc cần làm:
1. Trong `src/observability/quality.py`:
   - `run_data_quality_checks(df, settings, report_name)`: Dùng **Great Expectations 1.x Ephemeral Context**:
     - Khởi tạo context: `context = gx.get_context(mode="ephemeral")`.
     - Thêm data source và dataframe asset.
     - Thiết lập đủ 4 Expectations:
       1. Số dòng từ 5 đến 5000 (`ExpectTableRowCountToBeBetween`).
       2. Cột `paper_id`, `title`, `text_for_embedding` không được null (`ExpectColumnValuesToNotBeNull`).
       3. Cột `paper_id` là duy nhất (`ExpectColumnValuesToBeUnique`).
       4. Độ dài `summary` >= 30 ký tự (`ExpectColumnValueLengthsToBeBetween`).
     - Lưu kết quả vào `data/quality/{report_name}_quality_report.json`.
   - `build_freshness_report(df, settings, report_path)`: Cảnh báo `is_fresh = False` nếu tỷ lệ bài báo có `age_days > 180` vượt quá 25%.
2. Trong `src/evaluation/testset.py`:
   - `build_test_set(df, output_path)`: Tự động trích xuất 10 câu hỏi Ground Truth qua 4 dạng bài toán: `summary`, `authors`, `date`, `categories`. Lưu ra `data/eval/test_set.json`.
3. Trong `src/observability/reporting.py`:
   - `generate_phase1_report(...)`: Xuất file `data/reports/phase1_report.md`.
   - `generate_corruption_report(...)`: Xuất file `data/reports/corruption_report.md` so sánh 3 trạng thái.

#### Lệnh tự kiểm tra (Pass Signals):
```bash
# Kiểm tra sinh 10 câu hỏi test:
python -c "from core.config import load_settings; from evaluation.testset import build_test_set; import pandas as pd; s=load_settings(); df=pd.read_json('data/raw/crossref_records.json'); df['summary_chars']=df['summary'].str.len(); df['authors_joined']=df['authors'].apply(lambda x: ', '.join(x)); df['categories_joined']=df['categories'].apply(lambda x: ', '.join(x)); df['text_for_embedding']='Sample text'; ts=build_test_set(df, s.paths.eval_testset); print(f'Tín hiệu hoàn thành: Sinh được {len(ts)} câu hỏi test')"

# Kiểm tra Quality Gate GX 1.x:
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json('data/raw/crossref_records.json'); df['text_for_embedding']='Sample text'; res=run_data_quality_checks(df, s, 'test'); print('Tín hiệu hoàn thành: Quality check status =', res['success'])"
```

#### Prompt đưa cho AI Assistant:
> "Hãy hoàn thiện `src/observability/quality.py`, `src/evaluation/testset.py` và `src/observability/reporting.py`. Yêu cầu: Sử dụng Great Expectations 1.x (chuẩn Ephemeral Context) kiểm định 4 expectations, tính Freshness SLA 180 ngày (ngưỡng 25%), sinh testset 10 câu Ground Truth 4 nhóm và viết hàm xuất báo cáo Markdown đẹp mắt."

---

### 👤 THÀNH VIÊN 3 (Leader - Bạn): Corruption & Pipelines Orchestration
- **Nhánh Git:** `feat/corruption-pipelines`
- **File phụ trách:** `src/ingestion/corruption.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `docs/TEAM.md`

#### Công việc cần làm:
1. Trong `src/ingestion/corruption.py`:
   - `corrupt_clean_dataframe(df, output_log_path)`: Tiêm đủ 6 lỗi dữ liệu:
     1. `drop_latest`: Xóa 20% bài báo mới nhất.
     2. `blank_summary`: Xóa trắng summary ở 2 bài.
     3. `inject_noise`: Chèn chuỗi rác vào summary.
     4. `truncate_title`: Cắt title xuống < 8 ký tự.
     5. `stale_date`: Lùi published về 365 ngày trước.
     6. `duplicate_rows`: Nhân đôi 2 dòng để tạo trùng `paper_id`.
   - Cập nhật lại cột `text_for_embedding` và ghi log ra `data/results/corruption_log.json`.
2. Trong `src/pipelines/phase1.py`:
   - Viết hàm `main()`: Ingest ➔ Clean ➔ Index ChromaDB (`papers-baseline`) ➔ Build Testset ➔ Evaluate RAG (Hit Rate & Token F1) ➔ Quality & Freshness Gate ➔ Xuất `phase1_report.md`.
3. Trong `src/pipelines/corruption_flow.py`:
   - Viết hàm `main()`:
     - Tiêm lỗi ➔ Index ChromaDB (`papers-corrupted`) ➔ Evaluate (thấy chỉ số tụt dốc) ➔ GX 1.x bắt lỗi.
     - **Idempotent Repair:** Phục hồi lại từ raw snapshot ban đầu `data/raw/crossref_records.json` ➔ Clean lại ➔ Index ChromaDB (`papers-repaired`) ➔ Evaluate lại (chỉ số phục hồi).
     - Xuất báo cáo Markdown so sánh 3 trạng thái tại `data/reports/corruption_report.md`.

#### Lệnh tự kiểm tra (Pass Signals):
```bash
# Kiểm tra kịch bản Tiêm lỗi:
python -c "from core.config import load_settings; from ingestion.corruption import corrupt_clean_dataframe; import pandas as pd; s=load_settings(); df=pd.read_json('data/raw/crossref_records.json'); df['summary_chars']=df['summary'].str.len(); df['authors_joined']=df['authors'].apply(lambda x: ', '.join(x)); df['categories_joined']=df['categories'].apply(lambda x: ', '.join(x)); df['text_for_embedding']='Sample text'; c=corrupt_clean_dataframe(df, s.paths.corruption_log); print(f'Tín hiệu hoàn thành: Corrupted {len(c)} dòng')"
```

#### Prompt đưa cho AI Assistant:
> "Hãy hoàn thiện `src/ingestion/corruption.py`, `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`. Yêu cầu: Tiêm đủ 6 dạng lỗi dữ liệu và ghi log, kết nối pipeline Phase 1 chạy thông suốt từ clean data đến ChromaDB và xuất báo cáo; kết nối pipeline Phase 2 tiêm lỗi, đo suy giảm, tự phục hồi idempotent từ raw snapshot và xuất bảng đối chiếu 3 trạng thái."

---

## 🔀 3. QUY TRÌNH PHỐI HỢP GIT TỪ ĐẦU ĐẾN CUỐI

### Bước 1: Tạo nhánh riêng
Trước khi bắt đầu viết code:
- Thành viên 1: `git checkout -b feat/ingestion-cleaning`
- Thành viên 2: `git checkout -b feat/observability-evaluation`
- Thành viên 3: `git checkout -b feat/corruption-pipelines`

### Bước 2: Làm việc độc lập & Push lên GitHub
Khi hoàn thành phần việc và kiểm tra bằng lệnh test thành công:
```bash
git add src/
git commit -m "feat: complete assigned modules and verified pass signal"
git push origin <ten-nhanh-cua-ban>
```

### Bước 3: Hợp nhất (Merge) tuần tự vào `main`
Trưởng nhóm thực hiện lần lượt 3 lệnh merge sau trên máy:

```bash
# 1. Chuyển về main
git checkout main
git pull origin main

# 2. Merge Thành viên 1 (Dữ liệu nền)
git merge feat/ingestion-cleaning --no-ff -m "merge: feat/ingestion-cleaning from Member 1"

# 3. Merge Thành viên 2 (Quality Gate & Test)
git merge feat/observability-evaluation --no-ff -m "merge: feat/observability-evaluation from Member 2"

# 4. Merge Thành viên 3 (Corruption & Pipelines)
git merge feat/corruption-pipelines --no-ff -m "merge: feat/corruption-pipelines from Member 3"

# 5. Push lên GitHub
git push origin main
```
*(Do phân chia file độc lập, 100% các bước merge này sẽ thành công tự động không có xung đột).*

---

## 🏁 4. CHẠY NGHIỆM THU CUỐI CÙNG (SANITY CHECK)

Sau khi merge xong vào nhánh `main`, Trưởng nhóm chạy 2 lệnh để xác nhận toàn bộ hệ thống hoạt động hoàn hảo:

```bash
# Chạy Baseline Phase 1:
python script/run_phase1.py

# Chạy Corruption Flow Phase 2:
python script/run_corruption_flow.py
```

### Kiểm tra các Artifact sinh ra:
1. `data/clean/papers_clean.csv` (24 dòng sạch)
2. `data/results/baseline_metrics.json`
3. `data/reports/phase1_report.md`
4. `data/results/corruption_log.json`
5. `data/results/corrupted_metrics.json` & `repaired_metrics.json`
6. `data/reports/corruption_report.md` (có bảng 3 cột Baseline vs Corrupted vs Repaired)

---

## 📝 5. HOÀN THIỆN HỒ SƠ & NỘP BÀI

1. **Điền thông tin nhóm:** Mở `docs/TEAM.md`, điền tên nhóm, thông tin 3 thành viên và tỷ lệ % đóng góp.
2. **Điền báo cáo nhóm:** Mở `report/group_report.md`, copy bảng số liệu từ `data/reports/corruption_report.md` vào.
3. **Mỗi thành viên làm 1 báo cáo cá nhân:**
   - Thành viên 1: `report/<MSSV1>_<HoTen1>.md`
   - Thành viên 2: `report/<MSSV2>_<HoTen2>.md`
   - Thành viên 3: `report/<MSSV3>_<HoTen3>.md`
4. **Push toàn bộ lên GitHub:**
   ```bash
   git add docs/TEAM.md report/ data/
   git commit -m "docs: finalize team reports and deliverables"
   git push origin main
   ```
5. **Nộp bài:** Kiểm tra GitHub repo ở chế độ **Public**, tab **Insights ➔ Contributors** có tên cả 3 bạn. **Từng thành viên tự copy link repo và nộp lên VLearn LMS.**
