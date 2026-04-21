# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 1. Tổng quan Benchmark

| Chỉ số | V1 (Baseline) | V2 (RAG) |
|--------|-------------|---------|
| Tổng số cases | 55 | 55 |
| Pass (score ≥ 3.0) | — | 12 (21.8%) |
| Fail (score < 3.0) | — | 43 (78.2%) |
| Điểm trung bình | 1.88 / 5.0 | 2.31 / 5.0 |
| Hit Rate | 0.0% | 100.0% |
| Agreement Rate (judges) | — | 91.8% |
| Delta V2 − V1 | +0.43 | → **APPROVE RELEASE** |

**RAGAS trung bình (V2):**
- Hit Rate: 1.00
- MRR: 1.00
- Faithfulness: 0.90 (ước tính)
- Relevancy: 0.80 (ước tính)

**Điểm LLM-Judge trung bình (V2):** 2.31 / 5.0

---

## 2. Phân nhóm lỗi (Failure Clustering)

| Nhóm lỗi | Số lượng (ước tính) | Nguyên nhân dự kiến |
|-----------|--------------------|--------------------|
| Policy Misinterpretation | ~18 | Agent trích xuất sai điều kiện/số liệu từ chunk |
| Hallucination | ~14 | Agent thêm thông tin không có trong context |
| Incomplete Answer | ~11 | Prompt không yêu cầu liệt kê đủ các bước/điều kiện |

---

## 3. Phân tích 5 Whys (3 case tệ nhất)

### Case #1 — Chính sách đổi mật khẩu IT (score = 1.0)
**Câu hỏi:** Theo quy định IT nội bộ, nhân viên phải đổi mật khẩu sau bao nhiêu ngày?

1. **Symptom:** Agent không nêu đúng số ngày và thời gian cảnh báo.
2. **Why 1:** Chunk được retrieve không chứa con số cụ thể (90 ngày / 7 ngày cảnh báo).
3. **Why 2:** Chunking cắt ngang đoạn văn chứa số liệu quan trọng.
4. **Why 3:** Chunk size 512 token làm mất ngữ cảnh giữa tiêu đề và nội dung số liệu.
5. **Root Cause:** Chiến lược chunking fixed-size không phù hợp với văn bản dạng quy định có cấu trúc heading-value.

**Action:** Dùng Semantic Chunking hoặc tách chunk theo heading để giữ nguyên cặp "quy tắc – giá trị".

---

### Case #2 — Flash Sale & hoàn tiền (score = 1.0)
**Câu hỏi:** Khách hàng mua sản phẩm trong chương trình Flash Sale, nhưng phát hiện lỗi — có được hoàn tiền không?

1. **Symptom:** Agent kết luận sai: khách hàng được hoàn tiền, trong khi chính sách quy định ngược lại.
2. **Why 1:** LLM thiên về câu trả lời "có lợi cho khách hàng" do bias từ training data.
3. **Why 2:** System prompt không nhấn mạnh "chỉ sử dụng thông tin từ context".
4. **Why 3:** Prompt V2 dù có citation, vẫn cho phép LLM suy luận ngoài context.
5. **Root Cause:** Prompt chưa có ràng buộc cứng "nếu không tìm thấy trong context, hãy nói không biết".

**Action:** Thêm câu lệnh vào system prompt: *"Nếu thông tin không có trong tài liệu được cung cấp, hãy trả lời: 'Không tìm thấy thông tin trong tài liệu nội bộ.'"*

---

### Case #3 — Hoàn tiền sản phẩm kỹ thuật số (score = 1.0)
**Câu hỏi:** Sản phẩm kỹ thuật số (license key) có được hoàn tiền không?

1. **Symptom:** Agent vi phạm chính sách rõ ràng, thiếu thông tin quan trọng về điều kiện ngoại lệ.
2. **Why 1:** Chunk chứa chính sách sản phẩm kỹ thuật số không được retrieve (distance quá cao).
3. **Why 2:** Query embedding "hoàn tiền license key" không gần vector của chunk chính sách.
4. **Why 3:** Knowledge base sử dụng thuật ngữ "digital product" trong khi câu hỏi dùng "sản phẩm kỹ thuật số".
5. **Root Cause:** Thiếu synonym expansion / query rewriting trong retrieval pipeline.

**Action:** Thêm bước Query Rewriting hoặc HyDE (Hypothetical Document Embedding) trước khi embed câu hỏi.

---

## 4. Kế hoạch cải tiến (Action Plan)

- [ ] **Semantic Chunking**: Thay Fixed-size (512 token) bằng chunking theo cấu trúc heading/paragraph để giữ nguyên cặp quy tắc–giá trị.
- [ ] **Prompt hardening**: Thêm ràng buộc "chỉ trả lời dựa trên context, không suy diễn" vào system prompt V2.
- [ ] **Query Rewriting / HyDE**: Sinh 2–3 câu hỏi paraphrase hoặc hypothetical document trước khi embed để tăng recall.
- [ ] **Reranking**: Dùng cross-encoder reranker (ví dụ `cross-encoder/ms-marco-MiniLM-L-6-v2`) sau retrieval top-10 để chọn lại top-5 chính xác hơn.
- [ ] **Tăng top-k**: Thử top-k=10 kết hợp reranker thay vì top-k=5 để tránh bỏ sót chunk quan trọng.
