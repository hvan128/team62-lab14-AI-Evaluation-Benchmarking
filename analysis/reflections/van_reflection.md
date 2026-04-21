# Reflection cá nhân — Ngô Hải Văn

**Vai trò:** Merge Manager / Project Lead  
**Lab:** Lab 14 — AI Evaluation & Benchmarking  
**Ngày:** 2026-04-21

---

## 1. Tôi đã làm gì trong lab này?

Tôi đảm nhận vai trò **Merge Manager** — không implement một component cụ thể mà chịu trách nhiệm toàn bộ vòng đời tích hợp của nhóm:

- **Thiết kế skeleton & phân công việc**: Viết interface contract cho từng module (agent, judge, runner, evaluator, data), chia task cho 4 thành viên còn lại để không có dependency conflict.
- **Review & merge 4 PR**: Đọc code từng PR (Sang, Khiêm, Vương, Dũng), phát hiện lỗi logic và conflict trước khi merge vào `main`.
- **Fix conflict trực tiếp trên branch**: Thay vì yêu cầu teammate sửa, tôi tự checkout branch của họ, resolve conflict, và force-push để tiết kiệm thời gian.
- **Debug pipeline end-to-end**: Sau khi merge xong, chạy `python3 main.py` và debug toàn bộ chuỗi lỗi từ ChromaDB → embedding → judge → output format.
- **Chuẩn hoá output**: Điều chỉnh `benchmark_results.json` khớp với schema example (`{"v1": [], "v2": []}`, `latency` thay `latency_ms`, `individual_results` key by model name, `status` field, retry khi score=0).

---

## 2. Thách thức lớn nhất

### Embedding dimension mismatch (1536 vs 384)
ChromaDB collection `rag_lab` được tạo với OpenAI ada-002 (1536 dim), nhưng agent ban đầu dùng `query_texts` — ChromaDB tự embed bằng default model (384 dim) → dimension mismatch exception.

**Giải pháp:** Thêm `_embed()` async helper gọi OpenAI ada-002, dùng `query_embeddings` thay `query_texts`. Đây là bài học quan trọng: khi dùng lại ChromaDB từ lab khác, phải biết chính xác embedding model nào đã tạo collection.

### V2 < V1 do filter quá chặt
V2 có filter `distance < 0.5` nhưng tất cả chunks đều có distance > 0.5 → trả về empty context → LLM trả lời "không có thông tin" → điểm thấp hơn V1 (no-RAG). Phản trực giác nhưng đúng: một RAG tệ còn tệ hơn không có RAG.

**Giải pháp:** Bỏ filter, lấy top-5 không điều kiện. Đồng thời redesign V1 thành intentional no-RAG baseline để tạo contrast có ý nghĩa.

### PR #3 (Vương) vô tình revert code của Sang
Vương branch từ commit cũ (trước khi Sang merge), nên PR của Vương xóa mất `data/synthetic_gen.py`. Phải dùng `git checkout origin/main -- data/synthetic_gen.py` trên branch của Vương trước khi merge.

---

## 3. Điều tôi học được

**Về kỹ thuật:**
- RAG evaluation phức tạp hơn tôi nghĩ: Hit Rate, MRR chỉ đo retrieval; LLM-Judge mới đo generation quality — hai tầng hoàn toàn độc lập.
- Multi-judge với conflict resolution (average khi |a-b|≤1, min khi conflict) là cách thực tế để giảm variance của LLM evaluation.
- Retry khi score=0 quan trọng hơn tôi nghĩ — API timeout/parse error im lặng, không throw exception, nên phải check score explicitly.

**Về quản lý nhóm:**
- Interface contract viết trước giúp mỗi người code độc lập mà không cần chờ nhau — nhưng chỉ hiệu quả nếu contract đủ chi tiết (schema, type, edge case).
- Merge manager cần hiểu code của tất cả mọi người ở mức đủ để debug, không chỉ approve/reject.
- Git conflict dễ xảy ra khi nhiều người làm việc trên cùng file schema — nên lock interface sớm và tránh chỉnh sửa sau khi đã phân công.

---

## 4. Nếu làm lại, tôi sẽ làm gì khác?

1. **Pin embedding model ngay từ đầu** trong `.env.example` và README — tránh mismatch khi dùng lại ChromaDB.
2. **Yêu cầu mỗi PR có test script nhỏ** (`python3 -c "from engine.xxx import ..."`) chạy được trước khi mở PR — catch import error sớm hơn.
3. **Dùng `git rebase main` thay `git merge main`** khi branch bị cũ — lịch sử sạch hơn, ít conflict hơn.
4. **Chạy integration test sau mỗi PR merge** (không chỉ sau khi merge hết) — phát hiện regression sớm hơn.

---

## 5. Kết quả cuối cùng

| | V1 | V2 |
|--|--|--|
| avg_score | 1.95 / 5.0 | 2.15 / 5.0 |
| hit_rate | 0.0% | 100.0% |
| agreement_rate | — | ~90% |
| decision | — | **APPROVE RELEASE** ✅ |

Pipeline chạy ổn định, output đúng schema, checklist pass. Tổng chi phí API cho 110 lần chạy agent + judge: ~$0.01.
