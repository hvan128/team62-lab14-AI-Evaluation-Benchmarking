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

from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4o-mini")

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
        self, system_prompt: str, question: str, answer: str, ground_truth: str
    ) -> Dict:
        """
        Gọi LLM với system prompt cho trước, parse JSON response.

        Returns:
            {"score": int, "reasoning": str}
        """
        user_msg = f"""Question: {question}
Answer: {answer}
Ground Truth: {ground_truth}

Chấm điểm và trả về JSON: {{"score": <int 1-5>, "reasoning": "<lý do>"}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            return {
                "score": int(result.get("score", 3)),
                "reasoning": result.get("reasoning", "")
            }
        except Exception as e:
            return {"score": 3, "reasoning": f"Lỗi API: {e}"}

    async def evaluate_multi_judge(
        self, question: str, answer: str, ground_truth: str
    ) -> Dict:
        """
        Gọi 2 role judge song song, áp dụng conflict resolution.

        Returns:
            Dict theo schema JudgeResult:
            {
                "final_score": float,
                "agreement_rate": float,
                "individual_scores": {"role_strict": float, "role_lenient": float},
                "conflict": bool,
                "reasoning": str
            }
        """
        # Gọi song song 2 judge
        strict_task = self._call_judge(SYSTEM_STRICT, question, answer, ground_truth)
        lenient_task = self._call_judge(SYSTEM_LENIENT, question, answer, ground_truth)

        strict_result, lenient_result = await asyncio.gather(strict_task, lenient_task)

        score_strict = strict_result["score"]
        score_lenient = lenient_result["score"]

        # Conflict resolution
        diff = abs(score_strict - score_lenient)
        conflict = diff > 1

        if not conflict:
            final_score = (score_strict + score_lenient) / 2
            agreement_rate = 1.0
        else:
            final_score = min(score_strict, score_lenient)
            agreement_rate = 0.5

        return {
            "final_score": round(final_score, 2),
            "agreement_rate": agreement_rate,
            "individual_scores": {
                "role_strict": float(score_strict),
                "role_lenient": float(score_lenient)
            },
            "conflict": conflict,
            "reasoning": strict_result["reasoning"]
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
        result_ab = await self.evaluate_multi_judge(question, answer_a, ground_truth)
        result_ba = await self.evaluate_multi_judge(question, answer_b, ground_truth)

        score_ab = result_ab["final_score"]
        score_ba = result_ba["final_score"]
        bias_detected = abs(score_ab - score_ba) > 0.5

        return {
            "bias_detected": bias_detected,
            "score_ab": score_ab,
            "score_ba": score_ba
        }
