# Báo cáo cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Nguyễn Gia Khánh |
| MSSV | 2A202602851 |
| Khóa/Lớp | K4 / L3B |
| Tên nhóm | AGI (theo tên repository) |
| Vai trò chính | Data ingestion và cleaning |
| Repository | https://github.com/ChauTungDuong/K4-L3B-DAY10-AGI-DataPipelineDataObservability |
| Ngày lập báo cáo | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc phụ trách

| Module/deliverable | File/hàm phụ trách | Input | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Thu thập và bảo toàn dữ liệu nguồn | `src/ingestion/crossref.py`: `parse_crossref_payload`, `fetch_source_records`, `load_raw_records` | Crossref works JSON hoặc snapshot offline; `Settings` | `PaperRecord`, `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Đã triển khai và xác minh trên dữ liệu hiện có |
| Làm sạch và chuẩn bị văn bản tạo vector | `src/ingestion/cleaning.py`: `build_clean_dataframe` | Danh sách `PaperRecord`, `run_date` | DataFrame 16 cột; `data/clean/papers_clean.csv` và `.json` | Đã triển khai và xác minh trên dữ liệu hiện có |

Đầu ra của phần này là hợp đồng dữ liệu cho các bước tạo evaluation set, lập chỉ mục ChromaDB và kiểm tra chất lượng. Tôi chỉ nhận phạm vi ingestion/cleaning trong báo cáo này; các module đánh giá, quality gate và repair thuộc các bước tích hợp khác.

### Hỗ trợ ngoài phạm vi chính

| Hoạt động | Module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Kiểm tra schema để bàn giao | Evaluation, retrieval và observability | DataFrame có `paper_id`, `title`, `summary`, `published`, `age_days`, `authors_joined`, `categories_joined` và `text_for_embedding`; 24 DOI duy nhất. |

## 3. Kết quả theo vai trò

| Nhiệm vụ | File/hàm/artifact | Kết quả thực tế | Cách xác minh |
| --- | --- | --- | --- |
| Bóc tách Crossref metadata | `parse_crossref_payload`; `data/raw/crossref_response.json` | Payload hiện có 24 items và bóc tách được 24 `PaperRecord`. | Đọc snapshot và gọi hàm parse. |
| Lưu dấu vết nguồn | `fetch_source_records`; hai file trong `data/raw/` | Có bản phản hồi API và danh sách records riêng; khi lỗi mạng có thể đọc snapshot hiện có. | Kiểm tra hai JSON và gọi `load_raw_records`. |
| Chuẩn hóa dữ liệu | `build_clean_dataframe`; hai file trong `data/clean/` | 24 dòng sạch, 24 DOI duy nhất, không thiếu title/summary; mỗi dòng có văn bản embedding đủ 5 phần. | Chạy lệnh ở mục 4 và đọc lại JSON. |

Ở lần kiểm tra ngày 2026-09-26, `summary_chars` nhỏ nhất là **826**, không có dòng `age_days > 180`. Đây là thống kê trực tiếp từ dataset sạch; chưa phải kết quả của Great Expectations hoặc Freshness SLA.

## 4. Giải thích kỹ thuật

### Vấn đề cần giải quyết

Crossref trả metadata không đồng nhất: title là danh sách, abstract có thể chứa JATS/XML, ngày có nhiều nguồn và độ chính xác khác nhau. Dữ liệu đó cần được giữ nguyên để truy vết, đồng thời chuyển thành schema ổn định để downstream có thể tạo vector, kiểm tra chất lượng và phục hồi từ raw snapshot.

### Cách triển khai

1. `parse_crossref_payload` duyệt `message.items`, lấy DOI, title, abstract, author, subject, ngày và URL. Hàm bỏ mục thiếu DOI, title, summary hoặc ngày hợp lệ. `HTMLParser` loại thẻ JATS và giải mã HTML entity; ngày chỉ có năm hoặc năm/tháng được điền ngày/tháng mặc định là `01`.
2. `fetch_source_records` gọi `https://api.crossref.org/works` với query, filter và số dòng từ `Settings`. HTTP 429/5xx được retry. Phản hồi hợp lệ được lưu dưới dạng bytes gốc tại `crossref_response.json`; danh sách `PaperRecord` được lưu riêng tại `crossref_records.json`. Khi API lỗi và snapshot tồn tại, hàm đọc snapshot mà không ghi đè nó.
3. `build_clean_dataframe` chuẩn hóa khoảng trắng và thẻ còn sót, ngày về `YYYY-MM-DD`, nối tác giả/chủ đề bằng dấu phẩy, tính `summary_chars` và `age_days = (run_date.date() - published_date).days`. Hàm bỏ dòng thiếu các trường thiết yếu hoặc ngày sai và khử trùng lặp DOI không phân biệt hoa/thường; bản ghi xuất hiện trước được giữ lại.
4. `text_for_embedding` ghép đúng thứ tự `Title`, `Authors`, `Published`, `Categories`, `Summary`, mỗi phần một dòng. DataFrame được sắp theo ngày xuất bản giảm dần và DOI tăng dần để đầu ra ổn định.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input nguồn | Crossref JSON với `message.items`, hoặc snapshot `data/raw/crossref_response.json`. |
| Raw record | `PaperRecord` gồm DOI (`paper_id`), title, summary, authors, categories, dates, URLs và comment. |
| Input cleaning | `list[PaperRecord]` và thời điểm chạy `datetime`. |
| Output cleaning | DataFrame 16 cột; các cột bổ sung gồm `authors_joined`, `categories_joined`, `summary_chars`, `age_days`, `text_for_embedding`. |
| Module phụ thuộc | `core.config.Settings`, `core.utils`; downstream sử dụng dữ liệu sạch gồm `retrieval.index`, evaluation và observability. |
| Lỗi được xử lý | API lỗi/429/503 có retry hoặc snapshot; item metadata thiếu trường quan trọng bị bỏ; ngày cập nhật sai thì dùng ngày xuất bản. |

