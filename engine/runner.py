"""
Async Benchmark Runner — Trần Tiến Dũng implement

Interface contract (KHÔNG thay đổi tên hàm / cấu trúc return):
    run_single_test(test_case, version) -> TestResult
    run_all(dataset, version, batch_size) -> List[TestResult]

TestResult schema:
{
    "test_case": str,            # câu hỏi
    "agent_response": str,       # câu trả lời của agent
    "retrieved_chunk_ids": List[str],
    "latency_ms": float,
    "ragas": {
        "hit_rate": float,
        "mrr": float
    },
    "judge": {
        "final_score": float,
        "agreement_rate": float,
        "individual_scores": {"role_strict": float, "role_lenient": float},
        "conflict": bool
    },
    "status": "pass" | "fail"    # pass nếu final_score >= 3.0
}
"""

import asyncio
import time
from typing import Dict, List

from agent.main_agent import MainAgent
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator


class BenchmarkRunner:
    def __init__(self, agent: MainAgent, evaluator: RetrievalEvaluator, judge: LLMJudge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge

    async def run_single_test(self, test_case: Dict, version: str = "v2") -> Dict:
        """
        Chạy 1 test case: agent → retrieval eval → judge.

        Args:
            test_case: 1 dòng từ golden_set.jsonl
            version: "v1" hoặc "v2"

        Returns:
            Dict theo schema TestResult ở trên
        """
        # TODO (Dũng): implement
        # 1. Gọi self.agent.query(test_case["question"], version=version)
        # 2. Tính hit_rate và mrr từ evaluator (dùng retrieved_chunk_ids vs ground_truth_chunk_ids)
        # 3. Gọi self.judge.evaluate_multi_judge(question, answer, expected_answer)
        # 4. Build và return TestResult
        raise NotImplementedError("Dũng implement run_single_test()")

    async def run_all(
        self, dataset: List[Dict], version: str = "v2", batch_size: int = 10
    ) -> List[Dict]:
        """
        Chạy toàn bộ dataset song song theo batch.
        Dùng asyncio.Semaphore để tránh rate limit.

        Args:
            dataset: list test cases từ golden_set.jsonl
            version: "v1" hoặc "v2"
            batch_size: số case chạy song song cùng lúc

        Returns:
            List[TestResult]
        """
        # TODO (Dũng): implement
        # Gợi ý:
        #   sem = asyncio.Semaphore(batch_size)
        #   async def _run_with_sem(case):
        #       async with sem:
        #           return await self.run_single_test(case, version)
        #   return await asyncio.gather(*[_run_with_sem(c) for c in dataset])
        raise NotImplementedError("Dũng implement run_all()")
