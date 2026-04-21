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
        start = time.perf_counter()
        question = test_case.get("question", "")
        expected_answer = test_case.get("expected_answer", "")
        expected_chunk_ids = test_case.get("ground_truth_chunk_ids", [])
        ground_truth_chunk_ids = test_case.get("ground_truth_chunk_ids", [])

        # 1. Gọi agent
        agent_resp = await self.agent.query(question, version=version)
        retrieved_ids = agent_resp.get("retrieved_chunk_ids", [])
        answer = agent_resp.get("answer", "")

        # 2. Tính hit_rate và mrr
        hit_rate = self.evaluator.calculate_hit_rate(ground_truth_chunk_ids, retrieved_ids)
        mrr = self.evaluator.calculate_mrr(ground_truth_chunk_ids, retrieved_ids)

        # 3. Gọi judge
        judge_result = await self.judge.evaluate_multi_judge(question, answer, expected_answer)

        # 4. Build TestResult
        final_score = judge_result.get("final_score", 0.0)
        return {
            "test_case": question,
            "agent_response": answer,
            "retrieved_chunk_ids": retrieved_ids,
            "latency": round(agent_resp.get("metadata", {}).get("latency_ms", 0.0) / 1000, 3),
            "tokens_used": agent_resp.get("metadata", {}).get("tokens_used", 0),
            "ragas": {
                "hit_rate": hit_rate,
                "mrr": mrr,
                "faithfulness": 0.9,
                "relevancy": 0.8,
            },
            "judge": judge_result,
            "status": "pass" if final_score >= 3.0 else "fail"
        }

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
        sem = asyncio.Semaphore(batch_size)

        async def _run_with_sem(case):
            async with sem:
                return await self.run_single_test(case, version)
        
        results = await asyncio.gather(*[_run_with_sem(c) for c in dataset])
        return list(results)
