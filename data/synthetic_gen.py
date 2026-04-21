"""Golden dataset generator for evaluation benchmarks."""
"""Golden dataset generator for evaluation benchmarks."""

import asyncio
import json
import os
import sys
from typing import Dict, List

import chromadb
from dotenv import load_dotenv
from openai import AsyncOpenAI

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from engine.chroma_utils import get_or_bootstrap_collection, query_collection
from openai import AsyncOpenAI

load_dotenv()

OUTPUT_PATH = "data/golden_set.jsonl"
CHROMA_PATH = "data/chroma_db"
ALLOWED_DIFFICULTIES = {"easy", "medium", "hard", "adversarial"}
ALLOWED_CATEGORIES = {
    "SLA",
    "Refund",
    "Access Control",
    "HR",
    "IT FAQ",
    "Edge Case",
}


def _normalize_difficulty(value: str) -> str:
    if not value:
        return "medium"
    normalized = value.strip().lower()
    return normalized if normalized in ALLOWED_DIFFICULTIES else "medium"


def _normalize_category(value: str) -> str:
    if not value:
        return "Edge Case"
    normalized = value.strip().lower()
    if normalized in {"sla", "incident", "p1"}:
        return "SLA"
    if normalized in {"refund", "refund policy"}:
        return "Refund"
    if normalized in {"access", "access control", "security"}:
        return "Access Control"
    if normalized in {"hr", "hr policy", "human resources"}:
        return "HR"
    if normalized in {"it", "it faq", "it helpdesk", "it support"}:
        return "IT FAQ"
    return "Edge Case"


def _normalize_case(case: Dict) -> Dict:
    return {
        "id": str(case["id"]),
        "question": str(case["question"]),
        "expected_answer": str(case["expected_answer"]),
        "expected_sources": [str(s) for s in case.get("expected_sources", [])],
        "ground_truth_chunk_ids": [
            str(c) for c in case.get("ground_truth_chunk_ids", [])
        ],
        "difficulty": _normalize_difficulty(case.get("difficulty", "medium")),
        "category": _normalize_category(case.get("category", "Edge Case")),
    }


def _build_expected_answer(item: Dict) -> str:
    if item.get("expected_answer"):
        return item["expected_answer"]

    criteria = item.get("grading_criteria")
    if isinstance(criteria, list) and criteria:
        return " ".join(str(c) for c in criteria)

    return "Không có thông tin đủ trong tài liệu hiện có."


def _init_collection():
    try:
        collection_name = os.getenv("CHROMA_COLLECTION", "lab14_seed_kb")
        return get_or_bootstrap_collection(CHROMA_PATH, collection_name=collection_name)
    except Exception:
        return None


def _lookup_chunk_ids(question: str, collection) -> List[str]:
    if not collection:
        return []
    try:
        result = query_collection(collection, question, n_results=1)
        ids = result.get("ids", [])
        if ids and ids[0]:
            return [ids[0][0]]
    except Exception:
        return []
    return []


def load_existing_questions(collection=None) -> List[Dict]:
    """Load and normalize existing cases from available files."""
CHROMA_PATH = "data/chroma_db"
ALLOWED_DIFFICULTIES = {"easy", "medium", "hard", "adversarial"}
ALLOWED_CATEGORIES = {
    "SLA",
    "Refund",
    "Access Control",
    "HR",
    "IT FAQ",
    "Edge Case",
}


def _normalize_difficulty(value: str) -> str:
    if not value:
        return "medium"
    normalized = value.strip().lower()
    return normalized if normalized in ALLOWED_DIFFICULTIES else "medium"


def _normalize_category(value: str) -> str:
    if not value:
        return "Edge Case"
    normalized = value.strip().lower()
    if normalized in {"sla", "incident", "p1"}:
        return "SLA"
    if normalized in {"refund", "refund policy"}:
        return "Refund"
    if normalized in {"access", "access control", "security"}:
        return "Access Control"
    if normalized in {"hr", "hr policy", "human resources"}:
        return "HR"
    if normalized in {"it", "it faq", "it helpdesk", "it support"}:
        return "IT FAQ"
    return "Edge Case"


