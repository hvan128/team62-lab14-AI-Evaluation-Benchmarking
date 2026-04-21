"""
Multi-Judge Engine — Trần Đình Minh Vương implement

Interface contract (KHÔNG thay đổi tên hàm / cấu trúc return):
    evaluate_multi_judge(question, answer, ground_truth) -> JudgeResult

JudgeResult schema:
{
    "final_score": float,          # 1.0 – 5.0, điểm cuối cùng sau conflict resolution
    "agreement_rate": float,       # 1.0 nếu |score_a - score_b| <= 1, else 0.5
    "individual_scores": {
        "role_strict": float,      # điểm từ Judge "nghiêm khắc"
        "role_lenient": float      # điểm từ Judge "dễ chịu"
    },
    "conflict": bool,              # True nếu |score_a - score_b| > 1
    "reasoning": str               # lý do của Judge (từ model nghiêm khắc)
}

Conflict resolution rule:
    |score_a - score_b| <= 1  →  final_score = average, agreement_rate = 1.0
    |score_a - score_b| >  1  →  final_score = min(score_a, score_b), agreement_rate = 0.5
"""

import asyncio
import json
import os
from typing import Dict

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4o-mini")
JUDGE_MODEL_STRICT = os.getenv("JUDGE_MODEL_STRICT", JUDGE_MODEL)
JUDGE_MODEL_LENIENT = os.getenv("JUDGE_MODEL_LENIENT", JUDGE_MODEL)


def _unique_model_key(primary: str, secondary: str, suffix: str) -> str:
    if primary == secondary:
        return f"{primary} ({suffix})"
    return primary

RUBRIC = """
Chấm điểm câu trả lời từ 1 đến 5 dựa trên:
- Accuracy (độ chính xác so với Ground Truth): 40%
- Completeness (đầy đủ thông tin quan trọng): 30%
- No Hallucination (không bịa thêm thông tin ngoài context): 30%

Trả về JSON: {"score": <int 1-5>, "reasoning": "<lý do ngắn gọn>"}
"""

SYSTEM_STRICT = (
    "Bạn là một Judge AI cực kỳ nghiêm khắc. "
    "Chỉ cho điểm cao khi câu trả lời chính xác 100% và không có bất kỳ thông tin sai nào. "
    + RUBRIC
)

SYSTEM_LENIENT = (
    "Bạn là một Judge AI cởi mở. "
    "Chấp nhận câu trả lời nếu ý chính đúng, dù có thể thiếu chi tiết nhỏ. "
    + RUBRIC
)


class LLMJudge:
    def __init__(self, model: str = JUDGE_MODEL):
        self.model = model
        self.client = AsyncOpenAI()

    async def _call_judge(
        self,
        system_prompt: str,
        question: str,
        answer: str,
        ground_truth: str,
        model: str,
    ) -> Dict:
        """
        Gọi LLM với system prompt cho trước, parse JSON response.

        Returns:
            {"score": int, "reasoning": str}
        """
        if self.client is None:
            gt_tokens = set(ground_truth.lower().split())
            ans_tokens = set(answer.lower().split())
            overlap = len(gt_tokens & ans_tokens) / max(1, len(gt_tokens))
            if overlap >= 0.75:
                score = 5
            elif overlap >= 0.55:
                score = 4
            elif overlap >= 0.35:
                score = 3
            elif overlap >= 0.2:
                score = 2
            else:
                score = 1
            return {
                "score": score,
                "reasoning": "Fallback lexical judge (không có OpenAI API key).",
            }

        user_message = (
            f"Question: {question}\n"
            f"Answer: {answer}\n"
            f"Ground Truth: {ground_truth}"
        )
        response = await self.client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
        )

        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        score = int(parsed.get("score", 1))
        score = max(1, min(5, score))
        return {
            "score": score,
            "reasoning": str(parsed.get("reasoning", "")),
        }

    async def evaluate_multi_judge(
        self, question: str, answer: str, ground_truth: str
    ) -> Dict:
        """
        Gọi 2 role judge song song, áp dụng conflict resolution.

        Returns:
            Dict theo schema JudgeResult ở trên
        """
        strict_result, lenient_result = await asyncio.gather(
            self._call_judge(
                SYSTEM_STRICT,
                question,
                answer,
                ground_truth,
                model=JUDGE_MODEL_STRICT,
            ),
            self._call_judge(
                SYSTEM_LENIENT,
                question,
                answer,
                ground_truth,
                model=JUDGE_MODEL_LENIENT,
            ),
        )

        score_strict = float(strict_result["score"])
        score_lenient = float(lenient_result["score"])
        conflict = abs(score_strict - score_lenient) > 1
        if conflict:
            final_score = min(score_strict, score_lenient)
            agreement_rate = 0.5
        else:
            final_score = (score_strict + score_lenient) / 2
            agreement_rate = 1.0

        return {
            "final_score": float(final_score),
            "agreement_rate": agreement_rate,
            "individual_scores": {
                "role_strict": score_strict,
                "role_lenient": score_lenient,
            },
            "individual_results": {
                _unique_model_key(JUDGE_MODEL_STRICT, JUDGE_MODEL_LENIENT, "strict"): {
                    "score": score_strict,
                    "reasoning": strict_result.get("reasoning", ""),
                },
                _unique_model_key(JUDGE_MODEL_LENIENT, JUDGE_MODEL_STRICT, "lenient"): {
                    "score": score_lenient,
                    "reasoning": lenient_result.get("reasoning", ""),
                },
            },
            "conflict": conflict,
            "reasoning": strict_result.get("reasoning", ""),
        }

    async def check_position_bias(
        self, question: str, answer_a: str, answer_b: str, ground_truth: str
    ) -> Dict:
        """
        Kiểm tra position bias: đổi thứ tự A/B xem điểm có thay đổi không.
        Gọi judge 2 lần: (A, B) rồi (B, A), so sánh kết quả.

        Returns:
            {"bias_detected": bool, "score_ab": float, "score_ba": float}
        """
        result_ab = await self.evaluate_multi_judge(
            question,
            f"A: {answer_a}\nB: {answer_b}",
            ground_truth,
        )
        result_ba = await self.evaluate_multi_judge(
            question,
            f"A: {answer_b}\nB: {answer_a}",
            ground_truth,
        )
        score_ab = float(result_ab["final_score"])
        score_ba = float(result_ba["final_score"])
        return {
            "bias_detected": abs(score_ab - score_ba) >= 1.0,
            "score_ab": score_ab,
            "score_ba": score_ba,
        }
