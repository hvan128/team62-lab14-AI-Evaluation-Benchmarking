"""
Retrieval Evaluation — Đỗ Minh Khiêm implement

Interface contract (KHÔNG thay đổi tên hàm / cấu trúc return):
    calculate_hit_rate(expected_ids, retrieved_ids, top_k) -> float
    calculate_mrr(expected_ids, retrieved_ids) -> float
    evaluate_batch(dataset, agent, version) -> BatchRetrievalResult

BatchRetrievalResult schema:
{
    "avg_hit_rate": float,   # 0.0 – 1.0
    "avg_mrr": float,        # 0.0 – 1.0
    "per_case": [
        {
            "question": str,
            "expected_chunk_ids": List[str],
            "retrieved_chunk_ids": List[str],
            "hit": bool,
            "mrr": float
        },
        ...
    ]
}
"""

import asyncio
from typing import Dict, List


class RetrievalEvaluator:
    def calculate_hit_rate(
        self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3
    ) -> float:
        """
        1.0 nếu ít nhất 1 expected_id nằm trong top_k retrieved_ids, ngược lại 0.0.
        Logic đã đúng — Khiêm KHÔNG cần sửa hàm này.
        """
        top_retrieved = retrieved_ids[:top_k]
        return 1.0 if any(doc_id in top_retrieved for doc_id in expected_ids) else 0.0

    def calculate_mrr(
        self, expected_ids: List[str], retrieved_ids: List[str]
    ) -> float:
        """
        MRR = 1 / rank của expected_id đầu tiên xuất hiện trong retrieved_ids (1-indexed).
        0.0 nếu không tìm thấy.
        Logic đã đúng — Khiêm KHÔNG cần sửa hàm này.
        """
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    async def evaluate_batch(
        self, dataset: List[Dict], agent, version: str = "v2"
    ) -> Dict:
        """
        Chạy retrieval eval cho toàn bộ dataset.

        Args:
            dataset: list các test case từ golden_set.jsonl
                     Mỗi case phải có 'ground_truth_chunk_ids'
            agent: instance của MainAgent
            version: "v1" hoặc "v2"

        Returns:
            Dict theo schema BatchRetrievalResult ở trên
        """
        per_case = []

        for case in dataset:
            response = await agent.query(case["question"], version=version)
            expected_ids = case.get("ground_truth_chunk_ids", [])
            retrieved_ids = response.get("retrieved_chunk_ids", [])

            hit_rate = self.calculate_hit_rate(expected_ids, retrieved_ids, top_k=3)
            mrr = self.calculate_mrr(expected_ids, retrieved_ids)
            per_case.append(
                {
                    "question": case["question"],
                    "expected_chunk_ids": expected_ids,
                    "retrieved_chunk_ids": retrieved_ids,
                    "hit": hit_rate == 1.0,
                    "mrr": mrr,
                }
            )

        total = len(per_case) if per_case else 1
        avg_hit_rate = sum(1.0 if item["hit"] else 0.0 for item in per_case) / total
        avg_mrr = sum(item["mrr"] for item in per_case) / total

        return {
            "avg_hit_rate": avg_hit_rate,
            "avg_mrr": avg_mrr,
            "per_case": per_case,
        }
