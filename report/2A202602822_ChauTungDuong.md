# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                 |
| ------------------ | ------------------------------------------------------------------------ |
| Họ và tên       | Châu Tùng Dương                                                          |
| MSSV               | 2A202602822                                         |
| Khóa/Lớp         | K4-L3B                                                                   |
| Tên nhóm         | AGI                                         |
| Vai trò chính    | Trưởng nhóm / Pipeline Orchestration & Corruption Engine                 |
| Repository         | https://github.com/ChauTungDuong/K4-L3B-DAY10-AGI-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26                                                               |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | ------------------ | -------------- | --------------- | ---------- |
| Synthetic Corruption Engine | `src/ingestion/corruption.py` (`corrupt_clean_dataframe`, 6 kịch bản) | `data/clean/papers_clean.csv` | `data/clean/papers_clean_corrupted.csv`, `data/results/corruption_log.json` | Hoàn thành |
| Baseline Pipeline Orchestration | `src/pipelines/phase1.py` (`run_phase1_pipeline`), `script/run_phase1.py` | Settings, raw/clean data, testset | `data/chroma/` (`papers-baseline`), `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` | Hoàn thành |
| Corruption & Repair Flow | `src/pipelines/corruption_flow.py` (`run_corruption_flow_pipeline`), `script/run_corruption_flow.py` | Baseline data & metrics, raw snapshot | `data/clean/papers_clean_repaired.csv`, `data/chroma/` (`papers-repaired`), `data/results/corrupted_metrics.json`, `repaired_metrics.json`, `data/reports/corruption_report.md` | Hoàn thành |
| LLM Integration & Timeout Guard | `src/retrieval/llm.py` (`build_llm`), `.env` | Provider settings & API Keys | Cấu hình `gemini-3.8-flash` với timeout & fallback an toàn | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ----------------------------- | ------- |
| Tích hợp Git & Code Review | Nguyễn Gia Khánh (Thành viên 1), Nguyễn Đình Tuấn Anh (Thành viên 2) | Review mã nguồn, giải quyết merge conflict và đồng bộ sạch sẽ 2 nhánh `nguyengiakhanh` và `tuananh` vào `main`. |
| Sửa lỗi trích xuất ngày đa nguồn | Ingestion (`src/ingestion/crossref.py`) | Mở rộng regex/parser để bắt `published-online`, `published-print`, `issued`, `created` và lọc bỏ thẻ XML JATS `<jats:p>`. |
| Phòng vệ ép kiểu dữ liệu null/float | Retrieval QA (`src/retrieval/qa.py`) | Đảm bảo chuyển đổi an toàn các trường metadata tránh lỗi `AttributeError` / `TypeError` khi dữ liệu bị tiêm null. |
| Khắc phục lỗi mã hóa Windows Console | Pipeline Execution (`src/pipelines/corruption_flow.py`) | Chuẩn hóa chuỗi in ra console thành mã ASCII an toàn, tránh văng lỗi `UnicodeEncodeError: 'charmap'` trên PowerShell Windows. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------- | --------------------------- | ---------------- | ------------- |
| Thiết kế 6 kịch bản tiêm lỗi dữ liệu | `src/ingestion/corruption.py` | File dữ liệu bẩn và nhật ký `data/results/corruption_log.json` | `python -c "from ingestion.corruption import corrupt_clean_dataframe..."` |
| Kết nối toàn trình Baseline Pipeline | `src/pipelines/phase1.py` | Báo cáo baseline `data/reports/phase1_report.md`, Hit Rate = 1.0000 | `python script/run_phase1.py` (Exit code 0) |
| Thực thi luồng Corruption - Evaluation - Idempotent Repair | `src/pipelines/corruption_flow.py` | Báo cáo 3 trạng thái `data/reports/corruption_report.md`, Hit Rate phục hồi 1.0000 | `python script/run_corruption_flow.py` (Exit code 0) |

**Output cụ thể tạo ra:**
- Bảng đối chiếu 3 trạng thái (Baseline vs Corrupted vs Repaired) tại `data/reports/corruption_report.md` thể hiện sự suy giảm định lượng khi có lỗi và sự phục hồi 100% của hệ thống RAG sau cơ chế Idempotent Repair.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. Trong môi trường thực tế, dữ liệu bẩn (Silent Data Corruption) xâm nhập vào Vector DB mà không làm sập ứng dụng, nhưng lại âm thầm làm suy giảm nghiêm trọng độ chính xác của AI Agent.
2. Cần một cơ chế giả lập lỗi có thể tái lặp (Reproducible) với đầy đủ 6 dạng biến dạng (mất dữ liệu, rỗng tóm tắt, nhiễu văn bản, cắt ngắn tiêu đề, dữ liệu cũ/stale, trùng lặp dòng).
3. Khi phát hiện dữ liệu bẩn thông qua Chốt kiểm dịch (Great Expectations), hệ thống không được sửa chữa chắp vá (patch-in-place) mà phải kích hoạt cơ chế **Idempotent Repair** khôi phục hoàn toàn từ raw snapshot bất biến.

