# Báo Cáo Reflection Cá Nhân - Trần Đình Minh Vương

## 1) Đóng góp kỹ thuật (Engineering Contribution)
- Module tôi tham gia:
    - `engine/llm_judge.py`: triển khai Multi-Judge Scoring Engine với 2 judge (nghiêm khắc và dễ chịu), xử lý conflict resolution, và kiểm tra position bias.
- Các commit kỹ thuật chính:
    - `feat(Vuong): implement multi-judge scoring engine with conflict resolution` (#3)
- Chi tiết implementation:
    - Gọi LLM 2 lần song song với 2 system prompt khác nhau:
        - `role_strict`: Judge nghiêm khắc, chỉ cho điểm cao khi câu trả lời chính xác 100%.
        - `role_lenient`: Judge cởi mở, chấp nhận câu trả lời nếu ý chính đúng.
    - Mỗi judge chấm theo thang 1-5 với 3 tiêu chí: accuracy (40%), completeness (30%), hallucination (30%).
    - Conflict resolution: nếu |score_a - score_b| <= 1 → lấy trung bình, agreement_rate = 1.0; ngược lại → lấy điểm thấp hơn, agreement_rate = 0.5.
    - Có kiểm tra position bias bằng cách đổi thứ tự A/B và so sánh điểm.

## 2) Chiều sâu kỹ thuật (Technical Depth)
- Giải thích Agreement Rate trong multi-judge system:
    - Agreement rate đo mức độ nhất quán giữa 2 judge. Nếu điểm lệch nhau không quá 1 (|score_a - score_b| <= 1), coi như đồng thuận và agreement_rate = 1.0.
    - Khi lệch lớn hơn 1, có conflict xảy ra → agreement_rate giảm xuống 0.5, final_score lấy điểm thấp hơn để an toàn.
    - Điều này đảm bảo hệ thống không quá lạc quan khi 2 judge không đồng thuận.
- Giải thích tại sao cần 2 judge thay vì 1:
    - Một judge duy nhất dễ bị thiên vị theo hướng đánh giá của model hoặc prompt.
    - 2 judge với tính cách khác nhau (nghiêm khắc vs dễ chịu) giúp phát hiện edge cases tốt hơn.
    - Khi cả 2 cùng đồng thuận → điểm đáng tin cậy cao.
- Position bias trong LLM-as-a-judge:
    - Khi so sánh 2 phương án, judge có xu hướng ưu tiên phương án xuất hiện trước.
    - Cách phát hiện: gọi evaluate 2 lần với thứ tự A-B và B-A, so sánh điểm.
    - Nếu |score_ab - score_ba| > 0.5 → có position bias, cần cảnh báo.

## 3) Giải quyết vấn đề (Problem Solving)
- Vấn đề gặp phải khi triển khai:
    - Parse JSON response từ LLM có thể fail nếu model trả về format không đúng.
    - Xử lý async parallel calls cho 2 judge cần đảm bảo error handling riêng.
- Cách xử lý:
    - Dùng `asyncio.gather()` để gọi 2 judge song song, tối ưu latency.
    - Wrap try-except quanh API call, trả về score mặc định = 3 nếu lỗi.
    - Dùng `response_format={"type": "json_object"}` để yêu cầu model trả JSON chuẩn.
- Trade-off thiết kế:
    - Chọn lấy min(score_a, score_b) khi conflict thay vì max → an toàn hơn, tránh điểm ảo.
    - agreement_rate = 0.5 khi conflict thay vì 0 → vẫn giữ một phần tin cậy.

## 4) Bài học rút ra (Lessons Learned)
- Nếu làm V2, cải tiến:
    - Thêm judge thứ 3 (neutral) để có voting mechanism 3-chiều.
    - Tính Cohen's Kappa thay vì chỉ agreement_rate đơn giản để đo đồng thuận chuẩn hóa theo xác suất ngẫu nhiên.
    - Cache judge responses để tránh gọi lại LLM khi cùng một question-answer được chấm nhiều lần.
- Bài học về LLM-as-a-judge:
    - Prompt engineering quyết định lớn đến độ tin cậy của judge. System prompt càng rõ ràng, điểm càng nhất quán.
    - Không nên tin tuyệt đối điểm số từ 1 lần gọi; cần multi-judge để giảm variance.

## 5) Minh chứng (Evidence)
- Commit liên quan: `b01a30f loversky02 - feat(Vuong): implement multi-judge scoring engine with conflict resolution (#3)`
- File chứng minh: `engine/llm_judge.py` (164 dòng)
- Kết quả chạy benchmark:
    - Agreement Rate đạt 97-99% trên 50 test cases
    - Multi-judge system hoạt động ổn định, không có case nào crash
