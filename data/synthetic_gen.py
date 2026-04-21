"""
Golden Dataset Generator — Phan Thanh Sang implement

Mục tiêu: tạo file data/golden_set.jsonl với ≥ 50 test cases.

Mỗi dòng JSONL phải có đúng schema sau (KHÔNG thêm / bỏ field):
{
    "id": "q01",
    "question": "...",
    "expected_answer": "...",
    "expected_sources": ["sla_p1_2026.txt"],      # tên file document
    "ground_truth_chunk_ids": ["chunk_abc123"],    # chunk_id từ ChromaDB — bắt buộc để tính Hit Rate
    "difficulty": "easy" | "medium" | "hard" | "adversarial",
    "category": "SLA" | "Refund" | "Access Control" | "HR" | "IT FAQ" | "Edge Case"
}

Nguồn data:
    - Lab 08: data/grading_questions.json (10 câu) + data/test_questions.json (10 câu)
    - Lab 09: data/test_questions.json (15 câu)
    → Tổng 35 câu có sẵn, cần sinh thêm ≥ 15 câu adversarial/edge-case bằng LLM

Cách lấy chunk_id từ ChromaDB:
    collection.query(query_texts=[question], n_results=1)["ids"][0][0]
    → Dùng kết quả này làm ground_truth_chunk_ids cho câu hỏi đó

Adversarial cases cần có (≥ 5 loại):
    - Câu hỏi mâu thuẫn với document (agent phải nói "không có thông tin")
    - Câu hỏi cross-document (cần combine 2 tài liệu)
    - Câu hỏi có thông tin bẫy (số liệu sai trong câu hỏi)
    - Câu hỏi ngoài phạm vi hoàn toàn
    - Câu hỏi yêu cầu reasoning (không lookup thẳng được)
"""

import asyncio
import json
import os
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

LAB08_PATH = "../team62-lecture-Day-08-09-10/day08/lab"
LAB09_PATH = "../team62-lecture-Day-08-09-10/day09/lab"
OUTPUT_PATH = "data/golden_set.jsonl"


def load_existing_questions() -> List[Dict]:
    """Load 35 câu từ lab 08 và lab 09, chuẩn hoá về schema mới."""
    cases = []

    # Lab 08 - grading_questions.json
    path = os.path.join(LAB08_PATH, "data/grading_questions.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for item in json.load(f):
                cases.append({
                    "id": f"lab08_gq_{item['id']}",
                    "question": item["question"],
                    "expected_answer": item["expected_answer"],
                    "expected_sources": item.get("expected_sources", []),
                    "ground_truth_chunk_ids": [],   # TODO (Sang): điền từ ChromaDB
                    "difficulty": item.get("difficulty", "medium"),
                    "category": item.get("category", "General"),
                })

    # Lab 08 - test_questions.json
    path = os.path.join(LAB08_PATH, "data/test_questions.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for item in json.load(f):
                cases.append({
                    "id": f"lab08_tq_{item['id']}",
                    "question": item["question"],
                    "expected_answer": item["expected_answer"],
                    "expected_sources": item.get("expected_sources", []),
                    "ground_truth_chunk_ids": [],   # TODO (Sang): điền từ ChromaDB
                    "difficulty": item.get("difficulty", "medium"),
                    "category": item.get("category", "General"),
                })

    # Lab 09 - test_questions.json
    path = os.path.join(LAB09_PATH, "data/test_questions.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for item in json.load(f):
                cases.append({
                    "id": f"lab09_tq_{item['id']}",
                    "question": item["question"],
                    "expected_answer": item["expected_answer"],
                    "expected_sources": item.get("expected_sources", []),
                    "ground_truth_chunk_ids": [],   # TODO (Sang): điền từ ChromaDB
                    "difficulty": item.get("difficulty", "medium"),
                    "category": item.get("category", "General"),
                })

    return cases


async def generate_adversarial_cases(num: int = 15) -> List[Dict]:
    """
    Dùng LLM API sinh thêm câu hỏi adversarial/edge-case.

    TODO (Sang): implement bằng cách gọi OpenAI với prompt yêu cầu sinh
    các câu hỏi khó, mâu thuẫn, cross-document từ nội dung 5 tài liệu lab 08.
    """
    # TODO (Sang): implement
    # Gợi ý prompt:
    #   "Dựa trên 5 tài liệu sau: [nội dung], hãy tạo {num} câu hỏi adversarial
    #    bao gồm: câu hỏi mâu thuẫn, câu hỏi ngoài phạm vi, câu hỏi cross-document.
    #    Trả về JSON array với schema: [{id, question, expected_answer, expected_sources,
    #    ground_truth_chunk_ids, difficulty, category}]"
    raise NotImplementedError("Sang implement generate_adversarial_cases()")


async def main():
    existing = load_existing_questions()
    print(f"Loaded {len(existing)} questions from lab 08/09")

    adversarial = await generate_adversarial_cases(num=max(15, 50 - len(existing)))
    all_cases = existing + adversarial

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for case in all_cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"Done! Saved {len(all_cases)} cases to {OUTPUT_PATH}")
    assert len(all_cases) >= 50, f"Cần ≥50 cases, hiện có {len(all_cases)}"


if __name__ == "__main__":
    asyncio.run(main())
