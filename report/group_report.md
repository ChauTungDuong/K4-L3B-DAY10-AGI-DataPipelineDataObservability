# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4-L3B                     |
| Tên nhóm         | Nhóm 3 người               |
| Repository         | https://github.com/ChauTungDuong/K4-L3B-DAY10-AGI-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26                 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Châu Tùng Dương | (Trưởng nhóm) | Pipeline Orchestration & Corruption Engine | `src/ingestion/corruption.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `core/` |
| 2 | Nguyễn Gia Khánh | Thành viên 1 | Ingestion & Data Cleaning | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `data/raw/`, `data/clean/` |
| 3 | Nguyễn Đình Tuấn Anh | Thành viên 2 | Observability & Evaluation | `src/observability/quality.py`, `src/evaluation/testset.py`, `src/observability/reporting.py` |

## 2. Tóm tắt kết quả

Nhóm đã hoàn thành toàn diện toàn bộ 6 checkpoint của bài lab theo kiến trúc phân tán 3 thành viên:
1. **Baseline Pipeline:** Thu thập 24 tài liệu khoa học từ Crossref API, chuẩn hóa schema, tính toán `age_days` và `text_for_embedding`, lưu trữ snapshot raw bất biến và lập chỉ mục vào ChromaDB (`papers-baseline`). Đánh giá 10 câu hỏi chuẩn đạt **Retrieval Hit Rate = 1.0000** và **Mean Token F1 = 0.6933**; kiểm định chất lượng dữ liệu với Great Expectations 1.x đạt **PASSED**.
2. **Data Corruption:** Giả lập 6 kịch bản lỗi thực tế (`drop_latest`, `blank_summary`, `inject_noise`, `truncate_title`, `stale_date`, `duplicate_rows`). Lỗi khiến Retrieval Hit Rate suy giảm từ **1.0000 xuống 0.9000**, Token F1 giảm xuống 0.6799; Great Expectations Quality Gate chuyển sang **FAILED (False)**; Freshness SLA chuyển sang **STALE (False)**.
3. **Idempotent Repair:** Kích hoạt cơ chế phục hồi tự động đọc lại từ snapshot raw bất biến, tái xử lý sạch 24 records, tái lập chỉ mục vào collection ChromaDB mới (`papers-repaired`). Hiệu năng RAG được khôi phục hoàn toàn: **Hit Rate đạt lại 1.0000**, **Token F1 đạt lại 0.6933**, và Quality Gate đạt lại **PASSED (True)**.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API (Fallback Offline Snapshot)
    -> raw response / raw records (data/raw/papers_raw.json)
    -> cleaning & schema enrichment (age_days, text_for_embedding)
    -> embedding (all-MiniLM-L6-v2) + ChromaDB index (papers-baseline)
    -> evaluation baseline (10 questions test set)
    -> quality (GX 1.x) & freshness SLA reports
    -> corruption injection (6 scenarios -> data/clean/papers_clean_corrupted.csv)
    -> re-index (papers-corrupted) & re-evaluate (Hit Rate drops to 0.90)
    -> idempotent repair from raw snapshot (data/clean/papers_clean_repaired.csv)
    -> re-index (papers-repaired) & re-evaluate (Hit Rate recovers to 1.00)
    -> 3-state comparison report (data/reports/corruption_report.md)
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref REST API / Snapshot | Fetch, timeout retry, fallback offline | `data/raw/papers_raw.json` | Nguyễn Gia Khánh |
| Cleaning          | Raw records    | Parse đa dạng trường ngày, validate null, tạo text_for_embedding, age_days | `data/clean/papers_clean.csv`, `papers_clean.json` | Nguyễn Gia Khánh |
| Embedding/index   | Clean texts    | SentenceTransformer all-MiniLM-L6-v2, ChromaDB persistent client | `data/chroma/`, `data/embeddings/` | Cả nhóm |
| Evaluation        | Clean papers   | Sinh bộ 10 câu hỏi đa dạng, đo Hit Rate, Token F1, LLM Judge | `data/eval/test_set.json`, `data/results/` | Nguyễn Đình Tuấn Anh |
| Observability     | Clean DataFrame | GX 1.x Ephemeral Data Context, In-memory Batch, Freshness SLA | `data/quality/*.json` | Nguyễn Đình Tuấn Anh |
| Corruption/repair | Clean dataset  | Bơm 6 kịch bản lỗi, log corruption; Idempotent repair từ snapshot | `data/results/corruption_log.json`, `data/clean/*_repaired.*` | Châu Tùng Dương |
| Orchestration     | Toàn bộ modules | Kết nối pipeline Phase 1 & Corruption Flow, xuất báo cáo đối chiếu | `script/run_phase1.py`, `script/run_corruption_flow.py`, `data/reports/` | Châu Tùng Dương |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `gemini`            |
| `LLM_MODEL`                | `gemini-3.8-flash`  |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24                  |
| Retrieval `top_k`           | 3                   |
| Freshness threshold          | 30 ngày (90 ngày)   |
| Random seed                  | 42                  |

