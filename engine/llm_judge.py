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
import os
from typing import Dict

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
        # TODO (Vương): import openai, khởi tạo AsyncOpenAI client

    async def _call_judge(
        self, system_prompt: str, question: str, answer: str, ground_truth: str
    ) -> Dict:
        """
        Gọi LLM với system prompt cho trước, parse JSON response.

        Returns:
            {"score": int, "reasoning": str}
        """
        # TODO (Vương): implement
        # 1. Tạo user message: "Question: {question}\nAnswer: {answer}\nGround Truth: {ground_truth}"
        # 2. Gọi openai.chat.completions.create(model=self.model, response_format={"type": "json_object"})
        # 3. Parse JSON, trả về {"score": int, "reasoning": str}
        raise NotImplementedError("Vương implement _call_judge()")

    async def evaluate_multi_judge(
        self, question: str, answer: str, ground_truth: str
    ) -> Dict:
        """
        Gọi 2 role judge song song, áp dụng conflict resolution.

        Returns:
            Dict theo schema JudgeResult ở trên
        """
        # TODO (Vương): implement
        # 1. Gọi song song: asyncio.gather(_call_judge(SYSTEM_STRICT, ...), _call_judge(SYSTEM_LENIENT, ...))
        # 2. Lấy score_strict, score_lenient
        # 3. Tính conflict, agreement_rate, final_score theo rule ở trên
        # 4. Trả về JudgeResult
        raise NotImplementedError("Vương implement evaluate_multi_judge()")

    async def check_position_bias(
        self, question: str, answer_a: str, answer_b: str, ground_truth: str
    ) -> Dict:
        """
        Kiểm tra position bias: đổi thứ tự A/B xem điểm có thay đổi không.
        Gọi judge 2 lần: (A, B) rồi (B, A), so sánh kết quả.

        Returns:
            {"bias_detected": bool, "score_ab": float, "score_ba": float}
        """
        # TODO (Vương): optional — implement sau khi evaluate_multi_judge xong
        pass
