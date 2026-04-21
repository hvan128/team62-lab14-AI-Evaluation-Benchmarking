# Manual Review Dataset Report

## 1. Scope
- Dataset reviewed: `data/golden_set.jsonl`
- Total cases in dataset: 55
- Manual review mode: spot-check + schema consistency check
- Review date: 2026-04-21

## 2. Review Checklist
For each sampled case, reviewers validated:
- Question clarity and unambiguous intent
- Expected answer correctness against policy logic
- `ground_truth_chunk_ids` is present and mappable
- Difficulty/category labels are consistent
- Expected sources are coherent with domain

## 3. Sampling Plan
- Sample size: 20/55 cases (36.4%)
- Coverage:
  - Easy: 5
  - Medium: 8
  - Hard/Adversarial: 7
- Domain coverage:
  - SLA, Refund, Access Control, HR, IT FAQ, Edge Case

## 4. Review Outcome Summary
- Passed as-is: 16
- Minor fix suggested: 3
- Major fix required: 1

### Main issues found
1. Some `expected_sources` fields are empty while answer text is clearly policy-specific.
2. A few temporal-policy questions require stronger note about policy version boundary.
3. Some hard cases are too close to easy paraphrases and can be strengthened.

## 5. Sampled Cases and Decision Log
| ID | Topic | Decision | Notes |
|---|---|---|---|
| lab08_gq_gq01 | SLA escalation | Pass | Good time arithmetic + channel detail requirement |
| lab08_gq_gq02 | Refund temporal | Minor fix | Add explicit v3/v4 cutoff wording |
| lab08_gq_gq06 | HR remote policy | Pass | Clear deny + condition logic |
| lab08_gq_gq09 | Multi-hop SLA + Access | Pass | Good cross-document reasoning demand |
| lab08_gq_gq10 | Flash Sale exception | Pass | High-value anti-hallucination case |
| lab08_tq_q01 | SLA baseline | Pass | Good easy baseline |
| lab08_tq_q03 | Access L3 approvals | Pass | Correct triple-approval requirement |
| lab08_tq_q06 | P1 no-response path | Pass | Good operational behavior check |
| lab08_tq_q09 | Out-of-scope error code | Pass | Proper abstain behavior target |
| lab08_tq_q13 | Level 3 no bypass | Pass | Good contradiction trap |
| lab09_tq_q02 | Refund window | Minor fix | Add explicit business-day interpretation note |
| lab09_tq_q05 | HR remote quota | Pass | Good policy extraction |
| lab09_tq_q08 | P1 process steps | Pass | Strong structured answer target |
| lab09_tq_q11 | P1 at 22:47 | Pass | Strong timeline consistency check |
| lab09_tq_q12 | Refund versioning | Minor fix | Reinforce expected abstention/verification wording |
| adv_001 | Adversarial contradiction | Major fix | Chunk grounding too weak in current vector seed |
| adv_002 | Cross-document emergency | Pass | Good combined constraints |
| adv_005 | Out-of-scope enterprise policy | Pass | Good hallucination guard |
| adv_010 | Trap numeric policy | Pass | Useful for numeric precision |
| adv_015 | Multi-hop exception | Pass | Good stress case |

## 6. Action Items Before Final Submission
- [ ] Patch 1 major issue (`adv_001`) with stronger grounded expected source/chunk mapping.
- [ ] Add missing `expected_sources` for policy-bound questions where currently empty.
- [ ] Regenerate dataset and rerun benchmark after fixes.

## 7. Reviewer Sign-off Template
- Reviewer A: ____________________
- Reviewer B: ____________________
- Reviewer C: ____________________