### Cách xác minh

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from datetime import datetime,timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records,parse_crossref_payload; from ingestion.cleaning import build_clean_dataframe; from core.utils import read_json; s=load_settings(); p=read_json(s.paths.raw_api_response); r=load_raw_records(s.paths.raw_records_json); df=build_clean_dataframe(r,datetime.now(timezone.utc)); print(len(p['message']['items']),len(parse_crossref_payload(p)),len(r),len(df),df.paper_id.is_unique)"
```

Kết quả thực tế: `24 24 24 24 True`. Đọc lại `data/clean/papers_clean.json` cũng cho 24 dòng. Artifact đối chiếu: `data/raw/crossref_response.json`, `data/raw/crossref_records.json`, `data/clean/papers_clean.csv`, `data/clean/papers_clean.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi Crossref tạm thời không truy cập được, lab vẫn cần cùng một nguồn dữ liệu để tiếp tục và để truy vết sai lệch về sau.
- **Hai phương án:** Chỉ gọi API và dừng khi lỗi; hoặc giữ nguyên phản hồi đã nhận và dùng lại snapshot khi API lỗi.
- **Phương án đã chọn:** Lưu phản hồi JSON gốc tách khỏi records đã bóc tách, retry lỗi HTTP tạm thời, sau đó fallback sang snapshot sẵn có.
- **Lý do:** Raw snapshot là điểm khởi đầu tái lập pipeline; không phụ thuộc vào việc API thay đổi giữa các lần chạy. Tách raw và parsed tránh nhầm dữ liệu nguồn với dữ liệu đã biến đổi.
- **Bằng chứng:** Hai artifact raw hiện tồn tại; payload có 24 items và danh sách parsed có 24 records. Việc kiểm thử nhánh API lỗi là kiểm thử mô phỏng, không được xem là bằng chứng Crossref đã lỗi trong lần chạy thực tế.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng:** Lệnh in tín hiệu nghiệm thu tiếng Việt từng gặp `UnicodeEncodeError: 'charmap' codec can't encode character` trên terminal Windows dùng mã hóa `cp1252`.
- **Cách tái hiện:** Chạy `python -c` và `print` chuỗi `Tín hiệu hoàn thành: Đã tải ... bài báo` trong terminal chưa cấu hình UTF-8.
- **Nguyên nhân:** Mã hóa đầu ra của terminal không biểu diễn được ký tự tiếng Việt; dữ liệu và hàm ingestion vẫn chạy trước khi `print` thất bại.
- **Cách xử lý:** Đặt `$env:PYTHONIOENCODING='utf-8'` trước lệnh kiểm tra.
- **Xác minh:** Lệnh nghiệm thu sau đó in `Đã tải 24 bài báo`; lệnh ở mục 4 xác minh tiếp 24 records và 24 dòng sạch.
- **Bài học:** Phân biệt lỗi hiển thị console với lỗi parse hay lỗi dữ liệu, rồi kiểm tra artifact thay vì kết luận pipeline thất bại từ một lần `print` lỗi.

## 7. Hiểu biết về luồng end-to-end

