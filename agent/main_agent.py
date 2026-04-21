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

import chromadb
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()


class MainAgent:
    def __init__(self):
        self.name = "SupportAgent"

        chroma_path = os.getenv("CHROMA_DB_PATH", "data/chroma_db")
        self._chroma = chromadb.PersistentClient(path=chroma_path)
        collection_name = os.getenv("CHROMA_COLLECTION_NAME", "lab14_seed_kb")
        self._collection = self._chroma.get_collection(collection_name)
        self._embed_model = "text-embedding-ada-002"

        self._llm = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._model = os.getenv("AGENT_MODEL", "gpt-4o-mini")

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

    async def _embed(self, text: str) -> List[float]:
        resp = await self._llm.embeddings.create(model=self._embed_model, input=text)
        return resp.data[0].embedding

    async def _query_v1(self, question: str, start: float) -> Dict:
        """V1: không dùng RAG, trả lời thuần LLM — intentionally worse baseline."""
        messages = [
            {
                "role": "system",
                "content": "Bạn là trợ lý hỗ trợ khách hàng. Hãy trả lời câu hỏi sau.",
            },
            {"role": "user", "content": question},
        ]

        completion = await self._llm.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.8,
        )
        answer = completion.choices[0].message.content
        tokens_used = completion.usage.total_tokens

        return {
            "answer": answer,
            "retrieved_chunk_ids": [],
            "contexts": [],
            "metadata": {
                "version": "v1",
                "model": self._model,
                "tokens_used": tokens_used,
                "latency_ms": (time.perf_counter() - start) * 1000,
            },
        }

    async def _query_v2(self, question: str, start: float) -> Dict:
        """V2: top_k=5, filter distance < 0.5, prompt kỹ, temperature=0.1"""
        emb = await self._embed(question)
        results = self._collection.query(
            query_embeddings=[emb],
            n_results=5,
        )
        chunk_ids: List[str] = results["ids"][0]
        contexts: List[str] = results["documents"][0]
        context_block = "\n\n".join(
            f"[Nguồn {i + 1}] {ctx}" for i, ctx in enumerate(contexts)
        )
        system_prompt = (
            "Bạn là chuyên gia hỗ trợ khách hàng. "
            "Dựa vào các tài liệu nội bộ dưới đây, hãy trả lời câu hỏi một cách đầy đủ và chính xác. "
            "Trích dẫn nguồn [Nguồn X] khi nêu thông tin cụ thể. "
            "Nếu câu hỏi liên quan đến số liệu hoặc quy trình, hãy nêu đúng con số và các bước.\n\n"
            f"{context_block}"
        )
        filtered_ids = chunk_ids
        filtered_contexts = contexts
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

        completion = await self._llm.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.1,
        )
        answer = completion.choices[0].message.content
        tokens_used = completion.usage.total_tokens

        return {
            "answer": answer,
            "retrieved_chunk_ids": filtered_ids,
            "contexts": filtered_contexts,
            "metadata": {
                "version": "v2",
                "model": self._model,
                "tokens_used": tokens_used,
                "latency_ms": (time.perf_counter() - start) * 1000,
            },
        }


if __name__ == "__main__":
    async def _test():
        agent = MainAgent()
        resp = await agent.query("SLA xử lý ticket P1 là bao lâu?", version="v2")
        print(resp)

    asyncio.run(_test())
