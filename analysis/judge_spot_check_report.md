# Judge Spot-Check Report

## 1. Objective
Verify that LLM Judge decisions are reliable and not systematically over/under-scoring.

## 2. Inputs and Method
- Source result file: `reports/benchmark_results.json`
- Evaluated split: V2 (latest candidate)
- Spot-check size: 12 cases
- Mix:
  - 6 fail cases with low score
  - 4 pass cases with high score
  - 2 conflict cases (`judge.status = conflict`)
- Manual rubric used:
  - Accuracy 40%
  - Completeness 30%
  - No hallucination 30%

## 3. Spot-Check Table
| Case (short) | Judge final | Judge status | Manual verdict | Alignment |
|---|---:|---|---|---|
| P1 22:47 notify + escalation | 5.0 | consensus | Correct & complete | Match |
| P1 no response after 10 mins | 5.0 | consensus | Correct behavior | Match |
| Flash Sale refund (manufacturer defect) | 1.0 | consensus | Wrong policy application | Match |
| Store credit percentage | 1.0 | consensus | Missing 110% fact | Match |
| L3 approval chain | 1.0 | consensus | Missing key approvers | Match |
| ERR-403-AUTH handling | 1.5 | consensus | Partially correct, incomplete action | Match |
| HR probation remote | 5.0 | consensus | Correct denial + condition | Match |
| P2 response at 10:00 | 5.0 | consensus | Correct at 12:00 | Match |
| P1 process 5 steps | 5.0 | consensus | Correct structure | Match |
| Employee security violation penalty | 4.5 | consensus | Correct abstain + escalation advice | Match |
| P1 auto action (partial answer) | 1.0 | conflict | Under-specified, low score justified | Match (strict) |
| Level 2 emergency dual workflow | 1.0 | conflict | Generic answer, misses required specifics | Match (strict) |

## 4. Results
- Exact alignment with manual verdict: 10/12 (83.3%)
- Acceptable band alignment (difference <= 1 score): 12/12 (100%)
- Conflict cases reviewed: 2/2, both acceptable with conservative final selection

## 5. Risks Observed
1. Lenient judge occasionally over-credits generic but non-grounded answers.
2. Some abstain-style answers are scored differently depending on whether expected answer itself is "unknown".

## 6. Recommendations
- Keep conservative conflict rule (`min(score_a, score_b)`) for release decisions.
- Add explicit hallucination penalty phrase in strict judge prompt for generic procedural text.
- Repeat spot-check after each major prompt or retrieval change.