### Cách triển khai
- **Cơ chế Tiêm Lỗi (`src/ingestion/corruption.py`):**
  Sử dụng `random.Random(seed=42)` để đảm bảo tính xác định (determinism). Thực thi tuần tự 6 thao tác:
  1. `drop_latest`: Sắp xếp theo ngày xuất bản và xóa bản ghi mới nhất.
  2. `blank_summary`: Chọn ngẫu nhiên 2 bản ghi và gán trường `summary = ""`.
  3. `inject_noise`: Bơm các chuỗi ký tự ngẫu nhiên hoặc cảnh báo nhiễu vào trường `summary`.
  4. `truncate_title`: Cắt ngắn tiêu đề bài báo xuống dưới 10 ký tự để kích hoạt lỗi độ dài của Great Expectations.
  5. `stale_date`: Gán ngày xuất bản về quá khứ xa (>365 ngày trước) để vi phạm SLA Freshness.
  6. `duplicate_rows`: Nhân đôi bản ghi đầu tiên để vi phạm tính duy nhất (Uniqueness).
  Mỗi bước đều ghi lại metadata vào danh sách và xuất ra `data/results/corruption_log.json`.

- **Cơ chế Idempotent Repair & Orchestration (`src/pipelines/corruption_flow.py`):**
  - Không sửa chữa đè lên tập dữ liệu bị hỏng.
  - Tải lại snapshot bất biến từ `data/raw/papers_raw.json` và gọi hàm `build_clean_dataframe()` với schema chuẩn.
  - Nạp dữ liệu phục hồi vào collection ChromaDB riêng biệt (`papers-repaired`), giữ nguyên collection `papers-baseline` và `papers-corrupted` để so sánh đa chiều.
  - Chạy bộ 10 câu hỏi testset chuẩn trên cả 3 trạng thái và tính toán metrics tổng hợp.

### Input, output và contract

| Thành phần | Mô tả |
| ---------- | ----- |
| Input | `data/clean/papers_clean.csv`, `data/raw/papers_raw.json`, `data/eval/test_set.json` |
| Output | `data/clean/papers_clean_corrupted.csv`, `data/clean/papers_clean_repaired.csv`, `data/results/*.json`, `data/reports/corruption_report.md` |
| Module phụ thuộc | `src/ingestion/cleaning.py`, `src/observability/quality.py`, `src/retrieval/index.py` |
| Module sử dụng output | `src/observability/reporting.py`, các script đánh giá và báo cáo chung nhóm |
| Điều kiện lỗi cần xử lý | Bắt lỗi thiếu trường, dữ liệu `NaN`/null trong DataFrame khi chuyển sang ChromaDB metadata; timeout từ LLM API |

### Cách xác minh
```bash
python script/run_corruption_flow.py
```
- **Kết quả mong đợi:** Toàn bộ pipeline chạy qua 3 pha, Great Expectations bắt được lỗi trên tập corrupted, sau đó sửa thành công và in bảng đối chiếu 3 trạng thái với exit code 0.
- **Kết quả thực tế:** Pipeline chạy hoàn hảo trong ~1.5 phút, tạo đầy đủ artifacts và in bảng đối chiếu 3 trạng thái ra console.
- **Artifacts:** `data/reports/corruption_report.md`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn chiến lược phục hồi dữ liệu khi Great Expectations phát hiện dữ liệu bẩn: Sửa trực tiếp trên bảng dữ liệu hiện tại (In-place patching) hay Khôi phục bất biến từ đầu nguồn (Idempotent Repair from raw snapshot).
- **Các phương án đã cân nhắc:**
  1. *Phương án 1 (In-place patching):* Viết hàm tìm các dòng bị `NaN` hoặc trùng lặp trong DataFrame bị lỗi rồi xóa/điền giá trị mặc định.
  2. *Phương án 2 (Idempotent Repair from snapshot):* Đọc lại từ raw snapshot ban đầu (`data/raw/papers_raw.json`), chạy lại toàn bộ bước làm sạch và tái lập chỉ mục vào một collection ChromaDB mới.