def _normalize_case(case: Dict) -> Dict:
    return {
        "id": str(case["id"]),
        "question": str(case["question"]),
        "expected_answer": str(case["expected_answer"]),
        "expected_sources": [str(s) for s in case.get("expected_sources", [])],
        "ground_truth_chunk_ids": [
            str(c) for c in case.get("ground_truth_chunk_ids", [])
        ],
        "difficulty": _normalize_difficulty(case.get("difficulty", "medium")),
        "category": _normalize_category(case.get("category", "Edge Case")),
    }


def _build_expected_answer(item: Dict) -> str:
    if item.get("expected_answer"):
        return item["expected_answer"]

    criteria = item.get("grading_criteria")
    if isinstance(criteria, list) and criteria:
        return " ".join(str(c) for c in criteria)

    return "Không có thông tin đủ trong tài liệu hiện có."


def _init_collection():
    if not os.path.exists(CHROMA_PATH):
        return None

    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collections = client.list_collections()
        if not collections:
            return None

        preferred = os.getenv("CHROMA_COLLECTION")
        if preferred:
            try:
                return client.get_collection(preferred)
            except Exception:
                pass

        first = collections[0]
        if hasattr(first, "name"):
            return first
        if isinstance(first, str):
            return client.get_collection(first)
    except Exception:
        return None
    return None


def _lookup_chunk_ids(question: str, collection) -> List[str]:
    if not collection:
        return []
    try:
        result = collection.query(query_texts=[question], n_results=1)
        ids = result.get("ids", [])
        if ids and ids[0]:
            return [ids[0][0]]
    except Exception:
        return []
    return []


