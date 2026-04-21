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

from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

LAB08_PATH = "../team62-lecture-Day-08-09-10/day08/lab"
LAB09_PATH = "../team62-lecture-Day-08-09-10/day09/lab"
OUTPUT_PATH = "data/golden_set.jsonl"

# ChromaDB client để lấy chunk_id
_chroma_client = None


def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        chroma_path = os.getenv("CHROMA_DB_PATH", "data/chroma_db")
        _chroma_client = chromadb.PersistentClient(path=chroma_path)
    return _chroma_client


def _get_collection():
    """Lấy ChromaDB collection, trả về None nếu không có."""
    try:
        client = _get_chroma_client()
        coll_name = os.getenv("CHROMA_COLLECTION_NAME", "rag_documents")
        try:
            return client.get_collection(name=coll_name)
        except Exception:
            # Thử lấy collection đầu tiên
            try:
                colls = client.list_collections()
                if colls:
                    return client.get_collection(name=colls[0].name)
            except Exception:
                pass
            return None
    except Exception:
        return None


def _get_chunk_id(question: str) -> List[str]:
    """Query ChromaDB để lấy ground_truth_chunk_ids cho câu hỏi."""
    try:
        coll = _get_collection()
        if coll is None:
            return []
        result = coll.query(query_texts=[question], n_results=1)
        ids = result.get("ids", [[]])[0]
        return ids if ids else []
    except Exception:
        return []


def load_existing_questions() -> List[Dict]:
    """Load 35 câu từ lab 08 và lab 09, chuẩn hoá về schema mới."""
    cases = []

    # Lab 08 - grading_questions.json
    path = os.path.join(LAB08_PATH, "data/grading_questions.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for item in json.load(f):
                chunk_ids = _get_chunk_id(item["question"])
                cases.append({
                    "id": f"lab08_gq_{item['id']}",
                    "question": item["question"],
                    "expected_answer": item["expected_answer"],
                    "expected_sources": item.get("expected_sources", []),
                    "ground_truth_chunk_ids": chunk_ids,
                    "difficulty": item.get("difficulty", "medium"),
                    "category": item.get("category", "General"),
                })

    # Lab 08 - test_questions.json
    path = os.path.join(LAB08_PATH, "data/test_questions.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for item in json.load(f):
                chunk_ids = _get_chunk_id(item["question"])
                cases.append({
                    "id": f"lab08_tq_{item['id']}",
                    "question": item["question"],
                    "expected_answer": item["expected_answer"],
                    "expected_sources": item.get("expected_sources", []),
                    "ground_truth_chunk_ids": chunk_ids,
                    "difficulty": item.get("difficulty", "medium"),
                    "category": item.get("category", "General"),
                })

    # Lab 09 - test_questions.json
    path = os.path.join(LAB09_PATH, "data/test_questions.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for item in json.load(f):
                chunk_ids = _get_chunk_id(item["question"])
                cases.append({
                    "id": f"lab09_tq_{item['id']}",
                    "question": item["question"],
                    "expected_answer": item["expected_answer"],
                    "expected_sources": item.get("expected_sources", []),
                    "ground_truth_chunk_ids": chunk_ids,
                    "difficulty": item.get("difficulty", "medium"),
                    "category": item.get("category", "General"),
                })

    return cases


async def generate_adversarial_cases(num: int = 15) -> List[Dict]:
    """
    Dùng LLM API sinh thêm câu hỏi adversarial/edge-case.
    """
    client = AsyncOpenAI()

    # Prompt để sinh adversarial cases đa dạng
    prompt = f"""Bạn cần tạo {num} câu hỏi adversarial cho một hệ thống RAG chatbot nội bộ.
Các loại adversarial cases cần sinh:
1. Câu hỏi mâu thuẫn với document (agent phải nói "không có thông tin")
2. Câu hỏi cross-document (cần combine 2 tài liệu)
3. Câu hỏi có thông tin bẫy (số liệu sai trong câu hỏi)
4. Câu hỏi ngoài phạm vi hoàn toàn
5. Câu hỏi yêu cầu reasoning phức tạp (không lookup thẳng được)
6. Câu hỏi ambiguous (mập mờ, thiếu thông tin)
7. Prompt injection (thử lừa agent bỏ qua context)

Mỗi câu hỏi phải thuộc một trong các category: SLA, Refund, Access Control, HR, IT FAQ, Edge Case
Mỗi câu hỏi phải có difficulty: easy, medium, hard, hoặc adversarial

Trả về JSON array với schema:
[{{
    "id": "adv_001",
    "question": "câu hỏi",
    "expected_answer": "câu trả lời đúng mong đợi",
    "expected_sources": [],
    "ground_truth_chunk_ids": [],
    "difficulty": "adversarial",
    "category": "Edge Case"
}}]

Chỉ trả về JSON array, không có gì khác."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Bạn là chuyên gia thiết kế test cases cho AI chatbot nội bộ."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        cases = result if isinstance(result, list) else result.get("cases", result.get("questions", []))

        # Đảm bảo format đúng
        formatted = []
        for i, case in enumerate(cases[:num]):
            if isinstance(case, dict) and "question" in case:
                formatted.append({
                    "id": case.get("id", f"adv_{i+1:03d}"),
                    "question": case["question"],
                    "expected_answer": case.get("expected_answer", "Từ chối hoặc nói không có thông tin"),
                    "expected_sources": [],
                    "ground_truth_chunk_ids": _get_chunk_id(case["question"]),
                    "difficulty": case.get("difficulty", "adversarial"),
                    "category": case.get("category", "Edge Case"),
                })

        return formatted

    except Exception as e:
        print(f"Lỗi khi gọi OpenAI API: {e}")
        return []


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
