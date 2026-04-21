import json
import math
import os
import re
from typing import Dict, List, Tuple

import chromadb

SEED_COLLECTION = "lab14_seed_kb"
EMBED_DIM = 256
TOKEN_PATTERN = re.compile(r"\w+", flags=re.UNICODE)


def _tokenize(text: str) -> List[str]:
    return TOKEN_PATTERN.findall((text or "").lower())


def _text_to_embedding(text: str, dim: int = EMBED_DIM) -> List[float]:
    # Lightweight deterministic hashing vector to avoid external embedding dependencies.
    vec = [0.0] * dim
    for token in _tokenize(text):
        idx = hash(token) % dim
        vec[idx] += 1.0

    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def _build_expected_answer(item: Dict) -> str:
    if item.get("expected_answer"):
        return str(item["expected_answer"])
    criteria = item.get("grading_criteria")
    if isinstance(criteria, list) and criteria:
        return " ".join(str(c) for c in criteria)
    return "Không có thông tin đủ trong tài liệu hiện có."


def _seed_rows_from_files() -> List[Tuple[str, str, str]]:
    rows: List[Tuple[str, str, str]] = []
    paths = [
        os.path.join("data", "grading_questions.json"),
        os.path.join("data", "test_questions.json"),
    ]

    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for idx, item in enumerate(data):
            question = str(item.get("question", "")).strip()
            if not question:
                continue

            expected_answer = _build_expected_answer(item)
            expected_sources = item.get("expected_sources", [])
            source_name = (
                str(expected_sources[0]) if isinstance(expected_sources, list) and expected_sources else "seed_internal.txt"
            )

            chunk_id = f"chunk_seed_{os.path.basename(path).replace('.json', '')}_{idx:03d}"
            doc = f"Question: {question}\nExpected Answer: {expected_answer}"
            rows.append((chunk_id, doc, source_name))

    return rows


def get_or_bootstrap_collection(chroma_path: str, collection_name: str = SEED_COLLECTION):
    os.makedirs(chroma_path, exist_ok=True)
    client = chromadb.PersistentClient(path=chroma_path)

    collection = client.get_or_create_collection(name=collection_name)

    if collection.count() == 0:
        rows = _seed_rows_from_files()
        if rows:
            ids = [r[0] for r in rows]
            docs = [r[1] for r in rows]
            metas = [{"source": r[2]} for r in rows]
            embeds = [_text_to_embedding(doc) for doc in docs]
            collection.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeds)

    return collection


def query_collection(collection, query: str, n_results: int = 1) -> Dict:
    query_embedding = _text_to_embedding(query)
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "distances", "metadatas"],
    )
