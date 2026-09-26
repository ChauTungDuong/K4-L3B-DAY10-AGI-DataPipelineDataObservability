# Báo cáo cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Nguyễn Đình Tuấn Anh |
| MSSV | 2A202602735 |
| Khóa/Lớp | K4 / L3B |
| Tên nhóm | AGI |
| Vai trò chính | Observability Gate & Evaluation Owner |
| Repository | https://github.com/ChauTungDuong/K4-L3B-DAY10-AGI-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc phụ trách

| Module/deliverable | File/hàm phụ trách | Input | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Chốt kiểm dịch dữ liệu (Quality Gate) | `src/observability/quality.py` (`run_data_quality_checks`, `build_freshness_report`) | DataFrame đã làm sạch | Báo cáo JSON kiểm định Great Expectations và SLA Freshness | Hoàn thành |
| Xây dựng Test Set | `src/evaluation/testset.py` (`build_test_set`) | DataFrame đã làm sạch | Bộ đề test (10 câu hỏi) dạng JSON | Hoàn thành |
| Xuất báo cáo Markdown | `src/observability/reporting.py` (`generate_phase1_report`, `generate_corruption_report`) | Metrics, source summary, quality dicts | Báo cáo `phase1_report.md` và `corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Xây dựng kịch bản Test RAG đa dạng | Đánh giá mô hình LLM | Hỗ trợ nhóm thiết kế các template câu hỏi (summary, authors, date, categories) để kiểm thử toàn diện năng lực trích xuất của hệ thống. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Cấu hình 4 quy tắc kiểm định Great Expectations | `run_data_quality_checks` | Báo cáo `{report_name}_quality_report.json` với trường `success: true/false` | Chạy lệnh kiểm thử đơn vị hoặc quan sát đầu ra pipeline phase 1 |
| Tạo ra bộ 10 câu hỏi đánh giá Ground Truth | `build_test_set` | File `data/eval/test_set.json` (10 câu hỏi 4 nhóm) | Mở file JSON để kiểm tra tính toàn vẹn của Ground Truth |
| Tổng hợp Markdown tự động | `generate_phase1_report`, `generate_corruption_report` | `phase1_report.md` và `corruption_report.md` | Đọc bảng Markdown để so sánh 3 trạng thái baseline, corrupted, repaired |

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Hệ thống AI không tự nhận biết được khi nào dữ liệu đầu vào bị hỏng. Khi có dữ liệu bẩn (rỗng, trùng lặp, mất thông tin) lọt vào Vector DB, câu trả lời sinh ra sẽ bị sai lệch. Hơn nữa, việc đánh giá độ chính xác RAG cần một bộ ground-truth đáng tin cậy. 

### Cách triển khai
- **Quality Gate:** Sử dụng `great_expectations` ở chế độ Ephemeral (trong bộ nhớ). Định nghĩa 4 Expectations (Số dòng 5-5000, không Null, duy nhất theo `paper_id`, độ dài summary >= 30). Tính tỷ lệ lỗi thời (stale rows > 180 ngày) để xác định xem pipeline có pass ngưỡng 25% SLA hay không.
- **Evaluation Test Set:** Tạo logic lấy mẫu 10 bài báo ngẫu nhiên, sinh ra 4 nhóm câu hỏi (Hỏi tóm tắt, hỏi tác giả, hỏi ngày xuất bản, hỏi chuyên mục). Thiết lập câu trả lời chuẩn (Ground Truth) để mô hình so sánh Token F1 ở bước sau.
- **Báo cáo Markdown:** Lấy input là các dictionaries của metrics và quality, format thành chuỗi MarkDown chuẩn có các bảng phân chia rõ ràng 3 trạng thái.

### Input, output và contract
- **Input:** DataFrame (`df`), các `Settings`.
- **Output:** File JSON của Great Expectations, Testset JSON, Báo cáo MarkDown sinh tự động.

### Cách xác minh
Chạy các dòng lệnh kiểm thử độc lập cho module. Ví dụ lệnh in ra `Tín hiệu hoàn thành: Sinh được 10 câu hỏi test` và `Tín hiệu hoàn thành: Quality check status = True` để xác nhận module hoàn thành hợp đồng dữ liệu.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Quyết định cách sinh câu hỏi Ground Truth từ dữ liệu tĩnh. Nếu hỏi quá dễ (chỉ hỏi tiêu đề), mô hình sẽ qua bài test quá dễ dàng và không phản ánh được sự giảm sút khi dữ liệu bị Corrupted.
- **Phương án đã chọn:** Chọn đa dạng 4 dạng câu hỏi: *summary* (để kiểm tra độ dài và ngữ cảnh), *authors* (kiểm tra entity), *date* (kiểm tra con số), *categories* (kiểm tra phân loại). Lấy câu đầu tiên của abstract làm Ground Truth cho câu hỏi Summary.
- **Lý do:** Điều này giúp khi Thành viên 3 thực hiện cắt độ dài văn bản hoặc tiêm lỗi `stale_date`, điểm Token F1 và Hit Rate sẽ phản ứng tức thì và chân thực nhất. Bằng chứng là `retrieval_hit_rate` giảm rõ rệt từ 1.0000 xuống 0.9000 trên tập Corrupted.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng:** Khi chạy Great Expectations (phiên bản 1.x mới), việc khai báo Batch Definition gặp khó khăn vì khác hoàn toàn với tài liệu cũ bản 0.x.
- **Cách xử lý:** Tham khảo kỹ tài liệu API v1 của GE. Áp dụng chuẩn `Ephemeral Context`: tạo `data_source` qua `context.data_sources.add_pandas`, tạo `dataframe_asset`, rồi dùng `batch_def.get_batch()` truyền dataframe trực tiếp qua tham số bộ nhớ thay vì đọc lại từ đĩa.
- **Điều học được:** Việc bám sát các bản cập nhật thư viện (như GX 1.x) rất quan trọng để không bị sử dụng API lỗi thời (Deprecated API).

## 7. Hiểu biết về luồng end-to-end

1. Dữ liệu từ Crossref cào về (Thành viên 1) được đẩy trực tiếp vào module Quality Gate của tôi. Nếu Pass, dữ liệu tiếp tục được index vào ChromaDB.
2. Bộ câu hỏi Test do tôi thiết kế sẽ được lưu sẵn ra đĩa. Ở cuối Pipeline, module Retrieval sẽ gọi lại bộ đề này, thực hiện RAG tìm kiếm và so sánh câu trả lời sinh ra với đáp án Ground Truth.
3. Khi Thành viên 3 thực hiện tiêm lỗi (Corruption), toàn bộ pipeline chạy lại. Module Quality của tôi lúc này bắt chính xác được các vi phạm (độ dài summary ngắn, paper_id trùng lặp) và báo FAILED, giúp ngăn chặn lỗi đi xa hơn. Sau đó module báo cáo Markdown ghi nhận lại lịch sử phục hồi (Repaired).

## 8. Phân tích kết quả

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | --------------------- |
| `retrieval_hit_rate` |   1.0000 |    0.9000 |   1.0000 | Phản ánh đúng việc mất ngữ cảnh tài liệu mục tiêu |
| `mean_token_f1`      |   0.6933 |    0.6799 |   0.6933 | Giảm do nhiễu và phục hồi thành công |
| Quality checks         |   PASSED |   FAILED  |   PASSED | Lớp khiên GE 1.x vận hành chính xác 100% |
| Freshness status       |    STALE |    STALE  |    STALE | Bắt đúng SLA do bài báo gốc đa phần là báo cũ >180 ngày |

## 9. Điều học được và hướng cải thiện

1. **Tầm quan trọng của Data Observability:** Great Expectations đóng vai trò như một bộ "khiên chặn lỗi" không thể thiếu trong luồng dữ liệu thực tế. Nhờ vậy mới chặn đứng được Silent Failures (ảo giác của LLM do dữ liệu bẩn).
2. **Evaluation Set là cốt lõi:** Bộ đề đánh giá tốt quyết định tính khả tín của việc đánh giá mô hình. 
3. Nếu có thêm thời gian, tôi sẽ bổ sung thêm các thư viện LLM-as-a-judge vào module sinh test set để sinh ra các câu hỏi dạng suy luận (reasoning) phức tạp hơn là trích xuất thông tin tĩnh.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Đình Tuấn Anh  
**Ngày xác nhận:** 2026-09-26
