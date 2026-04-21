"""
Agent V1 và V2 — Đỗ Minh Khiêm implement

Interface contract (KHÔNG thay đổi tên hàm / cấu trúc return):
    query(question, version) -> AgentResponse

AgentResponse schema:
{
    "answer": str,
    "retrieved_chunk_ids": List[str],   # chunk_id từ ChromaDB — bắt buộc để tính Hit Rate
    "contexts": List[str],              # nội dung các chunk đã retrieve
    "metadata": {
        "version": str,                 # "v1" hoặc "v2"
        "model": str,
        "tokens_used": int,
        "latency_ms": float
    }
}

V1 vs V2:
    V1: top_k=2, prompt ngắn, temperature=0.8
    V2: top_k=5, filter score < 0.5, prompt kỹ hơn, temperature=0.1
"""

import asyncio
import os
import time
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

# TODO (Khiêm): import chromadb và openai, kết nối collection


class MainAgent:
    def __init__(self):
        self.name = "SupportAgent"
        # TODO (Khiêm): khởi tạo ChromaDB client, OpenAI client

    async def query(self, question: str, version: str = "v2") -> Dict:
        """
        Thực hiện RAG: retrieve từ ChromaDB → generate bằng LLM.

        Args:
            question: câu hỏi cần trả lời
            version: "v1" (cơ bản) hoặc "v2" (tối ưu)

        Returns:
            Dict theo schema AgentResponse ở trên
        """
        start = time.perf_counter()

        if version == "v1":
            return await self._query_v1(question, start)
        return await self._query_v2(question, start)

    async def _query_v1(self, question: str, start: float) -> Dict:
        """V1: top_k=2, prompt đơn giản, temperature=0.8"""
        # TODO (Khiêm): implement
        # 1. ChromaDB query top_k=2
        # 2. Gọi LLM với system prompt ngắn
        # 3. Trả về đúng schema
        await asyncio.sleep(0.1)  # xóa khi implement thật
        return {
            "answer": "[V1 placeholder]",
            "retrieved_chunk_ids": [],
            "contexts": [],
            "metadata": {
                "version": "v1",
                "model": os.getenv("AGENT_MODEL", "gpt-4o-mini"),
                "tokens_used": 0,
                "latency_ms": (time.perf_counter() - start) * 1000,
            },
        }

    async def _query_v2(self, question: str, start: float) -> Dict:
        """V2: top_k=5, filter score threshold, prompt kỹ, temperature=0.1"""
        # TODO (Khiêm): implement
        # 1. ChromaDB query top_k=5, lọc distance < 0.5
        # 2. Gọi LLM với system prompt yêu cầu cite nguồn, temperature=0.1
        # 3. Trả về đúng schema
        await asyncio.sleep(0.1)  # xóa khi implement thật
        return {
            "answer": "[V2 placeholder]",
            "retrieved_chunk_ids": [],
            "contexts": [],
            "metadata": {
                "version": "v2",
                "model": os.getenv("AGENT_MODEL", "gpt-4o-mini"),
                "tokens_used": 0,
                "latency_ms": (time.perf_counter() - start) * 1000,
            },
        }


if __name__ == "__main__":
    async def _test():
        agent = MainAgent()
        resp = await agent.query("SLA xử lý ticket P1 là bao lâu?", version="v2")
        print(resp)

    asyncio.run(_test())
