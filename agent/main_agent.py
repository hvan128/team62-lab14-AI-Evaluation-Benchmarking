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
        chroma_path = os.getenv("CHROMA_DB_PATH", "data/chroma_db")
        self._chroma = chromadb.PersistentClient(path=chroma_path)
        collection_name = os.getenv("CHROMA_COLLECTION_NAME", "rag_documents")
        self._collection = self._chroma.get_collection(collection_name)

        from chromadb.utils import embedding_functions
        self._openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )
        self._fallback_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-ada-002"
        )

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

    async def _query_v1(self, question: str, start: float) -> Dict:
        """V1: top_k=2, prompt đơn giản, temperature=0.8"""
        # Embed manually
        query_embeds = self._openai_ef([question])
        try:
            results = self._collection.query(
                query_embeddings=query_embeds,
                n_results=2,
            )
        except Exception:
            # Thu lay fallback
            query_embeds = self._fallback_ef([question])
            results = self._collection.query(
                query_embeddings=query_embeds,
                n_results=2,
            )
        
        chunk_ids: List[str] = results["ids"][0] if results["ids"] else []
        contexts: List[str] = results["documents"][0] if results["documents"] else []

        context_block = "\n\n".join(contexts)
        messages = [
            {
                "role": "system",
                "content": (
                    "Bạn là trợ lý hỗ trợ khách hàng. "
                    "Trả lời ngắn gọn dựa trên tài liệu sau.\n\n"
                    + context_block
                ),
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
            "retrieved_chunk_ids": chunk_ids,
            "contexts": contexts,
            "metadata": {
                "version": "v1",
                "model": self._model,
                "tokens_used": tokens_used,
                "latency_ms": (time.perf_counter() - start) * 1000,
            },
        }

    async def _query_v2(self, question: str, start: float) -> Dict:
        """V2: top_k=5, filter score threshold, prompt kỹ, temperature=0.1"""
        # Embed manually
        query_embeds = self._openai_ef([question])
        try:
            results = self._collection.query(
                query_embeddings=query_embeds,
                n_results=5,
            )
        except Exception:
            query_embeds = self._fallback_ef([question])
            results = self._collection.query(
                query_embeddings=query_embeds,
                n_results=5,
            )
            
        distances = results["distances"][0] if results["distances"] else []
        all_chunk_ids = results["ids"][0] if results["ids"] else []
        all_contexts = results["documents"][0] if results["documents"] else []
        
        chunk_ids: List[str] = []
        contexts: List[str] = []
        for d, cid, ctx in zip(distances, all_chunk_ids, all_contexts):
            if d < 0.5:
                chunk_ids.append(cid)
                contexts.append(ctx)

        # Fallback top-2 nếu lọc hết
        if not chunk_ids and all_chunk_ids:
            chunk_ids = all_chunk_ids[:2]
            contexts = all_contexts[:2]

        filtered_ids = chunk_ids
        filtered_contexts = contexts

        context_block = "\n\n".join(
            f"[Nguồn {i + 1}] {ctx}" for i, ctx in enumerate(filtered_contexts)
        )
        system_prompt = (
            "Bạn là chuyên gia hỗ trợ khách hàng. "
            "Dựa CHÍNH XÁC vào tài liệu dưới đây, hãy trả lời câu hỏi một cách đầy đủ, "
            "có trích dẫn nguồn [Nguồn X] khi cần. "
            "Nếu tài liệu không đủ thông tin, hãy nói rõ điều đó.\n\n"
            f"{context_block}"
        )
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
