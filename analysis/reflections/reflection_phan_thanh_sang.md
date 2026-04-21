# Báo Cáo Reflection Cá Nhân - Phan Thanh Sang

## 1) Đóng góp kỹ thuật (Engineering Contribution)
- Các module tôi tham gia:
	- `data/synthetic_gen.py`: xây dựng bộ Golden Dataset 60 cases, có `expected_retrieval_ids` và nhóm hard cases (adversarial, out-of-context, conflicting-info).
	- `engine/retrieval_eval.py`: triển khai tính `Hit Rate`, `MRR`, và các chỉ số hỗ trợ chất lượng câu trả lời (`faithfulness`, `relevancy`).
	- `engine/llm_judge.py`: triển khai cơ chế multi-judge (2 judge), tính `agreement_rate`, `cohen_kappa`, và xử lý xung đột điểm số.
	- `engine/runner.py`: chạy benchmark bất đồng bộ theo batch, thu thập latency/token/cost theo từng test case.
	- `main.py`: tổng hợp kết quả V1 vs V2, tính delta, và áp dụng `release gate` tự động.
	- `check_lab.py`: mở rộng kiểm tra để xác nhận có MRR và khối regression/release gate.
- Các commit kỹ thuật chính và lý do thực hiện:
	- Hiện tại đang ở trạng thái thay đổi local chưa tách commit theo từng hạng mục. Kế hoạch commit trước khi nộp:
		- `feat(data): generate 60-case golden dataset with hard cases`
		- `feat(eval): add retrieval metrics (hit rate, mrr) and judge consensus`
		- `feat(regression): implement v1-v2 release gate and reporting`
		- `docs(analysis): complete failure analysis and personal reflection`
- Các quyết định triển khai quan trọng:
	- Chọn pipeline deterministic/offline để benchmark ổn định, không phụ thuộc API ngoài.
	- Tách rõ 3 lớp đánh giá: retrieval quality, answer quality, judge consensus.
	- Đưa ngưỡng chất lượng vào release gate để tự động hóa quyết định `APPROVE/ROLLBACK`.

## 2) Chiều sâu kỹ thuật (Technical Depth)
- Giải thích MRR theo cách hiểu của tôi:
	- MRR (Mean Reciprocal Rank) đo chất lượng xếp hạng retrieval bằng cách nhìn vị trí tài liệu đúng đầu tiên.
	- Nếu tài liệu đúng nằm ở vị trí 1 thì điểm là 1.0, vị trí 2 là 0.5, vị trí 3 là 0.333...
	- MRR trung bình càng cao thì tài liệu đúng càng xuất hiện sớm, giúp LLM có context tốt hơn để trả lời chính xác.
- Giải thích Cohen's Kappa trong bài toán đồng thuận giữa các Judge:
	- Agreement rate chỉ đo tỉ lệ giống nhau bề mặt; Cohen's Kappa đo mức đồng thuận sau khi loại trừ phần đồng thuận do ngẫu nhiên.
	- Kappa cao (tiệm cận 1) cho thấy hai judge nhất quán thật sự, giúp tăng độ tin cậy của quy trình chấm.
	- Trong benchmark hiện tại, Kappa cao thể hiện cơ chế multi-judge có tính ổn định.
- Giải thích rủi ro thiên vị vị trí (position bias) khi chấm bằng LLM:
	- Khi so sánh 2 phương án A/B, judge có thể ưu tiên phương án xuất hiện trước dù nội dung tương đương.
	- Cách giảm bias: đảo thứ tự A/B và đo chênh lệch điểm trước-sau; nếu chênh lớn thì cảnh báo bias.
	- Vì vậy cần bước kiểm tra position bias khi dùng LLM-as-a-judge trong môi trường thực tế.

## 3) Giải quyết vấn đề (Problem Solving)
- Vấn đề khó nhất tôi gặp phải:
	- Ban đầu hệ thống chỉ là placeholder, thiếu liên kết giữa dataset, retrieval metrics, judge consensus và regression gate.
- Phân tích nguyên nhân gốc rễ:
	- Thiếu cấu trúc dữ liệu thống nhất (`expected_retrieval_ids`, `retrieved_ids`) nên không thể tính retrieval metrics đúng nghĩa.
	- Thiếu chuẩn đầu ra giữa các module nên khó tổng hợp báo cáo để chấm điểm theo rubric.
- Cách tôi xử lý và vì sao cách này hiệu quả:
	- Chuẩn hóa schema test case và response từ agent.
	- Tách rõ luồng tính metric ở evaluator/judge rồi mới hợp nhất ở `main.py`.
	- Kết quả: benchmark chạy ổn định trên 60 cases, có đủ score retrieval + multi-judge + regression + cost/token.

## 4) Bài học rút ra (Lessons Learned)
- Nếu làm phiên bản V2, tôi sẽ cải tiến gì:
	- Thêm release gate theo từng nhóm lỗi (adversarial, multi-hop) thay vì chỉ gate theo trung bình toàn cục.
	- Bổ sung kiểm tra position bias tự động vào pipeline chính.
	- Thêm biểu đồ phân tích tương quan retrieval quality và answer quality để đọc nhanh hơn.
- Trade-off giữa chất lượng, độ trễ và chi phí:
	- Tăng số judge hoặc tăng top-k retrieval thường giúp chất lượng tăng nhưng sẽ tăng token/cost và latency.
	- Mục tiêu kỹ thuật là tối ưu điểm chất lượng trên mỗi đơn vị chi phí, không tối ưu một chiều.
	- Cần đặt ngưỡng release rõ ràng để tránh đánh đổi chất lượng lấy tốc độ quá mức.

## 5) Minh chứng (Evidence)
- Danh sách commit hash liên quan:
	- Sẽ bổ sung sau khi tách commit theo từng hạng mục kỹ thuật trước thời điểm nộp.
- Ảnh chụp màn hình hoặc phần báo cáo được tham chiếu:
	- `reports/summary.json`: có `hit_rate`, `mrr`, `agreement_rate`, `cohen_kappa`, `tokens_total`, `cost_usd_total`, `regression.release_gates`.
	- `reports/benchmark_results.json`: có kết quả chi tiết từng case cho cả V1 và V2.
	- `analysis/failure_analysis.md`: có phân cụm lỗi và phân tích 5 Whys cho các case xấu nhất.