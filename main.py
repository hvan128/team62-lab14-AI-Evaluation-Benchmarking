"""
Entry point — Trần Tiến Dũng implement phần regression gate + cost report.
Văn đã viết skeleton, Dũng điền vào các TODO.
"""

import asyncio
import json
import os
import time

from dotenv import load_dotenv

from agent.main_agent import MainAgent
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator
from engine.runner import BenchmarkRunner

load_dotenv()

RELEASE_GATE = {
    "min_score_delta": 0.0,       # V2 phải cao hơn V1 ít nhất 0.0
    "max_hit_rate_drop": 0.05,    # Hit Rate V2 không được giảm quá 5%
}

COST_PER_1K_TOKENS = 0.00015     # gpt-4o-mini input price USD


def load_dataset(path: str = "data/golden_set.jsonl"):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Thiếu {path}. Chạy 'python data/synthetic_gen.py' trước."
        )
    with open(path, encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]
    if len(dataset) < 50:
        print(f"⚠️  Chỉ có {len(dataset)} cases, cần ≥ 50.")
    return dataset


def build_summary(results, version: str, elapsed_s: float) -> dict:
    """Tổng hợp metrics từ list TestResult thành summary dict."""
    total = len(results)
    avg_score = sum(r["judge"]["final_score"] for r in results) / total
    hit_rate = sum(r["ragas"]["hit_rate"] for r in results) / total
    mrr = sum(r["ragas"]["mrr"] for r in results) / total
    agreement_rate = sum(r["judge"]["agreement_rate"] for r in results) / total
    total_tokens = sum(r.get("tokens_used", 0) for r in results)

    return {
        "metadata": {
            "version": version,
            "total": total,
            "elapsed_s": round(elapsed_s, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "metrics": {
            "avg_score": round(avg_score, 4),
            "hit_rate": round(hit_rate, 4),
            "mrr": round(mrr, 4),
            "agreement_rate": round(agreement_rate, 4),
        },
        "cost": {
            "total_tokens": total_tokens,
            "estimated_usd": round(total_tokens / 1000 * COST_PER_1K_TOKENS, 4),
        },
    }


def release_gate(v1_summary: dict, v2_summary: dict) -> str:
    """
    So sánh V1 vs V2 theo RELEASE_GATE thresholds.

    Returns:
        "APPROVE" hoặc "BLOCK"
    """
    delta = v2_summary["metrics"]["avg_score"] - v1_summary["metrics"]["avg_score"]
    hit_rate_drop = v1_summary["metrics"]["hit_rate"] - v2_summary["metrics"]["hit_rate"]
    if (
        delta >= RELEASE_GATE["min_score_delta"]
        and hit_rate_drop <= RELEASE_GATE["max_hit_rate_drop"]
    ):
        return "APPROVE"
    return "BLOCK"


async def run_benchmark(version: str, dataset, runner: BenchmarkRunner):
    print(f"\n🚀 Đang chạy benchmark cho {version} ({len(dataset)} cases)...")
    start = time.perf_counter()
    results = await runner.run_all(dataset, version=version)
    elapsed = time.perf_counter() - start
    summary = build_summary(results, version, elapsed)
    print(f"✅ {version} xong trong {elapsed:.1f}s | avg_score={summary['metrics']['avg_score']:.2f} | hit_rate={summary['metrics']['hit_rate']*100:.1f}%")
    return results, summary


async def main():
    dataset = load_dataset()

    agent = MainAgent()
    evaluator = RetrievalEvaluator()
    judge = LLMJudge()
    runner = BenchmarkRunner(agent, evaluator, judge)

    # Chạy V1
    v1_results, v1_summary = await run_benchmark("v1", dataset, runner)

    # Chạy V2
    v2_results, v2_summary = await run_benchmark("v2", dataset, runner)

    # Regression gate
    decision = release_gate(v1_summary, v2_summary)
    delta = v2_summary["metrics"]["avg_score"] - v1_summary["metrics"]["avg_score"]

    print("\n📊 --- REGRESSION REPORT ---")
    print(f"V1 avg_score : {v1_summary['metrics']['avg_score']:.2f}")
    print(f"V2 avg_score : {v2_summary['metrics']['avg_score']:.2f}")
    print(f"Delta        : {delta:+.2f}")
    print(f"V1 hit_rate  : {v1_summary['metrics']['hit_rate']*100:.1f}%")
    print(f"V2 hit_rate  : {v2_summary['metrics']['hit_rate']*100:.1f}%")
    print(f"Cost V2      : ${v2_summary['cost']['estimated_usd']:.4f} ({v2_summary['cost']['total_tokens']} tokens)")
    print(f"\n{'✅ QUYẾT ĐỊNH: APPROVE RELEASE' if decision == 'APPROVE' else '❌ QUYẾT ĐỊNH: BLOCK RELEASE'}")

    # Ghi vào v2_summary để check_lab.py validate
    v2_summary["regression"] = {
        "v1_avg_score": v1_summary["metrics"]["avg_score"],
        "v2_avg_score": v2_summary["metrics"]["avg_score"],
        "delta": round(delta, 4),
        "decision": decision,
    }

    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    print("\n📁 Đã lưu: reports/summary.json + reports/benchmark_results.json")


if __name__ == "__main__":
    asyncio.run(main())
