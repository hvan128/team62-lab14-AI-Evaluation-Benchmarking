# Lab14 AI Evaluation Benchmarking

## Mục tiêu
Xây dựng hệ thống benchmark để chứng minh Version 2 tốt hơn Version 1 bằng số liệu cụ thể:
- Retrieval metrics
- Judge score metrics
- Quality/latency/cost trade-off
- Phân tích nguyên nhân lỗi và đề xuất cải tiến

## Luồng công việc tổng hợp (Checklist theo phase)

### PHASE 1 - DATASET

#### Bước 1: Chuẩn bị source data
- Thu thập hoặc xác nhận:
	- Tài liệu gốc
	- Knowledge base
	- Vector DB (nếu có)
	- Chunk text + chunk id
- Nếu đã có vector DB, cần có cách truy vết chunk để đánh giá retrieval.

#### Bước 2: Chuẩn hóa chunk
- Mỗi chunk cần có:
	- chunk_id
	- chunk_text
	- source_document
- Kiểm tra lại tính đầy đủ của metadata trước khi sinh dataset.

#### Bước 3: Thiết kế prompt sinh dataset
- Prompt sinh case phải bắt buộc trả về:
	- question
	- expected_answer
	- ground_truth_chunk_ids
	- difficulty
	- category
	- metadata cần thiết
- Cần có hướng dẫn hard case và ví dụ mẫu.

#### Bước 4: Tạo golden dataset
- Tạo tối thiểu 50 test cases.
- Bao gồm:
	- easy, medium, hard
	- multi-hop reasoning
	- retrieval dễ sai
	- case dễ hallucination

#### Bước 5: Manual review dataset (bắt buộc)
- Review tối thiểu một phần dataset bằng tay:
	- Câu hỏi có rõ ràng không
	- Expected answer có đúng policy không
	- Ground truth chunk ids có hợp lệ không
	- Source có khớp domain không
- Tài liệu cần có:
	- `analysis/manual_review_dataset.md`

### PHASE 2 - AGENT VERSIONING

#### Bước 6: Tạo Version 1 (baseline)
- Cấu hình retrieval/prompt cơ bản để làm mốc so sánh.

#### Bước 7: Tạo Version 2 (improved)
- Nâng cấp retrieval/prompt/logic để hướng tới:
	- Hit rate cao hơn
	- Judge score cao hơn
	- Chất lượng ổn định hơn

### PHASE 3 - TRUST / JUDGE

#### Bước 8: Multi-judge
- Dùng ít nhất 2 judge role/model.
- Có agreement rate và conflict handling.

#### Bước 9: Verify judge (bắt buộc)
- Spot-check bằng tay một tập case đại diện.
- Đối chiếu kết quả judge với đánh giá thủ công.
- Tài liệu cần có:
	- `analysis/judge_spot_check_report.md`

### PHASE 4 - BENCHMARK

#### Bước 10: Chạy benchmark cho V1
- Chạy toàn bộ dataset với agent V1.

#### Bước 11: Chạy benchmark cho V2
- Chạy cùng dataset với agent V2 để so sánh công bằng.

#### Bước 12: Tính metrics
- Tối thiểu:
	- Hit Rate, MRR
	- Faithfulness, Relevancy
	- Judge final score, agreement rate
	- Latency, Cost
- Kết quả được lưu tại:
	- `reports/summary.json`
	- `reports/benchmark_results.json`

### PHASE 5 - ANALYSIS

#### Bước 13: Failure analysis và root cause
- Phân tích không chỉ nêu V2 tốt hơn, mà phải nêu:
	- Tốt hơn ở đâu
	- Vì sao tốt hơn
	- Rủi ro còn lại
	- Action tiếp theo
- Tài liệu cần có:
	- `analysis/failure_analysis.md`

### PHASE 6 - REPORT

#### Bước 14: Final report package
- Gồm:
	- Executive summary
	- Benchmark comparison
	- Trust analysis
	- Risk analysis
	- Recommendation + Next action
- Reflection cá nhân mỗi thành viên:
	- `analysis/reflections/reflection_member_01.md`
	- `analysis/reflections/reflection_member_02.md`
	- `analysis/reflections/reflection_member_03.md`
	- `analysis/reflections/reflection_member_04.md`
	- `analysis/reflections/reflection_member_05.md`
	- `analysis/reflections/reflection_member_06.md`

## Cách chạy từ đầu đến cuối

```bash
# 1) Cài đặt phụ thuộc
pip install -r requirements.txt

# 2) Tạo lại golden dataset
python data/synthetic_gen.py

# 3) Chạy benchmark V1/V2 + release gate
python main.py

# 4) Kiểm tra cấu trúc nộp bài
python check_lab.py
```

## Kiểm tra trước khi nộp
- Đã có dataset >= 50 case trong `data/golden_set.jsonl`
- Đã có report benchmark mới nhất trong `reports/`
- Đã điền đầy đủ:
	- `analysis/manual_review_dataset.md`
	- `analysis/judge_spot_check_report.md`
	- `analysis/failure_analysis.md`
	- reflection cho từng thành viên trong `analysis/reflections/`

## Tính năng làm thêm ngoài GRADING_RUBRIC
- **Manual Dataset Review riêng:** có biên bản review thủ công dataset tại `analysis/manual_review_dataset.md`.
- **Judge Spot-check Report riêng:** có báo cáo đối chiếu Judge vs đánh giá thủ công tại `analysis/judge_spot_check_report.md`.
- **Faithfulness & Relevancy per-case:** ngoài Hit Rate/MRR và Judge score, mỗi test case còn có thêm 2 chỉ số chất lượng này trong `reports/benchmark_results.json`.
- **Position Bias check cho Judge:** có hàm kiểm tra bias do thứ tự đáp án trong `engine/llm_judge.py` (`check_position_bias`).
- **Model-level judge trace:** kết quả từng Judge được lưu theo tên model trong `judge.individual_results` thay vì chỉ lưu theo role.
- **Offline-friendly retrieval bootstrap:** tự động tạo/seed collection khi thiếu vector DB bằng deterministic embedding trong `engine/chroma_utils.py`.
- **Fallback judge khi thiếu API key:** vẫn chạy được chế độ đánh giá lexical fallback để pipeline không bị gãy khi thiếu key.
- **Release gate tự động:** quyết định APPROVE/BLOCK dựa trên delta chất lượng và hit-rate drop trong `main.py`.

## Lưu ý
- Không commit `.env` và secret key.
- Nếu thay đổi dataset hoặc prompt retrieval, phải chạy lại benchmark để cập nhật report.
