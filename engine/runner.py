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

        agent_result = await self.agent.query(question, version=version)
        retrieved_chunk_ids = agent_result.get("retrieved_chunk_ids", [])
        contexts = agent_result.get("contexts", [])
        answer = agent_result.get("answer", "")

        hit_rate = self.evaluator.calculate_hit_rate(
            expected_chunk_ids, retrieved_chunk_ids, top_k=3
        )
        mrr = self.evaluator.calculate_mrr(expected_chunk_ids, retrieved_chunk_ids)
        faithfulness = self.evaluator.calculate_faithfulness(answer, contexts)
        relevancy = self.evaluator.calculate_relevancy(question, answer)

        judge_result = await self.judge.evaluate_multi_judge(
            question, answer, expected_answer
        )

        latency_ms = (time.perf_counter() - start) * 1000
        final_score = float(judge_result.get("final_score", 1.0))

        return {
            "test_case": question,
            "agent_response": answer,
            "retrieved_chunk_ids": retrieved_chunk_ids,
            "latency_ms": latency_ms,
            "ragas": {
                "hit_rate": hit_rate,
                "mrr": mrr,
                "faithfulness": faithfulness,
                "relevancy": relevancy,
            },
            "judge": {
                "final_score": final_score,
                "agreement_rate": float(judge_result.get("agreement_rate", 0.5)),
                "individual_scores": judge_result.get("individual_scores", {}),
                "individual_results": judge_result.get("individual_results", {}),
                "conflict": bool(judge_result.get("conflict", False)),
            },
            "tokens_used": agent_result.get("metadata", {}).get("tokens_used", 0),
            "status": "pass" if final_score >= 3.0 else "fail",
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

        async def _run_with_sem(case: Dict) -> Dict:
            async with sem:
                return await self.run_single_test(case, version=version)

        tasks = [_run_with_sem(case) for case in dataset]
        return await asyncio.gather(*tasks)