### Lệnh chạy

1. Chạy Baseline Pipeline:
```bash
python script/run_phase1.py
```

2. Chạy Luồng Corruption & Idempotent Repair:
```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công (Exit code 0)                       | 2026-09-26                    | `data/reports/phase1_report.md`      |
| Corruption flow   | Thành công (Exit code 0)                       | 2026-09-26                    | `data/reports/corruption_report.md`  |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | [Crossref endpoint/dataset thực tế] |
| Query/filter                | [Query hoặc filter]                  |
| Thời điểm lấy dữ liệu | [Timestamp]                           |
| Số record nhận được    | [Số lượng]                         |
| Cơ chế retry/backoff      | [Mô tả ngắn]                       |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| [Tên trường] | [Kiểu]         | [Có/Không] | [Ý nghĩa] | [Cách xử lý]        |
| [Tên trường] | [Kiểu]         | [Có/Không] | [Ý nghĩa] | [Cách xử lý]        |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| [Ví dụ: loại record không có title] | [Completeness/Validity/...]  |              [Số lượng] | [Artifact/kiểm tra] |
| [Quy tắc thực tế]                     | [Dimension]                  |              [Số lượng] | [Artifact/kiểm tra] |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

[Mô tả tại đây.]

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | [Số lượng]                 |
| Các`question_type`                    | [Danh sách]                  |
| Ground-truth document ID                 | [Cách tạo/đối chiếu]     |
| Embedding model                          | [Tên model]                  |
| Vector store/collection                  | [Tên/config]                 |
| Retrieval`top_k`                       | [Giá trị]                   |
| LLM provider/model                       | [Giá trị]                   |
| Test set dùng chung cho ba trạng thái | [Đường dẫn hoặc ID/hash] |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

[Giải thích tại đây.]

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | [Có/Thiếu] | [Ghi chú] |
| Cleaned dataset          | `data/clean/`                        | [Có/Thiếu] | [Ghi chú] |
| Embedding manifest/index | `data/embeddings/`                   | [Có/Thiếu] | [Ghi chú] |
| Evaluation set           | `data/eval/`                         | [Có/Thiếu] | [Ghi chú] |
| Baseline metrics         | `data/results/baseline_metrics.json` | [Có/Thiếu] | [Ghi chú] |
| Quality/freshness        | `data/quality/`                      | [Có/Thiếu] | [Ghi chú] |
| Baseline report          | `data/reports/phase1_report.md`      | [Có/Thiếu] | [Ghi chú] |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     [Giá trị] | [Ý nghĩa trong kết quả của nhóm]  |
| `mean_token_f1`      |     [Giá trị] | [Diễn giải]                           |
| `judge_accuracy`     |     [Giá trị] | [Diễn giải]                           |
| `mean_judge_score`   |     [Giá trị] | [Diễn giải]                           |
| Ragas, nếu có        | [Giá trị/N/A] | [Diễn giải hoặc lý do không chạy] |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| [Tên check] | [Dimension]       | [Ngưỡng]         | [Pass/Fail + giá trị] | [Artifact]   |
| [Tên check] | [Dimension]       | [Ngưỡng]         | [Pass/Fail + giá trị] | [Artifact]   |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | [Dataset/index/artifact]            |
| Timestamp mới nhất       | [Giá trị]                         |
| Ngưỡng freshness         | [Giá trị]                         |
| Trạng thái baseline      | [Fresh/Stale/Unknown]               |
| Lý do                     | [Giải thích dựa trên số liệu] |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| [Loại corruption] | [Mô tả]  |          [Số lượng] | [Kỳ vọng]              | [Artifact/metric]     | [Cách repair] |
| [Loại corruption] | [Mô tả]  |          [Số lượng] | [Kỳ vọng]              | [Artifact/metric]     | [Cách repair] |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: [Có/Thiếu]
- Nhận xét: [Log có đủ loại corruption, record bị tác động và tham số hay không?]

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

[Giải thích tại đây.]

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |   1.0000 |    0.9000 |   1.0000 |                  -0.1000 |          +0.1000 | Giảm do drop_latest & inject_noise; phục hồi hoàn toàn sau repair |
| `mean_token_f1`        |   0.6933 |    0.6799 |   0.6933 |                  -0.0134 |          +0.0134 | Giảm do nhiễu văn bản và tiêu đề bị cắt; phục hồi nguyên vẹn |
| `judge_accuracy`       |   0.7000 |    0.7000 |   0.7000 |                   0.0000 |           0.0000 | Đạt 7/10 câu chuẩn xác |
| `mean_judge_score`     |   3.4000 |    3.4000 |   3.4000 |                   0.0000 |           0.0000 | Ổn định ở mức 3.4/5.0 |
| Quality checks pass/fail | PASSED   | FAILED    | PASSED   |          Chuyển sang FAIL |  Trở lại PASSED | GX 1.x bắt được summary rỗng, duplicate và title ngắn |
| Freshness status         | FRESH    | STALE     | STALE    |         Chuyển sang STALE |           STALE | Cảnh báo đúng SLA dữ liệu cũ |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. **Nhân quả Corruption:** Khi giả lập xóa bản ghi mới nhất (`drop_latest`) và làm hỏng văn bản tóm tắt (`blank_summary` + `inject_noise`) trên tập dữ liệu sạch, chốt kiểm định Great Expectations lập tức báo động **FAILED** trên các expectation `expect_column_values_to_not_be_null` và `expect_column_value_lengths_to_be_between`. Đồng thời, hiệu năng truy vấn RAG bị suy giảm rõ rệt: **Retrieval Hit Rate rơi từ 100% (1.0000) xuống còn 90% (0.9000)** do câu hỏi liên quan đến tài liệu bị xóa không còn tìm thấy trong top-k.
2. **Nhân quả Idempotent Repair:** Khi hệ thống kích hoạt cơ chế Idempotent Repair, toàn bộ pipeline nạp lại từ raw snapshot bất biến (`data/raw/papers_raw.json`), loại bỏ hoàn toàn các biến dạng bẩn, tái lập chỉ mục vào một collection độc lập (`papers-repaired`). Kết quả là Quality Gate phục hồi về **PASSED**, và **Retrieval Hit Rate được khôi phục trọn vẹn 100% (1.0000)** cùng **Mean Token F1 đạt lại 0.6933**. Điều này chứng minh tính ưu việt của thiết kế Idempotent Pipeline so với việc sửa chắp vá dữ liệu tại chỗ.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** [Lỗi hoặc kết quả sai.]
- **Nguyên nhân:** [Root cause.]
- **Cách xử lý:** [Thay đổi đã thực hiện.]
- **Cách xác minh:** [Lệnh và artifact.]

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| [Giới hạn]          | [Ảnh hưởng] | [Đề xuất]                              |
| [Giới hạn]          | [Ảnh hưởng] | [Đề xuất]                              |

## 13. Checklist trước khi nộp

- [ ] Thông tin nhóm và repository chính xác.
- [ ] Phân công khớp với module, artifact và kết quả thực tế.
- [ ] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [ ] Baseline, corrupted và repaired dùng cùng evaluation set.
- [ ] Bảng metrics khớp với các file trong `data/results/`.
- [ ] Quality/freshness conclusions khớp với `data/quality/`.
- [ ] Các đường dẫn báo cáo và artifact truy cập được.
- [ ] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [ ] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