- **Phương án đã chọn:** Phương án 2 (Idempotent Repair).
- **Lý do:** In-place patching dễ để sót các lỗi tiềm ẩn (ví dụ: các dòng bị xóa mất do `drop_latest` không thể tự tái tạo lại nếu chỉ nhìn vào dữ liệu lỗi). Idempotent Repair đảm bảo tính toán tử tái lặp, tính toàn vẹn (Data Lineage) và phục hồi 100% thông tin bị mất mà không tạo ra các tác dụng phụ (side effects).
- **Bằng chứng:** Sau khi chạy Idempotent Repair, Retrieval Hit Rate được phục hồi nguyên vẹn từ `0.9000` về `1.0000` (khôi phục được cả bài báo bị xóa bởi `drop_latest`), và Great Expectations Quality Gate chuyển từ `FAILED` về `PASSED`.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  google.genai.errors.ClientError: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'This model models/gemini-2.0-flash is no longer available to new users. Please update your code to use models/gemini-3.8-flash for the latest features and improvements.'}}
  ```
  Và khi chạy trên Windows PowerShell:
  ```text
  UnicodeEncodeError: 'charmap' codec can't encode character '\u1ea2' in position 12: character maps to <undefined>
  ```
- **Lệnh hoặc bước tái hiện:** Chạy `python script/run_corruption_flow.py` khi cấu hình `LLM_MODEL=gemini-2.0-flash`.
- **Nguyên nhân gốc:**
  1. Google đã chính thức ngừng cung cấp `gemini-2.0-flash` và `gemini-2.5-flash` cho người dùng mới qua API và yêu cầu chuyển sang `gemini-3.8-flash`.
  2. Windows console sử dụng bảng mã mặc định `cp1252` thay vì UTF-8, nên khi in tiêu đề có dấu tiếng Việt trực tiếp ra `sys.stdout` đã gây ra lỗi mã hóa ký tự.
- **Cách xử lý:**
  1. Cập nhật `.env` sang `LLM_MODEL=gemini-3.8-flash`. Đồng thời thiết lập `timeout=8` và cơ chế fallback heuristic tự động trong `src/evaluation/metrics.py` để pipeline không bao giờ bị nghẽn nếu gặp giới hạn RPM (5 RPM).
  2. Chuẩn hóa tiêu đề in ra console trong `src/pipelines/corruption_flow.py` sang tiếng Anh ASCII-safe.
- **Cách xác minh sau khi sửa:** Chạy lại `python script/run_corruption_flow.py`, script chạy thông suốt đến bước cuối và kết thúc với Exit code 0.
- **Điều học được:** Khi xây dựng Data & AI Pipeline trên môi trường Windows và Cloud LLM, luôn cần thiết kế cơ chế graceful degradation (fallback) cho LLM evaluator và đảm bảo stdout an toàn về mã hóa ký tự.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Dữ liệu thô từ Crossref REST API được trích xuất qua `crossref.py` và lưu trữ nguyên bản tại `data/raw/papers_raw.json`. Module `cleaning.py` làm sạch các thẻ XML, chuẩn hóa ngày tháng, tính `age_days` và nối ghép `title` + `summary` thành `text_for_embedding`. Chuỗi văn bản này được mô hình `sentence-transformers/all-MiniLM-L6-v2` chuyển đổi thành các vector 384 chiều và lưu trữ vào ChromaDB persistent storage kèm theo metadata.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Module `testset.py` sinh ra 10 câu hỏi chuẩn hóa từ chính các bài báo sạch, lưu kèm `ground_truth_doc_ids`. Khi RAG agent truy vấn, nếu danh sách `retrieved_doc_ids` chứa ít nhất một document ID nằm trong ground-truth, `retrieval_hit` được tính là True. Answer quality được đo bằng Token F1 so khớp giữa câu trả lời sinh ra và `ground_truth`.
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - *Quality checks (Great Expectations):* Kiểm tra tính đúng đắn cấu trúc và nội dung tĩnh (Schema, Null values, Uniqueness, Length constraints).
   - *Freshness monitoring (SLA):* Đo lường tính cập nhật theo thời gian (Timestamp so với hiện tại), cảnh báo khi dữ liệu bị lỗi thời (Stale data) vượt quá ngưỡng thời gian cam kết (ví dụ >25% số bài báo cũ hơn 180 ngày).
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Để đảm bảo tính khách quan và khoa học của phương pháp đo lường (Controlled Experiment). Cùng một bộ câu hỏi kiểm tra thì sự thay đổi của Hit Rate hay Token F1 mới phản ánh chính xác 100% tác động của chất lượng dữ liệu chứ không bị nhiễu bởi độ khó của câu hỏi.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Repair thành công khi:
   - Dữ liệu sạch tái sinh đạt đủ 24 bản ghi chuẩn (`data/clean/papers_clean_repaired.csv`).
   - Great Expectations Quality Gate chuyển từ `FAILED` thành `PASSED (True)`.
   - `retrieval_hit_rate` phục hồi từ `0.9000` trở lại `1.0000`, và `mean_token_f1` đạt lại `0.6933`.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | --------------------- |
| `retrieval_hit_rate` |   1.0000 |    0.9000 |   1.0000 | Giảm 10% khi tiêm lỗi xóa bài; phục hồi trọn vẹn 100% sau repair |
| `mean_token_f1`      |   0.6933 |    0.6799 |   0.6933 | Giảm do nhiễu và cắt ngắn tiêu đề; phục hồi nguyên vẹn |
| `judge_accuracy`     |   0.7000 |    0.7000 |   0.7000 | Trả lời chính xác 7/10 câu hỏi phức tạp |
| `mean_judge_score`   |   3.4000 |    3.4000 |   3.4000 | Điểm đánh giá trung bình ổn định ở mức 3.4/5.0 |
| Quality checks         |   PASSED |   FAILED  |   PASSED | GX 1.x phát hiện chính xác null, title ngắn và duplicate |
| Freshness status       |    FRESH |    STALE  |    STALE | Bắt đúng sự vi phạm SLA thời gian xuất bản |

### Kết luận từ số liệu

1. **Chuỗi nguyên nhân 1 (Corruption):** Xóa bản ghi mới nhất (`drop_latest`) + tiêm nhiễu (`inject_noise`) $\rightarrow$ GX báo động vi phạm `expect_column_values_to_not_be_null` $\rightarrow$ `retrieval_hit_rate` sụt giảm từ **1.0000 xuống 0.9000** do mất ngữ cảnh tài liệu mục tiêu.
2. **Chuỗi nguyên nhân 2 (Idempotent Repair):** Kích hoạt đọc lại từ `data/raw/papers_raw.json` $\rightarrow$ Khôi phục 24 dòng sạch và nạp vào collection `papers-repaired` $\rightarrow$ `retrieval_hit_rate` **phục hồi 100% (1.0000)** và GX Quality Gate trở lại **PASSED**.

- **Corruption ảnh hưởng rõ nhất:** `drop_latest` ảnh hưởng trực tiếp và nghiêm trọng nhất đến Retrieval Hit Rate vì một khi văn bản nguồn bị biến mất hoàn toàn khỏi Vector DB, RAG Agent hoàn toàn không thể tìm thấy thông tin để trả lời.
- **Kết quả bất ngờ:** `mean_token_f1` trên tập corrupted chỉ giảm nhẹ (từ 0.6933 xuống 0.6799) vì 9 câu hỏi còn lại vẫn tìm thấy bài báo liên quan, cho thấy nếu chỉ nhìn vào Token F1 trung bình thì rất dễ bị "đánh lừa" nếu không có Retrieval Hit Rate và Great Expectations kiểm soát.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Kiến trúc Pipeline Bất Biến (Immutability & Idempotence):** Luôn bảo vệ bản sao Raw Data Snapshot nguyên gốc. Khi có sự cố dữ liệu, tái sinh pipeline từ đầu nguồn luôn an toàn và sạch sẽ hơn việc vá lỗi cục bộ.
2. **Data Observability chặn Silent Failure:** Các hệ thống AI Agent hiếm khi sập khi dữ liệu lỗi; chúng sẽ âm thầm trả về kết quả ảo tưởng (hallucination). Chốt kiểm dịch Great Expectations là phòng tuyến tối quan trọng.
3. **Phân tách không gian Vector (Vector Isolation):** Khi thử nghiệm hoặc phục hồi, việc tạo các collection ChromaDB độc lập (`papers-baseline`, `papers-corrupted`, `papers-repaired`) giúp việc đo lường và rollback diễn ra an toàn mà không làm gián đoạn hệ thống đang chạy.

### Nếu có thêm thời gian
Tích hợp thêm cơ chế Circuit Breaker tự động: Khi Great Expectations phát hiện Quality Gate bị `FAILED`, hệ thống sẽ tự động chặn không cho nạp dữ liệu vào Vector DB phục vụ người dùng và tự động kích hoạt quy trình Idempotent Repair mà không cần can thiệp thủ công.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Châu Tùng Dương  
**Ngày xác nhận:** 2026-09-26  
