# Final Failure Analysis Report

## Executive Summary
- Mục tiêu benchmark: chứng minh V2 tốt hơn V1 trên cùng dataset.
- Kết quả tổng quát: **V2 đạt hiệu năng tốt hơn V1** về chất lượng trả lời và retrieval.
- Quyết định release hiện tại: **APPROVE** (theo `reports/summary.json`).

## 1. Benchmark Overview
### V1
- Total cases: 55
- Pass/Fail: 8 / 47 (Pass rate 14.55%)
- Avg Judge score: 1.7909 / 5.0
- Retrieval: Hit Rate 0.1273, MRR 0.1091
- RAG metrics: Faithfulness 0.3902, Relevancy 0.4411
- Agreement rate: 0.9818, conflicts: 5
- Avg latency: 2.478s

### V2
- Total cases: 55
- Pass/Fail: 15 / 40 (Pass rate 27.27%)
- Avg Judge score: 2.2818 / 5.0
- Retrieval: Hit Rate 0.3091, MRR 0.1824
- RAG metrics: Faithfulness 0.5999, Relevancy 0.4321
- Agreement rate: 0.9818, conflicts: 2
- Avg latency: 2.695s

### Delta (V2 - V1)
- Avg score: +0.4909
- Hit Rate: +0.1818
- MRR: +0.0733
- Faithfulness: +0.2097
- Latency: +0.217s (tăng nhẹ)

## 2. Failure Clustering (V2)
| Failure cluster | Approx count | Observation |
|---|---:|---|
| Missing key fact in known domain | 16 | Trả lời "không có thông tin" dù knowledge có dữ liệu |
| Policy exception confusion | 9 | Sai ở câu có ngoại lệ (Flash Sale, temporal policy version) |
| Multi-hop workflow degradation | 7 | Câu cross-policy dài dễ trả lời chung chung |
| Access-control precision errors | 5 | Nhầm điều kiện L2/L3, bỏ sót approver |
| Numeric/detail mismatch | 3 | Sai số liệu cụ thể (ví dụ 110%, timeline) |

## 3. 5 Whys (Top 3 representative failures)

### Case A: Flash Sale + manufacturer defect refund
1. Symptom: Agent kết luận có thể hoàn tiền, trái policy.
2. Why: Agent ưu tiên rule chung "lỗi nhà sản xuất" hơn exception "Flash Sale no refund".
3. Why: Retrieval top chunks chưa đủ mạnh cho điều khoản ngoại lệ.
4. Why: Query expansion/reranking chưa ưu tiên "exception clause".
5. Why: Prompt trả lời chưa ép kiểm tra điều khoản loại trừ trước khi kết luận.
6. Root cause: Pipeline thiếu bước "exception-first reasoning" ở refund domain.

### Case B: Level 3 temporary access during P1
1. Symptom: Agent trả lời thiếu/nhầm quy trình approval.
2. Why: Agent pha trộn logic Level 2 emergency bypass vào Level 3.
3. Why: Cả hai policy xuất hiện gần nhau trong context và không có disambiguation step.
4. Why: Retriever chưa dùng metadata filter theo access level.
5. Why: Prompt chưa yêu cầu trích điều kiện bắt buộc theo từng level trước khi trả lời.
6. Root cause: Thiếu ràng buộc phân biệt rule theo entity (`Level 2` vs `Level 3`).

### Case C: Generic abstain on known SLA fact
1. Symptom: Agent trả lời "không có thông tin" cho câu SLA có đáp án trong KB.
2. Why: Retrieved chunks không chứa đúng đoạn chứa fact chính.
3. Why: Vector seed hiện tại còn mỏng, coverage chưa tương đương production corpus.
4. Why: Chunk source mapping chưa được kiểm định thủ công đủ rộng.
5. Why: Dataset có một số câu hard nhưng ground-truth chunk chưa tối ưu.
6. Root cause: Chất lượng retrieval grounding chưa ổn định trên toàn domain.

## 4. Trust Analysis
- Multi-judge hoạt động ổn định: agreement rate cao (0.9818), số conflict thấp ở V2 (2/55).
- Spot-check judge thủ công cho thấy judge đủ tin cậy khi dùng rule bảo thủ cho conflict.
- Rủi ro còn lại: lenient judge có xu hướng cộng điểm cho câu trả lời chung chung.

## 5. Risk Analysis
1. Retrieval risk: hit-rate dù tăng nhưng vẫn thấp (0.3091), có thể gây false fail ở QA policy.
2. Policy risk: câu hỏi có ngoại lệ và mốc thời gian còn dễ sai.
3. Cost/latency risk: V2 tăng latency ~0.217s/case; hiện chấp nhận được.
4. Evaluation risk: chưa có hallucination-rate metric chính thức (mới dùng proxy theo low score).

## 6. Recommendation
1. Thêm metadata-aware retrieval/filter theo domain (`refund`, `access`, `sla`).
2. Bổ sung reranking ưu tiên chunk có `exception`, `override`, `effective_date`.
3. Cập nhật answer prompt theo flow: facts -> exceptions -> final conclusion.
4. Chuẩn hóa manual review cho ground-truth chunk IDs trước mỗi lần benchmark lớn.
5. Bổ sung metric hallucination rate và user satisfaction cho phase tiếp theo.

## 7. Next Actions
- [x] Hoàn tất manual fix cho các case dataset bị đánh dấu major/minor.
- [x] Chạy lại benchmark sau khi cập nhật retrieval/reranking.
- [x] Đánh giá lại bằng judge spot-check 10-15 case sau mỗi iteration.
- [x] Chốt báo cáo submission với bảng so sánh V1 vs V2 cập nhật.
