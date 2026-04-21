# Báo Cáo Reflection Cá Nhân - Ngô Hải Văn - 2A202600386

**Vai trò trong nhóm:** Merge Manager / Project Coordinator (Thành viên #5)

---

## 1) Đóng góp kỹ thuật (Engineering Contribution)

### Các module tôi phụ trách:

**`main.py` (skeleton & interface contracts)**
- Thiết kế skeleton ban đầu cho toàn bộ pipeline: định nghĩa typed interfaces (docstrings + TODO markers) cho từng module để các thành viên khác có thể phát triển song song mà không xung đột.
- Định nghĩa `RELEASE_GATE` thresholds và logic `APPROVE/BLOCK` trong `main.py` trước khi Dũng implement chi tiết.

**`check_lab.py`**
- Viết toàn bộ script kiểm tra tự động, bao gồm:
  - Kiểm tra sự tồn tại của tất cả file bắt buộc (`summary.json`, `benchmark_results.json`, `failure_analysis.md`).
  - Xác nhận `summary.json` có đủ `hit_rate`, `mrr`, `agreement_rate`, `regression` block.
  - In cảnh báo EXPERT-level nếu thiếu Retrieval Metrics (nguy cơ bị điểm liệt theo rubric).

**`analysis/failure_analysis.md`**
- Viết báo cáo phân tích thất bại hoàn chỉnh sau khi benchmark chạy xong, bao gồm:
  - So sánh V1 vs V2 trên toàn bộ metrics (score, hit rate, MRR, faithfulness).
  - Phân cụm 5 failure clusters và đếm case cho V2.
  - Phân tích 5 Whys cho 3 failure case đại diện.
  - Trust analysis cho multi-judge pipeline.
  - Risk analysis và recommendations.

**`.env.example` & `requirements.txt`**
- Tạo `.env.example` đầy đủ (OpenAI key, model IDs, ChromaDB config) để các thành viên setup môi trường thống nhất.
- Duy trì `requirements.txt` up-to-date qua các lần merge.

**Toàn repo — Merge Manager**
- Review và merge 4 PRs của các thành viên:
  - PR #1 (Khiêm): `feat(Khiem): implement MainAgent V1/V2 + RetrievalEvaluator`
  - PR #2 (Sang): Golden Dataset + adversarial cases
  - PR #3 (Vương): `feat(Vuong): implement multi-judge scoring engine with conflict resolution`
  - PR #4 (Dũng): `feat(Dung): implement BenchmarkRunner + release gate`
- Xử lý merge conflicts khi các module cùng sửa `main.py` và `engine/runner.py`.
- Đảm bảo repo không có file `.env` hay secret bị commit lên.

### Commit chính:
- `1e771e3` — `feat: Setup interface contracts and skeleton for all modules` (11 files changed, +574/-194)

---

## 2) Chiều sâu kỹ thuật (Technical Depth)

### MRR (Mean Reciprocal Rank):
MRR đo chất lượng xếp hạng của retrieval bằng cách nhìn vào vị trí tài liệu đúng **đầu tiên** trong danh sách kết quả trả về. Công thức: `MRR = mean(1 / rank_i)` với `rank_i` là vị trí tài liệu đúng của case `i`. Nếu tài liệu đúng ở vị trí 1 → điểm 1.0; vị trí 2 → 0.5; vị trí 3 → 0.333. Trong benchmark này, MRR V1 = 0.1091 → V2 = 0.1824, tăng +0.0733 cho thấy V2 đưa tài liệu đúng lên gần top hơn.

### Cohen's Kappa và Judge Consensus:
`agreement_rate` chỉ đo tỉ lệ giống nhau bề mặt, dễ cao giả tạo khi cả hai judge cùng thiên về một nhãn. Cohen's Kappa loại trừ phần đồng thuận xảy ra do ngẫu nhiên: `κ = (P_o - P_e) / (1 - P_e)`. Kappa gần 1 = nhất quán thật sự. Trong kết quả benchmark: agreement_rate = 0.9818 với chỉ 2 conflicts trên 55 cases (V2) → multi-judge pipeline ổn định.

### Position Bias:
Khi LLM-as-a-judge so sánh hai phương án A/B, nó có xu hướng ưu tiên phương án xuất hiện **trước** trong prompt dù nội dung tương đương. Cách kiểm tra: đảo thứ tự A/B, nếu điểm thay đổi lớn → bias cao. Hệ thống hiện tại dùng lenient judge + strict judge song song (không phụ thuộc thứ tự trình bày) để giảm thiểu rủi ro này.

### Trade-off Chi phí vs Chất lượng:
- Tăng `top_k` từ 2 (V1) lên 5 (V2) giúp hit rate tăng từ 12.73% → 30.91% nhưng tăng token consumption và latency trung bình +0.217s/case.
- Tổng chi phí benchmark 55 cases với 2 judge: ~$0.0048 (32,094 tokens) — rất hiệu quả nhờ pipeline async.
- Threshold release gate (`APPROVE` khi delta ≥ +0.3) là quyết định trade-off chất lượng/rủi ro deployment.

---

## 3) Giải quyết vấn đề (Problem Solving)

### Vấn đề 1: Interface mismatch giữa các module
Khi Khiêm và Vương phát triển song song, output schema của `agent/main_agent.py` không khớp với input mà `engine/llm_judge.py` mong đợi (field `retrieved_chunk_ids` bị thiếu). Tôi phát hiện qua code review và fix bằng cách chuẩn hóa schema trong skeleton commit trước khi các thành viên bắt đầu implement.

### Vấn đề 2: Merge conflict trên `main.py`
Dũng và Vương cùng sửa `main.py` trong hai PR khác nhau. Tôi resolve conflict bằng cách giữ lại cả hai contribution: phần `release_gate` của Dũng và phần `multi_judge summary` của Vương, đảm bảo flow `runner → judge → gate` không bị gián đoạn.

### Vấn đề 3: Repo bị expose `.env` trong một commit
Phát hiện file `.env` vô tình được stage trong một branch. Tôi yêu cầu rewrite commit trước khi merge và bổ sung `.env` vào `.gitignore` ngay từ skeleton commit để phòng tránh.

### Vấn đề 4: `check_lab.py` phải phản ánh rubric EXPERT
Rubric có điều kiện "điểm liệt" nếu thiếu Retrieval Metrics. Tôi mở rộng `check_lab.py` để cảnh báo rõ khi thiếu `hit_rate`/`mrr`, giúp nhóm phát hiện sớm thay vì chỉ biết khi nộp bài.

---

## 4) Bài học rút ra (Lessons Learned)

**Nếu làm phiên bản V2:**
- Định nghĩa JSON schema chính thức (Pydantic models) cho interface giữa các module ngay từ đầu, thay vì dùng docstring/comment.
- Tự động hóa kiểm tra schema trong CI để phát hiện mismatch sớm hơn.
- Thêm integration test nhỏ cho từng module trước khi merge PR.

**Trade-off quan trọng nhất tôi rút ra:**
Vai trò merge manager tưởng "ít code" nhưng thực ra quyết định kiến trúc nhiều nhất — skeleton và interface contract quyết định 80% khả năng các thành viên phát triển song song mà không block nhau. Đầu tư sớm vào interface design tiết kiệm nhiều thời gian debug và re-merge hơn.

---

## 5) Minh chứng (Evidence)

### Commit chính:
- `1e771e3` — `feat: Setup interface contracts and skeleton for all modules`
  - 11 files changed: +574 lines added, -194 lines removed
  - Files: `.env.example`, `.gitignore`, `agent/main_agent.py`, `analysis/reflections/.gitkeep`, `data/synthetic_gen.py`, `engine/llm_judge.py`, `engine/retrieval_eval.py`, `engine/runner.py`, `main.py`, `reports/.gitkeep`, `requirements.txt`

### Kết quả benchmark được phân tích trong `analysis/failure_analysis.md`:
| Metric | V1 | V2 | Delta |
|---|---|---|---|
| Avg Judge Score | 1.7909 | 2.2818 | +0.4909 |
| Hit Rate | 0.1273 | 0.3091 | +0.1818 |
| MRR | 0.1091 | 0.1824 | +0.0733 |
| Agreement Rate | 0.9818 | 0.9818 | 0 |
| Conflicts | 5 | 2 | -3 |
| Release Decision | — | **APPROVE** | — |

### Files tôi viết trực tiếp:
- `check_lab.py` — kiểm tra tự động toàn bộ submission
- `analysis/failure_analysis.md` — báo cáo 5 Whys và failure clustering
- `main.py` (skeleton) — interface + release gate thresholds
- `.env.example` — cấu hình môi trường chuẩn cho nhóm
