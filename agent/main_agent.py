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
from openai import AsyncOpenAI

from engine.chroma_utils import get_or_bootstrap_collection, query_collection

load_dotenv()

class MainAgent:
    def __init__(self):
        self.name = "SupportAgent"
        self.model = os.getenv("AGENT_MODEL", "gpt-4o-mini")
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
        self.collection = None

        chroma_path = os.getenv("CHROMA_PATH", "data/chroma_db")
        collection_name = os.getenv("CHROMA_COLLECTION", "lab14_seed_kb")
        try:
            self.collection = get_or_bootstrap_collection(
                chroma_path, collection_name=collection_name
            )
        except Exception:
            self.collection = None

    def _retrieve(self, question: str, top_k: int) -> Dict:
        if self.collection is None:
            return {"ids": [], "documents": [], "distances": []}

        try:
            result = query_collection(self.collection, question, n_results=top_k)
        except Exception:
            return {"ids": [], "documents": [], "distances": []}

        ids = result.get("ids", [[]])
        docs = result.get("documents", [[]])
        distances = result.get("distances", [[]])
        return {
            "ids": ids[0] if ids else [],
            "documents": docs[0] if docs else [],
            "distances": distances[0] if distances else [],
        }

    async def _generate_answer(self, question: str, contexts: List[str], temperature: float) -> Dict:
        if not contexts:
            return {
                "answer": "Không có thông tin phù hợp trong tài liệu hiện có.",
                "tokens_used": 0,
            }

        if self.client is None:
            joined = "\n\n".join(contexts[:2])
            return {
                "answer": f"Tóm tắt từ context:\n{joined[:600]}",
                "tokens_used": 0,
            }

        context_text = "\n\n".join(contexts)
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là trợ lý nội bộ. Chỉ được trả lời dựa trên context. Nếu không đủ thông tin, phải nói rõ không có thông tin.",
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nContext:\n{context_text}",
                },
            ],
        )

        return {
            "answer": response.choices[0].message.content or "",
            "tokens_used": getattr(response.usage, "total_tokens", 0) if response.usage else 0,
        }

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
        retrieval = self._retrieve(question, top_k=2)
        gen = await self._generate_answer(question, retrieval["documents"], temperature=0.8)
        return {
            "answer": gen["answer"],
            "retrieved_chunk_ids": retrieval["ids"],
            "contexts": retrieval["documents"],
            "metadata": {
                "version": "v1",
                "model": self.model,
                "tokens_used": gen["tokens_used"],
                "latency_ms": (time.perf_counter() - start) * 1000,
            },
        }

    async def _query_v2(self, question: str, start: float) -> Dict:
        """V2: top_k=5, filter score threshold, prompt kỹ, temperature=0.1"""
        retrieval = self._retrieve(question, top_k=5)
        filtered_ids = []
        filtered_docs = []

        if retrieval["distances"]:
            for chunk_id, doc, dist in zip(
                retrieval["ids"], retrieval["documents"], retrieval["distances"]
            ):
                if dist is None or dist <= 0.5:
                    filtered_ids.append(chunk_id)
                    filtered_docs.append(doc)
            if not filtered_ids:
                # Fallback to top results when threshold is too strict for current embedding space.
                filtered_ids = retrieval["ids"]
                filtered_docs = retrieval["documents"]
        else:
            filtered_ids = retrieval["ids"]
            filtered_docs = retrieval["documents"]

        gen = await self._generate_answer(question, filtered_docs, temperature=0.1)
        return {
            "answer": gen["answer"],
            "retrieved_chunk_ids": filtered_ids,
            "contexts": filtered_docs,
            "metadata": {
                "version": "v2",
                "model": self.model,
                "tokens_used": gen["tokens_used"],
                "latency_ms": (time.perf_counter() - start) * 1000,
            },
        }


if __name__ == "__main__":
    async def _test():
        agent = MainAgent()
        resp = await agent.query("SLA xử lý ticket P1 là bao lâu?", version="v2")
        print(resp)

    asyncio.run(_test())