def load_existing_questions(collection=None) -> List[Dict]:
    """Load and normalize existing cases from available files."""
    cases = []

    path = os.path.join("data", "grading_questions.json")
    path = os.path.join("data", "grading_questions.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for item in json.load(f):
                case = {
                case = {
                    "id": f"lab08_gq_{item['id']}",
                    "question": item["question"],
                    "expected_answer": _build_expected_answer(item),
                    "expected_answer": _build_expected_answer(item),
                    "expected_sources": item.get("expected_sources", []),
                    "ground_truth_chunk_ids": _lookup_chunk_ids(item["question"], collection),
                    "ground_truth_chunk_ids": _lookup_chunk_ids(item["question"], collection),
                    "difficulty": item.get("difficulty", "medium"),
                    "category": item.get("category", "Edge Case"),
                }
                cases.append(_normalize_case(case))
                    "category": item.get("category", "Edge Case"),
                }
                cases.append(_normalize_case(case))

    path = os.path.join("data", "test_questions.json")
    path = os.path.join("data", "test_questions.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for item in json.load(f):
                case = {
                case = {
                    "id": f"lab08_tq_{item['id']}",
                    "question": item["question"],
                    "expected_answer": _build_expected_answer(item),
                    "expected_answer": _build_expected_answer(item),
                    "expected_sources": item.get("expected_sources", []),
                    "ground_truth_chunk_ids": _lookup_chunk_ids(item["question"], collection),
                    "ground_truth_chunk_ids": _lookup_chunk_ids(item["question"], collection),
                    "difficulty": item.get("difficulty", "medium"),
                    "category": item.get("category", "Edge Case"),
                }
                cases.append(_normalize_case(case))
                    "category": item.get("category", "Edge Case"),
                }
                cases.append(_normalize_case(case))

    path = os.path.join("data", "test_questions.json")
    path = os.path.join("data", "test_questions.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for item in json.load(f):
                case = {
                case = {
                    "id": f"lab09_tq_{item['id']}",
                    "question": item["question"],
                    "expected_answer": _build_expected_answer(item),
                    "expected_answer": _build_expected_answer(item),
                    "expected_sources": item.get("expected_sources", []),
                    "ground_truth_chunk_ids": _lookup_chunk_ids(item["question"], collection),
                    "ground_truth_chunk_ids": _lookup_chunk_ids(item["question"], collection),
                    "difficulty": item.get("difficulty", "medium"),
                    "category": item.get("category", "Edge Case"),
                }
                cases.append(_normalize_case(case))
                    "category": item.get("category", "Edge Case"),
                }
                cases.append(_normalize_case(case))

    return cases


def _build_fallback_adversarial_cases(num: int, collection) -> List[Dict]:
    templates = [
        {
            "question": "Tài liệu có nói SLA P1 resolution là 24 giờ không? Nếu có, trích nguồn.",
            "expected_answer": "Không có thông tin trong tài liệu xác nhận SLA P1 resolution là 24 giờ.",
            "expected_sources": ["sla_p1_2026.txt"],
            "difficulty": "adversarial",
            "category": "Edge Case",
        },
        {
            "question": "Nếu ticket P1 xảy ra lúc 2am và cần Level 2 emergency access, cần notify kênh nào và phê duyệt bởi ai?",
            "expected_answer": "Cần kết hợp SLA P1 notification (Slack #incident-p1, email incident@company.internal, PagerDuty) và Level 2 emergency access với approval đồng thời từ Line Manager và IT Admin on-call.",
            "expected_sources": ["sla_p1_2026.txt", "access_control_sop.txt"],
            "difficulty": "hard",
            "category": "Access Control",
        },
        {
            "question": "Khách hàng báo đơn Flash Sale vẫn được hoàn tiền 100 phần trăm trong 30 ngày, điều này đúng không?",
            "expected_answer": "Không đúng. Flash Sale là ngoại lệ không được hoàn tiền theo policy_refund_v4.txt.",
            "expected_sources": ["policy_refund_v4.txt"],
            "difficulty": "adversarial",
            "category": "Refund",
        },
        {
            "question": "Công ty có chính sách hỗ trợ visa du học cho thân nhân nhân viên không?",
            "expected_answer": "Không có thông tin về nội dung này trong bộ tài liệu hiện có.",
            "expected_sources": [],
            "difficulty": "adversarial",
            "category": "Edge Case",
        },
        {
            "question": "So sánh rủi ro nếu bỏ qua phản hồi 10 phút của P1 với việc cấp sai Level 3 access cho contractor.",
            "expected_answer": "Cần reasoning trên hai tài liệu: bỏ qua SLA P1 gây delay escalation, cấp sai Level 3 vi phạm quy trình 3 cấp phê duyệt và tăng rủi ro bảo mật.",
            "expected_sources": ["sla_p1_2026.txt", "access_control_sop.txt"],
            "difficulty": "adversarial",
            "category": "Edge Case",
        },
    ]

    generated = []
    for i in range(num):
        case = dict(templates[i % len(templates)])
        case["id"] = f"adv_{i+1:03d}"
        case["question"] = f"{case['question']} (case {i+1})"
        case["ground_truth_chunk_ids"] = _lookup_chunk_ids(case["question"], collection)
        generated.append(_normalize_case(case))
    return generated


async def generate_adversarial_cases(
    num: int = 15, collection=None, existing_cases: List[Dict] = None
) -> List[Dict]:
    """Generate adversarial/edge cases with LLM, fallback to templates."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _build_fallback_adversarial_cases(num, collection)

    client = AsyncOpenAI(api_key=api_key)
    model = os.getenv("SYNTHETIC_MODEL", "gpt-4o-mini")

    seed_text = ""
    if existing_cases:
        sample = existing_cases[:8]
        seed_text = "\n".join(
            f"- Q: {c['question']}\n  A: {c['expected_answer']}\n  Sources: {c['expected_sources']}"
            for c in sample
        )

    prompt = f"""
Hãy tạo CHÍNH XÁC {num} cases adversarial/edge-case bằng tiếng Việt.

Bắt buộc có đủ 5 loại:
1) Mâu thuẫn với tài liệu
2) Cross-document
3) Có thông tin bẫy (số liệu sai)
4) Ngoài phạm vi hoàn toàn
5) Câu hỏi reasoning

Schema mỗi case (không thêm field):
id, question, expected_answer, expected_sources, difficulty, category