1. Crossref JSON được lưu thành raw snapshot; parser tạo `PaperRecord`. Cleaning chuẩn hóa và tạo `text_for_embedding`. Bước kế tiếp sẽ embedding văn bản này bằng MiniLM rồi nạp vào ChromaDB với `paper_id` làm định danh tài liệu. Phần index chưa được xác minh trong báo cáo này.
2. Evaluation set chứa câu hỏi, đáp án chuẩn và `ground_truth_doc_ids`. Retrieval hit rate xét tài liệu đúng có xuất hiện trong kết quả tìm kiếm; các chỉ số câu trả lời so sánh câu trả lời Agent với ground truth.
3. Quality checks kiểm tra cấu trúc/nội dung như số dòng, trường bắt buộc, DOI duy nhất và độ dài summary. Freshness đo tỷ lệ bài cũ từ `age_days`; dữ liệu đúng schema vẫn có thể quá cũ.
4. Baseline, corrupted và repaired phải dùng cùng câu hỏi, đáp án và doc IDs để thay đổi metric có thể quy về thay đổi dữ liệu/index, thay vì thay đổi bộ đo.
5. Repair cần tái tạo dữ liệu sạch từ raw snapshot, nạp lại index, chạy lại quality/freshness và đánh giá trên cùng test set. Chỉ có thể kết luận phục hồi khi artifacts và metrics của trạng thái repaired xác nhận điều đó; hiện chưa có các artifacts này.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | --------------------- |
| `retrieval_hit_rate` |   1.0000 |    0.9000 |   1.0000 | Giảm 1/10 lượt tìm đúng sau khi tiêm đồng thời 6 dạng lỗi; phục hồi sau repair. |
| `mean_token_f1`      |   0.6933 |    0.6799 |   0.6933 | Giảm 0,0134 trong trạng thái corrupted; trở lại mức baseline sau repair. |
| `judge_accuracy`     |   0.7000 |    0.7000 |   0.7000 | Không đổi ở mức 7/10 câu. |
| `mean_judge_score`   |   3.4000 |    3.4000 |   3.4000 | Điểm đánh giá trung bình ổn định ở mức 3.4/5.0 |
| Quality checks         |   PASSED |   FAILED  |   PASSED | Dữ liệu corrupted vi phạm tính duy nhất của DOI và độ dài summary. |
| Freshness status       |    STALE |    STALE  |    STALE | Baseline đã có 21/24 bài quá 180 ngày; repair không làm mới ngày xuất bản. |

### Kết luận từ số liệu

Trên cùng bộ 10 câu hỏi, dữ liệu corrupted làm `retrieval_hit_rate` giảm từ **1,00 xuống 0,90** (mất 1 lượt tìm đúng tài liệu) và `mean_token_f1` giảm từ **0,6933 xuống 0,6799**. Quality gate chuyển từ **PASSED** sang **FAILED** vì DOI không còn duy nhất và có summary quá ngắn. Log ghi nhận cả sáu dạng lỗi được tiêm trong cùng lần chạy; việc bỏ 4 bài mới nhất có thể góp phần làm giảm hit rate, nhưng số liệu hiện tại không tách được tác động riêng của từng dạng lỗi. `judge_accuracy` vẫn **0,70** và `mean_judge_score` vẫn **3,40/5**, nên không thể kết luận mọi thước đo chất lượng câu trả lời đều suy giảm.

Sau khi repair từ dữ liệu raw, quality gate trở lại **PASSED**, hit rate phục hồi **1,00** và Token F1 trở lại **0,6933**, bằng baseline. Tuy nhiên, freshness **không phục hồi**: báo cáo baseline và repaired đều ghi **21/24** bài quá 180 ngày; corrupted là **22/22**. Điều này cho thấy repair đã khôi phục cấu trúc và hiệu năng đo được, nhưng không thể biến dữ liệu nguồn vốn cũ thành dữ liệu mới. Đây cũng là kết quả khác kỳ vọng nếu chỉ nhìn vào việc quality gate đã qua. Cần làm mới nguồn dữ liệu và chạy lại Freshness SLA để xử lý phần còn lại.

Các nhận định trên đối chiếu từ `data/results/{baseline,corrupted,repaired}_metrics.json`, `data/quality/*_quality_report.json`, các báo cáo freshness và `data/results/corruption_log.json`. Để xác định lỗi nào gây suy giảm mạnh nhất, cần chạy riêng từng kịch bản corruption trên cùng test set.

## 9. Điều học được và hướng cải thiện

1. Lưu raw response riêng với records đã parse giúp truy vết và chạy lại cleaning khi quy tắc biến đổi thay đổi.
2. Khử trùng lặp DOI và chuẩn hóa ngày trước khi index giúp mỗi tài liệu có định danh ổn định và hỗ trợ phép đo tuổi dữ liệu.
3. Dữ liệu đã sạch theo schema chưa chứng minh chất lượng câu trả lời RAG; vẫn cần quality gate và đánh giá trên test set cố định.

Nếu có thêm thời gian, tôi sẽ bổ sung báo cáo số item bị parser loại theo từng lý do (thiếu DOI/title/abstract/ngày), rồi đối chiếu số item nguồn với số records hợp lệ và số dòng sau cleaning. Cách này giúp phát hiện thay đổi chất lượng metadata từ Crossref mà chỉ số 24 dòng hiện tại chưa giải thích được.

## 10. Cam kết và xác nhận

- [x] Các kết quả định lượng trong báo cáo có thể đối chiếu với raw/clean artifacts hiện có.
- [x] Báo cáo phân biệt rõ phần đã kiểm tra với các bước chưa chạy.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Nội dung được viết cho phạm vi ingestion/cleaning, không sao chép báo cáo nhóm.
- [x] Chủ báo cáo xác nhận vai trò, mức đóng góp cá nhân và khả năng giải thích luồng end-to-end trước khi nộp.

**Họ và tên:** Nguyễn Gia Khánh  
**Ngày lập:** 2026-09-26  