Rules:
- difficulty: easy|medium|hard|adversarial
- category: SLA|Refund|Access Control|HR|IT FAQ|Edge Case
- expected_sources là list tên file, có thể rỗng nếu ngoài phạm vi

Output JSON object duy nhất: {{"cases": [ ... ]}}

Samples từ bộ existing:
{seed_text}
""".strip()

    try:
        resp = await client.chat.completions.create(
            model=model,
            temperature=0.4,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Chỉ trả về JSON object hợp lệ, không thêm text.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        payload = json.loads(resp.choices[0].message.content or "{}")
        raw_cases = payload.get("cases", [])
    except Exception:
        return _build_fallback_adversarial_cases(num, collection)

    generated = []
    for i, item in enumerate(raw_cases[:num]):
        question = str(item.get("question", "")).strip()
        expected_answer = str(item.get("expected_answer", "")).strip()
        if not question or not expected_answer:
            continue

        case = {
            "id": f"adv_{i+1:03d}",
            "question": question,
            "expected_answer": expected_answer,
            "expected_sources": item.get("expected_sources", []),
            "ground_truth_chunk_ids": _lookup_chunk_ids(question, collection),
            "difficulty": item.get("difficulty", "adversarial"),
            "category": item.get("category", "Edge Case"),
        }
        generated.append(_normalize_case(case))

    if len(generated) < num:
        needed = num - len(generated)
        extra = _build_fallback_adversarial_cases(needed, collection)
        generated.extend(extra)

    for i, case in enumerate(generated):
        case["id"] = f"adv_{i+1:03d}"
    return generated[:num]
def _build_fallback_adversarial_cases(num: int, collection) -> List[Dict]:
    templates = [
        {
            "question": "Tài liệu có nói SLA P1 resolution là 24 giờ không? Nếu có, trích nguồn.",
            "expected_answer": "Không có thông tin trong tài liệu xác nhận SLA P1 resolution là 24 giờ.",
            "expected_sources": ["sla_p1_2026.txt"],
            "difficulty": "adversarial",
            "category": "Edge Case",
        },
        {
            "question": "Nếu ticket P1 xảy ra lúc 2am và cần Level 2 emergency access, cần notify kênh nào và phê duyệt bởi ai?",
            "expected_answer": "Cần kết hợp SLA P1 notification (Slack #incident-p1, email incident@company.internal, PagerDuty) và Level 2 emergency access với approval đồng thời từ Line Manager và IT Admin on-call.",
            "expected_sources": ["sla_p1_2026.txt", "access_control_sop.txt"],
            "difficulty": "hard",
            "category": "Access Control",
        },
        {
            "question": "Khách hàng báo đơn Flash Sale vẫn được hoàn tiền 100 phần trăm trong 30 ngày, điều này đúng không?",
            "expected_answer": "Không đúng. Flash Sale là ngoại lệ không được hoàn tiền theo policy_refund_v4.txt.",
            "expected_sources": ["policy_refund_v4.txt"],
            "difficulty": "adversarial",
            "category": "Refund",
        },
        {
            "question": "Công ty có chính sách hỗ trợ visa du học cho thân nhân nhân viên không?",
            "expected_answer": "Không có thông tin về nội dung này trong bộ tài liệu hiện có.",
            "expected_sources": [],
            "difficulty": "adversarial",
            "category": "Edge Case",
        },
        {
            "question": "So sánh rủi ro nếu bỏ qua phản hồi 10 phút của P1 với việc cấp sai Level 3 access cho contractor.",
            "expected_answer": "Cần reasoning trên hai tài liệu: bỏ qua SLA P1 gây delay escalation, cấp sai Level 3 vi phạm quy trình 3 cấp phê duyệt và tăng rủi ro bảo mật.",
            "expected_sources": ["sla_p1_2026.txt", "access_control_sop.txt"],
            "difficulty": "adversarial",
            "category": "Edge Case",
        },
    ]

    generated = []
    for i in range(num):
        case = dict(templates[i % len(templates)])
        case["id"] = f"adv_{i+1:03d}"
        case["question"] = f"{case['question']} (case {i+1})"
        case["ground_truth_chunk_ids"] = _lookup_chunk_ids(case["question"], collection)
        generated.append(_normalize_case(case))
    return generated


async def generate_adversarial_cases(
    num: int = 15, collection=None, existing_cases: List[Dict] = None
) -> List[Dict]:
    """Generate adversarial/edge cases with LLM, fallback to templates."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _build_fallback_adversarial_cases(num, collection)

    client = AsyncOpenAI(api_key=api_key)
    model = os.getenv("SYNTHETIC_MODEL", "gpt-4o-mini")

    seed_text = ""
    if existing_cases:
        sample = existing_cases[:8]
        seed_text = "\n".join(
            f"- Q: {c['question']}\n  A: {c['expected_answer']}\n  Sources: {c['expected_sources']}"
            for c in sample
        )

    prompt = f"""
Hãy tạo CHÍNH XÁC {num} cases adversarial/edge-case bằng tiếng Việt.

Bắt buộc có đủ 5 loại:
1) Mâu thuẫn với tài liệu
2) Cross-document
3) Có thông tin bẫy (số liệu sai)
4) Ngoài phạm vi hoàn toàn
5) Câu hỏi reasoning

Schema mỗi case (không thêm field):
id, question, expected_answer, expected_sources, difficulty, category

Rules:
- difficulty: easy|medium|hard|adversarial
- category: SLA|Refund|Access Control|HR|IT FAQ|Edge Case
- expected_sources là list tên file, có thể rỗng nếu ngoài phạm vi

Output JSON object duy nhất: {{"cases": [ ... ]}}

Samples từ bộ existing:
{seed_text}
""".strip()

    try:
        resp = await client.chat.completions.create(
            model=model,
            temperature=0.4,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Chỉ trả về JSON object hợp lệ, không thêm text.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        payload = json.loads(resp.choices[0].message.content or "{}")
        raw_cases = payload.get("cases", [])
    except Exception:
        return _build_fallback_adversarial_cases(num, collection)

    generated = []
    for i, item in enumerate(raw_cases[:num]):
        question = str(item.get("question", "")).strip()
        expected_answer = str(item.get("expected_answer", "")).strip()
        if not question or not expected_answer:
            continue

        case = {
            "id": f"adv_{i+1:03d}",
            "question": question,
            "expected_answer": expected_answer,
            "expected_sources": item.get("expected_sources", []),
            "ground_truth_chunk_ids": _lookup_chunk_ids(question, collection),
            "difficulty": item.get("difficulty", "adversarial"),
            "category": item.get("category", "Edge Case"),
        }
        generated.append(_normalize_case(case))

    if len(generated) < num:
        needed = num - len(generated)
        extra = _build_fallback_adversarial_cases(needed, collection)
        generated.extend(extra)

    for i, case in enumerate(generated):
        case["id"] = f"adv_{i+1:03d}"
    return generated[:num]


async def main():
    collection = _init_collection()
    existing = load_existing_questions(collection=collection)
    collection = _init_collection()
    existing = load_existing_questions(collection=collection)
    print(f"Loaded {len(existing)} questions from lab 08/09")

    adversarial = await generate_adversarial_cases(
        num=max(15, 50 - len(existing)),
        collection=collection,
        existing_cases=existing,
    )
    adversarial = await generate_adversarial_cases(
        num=max(15, 50 - len(existing)),
        collection=collection,
        existing_cases=existing,
    )
    all_cases = existing + adversarial

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for case in all_cases:
            f.write(json.dumps(_normalize_case(case), ensure_ascii=False) + "\n")
            f.write(json.dumps(_normalize_case(case), ensure_ascii=False) + "\n")

    print(f"Done! Saved {len(all_cases)} cases to {OUTPUT_PATH}")
    assert len(all_cases) >= 50, f"Cần >=50 cases, hiện có {len(all_cases)}"
    assert len(all_cases) >= 50, f"Cần >=50 cases, hiện có {len(all_cases)}"


if __name__ == "__main__":
    asyncio.run(main())
